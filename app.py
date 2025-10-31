# app.py — Timmy Ship v1.1 (Sanitizer + FB-Safe OG Builder)
# Laws:
# - Local-only 127.0.0.1
# - NEVER bind 5000; port-hop to a free port (start 5050)
# - Auto-open "/"
# - Big readable text
# - Hard-clean YouTube links: store ONLY 11-char ID (+ optional start seconds)
# - Always render youtube-nocookie.com/embed/<ID>[?start=SS]
# - Ignore external query params (fbclid, utm_*, list, index, si, feature, etc.)
# - FB-safe Open Graph tags with absolute https URLs & 1200x630 image

import os, re, json, socket, threading, time, webbrowser
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string

APP_NAME = "Timmy Ship v1.1 — Sanitizer + FB-OG"
ROOT = Path(__file__).parent.resolve()
STATIC_DIR = ROOT / "static"
OG_DIR = STATIC_DIR / "og"
DATA_DIR = STATIC_DIR / "data"
DATA_FILE = DATA_DIR / "state.json"

# ----------- YOUR PUBLIC BASE (used for absolute OG URLs) -----------
# Override with env PUBLIC_BASE_URL if needed.
PUBLIC_BASE_URL = os.getenv(
    "PUBLIC_BASE_URL",
    "https://timmyjonesusn-netizen.github.io/bubbleworld-ship"
)

# ------------------------- DEFAULT STATE -------------------------
DEFAULT_STATE = {
    "rooms": {
        "1": {"video_id": "", "start": 0, "title": "Engine Room — Hammer Online"},
        "2": {"video_id": "", "start": 0, "title": "Room 2 — Purple Play"},
        "3": {"video_id": "", "start": 0, "title": "Room 3 — Suno Set"},
        "8": {"video_id": "", "start": 0, "title": "Room 8 — Reel Core"}
    },
    "brand": {
        "site_title": "TimmyTime • Bubble World Ship",
        "tagline": "Creative Rooms, Reels, and Music.",
        "theme_color": "#ff3bd1",
        "bg": "#05000c",
        "fg": "#ffffff"
    }
}

# ------------------------- SETUP FOLDERS/FILES -------------------------
STATIC_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
OG_DIR.mkdir(parents=True, exist_ok=True)

def ensure_default_state():
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps(DEFAULT_STATE, indent=2), encoding="utf-8")

def ensure_default_og():
    """Create a 1200x630 default banner if missing."""
    placeholder = OG_DIR / "ship_default_1200x630.png"
    if not placeholder.exists():
        try:
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (1200, 630), (5, 0, 12))  # deep space
            d = ImageDraw.Draw(img)
            # simple diagonal glow bar
            for i in range(0, 1200, 6):
                shade = 12 + int(8 * (i/1200))
                d.line([(i, 0), (i-80, 630)], fill=(255, 59, 209, 40), width=3)
            img.save(str(placeholder), format="PNG")
        except Exception:
            # If Pillow not available, silently skip; you can drop your own image
            pass

ensure_default_state()
ensure_default_og()

# ------------------------- APP CORE -------------------------
app = Flask(__name__)

YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")

def load_state():
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_STATE.copy()

def save_state(state):
    DATA_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

def extract_youtube_id(raw: str):
    """
    Accepts:
      - https://youtu.be/ID
      - https://www.youtube.com/watch?v=ID
      - https://www.youtube.com/shorts/ID
      - raw 11-char ID
      Optional t= / start= seconds allowed
    Returns (video_id, start_seconds) or (None, 0)
    """
    if not raw:
        return None, 0
    s = raw.strip()

    # start seconds: t=42 or start=42 (simple numeric)
    start = 0
    t_match = re.search(r"(?:[?&]|^)t=([0-9]+)s?\b", s) or re.search(r"(?:[?&]|^)start=([0-9]+)\b", s)
    if t_match:
        try:
            start = int(t_match.group(1))
        except ValueError:
            start = 0

    # raw ID
    if YOUTUBE_ID_RE.match(s):
        return s, start

    # shorts
    m = re.search(r"youtube\.com/shorts/([A-Za-z0-9_-]{11})", s)
    if m:
        return m.group(1), start

    # watch?v=
    m = re.search(r"[?&]v=([A-Za-z0-9_-]{11})\b", s)
    if m:
        return m.group(1), start

    # youtu.be/<id>
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})\b", s)
    if m:
        return m.group(1), start

    return None, 0

def build_embed(video_id: str, start: int = 0):
    base = f"https://www.youtube-nocookie.com/embed/{video_id}"
    return f"{base}?start={start}" if start and start > 0 else base

def room_meta(state, room_id: str):
    r = state["rooms"].get(room_id, {"video_id":"", "start":0, "title":f"Room {room_id}"})
    vid = r.get("video_id") or ""
    start = int(r.get("start") or 0)
    embed = build_embed(vid, start) if vid else ""
    title = r.get("title") or f"Room {room_id}"
    return title, vid, start, embed

def ensure_room_og_image(room_id: str):
    """
    Ensure a per-room OG image exists; if not, use default.
    Returns absolute URL to the image.
    """
    custom = OG_DIR / f"room{room_id}_1200x630.png"
    if custom.exists():
        return f"{PUBLIC_BASE_URL}/static/og/room{room_id}_1200x630.png"
    # fallback to default
    return f"{PUBLIC_BASE_URL}/static/og/ship_default_1200x630.png"

def build_og_meta(room_id: str, title: str, video_id: str, start: int = 0):
    """
    Build a dict of OG tags with absolute https URLs so FB shows the full banner.
    """
    room_url = f"{PUBLIC_BASE_URL}/room/{room_id}"
    image_url = ensure_room_og_image(room_id)
    og = {
        "og:url": room_url,
        "og:title": title,
        "og:description": "TimmyTime • Bubble World Ship — Creative Rooms, Reels, and Music.",
        "og:image": image_url,
        "og:image:width": "1200",
        "og:image:height": "630",
        "og:type": "website"
    }
    if video_id:
        v = build_embed(video_id, start)
        og["og:video:url"] = v
    return og

# ------------------------- PAGES -------------------------
BASE_CSS = """
:root {
  --bg: {{brand['bg']}};
  --fg: {{brand['fg']}};
  --accent: {{brand['theme_color']}};
}
html, body { margin:0; padding:0; background:var(--bg); color:var(--fg);
  font-family:-apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif; }
h1 { font-size:3rem; margin:1rem; }
a { color:#ffb6ff; }
.room { display:block; margin:1rem; padding:1rem 1.2rem; background:#0f0f18; border:1px solid #222;
  border-radius:12px; color:#fff; text-decoration:none; font-size:1.4rem; }
.small { opacity:.85; font-size:.95rem; }
button { font-size:1.2rem; padding:.8rem 1.1rem; border-radius:10px; border:1px solid #444;
  background:var(--accent); color:#000; cursor:pointer; }
input[type=text], input[type=number] {
  font-size:1.2rem; padding:.8rem; border-radius:10px; border:1px solid #333; background:#0f0f18; color:#fff;
}
.inputrow { display:flex; gap:.6rem; flex-wrap:wrap; }
.player { aspect-ratio:16/9; width:min(960px, 96vw); max-width:100%; border-radius:14px; border:1px solid #222;
  overflow:hidden; background:#000; }
"""

HOME_TPL = f"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{{{{brand['site_title']}}}} — Dock</title>
<meta name="theme-color" content="{{{{brand['theme_color']}}}}">
<style>{BASE_CSS}</style>
</head>
<body>
  <h1>TimmyTime Dock</h1>
  <div class="small" style="margin:0 1rem .8rem 1rem;">{APP_NAME} — Paste any YouTube link in a room; it becomes <b>hard-clean</b> and final.</div>
  {{{{room_links}}}}
</body>
</html>
"""

ROOM_TPL = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{{ title }}</title>
<meta name="theme-color" content="{{ brand['theme_color'] }}" />
<link rel="canonical" href="{{ og['og:url'] }}" />
{% for k,v in og.items() %}
<meta property="{{k}}" content="{{v}}">
{% endfor %}
<style>""" + BASE_CSS + """</style>
</head>
<body>
  <div style="padding:1rem">
    <h1>{{ title }}</h1>

    <div class="inputrow" style="margin:.6rem 0 1rem 0;">
      <input id="paste" type="text" placeholder="Paste YouTube link or 11-char ID" autocomplete="off" style="flex:1;min-width:240px;">
      <input id="start" type="number" min="0" step="1" value="{{ start }}" title="Start seconds (optional)" style="width:120px;">
      <button onclick="lockVideo()">Lock Clean Link</button>
    </div>
    <div class="small">Accepts youtu.be/ID, watch?v=ID, /shorts/ID, or raw 11-char ID. We store only the ID (optional start). Everything else is ignored.</div>
    <div id="msg" class="small" style="color:#ff6b6b; display:none; margin-top:.3rem;"></div>
    <div id="ok" class="small" style="color:#7ef0a8; display:none; margin-top:.3rem;"></div>

    <div style="margin:1rem 0;">
      <div class="player">
        {% if embed %}
          <iframe id="yt" src="{{ embed }}" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowfullscreen referrerpolicy="strict-origin-when-cross-origin"
            style="border:0;width:100%;height:100%;"></iframe>
        {% else %}
          <div style="display:flex;align-items:center;justify-content:center;height:100%;color:#888;">No video locked yet.</div>
        {% endif %}
      </div>
      <div class="small" id="now" style="margin-top:.6rem;">
        {% if embed %}Now playing → {{ embed }}{% else %}Paste a link and press “Lock Clean Link”.{% endif %}
      </div>
      <div class="small" style="margin-top:.4rem;">
        <span style="text-decoration:underline;cursor:pointer;" onclick="copyClean()">Copy Clean Link</span>
        <span> • </span>
        <a target="_blank" href="https://developers.facebook.com/tools/debug/">Open Facebook Sharing Debugger</a>
      </div>
    </div>

    <div class="small">This page ignores any querystrings (fbclid, utm, list, si, feature, etc.). Only your locked ID controls playback.</div>
    <div class="small" style="margin-top:.5rem;"><a href="/">← Back to Dock</a></div>
  </div>

<script>
let CURRENT_EMBED = {{ embed|tojson }};
function copyClean(){
  if(!CURRENT_EMBED) return;
  navigator.clipboard.writeText(CURRENT_EMBED).then(()=>{
    const ok=document.getElementById('ok'); ok.style.display='block'; ok.textContent='Copied clean link.';
    setTimeout(()=>{ ok.style.display='none'; }, 1200);
  });
}
function lockVideo(){
  const raw = document.getElementById('paste').value.trim();
  const start = parseInt(document.getElementById('start').value || '0', 10);
  const msg = document.getElementById('msg'); msg.style.display='none'; msg.textContent='';
  fetch('/api/set_video', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({room_id:'{{ room_id }}', raw, start: isNaN(start)?0:start})
  }).then(r=>r.json()).then(d=>{
    if(!d.ok){
      msg.style.display='block'; msg.textContent=d.error || 'Unrecognized link — paste a YouTube URL or 11-char ID.';
      return;
    }
    CURRENT_EMBED = d.embed;
    const now = document.getElementById('now');
    now.textContent = 'Now playing → ' + CURRENT_EMBED;
    const player = document.getElementById('yt');
    if(player) player.src = CURRENT_EMBED;
    else {
      const div = document.querySelector('.player');
      div.innerHTML = "<iframe id='yt' src='"+CURRENT_EMBED+"' allow='accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; web-share' allowfullscreen referrerpolicy='strict-origin-when-cross-origin' style='border:0;width:100%;height:100%;'></iframe>";
    }
  }).catch(()=>{
    msg.style.display='block'; msg.textContent='Network hiccup. Try again.';
  });
}
// Never let page querystrings alter behavior
history.replaceState(null, '', window.location.pathname);
</script>
</body>
</html>
"""

@app.route("/")
def home():
    state = load_state()
    brand = state["brand"]
    # links
    items = []
    for k in sorted(state["rooms"].keys(), key=lambda x: int(x)):
        title = state["rooms"][k]["title"]
        items.append(f'<a class="room" href="/room/{k}">{title} <span class="small">/room/{k}</span></a>')
    html = render_template_string(
        HOME_TPL,
        brand=brand,
        room_links="".join(items),
    )
    return html

@app.route("/room/<room_id>")
def room(room_id):
    state = load_state()
    brand = state["brand"]
    title, vid, start, embed = room_meta(state, room_id)
    # Build OG with absolute URLs
    og = build_og_meta(room_id, title, vid, start)
    html = render_template_string(
        ROOM_TPL,
        brand=brand,
        title=title,
        start=start,
        embed=embed,
        og=og,
        room_id=room_id
    )
    return html

@app.post("/api/set_video")
def api_set_video():
    data = request.get_json(silent=True) or {}
    room_id = str(data.get("room_id", "")).strip()
    raw = str(data.get("raw", "")).strip()
    start = data.get("start", 0)
    try:
        start = int(start or 0)
        if start < 0:
            start = 0
    except (ValueError, TypeError):
        start = 0

    if not room_id:
        return jsonify(ok=False, error="Missing room_id")

    video_id, parsed_start = extract_youtube_id(raw)
    if not video_id:
        return jsonify(ok=False, error="Unrecognized link — paste a YouTube URL or 11-char ID.")

    final_start = start if start else parsed_start
    embed = build_embed(video_id, final_start)

    # Save ID + start only (hard-clean final)
    state = load_state()
    if "rooms" not in state:
        state["rooms"] = {}
    if room_id not in state["rooms"]:
        state["rooms"][room_id] = {"video_id":"", "start":0, "title": f"Room {room_id}"}
    state["rooms"][room_id]["video_id"] = video_id
    state["rooms"][room_id]["start"] = final_start
    save_state(state)

    return jsonify(ok=True, video_id=video_id, start=final_start, embed=embed)

# ------------------------- PORT-HOP + AUTO-OPEN -------------------------
def find_free_port(preferred=5050, max_tries=30):
    for p in range(preferred, preferred+max_tries):
        if p == 5000:
            continue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    raise RuntimeError("No free port found")

def open_browser(url):
    time.sleep(0.6)
    webbrowser.open(url)

if __name__ == "__main__":
    port = find_free_port()
    threading.Thread(target=open_browser, args=(f"http://127.0.0.1:{port}/",), daemon=True).start()
    app.run(host="127.0.0.1", port=port, debug=False)
