#!/usr/bin/env python3
# build.py — GerrOS site. Reads data.json (store API) + meta.json and writes the multi-page site:
#   index.html, apps.html, apps/<slug>.html, finder.html, whatsnew.html, wearos.html, studio.html,
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

apps = []
for slug, m in meta['apps'].items():
    a = by_slug.get(slug)
    if not a:
        continue
    apps.append({
        'slug': slug, 'title': m['title'], 'tag': m['tag'], 'cat': m['cat'],
        'pending': bool(m.get('pending')), 'id': m.get('id') or a['id'],
        'type': a['type'], 'rating': a['rating'], 'reviews': a['reviews'] or 0, 'version': a['version'],
        'desc': a['desc'], 'whatsnew': a.get('whatsnew', ''), 'changed': a.get('changed') or 0,
        'devices': a.get('devices', 0), 'updates': a.get('updates', 1),
        'cover': f'assets/covers/{slug}.jpg', 'dial': f'assets/dials/{slug}.jpg',
        'shots': [f'assets/screens/{slug}-{i+1}.jpg' for i in range(len(a['shots']))],
    })
by = {a['slug']: a for a in apps}
live = [a for a in apps if not a['pending']]
rated = [a for a in live if a['rating']]
AVG = sum(a['rating'] for a in rated) / len(rated)
REVIEWS = sum(a['reviews'] for a in live)
UPDATES = sum(a['updates'] for a in apps)
DEVICES = 207   # union of compatible device types across all apps (from the store API)

E = html.escape
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..800&family=Hanken+Grotesk:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">'

NAV_ITEMS = [('apps.html', 'Apps'), ('finder.html', 'Find your app'), ('whatsnew.html', "What's new"), ('wearos.html', 'Wear OS'), ('custom.html', 'Custom apps'), ('studio.html', 'Studio'), ('support.html', 'Support')]

def nav(active=''):
    CUR = ' aria-current="page"'
    links = ''.join(f'<a href="{h}"{CUR if h == active else ""}>{t}</a>' for h, t in NAV_ITEMS)
    return f'''<header class="nav"><div class="wrap">
  <a class="brand" href="index.html"><span class="mark" aria-hidden="true"></span>GerrOS</a>
  <nav class="nav-links">{links}</nav>
  <button class="nav-toggle" type="button" aria-label="Menu">☰</button>
</div></header>'''

FOOTER = f'''<footer class="footer"><div class="wrap">
  <div>© 2026 GerrOS · Den Dolder, the Netherlands</div>
  <div><a href="privacy.html">Privacy policy</a> &nbsp;·&nbsp; <a href="support.html">Support</a> &nbsp;·&nbsp; <a href="{DEV}" target="_blank" rel="noopener">Connect IQ developer page</a></div>
  <small>Garmin and Connect IQ are trademarks of Garmin Ltd. Wear OS is a trademark of Google LLC. GerrOS is an independent studio and is not affiliated with either.</small>
</div></footer>'''

def stars(a):
    if a['pending'] or not a['rating']:
        return 'In review'
    return f"★ {a['rating']:.1f} · {a['reviews']} {'review' if a['reviews'] == 1 else 'reviews'}"

def tile(a):
    badge = '<span class="badge">In review</span>' if a['pending'] else ''
    return f'''<a class="tile" href="apps/{a['slug']}.html">
      <span class="cover">{badge}<img src="{a['cover']}" alt="" loading="lazy" width="360" height="360"></span>
      <span class="name">{E(a['title'])}</span>
      <span class="sub">{'In review' if a['pending'] or not a['rating'] else '★ %.1f' % a['rating']}</span>
    </a>'''

def card(a):
    badge = '<span class="badge">In review</span>' if a['pending'] else ''
    face = '<span class="face">Watch face</span>' if a['type'] == '1' else ''
    return f'''<a class="app" href="apps/{a['slug']}.html" data-cat="{a['cat']}">
      <span class="cover">{badge}{face}<img src="{a['cover']}" alt="" loading="lazy" width="500" height="500"></span>
      <h3>{E(a['title'])}</h3>
      <p class="tag">{E(a['tag'])}</p>
      <p class="meta">{stars(a)}</p>
    </a>'''

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
            out.append(f'<h4>{E(line)}</h4>'); continue
        if re.match(r'^(Website|Note):', line, re.I):
            continue
        out.append(f'<p>{E(line)}</p>')
    flush()
    return ''.join(out)

def date(ms):
    return datetime.date.fromtimestamp(ms / 1000).strftime('%-d %b %Y') if ms else ''


PACKAGES = [
    ('Watch face', 'from €350', '1–2 weeks', 'Your design or brand on the dial. Complications, colours, one platform, two revision rounds.'),
    ('App', 'from €900', '2–4 weeks', 'One job done properly: a calculation, timer, tracker or tool with settings and a glance. One platform.'),
    ('App + backend', 'from €2,500', '4–8 weeks', 'An app that talks to something: a server, an API, a live scoreboard or a shared ranking.'),
]
def package_cards():
    return ''.join(f'<div class="package"><p class="eyebrow">{E(n)}</p><b class="price">{E(pr)}</b><span class="mono muted">{E(t)}</span><p>{E(d)}</p></div>' for n, pr, t, d in PACKAGES)

MAIL_CUSTOM = f'mailto:{MAIL}?subject=Custom%20app%20request&body=Hi%20Thijs%2C%0A%0AWhat%20I%20want%20the%20app%20to%20do%3A%20%0AWho%20it%20is%20for%3A%20%0AGarmin%20or%20Wear%20OS%3A%20%0AWatch%20model(s)%3A%20%0ADeadline%3A%20%0ABudget%20range%3A%20%0A'

# ------------------------------------------------------------------ pages
def page_home():
    dials = ''.join(f'<span class="dial" style="background-image:url(\'{by[s]["dial"]}\')" title="{E(by[s]["title"])}"></span>' for s in meta['hero'])
    strip = ''.join(tile(a) for a in apps)
    latest = sorted(live, key=lambda a: a['changed'], reverse=True)[:3]
    news = ''.join(f'<a class="news-mini" href="apps/{a["slug"]}.html"><span class="cover-dial" style="background-image:url(\'{a["dial"]}\')"></span><span><b>{E(a["title"])} {a["version"]}</b><span class="mono">{date(a["changed"])}</span></span></a>' for a in latest)
    return f'''
<section class="hero"><div class="wrap">
  <div class="hero-copy">
    <p class="eyebrow">GerrOS · independent watch-app studio</p>
    <h1>Apps that earn their place on your <em>wrist</em>.</h1>
    <p class="lede">Small, focused tools for Garmin watches: a budget that knows what you can still spend today, a shift that pays out per second, a race predictor, a chess clock. Everything runs on the watch itself. No phone, no account, no subscription.</p>
    <div class="hero-actions"><a class="btn" href="apps.html">Browse the apps</a><a class="btn ghost" href="finder.html">Find the one for you</a></div>
  </div>
  <div class="dials" aria-hidden="true">{dials}<span class="dial-tag">Six of the {len(apps)} apps</span></div>
</div></section>

<section class="stats"><div class="wrap">
  <div class="stat"><b>{len(live)}</b><span>apps in the Connect IQ Store</span></div>
  <div class="stat"><b>{AVG:.1f}</b><span>average rating out of 5</span></div>
  <div class="stat"><b>{REVIEWS}</b><span>reviews from wearers</span></div>
  <div class="stat"><b>5</b><span>languages in every app</span></div>
</div></section>

<section class="section apps-strip" id="apps">
  <div class="wrap section-head"><div><p class="eyebrow">Catalogue</p><h2>{len(apps)} apps, one tap from the store.</h2></div><a class="btn ghost" href="apps.html">All apps and categories →</a></div>
  <div class="strip-outer">
    <button class="strip-arrow prev" type="button" aria-label="Scroll left">‹</button>
    <div class="strip">{strip}</div>
    <button class="strip-arrow next" type="button" aria-label="Scroll right">›</button>
  </div>
</section>

<section class="section split" id="how"><div class="wrap">
  <div><p class="eyebrow">How they are made</p><h2>One screen, one number, no noise.</h2>
  <p class="lede" style="margin-top:14px">A watch is read in half a second. Each app leads with the one number that matters, does real arithmetic underneath, and keeps your data on the device.</p>
  <p style="margin-top:18px"><a class="btn ghost" href="studio.html">About the studio →</a></p></div>
  <div class="news-block"><p class="eyebrow">Latest updates</p>{news}<a class="more" href="whatsnew.html">All release notes →</a></div>
</div></section>

<section class="section custom" id="custom"><div class="wrap">
  <div class="section-head"><div><p class="eyebrow">Custom apps</p><h2>Need one that does not exist yet?</h2></div><a class="btn ghost" href="custom.html">How it works →</a></div>
  <p class="lede">GerrOS also builds watch apps and watch faces to order, for clubs, coaches, companies and people with a very specific wish. Fixed price, fixed scope, built by the same person who shipped the {len(apps)} apps above.</p>
  <div class="packages">{package_cards()}</div>
  <p class="hero-actions"><a class="btn" href="{MAIL_CUSTOM}">Request a quote</a><a class="btn ghost" href="custom.html">Packages, process and FAQ</a></p>
</div></section>

<section class="section wear" id="wearos"><div class="wrap">
  <div><p class="eyebrow">Next</p><h2>Coming to Wear OS.</h2><p class="lede" style="margin-top:14px">The same apps, rebuilt natively in Kotlin for Wear OS watches. The first four are in development.</p><p style="margin-top:18px"><a class="btn ghost" href="wearos.html">The roadmap →</a></p></div>
  <div class="wear-list">{''.join(f'<div>{n}<span>in development</span></div>' for n in meta['wearos'])}</div>
</div></section>'''

def page_apps():
    chips = '<button class="chip" data-cat="all" aria-pressed="true">All apps</button>' + ''.join(
        f'<button class="chip" data-cat="{k}" aria-pressed="false">{v}</button>' for k, v in CATS)
    return f'''
<section class="section"><div class="wrap">
  <div class="section-head"><div><p class="eyebrow">Catalogue</p><h1 class="h2">Every app, one tap from the store.</h1></div><p class="lede">{len(live)} in the Connect IQ Store, {len(apps) - len(live)} in review. Tap one for screenshots, the full story and the store link.</p></div>
  <div class="filters" id="filters">{chips}</div>
  <div class="grid" id="grid">{''.join(card(a) for a in apps)}</div>
</div></section>'''

def page_app(a):
    hero = f'<img class="app-hero" src="{a["shots"][0]}" alt="{E(a["title"])}" width="1536" height="1024">' if a['shots'] else ''
    rest = ''.join(f'<img src="{s}" alt="{E(a["title"])} screenshot {i+2}" loading="lazy" width="1536" height="1024">' for i, s in enumerate(a['shots'][1:]))
    link = (f'<a class="btn accent" href="{STORE}{a["id"]}" target="_blank" rel="noopener">Open in the Connect IQ Store <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 3h8v8M13 3 3 13"/></svg></a>' if a['id'] else '')
    note = '<p class="note">Submitted to Garmin and awaiting review. The store page opens once it is approved.</p>' if a['pending'] else ''
    related = [b for b in apps if b['cat'] == a['cat'] and b['slug'] != a['slug']][:4]
    wn = f'<section class="whatsnew"><h3>What\'s new in {a["version"]}</h3>{fmt_desc(a["whatsnew"])}<p class="mono muted">{date(a["changed"])}</p></section>' if a['whatsnew'].strip() else ''
    return f'''
<section class="apphead"><div class="wrap">
  <a class="crumb" href="apps.html">← All apps</a>
  <div class="apphead-row">
    <span class="cover-dial big" style="background-image:url('{a['dial']}')"></span>
    <div>
      <p class="eyebrow">{E(CATNAME[a['cat']])} · {'Watch face' if a['type'] == '1' else 'Device app'}</p>
      <h1>{E(a['title'])}</h1>
      <p class="lede">{E(a['tag'])}.</p>
      <p class="meta mono">{stars(a)}{'' if a['pending'] else ' · version ' + a['version']}</p>
    </div>
    <div class="apphead-cta">{link}{note}</div>
  </div>
</div></section>
<section class="gallery-wrap"><div class="wrap">{hero}<div class="gallery-grid">{rest}</div></div></section>
<section class="section appbody"><div class="wrap">
  <div class="desc">{fmt_desc(a['desc'])}</div>
  <aside class="sheet-side">
    <div class="kv">
      <span>Platform</span><b>Garmin Connect IQ</b>
      <span>Type</span><b>{'Watch face' if a['type'] == '1' else 'Device app'}</b>
      <span>Version</span><b>{a['version']}</b>
      <span>Watches</span><b>{a['devices'] or '—'} models</b>
      <span>Languages</span><b>EN · NL · DE · FR · ES</b>
      <span>Account</span><b>None needed</b>
      <span>Data</span><b>Stays on the watch</b>
    </div>
    {wn}
  </aside>
</div></section>
<section class="section related"><div class="wrap">
  <p class="eyebrow">More in {E(CATNAME[a['cat']])}</p>
  <div class="grid">{''.join(card(b) for b in related)}</div>
</div></section>'''

GOALS = [
    ('Keep my money in check', 'money', ['spent', 'shiftpay', 'pitstop']),
    ('Run a faster race', 'run', ['racecast', 'speedometer-pro', 'reactr']),
    ('Quit, cut down or drink smarter', 'habits', ['smokeless', 'sobr', 'caffi']),
    ('Fast, breathe and sleep better', 'body', ['fasted', 'breathgym', 'jetshift', 'caffi']),
    ('Keep score in a game', 'games', ['rallypoint', 'strike', 'zeitnot']),
    ('Remember things', 'memory', ['remindersplus', 'listo', 'cardvault']),
    ('Travel and get outdoors', 'travel', ['jetshift', 'altizone', 'spotsave', 'convertr']),
    ('Stand on a stage', 'stage', ['podium', 'morsetap']),
    ('See what my body does', 'insight', ['earned', 'caffi', 'sobr', 'breathgym']),
    ('Give my watch a new face', 'faces', ['wordclock', 'redline', 'triptych']),
]

def page_finder():
    goals = ''.join(f'<button class="goal" type="button" data-goal="{k}">{E(t)}</button>' for t, k, _ in GOALS)
    results = ''.join(f'<div class="goal-result" data-goal="{k}" hidden><div class="grid">{"".join(card(by[s]) for s in slugs if s in by)}</div></div>' for _, k, slugs in GOALS)
    return f'''
<section class="section finder"><div class="wrap">
  <p class="eyebrow">Find your app</p>
  <h1 class="h2">What do you want from your watch?</h1>
  <p class="lede">Pick one. You get the two or three apps that do exactly that, nothing else.</p>
  <div class="goals" id="goals">{goals}</div>
  <div id="goal-results">{results}<p class="goal-empty" id="goal-empty">Tap a goal above.</p></div>
</div></section>'''

def page_whatsnew():
    items = []
    for a in sorted(live, key=lambda a: a['changed'], reverse=True):
        body = fmt_desc(a['whatsnew']) if a['whatsnew'].strip() else '<p>First release.</p>'
        items.append(f'''<article class="news">
      <div class="news-when mono">{date(a['changed'])}</div>
      <a class="cover-dial" href="apps/{a['slug']}.html" style="background-image:url('{a['dial']}')" aria-label="{E(a['title'])}"></a>
      <div class="news-body"><h3><a href="apps/{a['slug']}.html">{E(a['title'])}</a> <span class="mono">{a['version']}</span></h3>{body}</div>
    </article>''')
    return f'''
<section class="section"><div class="wrap">
  <p class="eyebrow">What's new</p>
  <h1 class="h2">Release notes, straight from the store.</h1>
  <p class="lede">{UPDATES} versions shipped across {len(apps)} apps. The latest change per app, newest first.</p>
  <div class="newslist">{''.join(items)}</div>
</div></section>'''

WEAR = [
    ('Caffi', 'Caffeine curve with a sleep cut-off, a tile for the watch face and a complication.', 'Tile done · complication in progress'),
    ('Sobr', 'Blood-alcohol estimate that keeps counting in the background, with alarms instead of polling.', 'App, tile and icon done · testing'),
    ('BreathGym', 'CO₂ and O₂ tables, max-hold tests and a tile that shows today\'s training.', 'App and tile done · testing'),
    ('Convertr', 'Units and live currency rates, the whole table ported one to one.', 'App done · live rates working'),
]

def page_wearos():
    rows = ''.join(f'<div class="wear-row"><div><h3>{n}</h3><p>{E(d)}</p></div><span class="mono">{E(s)}</span></div>' for n, d, s in WEAR)
    return f'''
<section class="section"><div class="wrap">
  <p class="eyebrow">Wear OS</p>
  <h1 class="h2">The same apps, native on Wear OS.</h1>
  <p class="lede">Every GerrOS app started on Garmin. The Wear OS versions are not ports of a port: each one is rebuilt in Kotlin with Compose for Wear OS, with tiles and complications where they make sense, and the same maths underneath. They will arrive in the Play Store under the GerrOS name.</p>
  <div class="wear-rows">{rows}</div>
  <p class="lede" style="margin-top:32px">Want to hear when one lands? Mail <a href="mailto:{MAIL}?subject=Wear%20OS">{MAIL}</a> with the app name and you get one message when it is live.</p>
</div></section>'''


def page_custom():
    steps = [
        ('Brief', 'Mail what the app should do, for whom, on which watches and by when. A 20-minute call if it is easier to talk.'),
        ('Quote', 'Within a few days you get a fixed price and a one-page scope: screens, features, devices, languages.'),
        ('Build', 'Half up front, then the app gets built. You see simulator screenshots and short videos along the way.'),
        ('Revise', 'Two revision rounds are included. Extra changes are quoted by the hour before they are made.'),
        ('Deliver', 'The finished app, published in the store under your name or delivered as a file to sideload. Rest of the invoice on delivery.'),
        ('Support', '30 days of bug fixes included. After that, a small monthly plan or per-hour fixes, your choice.'),
    ]
    faqs = [
        ('Who owns the app?', 'You do, once the final invoice is paid. Source code is available for an extra fee if you want to keep building on it yourself.'),
        ('Can it go in the Connect IQ Store or Google Play?', 'Yes. It can be published under your own developer account, or under GerrOS if you prefer. Store review is outside my control, but I build to the guidelines and have had every one of my own apps approved.'),
        ('Which watches?', 'All Garmin models that run Connect IQ, and Wear OS watches. Tell me which models matter and the quote will list exactly which ones are covered.'),
        ('What about data and privacy?', 'By default everything stays on the watch, like my own apps. If the app needs a server, that is scoped and priced separately.'),
        ('How is the price built up?', 'An internal rate of about €50 an hour. A watch face is 8–12 hours, an app 20–35, an app with a backend 50 or more. You get a fixed price, so the risk of overrun is mine.'),
        ('Do you do NDAs and invoices?', 'Yes. GerrOS is a registered Dutch company; you get a proper invoice, VAT reverse-charged for EU businesses.'),
    ]
    steps_html = ''.join(f'<li><b>{E(t)}</b><span>{E(d)}</span></li>' for t, d in steps)
    faq_html = ''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in faqs)
    return f'''
<section class="section"><div class="wrap studio">
  <div>
  <p class="eyebrow">Custom apps</p>
  <h1 class="h2">A watch app built to your brief.</h1>
  <p class="lede" style="margin-top:16px">Sports clubs, coaches, companies, researchers and people with one very specific wish: if the app you need is not in the store, GerrOS builds it. Garmin Connect IQ or Wear OS, fixed price, fixed scope.</p>
  <p class="lede" style="margin-top:14px">You work directly with the person who designed, built and shipped the {len(apps)} apps on this site, so the Garmin quirks, review rules and small-screen habits are already solved.</p>
  </div>
  <div class="contact-card">
    <h3>Start with a brief</h3>
    <p class="muted" style="font-size:.95rem">One mail is enough: what it should do, for whom, which watches, when, and a budget range. You get a fixed quote back, no obligation.</p>
    <a class="btn" href="{MAIL_CUSTOM}">Request a quote</a>
    <div class="kv"><span>Mail</span><b><a href="mailto:{MAIL}">{MAIL}</a></b><span>Reply</span><b>within 2 working days</b><span>Portfolio</span><b><a href="apps.html">{len(apps)} apps in the store</a></b></div>
  </div>
</div></section>

<section class="section"><div class="wrap">
  <p class="eyebrow">Packages</p><h2>Three sizes, one fixed price each.</h2>
  <p class="lede" style="margin-top:14px">Prices exclude VAT and are starting points; the quote is final. Second platform (Garmin and Wear OS) adds about 40%. Store publication under your own name: €150.</p>
  <div class="packages">{package_cards()}</div>
</div></section>

<section class="stats"><div class="wrap">
  <div class="stat"><b>{len(apps)}</b><span>apps shipped by GerrOS</span></div>
  <div class="stat"><b>{AVG:.1f}</b><span>average store rating</span></div>
  <div class="stat"><b>{DEVICES}</b><span>Garmin models covered</span></div>
  <div class="stat"><b>2</b><span>platforms: Connect IQ and Wear OS</span></div>
</div></section>

<section class="section"><div class="wrap">
  <p class="eyebrow">Process</p><h2>From brief to wrist in six steps.</h2>
  <ol class="steps">{steps_html}</ol>
</div></section>

<section class="section"><div class="wrap">
  <p class="eyebrow">Good fits</p><h2>What people ask for.</h2>
  <div class="principles">
    <div class="principle"><h3>Clubs and coaches</h3><p>A club watch face, a training protocol on the wrist, a score tracker for your sport with your rules.</p></div>
    <div class="principle"><h3>Companies</h3><p>A branded watch face as merchandise, or an internal tool: a shift logger, a checklist, a timer that follows your procedure.</p></div>
    <div class="principle"><h3>Research and study</h3><p>Collect heart rate, movement or answers on the watch and export them cleanly for analysis.</p></div>
    <div class="principle"><h3>One-off wishes</h3><p>The app you searched the store for and never found. If it fits on a watch, it can be built.</p></div>
    <div class="principle"><h3>Ports</h3><p>Already have a Garmin app? Bring it to Wear OS, or the other way round.</p></div>
    <div class="principle"><h3>Rescue jobs</h3><p>An existing Connect IQ app that crashes, fails review or needs new devices. Fixed and shipped.</p></div>
  </div>
</div></section>

<section class="section"><div class="wrap">
  <p class="eyebrow">Questions</p><h2>The practical part.</h2>
  <div class="faq">{faq_html}</div>
  <p class="hero-actions" style="margin-top:28px"><a class="btn" href="{MAIL_CUSTOM}">Request a quote</a><a class="btn ghost" href="studio.html">About the studio</a></p>
</div></section>'''

def page_studio():
    return f'''
<section class="section"><div class="wrap studio">
  <div>
  <p class="eyebrow">Studio</p>
  <h1 class="h2">A one-person studio in the Netherlands.</h1>
  <p class="lede" style="margin-top:16px">GerrOS is run by Thijs Gerritsen from Den Dolder. Every app starts as something he wanted on his own watch, gets built end to end, and is then kept alive: reviews are answered, bugs are fixed and features land in updates.</p>
  <p class="lede" style="margin-top:14px">It began with RallyPoint, a score tracker for padel that grew a live web scoreboard. Since then the catalogue has grown to {len(apps)} apps, from a chess clock to a race predictor, all in five languages, all working without a phone nearby.</p>
  </div>
  <div class="contact-card">
    <h3>Get in touch</h3>
    <div class="kv"><span>Mail</span><b><a href="mailto:{MAIL}">{MAIL}</a></b><span>Store</span><b><a href="{DEV}" target="_blank" rel="noopener">ThijsGer on Connect IQ</a></b><span>Based in</span><b>Den Dolder, NL</b></div>
    <p class="muted" style="font-size:.92rem">Bug, idea or question? Mail with the app name and your watch model, and you will hear back from the person who wrote the code.</p>
  </div>
</div></section>

<section class="stats"><div class="wrap">
  <div class="stat"><b>{len(apps)}</b><span>apps built</span></div>
  <div class="stat"><b>{UPDATES}</b><span>versions shipped</span></div>
  <div class="stat"><b>{DEVICES}</b><span>Garmin models supported</span></div>
  <div class="stat"><b>{REVIEWS}</b><span>reviews, {AVG:.1f} on average</span></div>
</div></section>

<section class="section"><div class="wrap">
  <p class="eyebrow">How they are made</p><h2>One screen, one number, no noise.</h2>
  <div class="principles">
    <div class="principle"><h3>Built for a glance</h3><p>A watch is read in half a second. Each app leads with the one number that matters and keeps the rest a swipe away. The glance strip on the watch shows something useful before you even open the app.</p></div>
    <div class="principle"><h3>Real arithmetic inside</h3><p>Budgets that pace themselves, a fasting clock that knows your window, a race predictor with three models, a caffeine curve. Not just trackers: apps that plan, predict and advise.</p></div>
    <div class="principle"><h3>Yours stays on the watch</h3><p>No accounts, no cloud, no tracking. Your data lives on the device, and every app works without a phone nearby.</p></div>
    <div class="principle"><h3>Buttons and touch</h3><p>Every app works on a touch screen and with the five buttons alone, on round AMOLED screens and on the older memory-in-pixel displays.</p></div>
    <div class="principle"><h3>Five languages, always</h3><p>English, Dutch, German, French and Spanish in every app, in the store text and on the screen.</p></div>
    <div class="principle"><h3>Kept alive</h3><p>Reviews get a reply. Bugs get fixed. The {UPDATES} versions in the store so far are the proof.</p></div>
  </div>
</div></section>'''

def page_support():
    return f'''
<main class="prose"><div class="wrap">
  <p class="eyebrow">Support</p>
  <h1>Something not working? Tell the person who wrote it.</h1>
  <p>Mail <a href="mailto:{MAIL}">{MAIL}</a> with the name of the app, your watch model and what happened. Screenshots help. You will hear back from the developer, usually within a few days, and fixes ship as app updates through the Connect IQ Store.</p>
  <h2>Before you write</h2>
  <ul>
    <li><b>App will not open or shows an IQ! symbol:</b> update the app in the Connect IQ app on your phone, then restart the watch. If it keeps happening, mail us the watch model and the app version.</li>
    <li><b>Glance shows nothing:</b> open the app once so it has data to show, then check the glance again. Updated versions of all apps show a summary even before first use.</li>
    <li><b>Buttons instead of touch:</b> every app can be operated with the physical buttons. START selects or confirms, BACK goes back or opens the menu, UP and DOWN scroll.</li>
    <li><b>Settings from the phone:</b> some apps can be configured in the Connect IQ app under the app's settings. Changes arrive on the watch within a minute.</li>
    <li><b>Refunds:</b> purchases are handled by Garmin. Refund requests go through Garmin support, not through GerrOS.</li>
  </ul>
  <h2>Feature requests</h2>
  <p>Most features in the apps came from wearers writing in. If something would make an app more useful for you, say so, and mention what you would use it for.</p>
</div></main>'''

def page_privacy():
    return f'''
<main class="prose"><div class="wrap">
  <p class="eyebrow">Privacy policy</p>
  <h1>Your data stays on your watch.</h1>
  <p class="updated">Applies to all GerrOS apps · last updated 6 September 2026</p>
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
def document(title, desc, body, active='', depth=0):
    pre = '../' * depth
    head = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:image" content="https://gerros.app/assets/covers/spent.jpg">
<link rel="icon" href="{pre}assets/favicon.svg" type="image/svg+xml">
{FONTS}
<link rel="stylesheet" href="{pre}style.css">
</head>
<body>'''
    doc = head + nav(active) + body + FOOTER + f'\n<script src="{pre}site.js"></script>\n</body></html>'
    if depth:
        doc = re.sub(r'(href|src)="(assets/|apps/|index\.html|apps\.html|finder\.html|whatsnew\.html|wearos\.html|studio\.html|support\.html|privacy\.html)', lambda m: f'{m.group(1)}="{pre}{m.group(2)}', doc)
        doc = doc.replace("url('assets/", f"url('{pre}assets/")
    return doc

PAGES = [
    ('index.html', 'GerrOS', 'Independent studio making focused apps for Garmin watches: budgets, timers, trackers and watch faces.', page_home, ''),
    ('apps.html', 'GerrOS apps', 'All GerrOS apps for Garmin watches, by category.', page_apps, 'apps.html'),
    ('finder.html', 'Find your app', 'Pick what you want from your watch and get the GerrOS app that does it.', page_finder, 'finder.html'),
    ('whatsnew.html', "What's new at GerrOS", 'Latest release notes for every GerrOS app.', page_whatsnew, 'whatsnew.html'),
    ('wearos.html', 'GerrOS on Wear OS', 'GerrOS apps coming to Wear OS: Caffi, Sobr, BreathGym and Convertr.', page_wearos, 'wearos.html'),
    ('custom.html', 'Custom watch apps by GerrOS', 'Garmin Connect IQ and Wear OS apps and watch faces built to order: fixed price, fixed scope, from €350.', page_custom, 'custom.html'),
    ('studio.html', 'GerrOS studio', 'About GerrOS, the one-person watch-app studio from the Netherlands.', page_studio, 'studio.html'),
    ('support.html', 'GerrOS support', 'Help with GerrOS apps for Garmin watches.', page_support, 'support.html'),
    ('privacy.html', 'GerrOS privacy policy', 'How GerrOS apps handle your data: on the watch, without accounts or tracking.', page_privacy, ''),
]
os.makedirs('apps', exist_ok=True)
bodies = {}
actives = {}
for fn, title, desc, fnc, active in PAGES:
    bodies[fn] = fnc(); actives[fn] = active
    open(fn, 'w').write(document(title, desc, bodies[fn], active))
for a in apps:
    body = page_app(a)
    fn = f'apps/{a["slug"]}.html'
    bodies[fn] = body; actives[fn] = 'apps.html'
    open(fn, 'w').write(document(f'{a["title"]} · GerrOS', f'{a["tag"]}. A GerrOS app for Garmin watches.', body, 'apps.html', depth=1))
open('assets/favicon.svg', 'w').write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="22" fill="none" stroke="#131518" stroke-width="7"/><path d="M32 6a26 26 0 0 1 26 26" fill="none" stroke="#3EDC96" stroke-width="7" stroke-linecap="round"/></svg>')

# ------------------------------------------------------------------ single-file preview with hash routing
def route_of(fn):
    if fn == 'index.html': return '/'
    if fn.startswith('apps/'): return '/app/' + fn[5:-5]
    return '/' + fn[:-5]
sections = ''.join(f'<main class="route" data-route="{route_of(fn)}" hidden>{nav(actives[fn])}{b}</main>' for fn, b in bodies.items())
single = re.sub(r'href="((?:\.\./)?)((?:apps/[a-z0-9-]+|index|apps|finder|whatsnew|wearos|custom|studio|support|privacy)\.html)(#[a-z]+)?"',
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
out = f'<title>GerrOS</title>\n{FONTS}\n<style>{css}</style>\n{single}{FOOTER.replace("privacy.html", "#/privacy").replace("support.html", "#/support")}\n<script>{js}</script>'
os.makedirs('dist', exist_ok=True)
open('dist/gerros.html', 'w').write(out)
print(f'{len(PAGES)} pages + {len(apps)} app pages · preview {len(out) // 1024 // 1024} MB · {len(live)} live · avg {AVG:.2f} · {REVIEWS} reviews · {UPDATES} versions')
