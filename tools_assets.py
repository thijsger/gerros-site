#!/usr/bin/env python3
# tools_assets.py — zet de storebeelden van één app om naar de site-assets.
#
#   python3 tools_assets.py <slug> <map> [--main 1|2|..|cover] [--check uit.jpg]
#
#   <map>  = de App-screenshots-map van de app (met daarin store/), of de store-map zelf.
#            Verwacht: cover-500.png, pagina-01..NN.jpg, hero-1440x720.png (hero is optioneel).
#   --main = uit welk beeld het hoofdscherm (assets/dials/<slug>.jpg) komt. Standaard pagina 1:
#            dat is hetzelfde scherm als de cover, maar bijna twee keer zo groot. Zonder pagina's: cover.
#   --check = schrijft een controlevel: elk bronbeeld met de gemeten cirkel erin + alle uitsnedes.
#
# Schrijft:
#   assets/covers/<slug>.jpg          500 px   horloge op off-white (cover)
#   assets/heroes/<slug>.jpg          1440x720 deelbeeld (og:image)
#   assets/screens/<slug>-N.jpg       1536 px  marketingbeeld N        (+ assets/small/<slug>-N.jpg, 960 px)
#   assets/dials/<slug>.jpg           480 px   alleen het ronde scherm (+ assets/small/dial-<slug>.jpg, 320 px)
#   assets/dials/<slug>-N.jpg         480 px   het scherm uit beeld N   (+ assets/small/dial-<slug>-N.jpg)
#   assets/local.json                 per slug: aantal beelden + gemeten cirkels. Zolang een slug hierin
#                                     staat, blijven refresh.py en tools_dials.py van zijn beelden af.
#
# Hoe het scherm wordt gemeten (niet gegokt): alle horloges in de storebeelden hebben een ring met
# streepjes binnen de bezel en daarbinnen een dunne lijn precies op de schermrand.
#   1. Randpunten zoeken waar zwart (scherm/streepjesring) aan grijs (bezel) grenst, en daar met RANSAC
#      de cirkel doorheen leggen die over de meeste graden van de omtrek klopt.
#   2. Vanuit dat middelpunt per straal de mediaan over 360 graden nemen. Losse streepjes en tekst vallen
#      in een mediaan weg; een volledige ring (de schermrand) blijft over als piek.
#   3. Net binnen die lijn uitsnijden en de hoeken buiten de cirkel zwart maken.
# Elke meting wordt geprint met dekking (graden van 360) en piekhoogte; "GESCHAT" betekent dat de lijn
# niet gevonden is en de vaste verhouding scherm/bezel (0,843, gemeten over 36 beelden) is gebruikt.
import json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
RATIO = 0.843            # schermrand / binnenrand bezel, gemeten
DIAL = 480               # uitvoer in px; het scherm in een pagina-beeld is ~460 px
ANG = np.linspace(0, 2 * math.pi, 360, endpoint=False)
CA, SA = np.cos(ANG), np.sin(ANG)


def polar(ch, cx, cy, rs):
    xs = np.clip(np.rint(cx + rs[:, None] * CA[None]).astype(int), 0, ch.shape[1] - 1)
    ys = np.clip(np.rint(cy + rs[:, None] * SA[None]).astype(int), 0, ch.shape[0] - 1)
    return ch[ys, xs]


def fit(p):
    x, y = p[:, 0], p[:, 1]
    c = np.linalg.lstsq(np.c_[2 * x, 2 * y, np.ones(len(x))], x * x + y * y, rcond=None)[0]
    return c[0], c[1], math.sqrt(max(1e-9, c[2] + c[0] ** 2 + c[1] ** 2))


def coverage(p, cx, cy, r, tol):
    m = np.abs(np.hypot(p[:, 0] - cx, p[:, 1] - cy) - r) < tol
    return len(np.unique((np.degrees(np.arctan2(p[m, 1] - cy, p[m, 0] - cx)) % 360).astype(int))), m


def find_ring(v):
    """Grootste volledige cirkel op een zwart/grijs-grens: de binnenrand van de bezel, of (als die lijn
    helder genoeg is) de schermrand zelf. measure() zoekt uit welke van de twee het is."""
    H = v.shape[0]
    dk, br = v < 22, (v >= 34) & (v < 200)
    e = np.zeros_like(dk)
    for d in (1, 2):
        e[:, d:] |= dk[:, d:] & br[:, :-d]; e[:, :-d] |= dk[:, :-d] & br[:, d:]
        e[d:] |= dk[d:] & br[:-d];          e[:-d] |= dk[:-d] & br[d:]
    ys, xs = np.nonzero(e)
    p = np.c_[xs, ys].astype(float)
    rng = np.random.default_rng(7)
    if len(p) > 7000:
        p = p[rng.choice(len(p), 7000, replace=False)]
    lo, hi, tol = 0.20 * H, 0.40 * H, max(1.2, H / 400)
    best = (0, None)
    for _ in range(6000):
        cx, cy, r = fit(p[rng.choice(len(p), 3, replace=False)])
        if lo < r < hi:
            n, _m = coverage(p, cx, cy, r, tol)
            if n > best[0]:
                best = (n, (cx, cy, r))
    if best[1] is None:
        raise SystemExit('geen cirkel gevonden')
    cx, cy, r = best[1]
    for t in (tol * 1.5, tol, tol * 0.8):
        _n, m = coverage(p, cx, cy, r, t)
        cx, cy, r = fit(p[m])
    return cx, cy, r, coverage(p, cx, cy, r, tol)[0]


def measure(im):
    """-> dict(cx, cy, r, how, cov, peak): middelpunt en straal van de schermrand."""
    v = np.asarray(im.convert('RGB')).astype(float).max(2)
    cx, cy, R, cov = find_ring(v)
    prof = lambda x, y, rs: np.median(polar(v, x, y, rs), axis=1)
    # Is de gevonden cirkel een stap (zwart -> bezel) of een dunne lijn (de schermrand zelf)?
    inner = np.median(prof(cx, cy, np.arange(R - 9, R - 3, 1.0)))
    outer = np.median(prof(cx, cy, np.arange(R + 4, R + 10, 1.0)))
    if outer - inner < 14:
        # dunne lijn: dit is de schermrand al. Straal op de piek zetten.
        rs = np.arange(R - 4, R + 4, 0.5)
        best = max(((prof(cx + dx, cy + dy, rs), dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)), key=lambda t: t[0].max())
        return dict(cx=cx + best[1], cy=cy + best[2], r=float(rs[int(best[0].argmax())]), how='lijn', cov=cov, peak=float(best[0].max()))
    # stap: binnenrand van de bezel. De schermrand is de ring rond 0,843 R.
    rs = np.arange(0.822 * R, 0.864 * R, 0.5)
    best = None
    for dx in np.arange(-3, 3.01, 1):
        for dy in np.arange(-3, 3.01, 1):
            q = prof(cx + dx, cy + dy, rs)
            q = q - np.median(q)
            i = int(q.argmax())
            if best is None or q[i] > best[0]:
                best = (float(q[i]), float(rs[i]), cx + dx, cy + dy)
    if best[0] >= 4:
        return dict(cx=best[2], cy=best[3], r=best[1], how='bezel+lijn', cov=cov, peak=best[0])
    return dict(cx=cx, cy=cy, r=RATIO * R, how='GESCHAT', cov=cov, peak=best[0])


def cut(im, c, size=DIAL):
    """Vierkant rond het scherm, net binnen de randlijn, met zwarte hoeken buiten de cirkel."""
    r = c['r'] - max(2.0, 0.013 * c['r'])
    box = (c['cx'] - r, c['cy'] - r, c['cx'] + r, c['cy'] + r)
    s = 3
    d = im.convert('RGB').resize((size * s, size * s), Image.LANCZOS, box=box)
    mask = Image.new('L', (size * s, size * s), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * s - 1, size * s - 1), fill=255)
    out = Image.composite(d, Image.new('RGB', d.size, (0, 0, 0)), mask)
    return out.resize((size, size), Image.LANCZOS)


def accents(dial, k=3):
    """De meest voorkomende verzadigde kleuren in het scherm: hulp bij het kiezen van 'accent' in meta.json."""
    a = np.asarray(dial.convert('HSV')).reshape(-1, 3).astype(int)
    rgb = np.asarray(dial.convert('RGB')).reshape(-1, 3)
    m = (a[:, 1] > 110) & (a[:, 2] > 150)
    out = []
    if m.sum() < 50:
        return out
    bins = (a[m, 0] // 12)
    for b in np.argsort(-np.bincount(bins, minlength=22))[:k]:
        sel = rgb[m][bins == b]
        if len(sel) > 40:
            out.append('#%02X%02X%02X' % tuple(int(x) for x in np.median(sel, axis=0)))
    return out


def main():
    args = sys.argv[1:]
    opt = {}
    for flag in ('--main', '--check'):
        if flag in args:
            i = args.index(flag); opt[flag] = args[i + 1]; del args[i:i + 2]
    if len(args) != 2:
        sys.exit('gebruik: python3 tools_assets.py <slug> <map> [--main 1|2|..|cover] [--check uit.jpg]')
    slug, src = args[0], os.path.abspath(os.path.expanduser(args[1]))
    if not re.fullmatch(r'[a-z0-9-]+', slug):
        sys.exit('slug: alleen kleine letters, cijfers en streepjes (zoals in meta.json)')
    if os.path.isdir(os.path.join(src, 'store')):
        src = os.path.join(src, 'store')
    cover = os.path.join(src, 'cover-500.png')
    if not os.path.exists(cover):
        sys.exit(f'geen cover-500.png in {src}')
    pages = sorted(f for f in os.listdir(src) if re.fullmatch(r'pagina-\d+\.jpe?g', f))
    hero = next((os.path.join(src, f) for f in os.listdir(src) if f.startswith('hero-')), None)
    os.chdir(ROOT)
    for d in ('covers', 'heroes', 'screens', 'dials', 'small'):
        os.makedirs(f'assets/{d}', exist_ok=True)

    def save_dial(d, name):
        d.save(f'assets/dials/{name}.jpg', quality=92, optimize=True)
        d.resize((320, 320), Image.LANCZOS).save(f'assets/small/dial-{name}.jpg', quality=84, optimize=True)

    sheet = []
    def report(label, im, c):
        flag = '' if c['how'] != 'GESCHAT' and c['cov'] >= 270 else '   <-- NAKIJKEN'
        print(f"  {label:<14} midden ({c['cx']:.1f}, {c['cy']:.1f})  straal {c['r']:.1f} px  [{c['how']}, dekking {c['cov']}/360, piek {c['peak']:.0f}]{flag}")
        sheet.append((label, im, c))

    print(f'{slug}: {src}')
    c_im = Image.open(cover).convert('RGB')
    c_im.save(f'assets/covers/{slug}.jpg', quality=92, optimize=True)
    c_im.resize((360, 360), Image.LANCZOS).save(f'assets/small/{slug}.jpg', quality=80, optimize=True)
    circles = {'cover': measure(c_im)}
    report('cover', c_im, circles['cover'])
    dials = {'cover': cut(c_im, circles['cover'])}
    if hero:
        h = Image.open(hero).convert('RGB')
        if h.size != (1440, 720):
            h = h.resize((1440, 720), Image.LANCZOS)
        h.save(f'assets/heroes/{slug}.jpg', quality=88, optimize=True)
    for n, f in enumerate(pages, 1):
        im = Image.open(os.path.join(src, f)).convert('RGB')
        im.save(f'assets/screens/{slug}-{n}.jpg', quality=90, optimize=True)
        im.resize((960, round(im.height * 960 / im.width)), Image.LANCZOS).save(f'assets/small/{slug}-{n}.jpg', quality=80, optimize=True)
        circles[str(n)] = measure(im)
        report(f, im, circles[str(n)])
        dials[str(n)] = cut(im, circles[str(n)])
        save_dial(dials[str(n)], f'{slug}-{n}')
    # beelden van een eerdere, langere reeks opruimen
    n = len(pages) + 1
    while os.path.exists(f'assets/screens/{slug}-{n}.jpg'):
        for p in (f'assets/screens/{slug}-{n}.jpg', f'assets/small/{slug}-{n}.jpg', f'assets/dials/{slug}-{n}.jpg', f'assets/small/dial-{slug}-{n}.jpg'):
            if os.path.exists(p):
                os.remove(p)
        n += 1
    which = opt.get('--main') or ('1' if pages else 'cover')
    if which not in dials:
        sys.exit(f'--main {which}: dat beeld bestaat niet')
    save_dial(dials[which], slug)
    print(f"  hoofdscherm uit {'de cover' if which == 'cover' else 'pagina ' + which}; kleuren in dat scherm: {', '.join(accents(dials[which])) or '-'}")

    local = json.load(open('assets/local.json')) if os.path.exists('assets/local.json') else {}
    local[slug] = {'screens': len(pages), 'main': which, 'hero': bool(hero),
                   'circles': {k: [round(c['cx'], 1), round(c['cy'], 1), round(c['r'], 1), c['how']] for k, c in circles.items()}}
    json.dump(local, open('assets/local.json', 'w'), indent=1, ensure_ascii=False, sort_keys=True)

    if opt.get('--check'):
        T = 380
        out = Image.new('RGB', (T * len(sheet), T * 2), (20, 20, 20))
        for i, (label, im, c) in enumerate(sheet):
            R = c['r'] * 1.45
            box = (c['cx'] - R, c['cy'] - R, c['cx'] + R, c['cy'] + R)
            t = im.crop(tuple(int(round(x)) for x in box)).resize((T, T), Image.LANCZOS)   # crop vult buiten het beeld aan
            t = Image.eval(t, lambda x: min(255, int((x / 255) ** 0.5 * 255)))   # donker oplichten: rand zichtbaar
            k = T / (2 * R)
            rr = (c['r'] - max(2.0, 0.013 * c['r'])) * k
            ImageDraw.Draw(t).ellipse((T / 2 - rr, T / 2 - rr, T / 2 + rr, T / 2 + rr), outline=(255, 0, 80), width=1)
            out.paste(t, (i * T, 0))
            out.paste(dials['cover' if label == 'cover' else str(i)].resize((T, T), Image.LANCZOS), (i * T, T))
        out.save(opt['--check'], quality=88)
        print('  controlevel:', opt['--check'])


if __name__ == '__main__':
    main()
