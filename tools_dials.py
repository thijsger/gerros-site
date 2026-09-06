#!/usr/bin/env python3
# tools_dials.py — snijdt de wijzerplaat (het zwarte scherm) scherp uit de grote store-screenshot
# van elke app en bewaart hem als assets/dials/<slug>.jpg (640x640, midden = midden van het scherm).
import json, os
import numpy as np
from PIL import Image
d = json.load(open('data.json'))
os.makedirs('assets/dials', exist_ok=True)
def find_dial(im):
    a = np.asarray(im.convert('RGB')).astype(int)
    dark = (a.max(axis=2) < 70)
    h, w = dark.shape
    best = (0, 0, 0, 0)  # width, y, x0, x1
    for y in range(0, h, 2):
        row = dark[y]
        # langste aaneengesloten donkere run in deze rij
        run = 0; start = 0
        for x in range(w):
            if row[x]:
                if run == 0: start = x
                run += 1
                if run > best[0]: best = (run, y, start, x)
            else:
                run = 0
    wd, y, x0, x1 = best
    cx = (x0 + x1) / 2.0
    # verticale uitgestrektheid door het midden: de kast (band loopt door, dus beperk tot ~1.1x breedte)
    col = dark[:, int(cx)]
    top = y; bot = y
    while top > 0 and col[top - 1]: top -= 1
    while bot < h - 1 and col[bot + 1]: bot += 1
    cy = y if (bot - top) > 1.4 * wd else (top + bot) / 2.0
    return cx, cy, wd / 2.0
for app in d:
    src = app['shots'][0] if app['shots'] else app['icon']
    im = Image.open(src).convert('RGB')
    cx, cy, r = find_dial(im)
    rd = r * 0.84                      # scherm zonder bezel/tickmarks
    box = (int(cx - rd), int(cy - rd), int(cx + rd), int(cy + rd))
    crop = im.crop(box).resize((640, 640), Image.LANCZOS)
    crop.save(f"assets/dials/{app['slug']}.jpg", quality=88, optimize=True)
    print(app['slug'], im.size, 'r=%d' % r, box)
