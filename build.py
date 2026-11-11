#!/usr/bin/env python3
# build.py — GerrOS site. Reads data.json (store API) + meta.json and writes the multi-page site:
#   index.html, apps.html, apps/<slug>.html, whatsnew.html, wearos.html, studio.html,
#   support.html, privacy.html — plus dist/gerros.html: every page in one file with hash routing
#   and inlined images, for previewing.
import json, base64, os, re, html, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
data = json.load(open('data.json'))
meta = json.load(open('meta.json'))
CATS = meta['categories']
CATNAME = dict(CATS)
by_slug = {a['slug']: a for a in data}
STORE = 'https://apps.garmin.com/apps/'
DEV = 'https://apps.garmin.com/developer/de6acef4-c127-4cf2-84bc-baccde5f8b16/apps'
MAIL = 'thijsjwger@gmail.com'

# assets/local.json is written by tools_assets.py: the apps whose images come from the local store
# folder (new look) instead of the store API. It says how many marketing images and dials exist.
LOCAL = json.load(open('assets/local.json')) if os.path.exists('assets/local.json') else {}

apps = []
for slug, m in meta['apps'].items():
    a = by_slug.get(slug)
    if not a:
        continue
    # meta['show']: only the apps in the new look are on the site
    if meta.get('show') and slug not in meta['show']:
        continue
    loc = LOCAL.get(slug)
    n = loc['screens'] if loc else len(a['shots'])
    caps = (m.get('screens') or []) + [None] * n
    apps.append({
        'slug': slug, 'title': m['title'], 'tag': m['tag'], 'cat': m['cat'], 'accent': m.get('accent') or '#A9A49C',
        'pending': bool(m.get('pending')), 'id': m.get('id') or a['id'],
        'type': a['type'], 'rating': a['rating'], 'reviews': a['reviews'] or 0, 'version': a['version'],
        'desc': a['desc'], 'whatsnew': a.get('whatsnew', ''), 'changed': a.get('changed') or 0,
        'devices': a.get('devices', 0), 'updates': a.get('updates', 1),
        'cover': f'assets/covers/{slug}.jpg', 'dial': f'assets/dials/{slug}.jpg',
        'share': f'assets/heroes/{slug}.jpg' if loc and loc.get('hero') else f'assets/covers/{slug}.jpg',
        'shots': [f'assets/screens/{slug}-{i+1}.jpg' for i in range(n)],
        'dials': [f'assets/dials/{slug}-{i+1}.jpg' for i in range(n)] if loc else [],
        'main': int(loc['main']) if loc and str(loc.get('main', '')).isdigit() else 0,
        'caps': caps[:n],
    })
if meta.get('show'):
    apps.sort(key=lambda x: meta['show'].index(x['slug']))
by = {a['slug']: a for a in apps}
live = [a for a in apps if not a['pending']]
UPDATES = sum(a['updates'] for a in apps)
COUNT = {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six', 7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten', 11: 'Eleven', 12: 'Twelve'}.get(len(apps), str(len(apps)))

E = html.escape
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400..800&display=swap">'
# the GerrOS mark: a ring with a gap, like the ring round the edge of every app
MARK = '<svg class="mark" viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="22" fill="none" stroke="#131518" stroke-width="7"/><path d="M32 6a26 26 0 0 1 26 26" fill="none" stroke="#3EDC96" stroke-width="7" stroke-linecap="round"/></svg>'
ARROW = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5.5 3.5h7v7M12.5 3.5 3.5 12.5"/></svg>'

NAV_ITEMS = [('apps.html', 'Apps'), ('whatsnew.html', "What's new"), ('wearos.html', 'Wear OS'), ('studio.html', 'Studio'), ('support.html', 'Support')]

def nav(active=''):
    CUR = ' aria-current="page"'
    links = ''.join(f'<a href="{h}"{CUR if h == active else ""}>{t}</a>' for h, t in NAV_ITEMS)
    return f'''<header class="nav"><div class="wrap">
  <a class="brand" href="index.html">{MARK}GerrOS</a>
  <nav class="nav-links" aria-label="Main">{links}<a class="pill" href="custom.html"{CUR if active == 'custom.html' else ''}>Custom apps</a></nav>
  <button class="nav-toggle pill" type="button" aria-expanded="false">Menu</button>
</div></header>'''

FOOTER = f'''<footer class="footer"><div class="wrap">
  <a class="brand" href="index.html">{MARK}GerrOS</a>
  <nav aria-label="Footer"><a href="apps.html">Apps</a><a href="custom.html">Custom apps</a><a href="support.html">Support</a><a href="privacy.html">Privacy policy</a><a href="{DEV}" target="_blank" rel="noopener">Connect IQ developer page</a></nav>
  <p>© 2026 GerrOS, Den Dolder, the Netherlands. Garmin and Connect IQ are trademarks of Garmin Ltd. Wear OS is a trademark of Google LLC. GerrOS is an independent studio and is not affiliated with either.</p>
</div></footer>'''

def stars(a):
    if a['pending']:
        return 'In review'
    if not a['rating']:
        return 'No ratings yet'
    return f"{a['rating']:.1f} out of 5 from {a['reviews']} {'review' if a['reviews'] == 1 else 'reviews'}"

def state(a):
    """Short status for lists: a rating, or the reason there is none."""
    if a['pending']:
        return '<span class="state">In review at Garmin</span>'
    if not a['rating']:
        return '<span class="state">New in the store</span>'
    return f'<span class="rating"><b>{a["rating"]:.1f}</b> out of 5, {a["reviews"]} {"review" if a["reviews"] == 1 else "reviews"}</span>'

LAZY = ' loading="lazy"'
def dial(a, i=None, cls='', lazy=True):
    """The round watch screen. i = index of a marketing image; None = the app's main screen."""
    src = a['dial'] if i is None else a['dials'][i]
    cap = a['caps'][i] if i is not None else (a['caps'][a['main'] - 1] if a['main'] and a['caps'] else None)
    alt = f"{a['title']} watch screen" + (f": {cap[0]}" if cap else '')
    return f'<span class="dial{" " + cls if cls else ""}"><img src="{src}" alt="{E(alt)}" width="480" height="480"{LAZY if lazy else ""} decoding="async"></span>'

def store_link(a, cls='btn accent'):
    if a['id'] and not a['pending']:
        return f'<a class="{cls}" href="{STORE}{a["id"]}" target="_blank" rel="noopener">Open in the Connect IQ Store {ARROW}</a>'
    return ''

def first_line(text, n=150):
    t = re.sub(r'\s+', ' ', text).strip()
    if len(t) <= n:
        return t
    cut = t[:n].rsplit(' ', 1)[0].rstrip(',;:')
    return cut + '…'

# Store text → HTML: blank lines separate paragraphs, "- " lines are bullets, ALL-CAPS lines are headings.
def fmt_desc(text):
    out, lst = [], None
    def flush():
        nonlocal lst
        if lst:
            out.append('<ul>' + ''.join(f'<li>{E(l)}</li>' for l in lst) + '</ul>'); lst = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            flush(); continue
        if re.match(r'^[-•]\s+', line):
            lst = (lst or []); lst.append(re.sub(r'^[-•]\s+', '', line)); continue
        flush()
        if len(line) < 60 and line == line.upper() and re.search('[A-Z]', line):
            out.append(f'<h4>{E(line.capitalize())}</h4>'); continue   # store headings are ALL CAPS; the site uses sentence case
        if re.match(r'^(Website|Note):', line, re.I):
            continue
        out.append(f'<p>{E(line)}</p>')
    flush()
    return ''.join(out)

def date(ms):
    return datetime.date.fromtimestamp(ms / 1000).strftime('%-d %b %Y') if ms else ''


PACKAGES = [
    ('Watch face', '1–2 weeks', 'Your design or brand on the dial. Complications, colours, one platform, two revision rounds.'),
    ('App', '2–4 weeks', 'One job done properly: a calculation, timer, tracker or tool with settings and a glance. One platform.'),
    ('App + backend', '4–8 weeks', 'An app that talks to something: a server, an API, a live scoreboard or a shared ranking.'),
]
def package_cards():
    return ''.join(f'<div class="package"><h3>{E(n)}</h3><b>{E(t)}</b><p>{E(d)}</p></div>' for n, t, d in PACKAGES)

FORM_ACTION = f'https://formsubmit.co/{MAIL}'
def quote_form():
    return f'''<form class="quote-form" id="quote" action="{FORM_ACTION}" method="POST">
    <input type="hidden" name="_subject" value="Custom app request via gerros.app">
    <input type="hidden" name="_template" value="table">
    <input type="hidden" name="_captcha" value="false">
    <input type="hidden" name="_next" value="https://gerros.app/thanks.html">
    <input type="text" name="_honey" class="honey" tabindex="-1" autocomplete="off" aria-hidden="true">
    <div class="field-row">
      <label>Name<input type="text" name="name" required autocomplete="name"></label>
      <label>Email<input type="email" name="email" required autocomplete="email"></label>
    </div>
    <div class="field-row">
      <label>Club or company <span class="opt">optional</span><input type="text" name="organisation" autocomplete="organization"></label>
      <label>Platform<select name="platform"><option>Garmin (Connect IQ)</option><option>Wear OS</option><option>Both</option><option>Not sure yet</option></select></label>
    </div>
    <label>What should the app do, and for whom?<textarea name="brief" rows="5" required placeholder="The one thing it must do, who wears it, and what you tried so far."></textarea></label>
    <div class="field-row">
      <label>Watch models <span class="opt">optional</span><input type="text" name="watches" placeholder="e.g. Venu 3, Forerunner 265"></label>
      <label>Deadline <span class="opt">optional</span><input type="text" name="deadline" placeholder="e.g. before the season starts"></label>
    </div>
    <button class="btn" type="submit">Send the brief</button>
    <p class="muted small">Goes straight to {MAIL}. Reply within two working days, no obligation. Prefer mail? <a href="{MAIL_CUSTOM}">Open a pre-filled message</a>.</p>
  </form>'''

MAIL_CUSTOM = f'mailto:{MAIL}?subject=Custom%20app%20request&body=Hi%20Thijs%2C%0A%0AWhat%20I%20want%20the%20app%20to%20do%3A%20%0AWho%20it%20is%20for%3A%20%0AGarmin%20or%20Wear%20OS%3A%20%0AWatch%20model(s)%3A%20%0ADeadline%3A%20%0ABudget%20range%3A%20%0A'

# ------------------------------------------------------------------ pages
def page_home():
    cards = ''.join(f'''<a class="pick" href="apps/{a['slug']}.html" style="--accent:{a['accent']}">
      {dial(a, lazy=False)}
      <span class="pick-name">{E(a['title'])}</span>
      <span class="pick-tag">{E(a['tag'])}</span>
    </a>''' for a in apps)
    latest = sorted(live, key=lambda a: a['changed'], reverse=True)[:3]
    news = ''.join(f'''<a class="update" href="apps/{a['slug']}.html">
      {dial(a)}
      <span class="update-head"><b>{E(a['title'])} {a['version']}</b><time>{date(a['changed'])}</time></span>
      <span class="update-text">{E(first_line(a['whatsnew']) or 'First release.')}</span>
    </a>''' for a in latest)
    wear = meta['wearos']
    wear_names = ', '.join(wear[:-1]) + ' and ' + wear[-1] if len(wear) > 1 else ''.join(wear)
    return f'''
<section class="hero"><div class="wrap">
  <h1>{COUNT} apps for Garmin watches.</h1>
  <p class="lede">Each one does one job and shows the answer as one clear number. Everything runs on the watch itself: no phone, no account, no subscription.</p>
  <div class="picks">{cards}</div>
</div></section>

<section class="section"><div class="wrap">
  <div class="section-head"><h2>Latest updates</h2><a class="link" href="whatsnew.html">All release notes</a></div>
  <div class="updates">{news}</div>
</div></section>

<section class="section"><div class="wrap duo">
  <div class="panel" id="custom">
    <h2>Custom apps</h2>
    <p>Need a watch app that does not exist yet? GerrOS builds Garmin and Wear OS apps and watch faces to order, at a fixed quote.</p>
    <p class="actions"><a class="btn" href="custom.html">How it works</a><a class="btn ghost" href="custom.html#quote">Request a quote</a></p>
  </div>
  <div class="panel" id="wearos">
    <h2>Wear OS</h2>
    <p>{wear_names} are being rebuilt natively for Wear OS watches.</p>
    <p class="actions"><a class="btn ghost" href="wearos.html">Where each one stands</a></p>
  </div>
</div></section>'''

def app_row(a):
    main = a['main'] - 1 if a['main'] else -1
    minis = ''.join(f'<figure>{dial(a, i)}<figcaption>{E(a["caps"][i][0]) if a["caps"][i] else ""}</figcaption></figure>' for i in range(len(a['dials'])) if i != main)
    return f'''<article class="row" id="{a['slug']}" style="--accent:{a['accent']}">
    <a class="row-dial" href="apps/{a['slug']}.html" tabindex="-1" aria-hidden="true">{dial(a, lazy=False)}</a>
    <div class="row-body">
      <h2><a href="apps/{a['slug']}.html">{E(a['title'])}</a></h2>
      <p class="row-tag">{E(a['tag'])}</p>
      <p class="row-meta">{state(a)}</p>
      {f'<div class="minis">{minis}</div>' if minis else ''}
      <p class="actions"><a class="btn" href="apps/{a['slug']}.html">About {E(a['title'])}</a>{store_link(a, 'btn ghost')}</p>
    </div>
  </article>'''

def page_apps():
    review = len(apps) - len(live)
    where = f'{COUNT if not review else len(live)} in the Connect IQ Store' + (f', {review} in review at Garmin' if review else '')
    return f'''
<section class="page-head"><div class="wrap">
  <h1>Apps</h1>
  <p class="lede">{where}. Each one with its main screen and the pages behind it.</p>
</div></section>
<section class="rows"><div class="wrap">{''.join(app_row(a) for a in apps)}</div></section>'''

def page_app(a):
    # the image of the main screen is left out: that screen is the dial in the header
    show = [i for i in range(len(a['shots'])) if i != a['main'] - 1]
    shots = ''.join(f'<figure class="shot"><img src="{a["shots"][i]}" alt="{E(a["title"])}: {E(". ".join(a["caps"][i]) if a["caps"][i] else "screen " + str(i + 1))}" width="1536" height="1024"{LAZY if k > 1 else ""} decoding="async"></figure>' for k, i in enumerate(show))
    note = '<p class="note">Submitted to Garmin and waiting for review. The store link appears here once it is approved.</p>' if a['pending'] else ''
    facts = []
    if a['pending']:
        facts.append(('In review', 'at Garmin'))
    elif a['rating']:
        facts.append((f"{a['rating']:.1f}", f"out of 5, {a['reviews']} {'review' if a['reviews'] == 1 else 'reviews'}"))
    else:
        facts.append(('New', 'no ratings yet'))
    facts.append((a['version'], 'version' + (', ' + date(a['changed']) if a['changed'] else '')))
    if a['devices']:
        facts.append((str(a['devices']), 'Garmin watch models'))
    facts_html = ''.join(f'<div><b>{E(n)}</b><span>{E(l)}</span></div>' for n, l in facts)
    wn = f'<section class="whatsnew"><h2>New in {a["version"]}</h2>{fmt_desc(a["whatsnew"])}<p class="when">{date(a["changed"])}</p></section>' if a['whatsnew'].strip() else ''
    others = ''.join(f'<a class="other" href="apps/{b["slug"]}.html">{dial(b)}<span>{E(b["title"])}</span></a>' for b in apps if b['slug'] != a['slug'])
    return f'''
<div class="app-page" style="--accent:{a['accent']}">
<section class="apphead"><div class="wrap">
  <div class="apphead-copy">
    <a class="crumb" href="apps.html">All apps</a>
    <h1>{E(a['title'])}</h1>
    <p class="lede">{E(a['tag'])}.</p>
    <div class="facts">{facts_html}</div>
    <div class="actions">{store_link(a)}{note}</div>
  </div>
  {dial(a, cls='big', lazy=False)}
</div></section>
<section class="shots"><div class="wrap{' odd' if len(show) % 2 else ''}">{shots}</div></section>
<section class="section appbody"><div class="wrap">
  <div class="desc">{fmt_desc(a['desc'])}</div>
  <aside class="side">
    {wn}
    <dl class="kv">
      <dt>Platform</dt><dd>Garmin Connect IQ</dd>
      <dt>Type</dt><dd>{'Watch face' if a['type'] == '1' else 'Watch app'}</dd>
      <dt>Account</dt><dd>None needed</dd>
      <dt>Your data</dt><dd>Stays on the watch</dd>
      <dt>Help</dt><dd><a href="support.html">Support</a></dd>
    </dl>
    {store_link(a, 'btn ghost')}
  </aside>
</div></section>
<section class="section others"><div class="wrap">
  <h2>Other apps</h2>
  <div class="other-list">{others}</div>
</div></section>
</div>'''

def page_whatsnew():
    items = []
    for a in sorted(live, key=lambda a: a['changed'], reverse=True):
        body = fmt_desc(a['whatsnew']) if a['whatsnew'].strip() else '<p>First release.</p>'
        items.append(f'''<article class="news">
      <a class="news-dial" href="apps/{a['slug']}.html" tabindex="-1" aria-hidden="true">{dial(a)}</a>
      <div class="news-body"><h2><a href="apps/{a['slug']}.html">{E(a['title'])}</a> <span>{a['version']}</span></h2><time>{date(a['changed'])}</time>{body}</div>
    </article>''')
    return f'''
<section class="page-head"><div class="wrap">
  <h1>What's new</h1>
  <p class="lede">The latest release notes for each app, newest first.</p>
</div></section>
<section class="section flush"><div class="wrap"><div class="newslist">{''.join(items)}</div></div></section>'''

WEAR = [
    ('Caffi', 'Caffeine curve with a sleep cut-off, a tile for the watch face and a complication.', 'Tile done, complication in progress'),
    ('Sobr', 'Blood-alcohol estimate that keeps counting in the background, with alarms instead of polling.', 'App, tile and icon done, testing'),
    ('BreathGym', 'CO₂ and O₂ tables, max-hold tests and a tile that shows today\'s training.', 'App and tile done, testing'),
    ('Convertr', 'Units and live currency rates, the whole table ported one to one.', 'App done, live rates working'),
]

def page_wearos():
    rows = ''.join(f'<div class="wear-row"><h2>{n}</h2><p>{E(d)}</p><span class="state">{E(s)}</span></div>' for n, d, s in WEAR)
    return f'''
<section class="page-head"><div class="wrap">
  <h1>Wear OS</h1>
  <p class="lede">The same apps, rebuilt in Kotlin with Compose for Wear OS, with tiles and complications where they make sense and the same maths underneath. They arrive in the Play Store under the GerrOS name.</p>
</div></section>
<section class="section flush"><div class="wrap">
  <div class="wear-rows">{rows}</div>
  <p class="after">Want to hear when one is out? Mail <a href="mailto:{MAIL}?subject=Wear%20OS">{MAIL}</a> with the app name and you get one message when it is live.</p>
</div></section>'''


FAQS = [
    ('Who owns the app?', 'You do, once the final invoice is paid. Source code is available for an extra fee if you want to keep building on it yourself.'),
    ('Can it go in the Connect IQ Store or Google Play?', 'Yes. It can be published under your own developer account, or under GerrOS if you prefer. Store review is outside my control, but I build to the guidelines and have had every one of my own apps approved.'),
    ('Which watches?', 'All Garmin models that run Connect IQ, and Wear OS watches. Tell me which models matter and the quote will list exactly which ones are covered.'),
    ('What about data and privacy?', 'By default everything stays on the watch, like my own apps. If the app needs a server, that is scoped and priced separately.'),
    ('How is the price built up?', 'From the hours the brief needs: screens, features, devices and languages. You get one fixed price for the whole scope before anything is built, so the risk of overrun is mine, not yours.'),
    ('Do you do NDAs and invoices?', 'Yes. GerrOS is a registered Dutch company; you get a proper invoice, VAT reverse-charged for EU businesses.'),
]

def page_custom():
    steps = [
        ('Brief', 'Mail what the app should do, for whom, on which watches and by when. A 20-minute call if it is easier to talk.'),
        ('Quote', 'Within a few days you get a fixed price and a one-page scope: screens, features, devices, languages.'),
        ('Build', 'Half up front, then the app gets built. You see simulator screenshots and short videos along the way.'),
        ('Revise', 'Two revision rounds are included. Extra changes are quoted by the hour before they are made.'),
        ('Deliver', 'The finished app, published in the store under your name or delivered as a file to sideload. Rest of the invoice on delivery.'),
        ('Support', '30 days of bug fixes included. After that, a small monthly plan or per-hour fixes, your choice.'),
    ]
    steps_html = ''.join(f'<li><b>{E(t)}</b><span>{E(d)}</span></li>' for t, d in steps)
    faq_html = ''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in FAQS)
    fits = [
        ('Clubs and coaches', 'A club watch face, a training protocol on the watch, a score tracker for your sport with your rules.'),
        ('Companies', 'A branded watch face as merchandise, or an internal tool: a shift logger, a checklist, a timer that follows your procedure.'),
        ('Research and study', 'Collect heart rate, movement or answers on the watch and export them cleanly for analysis.'),
        ('One-off wishes', 'The app you searched the store for and never found. If it fits on a watch, it can be built.'),
        ('Ports', 'Already have a Garmin app? Bring it to Wear OS, or the other way round.'),
        ('Rescue jobs', 'An existing Connect IQ app that crashes, fails review or needs new devices. Fixed and shipped.'),
    ]
    fits_html = ''.join(f'<div><h3>{E(t)}</h3><p>{E(d)}</p></div>' for t, d in fits)
    return f'''
<section class="page-head"><div class="wrap split">
  <div>
    <h1>A watch app built to your brief.</h1>
    <p class="lede">For sports clubs, coaches, companies, researchers and people with one specific wish. If the app you need is not in the store, GerrOS builds it for Garmin Connect IQ or Wear OS, at a fixed price and a fixed scope.</p>
    <p class="lede">You work directly with the person who designed and built the apps on this site, so the Garmin quirks, the review rules and the small-screen habits are already solved.</p>
    <div class="packages">{package_cards()}</div>
    <p class="muted small">Lead times per size. Every project gets a fixed quote after the brief; a second platform or publication under your own name is added to it.</p>
  </div>
  <div class="card">
    <h2>Start with a brief</h2>
    <p class="muted">A few lines are enough. You get a fixed quote and a one-page scope back.</p>
    {quote_form()}
  </div>
</div></section>

<section class="section"><div class="wrap">
  <h2>From brief to delivery</h2>
  <ol class="steps">{steps_html}</ol>
</div></section>

<section class="section"><div class="wrap">
  <h2>What people ask for</h2>
  <div class="cols">{fits_html}</div>
</div></section>

<section class="section"><div class="wrap">
  <h2>Practical questions</h2>
  <div class="faq">{faq_html}</div>
  <p class="actions"><a class="btn" href="#quote">Request a quote</a><a class="btn ghost" href="studio.html">About the studio</a></p>
</div></section>'''

def page_thanks():
    return f'''
<section class="page-head"><div class="wrap">
  <h1>Your brief is sent.</h1>
  <p class="lede">You hear back within two working days with a fixed quote and a one-page scope, or a couple of questions first if the brief needs them.</p>
  <p class="actions"><a class="btn" href="apps.html">See the apps</a><a class="btn ghost" href="index.html">Back to the homepage</a></p>
</div></section>'''

def page_studio():
    made = [
        ('Built for a glance', 'A watch is read in half a second. Each app leads with the one number that matters and keeps the rest a swipe away.'),
        ('Real arithmetic inside', 'A caffeine curve, a blood-alcohol estimate that knows when you are sober, a fasting clock that knows your window, a cycle forecast. The apps plan and predict; they do not only count.'),
        ('Yours stays on the watch', 'No accounts, no cloud, no tracking. Your data lives on the device, and every app works without a phone nearby.'),
        ('Buttons and touch', 'Every app works on a touch screen and with the buttons alone, and every menu is a page with large buttons.'),
        ('Kept alive', f'Reviews get a reply and bugs get fixed. The apps on this site have had {UPDATES} versions between them so far.'),
    ]
    made_html = ''.join(f'<div><h3>{E(t)}</h3><p>{E(d)}</p></div>' for t, d in made)
    return f'''
<section class="page-head"><div class="wrap split">
  <div>
    <h1>A one-person studio in the Netherlands.</h1>
    <p class="lede">GerrOS is run by Thijs Gerritsen from Den Dolder. Every app starts as something he wanted on his own watch, gets built end to end, and is then kept up: reviews are answered, bugs are fixed and features arrive in updates.</p>
    <p class="lede">It began with a score tracker for padel. The {COUNT.lower()} apps on this site are the ones rebuilt in the current design: one typeface, large clear numbers, a ring round the edge and every menu as a page with big buttons.</p>
  </div>
  <div class="card">
    <h2>Get in touch</h2>
    <dl class="kv"><dt>Mail</dt><dd><a href="mailto:{MAIL}">{MAIL}</a></dd><dt>Store</dt><dd><a href="{DEV}" target="_blank" rel="noopener">ThijsGer on Connect IQ</a></dd><dt>Based in</dt><dd>Den Dolder, the Netherlands</dd></dl>
    <p class="muted">Bug, idea or question? Mail with the app name and your watch model, and you hear back from the person who wrote the code.</p>
  </div>
</div></section>

<section class="section"><div class="wrap">
  <h2>How the apps are made</h2>
  <div class="cols">{made_html}</div>
</div></section>'''

def page_support():
    return f'''
<main class="prose"><div class="wrap">
  <h1>Support</h1>
  <p class="lede">Something not working? Mail <a href="mailto:{MAIL}">{MAIL}</a> with the name of the app, your watch model and what happened. Screenshots help.</p>
  <p>You hear back from the developer, usually within a few days, and fixes ship as app updates through the Connect IQ Store.</p>
  <h2>Before you write</h2>
  <ul>
    <li><b>App will not open or shows an IQ! symbol:</b> update the app in the Connect IQ app on your phone, then restart the watch. If it keeps happening, mail the watch model and the app version.</li>
    <li><b>Glance shows nothing:</b> open the app once so it has data to show, then check the glance again. Updated versions of all apps show a summary even before first use.</li>
    <li><b>Buttons instead of touch:</b> every app can be operated with the physical buttons. START selects or confirms, BACK goes back or opens the menu, UP and DOWN scroll.</li>
    <li><b>Settings from the phone:</b> some apps can be configured in the Connect IQ app under the app's settings. Changes arrive on the watch within a minute.</li>
    <li><b>Refunds:</b> purchases are handled by Garmin. Refund requests go through Garmin support, not through GerrOS.</li>
  </ul>
  <h2>Feature requests</h2>
  <p>Most features in the apps came from people writing in. If something would make an app more useful for you, say so, and mention what you would use it for.</p>
</div></main>'''

def page_privacy():
    return f'''
<main class="prose"><div class="wrap">
  <h1>Your data stays on your watch.</h1>
  <p class="updated">Privacy policy for all GerrOS apps, last updated 6 September 2026</p>
  <p>GerrOS builds apps for Garmin (Connect IQ) and, soon, Wear OS watches. This policy explains what the apps do with your data. The short version: they keep it on the device and do not send it to us.</p>
  <h2>What the apps store</h2>
  <p>Everything you enter (expenses, shifts, fasting windows, lists, talks, race results, settings) is saved in the app's own storage on the watch. Some apps read data the watch already has, such as heart rate, steps, calories, barometric pressure, GPS position or the weather, to do their job. That data is processed on the watch and is not transmitted to GerrOS.</p>
  <h2>What we do not do</h2>
  <ul>
    <li>No accounts, no sign-in, no e-mail address required.</li>
    <li>No analytics, no advertising, no tracking of any kind.</li>
    <li>No servers operated by GerrOS receive personal data from the apps.</li>
  </ul>
  <h2>Apps that use the internet</h2>
  <ul>
    <li><b>Convertr</b> fetches current exchange rates from a public rates service. The request contains no personal data.</li>
    <li><b>RallyPoint</b> can show a live scoreboard on a web page if you switch that on. Only the scores and player names you entered are sent, to a page identified by a code you choose. Leave the feature off and nothing is sent.</li>
  </ul>
  <h2>Purchases</h2>
  <p>Paid apps are sold through the Garmin Connect IQ Store. Garmin handles the payment; GerrOS never sees your payment details. Garmin's own privacy policy applies to the store and to your Garmin account.</p>
  <h2>Deleting your data</h2>
  <p>Uninstall the app from your watch and its data is gone. Most apps also offer a "clear" or "reset" option in their settings.</p>
  <h2>Contact</h2>
  <p>Questions about privacy: <a href="mailto:{MAIL}">{MAIL}</a>. GerrOS is a sole proprietorship registered in the Netherlands.</p>
</div></main>'''

# ------------------------------------------------------------------ assemble
SITE = 'https://gerros.app/'
ORG = {"@type": "Organization", "@id": SITE + "#org", "name": "GerrOS", "url": SITE, "logo": SITE + "assets/brand/gerros-icon-512.png",
       "email": MAIL, "founder": {"@type": "Person", "name": "Thijs Gerritsen"},
       "address": {"@type": "PostalAddress", "addressLocality": "Den Dolder", "addressCountry": "NL"},
       "sameAs": [DEV],
       "description": "Independent one-person studio from the Netherlands that publishes Garmin Connect IQ apps and watch faces and builds custom Garmin and Wear OS apps to order."}
def jsonld(*objs):
    return ''.join('<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False) + '</script>\n' for o in objs if o)

def document(title, desc, body, active='', depth=0, path='', image=None, ld=(), noindex=False):
    pre = '../' * depth
    canon = SITE + (path if path != 'index.html' else '')
    image = SITE + (image or (apps[0]['share'] if apps else 'assets/brand/gerros-icon-512.png'))
    head = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canon}">
{'<meta name="robots" content="noindex,follow">' if noindex else '<meta name="robots" content="index,follow,max-image-preview:large">'}
<meta name="theme-color" content="#FAF6F3">
<meta property="og:site_name" content="GerrOS">
<meta property="og:type" content="website">
<meta property="og:url" content="{canon}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:image" content="{image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{E(title)}">
<meta name="twitter:description" content="{E(desc)}">
<meta name="twitter:image" content="{image}">
<link rel="icon" href="{pre}assets/favicon.svg" type="image/svg+xml">
{FONTS}
<link rel="stylesheet" href="{pre}style.css">
{jsonld(ORG, *ld)}</head>
<body>'''
    doc = head + nav(active) + body + FOOTER + f'\n<script src="{pre}site.js"></script>\n</body></html>'
    if depth:
        # pages in a subfolder: every relative link and asset gets the ../ prefix
        doc = re.sub(r'(href|src)="(?!https?:|mailto:|data:|#|/|\.\./)([^"]+)"', lambda m: f'{m.group(1)}="{pre}{m.group(2)}"', doc)
        doc = doc.replace("url('assets/", f"url('{pre}assets/")
    return doc

PAGES = [
    ('index.html', 'GerrOS · Garmin Connect IQ apps and custom watch-app development', 'GerrOS makes apps for Garmin watches (' + ', '.join(a['title'] for a in apps) + ') and builds custom Garmin and Wear OS apps to order. Independent studio from the Netherlands.', page_home, ''),
    ('apps.html', 'All GerrOS apps for Garmin watches', 'The GerrOS apps for Garmin watches (' + ', '.join(a['title'] for a in apps) + '), each with its screens, the full description and the store link.', page_apps, 'apps.html'),
    ('whatsnew.html', "What's new at GerrOS", 'Latest release notes for every GerrOS app.', page_whatsnew, 'whatsnew.html'),
    ('wearos.html', 'GerrOS on Wear OS', 'GerrOS apps coming to Wear OS: Caffi, Sobr, BreathGym and Convertr.', page_wearos, 'wearos.html'),
    ('custom.html', 'Custom Garmin Connect IQ and Wear OS app development · GerrOS', 'Hire a Garmin Connect IQ developer: custom apps, data fields and watch faces for Garmin and Wear OS, built to order at a fixed quote by an independent studio with its own apps in the Connect IQ Store.', page_custom, 'custom.html'),
    ('studio.html', 'About GerrOS, Garmin watch-app studio', 'GerrOS is a one-person Garmin Connect IQ and Wear OS studio in Den Dolder, the Netherlands, run by Thijs Gerritsen.', page_studio, 'studio.html'),
    ('support.html', 'GerrOS support', 'Help with GerrOS apps for Garmin watches.', page_support, 'support.html'),
    ('thanks.html', 'Thanks', 'Your custom app brief has been sent to GerrOS.', page_thanks, 'custom.html'),
    ('privacy.html', 'GerrOS privacy policy', 'How GerrOS apps handle your data: on the watch, without accounts or tracking.', page_privacy, ''),
]
os.makedirs('apps', exist_ok=True)
bodies = {}
actives = {}
def app_ld(a):
    o = {"@type": "SoftwareApplication", "name": a['title'], "url": SITE + f"apps/{a['slug']}.html",
         "applicationCategory": "HealthApplication" if a['cat'] == 'health' else "SportsApplication" if a['cat'] == 'sport' else "FinanceApplication" if a['cat'] == 'money' else "GameApplication" if a['cat'] == 'games' else "UtilitiesApplication",
         "operatingSystem": "Garmin Connect IQ", "description": a['tag'], "image": SITE + a['cover'],
         "screenshot": [SITE + x for x in a['shots']], "softwareVersion": a['version'], "inLanguage": ["en", "nl", "de", "fr", "es"],
         "author": {"@id": SITE + "#org"}, "publisher": {"@id": SITE + "#org"}}
    if a['id'] and not a['pending']:
        o["installUrl"] = STORE + a['id']; o["sameAs"] = STORE + a['id']
    if a['rating'] and a['reviews']:
        o["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": round(a['rating'], 1), "reviewCount": a['reviews'], "bestRating": 5}
    return o
def crumbs(*items):
    return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(items)]}
PAGE_LD = {
    'index.html': [{"@type": "WebSite", "name": "GerrOS", "url": SITE, "publisher": {"@id": SITE + "#org"}}],
    'apps.html': [{"@type": "ItemList", "name": "GerrOS apps for Garmin watches", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": SITE + f"apps/{a['slug']}.html", "name": a['title']} for i, a in enumerate(apps)]}],
    'custom.html': [{"@type": "Service", "name": "Custom Garmin Connect IQ and Wear OS app development", "serviceType": "Software development",
                     "provider": {"@id": SITE + "#org"}, "areaServed": "Worldwide", "url": SITE + "custom.html",
                     "description": "Garmin Connect IQ apps, data fields and watch faces, and Wear OS apps, built to order at a fixed quote by an independent studio with its own apps in the Connect IQ Store.",
                     "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Packages", "itemListElement": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": n, "description": d}} for n, t, d in PACKAGES]}},
                    {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQS]}],
}
for fn, title, desc, fnc, active in PAGES:
    bodies[fn] = fnc(); actives[fn] = active
    open(fn, 'w').write(document(title, desc, bodies[fn], active, path=fn, ld=PAGE_LD.get(fn, ()), noindex=(fn == 'thanks.html')))
for a in apps:
    body = page_app(a)
    fn = f'apps/{a["slug"]}.html'
    bodies[fn] = body; actives[fn] = 'apps.html'
    kind = 'watch face' if a['type'] == '1' else 'app'
    open(fn, 'w').write(document(f'{a["title"]} · Garmin {kind} by GerrOS', f'{a["tag"]}. {a["title"]} is a Garmin Connect IQ {kind} by GerrOS: runs on the watch, no phone or account needed.', body, 'apps.html', depth=1,
                                 path=fn, image=a['share'], ld=[app_ld(a), crumbs(('GerrOS', ''), ('Apps', 'apps.html'), (a['title'], fn))]))

# ---- robots.txt, sitemap.xml, llms.txt
today = datetime.date.today().isoformat()
open('robots.txt', 'w').write('''# gerros.app — everyone welcome, including AI crawlers.
User-agent: *
Allow: /
Disallow: /thanks.html
Disallow: /dist/

User-agent: GPTBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-User
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: anthropic-ai
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Perplexity-User
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Applebot-Extended
Allow: /
User-agent: CCBot
Allow: /
User-agent: Amazonbot
Allow: /
User-agent: meta-externalagent
Allow: /

Sitemap: https://gerros.app/sitemap.xml
''')
urls = [('', today, '1.0'), ('custom.html', today, '0.9'), ('apps.html', today, '0.9'), ('whatsnew.html', today, '0.6'), ('wearos.html', today, '0.5'), ('studio.html', today, '0.6'), ('support.html', today, '0.4'), ('privacy.html', today, '0.2')]
urls += [(f"apps/{a['slug']}.html", datetime.date.fromtimestamp(a['changed'] / 1000).isoformat() if a['changed'] else today, '0.7') for a in apps]
open('sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    ''.join(f'  <url><loc>{SITE}{u}</loc><lastmod>{d}</lastmod><priority>{pr}</priority></url>\n' for u, d, pr in urls) + '</urlset>\n')
def plain(t):
    return re.sub(r'\s+', ' ', t).strip()
llms = ['# GerrOS', '', '> GerrOS is an independent one-person studio in Den Dolder, the Netherlands, run by Thijs Gerritsen. It publishes apps for Garmin watches (Connect IQ) and builds custom Garmin Connect IQ and Wear OS apps to order at a fixed quote.', '',
        'Contact: %s · Custom app requests: %scustom.html · Connect IQ developer page: %s' % (MAIL, SITE, DEV), '',
        '## Custom app development (the service)', '',
        '- Builds Garmin Connect IQ apps, data fields, widgets and watch faces, and Wear OS (Kotlin/Compose) apps, for sports clubs, coaches, companies, researchers and individuals.',
        '- Fixed scope and fixed quote after a short brief; typical lead times: watch face 1-2 weeks, app 2-4 weeks, app with backend 4-8 weeks.',
        '- Process: brief → quote and one-page scope → 50% up front → build with simulator previews → two revision rounds → delivery (store publication under the client name or sideload file) → 30 days of bug fixes.',
        '- Also takes rescue jobs (existing Connect IQ apps that crash, fail review or need new devices) and ports between Garmin and Wear OS.',
        '- Request a quote: %scustom.html#quote' % SITE, '', '## FAQ', '']
llms += ['**%s** %s' % (q, a) for q, a in FAQS]
llms += ['', '## Apps (%d, all run on the watch without a phone, account or subscription)' % len(apps), '']
for a in apps:
    st = 'in review' if a['pending'] else ('%.1f/5 from %d reviews' % (a['rating'], a['reviews']) if a['rating'] and a['reviews'] else 'in the Connect IQ Store')
    llms.append('- [%s](%sapps/%s.html): %s. %s, version %s%s.' % (a['title'], SITE, a['slug'], a['tag'], CATNAME[a['cat']], a['version'], (', store: ' + STORE + a['id']) if a['id'] else '') + (' Rating ' + st + '.' if not a['pending'] else ' Status: in review.'))
llms += ['', '## Pages', '', '- [Home](%s)' % SITE, '- [All apps](%sapps.html)' % SITE, '- [Custom apps](%scustom.html)' % SITE, '- [What\'s new](%swhatsnew.html)' % SITE, '- [Wear OS](%swearos.html)' % SITE, '- [Studio](%sstudio.html)' % SITE, '- [Support](%ssupport.html)' % SITE, '- [Privacy](%sprivacy.html)' % SITE, '']
open('llms.txt', 'w').write('\n'.join(llms))

open('assets/favicon.svg', 'w').write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="22" fill="none" stroke="#131518" stroke-width="7"/><path d="M32 6a26 26 0 0 1 26 26" fill="none" stroke="#3EDC96" stroke-width="7" stroke-linecap="round"/></svg>')

# ------------------------------------------------------------------ single-file preview with hash routing
def route_of(fn):
    if fn == 'index.html': return '/'
    if fn.startswith('apps/'): return '/app/' + fn[5:-5]
    return '/' + fn[:-5]
sections = ''.join(f'<main class="route" data-route="{route_of(fn)}" hidden>{nav(actives[fn])}{b}</main>' for fn, b in bodies.items())
single = re.sub(r'href="((?:\.\./)?)((?:apps/[a-z0-9-]+|index|apps|whatsnew|wearos|custom|thanks|studio|support|privacy)\.html)(#[a-z]+)?"',
                lambda m: f'href="#{route_of(m.group(2))}"', sections)
cache = {}
def uri(path):
    if path not in cache:
        p = path.replace('assets/covers/', 'assets/small/').replace('assets/screens/', 'assets/small/').replace('assets/dials/', 'assets/small/dial-')
        cache[path] = 'data:image/jpeg;base64,' + base64.b64encode(open(p, 'rb').read()).decode()
    return cache[path]
single = re.sub(r'(src="|url\(\')(assets/[a-z]+/[a-z0-9-]+\.jpg)', lambda m: m.group(1) + uri(m.group(2)), single)
css = open('style.css').read()
js = open('site.js').read()
HREF = r'href="((?:\.\./)?)((?:apps/[a-z0-9-]+|index|apps|whatsnew|wearos|custom|thanks|studio|support|privacy)\.html)(#[a-z]+)?"'
footer1 = re.sub(HREF, lambda m: f'href="#{route_of(m.group(2))}"', FOOTER)
out = f'<!doctype html>\n<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n<title>GerrOS</title>\n{FONTS}\n<style>{css}</style>\n{single}{footer1}\n<script>{js}</script>'
os.makedirs('dist', exist_ok=True)
open('dist/gerros.html', 'w').write(out)
print(f'{len(PAGES)} pages + {len(apps)} app pages · preview {len(out) // 1024 // 1024} MB · {len(live)} live · {UPDATES} versions')
