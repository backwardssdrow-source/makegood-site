"""One-time MakeGood launch edit and non-submitting browser checks."""
from __future__ import annotations
import json, re, subprocess, threading, functools, http.server, os, shutil, zipfile
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from xml.sax.saxutils import escape
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = Path.cwd()
OUT = ROOT / '.qa'
OUT.mkdir(exist_ok=True)
REV = '20261013-public-launch-1'
SITE = 'https://backwardssdrow-source.github.io/makegood-site/'
HTML = sorted(p for p in ROOT.rglob('*.html') if '.git' not in p.parts and '.qa' not in p.parts and '.github' not in p.parts)
assert len(HTML) == 16, f'Unexpected HTML inventory: {len(HTML)}'
MODE = (ROOT / '.github/qa-mode').read_text().strip() if (ROOT / '.github/qa-mode').exists() else 'prepare'

def replace_once(text: str, old: str, new: str) -> str:
    if new in text and old not in text:
        return text
    assert text.count(old) == 1, f'Expected one occurrence: {old[:100]}'
    return text.replace(old, new, 1)

def edit(path: str, replacements: list[tuple[str, str]]) -> None:
    p = ROOT / path
    text = p.read_text()
    for old, new in replacements:
        text = replace_once(text, old, new)
    p.write_text(text)

if MODE == 'prepare':
    before_scopes = {str(p.relative_to(ROOT)): [str(x) for x in BeautifulSoup(p.read_text(), 'html.parser').select('.detail-summary, .scope-list, .scope-boundary')] for p in HTML}
    edit('index.html', [
        ('MakeGood provides consulting and coaching for organizations, leaders, and individuals. We help build employee resource group (ERG) programs, develop the people leading them, and work through decisions that shape everyday life at work.', 'MakeGood helps organizations build stronger employee communities, develop leaders, and work through change. We also offer one-to-one coaching.'),
        ('Our founders bring experience leading global employee communities. We help organizations connect a shared direction with the cultural context, relationships, and priorities that shape participation in each market.', 'Our global experience helps connect a shared direction with the cultures, relationships, and priorities of local communities.'),
        ('Drawing on experience building and supporting employee communities across a large, global workforce, we understand that participation takes more than an invitation. It takes trust, shared purpose, and practical support that make it worthwhile for people to get involved and stay invested.', 'Our founders’ experience includes leading Uber’s global ERG program and strengthening strategy and governance across 15 employee communities in four regions.')
    ])
    descriptors = {'presence-scan': ('Presence Scan', 'Individual leadership feedback'), 'presence-lab': ('Presence Lab', 'Team workshops and working agreements'), 'fractional-erg-office': ('Fractional ERG Office', 'Ongoing senior ERG advisory')}
    for slug, (name, description) in descriptors.items():
        edit('services.html', [(f'<h3>{name}</h3>', f'<h3>{name}</h3><p class="service-descriptor">{description}</p>')])
        edit(f'services/{slug}.html', [(f'<h1>{name}</h1>', f'<h1>{name}</h1><p class="service-descriptor">{description}</p>')])
    edit('contact.html', [('We’ll use your inquiry to understand what you need and follow up.', 'One of us will review your note and reply by email. We’ll clarify what you need and whether an introductory conversation would be useful.')])
    css = ROOT / 'site.css'
    addition = '\n/* Plain-language service labels: retain the service names and scope. */\n.service-descriptor{font-size:1rem;font-weight:500;line-height:1.5;margin-top:-8px;margin-bottom:16px}\n'
    if addition not in css.read_text():
        css.write_text(css.read_text() + addition)
    image = SITE + 'makegood-social.png'
    for p in HTML:
        text = p.read_text()
        text, count = re.subn(r'<meta\b(?=[^>]*\bname="robots")[^>]*>', '<meta name="robots" content="index,follow,max-image-preview:large"/>', text)
        assert count == 1, f'Unexpected robots tags: {p}'
        text = re.sub(r'(<link\b[^>]*href="(?:\.\./)?site\.css)\?v=[^" ]+', r'\1?v=' + REV, text)
        if 'name="editorial-revision"' in text:
            text = re.sub(r'<meta\b(?=[^>]*\bname="editorial-revision")[^>]*>', f'<meta name="editorial-revision" content="{REV}"/>', text)
        else:
            text = text.replace('</head>', f'<meta name="editorial-revision" content="{REV}"/>\n</head>')
        text = text.replace('<meta name="twitter:card" content="summary"/>', '<meta name="twitter:card" content="summary_large_image"/>')
        assert 'property="og:image"' not in text
        tags = f'<meta property="og:image" content="{image}"/>\n<meta property="og:image:secure_url" content="{image}"/>\n<meta property="og:image:type" content="image/png"/>\n<meta property="og:image:width" content="1200"/>\n<meta property="og:image:height" content="630"/>\n<meta property="og:image:alt" content="MakeGood Co. People. Culture. Possibilities. ERG consulting, leadership development, and coaching."/>\n<meta name="twitter:image" content="{image}"/>\n<meta name="twitter:image:alt" content="MakeGood Co. People. Culture. Possibilities."/>\n'
        text = text.replace('</head>', tags + '</head>')
        assert '—' not in text and 'noindex' not in text and 'nofollow' not in text, f'Blocking or unedited copy in {p}'
        p.write_text(text)
        scopes = [str(x) for x in BeautifulSoup(text, 'html.parser').select('.detail-summary, .scope-list, .scope-boundary')]
        assert scopes == before_scopes[str(p.relative_to(ROOT))], f'Service price or scope changed in {p}'
    manifest = json.loads((ROOT/'site-manifest.json').read_text())
    manifest.update(search_indexing=True, review_only=False, editorial_revision=REV, public_launch_revision=REV)
    (ROOT/'site-manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n')
    entries = []
    for p in HTML:
        soup = BeautifulSoup(p.read_text(), 'html.parser')
        canonical = soup.select_one('link[rel="canonical"]')['href']
        entries.append('  <url><loc>'+escape(canonical)+'</loc></url>')
    (ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+'\n'.join(entries)+'\n</urlset>\n')
    (ROOT/'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: '+SITE+'sitemap.xml\n')
    readme = (ROOT/'README.md').read_text()
    readme = readme.replace('Current canonical/sharing URLs use the standalone preview base. `noindex,nofollow` remains in place until final-domain cutover. No domain connection is claimed by this migration.', 'Search visibility was enabled with founder approval on October 13, 2026. All 16 public pages allow indexing and have branded social-image metadata. `sitemap.xml` lists the current canonical URLs. The project-level `robots.txt` will apply when served at a custom-domain root; it does not control the parent github.io host. Canonical, sharing, image, sitemap, and robots URLs still use the active standalone GitHub Pages base. Update them together after verifying the custom domain. No custom-domain connection or completed search-engine indexing is claimed.')
    readme = readme.replace('## Migration status — October 12, 2026', '## Migration status: October 12, 2026')
    readme = readme.replace('- Pending: domain DNS/HTTPS, indexing cutover, old-URL redirects, and final-domain email signatures.', '- Indexing restrictions were removed with approval on October 13, 2026. Search-engine discovery is not instantaneous or guaranteed.\n- Pending: domain DNS/HTTPS, final-domain metadata and sitemap URLs, old-URL redirects, and final-domain email signatures.')
    (ROOT/'README.md').write_text(readme)

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

server = http.server.ThreadingHTTPServer(('127.0.0.1', 8765), functools.partial(QuietHandler, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
base = SITE if MODE == 'live' else 'http://127.0.0.1:8765/'
results = {'mode': MODE, 'revision': REV, 'base_url': base, 'pages': [], 'checks': {}, 'form_delivery_tested': False}
failures = []

def require(condition, message):
    if not condition:
        failures.append(message)

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    context = browser.new_context(viewport={'width':1200, 'height':630}, device_scale_factor=1)
    context.route('**/macros/s/**', lambda route: route.abort())
    page = context.new_page()
    if MODE == 'prepare':
        card = '''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"><style>*{box-sizing:border-box}html,body{margin:0;width:1200px;height:630px;overflow:hidden}body{background:#FAF1E0;color:#1F2E2A;font-family:Inter,Arial,sans-serif}.top{height:472px;padding:62px 68px 40px;display:flex;gap:72px;align-items:center}.logo{width:430px;flex-shrink:0;background:#FAF7F2;padding:28px 46px;display:flex;align-items:center;justify-content:center}.logo img{width:338px;height:auto;display:block}h1{font-size:62px;line-height:1.14;letter-spacing:-.035em;font-weight:600;margin:0}.bottom{margin:0 68px;border-top:1px solid #697A39;padding-top:24px;font-size:24px;line-height:1.5;white-space:nowrap}.stripes{position:absolute;left:0;bottom:0;width:100%;display:flex;height:16px}.stripes span{flex:1}.stripes span:nth-child(1){background:#F0441C}.stripes span:nth-child(2){background:#F2A6A2}.stripes span:nth-child(3){background:#F4AC0C}</style></head><body><div class="top"><div class="logo"><img src="../makegood-sunrise.svg" alt="MakeGood Co."></div><h1>People.<br>Culture.<br>Possibilities.</h1></div><div class="bottom">ERG consulting · Leadership development · Coaching</div><div class="stripes"><span></span><span></span><span></span></div></body></html>'''
        (OUT/'social-card.html').write_text(card)
        page.goto('http://127.0.0.1:8765/.qa/social-card.html', wait_until='networkidle')
        page.evaluate('document.fonts.ready')
        assert page.locator('img').evaluate('(img)=>img.complete && img.naturalWidth>0')
        page.screenshot(path=str(ROOT/'makegood-social.png'))
        shutil.copy(ROOT/'makegood-social.png', OUT/'makegood-social.png')
        for p in HTML:
            soup = BeautifulSoup(p.read_text(), 'html.parser')
            ids = [x['id'] for x in soup.select('[id]')]
            require(len(ids)==len(set(ids)), f'Duplicate IDs: {p.name}')
            require(len(soup.select('h1'))==1, f'H1 count: {p.name}')
            for node in soup.select('[href], [src]'):
                for attr in ('href','src'):
                    val = node.get(attr)
                    if not val or urlparse(val).scheme or val.startswith('//'):
                        continue
                    parsed=urlparse(val)
                    target = (p.parent/unquote(parsed.path)).resolve() if parsed.path else p
                    if target.is_dir(): target=target/'index.html'
                    require(target.exists(), f'Missing target {val} in {p.name}')
                    if parsed.fragment and target.suffix=='.html' and target.exists():
                        target_soup=BeautifulSoup(target.read_text(), 'html.parser')
                        require(target_soup.find(id=unquote(parsed.fragment)) is not None, f'Missing fragment {val} in {p.name}')
    shots={'index.html','services.html','about.html','contact.html'}
    for width in (1440, 390):
        page.set_viewport_size({'width':width,'height':960 if width==1440 else 844})
        for p in HTML:
            rel=p.relative_to(ROOT).as_posix()
            response=page.goto(urljoin(base,rel), wait_until='networkidle', timeout=60000)
            page.evaluate('document.fonts.ready')
            page.evaluate('document.activeElement.blur(); window.scrollTo(0,0)')
            page.wait_for_timeout(100)
            state=page.evaluate('''()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,brokenImages:[...document.images].filter(x=>!x.complete||x.naturalWidth===0).map(x=>x.src),h1:document.querySelectorAll('h1').length,robots:document.querySelector('meta[name="robots"]')?.content,rev:document.querySelector('meta[name="editorial-revision"]')?.content,headerBottom:document.querySelector('header').getBoundingClientRect().bottom,mainTop:document.querySelector('main').getBoundingClientRect().top,skipBottom:document.querySelector('.skip').getBoundingClientRect().bottom})''')
            require(response.status==200, f'{rel} HTTP {response.status}')
            require(state['scrollWidth']<=width+1, f'{rel} overflow at {width}: {state["scrollWidth"]}')
            require(not state['brokenImages'], f'{rel} broken images: {state["brokenImages"]}')
            require(state['h1']==1, f'{rel} wrong H1 count')
            require('noindex' not in (state['robots'] or '') and 'index' in (state['robots'] or ''), f'{rel} indexing not enabled')
            require(state['rev']==REV, f'{rel} stale revision {state["rev"]}')
            require(state['headerBottom']<=state['mainTop']+1, f'{rel} header overlaps main at {width}')
            require(state['skipBottom']<=1, f'{rel} skip link visible without focus at {width}')
            require('noindex' not in response.headers.get('x-robots-tag','').lower(), f'{rel} blocked by HTTP header')
            results['pages'].append({'page':rel,'viewport':width,'status':response.status,**state})
            if rel in shots:
                page.screenshot(path=str(OUT/f'{p.stem}-{width}.png'), full_page=True)
    for width in (320,768):
        page.set_viewport_size({'width':width,'height':900})
        page.goto(base, wait_until='networkidle')
        require(page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'), f'Homepage overflow at {width}')
    page.set_viewport_size({'width':390,'height':844})
    page.goto(base,wait_until='networkidle')
    menu=page.locator('.menu-toggle')
    menu.click()
    require(menu.get_attribute('aria-expanded')=='true' and page.locator('#navigation').is_visible(),'Mobile menu did not open')
    require(page.evaluate('document.querySelector("header").getBoundingClientRect().bottom <= document.querySelector("main").getBoundingClientRect().top+1'),'Open menu overlaps content')
    page.keyboard.press('Escape')
    require(menu.get_attribute('aria-expanded')=='false','Escape did not close mobile menu')
    page.goto(urljoin(base,'services.html'),wait_until='networkidle')
    for category,count in [('all',9),('erg',5),('presence',4),('individual',1)]:
        page.locator(f'[data-filter="{category}"]').click()
        require(page.locator('.offer:visible').count()==count, f'Service filter {category} failed')
    page.goto(urljoin(base,'contact.html?service=presence-scan'),wait_until='networkidle')
    require(page.locator('#service-select').input_value()=='presence-scan','Contact service preselection failed')
    require(page.locator('[data-inquiry-submit]').is_enabled(),'Contact form submit not enabled')
    require('One of us will review your note' in page.locator('#contact-availability').inner_text(),'Contact next-step copy absent')
    page.goto(base,wait_until='networkidle')
    page.keyboard.press('Tab')
    require(page.evaluate('document.activeElement.classList.contains("skip")'),'Keyboard skip-link unavailable')
    page.keyboard.press('Enter')
    require(page.evaluate('document.activeElement.id=="main"'),'Skip-link did not focus main')
    metadata=page.evaluate('''()=>({image:document.querySelector('meta[property="og:image"]')?.content,card:document.querySelector('meta[name="twitter:card"]')?.content})''')
    require(metadata['card']=='summary_large_image','Wrong Twitter card')
    img_response=context.request.get(urljoin(base,'makegood-social.png'))
    require(img_response.status==200 and img_response.body().startswith(b'\x89PNG\r\n\x1a\n'),'Social image inaccessible or not PNG')
    require(img_response.headers.get('content-type','').startswith('image/png'),'Social image MIME wrong')
    import struct
    image_size=struct.unpack('>II', img_response.body()[16:24]) if img_response.body().startswith(b'\x89PNG') else (0,0)
    require(image_size==(1200,630),'Social image dimensions wrong')
    require(metadata['image']==SITE+'makegood-social.png','Wrong social URL')
    sitemap=context.request.get(urljoin(base,'sitemap.xml'))
    require(sitemap.status==200 and sitemap.text().count('<loc>')==16,'Sitemap missing or incomplete')
    robots=context.request.get(urljoin(base,'robots.txt'))
    require(robots.status==200 and 'Disallow: /' not in robots.text(),'Project robots file blocks crawling')
    if MODE=='live':
        from urllib.robotparser import RobotFileParser
        host_robots=urljoin(SITE,'/robots.txt')
        resp=context.request.get(host_robots)
        host_record={'url':host_robots,'status':resp.status}
        if resp.status==200:
            parser=RobotFileParser(); parser.parse(resp.text().splitlines())
            host_record['allows_site']=parser.can_fetch('Googlebot',SITE)
            require(host_record['allows_site'],'Host-level robots blocks site')
        else:
            require(resp.status in (404,410),'Cannot verify host-level robots availability')
        results['checks']['host_robots']=host_record
    results['checks'].update(mobile_menu=True,service_filters=True,contact_preselection=True,keyboard_skip=True,social_image_dimensions=list(image_size),sitemap_urls=16)
    browser.close()
server.shutdown()
results['failures']=failures
results['passed']=not failures
(OUT/'results.json').write_text(json.dumps(results,indent=2))
print(json.dumps({'mode':MODE,'pages_checked':len(results['pages']),'passed':not failures,'failures':failures,'form_delivery_tested':False},indent=2))
if failures:
    raise SystemExit(1)
if MODE=='prepare':
    with zipfile.ZipFile(OUT/'site-source.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for p in ROOT.rglob('*'):
            if p.is_file() and not any(x in p.parts for x in ('.git','.github','.qa')):
                archive.write(p,p.relative_to(ROOT))
