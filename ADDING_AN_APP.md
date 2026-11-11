# Adding an app to the site

The site shows only the apps listed in `meta.json` → `"show"`, in that order. Each of those apps gets
its images from its local store folder (`App-screenshots/<Folder>/store/`), not from the store API.

## 1. Store data

The app must exist in `data.json` (name, description, rating, version, release notes). For an app that
is in the Connect IQ Store, `python3 refresh.py` fetches it. Check the slug it got:

    python3 -c "import json;print([a['slug'] for a in json.load(open('data.json'))])"

## 2. meta.json

Add (or complete) the entry under `"apps"` and put the slug in `"show"`:

    "convertr": {
      "title": "Convertr",
      "tag": "Units and live currencies in 18 categories",     what it is, no sales talk, no full stop
      "cat": "tools",                                            health | sport | money | tools | games | faces
      "accent": "#F8A858",                                       the one colour of the app (see step 3)
      "screens": [                                               headline + subline of pagina-01..05, in order
        ["Headline of image 1", "Subline of image 1"],
        ["Headline of image 2", "Subline of image 2"]
      ]
    }

- `"screens"` is used for alt texts and for the captions under the small screens on the Apps page.
  Copy the text that is in the images.
- `"pending": true` = submitted but not approved yet: the page says "In review" and shows no store link.
  Remove it once the app is live.
- `"id"` is only needed when the app is not in the store API yet (in review).

## 3. Images

    python3 tools_assets.py <slug> "<path>/App-screenshots/<Folder>" --check /tmp/check-<slug>.jpg

The folder needs `store/cover-500.png`, `store/pagina-01.jpg` … and (optional) `store/hero-1440x720.png`.
The script writes the cover, the share image, the marketing images and the round screens ("dials"), and
registers the app in `assets/local.json`.

- It measures the screen circle in every image and prints centre, radius and how sure it is.
  A line ending in `<-- NAKIJKEN` needs a look. Open the `--check` sheet either way: top row = the
  source with the measured circle in red, bottom row = the cut-out. The circle must lie on the thin
  line at the edge of the screen.
- It prints the most common colours in the main screen. Pick the app's colour from those (or from the
  app itself) and put it in `"accent"`.
- The main screen comes from image 1 (same screen as the cover, but larger). Other image: `--main 3`;
  from the cover: `--main cover`.
- New images for an existing app: run the same command again; it overwrites.

As long as a slug is in `assets/local.json`, `refresh.py` and `tools_dials.py` do not touch its images.

## 4. Build

    python3 refresh.py      # store data + build   (or only: python3 build.py)

Then look at `index.html`, `apps.html` and `apps/<slug>.html`. `dist/gerros.html` is the whole site
in one file for a quick preview.

## Removing an app from the site

Take the slug out of `"show"` and run `python3 build.py`. Delete `apps/<slug>.html` by hand; the build
does not remove pages it no longer writes.
