# ============================================================
# Bubble World Ship Core v3.3.3 — "Studio Sync Mode"
# ============================================================
# Laws:
# - 0.0.0.0 host so iPhone + tablet share one live build.
# - Auto BUILD_ID version tag → cache-busting built in.
# - Flask serves / and /telemetry directly from ship.html.
# - Port 5000 preserved (music safe).
# - Auto-open browser (optional).
# ============================================================

from flask import Flask, send_file, jsonify, make_response
import socket, random, string, threading, webbrowser, datetime, os

app = Flask(__name__)

# ------------------------------------------------------------
# 1. Generate BUILD_ID (used for cache bust + display)
# ------------------------------------------------------------
now = datetime.datetime.now()
BUILD_ID = now.strftime("BUBBLE-%Y%m%d-%H%M%S-") + ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))
print(f"🫧 Bubble Ship Build: {BUILD_ID}")

# ------------------------------------------------------------
# 2. Serve the canonical ship.html with cache headers disabled
# ------------------------------------------------------------
@app.route("/")
def serve_ship():
    try:
        response = make_response(send_file("ship.html"))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-Bubble-Build"] = BUILD_ID
        return response
    except Exception as e:
        return f"<h1>Ship missing!</h1><p>{e}</p>"

# ------------------------------------------------------------
# 3. Telemetry route (for Maya panel)
# ------------------------------------------------------------
@app.route("/telemetry")
def telemetry():
    return jsonify({
        "sniffer": "all clear on local ports",
        "hopper": "port hop stable / cloak engaged",
        "healer": "shield green / bubble field intact",
        "maya": "awake and watching you 💖",
        "build": BUILD_ID
    })

# ------------------------------------------------------------
# 4. Helper: find local IP to display correct URL
# ------------------------------------------------------------
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# ------------------------------------------------------------
# 5. Optional auto-open browser
# ------------------------------------------------------------
def open_browser():
    webbrowser.open(f"http://{get_local_ip()}:5000/?v={BUILD_ID}")

# ------------------------------------------------------------
# 6. Run the ship
# ------------------------------------------------------------
if __name__ == "__main__":
    print(f"🛠  Serving Bubble Ship Build {BUILD_ID}")
    print(f"🌐  Access locally at:  http://{get_local_ip()}:5000/?v={BUILD_ID}")
    threading.Timer(2.0, open_browser).start()
    app.run(host="0.0.0.0", port=5000, debug=False)
