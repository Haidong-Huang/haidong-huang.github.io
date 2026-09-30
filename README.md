# Haidong (Andrew) Huang — Academic Homepage

English personal website: **https://haidong-huang.github.io/**

Uses the supplied TidalHarley homepage design, with a section index, local fonts, selected/all publication views, and full-size figure previews. The Language section is omitted. Miscellaneous contains Haidong's interests and personal quotation. The previous site's personal content and images are preserved.

## Preview

Double-click `preview.cmd`, then open **http://127.0.0.1:4001/**. The preview builds the same files deployed to GitHub Pages. Refresh after editing content.

Alternatively, use Python 3.9 or later:

```sh
python tools/preview.py
```

No Ruby, Node.js, package installation or third-party Python library is required.

## Edit

- `data/site.json`: biography, contact links, education, experience, publications, News, awards, academic services and Miscellaneous.
- `templates/page.html`: shared page structure and metadata.
- `tools/build.py`: section rendering; preserves the full text from the content file.
- `stylesheet.css`: the supplied template's style and responsive layout adaptations.
- `navigation.js`, `interactions.js`: navigation, selected/all publications and figure previews.
- `assets/`: only the images, local font and icons used by this site.

## Build and publish

```sh
python tools/build.py
python tools/check_site.py
```

Generated pages are in `_site/`. Both `/publications.html` and `/publications/` remain available, with the previous `publication-N` anchors preserved.

GitHub Actions validates the site before deploying changes to `main` in `Haidong-Huang/haidong-huang.github.io`. Only `_site/` is published. Asset URLs use a content-based version to avoid stale style/script caches. The original supplied template folder is kept locally and excluded from Git and deployment.

Read [THIRD_PARTY.md](THIRD_PARTY.md) for attribution and asset notices.
