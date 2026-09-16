"""Preview the current Jekyll templates locally without a Ruby installation.

This serves the existing Liquid templates and YAML data for visual review. It is
not a replacement for validating the production site with Jekyll before release.
Install preview dependencies with:
    python -m pip install --target .preview-tools python-liquid==2.3.1 PyYAML
"""

from __future__ import annotations

import argparse
import functools
import json
import re
import shutil
import sys
import threading
from collections import OrderedDict
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_preview"
sys.path.insert(0, str(ROOT / ".preview-tools"))

try:
    import yaml
    from liquid import DictLoader, Environment
except ImportError:
    raise SystemExit(
        "Preview dependencies are missing. Run:\n"
        "python -m pip install --target .preview-tools python-liquid==2.3.1 PyYAML"
    )

PAGES = ("index.html", "publications.html", "404.html", "robots.txt", "sitemap.xml")
BUILD_LOCK = threading.Lock()
INCLUDE = re.compile(r"{%(-?)\s*include\s+([^\s%]+)(.*?)\s*(-?)%}", re.S)
ARGUMENT = re.compile(r'''([A-Za-z_]\w*)\s*=\s*("[^"]*"|'[^']*'|[^\s]+)''')


def adapt_includes(source: str) -> str:
    """Map Jekyll's include namespace to isolated Liquid render arguments."""
    def replace(match: re.Match) -> str:
        arguments = ARGUMENT.findall(match[3])
        arguments_text = ", ".join(
            f"{json.dumps(key)}, {value}" for key, value in arguments
        )
        prepare = '{% assign preview_include = "" | named_args'
        if arguments_text:
            prepare += ": " + arguments_text
        prepare += " %}"
        render = (
            "{% render " + json.dumps(match[2])
            + ", include: preview_include, site: site, page: page %}"
        )
        return prepare + render

    return INCLUDE.sub(replace, source).replace("include.limit", 'include["limit"]')


def front_matter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8-sig")
    if text.startswith("---\n"):
        _, header, body = text.split("---", 2)
        return yaml.safe_load(header) or {}, body
    return {}, text


def named_args(_value, *pairs) -> dict:
    values = dict(zip(pairs[::2], pairs[1::2]))
    # Jekyll treats an absent include.limit as an unlimited loop.
    values.setdefault("limit", 100000)
    return values


def group_by(items, key):
    groups = OrderedDict()
    for item in items:
        value = str(item.get(key, ""))
        groups.setdefault(value, []).append(item)
    return [
        {"name": name, "items": values, "size": len(values)}
        for name, values in groups.items()
    ]


def build() -> None:
    config = yaml.safe_load((ROOT / "_config.yml").read_text(encoding="utf-8"))
    data = {}
    for path in (ROOT / "_data").rglob("*.yml"):
        parts = path.relative_to(ROOT / "_data").with_suffix("").parts
        parent = data
        for part in parts[:-1]:
            parent = parent.setdefault(part, {})
        parent[parts[-1]] = yaml.safe_load(path.read_text(encoding="utf-8"))

    site = {**config, "data": data}
    for collection in config.get("collections", {}):
        site[collection] = []
        for path in sorted((ROOT / ("_" + collection)).rglob("*.md")):
            item, body = front_matter(path)
            item["content"] = body
            item["id"] = "/" + str(path.relative_to(ROOT).with_suffix("")).replace("\\", "/")
            site[collection].append(item)

    includes = {
        path.relative_to(ROOT / "_includes").as_posix(): adapt_includes(
            path.read_text(encoding="utf-8")
        )
        for path in (ROOT / "_includes").rglob("*.html")
    }
    environment = Environment(loader=DictLoader(includes))
    environment.add_filter("named_args", named_args)
    environment.add_filter("group_by", group_by)
    environment.add_filter(
        "encode_email", lambda value: "".join(f"&#{ord(char)};" for char in str(value))
    )

    def relative_url(value):
        value = str(value)
        if urlsplit(value).scheme or value.startswith("//"):
            return value
        return str(site.get("baseurl", "")).rstrip("/") + "/" + value.lstrip("/")

    environment.add_filter("relative_url", relative_url)
    environment.add_filter(
        "absolute_url", lambda value: str(site.get("url", "")).rstrip("/") + relative_url(value)
    )
    OUTPUT.mkdir(exist_ok=True)
    for name in PAGES:
        page, source = front_matter(ROOT / name)
        page["url"] = "/" if name == "index.html" else "/" + name
        body = environment.from_string(adapt_includes(source)).render(site=site, page=page)
        html = body
        if page.get("layout"):
            layout = ROOT / "_layouts" / (page["layout"] + ".html")
            html = environment.from_string(adapt_includes(layout.read_text(encoding="utf-8"))).render(
                site=site, page=page, content=body
            )
        (OUTPUT / name).write_text(html, encoding="utf-8")

    for source in (ROOT / "assets").rglob("*"):
        if not source.is_file():
            continue
        target = OUTPUT / source.relative_to(ROOT)
        if not target.exists() or source.stat().st_mtime_ns != target.stat().st_mtime_ns:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


class PreviewHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ("/", "/index.html", "/publications", "/publications/", "/publications.html"):
            with BUILD_LOCK:
                build()
            self.path = "/index.html" if path in ("/", "/index.html") else "/publications.html"
        super().do_GET()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=4000)
    args = parser.parse_args()
    build()
    print(f"Preview generated in {OUTPUT}", flush=True)
    if args.serve:
        handler = functools.partial(PreviewHandler, directory=str(OUTPUT))
        try:
            server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
        except OSError as error:
            raise SystemExit(f"Unable to start preview: {error}. Try --port 4001.")
        print(f"Open http://127.0.0.1:{args.port}/ in your browser.", flush=True)
        print("Refresh to see content edits. Press Ctrl+C to stop.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


if __name__ == "__main__":
    main()
