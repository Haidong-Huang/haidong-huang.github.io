# Haidong (Andrew) Huang

English academic homepage for research in Physical AI and robotics.

Planned public URL: **https://haidong-huang.github.io/**. Available after the repository is renamed and GitHub Pages is enabled.

Read [DEPLOYMENT.md](DEPLOYMENT.md) for the publishing guide in Chinese.

## Content

- Profile, education, experience, awards and services: `_data/profile.yml`
- News: `_news/*.md`
- Publications and figures: `_publications/**/*.md`
- Website address: `_config.yml`
- Layout and styles: `_includes/`, `_layouts/`, `assets/css/global.css`

## Preview and build

Run `preview.cmd`, then open http://127.0.0.1:4000/ for the Windows visual preview. This lightweight preview is not the production Jekyll build.

For the production build, install Ruby 3.3 and Bundler, then run:

```sh
bundle install
bundle exec jekyll build
python tools/check_site.py _site
```

For Jekyll's live preview, run `bundle exec jekyll serve`.

GitHub Actions builds and checks pull requests. After initial Pages setup, commits to `main` automatically deploy when the repository is named `haidong-huang.github.io`.

Run `python tools/package_source.py` to create a clean source archive. Archives, browser profiles, preview dependencies and original image imports are excluded from the public site.

## Attribution

Based on the supplied local version of [academic-homepage](https://github.com/luost26/academic-homepage). The original MIT [license](LICENSE) and footer attribution are retained.
