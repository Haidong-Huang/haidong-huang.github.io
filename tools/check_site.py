"""Validate generated pages before deployment (Python standard library only)."""

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.duplicates = [], set(), set()
        self.canonical = self.language = None
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.language = attrs.get("lang")
        if "id" in attrs:
            identifier = attrs["id"]
            if identifier in self.ids:
                self.duplicates.add(identifier)
            self.ids.add(identifier)
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href")
        for key in ("src", "href"):
            if attrs.get(key):
                self.links.append(attrs[key])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--url", default="https://haidong-huang.github.io")
    parser.add_argument("--preview", action="store_true", help="Skip production exclusion checks")
    args = parser.parse_args()
    root, errors = args.directory.resolve(), []
    pages = {path: Page(path) for path in root.rglob("*.html")}
    for name in ("index.html", "publications.html", "404.html", "robots.txt", "sitemap.xml"):
        if not (root / name).is_file():
            errors.append(f"Missing {name}")
    for path, page in pages.items():
        name = path.relative_to(root).as_posix()
        if page.language != "en":
            errors.append(f"{name}: missing English language declaration")
        if page.duplicates:
            errors.append(f"{name}: duplicate IDs {sorted(page.duplicates)}")
        if name in ("index.html", "publications.html"):
            expected = args.url.rstrip("/") + ("/" if name == "index.html" else "/" + name)
            if page.canonical != expected:
                errors.append(f"{name}: incorrect canonical URL {page.canonical!r}")
        for link in page.links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            target = (root / unquote(parsed.path).lstrip("/") if parsed.path.startswith("/")
                      else path.parent / unquote(parsed.path)) if parsed.path else path
            if target.is_dir():
                target /= "index.html"
            elif not target.is_file() and not target.suffix:
                target = target.with_suffix(".html")
            target = target.resolve()
            if not target.is_file():
                errors.append(f"{name}: missing local target {link}")
            elif parsed.fragment and target in pages and unquote(parsed.fragment) not in pages[target].ids:
                errors.append(f"{name}: missing anchor {link}")
    sitemap = root / "sitemap.xml"
    if sitemap.is_file():
        try:
            locations = {node.text for node in ET.parse(sitemap).iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")}
            expected = {args.url.rstrip("/") + "/", args.url.rstrip("/") + "/publications.html"}
            if locations != expected:
                errors.append("Sitemap must contain canonical home and publications URLs")
        except ET.ParseError as error:
            errors.append(f"Invalid sitemap: {error}")
    robots = root / "robots.txt"
    if robots.is_file() and f"Sitemap: {args.url.rstrip('/')}/sitemap.xml" not in robots.read_text():
        errors.append("robots.txt has no correct sitemap URL")
    if not args.preview:
        for name in ("README.md", "README.html", "CONTENT_NOTES.md", "DEPLOYMENT.md", "Gemfile", "Gemfile.lock", "tools", "release", "assets/images/incoming", "assets/images/etc", "assets/images/photos/portrait.jpg"):
            if (root / name).exists():
                errors.append(f"Non-public source included in build: {name}")
    if errors:
        raise SystemExit("Site checks failed:\n- " + "\n- ".join(errors))
    print(f"Site checks passed: {len(pages)} HTML pages; local links, image paths, anchors, canonical URLs and sitemap valid.")


if __name__ == "__main__":
    main()
