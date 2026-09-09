#!/usr/bin/env python3
# refresh.py — haalt de app-lijst opnieuw uit de Connect IQ-API, ververst data.json (met behoud van
# de lokale pending-apps), downloadt ontbrekende iconen/screenshots, maakt de web-varianten en bouwt
# de site. Draaien na elke store-wijziging.
import json, os, subprocess, sys
from PIL import Image
os.chdir(os.path.dirname(os.path.abspath(__file__)))
API = 'https://apps.garmin.com/api/appsLibraryExternalServices/api/asw/apps/developer/de6acef4-c127-4cf2-84bc-baccde5f8b16?pageSize=30'
IMG = 'https://services.garmin.com/appsLibraryExternalServices/api/'
raw = json.loads(subprocess.run(['curl', '-sL', API], capture_output=True, text=True).stdout)
if not isinstance(raw, list) or not raw:
    sys.exit('API gaf niets terug')
old = {a['slug']: a for a in json.load(open('data.json'))}
def slug_of(name):
    for sep in (' - ', ' – ', ' — ', ' | '):
        name = name.split(sep)[0]
    return name.strip().lower().replace(' ', '-').replace('+', 'plus')
new = []
seen = set()
alldev = set()
SINGLE = 'https://apps.garmin.com/api/appsLibraryExternalServices/api/asw/apps/'
for a in raw:
    # De lijst-API loopt achter op de per-app-API (release-notes van een net ingediende versie
    # staan daar al); teksten en versie dus per app vers ophalen.
    try:
        one = json.loads(subprocess.run(['curl', '-sL', SINGLE + a['id'] + '?locale=en-US'], capture_output=True, text=True).stdout)
        if isinstance(one, dict) and one.get('appLocalizations'):
            a['appLocalizations'] = one['appLocalizations']
            for k in ('latestExternalVersion', 'latestInternalVersion', 'changedDate', 'averageRating', 'reviewCount', 'downloadCount'):
                if one.get(k) is not None: a[k] = one[k]
    except Exception:
        pass
    loc = {l['locale']: l for l in a['appLocalizations']}
    en = loc.get('en') or a['appLocalizations'][0]
    slug = slug_of(en['name']); seen.add(slug)
    ic = f'assets/icons/{slug}.png'
    if not os.path.exists(ic):
        subprocess.run(['curl', '-sL', IMG + 'icons/' + a['iconFileId'], '-o', ic])
    shots = []
    for i, s in enumerate(a.get('screenshotFileIds') or []):
        p = f'assets/shots/{slug}-{i+1}.jpg'
        if not os.path.exists(p):
            subprocess.run(['curl', '-sL', IMG + 'screenshots/' + s, '-o', p])
        shots.append(p)
    alldev |= set(a.get('compatibleDeviceTypeIds') or [])
    new.append({'id': a['id'], 'slug': slug, 'name': en['name'], 'desc': en['description'],
                'nl': (loc.get('nl') or {}).get('description', ''), 'type': a['typeId'],
                'rating': a.get('averageRating'), 'reviews': a.get('reviewCount'), 'downloads': a.get('downloadCount'),
                'version': a.get('latestExternalVersion'), 'category': a.get('categoryId'), 'icon': ic, 'shots': shots,
                'changed': a.get('changedDate'), 'whatsnew': en.get('whatsNew') or '',
                'devices': len(a.get('compatibleDeviceTypeIds') or []), 'updates': a.get('latestInternalVersion') or 1})
# lokale apps die (nog) niet in de API staan (in review) blijven staan
for slug, a in old.items():
    if slug not in seen:
        new.append(a)
json.dump(new, open('data.json', 'w'), indent=1, ensure_ascii=False)
# web-varianten voor wat nieuw is
for a in new:
    s = a['slug']
    if not os.path.exists(f'assets/covers/{s}.jpg'):
        im = Image.open(a['icon']).convert('RGB')
        im.save(f'assets/covers/{s}.jpg', quality=92, optimize=True)
        im.resize((360, 360), Image.LANCZOS).save(f'assets/small/{s}.jpg', quality=76, optimize=True)
    if not os.path.exists(f'assets/dials/{s}.jpg'):
        c = Image.open(a['icon']).convert('RGB'); w, h = c.size; r = w * 0.255; cx, cy = w / 2, h * 0.485
        d = c.crop((int(cx - r), int(cy - r), int(cx + r), int(cy + r))).resize((454, 454), Image.LANCZOS)
        d.save(f'assets/dials/{s}.jpg', quality=90, optimize=True)
        d.resize((320, 320), Image.LANCZOS).save(f'assets/small/dial-{s}.jpg', quality=82, optimize=True)
    for i, src in enumerate(a['shots']):
        q = f'assets/screens/{s}-{i+1}.jpg'
        if not os.path.exists(q):
            im = Image.open(src).convert('RGB'); w, h = im.size
            im.save(q, quality=90, optimize=True)
            im.resize((960, int(h * 960 / w)), Image.LANCZOS).save(f'assets/small/{s}-{i+1}.jpg', quality=78, optimize=True)
print(f'{len(raw)} apps uit de API, {len(new)} totaal, {len(alldev)} toesteltypes (DEVICES in build.py)')
subprocess.run([sys.executable, 'build.py'], check=True)
