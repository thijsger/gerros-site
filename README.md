# GerrOS / The wrist engine

A static watch studio with a cinematic, scroll-driven WebGL homepage. A custom 3D sports watch rotates through Caffi, Racecast and Spent, with the original app screen textures. Charcoal, acid lime, oversized typography and contrasting editorial sections. Native HTML, CSS and vanilla JavaScript. No runtime framework, fonts, analytics, cookies or browser storage. Theme controls affect the current page; the default follows the device. Motion can be paused and respects reduced-motion preferences.

## Build and preview

Run from this repository root with Python 3.10 or newer:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 build.py
python3 -m http.server 8000 --directory public
```

Open http://localhost:8000. Use an HTTP server, not file://, for the guided chooser. Generated HTML is also written to the repository root for compatibility with the previous project. `public/` is the deployable artifact. No Node build is required. Pillow generates responsive WebP derivatives once, then updates only changed assets.

## Render

Connect the repository as a Static Site, or use the included `render.yaml` blueprint. Root directory: repository root. Build command: `pip install -r requirements.txt && python3 build.py`. Publish directory: `public`. Keep the rewrite `/privacy` → `/privacy.html`. Every other clean route has its own directory and index.html. Existing .html app URLs remain functional. Set gerros.app as the custom domain; canonical and sitemap URLs use https://gerros.app. Publishing is not performed by this project setup.

## Data and copy

The real supplied `data.json` is included and renders immediately. Do not replace it with invented ratings. Continue running the existing `refresh.py` store script, then run `build.py`. Each app provides slug, id, descriptions, rating, reviews, version, changed (Unix milliseconds), whatsnew, device count, icon and shots. `meta.json` supplies the editorial names, taglines, categories and explicit pending status because the API categories are numeric. A null rating alone does not imply review status. Change `pending` to false when an app is approved. Full descriptions and release notes are escaped and formatted at build time.

Assets use `assets/icons`, `assets/dials` and `assets/screens`; `assets/web` is generated. The supplied marketing screenshot set takes precedence over older `assets/shots` references in the API JSON. Preserve original screenshots for social previews. Watch dial images always retain a square aspect ratio and 50% border radius.

Google Play URLs are not supplied, so Wear OS entries say coming soon without fabricated links. Add a verified `play_url` to the corresponding app in `meta.json` to enable a Google Play button. The Garmin links use the actual store IDs. Prices are the supplied $1.99 / €2.49.

English editorial copy is centralized in `build.py`; Dutch app descriptions already live in `data.json` under `nl`. To add Dutch, extract the page copy to a locale dictionary, select desc/nl by locale, generate /nl/ routes, and add alternate hreflang tags. Avoid translating IDs, slugs or store metadata.

The release feed shows the latest supplied release for each app, chronologically. The source does not include historical release records. The finder ranks apps using all three answers and returns up to three within the requested category. All catalogue pages and app content work without JavaScript; the chooser provides a catalogue fallback.

## Checks

```sh
python3 verify.py
node --check site.js
```

For mobile Lighthouse, serve `public/` and audit home, catalogue, one app page and finder with Chrome Lighthouse. Target performance and accessibility: 95+. No score is promised without measuring the deployed site. Confirm store metadata and hosting-provider privacy details before publishing. The current locally modified build was preserved as `build.before-rebuild.py` and is excluded from publication.

## Missing source assets

The source has four screenshots for ShiftPay, Reminders+, JetShift, MorseTap, SpotSave, Redline, Triptych, Convertr and RallyPoint; WordClock has two. Their pages show all available images. Add the missing numbered assets/screens/<slug>-N.jpg files and rebuild to reach five. No substitute screenshots have been invented.

## Validation result — 8 September 2026

Local Chrome Lighthouse, mobile defaults: home 99 performance / 100 accessibility; Caffi detail 99 / 100. Reports are in reports/. The audit also caught a decorative logo letter in the accessible name, fixed after measurement with aria-hidden. Browser checks passed at 360px across home, apps, Caffi, Wear OS, finder, studio, support and privacy: no page overflow. Category/search/empty state, three-answer recommendations, restart, colour theme, mobile navigation, Escape, reduced motion and JavaScript error checks passed. Preview PNGs are in previews/. Production hosting may change scores.

## 3D homepage — second edition

`watch.js` builds an original sports-watch visualization from geometry: silicone strap, case, machined bezel, screws, physical buttons and a circular texture-mapped screen. It is a Garmin-style study, not an official or model-accurate Garmin CAD asset. There is no Three.js or external 3D asset dependency. WebGL draws only on scroll, resize, scene selection or texture load; it stops rendering offscreen and caps pixel density at 1.7. Scroll position controls rotation, camera distance and app selection. Numbered controls jump to scenes and remain usable by keyboard.

Reduced motion uses a short static stage with manual app selection. Pause motion holds the watch front-facing while leaving navigation available. WebGL failure shows an original circular app screenshot; no-JavaScript readers retain the intro, catalogue and all content below. HTML content is independent of canvas. The first Lighthouse reports describe the previous design; see reports/home-3d-lighthouse.json for this version when present.
