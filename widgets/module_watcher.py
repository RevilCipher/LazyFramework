#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Watcher - Auto refresh modules when files change
Fix untuk installed version (Debian package)
"""

import os
import sys
import io
import shutil
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr

from PyQt6.QtCore import QObject, QFileSystemWatcher, QTimer, pyqtSignal


class ModuleWatcher(QObject):
    """Class terpisah untuk auto refresh modules - FIX PATH DETECTION"""
    
    modulesRefreshed = pyqtSignal()   # Signal ke GUI

    def __init__(self, framework, gui_instance=None, parent=None):
        super().__init__(parent)
        self.framework = framework
        self.gui = gui_instance
        self._watcher = None
        self._refresh_timer = None
        self._module_root = None

    def _find_module_root(self):
        """Find modules directory - robust untuk berbagai environment"""
        
        # === 1. Cek dari path file ini (widgets/module_watcher.py) ===
        current_file = Path(__file__).resolve()
        
        # widgets/module_watcher.py -> widgets -> root
        possible_root = current_file.parent.parent
        if (possible_root / "modules").exists():
            return possible_root / "modules"
        
        # === 2. Cek dari current working directory ===
        cwd = Path.cwd()
        if (cwd / "modules").exists():
            return cwd / "modules"
        
        # === 3. Cek dari parent cwd ===
        if (cwd.parent / "modules").exists():
            return cwd.parent / "modules"
        
        # === 4. Installed location (Debian package) ===
        installed_paths = [
            Path("/usr/share/lazyframework/modules"),
            Path("/usr/local/share/lazyframework/modules"),
            Path("/opt/lazyframework/modules"),
            Path.home() / ".local/share/lazyframework/modules",
            Path.home() / "lazyframework/modules",
        ]
        
        for p in installed_paths:
            if p.exists():
                return p
        
        # === 5. Termux location ===
        termux_path = Path("/data/data/com.termux/files/home/lazyframework/modules")
        if termux_path.exists():
            return termux_path
        
        # === 6. Scan dari sys.path ===
        for path in sys.path:
            p = Path(path) / "modules"
            if p.exists():
                return p
        
        # === 7. Fallback: cari dari project root dengan berbagai cara ===
        # Coba dari lokasi script utama
        for script in ["gui.py", "lzfconsole"]:
            for base in [Path.cwd(), Path(__file__).resolve().parent.parent, Path("/usr/share/lazyframework")]:
                if (base / script).exists():
                    mod_path = base / "modules"
                    if mod_path.exists():
                        return mod_path
        
        # === 8. Terakhir: buat folder modules jika belum ada ===
        fallback_path = Path.cwd() / "modules"
        fallback_path.mkdir(parents=True, exist_ok=True)
        return fallback_path

    def start_watching(self):
        """Mulai memantau folder modules"""
        try:
            # === FIND MODULES ROOT ===
            self._module_root = self._find_module_root()
            
            if not self._module_root.exists():
                if self.gui:
                    self.gui.append_output(f"[red]❌ Modules folder not found! Checked: {self._module_root}[/]")
                return False

            # === KUMPULKAN SEMUA FOLDER YANG DI-WATCH ===
            dirs_to_watch = [str(self._module_root)]
            
            # Tambahkan semua subfolder (kecuali __pycache__)
            for d in self._module_root.rglob("*"):
                if d.is_dir() and "__pycache__" not in d.parts:
                    dirs_to_watch.append(str(d.resolve()))

            # Hapus duplikat
            dirs_to_watch = list(set(dirs_to_watch))

            # === SETUP QFileSystemWatcher ===
            self._watcher = QFileSystemWatcher(self)
            
            # Tambahkan path satu per satu (lebih aman)
            added_count = 0
            for path in dirs_to_watch:
                try:
                    self._watcher.addPath(path)
                    added_count += 1
                except Exception as e:
                    if self.gui:
                        self.gui.append_output(f"[dim]Could not watch: {path} ({e})[/]")
            
            if self.gui and added_count > 0:
                self.gui.append_output(f"[cyan]👁️ Module watcher aktif: {added_count} folder dipantau[/]")
                self.gui.append_output(f"[dim]Monitoring: {self._module_root}[/]")

            # === SETUP TIMER ===
            self._refresh_timer = QTimer(self)
            self._refresh_timer.setSingleShot(True)
            self._refresh_timer.setInterval(1200)  # 1.2 detik debounce
            self._refresh_timer.timeout.connect(self._do_refresh)

            # === CONNECT SIGNALS ===
            self._watcher.directoryChanged.connect(self._on_dir_changed)
            self._watcher.fileChanged.connect(self._on_file_changed)

            return True

        except Exception as e:
            if self.gui:
                self.gui.append_output(f"[red]ModuleWatcher error: {e}[/]")
            print(f"ModuleWatcher error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _on_dir_changed(self, path):
        """Dipanggil saat folder berubah"""
        # Tambahkan folder baru jika ada
        try:
            p = Path(path)
            for d in p.iterdir():
                if d.is_dir() and "__pycache__" not in d.parts:
                    dp = str(d.resolve())
                    if dp not in self._watcher.directories():
                        self._watcher.addPath(dp)
        except Exception:
            pass
        
        if self._refresh_timer and not self._refresh_timer.isActive():
            self._refresh_timer.start()

    def _on_file_changed(self, path):
        """Dipanggil saat file berubah"""
        # Jika file .py berubah, refresh
        if path.endswith('.py'):
            if self._refresh_timer and not self._refresh_timer.isActive():
                self._refresh_timer.start()

    def _do_refresh(self):
        """Lakukan refresh modules - dengan capture output"""
        try:
            # === CAPTURE OUTPUT DARI SCAN_MODULES ===
            output_buffer = io.StringIO()
            
            with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                self.framework.scan_modules()
            
            # Optional: tampilkan output jika diperlukan (tapi filter)
            output = output_buffer.getvalue()
            if output.strip() and self.gui:
                # Filter pesan yang tidak perlu ditampilkan
                lines = output.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and '[DEBUG]' not in line:
                        # Jangan tampilkan pesan scanning module tree
                        if not line.startswith('[*] Scanning module tree'):
                            # Tampilkan dengan warna dim
                            self.gui.append_output(f"[dim]{line}[/]")
            
            # === EMIT SIGNAL KE GUI ===
            self.modulesRefreshed.emit()

            if self.gui:
                total = len(self.framework.modules)
                self.gui.append_output(f"[green]✓ Auto-refresh: {total} modules ditemukan[/]")
                self.gui.update_session_info()

        except Exception as e:
            if self.gui:
                self.gui.append_output(f"[red]Auto-refresh failed: {e}[/]")
                import traceback
                self.gui.append_output(f"[red]{traceback.format_exc()}[/]")

    def stop_watching(self):
        """Stop watching modules"""
        if self._watcher:
            try:
                paths = self._watcher.directories() + self._watcher.files()
                if paths:
                    self._watcher.removePaths(paths)
            except Exception:
                pass
            self._watcher = None
        
        if self._refresh_timer:
            self._refresh_timer.stop()
            self._refresh_timer = None
        
        if self.gui:
            self.gui.append_output("[dim]Module watcher stopped[/]")

    def add_watch_path(self, path):
        """Tambahkan path baru untuk di-watch"""
        if self._watcher:
            try:
                p = Path(path)
                if p.exists():
                    self._watcher.addPath(str(p.resolve()))
                    return True
            except Exception:
                pass
        return False

    def remove_watch_path(self, path):
        """Hapus path dari watch list"""
        if self._watcher:
            try:
                self._watcher.removePath(path)
                return True
            except Exception:
                pass
        return False

    def get_watched_paths(self):
        """Dapatkan daftar path yang di-watch"""
        if self._watcher:
            return self._watcher.directories() + self._watcher.files()
        return []