#!/usr/bin/env python3
"""Build GerrOS as dependency-free static HTML from data.json and meta.json."""
from pathlib import Path
from datetime import datetime, timezone
import html, json, re, shutil

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "data.json").read_text())
META = json.loads((ROOT / "meta.json").read_text())
DOMAIN = "https://gerros.app"
EMAIL = "thijsjwger@gmail.com"
GARMIN = "https://apps.garmin.com/apps/"
PRICE = "$1.99 / €2.49"
CATS = dict(META["categories"])
NAV = [("/apps/", "Apps"), ("/finder/", "Find your app"), ("/whats-new/", "What's new"), ("/wear-os/", "Wear OS"), ("/studio/", "Studio"), ("/support/", "Support")]
E = html.escape

raw = {a["slug"]: a for a in DATA}
apps = []
for slug, m in META["apps"].items():
    if slug not in raw:
        continue
    a = raw[slug]
    shots = [f"/assets/screens/{slug}-{i}.jpg" for i in range(1, 6) if (ROOT / f"assets/screens/{slug}-{i}.jpg").exists()]
    apps.append({**a, **m, "slug": slug, "pending": bool(m.get("pending")), "shots_web": shots,
                 "dial": f"/assets/dials/{slug}.jpg", "icon_web": f"/assets/icons/{slug}.png"})
BY = {a["slug"]: a for a in apps}

def date(value):
    if not value: return "Date pending"
    return datetime.fromtimestamp(value / 1000, timezone.utc).strftime("%d %b %Y").lstrip("0")

def rating(a, full=True):
    if a["pending"]: return '<span class="status">In review</span>'
    if a.get("rating") is None: return '<span class="unrated">Not yet rated</span>'
    reviews = a.get("reviews") or 0
    suffix = f" · {reviews} {'review' if reviews == 1 else 'reviews'}" if full else ""
    return f'<span aria-label="Rated {a["rating"]:.1f} out of 5">★ {a["rating"]:.1f}{suffix}</span>'

def rich(text):
    blocks, para, bullets = [], [], []
    def flush_para():
        nonlocal para
        if para: blocks.append("<p>" + E(" ".join(para)) + "</p>"); para = []
    def flush_list():
        nonlocal bullets
        if bullets: blocks.append("<ul>" + "".join(f"<li>{E(x)}</li>" for x in bullets) + "</ul>"); bullets = []
    for rawline in (text or "").splitlines() + [""]:
        line = rawline.strip()
        if not line:
            flush_para(); flush_list(); continue
        if line.startswith(("- ", "• ")):
            flush_para(); bullets.append(line[2:]); continue
        flush_list()
        if len(line) < 55 and line.upper() == line and re.search(r"[A-Z]", line):
            flush_para(); blocks.append(f"<h3>{E(line.title())}</h3>")
        else: para.append(line)
    return "".join(blocks)

def header(active=""):
    links = "".join(f'<a href="{u}" {"aria-current=page" if active == u else ""}>{t}</a>' for u,t in NAV)
    return f'''<a class="skip" href="#main">Skip to content</a><header class="top"><div class="shell navrow">
      <a class="logo" href="/" aria-label="GerrOS home"><span aria-hidden="true">G</span>GerrOS</a>
      <button class="theme" type="button" aria-label="Switch colour theme">◐</button><button class="motion" type="button" aria-pressed="false">Pause motion</button><button class="menu" type="button" aria-expanded="false" aria-controls="nav">Menu</button>
      <nav id="nav" aria-label="Main navigation">{links}</nav>
    </div></header>'''

def footer():
    return f'''<footer><div class="shell foot"><div><a class="logo inverse" href="/"><span aria-hidden="true">G</span>GerrOS</a><p>Precise tools for wrists.<br>Made by Thijs in the Netherlands.</p></div><div><p class="label">Contact</p><a href="mailto:{EMAIL}">{EMAIL}</a></div><div><p class="label">Small print</p><a href="/privacy">Privacy</a><a href="/support/">Support</a></div></div><p class="shell legal">© 2026 GerrOS. Garmin, Connect IQ and Wear OS are trademarks of their respective owners.</p></footer>'''

def document(title, desc, body, path="/", active="", image="/assets/screens/caffi-1.jpg", pageclass=""):
    canonical = DOMAIN + path
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{canonical}">
    <meta property="og:type" content="website"><meta property="og:site_name" content="GerrOS"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{DOMAIN + image}">
    <meta name="theme-color" content="#ece9df" media="(prefers-color-scheme:light)"><meta name="theme-color" content="#10110f" media="(prefers-color-scheme:dark)"><link rel="icon" href="/assets/favicon.svg"><link rel="stylesheet" href="/style.css"><script src="/site.js" defer></script></head>
    <body class="{pageclass}">{header(active)}<main id="main">{body}</main>{footer()}</body></html>'''

def app_card(a, compact=False):
    cls = "appcard compact" if compact else "appcard"
    return f'''<a class="{cls}" href="/apps/{a['slug']}/" data-cat="{a['cat']}" data-search="{E((a['title']+' '+a['tag']).lower())}">
      <img src="{a['icon_web']}" alt="" width="500" height="500" loading="lazy"><span class="cardcopy"><span class="cardtop"><strong>{E(a['title'])}</strong>{rating(a)}</span><span>{E(a['tag'])}</span></span></a>'''

def home():
    featured = [BY[x] for x in ("caffi", "racecast", "spent")]
    rail = "".join(app_card(a, True) for a in apps)
    latest = sorted([a for a in apps if a.get("changed")], key=lambda x:x["changed"], reverse=True)[:3]
    latest_html = "".join(f'<a href="/apps/{a["slug"]}/"><time>{date(a["changed"])}</time><strong>{E(a["title"])} <span>v{E(a["version"])}</span></strong><p>{E((a.get("whatsnew") or a["tag"]).splitlines()[0].lstrip("- "))}</p></a>' for a in latest)
    dials = "".join(f'<a href="/apps/{a["slug"]}/"><img src="{a["dial"]}" width="454" height="454" alt="{E(a["title"])} watch screen"></a>' for a in featured)
    body = f'''<section class="watch-story" aria-label="Inside GerrOS: a watch in three acts">
      <div class="watch-stage">
        <div class="stage-grid" aria-hidden="true"></div>
        <div class="stage-top"><span>GERR OS / INDEPENDENT WATCH SOFTWARE</span><span>EST. NETHERLANDS</span></div>
        <div class="watch-visual"><img class="watch-fallback" src="/assets/dials/caffi.jpg" alt="Caffi caffeine curve on a round watch display" width="454" height="454"><canvas id="watch-canvas" aria-label="Interactive 3D watch showing original GerrOS app screens" role="img"></canvas></div>
        <div class="story-copy story-intro is-active" data-scene="0"><p class="kicker">Small screen. Deep thinking.</p><h1>BEYOND<br><span>THE TIME.</span></h1><p class="story-description">Your watch has more to give.<br>We build the engines that bring it out.</p><a class="button acid" href="/apps/">Explore the apps <span>↗</span></a></div>
        <div class="story-copy" data-scene="1" inert><p class="kicker">01 / Caffi · Health & habits</p><h2>COFFEE IN.<br><span>SLEEP</span><br>WORKED OUT.</h2><p class="story-description">A pharmacokinetic curve. A clear view of the caffeine still in your system. All on your watch.</p><a class="text-link" href="/apps/caffi/">Meet Caffi ↗</a></div>
        <div class="story-copy" data-scene="2" inert><p class="kicker">02 / Racecast · Sport & outdoors</p><h2>ONE RUN.<br><span>WHAT’S</span><br>POSSIBLE?</h2><p class="story-description">Your result. Your fatigue factor. Race predictions from 5K to marathon.</p><a class="text-link" href="/apps/racecast/">Inside Racecast ↗ <small>IN REVIEW</small></a></div>
        <div class="story-copy" data-scene="3" inert><p class="kicker">03 / Spent · Money & work</p><h2>LESS<br><span>GUESSING.</span><br>MORE LEFT.</h2><p class="story-description">Your daily budget, worked out.<br>One number tells you what you can still spend.</p><a class="text-link" href="/apps/spent/">Meet Spent ↗</a></div>
        <div class="stage-bottom"><span class="scroll-cue">↓ SCROLL TO TURN THE ENGINE</span><div class="scene-nav" aria-label="Watch scenes"><button data-jump="0" aria-label="Introduction" aria-pressed="true">00</button><button data-jump="1" aria-label="Show Caffi" aria-pressed="false">01</button><button data-jump="2" aria-label="Show Racecast" aria-pressed="false">02</button><button data-jump="3" aria-label="Show Spent" aria-pressed="false">03</button></div><span class="model-note">3D WATCH STUDY / ORIGINAL APP SCREENS</span></div>
        <div class="story-progress" aria-hidden="true"></div>
      </div>
    </section>
    <section class="statement"><div class="shell"><p class="kicker">Built by Thijs. Made for your wrist.</p><h2>NOT ANOTHER<br>THING TO <em>CHECK.</em><br>A TOOL TO <em>USE.</em></h2><div class="statement-bottom"><span class="asterisk" aria-hidden="true">✳</span><p>GerrOS is a one-person studio in the Netherlands. Thirty focused apps that calculate, predict or advise. No phone. No account. Your data stays on the watch.</p><a class="text-link" href="/studio/">Inside the studio ↗</a></div></div></section>
    <section class="rail-section"><div class="shell section-title"><div><p class="kicker">The tool cabinet / {len(apps):02d} instruments</p><h2>FIND YOUR<br><em>EXTRA GEAR.</em></h2></div><a class="text-link" href="/apps/">Open the full catalogue ↗</a></div><div class="shell rail-controls"><button type="button" data-rail="-1" aria-label="Previous apps">←</button><button type="button" data-rail="1" aria-label="Next apps">→</button></div><div class="rail" tabindex="0" aria-label="All GerrOS apps">{rail}</div></section>
    <section class="rules-section shell"><div class="rule-heading"><p class="kicker">Complex underneath. Clear on top.</p><h2>THE ART OF<br><em>LEAVING OUT.</em></h2><a class="text-link" href="/finder/">Find your app in three questions ↗</a></div><div class="rule-rows"><div><span>01</span><h3>One big number.</h3><p>A thin ring. One muted line. Read it in a glance.</p></div><div><span>02</span><h3>Both hands welcome.</h3><p>Touch screens and button-only watches. Both get the full app.</p></div><div><span>03</span><h3>Five languages.</h3><p>English, Dutch, German, French and Spanish.</p></div><div><span>04</span><h3>Zero accounts.</h3><p>The engine runs on the watch. Your data stays there.</p></div></div></section>
    <section class="shell releases"><div class="section-title"><div><p class="kicker">Fresh from the workbench</p><h2>STILL<br><em>GETTING BETTER.</em></h2></div><a class="text-link" href="/whats-new/">The release log ↗</a></div><div class="release-list">{latest_html}</div></section>
    <section class="closing"><p class="kicker">Garmin Connect IQ / Wear OS</p><a href="/apps/">PUT IT<br>TO <em>WORK.</em><span>↗</span></a><p>Small tools. A more capable watch.</p></section>
    <noscript><style>.watch-story{{height:auto}}.watch-stage{{position:relative}}</style></noscript><script src="/watch.js" defer></script>'''
    return document("GerrOS — precise tools for Garmin and Wear OS", "Independent Dutch studio making focused watch apps that calculate, predict and advise. No phone, account or off-watch data.", body, pageclass="home-page")

def catalogue():
    chips = '<button data-filter="all" aria-pressed="true">All</button>' + "".join(f'<button data-filter="{k}" aria-pressed="false">{E(v)}</button>' for k,v in META["categories"])
    body = f'''<section class="pagehead shell"><p class="kicker">All apps</p><h1>Pick one useful thing<br>for your wrist.</h1><p>{len(apps)} focused tools. Every live app costs {PRICE}. No subscription.</p></section><section class="shell catalogue"><div class="catalogue-tools"><label>Search apps<input id="app-search" type="search" placeholder="Try budget, caffeine or score" autocomplete="off"></label><div class="chips" aria-label="Filter by category">{chips}</div></div><p class="result-count" aria-live="polite">Showing all {len(apps)} apps</p><div class="appgrid">{"".join(app_card(a) for a in apps)}</div><p class="empty" hidden>No app matches that search.</p></section>'''
    return document("All watch apps — GerrOS", "Browse all GerrOS Garmin apps by category, rating and status.", body, "/apps/", "/apps/")

def app_page(a):
    shots = a["shots_web"]
    hero = shots[0] if shots else a["icon_web"]
    gallery = "".join(f'<figure><img src="{s}" alt="{E(a["title"])} app screenshot {i+1} of {len(shots)}" width="1536" height="1024" loading="lazy"></figure>' for i,s in enumerate(shots))
    store = '<span class="button disabled">Garmin review in progress</span>' if a["pending"] else f'<a class="button dark" href="{GARMIN}{a["id"]}" rel="noopener">Get it on Connect IQ ↗</a>'
    if a.get('play_url', '').startswith('https://play.google.com/store/apps/details?'):
        store += f'<a class="button line" href="{E(a["play_url"])}">Get it on Google Play ↗</a>'
    notes = rich(a.get("whatsnew") or "No release notes supplied for this version.")
    body = f'''<section class="app-hero shell"><a class="back" href="/apps/">← All apps</a><div class="app-intro"><div><p class="kicker">{E(CATS[a['cat']])}</p><h1>{E(a['title'])}</h1><p class="app-tag">{E(a['tag'])}</p><div class="actions">{store}<span class="price">{PRICE}<small>one-time purchase</small></span></div></div><img class="dial" src="{a['dial']}" alt="{E(a['title'])} watch screen" width="454" height="454"></div></section>
    <section class="hero-shot shell"><img src="{hero}" alt="{E(a['title'])} shown on a watch" width="1536" height="1024"></section>
    <section class="shell app-detail"><article><p class="kicker">What it does</p>{rich(a['desc'])}</article><aside><div class="facts"><p>{rating(a)}</p><dl><div><dt>Version</dt><dd>{E(a['version'])}</dd></div><div><dt>Release</dt><dd>{date(a.get('changed'))}</dd></div><div><dt>Supported devices</dt><dd>{a.get('devices') or 'Pending'} models</dd></div><div><dt>Languages</dt><dd>EN · NL · DE · FR · ES</dd></div><div><dt>Data</dt><dd>On-watch only</dd></div></dl></div><div class="notes"><p class="kicker">What's new</p><h2>Version {E(a['version'])}</h2>{notes}</div></aside></section>
    <section class="gallery shell"><div class="section-title"><div><p class="kicker">On the watch</p><h2>On screen. In context.</h2></div></div><div class="shot-grid">{gallery}</div></section>'''
    return document(f"{a['title']} — Garmin watch app by GerrOS", a["tag"] + ". Runs fully on the watch; no account required.", body, f"/apps/{a['slug']}/", "/apps/", hero, "app-page")

def finder():
    questions = '''<section class="finder" data-step="1"><p class="step">01 / 03</p><h2>What should the watch help with?</h2><div class="choices"><button data-answer="health">My body or a habit</button><button data-answer="sport">A sport or the outdoors</button><button data-answer="money">Money or work</button><button data-answer="tools">An everyday task</button><button data-answer="faces">Just tell the time differently</button></div></section>
    <section class="finder" data-step="2" hidden><p class="step">02 / 03</p><h2>What kind of help?</h2><div class="choices"><button data-answer="predict">Predict or calculate</button><button data-answer="guide">Guide me while I do it</button><button data-answer="record">Keep score or remember</button></div><button class="backstep">← Back</button></section>
    <section class="finder" data-step="3" hidden><p class="step">03 / 03</p><h2>How much attention can you give it?</h2><div class="choices"><button data-answer="glance">A quick glance</button><button data-answer="interact">I can tap or press buttons</button></div><button class="backstep">← Back</button></section>
    <section class="finder results" data-step="4" hidden><p class="kicker">A short list</p><h2>Start with these.</h2><div class="recommendations"></div><button class="button line restart">Start over</button></section>'''
    body = f'<section class="pagehead shell"><p class="kicker">Find your app</p><h1>Three questions.<br>No personality test.</h1><p>Tell us what the watch should do. We will narrow the catalogue to one, two or three apps.</p></section><noscript><p class="shell">The guided chooser needs JavaScript. <a href="/apps/">Browse all apps instead.</a></p></noscript><div class="shell finder-wrap">{questions}</div>'
    return document("Find your Garmin app — GerrOS", "Answer three short questions and get a focused GerrOS app recommendation.", body, "/finder/", "/finder/")

def whatsnew():
    items = "".join(f'''<article><time datetime="{datetime.fromtimestamp(a['changed']/1000, timezone.utc).date().isoformat() if a.get('changed') else ''}">{date(a.get('changed'))}</time><div><p class="kicker">{E(a['title'])} · v{E(a['version'])}</p><h2><a href="/apps/{a['slug']}/">{E(a['tag'])}</a></h2>{rich(a.get('whatsnew') or 'Release notes not supplied.')}</div></article>''' for a in sorted(apps,key=lambda x:x.get("changed") or 0,reverse=True))
    body = f'<section class="pagehead shell"><p class="kicker">Release log</p><h1>What changed,<br>and when.</h1><p>Every current release across the GerrOS catalogue.</p></section><section class="shell timeline">{items}</section>'
    return document("What's new — GerrOS release notes", "A chronological feed of GerrOS watch app versions and release notes.", body, "/whats-new/", "/whats-new/")

def wear():
    names = [("Caffi", "Live on Garmin. Google Play release is next."), ("Sobr", "Ported for Wear OS. Release coming."), ("BreathGym", "Ported for Wear OS. Release coming."), ("Convertr", "Ported for Wear OS. Release coming.")]
    def play_link(n):
        url=BY[n.lower()].get('play_url','')
        return f'<a class="button line" href="{E(url)}">Get it on Google Play ↗</a>' if url.startswith('https://play.google.com/store/apps/details?') else '<span class="status">Coming to Google Play</span>'
    rows = "".join(f'<article><img src="{BY[n.lower()]["dial"]}" alt="{n} watch screen" width="454" height="454"><div><p class="kicker">{E(state)}</p><h2>{n}</h2><p>{E(BY[n.lower()]["tag"])}.</p>{play_link(n)}</div></article>' for n,state in names)
    body = f'<section class="pagehead shell"><p class="kicker">Wear OS</p><h1>The engines are<br>changing watches.</h1><p>GerrOS started on Garmin. From 2026, selected apps are being rebuilt natively for Google watches. Caffi is first.</p></section><section class="shell wear-grid">{rows}</section>'
    return document("Wear OS apps — GerrOS", "Caffi, Sobr, BreathGym and Convertr are coming to Wear OS.", body, "/wear-os/", "/wear-os/")

def studio():
    body='''<section class="pagehead shell"><p class="kicker">The studio</p><h1>One person.<br>Thirty small machines.</h1><p>GerrOS is the sole proprietorship of Thijs in the Netherlands. Small is the operating model, not a phase.</p></section><section class="shell process"><div><p class="kicker">How an app gets made</p><h2>Start with the gap.</h2></div><ol><li><b>Idea</b><span>One watch-sized job worth doing.</span></li><li><b>Research</b><span>Read forums, reviews and the store. Find what existing apps miss.</span></li><li><b>Build</b><span>Put the calculation first. Remove everything that does not help it.</span></li><li><b>Test</b><span>Run it in the simulator on small screens, MIP displays and button-only watches.</span></li><li><b>Store</b><span>Ship, read the feedback and tighten the next version.</span></li></ol></section><section class="dark-panel"><div class="shell engines"><div><p class="kicker">Not dumb trackers</p><h2>Every app has<br>an engine.</h2></div><div class="engine-grid"><article><b>Racecast</b><p>Uses a personal fatigue factor to predict 5K through marathon times from one result.</p></article><article><b>Caffi</b><p>Models a pharmacokinetic caffeine curve to show what remains in your system.</p></article><article><b>Adapt</b><p>Measures TDEE from scale changes and adjusts a calorie target.</p></article><article><b>Recover</b><p>Uses a heart-rate recovery constant to decide when the next effort should start.</p></article></div></div></section><section class="shell manifesto"><p class="kicker">Interface principles</p><h2>The screen is read while walking, running, shopping or speaking. So the hierarchy is fixed: a thin ring, one big number, one muted line. Every flow works with touch and physical buttons. Every app speaks English, Dutch, German, French and Spanish.</h2></section>'''
    return document("Studio — how GerrOS builds watch apps", "How GerrOS researches, builds and tests precise Garmin and Wear OS apps.", body, "/studio/", "/studio/")

def support():
    faqs=[("How do I install a Connect IQ app?","Open its Connect IQ store page, buy the app and choose Install. Garmin Connect syncs it to a compatible watch."),("Why does an app ask for a permission?","A permission unlocks a watch feature the app needs, such as GPS, heart rate or storage. GerrOS apps do not send that data to us."),("Can I get a refund?","Purchases and refunds are handled by the store. Contact Garmin for Connect IQ purchases or Google for Google Play purchases."),("Which watches are supported?","Compatibility differs by app. Open an app page here for its device count, then use the store page to check your exact model."),("Which languages are included?","Every app includes English, Dutch, German, French and Spanish. WordClock supports ten languages.")]
    details="".join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q,a in faqs)
    body=f'<section class="pagehead shell"><p class="kicker">Support</p><h1>A direct line<br>to the builder.</h1><p>Read the common answers below. If something still does not work, email Thijs with the app name and watch model.</p><a class="button dark" href="mailto:{EMAIL}">{EMAIL}</a></section><section class="shell faq">{details}</section>'
    return document("Support — GerrOS", "Installation, permissions, refunds, compatibility and language help for GerrOS apps.", body, "/support/", "/support/")

def privacy():
    body=f'''<section class="pagehead shell"><p class="kicker">Privacy policy · 8 September 2026</p><h1>Your data stays<br>on your wrist.</h1><p>This is the complete policy for GerrOS apps and this website.</p></section><article class="shell policy"><h2>Apps</h2><p>GerrOS does not collect, receive, sell or share personal data. All app data is stored and processed on the watch. No account is required. Nothing is sent to GerrOS.</p><h2>Analytics and cookies</h2><p>GerrOS does not use analytics, advertising trackers or marketing cookies. The hosting provider may process technical request data or use cookies strictly required to deliver and protect the site.</p><h2>Store purchases</h2><p>Garmin and Google process purchases and refunds under their own privacy policies. GerrOS does not receive payment details.</p><h2>Contact</h2><p>Questions about privacy can be sent to <a href="mailto:{EMAIL}">{EMAIL}</a>. If you email, the message and address are used only to answer you.</p></article>'''
    return document("Privacy policy — GerrOS", "GerrOS collects no app data. Everything is stored and processed on the watch.", body, "/privacy")

(ROOT/"finder-data.json").write_text(json.dumps([{ "slug":a["slug"], "name":a["title"], "tag":a["tag"], "cat":a["cat"], "pending":a["pending"] } for a in apps]))

PAGES = {"index.html":home(), "apps/index.html":catalogue(), "finder/index.html":finder(), "whats-new/index.html":whatsnew(), "wear-os/index.html":wear(), "studio/index.html":studio(), "support/index.html":support(), "privacy.html":privacy(), "privacy/index.html":privacy()}
for a in apps: PAGES[f"apps/{a['slug']}/index.html"] = app_page(a)
from PIL import Image
optimized = ROOT / "assets" / "web"
optimized.mkdir(exist_ok=True)
for source in list((ROOT/"assets/dials").glob("*.jpg")) + list((ROOT/"assets/icons").glob("*.png")) + list((ROOT/"assets/screens").glob("*.jpg")):
    sizes = (240,454) if source.parent.name == "dials" else ((160,320) if source.parent.name == "icons" else (640,1280))
    for width in sizes:
        dest = optimized / f"{source.parent.name}-{source.stem}-{width}.webp"
        if not dest.exists() or dest.stat().st_mtime < source.stat().st_mtime:
            with Image.open(source) as im:
                im.thumbnail((width,width*2))
                im.convert("RGB").save(dest,"WEBP",quality=84)
def responsive(match):
    tag=match.group(0)
    found=re.search(r'src="(/assets/(dials|icons|screens)/([^".]+)\.(jpg|png))"',tag)
    if not found: return tag
    path,kind,slug,_=found.groups()
    widths=(240,454) if kind=="dials" else ((160,320) if kind=="icons" else (640,1280))
    if not (optimized/f"{kind}-{slug}-{widths[0]}.webp").exists(): return tag
    srcs=", ".join(f"/assets/web/{kind}-{slug}-{w}.webp {w}w" for w in widths)
    sizes="(max-width: 600px) 75vw, 400px" if kind=="dials" else ("100px" if kind=="icons" else "(max-width: 700px) 94vw, 1100px")
    return tag.replace(f'src="{path}"',f'src="/assets/web/{kind}-{slug}-{widths[-1]}.webp" srcset="{srcs}" sizes="{sizes}" decoding="async"')
for name, content in PAGES.items():
    content=re.sub(r'<img\b[^>]*>',responsive,content)
    path=ROOT/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(content)

# Compatibility copies for hosts/bookmarks that still request .html routes.
for slug in BY: shutil.copyfile(ROOT/f"apps/{slug}/index.html", ROOT/f"apps/{slug}.html")
for src,dst in [("apps/index.html","apps.html"),("finder/index.html","finder.html"),("whats-new/index.html","whatsnew.html"),("wear-os/index.html","wearos.html"),("studio/index.html","studio.html"),("support/index.html","support.html")]: shutil.copyfile(ROOT/src,ROOT/dst)

urls=["/","/apps/","/finder/","/whats-new/","/wear-os/","/studio/","/support/","/privacy"]+[f"/apps/{a['slug']}/" for a in apps]
(ROOT/"sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+"\n".join(f'  <url><loc>{DOMAIN}{u}</loc></url>' for u in urls)+'\n</urlset>\n')
(ROOT/"robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n")
print(f"Built {len(PAGES)} canonical pages for {len(apps)} apps.")

# Render publishes only the generated site, never source or backups.
PUBLIC = ROOT / 'public'
PUBLIC.mkdir(exist_ok=True)
for name in PAGES:
    target=PUBLIC/name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/name,target)
for filename in ['style.css','site.js','watch.js','finder-data.json','robots.txt','sitemap.xml']:
    shutil.copyfile(ROOT/filename,PUBLIC/filename)
for name in ['web','screens']:
    shutil.copytree(ROOT/'assets'/name,PUBLIC/'assets'/name,dirs_exist_ok=True)
shutil.copyfile(ROOT/'assets/favicon.svg',PUBLIC/'assets/favicon.svg')
# Keep historical incoming links functional without exposing source files.
for filename in ['apps.html','finder.html','whatsnew.html','wearos.html','studio.html','support.html']:
    shutil.copyfile(ROOT/filename,PUBLIC/filename)
for slug in BY:
    shutil.copyfile(ROOT/f'apps/{slug}.html',PUBLIC/f'apps/{slug}.html')
(PUBLIC/'404.html').write_text(document('Page not found — GerrOS','Find your way back to the GerrOS watch app catalogue.','<section class="shell pagehead"><p class="kicker">404 / Outside the dial</p><h1>Nothing here.<br>Plenty on your wrist.</h1><div class="actions"><a class="button dark" href="/apps/">Browse the apps</a><a class="button line" href="/">Go home</a></div></section>','/404'))
print('Render-ready site: public/')
