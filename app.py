# app.py — Timmy Time Lab v1.0.4 (GitHub-ready)
# Laws: local-only 127.0.0.1, NEVER bind 5000, port-hop, auto-open "/".
# Big text, bubbles on all rooms, Matrix background, center-stage video + branding + joke.
# Rooms 2 & 3: Suno playlists (distinct). Rooms 4–9: "+ Add Link" for YouTube embeds.

import os, json, socket, threading, webbrowser, time, re, hashlib
from pathlib import Path
from flask import Flask, request, redirect, url_for, send_from_directory, jsonify
from flask import render_template_string

APP_NAME = "Timmy Time Lab v1.0.4"
ROOT = Path(__file__).parent.resolve()
STATIC_DIR = ROOT / "static"
DATA_DIR = STATIC_DIR / "data"
DATA_FILE = DATA_DIR / "state.json"

# ------------------------------ UTIL ------------------------------
def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps(DEFAULT_STATE, indent=2))

def load_state():
    ensure_dirs()
    try:
        return json.loads(DATA_FILE.read_text() or "{}")
    except Exception:
        return DEFAULT_STATE.copy()

def save_state(state):
    DATA_FILE.write_text(json.dumps(state, indent=2))

def ytd_to_embed(url: str) -> str:
    """
    Normalize YouTube watch/shorts/youtu.be to embed URL.
    """
    url = url.strip()
    m = re.search(r"(?:v=|/shorts/|youtu\.be/)([A-Za-z0-9_-]{6,})", url)
    if m:
        vid = m.group(1)
        return f"https://www.youtube.com/embed/{vid}"
    return url  # leave untouched if not recognized

def pick_port():
    preferred = list(range(5050, 5070))
    # NEVER 5000 (reserved for Suno)
    for p in preferred:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    # last resort (shouldn't happen)
    return 0

# ------------------------------ ROOMS ------------------------------
ROOMS = {
    1: {"name": "Engine Room", "subtitle": "Pink Halo Reactor", "theme":"engine",
        "tagline": "Elevator online — matrix clears for the hammer.",
        "marketing": "TimmyTime • Bubble Ship • LIVE"},
    2: {"name": "Purple Play", "subtitle": "Suno Room A", "theme":"purple",
        "marketing": "Music with Timmy — Free for creators"},
    3: {"name": "Warm Core", "subtitle": "Suno Room B", "theme":"warm",
        "marketing": "Chill/Funk/Jazz — Creator-safe"},
    4: {"name": "Drift Space", "subtitle": "Reels Lab A", "theme":"aqua",
        "marketing": "TimmyBubbles • Daily punchline"},
    5: {"name": "Golden Deck", "subtitle": "Reels Lab B", "theme":"gold",
        "marketing": "TerrificTimmy • Short & sweet"},
    6: {"name": "Crimson Rail", "subtitle": "Reels Lab C", "theme":"crimson",
        "marketing": "TornadoTimmy • First-punch only"},
    7: {"name": "Neon Blue", "subtitle": "Reels Lab D", "theme":"blue",
        "marketing": "TimmyFantastic • One take"},
    8: {"name": "Magenta Stage", "subtitle": "Reels Lab E", "theme":"magenta",
        "marketing": "Center-stage marketing shell"},
    9: {"name": "Emerald Bay", "subtitle": "Reels Lab F", "theme":"emerald",
        "marketing": "Daily fun • Post fast"},
}

# ------------------------------ DEFAULT STATE ------------------------------
DEFAULT_STATE = {
  "rooms": {
    "2": {
      "suno": [
        "https://suno.com/playlist/bb594ef1-d260-46b7-af7f-e3a3286d39b1",
        "https://suno.com/playlist/2ec04889-1c23-4e2d-9c27-8a2b6475da4b",
        "https://suno.com/playlist/e95ddd12-7e37-43e2-b3e0-fe342085a19f",
        "https://suno.com/playlist/c387adf4-abdb-4f74-9075-c4cb460c8840",
        "https://suno.com/playlist/34190a09-abb2-470d-85a5-a1201f5e827c"
      ],
      "youtube": []
    },
    "3": {
      "suno": [
        "https://suno.com/playlist/b11f5b9a-b2d1-46f2-a307-e62491ae2479",
        "https://suno.com/playlist/d04a7c63-52b7-4695-b47f-64f3a3dae677",
        "https://suno.com/playlist/06b80fa9-8c72-4e0a-b277-88d00c441316",
        "https://suno.com/playlist/3a82341f-95df-4b1b-91a2-4d5e6531ae08",
        "https://suno.com/playlist/d3ed7e46-ea14-477f-a9cf-051bdfc0c9c3"
      ],
      "youtube": []
    },
    "4": {"youtube": []},
    "5": {"youtube": []},
    "6": {"youtube": []},
    "7": {"youtube": []},
    "8": {"youtube": []},
    "9": {"youtube": []}
  },
  "weather": {"zip": "", "cache": {"high": "", "low": "", "cond": "", "ts": 0}}
}

# ------------------------------ APP ------------------------------
app = Flask(__name__, static_folder=str(STATIC_DIR))

@app.route("/")
def home():
    return redirect(url_for("room", n=1))

@app.route("/room/<int:n>")
def room(n):
    if n not in ROOMS:
        return redirect(url_for("room", n=1))
    state = load_state()
    r = ROOMS[n]
    # videos list is from state, newest first
    vids = list(reversed(state["rooms"].get(str(n), {}).get("youtube", [])))
    suno = state["rooms"].get(str(n), {}).get("suno", [])
    joke = daily_punchline(n)
    stealth = stealth_hash()
    return render_template_string(TPL_ROOM,
        app_name=APP_NAME, n=n, room=r, vids=vids, suno=suno, joke=joke, stealth=stealth)

@app.route("/api/add_link", methods=["POST"])
def add_link():
    try:
        room = int(request.form.get("room", "0"))
        url = request.form.get("url","").strip()
        if room not in ROOMS or not url:
            return jsonify({"ok": False, "err": "bad input"}), 400
        embed = ytd_to_embed(url)
        state = load_state()
        state["rooms"].setdefault(str(room), {}).setdefault("youtube", []).append(embed)
        save_state(state)
        return jsonify({"ok": True, "embed": embed})
    except Exception as e:
        return jsonify({"ok": False, "err": str(e)}), 500

def daily_punchline(n: int) -> str:
    lines = {
        4: "Marketing rule #1: hook in 3 seconds.",
        5: "If it makes you smile, post it.",
        6: "One take. No brakes. Boom.",
        7: "Short, shiny, shareable.",
        8: "Center stage: you + the moment.",
        9: "Ship daily. Fix live.",
    }
    return lines.get(n, "Bubble ship online · All systems go.")

def stealth_hash() -> str:
    seed = f"{APP_NAME}|{time.strftime('%Y-%m-%d')}"
    return hashlib.sha256(seed.encode()).hexdigest()[:8]

# ------------------------------ TEMPLATE ------------------------------
TPL_ROOM = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{{app_name}} · {{room.name}}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{{url_for('static', filename='style.css')}}">
<script defer src="{{url_for('static', filename='bubbles.js')}}"></script>
<style>
:root { --theme: {{room.theme}}; }
</style>
</head>
<body class="theme-{{room.theme}}">
<canvas id="bubble-canvas"></canvas>
<div class="matrix"></div>

<header class="top">
  <div class="brand">TIMMY TIME</div>
  <div class="room-title">{{room.name}} <span class="sub">· {{room.subtitle}}</span></div>
</header>

<main>
  {% if n == 1 %}
    <div class="hammer-wrap">
      <div class="hammer">🪓</div>
      <div class="lightning"></div>
    </div>
  {% endif %}

  <section class="stage">
    <div class="marketing">{{room.marketing}}</div>

    <div class="video-box">
      {% if vids %}
        <iframe class="yt" src="{{vids[0]}}" title="YouTube video" frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
      {% else %}
        <div class="placeholder">Paste a YouTube link below and tap Add →</div>
      {% endif %}
    </div>

    {% if suno %}
      <div class="suno-wrap">
        <div class="suno-title">Suno Playlists</div>
        <ul>
          {% for s in suno %}
          <li><a href="{{s}}" target="_blank">{{s}}</a></li>
          {% endfor %}
        </ul>
      </div>
    {% endif %}

    {% if n >= 4 %}
    <form class="add-link" method="post" onsubmit="return addLink(event)">
      <input type="hidden" name="room" value="{{n}}">
      <input name="url" type="url" required placeholder="https://youtube.com/watch?v=..." autocomplete="on">
      <button>Add</button>
      <span class="stealth">#{{stealth}}</span>
    </form>
    {% endif %}

    <div class="joke">{{joke}}</div>
  </section>

  <nav class="arrows">
    <a class="prev" href="{{ url_for('room', n=(n-1 if n>1 else 9)) }}">←</a>
    <a class="next" href="{{ url_for('room', n=(n+1 if n<9 else 1)) }}">→</a>
  </nav>
</main>

<script>
async function addLink(e){
  e.preventDefault();
  const fd = new FormData(e.target);
  const res = await fetch("{{ url_for('add_link') }}", {method:"POST", body:fd});
  const j = await res.json();
  if(j.ok){
    location.reload();
  }else{
    alert("Add failed: " + (j.err||""));
  }
  return false;
}
</script>
</body>
</html>
"""

# ------------------------------ RUNNER ------------------------------
def open_browser(port):
    time.sleep(0.6)
    webbrowser.open(f"http://127.0.0.1:{port}/")

def run():
    ensure_dirs()
    port = pick_port()
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    app.run(host="127.0.0.1", port=port, debug=False)

if __name__ == "__main__":
    run()
