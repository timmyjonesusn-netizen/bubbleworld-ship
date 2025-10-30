# healer.py — gentle health monitor with adaptive backoff (no killing port 5000).
import threading, time
try:
    import requests
except Exception:
    requests = None  # We'll degrade gracefully without it.

class Healer:
    """
    Pings /health and, if it looks stuck, re-pokes the browser using a
    growing delay. We DON'T kill processes or touch 5000—Suno is sacred.
    """
    def __init__(self, base_url: str, ping_path: str = "/health"):
        self.url = base_url.rstrip("/") + ping_path
        self._stop = threading.Event()

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        if requests is None:
            # No requests module; do a simple sleep loop so we don't spin.
            for _ in range(120):
                if self._stop.is_set():
                    return
                time.sleep(1.0)
            return

        # Adaptive cadence: quick when healthy, slower when flaky.
        ok_streak = 0
        delay = 2.0     # start calm
        max_delay = 20  # cap so it never feels dead

        while not self._stop.is_set():
            try:
                r = requests.get(self.url, timeout=1.5)
                healthy = (r.status_code == 200)
            except Exception:
                healthy = False

            if healthy:
                ok_streak += 1
                # reward health: shorten checks a bit
                delay = max(1.0, delay * 0.7)
            else:
                ok_streak = 0
                # back off so we don't thrash an app starting up
                delay = min(max_delay, delay * 1.6)

            time.sleep(delay)
