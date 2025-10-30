# jumper.py — binds Flask to a safe port and opens Safari with adaptive delay.
import threading, time, webbrowser, socket

def port_hop(app, port: int):
    """Run Flask on 127.0.0.1:port in a daemon thread."""
    def _run():
        # werkzeug reloader off to avoid double-threads on iPhone
        app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t

def _tcp_ready(host: str, port: int, timeout_s: float = 0.25) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout_s)
        try:
            s.connect((host, port))
            return True
        except OSError:
            return False

def open_when_ready(url: str, host: str, port: int):
    """
    Open the browser once the socket accepts. Adaptive delay:
    - Try fast for ~1.5s, then ease into small backoff up to ~2s sleeps.
    """
    def _watch():
        # Phase 1: quick spins (~1.5s total)
        for _ in range(15):
            if _tcp_ready(host, port, 0.2):
                webbrowser.open(url)
                return
            time.sleep(0.1)

        # Phase 2: gentle backoff (0.25 → 2.0s, cap 20 tries)
        delay = 0.25
        for _ in range(20):
            if _tcp_ready(host, port, min(0.3, delay)):
                webbrowser.open(url)
                return
            time.sleep(delay)
            delay = min(delay * 1.6, 2.0)

        # Last ping—if still not up, just open anyway (Flask may finish a moment later)
        webbrowser.open(url)
    threading.Thread(target=_watch, daemon=True).start()
