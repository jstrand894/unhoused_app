"""Check GitHub for a newer release. Manual only: nothing is sent unless the user asks."""
import json
import urllib.request

API = "https://api.github.com/repos/jstrand894/unhoused_app/releases/latest"
DMG = "https://github.com/jstrand894/unhoused_app/releases/latest/download/Unhoused-Reader-Pro.dmg"


def parse(v):
    return tuple(int(x) for x in v.lstrip("vV").split("."))


def is_newer(latest, current):
    try:
        return parse(latest) > parse(current)
    except ValueError:
        return False


def latest_release():
    """Returns (version, notes) of the newest GitHub release. Raises on network errors or if none exists."""
    req = urllib.request.Request(API, headers={"Accept": "application/vnd.github+json", "User-Agent": "UnhousedReader"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.load(r)
    return data["tag_name"].lstrip("vV"), data.get("body") or ""
