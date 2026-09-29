"""Validate production HTML, migrated content, links and local assets."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / '_site'


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.ids, self.duplicates, self.refs = set(), set(), []
        self.text, self.articles = [], {}
        self.current = None
        self.canonical = self.language = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html':
            self.language = attrs.get('lang')
        if 'id' in attrs:
            if attrs['id'] in self.ids:
                self.duplicates.add(attrs['id'])
            self.ids.add(attrs['id'])
        if tag == 'article':
            self.current = attrs['id']
            self.articles[self.current] = []
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical = attrs.get('href')
        for key in ('src', 'href'):
            if attrs.get(key):
                self.refs.append(attrs[key])

    def handle_data(self, data):
        self.text.append(data)
        if self.current:
            self.articles[self.current].append(data)

    def handle_endtag(self, tag):
        if tag == 'article':
            self.current = None


def plain(html):
    return ' '.join(' '.join(Page(html).text).split())


def main():
    data = json.loads((ROOT / 'data/site.json').read_text(encoding='utf-8'))
    files = list(OUTPUT.rglob('*.html'))
    pages = {path.resolve(): Page(path.read_text(encoding='utf-8')) for path in files}
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    required = {'index.html', 'publications.html', 'publications/index.html', '404.html'}
    check({p.relative_to(OUTPUT).as_posix() for p in files} == required, 'Unexpected or missing public pages')
    for path, page in pages.items():
        name = path.relative_to(OUTPUT).as_posix()
        check(page.language == 'en', f'{name}: language must be English')
        check(not page.duplicates, f'{name}: duplicate IDs {page.duplicates}')
        check(not ({'language', 'beyond'} & page.ids), f'{name}: removed template section still present')
        check(not re.search(r'Haolin Yang|杨昊霖|Peking University|TOEFL|Miscellaneous', ' '.join(page.text)), f'{name}: template content remains')
        check(page.canonical == data['url'] + ('/' if name == 'index.html' else '/404.html' if name == '404.html' else '/publications.html'), f'{name}: incorrect canonical URL')
        for ref in page.refs:
            parsed = urlsplit(ref)
            if parsed.scheme or parsed.netloc:
                continue
            target = (OUTPUT / unquote(parsed.path).lstrip('/') if parsed.path.startswith('/') else path.parent / unquote(parsed.path)) if parsed.path else path
            if target.is_dir():
                target /= 'index.html'
            target = target.resolve()
            check(target.is_file(), f'{name}: missing local target {ref}')
            if parsed.fragment and target in pages:
                check(unquote(parsed.fragment) in pages[target].ids, f'{name}: missing fragment {ref}')
        if name != '404.html':
            check(len(page.articles) == len(data['publications']), f'{name}: publication count changed')
            for paper in data['publications']:
                article = ' '.join(' '.join(page.articles.get(f'publication-{paper["cv_order"]}', [])).split())
                for value in (paper['title'], plain(paper['abstract']), paper.get('highlight'), paper.get('role'), paper.get('pub_note')):
                    if value:
                        check(value in article, f'{name}: content missing from paper {paper["cv_order"]}: {value[:45]}')
                for author in paper['authors']:
                    check(author.rstrip('*#') in article, f'{name}: missing author {author}')
    home = pages[(OUTPUT / 'index.html').resolve()]
    home_text = ' '.join(' '.join(home.text).split())
    check(data['profile']['primary_name'] in home_text, 'Missing personal name')
    for item in data['news']:
        check(plain(item['title']) in home_text, f'Missing News item {item["month_key"]}')
    for section in ('education', 'experience', 'awards', 'academic_services'):
        for item in data['profile'][section]:
            check(item['name'] in home_text, f'Missing {section} item {item["name"]}')
    for paragraph in re.findall(r'<p>.*?</p>', data['profile']['short_bio'], re.S):
        check(plain(paragraph) in home_text, 'Biography or research-interest text changed')
    check(not any(char in home_text for char in ('🎆', '🎇')), 'News fireworks were reintroduced')
    for ref in re.findall(r'url\([\"\']?([^\)\"\']+)', (OUTPUT / 'stylesheet.css').read_text(encoding='utf-8')):
        check((OUTPUT / ref).is_file(), f'Missing CSS asset: {ref}')
    urls = {node.text for node in ET.parse(OUTPUT / 'sitemap.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}
    check(urls == {data['url'] + '/', data['url'] + '/publications.html'}, 'Sitemap URLs do not match the live domain')
    for name in ('tools', 'data', 'templates', 'TidalHarley.github.io-main', 'README.md'):
        check(not (OUTPUT / name).exists(), f'Non-public source copied into the site: {name}')
    if errors:
        raise SystemExit('Site checks failed:\n- ' + '\n- '.join(errors))
    print(f'Passed: {len(pages)} pages, {len(data["publications"])} complete publications, {len(data["news"])} news entries, all profile content, local assets and internal anchors.')


if __name__ == '__main__':
    main()
