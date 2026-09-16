"""Create a clean source archive for GitHub, excluding previews and demo images."""

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import re

ROOT = Path(__file__).resolve().parents[1]


def source_files():
    files = {ROOT / name for name in (
        ".gitignore", ".ruby-version", "_config.yml", "Gemfile", "LICENSE",
        "README.md", "DEPLOYMENT.md", "index.html", "publications.html", "404.html",
        "robots.txt", "sitemap.xml", "preview.cmd",
    )}
    if (ROOT / "Gemfile.lock").exists():
        files.add(ROOT / "Gemfile.lock")
    for folder in (".github/workflows", "_data", "_includes", "_layouts", "_news", "_publications", "assets/css", "assets/js"):
        files.update(path for path in (ROOT / folder).rglob("*") if path.is_file())
    files.discard(ROOT / "_data/gallery.yml")
    files.update((ROOT / "tools").glob("*.py"))
    for source in list(files):
        if source.suffix not in (".yml", ".md", ".html", ".css", ".js"):
            continue
        for name in re.findall(r'/assets/images/[A-Za-z0-9_./-]+\.(?:png|jpg|jpeg|gif|svg)', source.read_text(encoding="utf-8")):
            asset = ROOT / name.lstrip("/")
            if asset.exists() and "incoming" not in asset.parts:
                files.add(asset)
    files.discard(ROOT / "assets/images/badges/page_logo.png")
    return sorted(files)


def main():
    release = ROOT / "release"
    release.mkdir(exist_ok=True)
    archive = release / "haidong-huang-homepage-source.zip"
    files = source_files()
    with ZipFile(archive, "w", ZIP_DEFLATED) as package:
        for path in files:
            package.write(path, path.relative_to(ROOT).as_posix())
    (release / "source-files.txt").write_text("\n".join(path.relative_to(ROOT).as_posix() for path in files) + "\n", encoding="utf-8")
    print(f"Prepared {len(files)} source files: {archive} ({archive.stat().st_size / 1024 / 1024:.2f} MB)")


if __name__ == "__main__":
    main()
