from flask import Flask, render_template, jsonify, request
import csv, io, json, os, sqlite3, time, re, xml.etree.ElementTree as ET
from pathlib import Path
import requests

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / 'data'
CACHE_FILE = DATA_DIR / 'videos_cache.json'
FALLBACK_FILE = DATA_DIR / 'fallback_videos.json'
DB_FILE = DATA_DIR / 'community.db'
DATA_DIR.mkdir(exist_ok=True)

SOURCE_URL = 'https://raw.githubusercontent.com/kartikk-cmd/MrBeast-YouTube-Data-Analytics-Virality-Analysis/main/videos_mrbeast.csv'
CACHE_HOURS = 12

app = Flask(__name__)


def db_conn():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db_conn()
    con.execute('''
        CREATE TABLE IF NOT EXISTS community_signups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            favorite_topic TEXT,
            message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    con.commit(); con.close()


def load_fallback():
    try:
        with open(FALLBACK_FILE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def get_rss_videos():
    rss_url = 'https://www.youtube.com/feeds/videos.xml?channel_id=UCX6OQ3DkcsbYNE6H8uQQuVA'
    try:
        r = requests.get(rss_url, timeout=15, headers={'User-Agent': 'MrBeast-Fan-Hub/1.0'})
        r.raise_for_status()
        root = ET.fromstring(r.text)
        ns = {'yt':'http://www.youtube.com/xml/schemas/2015', 'atom':'http://www.w3.org/2005/Atom', 'media':'http://search.yahoo.com/mrss/'}
        out=[]
        for entry in root.findall('atom:entry', ns):
            vid=entry.findtext('yt:videoId', default='', namespaces=ns)
            title=entry.findtext('atom:title', default='', namespaces=ns)
            published=entry.findtext('atom:published', default='', namespaces=ns)
            if vid and title:
                out.append({'id':vid,'title':title,'published_at':published,'published_date':published[:10],'views':0,'likes':0,'comments':0,'duration_seconds':0,'thumbnail':f'https://i.ytimg.com/vi/{vid}/maxresdefault.jpg','url':f'https://www.youtube.com/watch?v={vid}'})
        return out
    except Exception:
        return []

def get_raw_videos(force=False):
    now = time.time()
    if not force and CACHE_FILE.exists():
        try:
            if now - CACHE_FILE.stat().st_mtime < CACHE_HOURS * 3600:
                with open(CACHE_FILE, encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
    try:
        r = requests.get(SOURCE_URL, timeout=30, headers={'User-Agent': 'MrBeast-Fan-Hub/1.0'})
        r.raise_for_status()
        rows = list(csv.DictReader(io.StringIO(r.text)))
        videos = []
        for row in rows:
            if row.get('channel_id') != 'UCX6OQ3DkcsbYNE6H8uQQuVA':
                continue
            vid = row.get('video_id', '').strip()
            title = row.get('title', '').strip()
            if not vid or not title:
                continue
            videos.append({
                'id': vid,
                'title': title,
                'published_at': row.get('published_at',''),
                'published_date': row.get('published_date',''),
                'views': safe_num(row.get('viewCount')),
                'likes': safe_num(row.get('likeCount')),
                'comments': safe_num(row.get('commentCount')),
                'duration_seconds': safe_num(row.get('duration_seconds')),
                'thumbnail': row.get('thumbnail_url') or f'https://i.ytimg.com/vi/{vid}/maxresdefault.jpg',
                'url': f'https://www.youtube.com/watch?v={vid}',
            })
        # Most recent first in source; normalize and cap to a sensible browser payload.
        videos = dedupe_sort(get_rss_videos() + videos)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False)
        return videos
    except Exception:
        return load_fallback()


def safe_num(value):
    try:
        return int(float(value or 0))
    except Exception:
        return 0


def dedupe_sort(videos):
    seen = set(); out = []
    for v in sorted(videos, key=lambda x: x.get('published_at',''), reverse=True):
        if v['id'] in seen: continue
        seen.add(v['id']); out.append(v)
    return out


def classify(v):
    t = v['title'].lower()
    rules = [
        ('Philanthropy & Giving', ['blind', 'deaf', 'water', 'africa', 'animals', 'cure', 'food', 'give', 'giving', 'charity', 'donat', 'help', 'rescue', 'people get', 'teamtrees', 'teamseas', 'trees']),
        ('Survival & Adventure', ['survive', 'survived', 'stranded', 'antarctica', 'island', 'buried', 'jungle', 'ocean', 'sea', 'desert', 'alone']),
        ('Challenges & Competitions', ['last to', '100 people', '100 kids', 'fight', 'race', 'win', 'versus', 'vs ', 'competition', 'challenge', 'eliminate', 'answer the', 'first to']),
        ('Money & Giveaways', ['$','money','cash','million','thousand','giveaway','rich','poor','job']),
        ('Stunts & Experiments', ['laser', 'shredder', 'hydraulic', 'dangerous', 'trap', 'press', 'power tools', 'plane', 'race car']),
        ('Food & Taste Tests', ['food','pizza','cake','grocery','restaurant','chocolate','feastables','eat','candy','burger']),
        ('Creators & Celebrities', ['celebrity','youtube','youtuber','creator','famous','noah lyles','gordon ramsay','celebrity']),
        ('Gaming & Early Era', ['minecraft','fortnite','gaming','cod','call of duty','worst intros']),
    ]
    category = 'Spectacle & Storytelling'
    for name, keys in rules:
        if any(k in t for k in keys):
            category = name; break
    try:
        year = int((v.get('published_date') or v.get('published_at',''))[:4])
    except Exception:
        year = 0
    if year <= 2016: era = 'Early experimentation'
    elif year <= 2018: era = 'Breakout era'
    elif year <= 2020: era = 'Scale-up era'
    elif year <= 2022: era = 'Global challenge era'
    elif year <= 2024: era = 'Record-breaking era'
    else: era = 'Current spectacle era'
    sec = v.get('duration_seconds',0)
    if sec <= 60: fmt = 'Short-form'
    elif sec <= 900: fmt = 'Standard'
    else: fmt = 'Long-form / special'
    if sec <= 300: duration_band = 'Under 5 min'
    elif sec <= 900: duration_band = '5–15 min'
    elif sec <= 1800: duration_band = '15–30 min'
    else: duration_band = '30+ min'
    views = v.get('views',0)
    if views >= 500_000_000: view_band = '500M+ views'
    elif views >= 100_000_000: view_band = '100M–500M'
    elif views >= 50_000_000: view_band = '50M–100M'
    elif views >= 10_000_000: view_band = '10M–50M'
    else: view_band = 'Under 10M'
    tags = set(re.findall(r'[a-z0-9]+', t))
    taste = []
    mapping = {
        'high-stakes': ['win','million','cash','survive','dangerous','race','fight'],
        'feel-good': ['give','giving','help','blind','deaf','water','animal','food','rescue'],
        'extreme': ['dangerous','trap','shredder','laser','survive','antarctica','plane','ocean'],
        'funny': ['weird','crazy','trick','answer','gifts'],
        'social': ['people','kids','girls','boys','celebrity','youtuber','creator'],
    }
    for tag, keys in mapping.items():
        if any(k in t for k in keys): taste.append(tag)
    return {**v, 'category': category, 'era': era, 'format': fmt, 'duration_band': duration_band, 'view_band': view_band, 'taste': taste}


def enrich(videos):
    return [classify(v) for v in videos]


# Verified milestone context. These are deliberately milestone-level; we do not claim an exact
# subscriber delta per individual video because such causal daily subscriber attribution is not
# publicly available in a reliable form.
MILESTONES = [
    {'date':'2012','subscribers':'Created','title':'The channel begins','story':'Jimmy Donaldson uploads his first videos at 13 under MrBeast6000, experimenting with gaming and commentary.'},
    {'date':'2016','subscribers':'~30K','title':'The risk becomes real','story':'After building the Worst Intros audience, he leaves college to pursue YouTube full-time. The choice was not immediately supported at home.'},
    {'date':'2017','subscribers':'1M','title':'Breakout','story':'Extreme commitment to studying virality and highly shareable challenges starts turning attention into a repeatable format.'},
    {'date':'2018','subscribers':'10M','title':'Scale arrives','story':'Giveaways, challenge concepts and a bigger production mindset push the channel into a new tier.'},
    {'date':'2019','subscribers':'20M+','title':'Content becomes a system','story':'The channel leans harder into teams, repeatable challenge formats and reinvestment into bigger ideas.'},
    {'date':'2020','subscribers':'~30M+','title':'Bigger than one channel','story':'MrBeast expands into multiple channels and large-scale donation videos while continuing to reinvest in main-channel storytelling.'},
    {'date':'2021','subscribers':'50M','title':'Global scale','story':'The channel becomes a global entertainment operation, with philanthropy becoming a major part of the public identity.'},
    {'date':'2022','subscribers':'100M','title':'100 million','story':'The main channel passes 100 million subscribers, confirming that the high-budget challenge model has reached global scale.'},
    {'date':'2023','subscribers':'200M','title':'Another doubling','story':'Subscriber growth accelerates again as huge-format videos and philanthropy continue to amplify one another.'},
    {'date':'2024','subscribers':'300M','title':'#1 on YouTube','story':'MrBeast becomes the first individual creator to pass 300 million subscribers and overtakes T-Series for the top subscriber position.'},
    {'date':'2025','subscribers':'400M+','title':'Creator becomes ecosystem','story':'The MrBeast brand expands across entertainment, products, philanthropy and larger-format productions.'},
    {'date':'2026','subscribers':'500M+','title':'New ceiling','story':'The channel reaches the half-billion scale, showing what years of iteration, reinvestment and audience-first packaging can compound into.'},
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/discover')
def discover():
    return render_template('discover.html')

@app.route('/journey')
def journey():
    return render_template('journey.html', milestones=MILESTONES)

@app.route('/join')
def join():
    return render_template('join.html')

@app.get('/api/videos')
def api_videos():
    force = request.args.get('refresh') == '1'
    videos = enrich(get_raw_videos(force=force))
    # 100 is intentionally the default for the home page wall.
    try: limit = max(1, min(int(request.args.get('limit', 100)), 1200))
    except ValueError: limit = 100
    return jsonify({'videos': videos[:limit], 'total_loaded': len(videos), 'source': SOURCE_URL})

@app.get('/api/filters')
def api_filters():
    videos = enrich(get_raw_videos())
    def uniq(key):
        vals = sorted({v.get(key) for v in videos if v.get(key)})
        return vals
    return jsonify({
        'categories': uniq('category'), 'years': sorted({str(v.get('published_date','')[:4]) for v in videos if v.get('published_date')}, reverse=True),
        'eras': uniq('era'), 'formats': uniq('format'), 'duration_bands': uniq('duration_band'), 'view_bands': uniq('view_band'),
        'total': len(videos)
    })

@app.post('/api/join')
def api_join():
    data = request.get_json(silent=True) or request.form
    name = str(data.get('name','')).strip()
    email = str(data.get('email','')).strip().lower()
    topic = str(data.get('favorite_topic','')).strip()
    message = str(data.get('message','')).strip()
    if len(name) < 2:
        return jsonify({'ok':False,'error':'Please enter your name.'}), 400
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        return jsonify({'ok':False,'error':'Please enter a valid email address.'}), 400
    con = db_conn()
    try:
        con.execute('INSERT INTO community_signups (name,email,favorite_topic,message) VALUES (?,?,?,?)', (name,email,topic,message))
        con.commit()
        return jsonify({'ok':True,'message':'You are officially on the community list. Welcome to the Beast mindset.'})
    except sqlite3.IntegrityError:
        return jsonify({'ok':False,'error':'That email is already on the list. You are already in.'}), 409
    finally:
        con.close()

@app.get('/health')
def health():
    return {'status':'ok'}

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
