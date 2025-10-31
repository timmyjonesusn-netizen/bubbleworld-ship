# app.py — Timmy Ship: Hard-Clean YouTube Link Sanitizer (v1.0)
# Laws upheld:
# - Local-only (127.0.0.1)
# - NEVER bind 5000; port-hop to a free one starting at 5050
# - Auto-open "/"
# - Big readable text
# - Store ONLY 11-char YouTube ID (+ optional start seconds)
# - Always render youtube-nocookie.com/embed/<ID>[?start=SS]
# - Ignore all external query params (fbclid, utm_*, list, index, si, feature, etc.)

import os, re, json, socket, threading, time, webbrowser
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string, abort

APP_NAME = "Timmy Ship — Sanitizer Add-On v1.0"
ROOT = Path(__file__).parent.resolve()
STATIC_DIR = ROOT / "static"
DATA_DIR = STATIC_DIR / "data"
DATA_FILE = DATA_DIR / "state.json"

# ------------------------- DEFAULT STATE -------------------------
DEFAULT_STATE = {
    "rooms": {
        # Example default: room 8 empty
        "8": {"video_id": "", "start": 0, "title": "Room 8 — Reel Core"},
        "2": {"video_id": "", "start": 0, "title": "Room 2 — Purple Play"},
        "3": {"video_id": "", "start": 0, "title": "Room 3 — Suno Set"},
        "1": {"video_id": "", "start": 0, "title": "Engine Room — Hammer Online"},
    },
    "brand": {
        "site_title": "TimmyTime Bubble World Ship",
        "og_image": "/static/og/ship_default_1200x630.png",
        "theme_color": "#ff3bd1",
        "bg": "#05000c",
        "fg": "#ffffff"
    }
}

# Ensure folders/files
STATIC_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
( STATIC_DIR / "og" ).mkdir(parents=True, exist_ok=True)
if not DATA_FILE.exists():
    DATA_FILE.write_text(json.dumps(DEFAULT_STATE, indent=2), encoding="utf-8")
# Tiny placeholder OG image if you don’t have one yet
og_placeholder = STATIC_DIR / "og" / "ship_default_1200x630.png"
if not og_placeholder.exists():
    # 1200x630 blank PNG placeholder
    from PIL import Image
    img = Image.new("RGB", (1200, 630), (5, 0, 12))
    img.save(str(og_placeholder), format="PNG")

# ------------------------- APP -------------------------
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
      - Optional t= / start= seconds (we'll parse separately)
    Returns (video_id, start_seconds)
    """
    if not raw:
        return None, 0

    # Normalize
    s = raw.strip()

    # Pull out explicit start time if present
    start = 0
    # support t=42, t=1m23s, start=42
    t_match = re.search(r"(?:[?&]|^)t=([0-9]+)s?\b", s) or re.search(r"(?:[?&]|^)start=([0-9]+)\b", s)
    if t_match:
        try:
            start = int(t_match.group(1))
        except ValueError:
            start = 0

    # Raw 11-char ID case
    if YOUTUBE_ID_RE.match(s):
        return s, start

    # Shorts
    m = re.search(r"youtube\.com/shorts/([A-Za-z0-9_-]{11})", s)
    if m:
        return m.group(1), start

    # watch?v=
    m = re.search(r"[?&]v=([A-Za-z0-9_-]{11})\b", s)
    if m:
        return m.group(1), start

    # youtu.be/ID
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})\b", s)
    if m:
        return m.group(1), start

    return None, 0

def build_embed(video_id: str, start: int = 0):
    base = f"https://www.youtube-nocookie.com/embed/{video_id}"
    return f"{base}?start={start}" if start and start > 0 else base

def room_meta(state, room_id: str):
    r = state["rooms"].get(room_id, {"video_id": "", "start": 0, "title": f"Room {room_id}"})
    vid = r.get("video_id") or ""
    start = int(r.get("start") or 0)
    embed = build_embed(vid, start) if vid else ""
    title = r.get("title") or f"Room {room_id}"
    return title, vid, start, embed

# ------------------------- ROUTES -------------------------
@app.route("/")
def home():
    state = load_state()
    rooms = state["rooms"]
    brand = state["brand"]
    html = f"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{brand['site_title']} — Dock</title>
<meta name="theme-color" content="{brand['theme_color']}">
<style>
  :root {{
    --bg: {brand['bg']};
    --fg: {brand['fg']};
    --accent: {brand['theme_color']};
  }}
  html, body {{ margin:0; padding:0; background:var(--bg); color:var(--fg); font-family: -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif; }}
  h1 {{ font-size: 3rem; margin: 1rem; }}
  a.room {{ display:block; margin: 1rem; padding: 1rem 1.2rem; background:#0f0f18; border:1px solid #222; border-radius: 12px; color:#fff; text-decoration:none; font-size: 1.4rem; }}
  .small {{ opacity: .8; font-size: .95rem; }}
</style>
</head>
<body>
  <h1>TimmyTime Dock</h1>
  <div class="small" style="margin:0 1rem 1rem 1rem;">Sanitizer Add-On v1.0 — Paste any YouTube link in a room, it becomes <b>hard-clean</b> and final.</div>
  {"".join([f'<a class="room" href="/room/{k}">{rooms[k]["title"]} <span class="small">/room/{k}</span></a>' for k in sorted(rooms.keys(), key=lambda x:int(x))])}
</body>
</html>
"""
    return html

@app.route("/room/<room_id>")
def room(room_id):
    state = load_state()
    brand = state["brand"]
    title, vid, start, embed = room_meta(state, room_id)

    # Open Graph (FB) wants stable og:url and the video thumbnail/image.
    # We point og:video:url at the clean embed; clicking the post goes to this room URL.
    room_url = f"http://127.0.0.1/room/{room_id}"  # for local preview; tunnel will rewrite host
    og_image = brand["og_image"]
    yt_thumb = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else og_image
    og_video = embed or ""

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<meta name="theme-color" content="{brand['theme_color']}" />

<!-- FB/Twitter share locks -->
<link rel="canonical" href="{room_url}" />
<meta property="og:url" content="{room_url}" />
<meta property="og:title" content="{title}" />
<meta property="og:description" content="TimmyTime Bubble World Ship — Hammer online." />
<meta property="og:image" content="{yt_thumb}" />
{"<meta property='og:video:url' content='" + og_video + "' />" if og_video else ""}

<style>
  :root {{
    --bg: {brand['bg']};
    --fg: {brand['fg']};
    --accent: {brand['theme_color']};
  }}
  html, body {{ margin:0; padding:0; background:var(--bg); color:var(--fg); font-family: -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif; }}
  h1 {{ font-size: 3rem; margin: 1rem; }}
  .wrap {{ padding: 1rem; }}
  .input {{ display:flex; gap:.6rem; flex-wrap:wrap; margin: .5rem 0 1rem 0; }}
  input[type=text] {{ flex:1; min-width:240px; font-size:1.2rem; padding:.8rem; border-radius:10px; border:1px solid #333; background:#0f0f18; color:#fff; }}
  input[type=number] {{ width:110px; font-size:1.2rem; padding:.8rem; border-radius:10px; border:1px solid #333; background:#0f0f18; color:#fff; }}
  button {{ font-size:1.2rem; padding:.8rem 1.1rem; border-radius:10px; border:1px solid #444; background:var(--accent); color:#000; cursor:pointer; }}
  .hint {{ font-size: .95rem; opacity:.85; margin-top:.3rem; }}
  .err {{ color:#ff6b6b; margin-top:.4rem; }}
  .ok {{ color:#7ef0a8; margin-top:.4rem; }}
  .player {{ aspect-ratio:16/9; width: min(960px, 96vw); max-width: 100%; border-radius: 14px; border:1px solid #222; overflow:hidden; background:#000; }}
  .now {{ margin-top:.6rem; font-size: .95rem; opacity:.85; }}
  .row {{ display:flex; align-items:center; gap:.6rem; flex-wrap:wrap; }}
  a, .linklike {{ color:#ffb6ff; text-decoration:underline; cursor:pointer; }}
</style>
</head>
<body>
  <div class="wrap">
    <h1>{title}</h1>

    <div class="input">
      <input id="paste" type="text" placeholder="Paste YouTube link or 11-char ID" autocomplete="off" />
      <input id="start" type="number" min="0" step="1" value="{start}" title="Start seconds (optional)" />
      <button onclick="lockVideo()">Lock Clean Link</button>
    </div>
    <div class="hint">Accepts youtu.be/ID, watch?v=ID, /shorts/ID, or raw 11-char ID. We store only the ID (optionally start seconds). Everything else is ignored.</div>
    <div id="msg" class="err" style="display:none;"></div>
    <div id="ok" class="ok" style="display:none;"></div>

    <div style="margin:1rem 0;">
      <div class="player">
        {"<iframe id='yt' src='"+embed+"' allow='accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; web-share' allowfullscreen referrerpolicy='strict-origin-when-cross-origin' style='border:0;width:100%;height:100%;'></iframe>" if embed else "<div style='display:flex;align-items:center;justify-content:center;height:100%;color:#888;'>No video locked yet.</div>"}
      </div>
      <div class="now" id="now">
        {"Now playing → " + embed.replace("&", "&amp;") if embed else "Paste a link and press “Lock Clean Link”. We’ll show the final embed here."}
      </div>
      <div class="row" style="margin-top:.4rem;">
        <span class="linklike" onclick="copyClean()">Copy Clean Link</span>
        <span class="hint">•</span>
        <a target="_blank" href="https://developers.facebook.com/tools/debug/">Open Facebook Sharing Debugger</a>
      </div>
    </div>

    <div class="hint">This page ignores any querystrings (fbclid, utm, list, si, feature, etc.). Only your locked ID controls playback.</div>
    <div class="hint" style="margin-top:.4rem;"><a href="/">← Back to Dock</a></div>
  </div>

<script>
let CURRENT_EMBED = {json.dumps(embed)};
function copyClean(){{
  if(!CURRENT_EMBED) return;
  navigator.clipboard.writeText(CURRENT_EMBED).then(()=>{{
    const ok = document.getElementById('ok'); ok.style.display='block'; ok.textContent='Copied clean link.';
    setTimeout(()=>{{ ok.style.display='none'; }}, 1200);
  }});
}}
function lockVideo(){{
  const raw = document.getElementById('paste').value.trim();
  const start = parseInt(document.getElementById('start').value || '0', 10);
  const msg = document.getElementById('msg'); msg.style.display='none'; msg.textContent='';
  fetch('/api/set_video', {{
    method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body: JSON.stringify({{room_id:'{room_id}', raw, start:isNaN(start)?0:start}})
  }}).then(r=>r.json()).then(d=>{{
    if(!d.ok){{
      msg.style.display='block'; msg.textContent=d.error || 'Unrecognized link — paste a YouTube URL or 11-char ID.';
      return;
    }}
    CURRENT_EMBED = d.embed;
    const now = document.getElementById('now'); now.innerHTML = 'Now playing → ' + CURRENT_EMBED.replaceAll('&','&amp;');
    const player = document.getElementById('yt');
    if(player) player.src = CURRENT_EMBED;
    else {{
      // inject iframe if it wasn’t present
      const div = document.querySelector('.player');
      div.innerHTML = "<iframe id='yt' src='"+CURRENT_EMBED+"' allow='accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; web-share' allowfullscreen referrerpolicy='strict-origin-when-cross-origin' style='border:0;width:100%;height:100%;'></iframe>";
    }}
  }}).catch(()=>{{
    msg.style.display='block'; msg.textContent='Network hiccup. Try again.';
  }});
}}
// Never let page querystrings alter behavior
history.replaceState(null, '', window.location.pathname);
</script>
</body>
</html>
"""
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

    # If user provided start, prefer that; else use parsed
    final_start = start if start else parsed_start
    embed = build_embed(video_id, final_start)

    # Save: ID only + start seconds
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
    # Local-only, debug off for pub-tunnel safety
    app.run(host="127.0.0.1", port=port, debug=False)
