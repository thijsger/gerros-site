#!/usr/bin/env python3
# tools_dials.py — maakt assets/dials/<slug>.jpg (454x454) en assets/small/dial-<slug>.jpg (320x320)
# uit assets/dials-src/<slug>.png: exacte 454 px sim-opnames van het scherm, dus het scherm staat
# altijd precies in het midden van de cirkel. Voor apps zonder sim-opname staat in MANUAL een
# handmatig gemeten uitsnede (bestand, middelpunt, straal van het scherm) uit een marketingbeeld;
# die wordt eerst naar dials-src geschreven en dan net zo behandeld.
import json, os
from PIL import Image
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('assets/dials', exist_ok=True); os.makedirs('assets/small', exist_ok=True)
MANUAL = {  # slug: (bron, cx, cy, r)  — r = straal van het zichtbare scherm, zonder bezel/tickmarks
    'radar':      (os.path.expanduser('~/Desktop/App-screenshots/Radar/full/s1.png'), 638, 773, 468),
    'caffi':      ('assets/screens/caffi-1.jpg', 649, 575, 298),
    'convertr':   ('assets/screens/convertr-2.jpg', 1028, 500, 243),
    'cardvault':  ('assets/screens/cardvault-2.jpg', 725, 626, 193),
    'morsetap':   ('assets/screens/morsetap-2.jpg', 378, 519, 232),
    'rallypoint': ('assets/screens/rallypoint-2.jpg', 733, 488, 180),
}
for slug, (src, cx, cy, r) in MANUAL.items():
    dst = f'assets/dials-src/{slug}.png'
    if not os.path.exists(dst) and os.path.exists(src):
        im = Image.open(src).convert('RGB')
        im.crop((cx - r, cy - r, cx + r, cy + r)).resize((454, 454), Image.LANCZOS).save(dst)
        print('manual crop ->', dst)
for app in json.load(open('data.json')):
    s = app['slug']; src = f'assets/dials-src/{s}.png'
    if not os.path.exists(src):
        print('GEEN dials-src voor', s, '(refresh.py-fallback blijft staan)'); continue
    im = Image.open(src).convert('RGB')
    if im.size != (454, 454): im = im.resize((454, 454), Image.LANCZOS)
    im.save(f'assets/dials/{s}.jpg', quality=90, optimize=True)
    im.resize((320, 320), Image.LANCZOS).save(f'assets/small/dial-{s}.jpg', quality=82, optimize=True)
print('klaar')
