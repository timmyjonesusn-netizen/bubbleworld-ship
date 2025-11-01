import os, json, glob, time, shutil, subprocess
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

GRAPH = "https://graph.facebook.com/v19.0"

def http_post(url, data):
    data_bytes = urlencode(data).encode("utf-8")
    req = Request(url, data=data_bytes)
    try:
        with urlopen(req, timeout=60) as r:
            return r.read().decode("utf-8")
    except HTTPError as e:
        raise RuntimeError(f"HTTPError {e.code}: {e.read().decode('utf-8', errors='ignore')}")
    except URLError as e:
        raise RuntimeError(f"URLError: {e.reason}")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def pick_next_payload(queue_dir):
    files = sorted(glob.glob(os.path.join(queue_dir, "*.json")))
    return files[0] if files else None

def post_to_page(dest, payload):
    page_id = dest["page_id"]
    token_env = dest["token_env"]
    token = os.environ.get(token_env, "").strip()
    if not token:
        raise RuntimeError(f"Missing token env: {token_env}")

    msg = payload.get("message", "").strip()
    link = payload.get("link", "").strip()
    image_url = payload.get("image_url", "").strip()
    video_url = payload.get("video_url", "").strip()

    # Priority: video > image > link/text
    if video_url:
        url = f"{GRAPH}/{page_id}/videos"
        data = {"file_url": video_url, "description": msg, "access_token": token}
        return http_post(url, data)

    if image_url:
        url = f"{GRAPH}/{page_id}/photos"
        data = {"url": image_url, "caption": msg, "access_token": token}
        return http_post(url, data)

    # Link or text
    url = f"{GRAPH}/{page_id}/feed"
    data = {"message": msg, "access_token": token}
    if link:
        data["link"] = link
    return http_post(url, data)

def git_move_and_commit(src_path, sent_dir, sha_note):
    os.makedirs(sent_dir, exist_ok=True)
    base = os.path.basename(src_path)
    dst_path = os.path.join(sent_dir, base)
    shutil.move(src_path, dst_path)
    # Commit the move so your ledger updates
    subprocess.run(["git", "config", "user.name", "bubbleworld-bot"], check=True)
    subprocess.run(["git", "config", "user.email", "actions@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", "-A"], check=True)
    msg = f"autoposter: sent {base} ({sha_note})"
    subprocess.run(["git", "commit", "-m", msg], check=True)
    # Push uses GITHUB_TOKEN via permissions in the workflow
    subprocess.run(["git", "push"], check=True)

def main():
    root = os.getcwd()
    meta = load_json(".github/autoposter/destinations.json")
    destinations = [d for d in meta.get("destinations", []) if d.get("active", True)]
    if not destinations:
        print("No active destinations.")
        return

    queue_dir = ".github/autoposter/queue"
    sent_dir  = ".github/autoposter/sent"
    next_file = pick_next_payload(queue_dir)
    if not next_file:
        print("Queue empty — nothing to post.")
        return

    payload = load_json(next_file)
    targets = payload.get("targets") or [d["alias"] for d in destinations]
    alias_map = {d["alias"]: d for d in destinations}

    results = {}
    for alias in targets:
        dest = alias_map.get(alias)
        if not dest:
            results[alias] = "SKIPPED (unknown alias)"
            continue
        try:
            resp = post_to_page(dest, payload)
            results[alias] = f"OK {resp[:140]}..."
            time.sleep(1.0)  # gentle
        except Exception as e:
            results[alias] = f"ERROR {e}"

    print("Post results:")
    for k, v in results.items():
        print(f"- {k}: {v}")

    sha_note = os.environ.get("GITHUB_SHA", "")[:7]
    git_move_and_commit(next_file, sent_dir, sha_note)

if __name__ == "__main__":
    main()
