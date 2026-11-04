"""Check GitHub for a newer release, and install it in place. Manual only: nothing is sent unless the user asks."""
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
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
    """Returns (version, dmg_url) of the newest GitHub release. Raises on network errors or if none exists."""
    req = urllib.request.Request(API, headers={"Accept": "application/vnd.github+json", "User-Agent": "UnhousedReader"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.load(r)
    url = next((a["browser_download_url"] for a in data.get("assets", []) if a["name"].endswith(".dmg")), DMG)
    return data["tag_name"].lstrip("vV"), url


def installed_app_path():
    """The .app this process is running from, or None when running from source."""
    exe = os.path.realpath(sys.executable)
    if getattr(sys, "frozen", False) and ".app/Contents/MacOS/" in exe:
        return exe.split("/Contents/MacOS/")[0]
    return None


def can_self_update():
    app = installed_app_path()
    return bool(app) and os.access(os.path.dirname(app), os.W_OK)


def stage_update(dmg_url, progress=None):
    """Download the DMG and copy the app out of it into a temp folder. Returns the staged .app path."""
    work = tempfile.mkdtemp(prefix="unhoused-update-")
    dmg = os.path.join(work, "update.dmg")
    req = urllib.request.Request(dmg_url, headers={"User-Agent": "UnhousedReader"})
    with urllib.request.urlopen(req, timeout=30) as r, open(dmg, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while chunk := r.read(1 << 16):
            f.write(chunk)
            done += len(chunk)
            if progress and total:
                progress(done, total)
    mnt = os.path.join(work, "mnt")
    os.mkdir(mnt)
    subprocess.run(["hdiutil", "attach", "-nobrowse", "-readonly", "-mountpoint", mnt, dmg],
                   check=True, capture_output=True)
    try:
        app = next(n for n in os.listdir(mnt) if n.endswith(".app"))
        staged = os.path.join(work, app)
        shutil.copytree(os.path.join(mnt, app), staged, symlinks=True)
    finally:
        subprocess.run(["hdiutil", "detach", mnt, "-quiet"], capture_output=True)
    os.remove(dmg)
    return staged


def swap_script(pid, target, staged, opener="open"):
    """Shell script that waits for the app to quit, swaps in the new copy (keeping the old one if that fails),
    and opens it."""
    t, s = shlex.quote(target), shlex.quote(staged)
    return f"""#!/bin/bash
while kill -0 {int(pid)} 2>/dev/null; do sleep 0.3; done
mv {t} {t}.old && {{ mv {s} {t} || mv {t}.old {t}; }}
rm -rf {t}.old
{opener} {t}
rm -rf {shlex.quote(os.path.dirname(staged))}
"""


def launch_swap(staged, opener="open"):
    """Start the swap script detached; the caller must quit the app right after."""
    target = installed_app_path()
    script = os.path.join(os.path.dirname(staged), "swap.sh")
    with open(script, "w") as f:
        f.write(swap_script(os.getpid(), target, staged, opener))
    subprocess.Popen(["/bin/bash", script], start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
