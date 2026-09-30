"""Build the static homepage with Python 3; no third-party dependencies required."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]


def text(value):
    return escape(str(value), quote=True)


def link(label, url):
    return f'<a href="{text(url)}" target="_blank" rel="noopener noreferrer">{text(label)}</a>' if url else text(label)


def asset(path, prefix):
    return prefix + path.lstrip('/')


def section(identifier, title, content, extra='', label=None):
    return (f'<section id="{identifier}" class="page-section {extra}" data-nav-section '
            f'data-nav-label="{text(label or title)}" tabindex="-1">'
            f'<header class="section-heading"><h2 class="section-title">{text(title)}</h2></header>{content}</section>')


def profile_html(profile, prefix):
    biography, interests = profile['short_bio'].split('<h6>Research Interests</h6>')
    paragraphs = re.findall(r'<p>.*?</p>', biography, re.S)
    introduction = ''.join(paragraphs[:2]).replace('<p>', '<p class="profile-intro">')
    continuation = ''.join(paragraphs[2:]).replace('<p>', '<p class="profile-intro">')
    contact = []
    email = ''.join(f'&#{ord(c)};' for c in profile['email'])
    contact.append(f'<a class="profile-link" href="mailto:{email}"><img src="{prefix}assets/files/icon/email.png" width="22" height="22" alt="">Email</a>')
    for title, url, icon in (
        ('Google Scholar', 'https://scholar.google.com/citations?user=' + profile['gscholar'], 'google_scholar.png'),
        ('GitHub', 'https://github.com/' + profile['github'], 'github.svg'),
    ):
        contact.append(f'<a class="profile-link" href="{url}" target="_blank" rel="noopener noreferrer"><img src="{prefix}assets/files/icon/{icon}" width="22" height="22" alt="">{title}</a>')
    for key, label, monogram in (('linkedin', 'LinkedIn', 'in'), ('zhihu', 'Zhihu', '知')):
        if profile.get(key):
            contact.append(f'<a class="profile-link" href="{text(profile[key])}" target="_blank" rel="noopener noreferrer"><span class="profile-monogram {key}-icon" aria-hidden="true">{monogram}</span>{label}</a>')
    return f'''<section id="about" class="page-section profile-section" data-nav-section data-nav-label="About" tabindex="-1">
      <div class="profile">
        <div class="profile-copy">
          <h1 class="name">{text(profile['primary_name'])}</h1>
          <p class="profile-tagline">{text(profile['secondary_name'])}</p>
          {introduction}
        </div>
        <figure class="profile-portrait"><a href="{asset(profile['portrait_url'], prefix)}" data-figure data-caption="{text(profile['primary_name'])}" aria-label="Enlarge portrait"><img class="avatar" src="{asset(profile['portrait_url'], prefix)}" alt="{text(profile['primary_name'])}" width="602" height="602" fetchpriority="high" decoding="async"></a></figure>
      </div>
      <div class="profile-continuation">{continuation}</div>
      <div class="profile-links" aria-label="Contact and profiles">{''.join(contact)}</div>
      <div class="research-interests"><h2 class="profile-subheading">Research Interests</h2>{interests}</div>
    </section>'''


def news_html(news):
    rows = []
    for item in sorted(news, key=lambda n: n['month_key'], reverse=True):
        title = re.sub(r'href="/?publications(?:\.html)?#', 'href="publications.html#', item['title'])
        emoji = f'<span class="news-emoji" aria-hidden="true">{text(item["emoji"])}</span> ' if item.get('emoji') else ''
        rows.append(f'<li><time datetime="{item["month_key"]}">{text(item["month"])} {item["year"]}</time><p>{emoji}{title}</p></li>')
    return section('news', 'News', '<ul class="news-list">' + ''.join(rows) + '</ul>', 'news-section')


def author_html(author, project_leader=False):
    name = author.rstrip('*#')
    marks = author[len(name):].replace('#', '†')
    if project_leader and name == 'Haidong Huang':
        marks += '‡'
    label = f'<span class="author-self">{text(name)}</span>' if name == 'Haidong Huang' else text(name)
    return label + (f'<sup>{text(marks)}</sup>' if marks else '')


def paper_html(paper, prefix, rank):
    number = paper['cv_order']
    title = text(paper['title'])
    authors = ', '.join(author_html(author, paper.get('role') == 'Project Leader') for author in paper['authors'])
    role = f' <span class="paper-role">({text(paper["role"])})</span>' if paper.get('role') else ''
    badge = re.sub(r'<[^>]+>', '', paper.get('pub_last', ''))
    badge = f'<span class="paper-badge">{text(badge)}</span>' if badge else ''
    note_badge = f' <span class="paper-badge">{text(paper["pub_note_badge"])}</span>' if paper.get('pub_note_badge') else ''
    note = f'<p class="paper-note">{text(paper["pub_note"])}{note_badge}</p>' if paper.get('pub_note') else ''
    highlight = f'<p class="paper-highlight">{text(paper["highlight"])}</p>' if paper.get('highlight') else ''
    links = []
    for label, value in paper.get('links', {}).items():
        url = value.get('url') if isinstance(value, dict) else value
        links.append(link(label, url))
    resources = '<div class="paper-links-group">' + ''.join(links) + '</div>' if links else ''
    selected = str(paper.get('selected', False)).lower()
    return f'''<article id="publication-{number}" class="paper-row {'highlight-paper' if paper.get('selected') else ''}" data-highlight="{selected}" data-selected-order="{paper.get('selected_order', 100 + rank)}" data-all-order="{rank}" aria-labelledby="publication-{number}-title">
      <a class="paper-figure" href="{asset(paper['cover'], prefix)}" data-figure data-caption="{title}" aria-label="Enlarge figure for {title}"><img src="{asset(paper['cover'], prefix)}" alt="Overview figure for {title}" width="{paper['cover_width']}" height="{paper['cover_height']}" loading="lazy" decoding="async"></a>
      <div class="paper-content">
        <h3 class="papertitle" id="publication-{number}-title">{title}{role}</h3>
        <p class="authors">{authors}</p>
        <p class="venue-full">{text(paper.get('pub_pre', ''))}{text(paper['pub'])}{paper.get('pub_post', '')} {text(paper['pub_date'])} {badge}</p>
        {note}{highlight}
        <p class="paper-description">{paper['abstract']}</p>{resources}
      </div>
    </article>'''


def papers_html(papers, prefix, home=True):
    ordered = sorted(papers, key=lambda p: p['cv_order'], reverse=True)
    rows = ''.join(paper_html(p, prefix, i) for i, p in enumerate(ordered))
    button = '<button class="research-toggle" id="research-toggle" type="button" aria-controls="research-papers" aria-expanded="true" hidden>All Research Papers</button>' if home else ''
    return f'''<section id="research" class="page-section research-section" data-nav-section data-nav-label="Publications" tabindex="-1">
      <header class="section-heading research-heading"><h2 class="section-title" id="research-heading">Publications &amp; Manuscripts</h2>{button}</header>
      <p class="paper-meta-note"><span>* Equal contribution</span><span>† Corresponding author</span><span>‡ Project Leader</span></p>
      <p class="sr-only" id="research-status" role="status" aria-live="polite"></p>
      <div id="research-papers">{rows}</div>
      {f'<p class="publication-directory"><a href="{prefix}publications.html">View complete publication list →</a></p>' if home else ''}
    </section>'''


def institutions_html(items, prefix, research=False):
    rows = []
    dimensions = {'polyu.png': (1002, 192), 'nottingham.png': (960, 389), 'hkust.png': (960, 308), 'eit.png': (500, 72)}
    for item in items:
        width, height = dimensions[Path(item['logo']).name]
        details = []
        if item.get('dept') and not research:
            details.append(f'<p>{link(item["dept"], item.get("dept_url"))}</p>')
        position = text(item['position'])
        if research and item.get('dept'):
            position += ' · ' + link(item['dept'], item.get('dept_url'))
        details.append(f'<p>{position}</p>')
        if item.get('lab'):
            details.append(f'<p>{link(item["lab"], item.get("lab_url"))}</p>')
        if item.get('advisor'):
            details.append(f'<p class="institution-detail">Advised by Prof. {link(item["advisor"], item.get("advisor_url"))}</p>')
        if item.get('topics'):
            details.append(f'<p class="institution-detail"><strong>Research:</strong> {text(item["topics"])}</p>')
        rows.append(f'''<div class="institution-row">
          <div class="institution-logo"><img src="{asset(item['logo'], prefix)}" alt="{text(item['name'])} logo" width="{width}" height="{height}" loading="lazy" decoding="async"></div>
          <div class="institution-copy"><h3>{link(item['name'], item.get('url'))}</h3>{''.join(details)}
          <p class="institution-date">{text(item['date'])}</p></div>
        </div>''')
    return section('experience' if research else 'education', 'Research Experience' if research else 'Education',
                   '<div class="experience-list">' + ''.join(rows) + '</div>', label='Experience' if research else 'Education')


def miscellaneous_html(miscellaneous):
    paragraphs = ''.join(f'<p>{paragraph}</p>' for paragraph in miscellaneous['paragraphs'])
    quote = miscellaneous['quote']
    content = f'''<div class="beyond-layout">{paragraphs}</div>
      <blockquote class="personal-quote"><p>“{text(quote['text'])}”</p><cite>— <strong>{text(quote['author'])}</strong></cite></blockquote>'''
    return section('beyond', 'Miscellaneous', content)


def build():
    content = json.loads((ROOT / 'data/site.json').read_text(encoding='utf-8'))
    profile = content['profile']
    output = ROOT / '_site'
    output.mkdir(exist_ok=True)
    fingerprint = sha256()
    inputs = [ROOT / 'data/site.json', ROOT / 'templates/page.html', Path(__file__), ROOT / 'stylesheet.css', ROOT / 'navigation.js', ROOT / 'interactions.js']
    for path in inputs:
        fingerprint.update(path.read_bytes())
    version = fingerprint.hexdigest()[:12]
    template = (ROOT / 'templates/page.html').read_text(encoding='utf-8')
    menu = [('about', 'About'), ('news', 'News'), ('research', 'Publications'), ('education', 'Education'), ('experience', 'Experience'), ('honors', 'Honors'), ('services', 'Services')]

    def page(path, body, title, canonical, nav, prefix='', start='about', robots=''):
        navigation = ''.join(f'<li class="section-nav__item"><a class="section-nav__link" href="{url}">{label}</a></li>' for url, label in nav)
        values = dict(NAME=text(profile['primary_name']), DESCRIPTION=text(content['description']), VERSION=version,
                      TITLE=text(title), CANONICAL=canonical, SITE_URL=content['url'], PREFIX=prefix, START=start,
                      NAV=navigation, CONTENT=body, YEAR=str(datetime.now(timezone.utc).year), ROBOTS=robots)
        rendered = template
        for key, value in values.items():
            rendered = rendered.replace('@@' + key + '@@', value)
        dest = output / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(rendered, encoding='utf-8')

    awards = '<ul class="awards-list">' + ''.join(f'<li><span class="award-year">{a["date"]}</span><span>{text(a["name"])}</span></li>' for a in profile['awards']) + '</ul>'
    services = '<ul class="services-list">' + ''.join(f'<li><span class="service-role">{text(s["role"])}</span><span>{link(s["name"], s.get("url"))}<span class="service-edition">{text(s["abbreviation"])}</span></span></li>' for s in profile['academic_services']) + '</ul>'
    home = profile_html(profile, '') + news_html(content['news']) + papers_html(content['publications'], '')
    home += section('honors', 'Honors & Awards', awards, label='Honors')
    home += institutions_html(profile['education'], '') + institutions_html(profile['experience'], '', True)
    home += section('services', 'Academic Services', services, label='Services')
    home += miscellaneous_html(profile['miscellaneous'])
    # Keep section navigation in the same order as the visible content.
    menu = [('about', 'About'), ('news', 'News'), ('research', 'Publications'), ('honors', 'Honors'), ('education', 'Education'), ('experience', 'Experience'), ('services', 'Services'), ('beyond', 'Miscellaneous')]
    page('index.html', home, profile['primary_name'] + ' | Physical AI / Robotics', content['url'] + '/', [(f'#{i}', n) for i, n in menu])
    for name, prefix in [('publications.html', ''), ('publications/index.html', '../')]:
        body = f'<div class="publications-intro"><a href="{prefix}index.html">← Back to homepage</a><p>{text(profile["primary_name"])}</p></div>'
        body += papers_html(content['publications'], prefix, False)
        page(name, body, 'Publications & Manuscripts | ' + profile['primary_name'], content['url'] + '/publications.html',
             [(prefix + 'index.html', 'Home'), ('#research', 'Publications')], prefix, 'research')
    page('404.html', section('not-found', 'Page not found', '<p>The requested page could not be found.</p><p><a href="/">Go to the homepage →</a></p>'),
         'Page not found | ' + profile['primary_name'], content['url'] + '/404.html', [('/', 'Home')], '/', 'not-found', '<meta name="robots" content="noindex">')
    for name in ('stylesheet.css', 'navigation.js', 'interactions.js'):
        shutil.copy2(ROOT / name, output / name)
    shutil.copytree(ROOT / 'assets', output / 'assets', dirs_exist_ok=True)
    (output / '.nojekyll').write_text('', encoding='utf-8')
    (output / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {content["url"]}/sitemap.xml\n', encoding='utf-8')
    (output / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + ''.join(f'<url><loc>{content["url"]}{p}</loc></url>' for p in ('/', '/publications.html')) + '</urlset>\n', encoding='utf-8')
    print(f'Built {output} | version {version} | {len(content["publications"])} publications | {len(content["news"])} news items')


if __name__ == '__main__':
    build()
