You are a senior web designer and front-end developer. Rebuild the website of my company GerrOS from scratch. Design, layout, typography, colour, motion and page structure are entirely your call: surprise me, avoid anything that looks like a generic template, and make it feel like a small, confident studio that builds precise tools for wrists. Below is everything the site must contain and the constraints it must respect. Do not ask me design questions; decide and build.

## Who we are
- GerrOS is a one-person app studio from the Netherlands (sole proprietorship, founder Thijs). Domain: https://gerros.app
- We build apps for Garmin watches (Connect IQ) and, since 2026, for Wear OS (Google Play). Every app runs fully on the watch: no phone, no account, no data leaves the device.
- Positioning: small, focused watch apps with a real "engine" inside (they calculate, predict or advise; they are not dumb trackers), a clean interface (thin ring, one big number, one muted line), five languages (English, Dutch, German, French, Spanish), and support for both touch and button-only watches.
- Support e-mail: thijsjwger@gmail.com. No phone number, no physical address on the site.

## What the site must contain (pages are a suggestion; merge or split as you see fit)
1. Home: who we are in one breath, a way to browse all apps without a huge grid on the home page (a compact horizontal strip or similar), the latest releases, and a route into the app catalogue.
2. All apps: a catalogue of every app with filtering by category and search. Categories: Health & habits · Sport & outdoors · Money & work · Everyday tools · Watch faces. Each app shows icon, name, one-line tagline, store rating and number of reviews when available, and an "In review" badge when the app is submitted but not yet approved.
3. One page per app: hero screenshot, tagline, full description, 5 screenshots, version, what's new (release notes), number of supported devices, rating, link to the Garmin Connect IQ store page (or Google Play for Wear OS apps), and the price (all apps are paid, $1.99 / €2.49).
4. Wear OS: the apps that also exist for Google's watches (Caffi live on Google Play soon; Sobr, BreathGym and Convertr ported and coming), with Play Store links when available.
5. "Find your app": a short guided chooser (a few questions about what someone wants from their watch) that ends in 1–3 recommended apps.
6. What's new: a chronological feed of releases across all apps (version, date, release notes).
7. Studio: how we work (idea → research on forums and store gaps → build → test in the simulator on small, MIP and button-only watches → store), the design principles above, and that every app has an engine (examples: Racecast's personal fatigue factor, Caffi's pharmacokinetic caffeine curve, Adapt's measured TDEE, Recover's heart-rate recovery constant).
8. Support: FAQ (installing a Connect IQ app, why an app asks for a permission, refunds go through Garmin/Google, which watches are supported, languages) and the support e-mail.
9. Privacy policy at exactly /privacy (this URL is registered in app stores and must keep working): no data is collected by us, everything is stored on the watch, no analytics, no cookies except what the hosting provider needs, contact e-mail.

## The apps (slug · name · category · status · tagline)
smokeless · Smokeless · health · live · Quit-smoking tracker with cravings, savings and badges
fasted · Fasted · health · live · Intermittent fasting timer, from 16:8 to Ramadan
breathgym · BreathGym · health · live · Breath-hold training with CO₂ and O₂ tables
caffi · Caffi · health · live (also Wear OS) · Caffeine curve that protects your sleep
sobr · Sobr · health · live · Blood-alcohol estimate, live, on your wrist
jetshift · JetShift · health · live · A light plan that beats jet lag
earned · Earned · health · live · Burned calories, shown as food you can picture
recover · Recover · health · in review · Rest timer driven by your heart rate
adapt · Adapt · health · in review · Calorie target that learns from your scale
rallypoint · RallyPoint · sport · live · Score tracker for padel, tennis, pickleball and more
strike · Strike · sport · live · Bowling scoreboard with splits and six players
zeitnot · Zeitnot · sport · live · Chess clock with Fischer, Bronstein and delay
speedometer-pro · Speedometer Pro · sport · live · GPS speedometer with ten instrument faces
altizone · AltiZone · sport · live · Barometric altimeter with colour zones and alarms
spotsave · SpotSave · sport · live · Save any spot, walk straight back to it
reactr · Reactr · sport · live · Reaction-time trainer with a world ranking
racecast · Racecast · sport · in review · Race predictor: 5K to marathon from one result
cue · Cue · sport · in review · Snooker and pool scoring on your watch
shiftpay · ShiftPay · money · live · Watch your shift earnings tick up every second
spent · Spent · money · live · Daily budget: what you may still spend today
pitstop · PitStop · money · in review · Fuel log with fill-up predictions and trip costs
podium · Podium · money · live · Speaker timer that tells you if you run behind
listo · Listo · tools · live · Grocery list in colour, sorted by aisle
remindersplus · Reminders+ · tools · live · Everything that repeats, from minutes to years
convertr · Convertr · tools · live · Units and live currencies in 18 categories
cardvault · CardVault · tools · live · Loyalty cards, tickets and 2FA codes
morsetap · MorseTap · tools · live · Learn, practise and translate Morse code
wordclock · WordClock · faces · live · The time in words, in ten languages
redline · Redline · faces · live · Racing dashboard with heart-rate zones
triptych · Triptych · faces · live · Cockpit HUD with everything in one glance

## Data and images you can rely on (do not invent content)
- A JSON file `data.json` with one object per app: id, slug, name, desc (full English description), nl (Dutch description), rating, reviews, downloads, version, category, changed (date), whatsnew, devices (count), icon path, shots (list of 5 screenshot paths). It is regenerated from the Garmin store API by a script we already have; build the site so it reads this JSON (a small Python or Node build step is fine, or a static site generator you choose). In-review apps are in the same JSON with rating null.
- Images per app: `assets/icons/<slug>.png` (500×500 store cover, watch on off-white), `assets/dials/<slug>.jpg` (454×454 sharp capture of the round watch screen, black background: perfect for round crops), `assets/screens/<slug>-1..5.jpg` (1536×1024 marketing screenshots with a watch and a headline), plus web-optimised variants in `assets/small/`.
- Round watch screens must always be shown as perfect circles, never cropped or stretched.

## Constraints
- Static site: plain HTML, CSS and vanilla JavaScript (no framework runtime, no build-time CMS). It is deployed as a static site on Render; the root is the repository root; `/privacy` must resolve (privacy.html plus a redirect rule is fine).
- Fast and lightweight: Lighthouse performance and accessibility ≥ 95 on mobile, lazy-loaded images, responsive images, system or self-hosted fonts (Google Fonts allowed), no external trackers.
- Fully responsive from 360 px phones to wide desktops; touch-friendly.
- Accessible: semantic HTML, keyboard navigation, visible focus, alt texts, colour contrast AA, respects prefers-reduced-motion.
- SEO: per-page titles and meta descriptions, Open Graph tags with the app's hero screenshot, a sitemap.xml and robots.txt, canonical URLs, clean URLs (`/apps/<slug>`).
- Light and dark mode both designed properly (not just inverted).
- English only for now, but structure the copy so a Dutch version can be added later.
- Write all copy yourself in a direct, concrete voice: no marketing fluff, no exclamation marks, no "revolutionary". Short sentences. Facts about what each app does.

## Deliverable
The complete project as files (HTML, CSS, JS, build script, README with the build and deploy steps), with example data so it renders immediately. Explain briefly the design direction you chose and why, then give the files.
