"""Field diagnostics: write one text file with everything needed to work out why a logger isn't reading.

Read-only. It never stops, launches or writes to the logger. Every step is wrapped so that a failure is
recorded (with the exact error and traceback) and the next step still runs.
"""
import os
import platform
import subprocess
import sys
import time
import traceback
from datetime import datetime

from . import device
from .version import __version__

SECTIONS_NOTE = "Send this whole file. Nothing in it is private except the logger's name and serial number."


def _run(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (r.stdout + (("\n[stderr]\n" + r.stderr) if r.stderr.strip() else "")).strip() or "(no output)"
    except Exception as e:  # noqa: BLE001
        return f"(could not run {cmd[0]}: {e!r})"


class Report:
    def __init__(self):
        self.lines = []

    def h(self, title):
        self.lines += ["", "=" * 70, title, "=" * 70]

    def add(self, text=""):
        self.lines.append(str(text))

    def step(self, title, fn):
        """Run fn(); record its return value or the failure. Returns fn's result, or None on failure."""
        t0 = time.time()
        try:
            out = fn()
            self.add(f"[ok  {time.time() - t0:5.2f}s] {title}" + (f": {out}" if out not in (None, "") else ""))
            return out if out is not None else True
        except Exception as e:  # noqa: BLE001
            self.add(f"[FAIL {time.time() - t0:5.2f}s] {title}: {type(e).__name__}: {e}")
            errno = getattr(e, "errno", None)
            if errno is not None:
                self.add(f"      errno={errno}  backend_error_code={getattr(e, 'backend_error_code', None)}")
            self.add("      " + traceback.format_exc().strip().replace("\n", "\n      "))
            return None

    def text(self):
        return "\n".join(self.lines) + "\n"


def _system(r: Report):
    r.h("APP AND SYSTEM")
    r.add(f"Unhoused Reader Pro {__version__}")
    r.add(f"Report made: {datetime.now().astimezone().isoformat(timespec='seconds')}")
    r.add(f"macOS: {platform.mac_ver()[0]}  machine: {platform.machine()}  platform: {platform.platform()}")
    r.add(f"Python: {sys.version.split()[0]}  frozen (packaged app): {bool(getattr(sys, 'frozen', False))}")
    r.add(f"Executable: {sys.executable}")
    r.add(f"Running as user: {os.environ.get('USER')}  uid={os.getuid()}")
    r.add(f"Bundled libusb dir: {getattr(sys, '_MEIPASS', None)}")
    r.add("sw_vers:\n" + _run(["sw_vers"]))


def _libusb(r: Report):
    r.h("LIBUSB / PYUSB")

    def backend():
        be = device._backend()
        if be is None:
            import usb.backend.libusb1 as l1
            be = l1.get_backend()
        if be is None:
            raise RuntimeError("No libusb backend found (libusb missing or not loadable)")
        lib = getattr(be, "lib", None)
        ver = getattr(lib, "_name", None)   # path of the loaded libusb
        return f"{type(be).__name__}, library {ver}"
    r.step("load libusb backend", backend)
    try:
        import usb
        r.add(f"pyusb version: {getattr(usb, '__version__', '?')}")
    except Exception as e:  # noqa: BLE001
        r.add(f"pyusb import failed: {e!r}")


def _macos_usb(r: Report):
    r.h("WHAT MACOS SEES ON USB")
    r.add("--- system_profiler SPUSBDataType ---")
    r.add(_run(["system_profiler", "SPUSBDataType"], timeout=40))
    r.add("")
    r.add("--- ioreg: Onset / HOBO entries ---")
    out = _run(["ioreg", "-p", "IOUSB", "-l", "-w0"], timeout=40)
    keep, block = [], []
    for line in out.splitlines():
        if "+-o" in line:
            if any(k in "\n".join(block).lower() for k in ("onset", "hobo", "0f1b", "3867")):
                keep += block
            block = []
        block.append(line)
    if any(k in "\n".join(block).lower() for k in ("onset", "hobo", "0f1b", "3867")):
        keep += block
    r.add("\n".join(keep) if keep else "(no Onset/HOBO entry in the IOUSB registry: macOS does not see the adapter)")


def _conflicts(r: Report):
    r.h("OTHER PROGRAMS THAT MIGHT HOLD THE ADAPTER")
    out = _run(["ps", "-axo", "pid,comm"])
    hits = [ln for ln in out.splitlines()
            if any(k in ln.lower() for k in ("hoboware", "onset", "hobo", "unhoused", "libusb", "ftdi", "silabs"))]
    r.add("\n".join(hits) if hits else "(no HOBOware / Onset processes running)")
    me = os.getpid()
    others = [ln for ln in hits if "unhoused" in ln.lower() and not ln.strip().startswith(str(me))]
    if others:
        r.add("NOTE: another copy of this app may be running (see the 'unhoused' lines above).")
    r.add("")
    r.add("launchd auto-open agent present: " + str(os.path.exists(
        os.path.expanduser("~/Library/LaunchAgents/com.jstrand.unhousedreader.usb.plist"))))


def _enumerate(r: Report):
    r.h("PYUSB ENUMERATION (every USB device libusb can see)")
    import usb.core

    def listing():
        devs = list(usb.core.find(find_all=True, backend=device._backend()))
        for d in devs:
            mark = "  <== HOBO adapter" if (d.idVendor, d.idProduct) == (device.VID, device.PID) else ""
            r.add(f"  {d.idVendor:04x}:{d.idProduct:04x}  bus {d.bus} addr {d.address}{mark}")
        return f"{len(devs)} device(s)"
    r.step("list devices", listing)
    return usb.core.find(idVendor=device.VID, idProduct=device.PID, backend=device._backend())


def _descriptors(r: Report, dev):
    r.h("ADAPTER DESCRIPTORS")
    for label, fn in (("manufacturer", lambda: dev.manufacturer), ("product", lambda: dev.product),
                      ("serial", lambda: dev.serial_number), ("bcdUSB", lambda: hex(dev.bcdUSB)),
                      ("speed", lambda: dev.speed), ("bNumConfigurations", lambda: dev.bNumConfigurations)):
        r.step(label, fn)
    r.step("kernel driver active on interface 0", lambda: dev.is_kernel_driver_active(0))
    r.step("active configuration", lambda: str(dev.get_active_configuration()).replace("\n", "\n      "))


def _talk(r: Report, dev):
    """Mirror Logger.__init__ but one stage at a time, so the failing stage is obvious. Read-only commands only."""
    import usb.util
    r.h("OPEN AND TALK TO THE ADAPTER (read-only)")
    claimed = False
    for attempt in range(1, 4):
        ok = r.step(f"attempt {attempt}: set_configuration", dev.set_configuration)
        ok = ok and r.step(f"attempt {attempt}: claim interface 0", lambda: usb.util.claim_interface(dev, 0))
        if ok:
            claimed = True
            break
        time.sleep(0.5)
    if not claimed:
        r.add("-> Could not open the adapter. The errors above say why (Access denied / busy = another program has it).")
        return

    def cmd(data):
        data = bytes(data).ljust(8, b"\0")
        dev.ctrl_transfer(0x21, 0x09, 0x0003, 0, data, timeout=2000)
        return bytes(dev.read(0x81, 8, timeout=2000))
    try:
        r.step("handshake 09 02", lambda: cmd([0x09, 0x02]).hex(" "))
        for i in range(1, 4):
            r.step(f"status 02 02 (try {i})", lambda: cmd([0x02, 0x02]).hex(" "))
            time.sleep(0.3)
        r.step("live reading 02 01", lambda: cmd([0x02, 0x01]).hex(" "))
        st = cmd([0x02, 0x02])
        r.add(f"decoded: logging={bool(st[0] & 0x02)} state=0x{st[0]:02x} pointer={st[1] << 8 | st[2]} "
              f"interval={st[3] << 8 | st[4]}s")

        def block(addr):
            cmd([0x03, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF])
            raw = bytes(dev.ctrl_transfer(0x80, 0x06, 0x030A, 0x0904, 74, timeout=2000))
            return raw[2:2 + device.BLOCK]
        head = b""
        for addr in range(0, 0x1C0, device.BLOCK):
            b = r.step(f"read block 0x{addr:04x}", lambda a=addr: block(a).hex(" "))
            if b is None:
                break
            head += bytes.fromhex(b) if isinstance(b, str) else b
        if head:
            r.add(f"header starts with 'HOBO' magic: {head[:4] == b'HOBO'}  (first bytes: {head[:16].hex(' ')})")
            from .actions import battery_volts
            from .decode import Readout
            r.step("decode header", lambda: (lambda ro: f"name={ro.name!r} serial={ro.serial} interval={ro.interval_s}s "
                                             f"started={ro.start}")(Readout(head)))
            r.step("battery estimate (V)", lambda: battery_volts(head))
            r.add("")
            r.add("Raw header (hex):")
            for i in range(0, len(head), 32):
                r.add(f"  {i:04x}  {head[i:i + 32].hex(' ')}")
    finally:
        r.step("release interface", lambda: usb.util.release_interface(dev, 0))
        r.step("dispose resources", lambda: usb.util.dispose_resources(dev))


def _library_path(r: Report):
    r.h("FULL-STACK CHECK (the app's own code path)")

    def go():
        from .actions import describe
        with device.Logger() as lg:
            d = describe(lg)
        return {k: d[k] for k in ("name", "serial", "interval_s", "logging", "state", "battery_v", "samples")}
    r.step("Logger() + describe()", go)


def build_report(context: dict | None = None) -> str:
    r = Report()
    r.add("UNHOUSED READER PRO - DIAGNOSTIC REPORT")
    r.add(SECTIONS_NOTE)
    if context:
        r.h("WHAT THE APP WAS SHOWING")
        for k, v in context.items():
            r.add(f"{k}: {v}")
    for section in (_system, _libusb, _macos_usb, _conflicts):
        try:
            section(r)
        except Exception:  # noqa: BLE001
            r.add("section crashed:\n" + traceback.format_exc())
    try:
        dev = _enumerate(r)
        if dev is None:
            r.h("ADAPTER")
            r.add("The HOBO adapter (0f1b:0160) is NOT visible to libusb. If it is also missing from the macOS list "
                  "above, the problem is the cable, port, hub or the adapter itself, not the app.")
        else:
            _descriptors(r, dev)
            _talk(r, dev)
            _library_path(r)
    except Exception:  # noqa: BLE001
        r.add("USB section crashed:\n" + traceback.format_exc())
    r.h("END OF REPORT")
    return r.text()


def default_path() -> str:
    folder = os.path.expanduser("~/Desktop")
    if not os.path.isdir(folder):
        folder = os.path.expanduser("~")
    return os.path.join(folder, f"Unhoused-diagnostics-{datetime.now():%Y%m%d-%H%M%S}.txt")


def write_report(path: str | None = None, context: dict | None = None) -> str:
    path = path or default_path()
    with open(path, "w", encoding="utf-8") as f:
        f.write(build_report(context))
    return path


def main():
    p = write_report()
    print("Wrote", p)


if __name__ == "__main__":
    main()
