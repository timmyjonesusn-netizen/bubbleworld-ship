# sniffer.py — finds a safe local port (never 5000), fast.
import socket

DEFAULT_START = 5050
DEFAULT_END = 5099
FORBIDDEN = {5000}

def _port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False

def find_open_port(start: int = DEFAULT_START, end: int = DEFAULT_END) -> int:
    """Return first free port in [start, end] skipping any FORBIDDEN."""
    for p in range(start, end + 1):
        if p in FORBIDDEN:
            continue
        if _port_free(p):
            return p
    # last resort, expand a bit
    for p in range(end + 1, end + 21):
        if _port_free(p):
            return p
    raise RuntimeError("No open port found for local run.")
