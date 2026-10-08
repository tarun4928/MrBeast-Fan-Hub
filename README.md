# BEAST / A STORY OF SCALE

A fan-made Flask web application inspired by MrBeast / Jimmy Donaldson. It is designed as a submission-ready creator website with a strong visual identity, a searchable video discovery experience, a research-led growth timeline, and a working backend form.

## Pages
- `/` — 100-thumbnail cinematic homepage with high-contrast readability overlay.
- `/discover` — searchable and filterable MrBeast video universe.
- `/journey` — growth timeline, mindset/struggle narrative and year-by-year release context.
- `/join` — working community signup form backed by SQLite.

## Video data
At startup the app tries to download a public MrBeast video analytics CSV from GitHub and caches it locally for 12 hours. The source contains video IDs, titles, publication dates, engagement metrics and YouTube thumbnail URLs. If the network is unavailable, the app automatically falls back to `data/fallback_videos.json`.

## Run locally
```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Deploy on Render
The repository includes `render.yaml` and `Procfile`.
Build: `pip install -r requirements.txt`
Start: `gunicorn app:app`

## Backend form
The form posts to `POST /api/join` and stores entries in `data/community.db`.

## Important note
This is a fan-made educational project and is not an official MrBeast/Beast Industries website. YouTube thumbnails and video metadata remain the property of their respective rights holders.

### Homepage visual wall update
The homepage now uses `static/img/mrbeast-100-wall.png` as a fixed 10 x 10 cinematic thumbnail wall. The image has been pre-darkened so the foreground copy remains readable, with repeated subtle brand-style stamps distributed across the wall. The interactive video catalog remains on the Discover page.

### Homepage visual treatment
The homepage uses the 10×10 thumbnail wall as a repeating full-page wallpaper. Text-heavy sections sit on localized translucent dark/relevant-color panels so the thumbnails remain visible while the content stays readable.
