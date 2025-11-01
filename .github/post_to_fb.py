import os, json, time, mimetypes
from datetime import datetime
from dateutil import tz
import requests

GRAPH = "https://graph.facebook.com/v18.0"  # update if FB bumps versions
TZ_NAME = os.getenv("HUI_TIMEZONE", "America/Chicago")
LOCAL_TZ = tz.gettz(TZ_NAME)
DRY_RUN = os.getenv("DRY_RUN", "false").strip().lower() == "true"

DEST_FILE = "destinations.json"
QUEUE_FILE = "content_queue.json"

def now_local():
    return datetime.now(LOCAL_TZ)

def parse_dt_local(s):
    """
    Accepts:
      - 'YYYY-MM-DD HH:MM' (local)
      - ISO 8601 (with or without tz; assumed local if none)
    Returns timezone-aware datetime in local tz.
    """
    if not s:
        return None
    s = s.strip()
    # try simple "YYYY-MM-DD HH:MM"
    try:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M")
        return dt.replace(tzinfo=LOCAL_TZ)
    except Exception:
        pass
    # try ISO
    try:
        from datetime import datetime as dtmod
        dt = dtmod.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=LOCAL_TZ)
        return dt.astimezone(LOCAL_TZ)
    except Exception:
        return None

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def get_token(env_name):
    val = os.getenv(env_name, "").strip()
    if not val:
        raise RuntimeError(f"Missing token in env: {env_name}")
    return val

def fb_post_feed(token, target_id, message, link=None):
    url = f"{GRAPH}/{target_id}/feed"
    data = {"access_token": token}
    if message:
        data["message"] = message
    if link:
        data["link"] = link
    if DRY_RUN:
        print("[DRY_RUN] FEED:", {"id": target_id, "message": message, "link": link})
        return {"id": "DRY_RUN_FEED"}
    r = requests.post(url, data=data, timeout=120)
    r.raise_for_status()
    return r.json()

def fb_post_photo(token, target_id, message, image_path, is_page):
    # Pages use /photos; Groups also accept /photos
    url = f"{GRAPH}/{target_id}/photos"
    data = {"access_token": token}
    if message:
        data["caption"] = message
    # For pages/groups, 'published' defaults to true when posting to container ID
    files = {}
    with open(image_path, "rb") as f:
        mime = mimetypes.guess_type(image_path)[0] or "image/jpeg"
        files["source"] = (os.path.basename(image_path), f, mime)
        if DRY_RUN:
            print("[DRY_RUN] PHOTO:", {"id": target_id, "message": message, "file": image_path})
            return {"id": "DRY_RUN_PHOTO"}
        r = requests.post(url, data=data, files=files, timeout=300)
        r.raise_for_status()
        return r.json()

def fb_post_video(token, target_id, message, video_path, is_page):
    # Pages: /{page-id}/videos ; Groups: /{group-id}/videos
    url = f"{GRAPH}/{target_id}/videos"
    data = {"access_token": token}
    if message:
        data["description"] = message
    with open(video_path, "rb") as f:
        mime = mimetypes.guess_type(video_path)[0] or "video/mp4"
        files = {"source": (os.path.basename(video_path), f, mime)}
        if DRY_RUN:
            print("[DRY_RUN] VIDEO:", {"id": target_id, "message": message, "file": video_path})
            return {"id": "DRY_RUN_VIDEO"}
        r = requests.post(url, data=data, files=files, timeout=1200)
        r.raise_for_status()
        return r.json()

def post_one(dest, item):
    alias = dest["alias"]
    dest_id = dest["id"]
    token = get_token(dest["token_env"])
    is_page = (dest.get("type","page").lower()=="page")

    msg   = item.get("message") or ""
    link  = item.get("link")
    img   = item.get("image_path")
    vid   = item.get("video_path")

    if vid:
        return fb_post_video(token, dest_id, msg, vid, is_page)
    if img:
        return fb_post_photo(token, dest_id, msg, img, is_page)
    return fb_post_feed(token, dest_id, msg, link)

def is_due(item, now):
    if "posted_by" in item and isinstance(item["posted_by"], dict):
        # if all targets already posted, skip entirely
        targets = item.get("targets") or []
        if targets and all(alias in item["posted_by"] for alias in targets):
            return False
    sched = parse_dt_local(item.get("scheduled_at"))
    if sched is None:
        return True
    return sched <= now

def main():
    now = now_local()
    destinations = load_json(DEST_FILE, [])
    queue = load_json(QUEUE_FILE, [])

    # Build alias → destination map
    dest_map = {d["alias"]: d for d in destinations}

    changed = False

    for item in queue:
        targets = item.get("targets") or []
        if not targets:
            continue

        if not is_due(item, now):
            continue

        posted_by = item.get("posted_by") or {}
        for alias in targets:
            if alias in posted_by:
                continue  # already posted to this target
            if alias not in dest_map:
                posted_by[alias] = {"error": "Unknown target alias"}
                continue

            dest = dest_map[alias]
            try:
                print(f"Posting to {alias}: {item.get('message','')[:60]!r}")
                resp = post_one(dest, item)
                posted_by[alias] = {
                    "ok": True,
                    "time": now.isoformat(),
                    "resp": resp
                }
                changed = True
                time.sleep(2)
            except requests.HTTPError as e:
                body = e.response.text if e.response is not None else str(e)
                print(f"[HTTPError] {alias}: {body}")
                posted_by[alias] = {"ok": False, "error": body}
                changed = True
            except Exception as e:
                print(f"[Error] {alias}: {e}")
                posted_by[alias] = {"ok": False, "error": str(e)}
                changed = True

        item["posted_by"] = posted_by

    if changed:
        save_json(QUEUE_FILE, queue)
        print("Queue updated.")
    else:
        print("Nothing due.")

if __name__ == "__main__":
    main()

