# app.py — Timmy Time Lab v1.0.4 (Local)
# Laws: local-only 127.0.0.1, NEVER bind 5000, port-hop, auto-open "/",
#       big text, matrix background, neon bubbles. Sniffer/Jumper/Healer with adaptive delays.

import os, hashlib, datetime
from flask import Flask, Response, render_template_string

from sniffer import find_open_port
from jumper import port_hop, open_when_ready
from healer import Healer

APP_NAME = "Timmy Time Lab v1.0.4"
BOOT_TS = datetime.datetime.utcnow().isoformat()
STEALTH = hashlib.sha256((APP_NAME + BOOT_TS).encode()).hexdigest()[:10]  # not used for routing here, reserved

app = Flask(__name__)

# -------------------- ROUTES --------------------
@app.route("/")
def home():
    return render_template_string(TEMPLATE, app_name=APP_NAME, version="v1.0.4")

@app.route("/health")
def health():
    return Response("ok", 200)

# -------------------- MAIN --------------------
if __name__ == "__main__":
    port = find_open_port()  # skips 5000 by design
    url = f"http://127.0.0.1:{port}/"

    # Start Flask (daemon thread) and open browser when socket is ready.
    port_hop(app, port)
    open_when_ready(url, "127.0.0.1", port)

    # Start the gentle healer ping loop (no killing, just adaptive pacing).
    Healer(url).start()

    # Keep the main thread parked so Pythonista doesn’t exit.
    try:
        import time
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass

# -------------------- INLINE TEMPLATE (matrix + bubbles + center stage) --------------------
TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Timmy Time · Magenta Stage · {{version}}</title>
<meta name="description" content="Timmy Time · Magenta Stage · Matrix · Neon bubbles · Center-stage marketing shell">
<style>
*{box-sizing:border-box}html,body{margin:0;padding:0;height:100%;background:#000;color:#fff;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial}
:root{--grid:rgba(0,255,120,.26);--title:#fff4ff;--bubble-rgb:255,244,255;--title-shadow:0 0 22px rgba(255,64,255,.6),0 0 44px rgba(255,64,255,.35)}
.grid{position:fixed;inset:0;pointer-events:none;background:
  radial-gradient(120vmin 120vmin at 10% 10%, rgba(255,255,255,.06), transparent 60%),
  radial-gradient(100vmin 100vmin at 88% 20%, rgba(255,255,255,.06), transparent 60%),
  radial-gradient(120vmin 120vmin at 28% 78%, rgba(255,255,255,.06), transparent 60%),
  linear-gradient(0deg,#05000c,#000 50%,#020005)}
.grid::before{content:"";position:absolute;inset:0;background-image:
  linear-gradient(transparent 31px,var(--grid) 32px,transparent 33px),
  linear-gradient(90deg,transparent 31px,var(--grid) 32px,transparent 33px);
  background-size:32px 32px;opacity:.9}
.bubbles{position:fixed;inset:0;overflow:hidden;pointer-events:none}
.bubble{position:absolute;width:12vmin;height:12vmin;border-radius:50%;
  background:radial-gradient(circle at 30% 30%,rgba(var(--bubble-rgb),.22),rgba(var(--bubble-rgb),.06) 60%,rgba(var(--bubble-rgb),0) 70%);
  filter:blur(.2vmin) drop-shadow(0 0 .75vmin rgba(255,255,255,.25));
  animation:rise linear infinite;opacity:.8;border:.5vmin solid rgba(255,182,255,.20)}
@keyframes rise{from{transform:translateY(110vh) translateX(var(--dx)) scale(var(--s))}to{transform:translateY(-15vh) translateX(calc(var(--dx) + var(--drift))) scale(var(--s))}}
.wrap{position:relative;min-height:100%;display:flex;flex-direction:column;gap:2rem;padding:10vh 6vw 22vh}
.brand{display:flex;align-items:center;gap:1rem}
.logo{font-weight:800;letter-spacing:.4rem;line-height:.9;text-shadow:var(--title-shadow)}
.logo .row{display:block;font-size:2rem}.logo .row:first-child{color:#ff7cff}.logo .row:last-child{color:#ffb3ff}
.ver{margin-left:auto;padding:.45rem .75rem;border:1px solid rgba(255,255,255,.25);border-radius:1rem;font-size:.95rem;color:#ffc8ff;background:rgba(0,0,0,.35);backdrop-filter:blur(6px)}
h1{font-size:clamp(2.4rem,6vw,4.4rem);margin:0;color:var(--title);text-shadow:var(--title-shadow)}
.subtitle{font-size:clamp(1.2rem,2.8vw,1.6rem);color:#e9d5ff;opacity:.95}
.bullets{font-size:clamp(1.1rem,2.6vw,1.5rem);color:#fff;opacity:.92}
.stage{margin-top:1rem;display:grid;gap:1rem}
.video-shell{position:relative;width:100%;max-width:1100px;margin-inline:auto;aspect-ratio:16/9;border-radius:1rem;border:2px solid rgba(255,128,255,.35);box-shadow:0 0 40px rgba(255,64,255,.25), inset 0 0 24px rgba(255,64,255,.18);overflow:hidden;background:#070109}
.video-shell iframe{width:100%;height:100%;border:0;display:block}
.joke{max-width:1100px;margin:.5rem auto 0;font-size:clamp(1.15rem,2.6vw,1.6rem);color:#ffd6ff;text-shadow:0 0 8px rgba(255,64,255,.35)}
.addlink{max-width:1100px;margin:.5rem auto 0;display:flex;gap:.5rem;align-items:center}
.addlink input{flex:1;padding:.8rem 1rem;font-size:1rem;border-radius:.8rem;border:1px solid rgba(255,255,255,.25);background:rgba(15,0,22,.65);color:#fff;outline:none}
.addlink button{padding:.85rem 1rem;font-weight:700;border-radius:.8rem;border:1px solid rgba(255,255,255,.25);background:linear-gradient(90deg,#ff40ff,#ffa0ff);color:#1a001f;cursor:pointer}
.nav-arrows{position:fixed;inset:auto 0 25vh 0;display:flex;justify-content:space-between;padding:0 4vw;pointer-events:none}
.arrow{pointer-events:auto;width:84px;height:84px;border-radius:20px;display:grid;place-items:center;border:1px solid rgba(255,255,255,.25);background:rgba(0,0,0,.35);backdrop-filter:blur(6px)}
.arrow svg{width:44px;height:44px;fill:#fff;opacity:.95}
.footer{max-width:1100px;margin:2rem auto 0;color:#ffeaff;opacity:.9;font-size:clamp(1rem,2.2vw,1.15rem)}
</style>
</head><body>
<div class="grid"></div><div class="bubbles" id="bubbles"></div>
<div class="wrap">
  <div class="brand">
    <div class="logo"><span class="row">TIMMY</span><span class="row">TIME</span></div>
    <div class="ver">Local · {{version}}</div>
  </div>
  <div>
    <h1>Magenta Stage <span class="subtitle">· Reels Lab E</span></h1>
    <div class="bullets">Center-stage marketing shell • Matrix background • Neon bubbles</div>
  </div>
  <section class="stage" aria-label="Video Stage">
    <div class="video-shell">
      <iframe id="ytFrame" src="https://www.youtube.com/embed/dQw4w9WgXcQ"
        title="YouTube video player"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
        allowfullscreen></iframe>
    </div>
    <div class="joke" id="jokeLine">“Creators welcome. Copyright-free vibes, neon-powered.”</div>
    <div class="addlink">
      <input id="ytInput" type="url" inputmode="url" placeholder="Paste YouTube link (watch / shorts / youtu.be) and tap +"
        autocomplete="off" spellcheck="false">
      <button id="addBtn" title="Embed">+</button>
    </div>
  </section>
  <div class="footer">Local run uses Sniffer/Jumper/Healer with adaptive delay. Suno’s port 5000 remains untouched.</div>
</div>
<div class="nav-arrows" aria-hidden="true">
  <a class="arrow" href="#prev" title="Prev">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15.41 7.41 14 6l-6 6 6 6 1.41-1.41L10.83 12z"/></svg>
  </a>
  <a class="arrow" href="#next" title="Next">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8.59 16.59 13.17 12 8.59 7.41 10 6l6 6z"/></svg>
  </a>
</div>
<script>
(function makeBubbles(){
  const root = document.getElementById('bubbles');
  const count = 22;
  for (let i=0;i<count;i++){
    const b = document.createElement('div');
    b.className = 'bubble';
    const size = 8 + Math.random()*18;
    const startX = Math.random()*100;
    const drift = (Math.random()*20-10) + 'vw';
    const delay = (-Math.random()*18)+'s';
    const dur = (18 + Math.random()*26) + 's';
    b.style.width = size+'vmin'; b.style.height = size+'vmin';
    b.style.left = startX+'vw';
    b.style.setProperty('--dx', (Math.random()*12-6) + 'vw');
    b.style.setProperty('--drift', drift);
    b.style.setProperty('--s', (0.7 + Math.random()*0.6).toFixed(2));
    b.style.animationDuration = dur; b.style.animationDelay = delay;
    root.appendChild(b);
  }
})();
function toEmbed(url){
  if(!url) return null;
  try{
    url = url.trim();
    let m;
    if (m = url.match(/^https?:\/\/youtu\.be\/([a-zA-Z0-9_-]{6,})/)) return 'https://www.youtube.com/embed/'+m[1];
    if (m = url.match(/[?&]v=([a-zA-Z0-9_-]{6,})/)) return 'https://www.youtube.com/embed/'+m[1];
    if (m = url.match(/youtube\.com\/shorts\/([a-zA-Z0-9_-]{6,})/)) return 'https://www.youtube.com/embed/'+m[1];
    return null;
  }catch(e){ return null; }
}
document.getElementById('addBtn').addEventListener('click', ()=>{
  const val = document.getElementById('ytInput').value;
  const embed = toEmbed(val);
  if(embed){
    document.getElementById('ytFrame').src = embed;
    document.getElementById('jokeLine').textContent = 'Loaded. Lights up—roll camera.';
    document.getElementById('ytInput').value = '';
  } else {
    document.getElementById('jokeLine').textContent = 'Hmm… that link doesn’t look like YouTube.';
  }
});
document.getElementById('ytInput').addEventListener('keydown', (e)=>{ if(e.key==='Enter') document.getElementById('addBtn').click(); });
</script>
</body></html>
"""
