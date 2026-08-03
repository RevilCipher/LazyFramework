#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import contextlib
import importlib
import sys
import socket
import math
import os
import io
import re
import signal
import time
import subprocess
import threading
import random

from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import *

from PyQt6.QtCore import (
    Qt,
    pyqtSignal,
    QObject,
    QThread,
    QTimer,
    QUrl,
    QEvent,
    QPropertyAnimation,
    QEasingCurve,
    QPoint,
    QFileSystemWatcher,
)
from PyQt6.QtCore import QMetaObject
from PyQt6.QtGui import (
    QFont,
    QTextCursor,
    QPalette,
    QColor,
    QAction,
    QKeySequence,
    QIntValidator,
    QLinearGradient,
    QPainter,
    QPen,
)
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon, QFontMetrics, QPainterPath
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtNetwork import QNetworkProxy
from PyQt6.QtCore import QMetaObject, Qt
from PyQt6.QtWidgets import QComboBox
from PyQt6.QtWidgets import QFileDialog, QInputDialog, QGraphicsDropShadowEffect
from widgets.ai_assistant import AIAssistantWidget
from PyQt6.QtWidgets import QSplitter

from bin.console import LazyFramework
from core import load_banners_from_folder, get_random_banner

try:
    import modules.payload.reverse.reverse_tcp as _rtcp_mod
    from modules.payload.reverse.reverse_tcp import send_command_to_session
except ImportError:
    import sys
    import os
    import modules.payload.reverse.reverse_tcp as _rtcp_mod
    from modules.payload.reverse.reverse_tcp import send_command_to_session

from widgets.notif import CyberpunkToast
from widgets.theme_manager import ThemeManager
from widgets.network_map import NetworkMapWidget
from widgets.proxy_dialog import ProxySettingsDialog
from widgets.module_watcher import ModuleWatcher
from widgets.module_tab import ModuleTab
from widgets.session_tab import SessionTab

from core.capture import UniversalCapture
from core.module_runner import ModuleRunner

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QLineEdit, QListWidget,
    QTreeWidget, QTreeWidgetItem, QTabWidget, QSplitter,
    QGroupBox, QScrollArea, QProgressBar, QMessageBox,
    QMenu, QMenuBar, QFileDialog, QInputDialog, QSplashScreen,
    QFormLayout, QFrame, QListWidgetItem, QTabBar
)
from widgets.ransomware_dialog import RansomwareDialog
import faulthandler
import signal
import sys

os.environ["PATH"] = os.environ.get("PATH", "") + ":/usr/bin:/usr/local/bin:/usr/share"

faulthandler.enable()
faulthandler.enable(file=open("crash.log", "a"))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class GUIConsole:
    def __init__(self, output_callback):
        self.output_callback = output_callback

    def print(self, *args, **kwargs):
        try:
            from io import StringIO
            from rich.console import Console

            with StringIO() as buffer:
                console = Console(file=buffer, force_terminal=False, width=120)
                console.print(*args, **kwargs)
                output = buffer.getvalue().rstrip()
                if output:
                    self.output_callback(output)
        except Exception as e:
            self.output_callback(f"[red]Console error: {e}[/red]")



# ===== ✅ FIXED: OSIconManager - Centralized OS icon/color management =====
class OSIconManager:
    """✅ Centralize OS icon dan color management untuk consistency"""
    
    ICONS = {
        "windows": "🪟", "linux": "🐧", "ubuntu": "🐧", "debian": "🐧", 
        "kali": "🐧", "fedora": "🐧", "arch": "🐧", "centos": "🐧",
        "rhel": "🐧", "amazon": "🐧", "alpine": "🐧", "macos": "🍎",
        "darwin": "🍎", "freebsd": "🐋", "bsd": "🐋", "openbsd": "🐋",
        "sunos": "☀️", "solaris": "☀️", "unknown": "💻"
    }
    
    COLORS = {
        "windows": "#4A90E2", "linux": "#F0F0F0", "ubuntu": "#DD4814",
        "debian": "#A53860", "kali": "#336699", "fedora": "#003478",
        "arch": "#1793D1", "centos": "#922B7A", "rhel": "#CC0000",
        "amazon": "#FF9900", "macos": "#646464", "freebsd": "#AB2B1D",
        "unknown": "#808080"
    }
    
    @staticmethod
    def get_icon(os_type: str) -> str:
        return OSIconManager.ICONS.get(os_type.lower() if os_type else "unknown", "💻")
    
    @staticmethod
    def get_color(os_type: str) -> str:
        return OSIconManager.COLORS.get(os_type.lower() if os_type else "unknown", "#808080")

class LazyFrameworkGUI(QMainWindow):
    session_output_signal = pyqtSignal(str, str)
    console_output_signal = pyqtSignal(str)
    session_killed_signal = pyqtSignal(str)
    session_connected = pyqtSignal(dict)  # ✅ NEW: Signal ketika session terhubung

    def __init__(self):
        super().__init__()
        self.show_splash_screen()
        self.setWindowIcon(QIcon(""))

        import io as _io
        _null = _io.StringIO()
        with redirect_stdout(_null), redirect_stderr(_null):
            self.framework = LazyFramework()

        self.capture = UniversalCapture()
        self.capture.output_signal.connect(self.append_output)

        self.framework.console = GUIConsole(self.append_output)
        self.framework.scan_modules()

        self.current_module = None
        self.workers = []
        self.command_history = []
        self.history_index = -1
        self.module_runner = None
        self.session_tabs = {}
        self.floating_sessions = {}

        self.active_session_id = None
        self.selected_session_id = None
        self.reverse_listener = None
        self.current_proxy = None
        self.proxy_enabled = False

        self.custom_proxies = []
        self.current_proxy_index = -1

        self.browser = None
        self.browser_tab = None
        self.browser_controls_widget = None
        self.browser_placeholder = None
        self.sessions = {}
        self.active_listeners = {}
        self.listener_lock = threading.Lock()
        self.session_lock = threading.Lock()
        self.framework.session["gui_sessions"] = {
            "dict": self.sessions,
            "lock": self.session_lock,
        }
        self.framework.session["gui_instance"] = self
        self.theme_manager = ThemeManager(QApplication.instance(), self)
        self.ensure_monospace_fonts()
        self.init_ui()
        self.console_output.setObjectName("console_output")
        self.session_output.setObjectName("session_output")
        self.session_info.setObjectName("session_info")
        self.module_info.setObjectName("module_info")
        self.search_input.setObjectName("search_input")

        self.session_output_signal.connect(self.append_session_output)
        self.console_output_signal.connect(self.append_output)
        self.session_killed_signal.connect(self.on_session_killed)
        self.session_connected.connect(self.on_session_connected)  # ✅ NEW

        self.active_listeners = []
        self.listener_lock = threading.RLock()

        import glob
        import shutil
        cache_dirs = glob.glob("**/__pycache__", recursive=True)
        for cache in cache_dirs:
            try:
                shutil.rmtree(cache)
            except Exception as e:
                pass

        self.load_banner()

        self.module_watcher = ModuleWatcher(
            self.framework, gui_instance=self, parent=self
        )
        self.module_watcher.modulesRefreshed.connect(self.load_all_modules)
        QTimer.singleShot(800, self.module_watcher.start_watching)
        QTimer.singleShot(2000, self.start_tor_auto_rotate)
        self.last_tor_ip = None
        self.active_module = ""

        self.update_session_info()

        QTimer.singleShot(
            1500,
            lambda: self.show_cyber_toast(
                "LazyFramework GUI v2.0 ready",
                title="Welcome",
                duration_ms=5000,
                level="success",
            ),
        )

    # ==================== SESSION TAB METHODS ====================

    def create_session_tab(self, session_id, session_data):
        """
        ✅ IMPROVED: Thread-safe session tab creation with SESSIONS sync
        """
        # First, try to sync with reverse_tcp SESSIONS
        try:
            from modules.payload.reverse.reverse_tcp import SESSIONS, SESSIONS_LOCK
            with SESSIONS_LOCK:
                if session_id in SESSIONS:
                    # Update session_data with info from SESSIONS
                    rev_sess = SESSIONS[session_id]
                    session_data['handler'] = rev_sess
                    session_data['socket'] = getattr(rev_sess, 'socket', None)
                    session_data['os'] = getattr(rev_sess, 'os', session_data.get('os', 'unknown'))
                    session_data['hostname'] = getattr(rev_sess, 'hostname', session_data.get('hostname', ''))
                    self.append_output(f"[dim]Synced session {session_id} with SESSIONS[/]")
        except Exception as e:
            print(f"[!] SESSIONS sync error: {e}")
        
        # Check if already open
        if session_id in self.session_tabs:
            print(f"[*] Session tab {session_id} already exists, switching to it")
            for i in range(self.main_tabs.count()):
                if self.main_tabs.tabText(i) == f"📡 {session_id}":
                    self.main_tabs.setCurrentIndex(i)
                    return
        
        print(f"[*] Creating session tab for {session_id}...")
        
        # Validate session data
        if not session_data:
            self.append_output(f"[red]Error: Invalid session data for {session_id}[/red]")
            return
        
        try:
            # Create tab
            tab = SessionTab(session_id, session_data)
            
            # Connect signals
            tab.command_sent.connect(
                lambda sid, cmd: self._on_session_command(sid, cmd)
            )
            tab.tab_closed.connect(
                lambda sid: self._close_session_tab(sid)
            )
            tab.detach_requested.connect(
                lambda sid: self._detach_session_tab(sid)
            )
            
            # Store reference
            self.session_tabs[session_id] = tab
            
            # Add to tab widget
            index = self.main_tabs.insertTab(0, tab, f"📡 {session_id}")
            self.main_tabs.setCurrentIndex(index)
            
            # Enable close button for tabs
            self.main_tabs.setTabsClosable(True)
            try:
                self.main_tabs.tabCloseRequested.disconnect()
            except:
                pass
            self.main_tabs.tabCloseRequested.connect(self._on_tab_close)
            
            # Update tab info
            self._update_session_tab_info(session_id, session_data)
            
            # Set focus to input field
            tab.cmd_input.setFocus()
            
            self.append_output(f"[green]✓ Session tab opened: {session_id}[/]")
            
        except Exception as e:
            self.append_output(f"[red]✗ Error creating session tab: {e}[/red]")
            print(f"[!] Session tab creation error: {e}")
            import traceback
            traceback.print_exc()

    def _detach_session_tab(self, session_id):
        """Lepas SessionTab dari main_tabs → jendela floating"""
        if session_id not in self.session_tabs:
            return
        if session_id in self.floating_sessions:
            # Sudah floating → fokuskan saja
            win = self.floating_sessions[session_id]
            win.raise_()
            win.activateWindow()
            return

        tab = self.session_tabs[session_id]

        # Hapus dari tab widget (jangan delete)
        for i in range(self.main_tabs.count()):
            if self.main_tabs.widget(i) == tab:
                self.main_tabs.removeTab(i)
                break

        # Buat floating window
        from widgets.floating_session import FloatingSessionWindow
        
        win = FloatingSessionWindow(tab, parent=self)
        win.closed.connect(self._redock_session_tab)
        
        # ===== PENTING: Connect signal command_sent dari tab ke GUI =====
        # Pastikan command dari floating window sampai ke GUI
        tab.command_sent.connect(self._on_session_command)
        
        self.floating_sessions[session_id] = win
        win.show()

        self.append_output(f"[dim]⧉ Session {session_id} detached (floating)[/]")

    def _redock_session_tab(self, session_id):
        """Kembalikan SessionTab ke main_tabs saat floating window ditutup"""
        if session_id not in self.floating_sessions:
            return

        win = self.floating_sessions.pop(session_id)
        tab = win.session_tab

        # Lepas dari floating window
        tab.setParent(None)

        # Tampilkan lagi tombol float
        if hasattr(tab, "float_btn"):
            tab.float_btn.show()

        # Masukkan kembali ke main_tabs
        index = self.main_tabs.insertTab(0, tab, f"📡 {session_id}")
        self.main_tabs.setCurrentIndex(index)

        win.deleteLater()
        self.append_output(f"[dim]⧉ Session {session_id} re-docked[/]")

    def _close_session_tab(self, session_id):
        """Update: handle juga kalau lagi floating"""
        # Tutup floating dulu jika ada
        if session_id in self.floating_sessions:
            win = self.floating_sessions.pop(session_id)
            win.close()
            win.deleteLater()

        if session_id not in self.session_tabs:
            return

        try:
            tab = self.session_tabs[session_id]

            for i in range(self.main_tabs.count()):
                if self.main_tabs.widget(i) == tab:
                    self.main_tabs.removeTab(i)
                    break

            try:
                tab.deleteLater()
            except Exception:
                pass

            del self.session_tabs[session_id]

            if self.active_session_id == session_id:
                self.active_session_id = None

            self.append_output(f"[dim]✓ Session tab closed: {session_id}[/]")
        except Exception as e:
            print(f"[!] Error closing session tab {session_id}: {e}")


    def fix_session_sync(self):
        """Force sync GUI sessions with reverse_tcp SESSIONS"""
        self.append_output("[yellow][*] Forcing session sync...[/]")
        
        try:
            from modules.payload.reverse.reverse_tcp import SESSIONS, SESSIONS_LOCK
            
            with SESSIONS_LOCK:
                rev_sessions = dict(SESSIONS)
            
            self.append_output(f"[dim]Reverse TCP SESSIONS: {len(rev_sessions)}[/]")
            
            for sid, sess in rev_sessions.items():
                # Check if session exists in GUI
                if sid not in self.sessions:
                    # Create GUI session
                    session_data = {
                        'id': sid,
                        'type': getattr(sess, 'type', 'reverse_tcp'),
                        'ip': getattr(sess, 'rhost', 'unknown'),
                        'port': getattr(sess, 'rport', 'unknown'),
                        'lhost': getattr(sess, 'lhost', 'unknown'),
                        'lport': getattr(sess, 'lport', 'unknown'),
                        'os': getattr(sess, 'os', 'unknown'),
                        'hostname': getattr(sess, 'hostname', f'target_{sid[-4:]}'),
                        'status': getattr(sess, 'status', 'alive'),
                        'handler': sess,
                        'socket': getattr(sess, 'socket', None),
                        'output': f"[*] Session {sid} synced\n"
                    }
                    self.sessions[sid] = session_data
                    self.append_output(f"[green]✓ Added session {sid} to GUI[/]")
                    
                    # Create tab if not exists
                    if sid not in self.session_tabs:
                        self.create_session_tab(sid, session_data)
                else:
                    # Update existing session
                    self.sessions[sid]['handler'] = sess
                    self.sessions[sid]['socket'] = getattr(sess, 'socket', None)
                    self.sessions[sid]['os'] = getattr(sess, 'os', 'unknown')
                    self.sessions[sid]['hostname'] = getattr(sess, 'hostname', 'unknown')
            
            self.update_sessions_ui()
            self.update_session_info()
            self.append_output("[green]✓ Session sync completed[/]")
            
        except Exception as e:
            self.append_output(f"[red]Sync error: {e}[/]")
            import traceback
            traceback.print_exc()


    def _on_tab_close(self, index):
        tab_text = self.main_tabs.tabText(index)

        for session_id, tab in self.session_tabs.items():
            if f"📡 {session_id}" == tab_text:
                self._close_session_tab(session_id)
                return

        self._close_main_tab(index)

    def _close_session_tab(self, session_id):
        """
        ✅ IMPROVED: Proper cleanup of session tabs
        """
        if session_id not in self.session_tabs:
            print(f"[*] Session {session_id} already closed")
            return
        
        try:
            tab = self.session_tabs[session_id]
            
            # Find and remove tab from widget
            for i in range(self.main_tabs.count()):
                if self.main_tabs.widget(i) == tab:
                    self.main_tabs.removeTab(i)
                    break
            
            # Cleanup tab
            try:
                tab.deleteLater()
            except:
                pass
            
            # Remove from dict
            del self.session_tabs[session_id]
            
            # Clear active session if needed
            if self.active_session_id == session_id:
                self.active_session_id = None
            
            self.append_output(f"[dim]✓ Session tab closed: {session_id}[/]")
            
        except Exception as e:
            print(f"[!] Error closing session tab {session_id}: {e}")

    def _on_session_command(self, session_id, command):
        try:
            from modules.payload.reverse.reverse_tcp import SESSIONS, SESSIONS_LOCK
            
            # Tampilkan status di console
            self.console_output.insertHtml(
                f'<span style="color:#ffff00;">→ Sending to {session_id}: {command}</span><br>'
            )
            
            self.sync_sessions_from_reverse_tcp()
            
            # Cari session object
            session_obj = None
            try:
                with SESSIONS_LOCK:
                    if session_id in SESSIONS:
                        session_obj = SESSIONS[session_id]
            except:
                pass
            
            if session_obj is None and session_id in self.sessions:
                session_obj = self.sessions[session_id].get('handler')
            
            if session_obj is None:
                self.console_output.insertHtml(
                    f'<span style="color:#ff5555;">❌ Session {session_id} not found</span><br>'
                )
                return
            
            # Kirim command
            try:
                if hasattr(session_obj, 'send_command_gui'):
                    output = session_obj.send_command_gui(command)
                elif hasattr(session_obj, 'send_command'):
                    output = session_obj.send_command(command)
                else:
                    from modules.payload.reverse.reverse_tcp import send_command_to_session
                    success = send_command_to_session(session_id, command)
                    if success:
                        self.console_output.insertHtml(
                            '<span style="color:#50fa7b;">✓ Command sent via module function</span><br>'
                        )
                    else:
                        self.console_output.insertHtml(
                            '<span style="color:#ff5555;">❌ Failed to send command</span><br>'
                        )
                    return
                
                if output and output.strip():
                    # ===== KIRIM KE SESSION TAB (yang akan forward ke floating) =====
                    self.append_session_output_to_tab(session_id, output)
                    
                    # ===== HAPUS INI: jangan kirim langsung ke floating =====
                    # if session_id in self.floating_sessions:
                    #     win = self.floating_sessions[session_id]
                    #     if hasattr(win, '_append_output'):
                    #         win._append_output(output)
                    
                    self.console_output.insertHtml(
                        '<span style="color:#50fa7b;">✓ Command executed</span><br>'
                    )
                else:
                    self.console_output.insertHtml(
                        '<span style="color:#888888;">Command executed (no output)</span><br>'
                    )
                    self.append_session_output_to_tab(session_id, "[*] Command executed (no output)")
                        
            except Exception as e:
                self.console_output.insertHtml(
                    f'<span style="color:#ff5555;">Command error: {e}</span><br>'
                )
                    
        except Exception as e:
            self.console_output.insertHtml(
                f'<span style="color:#ff5555;">Unexpected error: {e}</span><br>'
            )


    def _update_session_tab_info(self, session_id, session_data):
        if session_id not in self.session_tabs:
            return
        
        try:
            tab = self.session_tabs[session_id]
            ip = session_data.get('ip', '?')
            port = session_data.get('port', '?')
            os_type = session_data.get('os', 'unknown')
            hostname = session_data.get('hostname', '')
            
            # Update info label
            icon = OSIconManager.get_icon(os_type)
            tab.info_label.setText(f"{icon} {ip}:{port} | {os_type.upper()}")
            
            # Update tab title - LOOP YANG BENAR
            for i in range(self.main_tabs.count()):
                if self.main_tabs.widget(i) == tab:
                    if hostname and hostname != 'unknown':
                        tab_text = f"📡 {hostname[:15]}"
                    else:
                        tab_text = f"📡 {session_id[:10]}"
                    self.main_tabs.setTabText(i, tab_text)
                    break
        except Exception as e:
            print(f"[!] Error updating session tab info: {e}")


    def get_active_session_tab(self):
        """
        ✅ GET: Safely get current session tab
        """
        try:
            current_widget = self.main_tabs.currentWidget()
            if isinstance(current_widget, SessionTab):
                return current_widget
        except:
            pass
        return None



    def append_session_output_to_tab(self, session_id, text):
        """
        ✅ IMPROVED: Kirim output ke session tab DAN floating window
        """
        if not text or not text.strip():
            return
        
        # Kirim ke session tab
        if session_id in self.session_tabs:
            try:
                tab = self.session_tabs[session_id]
                if hasattr(tab, 'append_output'):
                    tab.append_output(text)
            except Exception as e:
                print(f"[!] Error appending to session tab: {e}")
        
        


    def _open_new_session_tab(self):
        if not self.sessions:
            self.append_output("[yellow]No sessions available[/yellow]")
            return

        session_ids = list(self.sessions.keys())
        if not session_ids:
            self.append_output("[yellow]No sessions available[/yellow]")
            return

        items = []
        for sid in session_ids:
            sess = self.sessions.get(sid, {})
            ip = sess.get('ip', '?')
            port = sess.get('port', '?')
            os_type = sess.get('os', 'unknown')
            hostname = sess.get('hostname', '')
            os_icons = {'linux': '🐧', 'windows': '🪟', 'macos': '🍎', 'unknown': '💻'}
            icon = os_icons.get(os_type, '💻')

            if hostname and hostname != 'unknown':
                display = f"{icon} {hostname} ({ip}:{port})"
            else:
                display = f"{icon} {sid} ({ip}:{port})"
            items.append(display)

        session_id, ok = QInputDialog.getItem(
            self,
            "Select Session",
            "Choose session to open in new tab:",
            items,
            0,
            False
        )

        if ok and session_id:
            idx = items.index(session_id)
            actual_id = session_ids[idx]
            session_data = self.sessions.get(actual_id, {})
            self.create_session_tab(actual_id, session_data)

    # ==================== EXISTING METHODS ====================

    def load_banner(self):
        try:
            from core import load_banners_from_folder, get_random_banner
            
            load_banners_from_folder()
            raw_banner = get_random_banner()
            
            if not raw_banner:
                self.append_output("[yellow]No banner found in 'banner/' folder[/yellow]")
                return
            
            # ===== PROPER PARSING =====
            import re
            
            # 1. Parse warna dan styling dari raw_banner
            def parse_banner_rich(text):
                # Mapping warna dari rich ke HTML
                color_map = {
                    'red': '#ff5555',
                    'green': '#50fa7b',
                    'yellow': '#f1fa8c',
                    'blue': '#6272a4',
                    'magenta': '#ff79c6',
                    'cyan': '#8be9fd',
                    'white': '#ffffff',
                    'bold': 'bold',
                    'dim': 'dim',
                }
                
                # Parse [color]...[/color] tags
                pattern = r'\[/?([a-zA-Z0-9_]+)\]'
                stack = []
                result = []
                i = 0
                
                while i < len(text):
                    match = re.search(pattern, text[i:])
                    if not match:
                        result.append(text[i:])
                        break
                    
                    # Add text before tag
                    if match.start() > 0:
                        result.append(text[i:i+match.start()])
                    
                    tag = match.group(1)
                    is_closing = tag.startswith('/')
                    tag_name = tag[1:] if is_closing else tag
                    
                    if is_closing and stack:
                        stack.pop()
                        result.append('</span>')
                    elif not is_closing:
                        if tag_name in color_map:
                            styles = []
                            if tag_name in ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']:
                                styles.append(f'color:{color_map[tag_name]}')
                                if tag_name != 'white':
                                    styles.append(f'text-shadow:0 0 6px {color_map[tag_name]}')
                            elif tag_name == 'bold':
                                styles.append('font-weight:bold')
                            elif tag_name == 'dim':
                                styles.append('opacity:0.7')
                                styles.append('color:#888888')
                            result.append(f'<span style="{";".join(styles)}">')
                            stack.append(tag_name)
                    
                    i += match.end()
                
                # Close any remaining tags
                while stack:
                    stack.pop()
                    result.append('</span>')
                
                return ''.join(result)
            
            # Parse the banner
            parsed_html = parse_banner_rich(raw_banner)
            
            # Also handle ASCII art characters with styling
            ascii_chars = ['─', '│', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼', '╭', '╮', '╯', '╰', '╱', '╲']
            for ch in ascii_chars:
                parsed_html = parsed_html.replace(ch, f'<span style="color:#50fa7b;">{ch}</span>')
            
            # Current font settings
            current_font = self.console_output.font()
            banner_font = QFont("DejaVu Sans Mono", 9)
            self.console_output.setFont(banner_font)
            
            # Insert parsed banner
            cursor = self.console_output.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertHtml(f"""
            <div style="font-family:'DejaVu Sans Mono','Courier New',monospace; line-height:1.3; white-space:pre;">
                {parsed_html}
            </div>
            """)
            cursor.insertText("\n\n")
            
            self.console_output.setFont(current_font)
            
            self.append_output("LazyFramework GUI v2.6")
            self.append_output("Type 'help' or click modules to start")
            self.append_output("Auto Tor IP rotation enabled (every 5 minutes)")
            
        except Exception as e:
            self.append_output(f"[red]Banner error: {e}[/]")

    def on_session_killed(self, session_id):
        self.append_output(f"[dim]Network map updating...[/]")
        if hasattr(self, "network_map_widget"):
            QTimer.singleShot(100, lambda: self.network_map_widget.refresh_map())

    def on_session_connected(self, session_data):
        """
        Handler untuk signal session_connected
        Dipanggil saat session baru terhubung
        """
        session_id = session_data.get('id', 'unknown')
        hostname = session_data.get('hostname', 'unknown')
        os_type = session_data.get('os', 'unknown')
        ip = session_data.get('rhost', '?')
        port = session_data.get('rport', '?')
        
        # ===== CEK APAKAH SESSION SUDAH ADA =====
        if session_id in self.sessions:
            self.append_output(f"[dim]Session {session_id} already exists, updating...[/]")
            self.sessions[session_id]['os'] = os_type
            self.sessions[session_id]['hostname'] = hostname
            self.sessions[session_id]['ip'] = ip
            self.sessions[session_id]['port'] = port
            self.update_sessions_ui()
            return
        
        # ===== BUAT SESSION DATA =====
        session_data_gui = {
            'id': session_id,
            'type': 'reverse_tcp',
            'ip': ip,
            'port': port,
            'lhost': session_data.get('lhost', '0.0.0.0'),
            'lport': session_data.get('lport', '4444'),
            'os': os_type,
            'hostname': hostname if hostname != 'unknown' else f'target_{session_id[-4:]}',
            'status': 'alive',
            'created': time.strftime("%H:%M:%S"),
            'handler': session_data.get('handler', None),
            'socket': session_data.get('socket', None),
            'output': f"[*] Session {session_id} connected\nHost: {hostname} ({os_type})\nIP: {ip}:{port}\n\n"
        }
        
        # ===== SIMPAN KE SESSIONS =====
        with self.session_lock:
            self.sessions[session_id] = session_data_gui
        
        # ===== UPDATE UI =====
        self.update_sessions_ui()
        self.update_session_info()
        
        # ===== REFRESH NETWORK MAP =====
        if hasattr(self, "network_map_widget"):
            QTimer.singleShot(500, self.network_map_widget.refresh_map)
        
        # ===== BUAT SESSION TAB =====
        self.create_session_tab(session_id, session_data_gui)
        
        # ===== AUTO-SELECT SESSION TERBARU =====
        self.selected_session_id = session_id
        self.active_session_id = session_id
        
        # ===== ❌ HAPUS INI: JANGAN PINDAH KE SESSIONS TAB =====
        # if hasattr(self, "main_tabs"):
        #     self.main_tabs.setCurrentIndex(4)  # HAPUS INI
        
        # ===== FOCUS COMMAND INPUT DI SESSIONS TAB TETAP =====
        # Tapi jangan pindah tab, hanya fokus ke input jika user sedang di sessions tab
        if hasattr(self, "session_cmd_input"):
            # Cek apakah user sedang di sessions tab
            if hasattr(self, "main_tabs") and self.main_tabs.currentIndex() == 4:
                self.session_cmd_input.setFocus()
        
        # ===== NOTIFIKASI =====
        icon = OSIconManager.get_icon(os_type)
        self.show_cyber_toast(
            f"{icon} New session connected!\n{hostname} ({os_type}) @ {ip}:{port}",
            title=f"Session #{len(self.sessions)} Connected",
            duration_ms=4000,
            level="success"
        )
        
        self.append_output(f"[bold green][+] Session {session_id} connected![/]")
        self.append_output(f"[dim]  {icon} Host: {hostname} ({os_type}) @ {ip}:{port}[/]")
        self.append_output(f"[dim]  Total sessions: {len(self.sessions)}[/]")

    def on_module_selected(self, item):
        if not item:
            return
        module_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not module_path:
            return
        self.load_module_info_to_main_tab(module_path)
        self._update_toolbar_module(module_path, active=False)

    def show_cyber_toast(self, message: str, title: str = "", duration_ms: int = 5500,
                         level: str = "info", width: int = 420, icon: str = None):
        toast = CyberpunkToast(
            self,
            title=title or "LAZYFRAMEWORK",
            message=message,
            duration=duration_ms,
            level=level,
            width=width,
            icon=icon,
        )
        toast.show()

    def stop_module(self):
        if not hasattr(self, "module_runner") or self.module_runner is None:
            return

        if not self.module_runner.isRunning():
            return

        self.append_output("[yellow]Stopping module…[/]")

        try:
            self.module_runner.stop()
        except Exception as e:
            self.append_output(f"[red]Stop error: {e}[/]")

        if (self.framework.loaded_module and
            "reverse_tcp" in str(self.framework.loaded_module).lower()):
            self.cleanup_reverse_tcp_sessions()

        self.run_btn.setEnabled(True)
        self.run_btn.setText("START")
        self.run_btn.setProperty("action", "run")

        self.append_output("[green]✓ Module stopped successfully[/]")

    def cleanup_reverse_tcp_sessions(self):
        self.append_output("[yellow][*] Cleaning up reverse TCP sessions...[/]")

        try:
            if hasattr(self, "reverse_listener") and self.reverse_listener is not None:
                self.reverse_listener.running = False
                if (hasattr(self.reverse_listener, "server_socket") and
                    self.reverse_listener.server_socket):
                    try:
                        self.reverse_listener.server_socket.close()
                    except:
                        pass
                self.reverse_listener = None

            with self.listener_lock:
                self.active_listeners.clear()
                self.append_output("[green]✓ Active listeners cleared[/]")

            with self.session_lock:
                for sess in list(self.sessions.values()):
                    if sess.get("socket"):
                        try:
                            sess["socket"].close()
                        except:
                            pass
                self.sessions.clear()

            try:
                if (self.framework.loaded_module and
                    hasattr(self.framework.loaded_module, "module") and
                    hasattr(self.framework.loaded_module.module, "SESSIONS")):
                    mod = self.framework.loaded_module.module
                    with getattr(mod, "SESSIONS_LOCK", _rtcp_mod.SESSIONS_LOCK):
                        mod.SESSIONS.clear()
                else:
                    with _rtcp_mod.SESSIONS_LOCK:
                        _rtcp_mod.SESSIONS.clear()
            except:
                pass

            self.update_sessions_ui()
            self.update_session_info()
            if hasattr(self, "network_map_widget"):
                self.network_map_widget.refresh_map()

            self.append_output("[green]✓ Reverse TCP cleanup completed[/]")

        except Exception as e:
            self.append_output(f"[red]Cleanup error: {e}[/]")

    def handle_run_stop(self):
        action = self.run_btn.property("action")

        if action == "run":
            self.run_module()
            self.run_btn.setText("STOP")
            self.run_btn.setProperty("action", "stop")
        elif action == "stop":
            self.stop_module()

    def open_module_in_tab(self, module_path: str):
        from widgets.module_tab import ModuleTab

        if module_path not in self.framework.modules:
            self.append_output(f"[red]Module tidak ditemukan: {module_path}[/]")
            return

        for i in range(self.module_tabs.count()):
            widget = self.module_tabs.widget(i)
            if isinstance(widget, ModuleTab) and widget.module_name == module_path:
                self.module_tabs.setCurrentIndex(i)
                return

        try:
            import importlib.util

            module_file = self.framework.modules[module_path]
            spec = importlib.util.spec_from_file_location(
                module_path.replace("/", "_"), module_file
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            from bin.console import ModuleInstance
            mod_instance = ModuleInstance(module_path, mod)

            if hasattr(mod, "OPTIONS"):
                for k, meta in mod.OPTIONS.items():
                    if "default" in meta:
                        mod_instance.options[k] = meta["default"]

            tab = ModuleTab(
                framework=self.framework,
                module_name=module_path,
                module_instance=mod_instance,
                parent=self.module_tabs,
            )

            tab.output_to_main_gui.connect(
                self.append_output,
                Qt.ConnectionType.QueuedConnection
            )

            if "reverse_tcp" in module_path.lower():
                tab._safe_append.connect(
                    self._parse_reverse_tcp_output,
                    Qt.ConnectionType.QueuedConnection
                )

            self._populate_module_tab_options(tab, mod_instance)

            short_name = module_path.split("/")[-1]
            idx = self.module_tabs.addTab(tab, f"⚡ {short_name}")
            self.module_tabs.setCurrentIndex(idx)

        except Exception as e:
            import traceback
            self.append_output(f"[red]{traceback.format_exc()}[/]")

    def _populate_module_tab_options(self, tab: "ModuleTab", mod_instance):
        from PyQt6.QtWidgets import QLineEdit, QLabel, QComboBox

        INPUT_STYLE = """
            QLineEdit, QComboBox {
                background: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                border-radius: 2px;
                padding: 3px 6px;
                font-size: 10px;
                min-height: 22px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #007acc;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #858585;
                width: 0;
                height: 0;
                margin-right: 4px;
            }
            QComboBox QAbstractItemView {
                background: #2d2d2d;
                color: #cccccc;
                border: 1px solid #007acc;
                selection-background-color: #007acc;
                selection-color: #ffffff;
                outline: none;
            }
        """

        LABEL_STYLE = """
            QLabel {
                color: #858585;
                font-size: 10px;
            }
        """

        try:
            options = getattr(mod_instance, "options", {})
            if not options:
                options = getattr(mod_instance.module, "OPTIONS", {})

            for key, meta in options.items():
                label = QLabel(key)
                label.setStyleSheet(LABEL_STYLE)

                current_val = ""
                choices = None
                if isinstance(meta, dict):
                    current_val = str(meta.get("value", "") or meta.get("default", ""))
                    choices = meta.get("choices")
                    if isinstance(meta, dict) and meta.get("description"):
                        label.setToolTip(meta["description"])
                elif isinstance(meta, str):
                    current_val = meta

                def make_updater(k):
                    def updater(val):
                        if k in mod_instance.options:
                            mod_instance.options[k] = val
                        elif hasattr(mod_instance.module, "OPTIONS"):
                            if k in mod_instance.module.OPTIONS:
                                if isinstance(mod_instance.module.OPTIONS[k], dict):
                                    mod_instance.module.OPTIONS[k]["value"] = val
                    return updater

                if choices:
                    field = QComboBox()
                    field.setStyleSheet(INPUT_STYLE)
                    for choice in choices:
                        field.addItem(str(choice))
                    idx = field.findText(current_val)
                    if idx >= 0:
                        field.setCurrentIndex(idx)
                    field.currentTextChanged.connect(make_updater(key))
                else:
                    field = QLineEdit()
                    field.setStyleSheet(INPUT_STYLE)
                    field.setText(current_val)
                    if isinstance(meta, dict) and meta.get("description"):
                        field.setPlaceholderText(meta["description"])
                    field.textChanged.connect(make_updater(key))

                tab.options_layout.addRow(label, field)
                tab.option_widgets[key] = field

        except Exception as e:
            print(f"[ERROR] _populate_module_tab_options: {e}")

    def _close_module_tab(self, index: int):
        try:
            widget = self.module_tabs.widget(index)
            if isinstance(widget, ModuleTab):
                if (hasattr(widget, "module_runner") and
                    widget.module_runner and
                    widget.module_runner.isRunning()):
                    widget.module_runner.stop()
                    widget.module_runner.wait(800)

                if hasattr(widget, "_request_close"):
                    widget._request_close()
                else:
                    self.module_tabs.removeTab(index)
                    widget.deleteLater()
            else:
                self.module_tabs.removeTab(index)
                if widget:
                    widget.deleteLater()

            self.append_output(f"[dim]✓ Tab closed[/]")

        except Exception as e:
            self.append_output(f"[red]Error closing tab: {e}[/]")
            import traceback
            self.append_output(f"[red]{traceback.format_exc()}[/]")
            try:
                self.module_tabs.removeTab(index)
            except:
                pass

    def ensure_monospace_fonts(self):
        if not hasattr(self, "console_output"):
            return

        try:
            monospace_fonts = [
                "DejaVu Sans Mono",
                "Source Code Pro",
                "Consolas",
                "Monaco",
                "Courier New",
                "Monospace",
            ]

            available_font = "Courier New"
            for font in monospace_fonts:
                if QFont(font).exactMatch():
                    available_font = font
                    break

            base_font = QFont(available_font, 10)

            self.console_output.setFont(base_font)
            self.module_detail_info.setFont(base_font)
            self.session_output.setFont(base_font)

            if hasattr(self, "session_info"):
                self.session_info.setFont(base_font)

            self.module_info.setFont(QFont(available_font, 9))

            if hasattr(self, "module_tree"):
                tree_font = QFont(available_font, 10)

                def _set_tree_font(node):
                    node.setFont(0, tree_font)
                    for j in range(node.childCount()):
                        _set_tree_font(node.child(j))

                root_node = self.module_tree.invisibleRootItem()
                for i in range(root_node.childCount()):
                    _set_tree_font(root_node.child(i))

            if hasattr(self, "option_widgets"):
                for widget in self.option_widgets.values():
                    if isinstance(widget, (QLineEdit, QTextEdit)):
                        widget.setFont(base_font)

            if hasattr(self, "session_cmd_input"):
                self.session_cmd_input.setFont(base_font)

            if hasattr(self, "search_input"):
                self.search_input.setFont(base_font)

            if hasattr(self, "url_bar") and self.url_bar:
                self.url_bar.setFont(base_font)

            return available_font

        except Exception as e:
            return "Courier New"

    def show_splash_screen(self):
        splash = QSplashScreen()
        splash.setFixedSize(900, 650)
        splash.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        splash.setStyleSheet("""
            QSplashScreen {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0a0a, stop:0.3 #0d0d0d, stop:0.7 #1a0a0a, stop:1 #0a0a0a);
                border: 1px solid #2a0a0a;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(splash)
        layout.setContentsMargins(50, 50, 50, 40)
        layout.setSpacing(20)

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setSpacing(25)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        glow_top = QFrame()
        glow_top.setFixedHeight(2)
        glow_top.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent,
                    stop:0.3 #ff2222,
                    stop:0.5 #ff4444,
                    stop:0.7 #ff2222,
                    stop:1 transparent);
            }
        """)
        center_layout.addWidget(glow_top)

        bracket_widget = QWidget()
        bracket_layout = QHBoxLayout(bracket_widget)
        bracket_layout.setSpacing(0)
        bracket_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_bracket = QLabel("[")
        left_bracket.setStyleSheet("""
            QLabel {
                color: #ff2222;
                font-size: 52px;
                font-weight: 100;
                font-family: 'Hack', 'Consolas', monospace;
                padding-right: 8px;
            }
        """)

        app_name = QLabel("LAZYFRAMEWORK")
        app_name.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 42px;
                font-weight: 600;
                font-family: 'Hack', 'Consolas', monospace;
                letter-spacing: 6px;
            }
        """)

        right_bracket = QLabel("]")
        right_bracket.setStyleSheet("""
            QLabel {
                color: #ff2222;
                font-size: 52px;
                font-weight: 100;
                font-family: 'Hack', 'Consolas', monospace;
                padding-left: 8px;
            }
        """)

        bracket_layout.addWidget(left_bracket)
        bracket_layout.addWidget(app_name)
        bracket_layout.addWidget(right_bracket)
        center_layout.addWidget(bracket_widget)

        subtitle = QLabel("⧩  ADVANCED SECURITY TESTING FRAMEWORK  ⧩")
        subtitle.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 13px;
                font-family: 'Hack', 'Consolas', monospace;
                letter-spacing: 4px;
                font-weight: 300;
            }
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(subtitle)

        line_frame = QFrame()
        line_frame.setFixedHeight(1)
        line_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent,
                    stop:0.3 #441111,
                    stop:0.5 #882222,
                    stop:0.7 #441111,
                    stop:1 transparent);
            }
        """)
        center_layout.addWidget(line_frame)

        info_widget = QWidget()
        info_layout = QHBoxLayout(info_widget)
        info_layout.setSpacing(30)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version = QLabel("v2.6.0")
        version.setStyleSheet("""
            QLabel {
                color: #555555;
                font-size: 12px;
                font-family: 'Hack', 'Consolas', monospace;
                font-weight: bold;
            }
        """)

        status_dot = QLabel("●")
        status_dot.setStyleSheet("""
            QLabel {
                color: #44ff44;
                font-size: 10px;
            }
        """)

        status_text = QLabel("SYSTEM ONLINE")
        status_text.setStyleSheet("""
            QLabel {
                color: #44ff44;
                font-size: 11px;
                font-family: 'Hack', 'Consolas', monospace;
                letter-spacing: 2px;
                font-weight: bold;
            }
        """)

        info_layout.addWidget(version)
        info_layout.addWidget(status_dot)
        info_layout.addWidget(status_text)
        center_layout.addWidget(info_widget)

        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setSpacing(12)

        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setFixedHeight(4)
        progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1a1a1a;
                border: none;
                border-radius: 2px;
                text-align: center;
                color: transparent;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff0000,
                    stop:0.5 #ff3333,
                    stop:1 #ff0000);
                border-radius: 2px;
            }
        """)
        progress_layout.addWidget(progress_bar)

        self.status_label = QLabel("⟳ Initializing core modules...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 12px;
                font-family: 'Hack', 'Consolas', monospace;
                letter-spacing: 1px;
            }
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.status_label)

        self.percentage_label = QLabel("0%")
        self.percentage_label.setStyleSheet("""
            QLabel {
                color: #ff3333;
                font-size: 13px;
                font-family: 'Hack', 'Consolas', monospace;
                font-weight: bold;
            }
        """)
        self.percentage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.percentage_label)

        center_layout.addWidget(progress_widget)

        glow_bottom = QFrame()
        glow_bottom.setFixedHeight(2)
        glow_bottom.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent,
                    stop:0.3 #ff2222,
                    stop:0.5 #ff4444,
                    stop:0.7 #ff2222,
                    stop:1 transparent);
            }
        """)
        center_layout.addWidget(glow_bottom)

        footer_widget = QWidget()
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        copyright_text = QLabel("© 2024 LAZYFRAMEWORK SECURITY TEAM  •  PROTECT & SERVE")
        copyright_text.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 10px;
                font-family: 'Hack', 'Consolas', monospace;
                letter-spacing: 2px;
            }
        """)
        footer_layout.addWidget(copyright_text)

        layout.addWidget(center_widget)
        layout.addStretch()
        layout.addWidget(footer_widget)

        screen_geo = QApplication.primaryScreen().availableGeometry()
        splash_geo = splash.frameGeometry()
        splash.move(
            (screen_geo.width() - splash_geo.width()) // 2,
            (screen_geo.height() - splash_geo.height()) // 2,
        )

        splash.show()

        loading_steps = [
            (5, "⟳ Initializing core modules..."),
            (15, "⟳ Loading security protocols..."),
            (25, "⟳ Establishing secure channels..."),
            (35, "⟳ Loading module database..."),
            (45, "⟳ Initializing user interface..."),
            (55, "⟳ Setting up proxy configurations..."),
            (65, "⟳ Loading session manager..."),
            (75, "⟳ Initializing browser engine..."),
            (85, "⟳ Starting security services..."),
            (92, "⟳ Finalizing setup..."),
            (98, "⟳ Ready..."),
            (100, "▶ SYSTEM ONLINE - READY"),
        ]

        for progress, status in loading_steps:
            progress_bar.setValue(progress)
            self.percentage_label.setText(f"{progress}%")
            self.status_label.setText(status)

            if progress == 100:
                self.status_label.setStyleSheet("""
                    QLabel {
                        color: #44ff44;
                        font-size: 12px;
                        font-family: 'Hack', 'Consolas', monospace;
                        letter-spacing: 2px;
                        font-weight: bold;
                    }
                """)
                status_text.setText("● SYSTEM ONLINE")
                status_text.setStyleSheet("""
                    QLabel {
                        color: #44ff44;
                        font-size: 11px;
                        font-family: 'Hack', 'Consolas', monospace;
                        letter-spacing: 2px;
                        font-weight: bold;
                    }
                """)

            QApplication.processEvents()
            time.sleep(0.40)

        time.sleep(0.60)
        splash.close()

    def set_active_module(self, module_name):
        self.active_module = module_name
        self.update_title()
        self._update_toolbar_module(module_name, active=bool(module_name))

    def _update_toolbar_module(self, module_path: str, active: bool = True):
        if not hasattr(self, "current_module_label"):
            return
        if module_path:
            short = module_path.split("/")[-1]
            dot_color = "#4ec9b0" if active else "#007acc"
            label_style = (
                "color: #ffffff; font-size: 10pt; font-weight: 600;"
                if active
                else "color: #9cdcfe; font-size: 10pt; font-weight: 500;"
            )
            self.current_module_label.setText(short)
            self.current_module_label.setStyleSheet(label_style)
            if hasattr(self, "_toolbar_dot"):
                self._toolbar_dot.setStyleSheet(
                    f"color: {dot_color}; font-size: 10px; margin-right: 2px;"
                )
            if hasattr(self, "run_btn"):
                self.run_btn.setEnabled(active)
            if hasattr(self, "back_btn"):
                self.back_btn.setEnabled(active)
        else:
            self.current_module_label.setText("No module loaded")
            self.current_module_label.setStyleSheet(
                "color: #555555; font-size: 10pt; font-weight: 500;"
            )
            if hasattr(self, "_toolbar_dot"):
                self._toolbar_dot.setStyleSheet(
                    "color: #444; font-size: 10px; margin-right: 2px;"
                )
            if hasattr(self, "run_btn"):
                self.run_btn.setEnabled(False)
            if hasattr(self, "back_btn"):
                self.back_btn.setEnabled(False)

    def center_title(self, text):
        padding = " " * ((150 - len(text)) // 2)
        return padding + text + padding

    def update_title(self):
        title = "Lazy Framework GUI"

        if self.active_module:
            title = f"{title}   |   {self.active_module}"

        self.setWindowTitle(self.center_title(title))

    def init_ui(self):
        self.active_module = ""
        self.update_title()
        self.setGeometry(100, 50, 1800, 1000)

        saved_font = self.framework.session.get("font", "DejaVu Sans Mono Bold")
        saved_size = self.framework.session.get("font_size", 12)
        default_font = QFont(saved_font, saved_size)
        self.setFont(default_font)

        self.create_menu_bar()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        left_sidebar = self.create_left_sidebar()
        layout.addWidget(left_sidebar, 1)

        main_content = self.create_main_content()
        layout.addWidget(main_content, 3)

        right_sidebar = self.create_right_sidebar()
        layout.addWidget(right_sidebar, 1)

        QTimer.singleShot(100, self.load_all_modules)
        font = QFont("DejaVu Sans Mono", 10)
        self.console_output.setFont(font)

        font_family = "DejaVu Sans Mono, Source Code Pro, Consolas, Monaco, Courier New, monospace"
        self.console_output.setStyleSheet(f"font-family: {font_family};")

        shortcuts = [
            ("Ctrl+Q", self.close),
            ("Ctrl+X", self.clear_console),
            ("F5", self.refresh_modules),
            ("Ctrl+P", self.show_proxy_settings),
            ("Ctrl+E", self.enable_proxy),
            ("Ctrl+A", self.open_ai_payload_dialog),
        ]

        for key, callback in shortcuts:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)

    def auto_rotate_proxy(self):
        mode = self.framework.session.get("proxy_mode", "Disabled")

        if mode == "Tor":
            self.rotate_tor_ip()
        elif mode == "FileProxy":
            self.rotate_custom_proxy()

    def rotate_custom_proxy(self):
        if not self.custom_proxies:
            self.append_output("[yellow]No custom proxies loaded[/]")
            return

        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.custom_proxies)
        self.current_proxy = self.custom_proxies[self.current_proxy_index]
        p = self.current_proxy

        self.append_output(
            f"[cyan]Switched to proxy → {p['server']}:{p['port']} ({p['type']})[/]"
        )
        self.update_session_info()
        self.append_output(
            f"[cyan]Browser proxy updated via PAC → {p['server']}:{p['port']}[/]"
        )

    def create_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("View")
        refresh_action = QAction("Refresh Modules", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_modules)
        view_menu.addAction(refresh_action)

        tools_menu = menubar.addMenu("Tools")
        clear_action = QAction("Clear Console", self)
        clear_action.setShortcut("Ctrl+X")
        clear_action.triggered.connect(self.clear_console)
        tools_menu.addAction(clear_action)

        settings_menu = menubar.addMenu("Settings")
        theme_menu = settings_menu.addMenu("Theme")

        available_themes = self.theme_manager.get_available_themes()
        current_theme_display = None

        for display_name, filename in self.theme_manager.theme_map.items():
            if filename == self.theme_manager.current_theme:
                current_theme_display = display_name
                break

        for display_name in available_themes:
            theme_action = QAction(display_name, self)
            theme_action.setCheckable(True)
            if display_name == current_theme_display:
                theme_action.setChecked(True)
            theme_action.triggered.connect(
                lambda checked, name=display_name: self.switch_theme(name)
            )
            theme_menu.addAction(theme_action)

        theme_menu.addSeparator()
        reload_themes_action = QAction("⟳ Reload Themes", self)
        reload_themes_action.triggered.connect(self.reload_themes)
        theme_menu.addAction(reload_themes_action)

        font_action = QAction("Change Font", self)
        font_action.triggered.connect(self.change_font)
        settings_menu.addAction(font_action)

        proxy_menu = menubar.addMenu("Proxy")
        proxy_settings = QAction("Proxy Settings", self)
        proxy_settings.setShortcut("Ctrl+P")
        proxy_settings.triggered.connect(self.show_proxy_settings)
        proxy_menu.addAction(proxy_settings)

        proxy_menu.addSeparator()
        enable_proxy = QAction("Enable Proxy", self)
        enable_proxy.setShortcut("Ctrl+E")
        enable_proxy.triggered.connect(self.enable_proxy)
        proxy_menu.addAction(enable_proxy)

        disable_proxy = QAction("Disable Proxy", self)
        disable_proxy.triggered.connect(self.disable_proxy)
        proxy_menu.addAction(disable_proxy)

        test_proxy = QAction("Test Proxy", self)
        test_proxy.triggered.connect(self.test_proxy_connection)
        proxy_menu.addAction(test_proxy)

        payload_menu = menubar.addMenu("Payloads")
        ai_payload_action = QAction("AI Payload Assistant", self)
        ai_payload_action.setShortcut("Ctrl+A")
        ai_payload_action.triggered.connect(self.open_ai_payload_dialog)
        payload_menu.addAction(ai_payload_action)

        payload_menu.addSeparator()
        ransomware_action = QAction("☠ Ransomware Builder", self)
        ransomware_action.triggered.connect(self.open_ransomware_builder)
        payload_menu.addAction(ransomware_action)

        c2_action = QAction("🖥 C2 Server", self)
        c2_action.triggered.connect(self.open_c2_server)
        payload_menu.addAction(c2_action)

    def open_ransomware_builder(self):
        try:
            from widgets.ransomware_dialog import RansomwareDialog
            dialog = RansomwareDialog(framework=self.framework, parent=self)
            dialog.show()
        except ImportError as e:
            self.append_output(f"[red]Error loading Ransomware Builder: {e}[/red]")
        except Exception as e:
            self.append_output(f"[red]Error: {e}[/red]")

    def open_c2_server(self):
        try:
            from widgets.c2_dialog import C2Dialog
            dialog = C2Dialog(framework=self.framework, parent=self)
            dialog.show()
        except ImportError as e:
            self.append_output(f"[red]Error loading C2 Server: {e}[/red]")
        except Exception as e:
            self.append_output(f"[red]Error: {e}[/red]")

    def open_ai_payload_dialog(self):
        try:
            from widgets.custom_payload_dialog import CustomPayloadDialog

            if not hasattr(self, 'ai_tab'):
                self.append_output("[red]AI Assistant not initialized[/]")
                return

            dialog = CustomPayloadDialog(
                framework=self.framework,
                gui=self,
                ai_assistant=self.ai_tab,
                parent=self
            )
            dialog.show()
        except ImportError as e:
            self.append_output(f"[red]Error loading Custom Payload Dialog: {e}[/]")
        except Exception as e:
            self.append_output(f"[red]Error: {e}[/]")
            import traceback
            self.append_output(f"[red]{traceback.format_exc()}[/]")

    def create_main_content(self):
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QWidget()
        toolbar.setFixedHeight(42)
        toolbar.setStyleSheet("""
            QWidget {
                border-bottom: 1px solid #3c3c3c;
            }
        """)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(10, 0, 10, 0)
        tb_layout.setSpacing(8)

        self._toolbar_dot = QLabel("●")
        self._toolbar_dot.setStyleSheet(
            "color: #555; font-size: 10px; margin-right: 2px;"
        )
        tb_layout.addWidget(self._toolbar_dot)

        self.current_module_label = QLabel("No module loaded")
        self.current_module_label.setStyleSheet(
            "color: #858585; font-size: 10pt; font-weight: 500;"
        )
        tb_layout.addWidget(self.current_module_label)

        tb_layout.addStretch()

        new_tab_btn = QPushButton("Multi Sessions")
        new_tab_btn.clicked.connect(self._open_new_session_tab)
        new_tab_btn.setFixedHeight(28)
        new_tab_btn.setMinimumWidth(80)
        new_tab_btn.setStyleSheet("""
            QPushButton {
                background: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                padding: 0 12px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: #3a3a3a;
                color: #ffffff;
            }
            QPushButton:pressed {
                background: #1a1a1a;
            }
        """)
        tb_layout.addWidget(new_tab_btn)

        self.run_btn = QPushButton("▶  Run")
        self.run_btn.setProperty("action", "run")
        self.run_btn.clicked.connect(self.handle_run_stop)
        self.run_btn.setEnabled(False)
        self.run_btn.setFixedHeight(28)
        self.run_btn.setMinimumWidth(80)
        self.run_btn.setStyleSheet("""
            QPushButton {
                color: #ffffff;
                border: none;
                border-radius: 3px;
                padding: 0 14px;
                font-size: 10pt;
                font-weight: 600;
            }
            QPushButton[action="run"] { background: #0e639c; }
            QPushButton[action="run"]:hover { background: #1177bb; }
            QPushButton:pressed { background: #0a4f7e; }
            QPushButton:disabled { background: #2d2d2d; color: #555; }
            QPushButton[action="stop"] { background: #a31515; }
            QPushButton[action="stop"]:hover { background: #c72e2e; }
        """)
        tb_layout.addWidget(self.run_btn)

        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(self.unload_module)
        self.back_btn.setEnabled(False)
        self.back_btn.setFixedHeight(28)
        self.back_btn.setMinimumWidth(60)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #858585;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                padding: 0 12px;
                font-size: 10pt;
            }
            QPushButton:hover  { background: #2d2d2d; color: #cccccc; }
            QPushButton:disabled { color: #444; border-color: #2c2c2c; }
        """)
        tb_layout.addWidget(self.back_btn)

        sep = QLabel("|")
        sep.setStyleSheet("color: #3c3c3c; font-size: 16px; padding: 0 2px;")
        tb_layout.addWidget(sep)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_console)
        clear_btn.setFixedHeight(28)
        clear_btn.setMinimumWidth(55)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #858585;
                border: none;
                border-radius: 3px;
                padding: 0 10px;
                font-size: 10pt;
            }
            QPushButton:hover { background: #2d2d2d; color: #cccccc; }
        """)
        tb_layout.addWidget(clear_btn)

        layout.addWidget(toolbar)

        self.main_tabs = QTabWidget()
        self.main_tabs.setDocumentMode(True)
        self.main_tabs.setTabsClosable(True)
        self.main_tabs.tabCloseRequested.connect(self._close_main_tab)
        

        # Console Tab
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Hack", 10))
        self.console_output.setAcceptRichText(True)
        self.main_tabs.addTab(self.console_output, "Console")

        # Options Tab
        self.options_widget = QWidget()
        self.options_layout = QFormLayout(self.options_widget)
        self.options_layout.setContentsMargins(10, 10, 10, 10)
        self.options_layout.setSpacing(8)
        self.options_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.options_scroll = QScrollArea()
        self.options_scroll.setWidgetResizable(True)
        self.options_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.options_scroll.setStyleSheet("""
            QScrollArea { border: none; background: #1e1e1e; }
            QScrollBar:vertical { background: #1e1e1e; width: 8px; }
            QScrollBar::handle:vertical { background: #424242; min-height: 24px; }
            QScrollBar::handle:vertical:hover { background: #686868; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        self.options_scroll.setWidget(self.options_widget)
        self.main_tabs.addTab(self.options_scroll, "Options")

        # Module Info Tab
        self.module_detail_info = QTextEdit()
        self.module_detail_info.setReadOnly(True)
        self.module_detail_info.setFont(QFont("DejaVu Sans Mono", 10))
        self.main_tabs.addTab(self.module_detail_info, "Info")

        # Sessions Tab
        self.session_tab = QWidget()
        self.session_layout = QVBoxLayout(self.session_tab)
        self.session_layout.setContentsMargins(12, 10, 12, 10)
        self.session_layout.setSpacing(8)

        session_header = QLabel("Sessions")
        session_header.setStyleSheet(
            "color: #cccccc; font-size: 11pt; font-weight: 600; padding-bottom: 4px;"
            "border-bottom: 1px solid #3c3c3c;"
        )
        self.session_layout.addWidget(session_header)

        self.session_list = QListWidget()
        self.session_list.itemClicked.connect(self.on_session_selected)
        self.session_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                color: #d4d4d4;
                font-size: 10pt;
                outline: none;
            }
            QListWidget::item { padding: 6px 8px; }
            QListWidget::item:selected { background: #094771; color: #ffffff; }
            QListWidget::item:hover { background: #2a2d2e; }
        """)
        self.session_layout.addWidget(self.session_list, 2)

        cmd_layout = QHBoxLayout()
        cmd_layout.setSpacing(6)
        self.session_cmd_input = QLineEdit()
        self.session_cmd_input.setPlaceholderText("Command for selected session…")
        self.session_cmd_input.returnPressed.connect(self.send_session_command)
        self.session_cmd_input.setStyleSheet("""
            QLineEdit {
                color: #d4d4d4;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 8px;
                font-family: 'DejaVu Sans Mono';
                font-size: 10pt;
            }
            QLineEdit:focus { border-color: #007acc; }
        """)
        cmd_layout.addWidget(self.session_cmd_input)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_session_command)
        send_btn.setFixedWidth(70)
        send_btn.setStyleSheet("""
            QPushButton {
                background: #0e639c; 
                color: white;
                border: none; border-radius: 3px;
                padding: 5px; font-size: 10pt;
            }
            QPushButton:hover { background: #1177bb; }
        """)
        cmd_layout.addWidget(send_btn)
        self.session_layout.addLayout(cmd_layout)

        self.session_output = QTextEdit()
        self.session_output.setReadOnly(True)
        self.session_output.setFont(QFont("DejaVu Sans Mono", 9))
        self.session_output.setStyleSheet("""
            QTextEdit {
                border: 1px solid #3c3c3c;
                border-radius: 3px; color: #d4d4d4; padding: 4px;
            }
        """)
        self.session_layout.addWidget(self.session_output, 3)

        sess_btn_layout = QHBoxLayout()
        sess_btn_layout.setSpacing(6)
        upgrade_btn = QPushButton("Upgrade Shell")
        upgrade_btn.clicked.connect(self.upgrade_session)
        upgrade_btn.setStyleSheet("""
            QPushButton {
                background: #2d2d2d; color: #cccccc;
                border: 1px solid #3c3c3c; border-radius: 3px; padding: 5px 10px;
            }
            QPushButton:hover { background: #3a3a3a; }
        """)
        sess_btn_layout.addWidget(upgrade_btn)

        kill_btn = QPushButton("Kill Session")
        kill_btn.setStyleSheet("""
            QPushButton {
                background: #6e1414; color: #ff8080;
                border: 1px solid #a31515; border-radius: 3px; padding: 5px 10px;
            }
            QPushButton:hover { background: #a31515; color: white; }
        """)
        kill_btn.clicked.connect(self.kill_selected_session)
        sess_btn_layout.addWidget(kill_btn)
        sess_btn_layout.addStretch()
        self.session_layout.addLayout(sess_btn_layout)

        self.main_tabs.addTab(self.session_tab, "Sessions")

        # Network Map Tab
        self.network_map_widget = NetworkMapWidget(self)
        self.main_tabs.addTab(self.network_map_widget, "Network Map")

        # AI Assistant Tab
        self.ai_tab = AIAssistantWidget(framework=self.framework)
        self.main_tabs.addTab(self.ai_tab, "AI Assistant")

        # Browser Tab
        browser_tab = QWidget()
        browser_tab_layout = QVBoxLayout(browser_tab)
        browser_tab_layout.setContentsMargins(0, 0, 0, 0)
        browser_tab_layout.setSpacing(0)

        control_widget = QWidget()
        control_widget.setFixedHeight(36)
        control_widget.setStyleSheet("""
            QWidget {
                background: #252526;
                border-bottom: 1px solid #3c3c3c;
            }
        """)
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(5, 2, 5, 2)
        control_layout.setSpacing(4)

        control_layout.addStretch()

        self.open_browser_btn = QPushButton("🌐 Open Browser")
        self.open_browser_btn.setFixedSize(130, 26)
        self.open_browser_btn.clicked.connect(self.open_browser_panel)
        self.open_browser_btn.setStyleSheet("""
            QPushButton {
                background: #0e639c;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #1177bb; }
            QPushButton:pressed { background: #0a4f7e; }
        """)
        control_layout.addWidget(self.open_browser_btn)

        self.close_browser_btn = QPushButton("✕ Hide")
        self.close_browser_btn.setFixedSize(75, 26)
        self.close_browser_btn.clicked.connect(self.close_browser_panel)
        self.close_browser_btn.setEnabled(False)
        self.close_browser_btn.setStyleSheet("""
            QPushButton {
                background: #a31515;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #c72e2e; }
            QPushButton:pressed { background: #8a0a0a; }
            QPushButton:disabled { background: #2d2d2d; color: #555; }
        """)
        control_layout.addWidget(self.close_browser_btn)

        browser_tab_layout.addWidget(control_widget)

        self.browser_placeholder = QLabel(
            "🌐 Browser is closed\n\nClick 'Open Browser' to start"
        )
        self.browser_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.browser_placeholder.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 13px;
                padding: 20px;
                background: #1e1e1e;
                font-family: 'DejaVu Sans Mono', monospace;
            }
        """)
        browser_tab_layout.addWidget(self.browser_placeholder)

        self.main_tabs.addTab(browser_tab, "🌐 Browser")

        protected_tabs = [
            "Console",
            "Options",
            "Info",
            "Sessions",
            "Network Map",
            "AI Assistant",
            "🌐 Browser",
        ]
        for i in range(self.main_tabs.count()):
            tab_text = self.main_tabs.tabText(i)
            clean_text = tab_text.lstrip("⚡● ").strip()
            if clean_text in protected_tabs:
                self.main_tabs.tabBar().setTabButton(
                    i, QTabBar.ButtonPosition.RightSide, None
                )

        self._protected_tab_count = self.main_tabs.count()

        layout.addWidget(self.main_tabs)

        self.module_tabs = self.main_tabs

        return main_widget

    def switch_theme(self, display_name):
        if display_name in self.theme_manager.theme_map:
            theme_filename = self.theme_manager.theme_map[display_name]
            self.theme_manager.load_theme(theme_filename)
            self.update_theme_menu_checks(display_name)

    def update_theme_menu_checks(self, active_display_name):
        for menu in self.menuBar().findChildren(QMenu):
            if menu.title() == "Settings":
                theme_menu = None
                for action in menu.actions():
                    if action.text() == "🎨 Theme" and action.menu():
                        theme_menu = action.menu()
                        break

                if theme_menu:
                    for action in theme_menu.actions():
                        if action.text() in self.theme_manager.theme_map:
                            action.setChecked(action.text() == active_display_name)
                break

    def reload_themes(self):
        self.theme_manager.theme_map = self.theme_manager._scan_themes()

    def _close_main_tab(self, index: int):
        protected = {
            "Console",
            "Options",
            "Info",
            "Sessions",
            "Network Map",
            "AI Assistant",
        }
        try:
            title = self.main_tabs.tabText(index)
            clean_title = title.lstrip("⚡● ").strip()
            if clean_title in protected:
                return
            widget = self.main_tabs.widget(index)
            if (hasattr(widget, "module_runner") and
                widget.module_runner and
                widget.module_runner.isRunning()):
                widget.module_runner.stop()
                widget.module_runner.wait(800)
            if hasattr(widget, "_request_close"):
                widget._request_close()
            else:
                self.main_tabs.removeTab(index)
                if widget:
                    widget.deleteLater()
        except Exception as e:
            try:
                self.main_tabs.removeTab(index)
            except:
                pass

    def interact_with_session(self, session_id):
        if not session_id:
            return

        if session_id.startswith("session_"):
            actual_id = session_id
        else:
            actual_id = (
                f"session_{session_id}"
                if not session_id.startswith("session_")
                else session_id
            )

        if actual_id in self.sessions:
            self.selected_session_id = actual_id
            self.active_session_id = actual_id

            self.update_sessions_ui()
            self.main_tabs.setCurrentIndex(4)

            session = self.sessions[actual_id]
            os_icons = {"linux": "🐧", "windows": "🪟", "macos": "🍎", "unknown": "💻"}
            icon = os_icons.get(session.get("os", "unknown"), "💻")
            self.append_output(
                f"[green]✓ Interacting with {icon} Session {actual_id}[/]"
            )
            self.append_output(
                f"[dim]IP: {session.get('ip', '?')}:{session.get('port', '?')}[/]"
            )

            self.session_cmd_input.setFocus()
        else:
            if session_id in self.sessions:
                self.selected_session_id = session_id
                self.active_session_id = session_id
                self.update_sessions_ui()
                self.main_tabs.setCurrentIndex(4)
                self.append_output(f"[green]✓ Interacting with Session {session_id}[/]")
                self.session_cmd_input.setFocus()
            else:
                self.append_output(f"[red]❌ Session {session_id} not found[/]")
                self.append_output(
                    f"[yellow]Available sessions: {list(self.sessions.keys())}[/]"
                )

    def create_right_sidebar(self):
        sidebar = QWidget()
        sidebar.setMaximumWidth(420)
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(6)
        layout.setContentsMargins(4, 4, 4, 4)

        session_group = QGroupBox("SESSION CONTROL")
        session_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #ff3333;
                margin-top: 8px;
                padding-top: 12px;
                border-radius: 4px;
                font-family: "Consolas", "Hack", monospace;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px;
                background-color: #000000;
                color: #ff3333;
                font-family: "Consolas", "Hack", monospace;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)
        session_layout = QVBoxLayout()
        session_layout.setSpacing(2)

        self.session_info = QTextEdit()
        self.session_info.setMinimumHeight(300)
        self.session_info.setReadOnly(True)
        self.session_info.setObjectName("session_info")
        self.session_info.setHtml("")
        session_layout.addWidget(self.session_info)
        session_group.setLayout(session_layout)
        layout.addWidget(session_group)

        context_group = QGroupBox("OUTPUT CONTEXT")
        context_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #ff3333;
                margin-top: 8px;
                padding-top: 12px;
                border-radius: 4px;
                font-family: "Consolas", "Hack", monospace;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px;
                background-color: #000000;
                color: #ff3333;
                font-family: "Consolas", "Hack", monospace;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)
        context_layout = QVBoxLayout()
        context_layout.setSpacing(4)

        self.sidebar_context_box = QTextEdit()
        self.sidebar_context_box.setPlaceholderText(
            "Output terminal masuk otomatis.\nAtau paste manual."
        )
        self.sidebar_context_box.setMaximumHeight(180)
        self.sidebar_context_box.setFont(QFont("Consolas", 10))
        self.sidebar_context_box.setStyleSheet("""
            QTextEdit {
                background-color: #050505;
                color: #88ff88;
                font-family: 'Consolas', 'Hack', monospace;
                font-size: 11px;
                border: 1px solid #330000;
                border-radius: 3px;
                padding: 6px;
                selection-background-color: #ff0000;
                selection-color: #ffffff;
            }
            QTextEdit:focus {
                border: 1px solid #ff0000;
            }
        """)
        context_layout.addWidget(self.sidebar_context_box)

        ctx_btn_layout = QHBoxLayout()
        ctx_btn_layout.setSpacing(6)

        analyze_btn = QPushButton("Analyze Output")
        analyze_btn.setStyleSheet("""
            QPushButton {
                background: #1a0000;
                color: #ff3333;
                border: 1px solid #ff0000;
                border-radius: 3px;
                padding: 4px 12px;
                font-family: "Consolas", "Hack", monospace;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2a0000;
                border-color: #ff4444;
                color: #ff6666;
            }
        """)
        analyze_btn.clicked.connect(self._analyze_sidebar_context)
        ctx_btn_layout.addWidget(analyze_btn)

        clear_ctx_btn = QPushButton("Clear")
        clear_ctx_btn.setFixedWidth(55)
        clear_ctx_btn.setStyleSheet("""
            QPushButton {
                background: #1a0000;
                color: #884444;
                border: 1px solid #440000;
                border-radius: 3px;
                padding: 4px 12px;
                font-family: "Consolas", "Hack", monospace;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #2a0000;
                border-color: #880000;
                color: #ff6666;
            }
        """)
        clear_ctx_btn.clicked.connect(self.sidebar_context_box.clear)
        ctx_btn_layout.addWidget(clear_ctx_btn)

        ctx_btn_layout.addStretch()
        context_layout.addLayout(ctx_btn_layout)

        context_group.setLayout(context_layout)
        layout.addWidget(context_group)

        actions_group = QGroupBox("QUICK ACTIONS")
        actions_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #ff3333;
                border: 1px solid #ff0000;
                margin-top: 8px;
                padding-top: 12px;
                border-radius: 4px;
                font-family: "Consolas", "Hack", monospace;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px;
                background-color: #000000;
                color: #ff3333;
                font-family: "Consolas", "Hack", monospace;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(4)

        quick_actions = [
            ("Scan Modules", "scan"),
            ("Show Banner", "show_banner"),
        ]

        for action_name, command in quick_actions:
            btn = QPushButton(action_name)
            btn.setStyleSheet("""
                QPushButton {
                    background: #000000;
                    color: #ff3333;
                    border: 1px solid #ff0000;
                    border-radius: 3px;
                    padding: 5px 12px;
                    font-family: "Consolas", "Hack", monospace;
                    font-size: 11px;
                    font-weight: bold;
                    text-align: left;
                }
                QPushButton:hover {
                    background: #1a0000;
                    color: #ff6666;
                    border-color: #ff4444;
                }
            """)
            btn.clicked.connect(lambda checked, cmd=command: self.quick_command(cmd))
            actions_layout.addWidget(btn)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        layout.addStretch()

        return sidebar

    def _analyze_sidebar_context(self):
        if not hasattr(self, "sidebar_context_box"):
            return

        ctx = self.sidebar_context_box.toPlainText().strip()
        if not ctx:
            self.append_output(
                "[yellow]Context is empty. Paste scan output first.[/yellow]"
            )
            return

        if hasattr(self, "ai_tab") and self.ai_tab.api_key_input.text().strip():
            ai_index = self.main_tabs.indexOf(self.ai_tab)
            if ai_index >= 0:
                self.main_tabs.setCurrentIndex(ai_index)

            self.ai_tab.send_message(
                "Analisis output berikut. Identifikasi service, versi, "
                "potensi vulnerability, dan rekomendasikan langkah selanjutnya:\n\n"
                + ctx
            )
        else:
            self.append_output(
                "[red]AI Assistant not connected. Please connect first.[/red]"
            )

    # ==================== BROWSER METHODS ====================

    def navigate_to_url(self):
        try:
            if not hasattr(self, "url_bar") or not self.url_bar:
                return

            url = self.url_bar.text().strip()
            if not url:
                return

            if url.startswith(("http://", "https://", "file://")):
                self.browser.setUrl(QUrl(url))
                return

            if "." in url and " " not in url:
                self.browser.setUrl(QUrl("https://" + url))
            else:
                self.browser.setUrl(
                    QUrl(f'https://www.google.com/search?q={url.replace(" ", "+")}')
                )

        except Exception as e:
            self.append_output(f"[red]Navigation error: {e}[/]")

    def create_left_sidebar(self):
        sidebar = QWidget()
        sidebar.setMaximumWidth(350)
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search modules...")
        self.search_input.textChanged.connect(self.search_modules)
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("🔍")
        search_btn.setFixedWidth(40)
        search_btn.clicked.connect(self.perform_search)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)

        categories_container = QWidget()
        categories_layout = QHBoxLayout(categories_container)
        categories_layout.setSpacing(6)
        categories_layout.setContentsMargins(4, 4, 4, 4)
        categories_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        categories = [
            ("All", "all", "#8be9fd", "📋"),
            ("Recon", "recon", "#8be9fd", "📡"),
            ("Scan", "scan", "#50fa7b", "🔍"),
            ("Exploit", "exploit", "#ff5555", "⚡"),
            ("Post", "post", "#f1fa8c", "🎯"),
            ("Privesc", "privesc", "#ffb86c", "⬆️"),
            ("Persist", "persistence", "#bd93f9", "🔒"),
            ("Lateral", "lateral", "#ff79c6", "🔄"),
            ("Web", "web", "#00ffff", "🌐"),
            ("Cloud", "cloud", "#ffffff", "☁️"),
            ("Mobile", "mobile", "#aaffaa", "📱"),
            ("Aux", "aux", "#888888", "🛠️"),
            ("Payloads", "payloads", "#bd93f9", "💣"),
            ("Evasion", "evasion", "#ffaa00", "👻"),
            ("Report", "report", "#4a90e2", "📊"),
        ]

        for name, cat_type, color, icon in categories:
            btn = QPushButton(f"{icon} {name}")
            btn.setProperty("category", cat_type)
            btn.setFixedHeight(28)
            btn.setMinimumWidth(70 if name != "All" else 55)
            btn.setStyleSheet(f"""
                QPushButton {{
                    color: #e0e0e0;
                    border: 1px solid #3c3c3c;
                    border-radius: 5px;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 4px 8px;
                }}
                QPushButton:hover {{
                    background: #3a3a3a;
                    border-color: {color};
                    color: {color};
                }}
                QPushButton:pressed {{
                    background: {color};
                    color: #000000;
                }}
            """)
            btn.clicked.connect(self.on_category_click)
            categories_layout.addWidget(btn)

        categories_scroll = QScrollArea()
        categories_scroll.setWidget(categories_container)
        categories_scroll.setWidgetResizable(True)
        categories_scroll.setFixedHeight(50)
        categories_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        categories_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        categories_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:horizontal {
                height: 5px;
                background: #1e1e1e;
                border-radius: 2px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #555555;
                border-radius: 2px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #777777;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
        """)

        layout.addWidget(categories_scroll)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.module_tree = QTreeWidget()
        self.module_tree.setHeaderHidden(True)
        self.module_tree.setColumnCount(1)
        self.module_tree.setIndentation(16)
        self.module_tree.setAnimated(True)
        self.module_tree.setRootIsDecorated(True)
        self.module_tree.setUniformRowHeights(False)

        self.module_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                font-family: "DejaVu Sans Mono", "Courier New", monospace;
                font-size: 10px;
                outline: none;
            }
            QTreeWidget::item {
                padding: 3px 4px;
                border-radius: 3px;
            }
            QTreeWidget::item:hover {
                background: #2a2a2e;
            }
            QTreeWidget::item:selected {
                background: #ff0022;
                color: #ffffff;
            }
        """)
        self.module_tree.itemDoubleClicked.connect(self.load_selected_module)
        self.module_tree.itemClicked.connect(self.on_module_selected)
        self.module_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.module_tree.customContextMenuRequested.connect(
            self.show_module_context_menu
        )
        self.module_tree.itemDoubleClicked.connect(self._on_module_tree_double_click)

        splitter.addWidget(self.module_tree)
        self.module_list = self.module_tree

        self.info_browser_tabs = QTabWidget()
        self.info_browser_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
            QTabBar::tab {
                color: #cccccc;
                padding: 5px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                color: #ffffff;
            }
        """)

        module_info_tab = QWidget()
        module_info_layout = QVBoxLayout(module_info_tab)
        module_info_layout.setContentsMargins(0, 0, 0, 0)

        self.module_info = QTextEdit()
        self.module_info.setReadOnly(True)
        self.module_info.setHtml("""
        <html>
        <head>
        <style>
            body { 
                color: #d4d4d4; 
                font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
                padding: 20px;
                line-height: 1.6;
                font-size: 14px;
            }
            h2 { 
                color: #ff0022; 
                font-size: 24px; 
                font-weight: 600;
                margin-bottom: 20px;
                border-bottom: 2px solid #50fa7b;
                padding-bottom: 10px;
            }
            h3 { 
                color: #8be9fd; 
                font-size: 18px; 
                font-weight: 600;
                margin: 25px 0 15px 0;
            }
            .card {
                background: #252525; 
                padding: 20px; 
                border-radius: 8px; 
                margin: 15px 0;
                border-left: 4px solid #6272a4;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }
            .tip-card {
                background: #1e2e1e; 
                border-left: 4px solid #50fa7b;
            }
            ul {
                margin: 10px 0;
                padding-left: 20px;
            }
            li {
                margin: 8px 0;
                padding-left: 5px;
            }
            b {
                color: #ffb86c;
                font-weight: 600;
            }
            .category {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 12px;
                margin-right: 8px;
            }
            .recon { background: #1e3a5c; color: #8be9fd; }
            .scan { background: #1e5c2e; color: #50fa7b; }
            .exploit { background: #5c1e1e; color: #ff5555; }
            .post { background: #5c4c1e; color: #f1fa8c; }
            .payloads { background: #3e1e5c; color: #bd93f9; }
        </style>
        </head>
        <body>
        <h2>LazyFramework GUI</h2>
        <div class="card">
            <h3>🚀 Quick Start Guide</h3>
            <ul>
                <li><b>Browse Modules:</b> Select from the list on the left</li>
                <li><b>Load Module:</b> Double-click the desired module</li>
                <li><b>Configure:</b> Set parameters in the "Options" tab</li>
                <li><b>Execute:</b> Click "START" to run the module</li>
                <li><b>Results:</b> View output in the "Console" tab</li>
            </ul>
        </div>
        <div class="card">
            <h3>🎯 Module Categories</h3>
            <ul>
                <li><span class="category recon">RECON</span> Information gathering & enumeration</li>
                <li><span class="category scan">SCAN</span> Network & service scanning</li>
                <li><span class="category exploit">EXPLOIT</span> Vulnerability exploitation</li>
                <li><span class="category post">POST</span> Post-exploitation operations</li>
                <li><span class="category payloads">PAYLOADS</span> Payload generation & delivery</li>
            </ul>
        </div>
        <div class="card tip-card">
            <h3>💡 Professional Tips</h3>
            <ul>
                <li>Use proxy settings for enhanced anonymity during scans</li>
                <li>Save session configurations for different projects</li>
                <li>Always verify module options before execution</li>
                <li>Monitor system resources during large-scale operations</li>
                <li>Utilize the integrated browser for manual testing</li>
            </ul>
        </div>
        <div class="card">
            <h3>🔧 Key Features</h3>
            <ul>
                <li><b>Real-time Output:</b> Live console output with syntax highlighting</li>
                <li><b>Integrated Browser:</b> Built-in web browser for manual testing</li>
                <li><b>Proxy Support:</b> Full proxy configuration with auto-rotation</li>
                <li><b>Session Management:</b> Save and restore your work sessions</li>
                <li><b>Module Library:</b> Extensive collection of security tools</li>
            </ul>
        </div>
        </body>
        </html>
        """)

        module_info_layout.addWidget(self.module_info)
        self.info_browser_tabs.addTab(module_info_tab, "Guides")

        splitter.addWidget(self.info_browser_tabs)
        splitter.setSizes([500, 400])

        layout.addWidget(splitter)

        return sidebar

    def _on_module_tree_double_click(self, item, column):
        module_path = item.data(0, Qt.ItemDataRole.UserRole)
        if module_path and module_path in self.framework.modules:
            self.open_module_in_tab(module_path)

    def show_module_context_menu(self, position):
        item = self.module_tree.itemAt(position)
        if not item:
            return

        module_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not module_path:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                color: #ffffff;
                border: 1px solid #555;
                padding: 5px;
            }
            QMenu::item {
                padding: 6px 25px;
                margin: 2px;
            }
        """)

        main_tab_action = QAction("📌 Open in Single Tab", self)
        main_tab_action.triggered.connect(
            lambda: self.load_module_to_main_tab(module_path)
        )
        menu.addAction(main_tab_action)

        new_tab_action = QAction("➕ Open in New Tab", self)
        new_tab_action.triggered.connect(lambda: self.open_module_in_tab(module_path))
        menu.addAction(new_tab_action)

        menu.addSeparator()

        info_action = QAction("ℹ️ Show Module Info", self)
        info_action.triggered.connect(lambda: self.show_module_info_only(module_path))
        menu.addAction(info_action)

        menu.exec(self.module_tree.viewport().mapToGlobal(position))

    def load_module_to_main_tab(self, module_path: str):
        try:
            args = [module_path]
            self.framework.cmd_use(args)

            if self.framework.loaded_module:
                self.current_module = self.framework.loaded_module.name
                self.current_module_label.setText(f"{self.current_module}")
                self.current_module_label.setStyleSheet(
                    "color: #50fa7b; font-weight: bold;"
                )
                self.run_btn.setEnabled(True)
                self.back_btn.setEnabled(True)
                self.load_module_options()
                self.show_module_info_in_tab()

                if hasattr(self, "ai_tab") and self.ai_tab.api_key_input.text().strip():
                    self.ai_tab.run_agent_mode(self.framework.loaded_module)

                self.main_tabs.setCurrentIndex(0)

        except Exception as e:
            self.append_output(f"[red]Error loading module: {e}[/]")

    def show_module_info_only(self, module_path: str):
        module_meta = self.framework.metadata.get(module_path, {})
        module_name = module_path.split("/")[-1]

        html = f"""
        <html>
        <head>
        <style>
            body {{ 
                background: #1e1e1e; 
                color: #d4d4d4; 
                font-family: monospace;
                padding: 15px;
            }}
            .name {{ color: #50fa7b; font-size: 16px; font-weight: bold; }}
            .desc {{ margin-top: 10px; padding: 10px; background: #252525; border-radius: 5px; }}
            .rank {{ color: #f1fa8c; }}
        </style>
        </head>
        <body>
            <div class="name">📦 {module_name}</div>
            <div><b>Path:</b> {module_path}</div>
            <div><b>Rank:</b> <span class="rank">{module_meta.get('rank', 'Normal')}</span></div>
            <div class="desc">{module_meta.get('description', 'No description')}</div>
        </body>
        </html>
        """

        self.module_detail_info.setHtml(html)
        self.main_tabs.setCurrentIndex(2)

    def open_browser_panel(self):
        if hasattr(self, "browser") and self.browser:
            self.browser.show()
            if hasattr(self, "browser_controls_widget"):
                self.browser_controls_widget.show()
            self.browser_placeholder.hide()
            self.open_browser_btn.setEnabled(False)
            self.close_browser_btn.setEnabled(True)
            self.update_browser_buttons()
            return

        try:
            self.browser_controls_widget = QWidget()
            control_layout = QHBoxLayout(self.browser_controls_widget)
            control_layout.setContentsMargins(0, 0, 0, 0)

            self.back_browser_btn = QPushButton("⬅")
            self.back_browser_btn.setFixedSize(28, 28)
            self.back_browser_btn.clicked.connect(self.browser_back)
            self.back_browser_btn.setStyleSheet("""
                QPushButton {
                    background: #2d2d2d;
                    color: #cccccc;
                    border: none;
                    border-radius: 3px;
                    font-size: 12px;
                }
                QPushButton:hover { background: #3a3a3a; }
            """)
            control_layout.addWidget(self.back_browser_btn)

            self.forward_browser_btn = QPushButton("⮕")
            self.forward_browser_btn.setFixedSize(28, 28)
            self.forward_browser_btn.clicked.connect(self.browser_forward)
            self.forward_browser_btn.setStyleSheet("""
                QPushButton {
                    background: #2d2d2d;
                    color: #cccccc;
                    border: none;
                    border-radius: 3px;
                    font-size: 12px;
                }
                QPushButton:hover { background: #3a3a3a; }
            """)
            control_layout.addWidget(self.forward_browser_btn)

            self.refresh_browser_btn = QPushButton("↻")
            self.refresh_browser_btn.setFixedSize(28, 28)
            self.refresh_browser_btn.clicked.connect(self.browser_refresh)
            self.refresh_browser_btn.setStyleSheet("""
                QPushButton {
                    background: #2d2d2d;
                    color: #cccccc;
                    border: none;
                    border-radius: 3px;
                    font-size: 14px;
                }
                QPushButton:hover { background: #3a3a3a; }
            """)
            control_layout.addWidget(self.refresh_browser_btn)

            self.url_bar = QLineEdit()
            self.url_bar.setPlaceholderText("Enter URL or search...")
            self.url_bar.returnPressed.connect(self.navigate_to_url)
            self.url_bar.setStyleSheet("""
                QLineEdit {
                    background: #2d2d2d;
                    color: #d4d4d4;
                    border: 1px solid #3c3c3c;
                    border-radius: 3px;
                    padding: 4px 8px;
                    font-family: 'DejaVu Sans Mono', monospace;
                    font-size: 11px;
                }
                QLineEdit:focus { border-color: #007acc; }
            """)
            control_layout.addWidget(self.url_bar, 4)

            self.browser = QWebEngineView()
            self.browser.setZoomFactor(1.0)

            settings = self.browser.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
            settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, False)
            settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, False)

            self.browser.urlChanged.connect(self.update_url_bar)
            self.browser.loadStarted.connect(self.on_load_started)
            self.browser.loadFinished.connect(self.on_load_finished)

            self.browser.setUrl(QUrl("https://www.google.com"))

            for i in range(self.main_tabs.count()):
                if self.main_tabs.tabText(i) == "🌐 Browser":
                    browser_tab = self.main_tabs.widget(i)
                    break
            else:
                browser_tab = self.main_tabs.widget(self.main_tabs.count() - 1)

            browser_tab_layout = browser_tab.layout()

            for i in reversed(range(browser_tab_layout.count())):
                item = browser_tab_layout.itemAt(i)
                if item and item.widget() == self.browser_placeholder:
                    browser_tab_layout.removeItem(item)
                    break

            browser_tab_layout.insertWidget(1, self.browser_controls_widget)
            browser_tab_layout.insertWidget(2, self.browser)

            self.browser_placeholder.hide()
            self.open_browser_btn.setEnabled(False)
            self.close_browser_btn.setEnabled(True)
            self.update_browser_buttons()

            if self.proxy_enabled and self.current_proxy:
                self.set_proxy(self.current_proxy)

        except Exception as e:
            self.append_output(f"[red]❌ Browser initialization failed: {e}[/red]")
            self.append_output("[yellow]⚠️ Browser functionality disabled[/yellow]")

            if hasattr(self, "browser"):
                try:
                    self.browser.deleteLater()
                    del self.browser
                except:
                    pass

            self.browser_placeholder.setText(
                "Browser unavailable due to system limitations"
            )
            self.browser_placeholder.setStyleSheet(
                "color: #ff5555; font-style: italic; padding: 40px;"
            )
            self.open_browser_btn.setEnabled(False)
            self.close_browser_btn.setEnabled(False)

    def set_browser_proxy(self, proxy_config):
        if not hasattr(self, "browser") or not self.browser:
            return

        try:
            from PyQt6.QtNetwork import QNetworkProxy

            proxy_type = proxy_config["type"].lower()
            server = proxy_config["server"]
            port = proxy_config["port"]

            if proxy_type.startswith("socks5"):
                qtype = QNetworkProxy.ProxyType.Socks5Proxy
            elif proxy_type.startswith("socks4"):
                qtype = QNetworkProxy.ProxyType.Socks4Proxy
            else:
                qtype = QNetworkProxy.ProxyType.HttpProxy

            qproxy = QNetworkProxy(qtype, server, port)
            QNetworkProxy.setApplicationProxy(qproxy)

            self.append_output(f"✓ Browser proxy applied: {server}:{port}")

        except Exception as e:
            self.append_output(f"✗ Browser proxy error: {e}")

    def set_proxy(self, proxy_config):
        try:
            self.current_proxy = proxy_config
            self.proxy_enabled = True
            self.apply_proxy_to_requests()
            self.set_browser_proxy(proxy_config)

            proxy_info = f"{proxy_config['server']}:{proxy_config['port']}"
            if proxy_config["type"] != "http":
                proxy_info += f" [{proxy_config['type'].upper()}]"
            self.append_output(f"✓ Proxy configured: {proxy_info}")
            self.append_output(f"Note: Proxy applied to requests + browser")

            self.update_proxy_status()

        except Exception as e:
            self.append_output(f"✗ Proxy error: {e}")

    def close_browser_panel(self):
        try:
            if not hasattr(self, "browser") or not self.browser:
                self.append_output("[dim]Browser is already hidden[/]")
                return

            self.browser.stop()
            self.browser.hide()
            if hasattr(self, "browser_controls_widget"):
                self.browser_controls_widget.hide()

            for i in range(self.main_tabs.count()):
                if self.main_tabs.tabText(i) == "🌐 Browser":
                    browser_tab = self.main_tabs.widget(i)
                    break
            else:
                browser_tab = self.main_tabs.widget(self.main_tabs.count() - 1)

            browser_layout = browser_tab.layout()

            placeholder_exists = False
            for j in range(browser_layout.count()):
                item = browser_layout.itemAt(j)
                if item and item.widget() == self.browser_placeholder:
                    placeholder_exists = True
                    break

            if not placeholder_exists:
                self.browser_placeholder.setStyleSheet("""
                    QLabel {
                        color: #666;
                        font-size: 13px;
                        padding: 10px;
                        background: #1e1e1e;
                        font-family: 'DejaVu Sans Mono', monospace;
                    }
                """)
                browser_layout.insertWidget(2, self.browser_placeholder)

            self.browser_placeholder.show()
            self.update_browser_buttons()

            browser_layout.setContentsMargins(0, 0, 0, 0)
            browser_layout.setSpacing(0)

        except Exception as e:
            self.append_output(f"[red]Error hiding browser: {e}[/]")
            try:
                self.browser_placeholder.show()
                self.update_browser_buttons()
            except:
                pass

    def update_browser_buttons(self):
        try:
            if hasattr(self, "browser") and self.browser:
                is_visible = self.browser.isVisible()
                self.open_browser_btn.setEnabled(not is_visible)
                self.close_browser_btn.setEnabled(is_visible)

                if is_visible:
                    self.close_browser_btn.setText("❌ Hide Browser")
                else:
                    self.close_browser_btn.setText("❌ Close Browser")
            else:
                self.open_browser_btn.setEnabled(True)
                self.close_browser_btn.setEnabled(False)
                self.close_browser_btn.setText("❌ Hide Browser")
        except Exception as e:
            self.open_browser_btn.setEnabled(True)
            self.close_browser_btn.setEnabled(False)

    def browser_back(self):
        try:
            if hasattr(self, "browser") and self.browser:
                self.browser.back()
        except Exception as e:
            self.append_output(f"[red]Browser back error: {e}[/]")

    def browser_forward(self):
        try:
            if hasattr(self, "browser") and self.browser:
                self.browser.forward()
        except Exception as e:
            self.append_output(f"[red]Browser forward error: {e}[/]")

    def browser_refresh(self):
        try:
            if hasattr(self, "browser") and self.browser:
                self.browser.reload()
        except Exception as e:
            self.append_output(f"[red]Browser refresh error: {e}[/]")

    def update_url_bar(self, url):
        try:
            if hasattr(self, "url_bar") and self.url_bar:
                self.url_bar.setText(url.toString())
        except Exception as e:
            pass

    def on_load_started(self):
        try:
            if hasattr(self, "url_bar") and self.url_bar:
                self.url_bar.setPlaceholderText("Loading...")
        except Exception as e:
            pass

    def on_load_finished(self, ok):
        try:
            if hasattr(self, "url_bar") and self.url_bar:
                if ok:
                    self.url_bar.setPlaceholderText("Enter URL or search...")
                else:
                    self.url_bar.setPlaceholderText("Failed to load page")
        except Exception as e:
            pass

    # ==================== PROXY METHODS ====================

    def show_proxy_settings(self):
        dialog = ProxySettingsDialog(self)
        dialog.exec()

    def enable_proxy(self):
        if not self.current_proxy:
            self.show_proxy_settings()
            return

        self.proxy_enabled = True
        self.apply_proxy_to_requests()

        try:
            if (self.current_proxy["server"] == "127.0.0.1" and
                str(self.current_proxy["port"]) == "9050"):
                from stem import Signal
                from stem.control import Controller

                with Controller.from_port(port=9051) as c:
                    c.authenticate()
                    c.signal(Signal.NEWNYM)
        except Exception as e:
            self.append_output(f"✗ Could not renew Tor IP automatically: {e}")

        self.update_proxy_status()

    def disable_proxy(self):
        self.proxy_enabled = False
        self.apply_proxy_to_requests()
        self.append_output("Proxy disabled")
        self.update_proxy_status()

    def apply_proxy_to_requests(self):
        if not self.current_proxy or not self.proxy_enabled:
            for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
                if var in os.environ:
                    del os.environ[var]
            return

        try:
            proxy_type = self.current_proxy["type"]
            server = self.current_proxy["server"]
            port = self.current_proxy["port"]

            proxy_url = f"{proxy_type}://{server}:{port}"

            os.environ["HTTP_PROXY"] = proxy_url
            os.environ["HTTPS_PROXY"] = proxy_url
            os.environ["http_proxy"] = proxy_url
            os.environ["https_proxy"] = proxy_url

        except Exception as e:
            self.append_output(f"System proxy error: {e}")

    def test_proxy_connection(self, proxy_config=None):
        config = proxy_config or self.current_proxy

        if not config:
            self.append_output("No proxy configured to test")
            return

        import socket
        import requests
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        try:
            s = socket.socket()
            s.settimeout(1)
            s.connect(("127.0.0.1", config["port"]))
        except Exception:
            try:
                s = socket.socket()
                s.settimeout(1)
                s.connect(("127.0.0.1", 9150))
                config["port"] = 9150
            except Exception:
                pass
        finally:
            s.close()

        proxy_scheme = config["type"]
        if proxy_scheme.startswith("socks5"):
            proxy_scheme = "socks5h"

        proxies = {
            "http": f"{proxy_scheme}://{config['server']}:{config['port']}",
            "https": f"{proxy_scheme}://{config['server']}:{config['port']}",
        }

        test_url = "http://api.ipify.org?format=json"
        try:
            response = requests.get(test_url, proxies=proxies, timeout=30, verify=False)
            if response.status_code == 200:
                ip_info = response.json()
                self.append_output(
                    f"✓ Proxy working! Your IP: {ip_info.get('ip', 'Unknown')}"
                )
                return True
            else:
                self.append_output(
                    f"✗ Proxy test failed (status {response.status_code})"
                )
                return False

        except requests.exceptions.ConnectTimeout:
            self.append_output(
                "✗ Proxy test failed: connection timed out (Tor may be slow)"
            )
            return False
        except requests.exceptions.ProxyError as e:
            self.append_output(f"✗ Proxy error: {e}")
            return False
        except Exception as e:
            self.append_output(f"✗ Proxy test failed: {e}")
            return False

    def start_tor_auto_rotate(self):
        from PyQt6.QtCore import QTimer

        self.tor_timer = QTimer(self)
        self.tor_timer.setInterval(300000)
        self.tor_timer.timeout.connect(self.rotate_tor_ip)
        self.tor_timer.start()

    def rotate_tor_ip(self):
        from stem import Signal
        from stem.control import Controller
        import requests

        old_ip = self.get_current_ip()

        for port in [9051, 9151]:
            try:
                with Controller.from_port(port=port) as c:
                    c.authenticate()
                    c.signal(Signal.NEWNYM)

                    QTimer.singleShot(
                        2500, lambda p=port, old=old_ip: self.check_new_ip(p, old)
                    )
                    return
            except Exception:
                continue

    def start_global_proxy_rotate(self):
        self.proxy_timer = QTimer()
        self.proxy_timer.timeout.connect(self.auto_rotate_proxy)
        self.proxy_timer.start(5 * 60 * 1000)

    def detect_tor_socks(self):
        import socket

        for port in [9050, 9150]:
            s = socket.socket()
            try:
                s.settimeout(0.5)
                s.connect(("127.0.0.1", port))
                s.close()
                return port
            except:
                pass
        return None

    def get_current_ip(self):
        import requests

        socks_port = self.detect_tor_socks()
        if socks_port is None:
            return "Unknown"

        try:
            s = requests.get(
                "https://check.torproject.org/api/ip",
                proxies={
                    "http": f"socks5h://127.0.0.1:{socks_port}",
                    "https": f"socks5h://127.0.0.1:{socks_port}",
                },
                timeout=10,
            ).json()

            return s.get("IP", "Unknown")

        except Exception:
            return "Unknown"

    def check_new_ip(self, port, old_ip):
        socks_port = self.detect_tor_socks()
        new_ip = self.get_current_ip()

        self.append_output(
            f"[cyan]SOCKS Port Used: {socks_port}[/]\n"
            f"[cyan]Old IP: {old_ip}[/]\n"
            f"[green]New IP: {new_ip}[/]\n"
            f"[green]✓ Tor IP rotated via port {port}[/]"
        )

    def update_proxy_status(self):
        self.update_session_info()

    def safe_ui_update(self, func):
        if QThread.currentThread() == QApplication.instance().thread():
            func()
        else:
            QTimer.singleShot(0, func)

    # ==================== OUTPUT METHODS ====================

    def append_output(self, text):
        """Append output ke console - SKIP session output"""
        if not text or not text.strip():
            return

        if QThread.currentThread() != QApplication.instance().thread():
            self.console_output_signal.emit(str(text))
            return

        if not hasattr(self, "console_output") or self.console_output is None:
            return

        raw_text = text

        # ===== CEK APAKAH INI OUTPUT DARI SESSION =====
        # Deteksi karakteristik output session
        is_session_output = False
        session_patterns = [
            r'┌──\(.*㉿.*\)',                    # Kali / oh-my-zsh style
            r'└─[#$]',
            r'\(.*㉿.*\)',
            r'root@[\w\.-]+:.*[#$]',
            r'[\w\-]+@[\w\.-]+:[~/\w].*[#$]\s*$',
            r'\[\?2004[hl]\]',                   # bracketed paste mode
            r'^\s*[#$%>]\s*$',                   # bare prompt
        ]
        
        for pattern in session_patterns:
            if re.search(pattern, raw_text, re.IGNORECASE):
                is_session_output = True
                break
        
        # Jika ini output dari session, JANGAN tampilkan di console
        if is_session_output:
            # Proses session detection tapi tanpa menampilkan di console
            self._process_session_detection(raw_text)
            return

        # ===== INI BUKAN OUTPUT SESSION, TAMPILKAN DI CONSOLE =====
        html = self.rich_to_html_with_matrix(text)
        self.console_output.insertHtml(html + "<br>")

        cursor = self.console_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.console_output.setTextCursor(cursor)

        scrollbar = self.console_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        # Session detection untuk non-session output (misal: "[+] Session opened")
        self._process_session_detection(raw_text)

        if hasattr(self, "sidebar_context_box") and self.sidebar_context_box:
            clean_text = self._filter_context_output(text)
            if clean_text and clean_text.strip():
                current = self.sidebar_context_box.toPlainText()
                merged = (current + "\n" + clean_text).strip()
                if len(merged) > 10000:
                    merged = merged[-10000:]
                self.sidebar_context_box.setPlainText(merged)
                scrollbar = self.sidebar_context_box.verticalScrollBar()
                if scrollbar:
                    scrollbar.setValue(scrollbar.maximum())

    def _process_session_detection(self, raw_text):
        """Proses deteksi session dari output - tanpa menampilkan di console"""
        session_patterns = [
            r"Session (.+?) opened \((.+?) -> (.+?)\)",
            r"\[\+\]\s+Session (.+?) opened",
            r"Session (\d+) opened \(([\d.]+):(\d+) -> ([\d.]+):(\d+)\)",
            r"\[\+\]\s+Meterpreter session (\d+) opened",
            r"Reverse shell spawned on ([\d.]+):(\d+)",
            r"Shell caught from ([\d.]+) on port (\d+)",
        ]

        detected = False
        for pattern in session_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                self.create_new_session(match, raw_text)
                detected = True
                break

        if (not detected and self.active_session_id and
            self.active_session_id in self.sessions):
            sess = self.sessions[self.active_session_id]
            sess["output"] += raw_text + "\n"
            if hasattr(self, "main_tabs") and self.main_tabs.currentIndex() == 4:
                self.session_output.setPlainText(sess["output"])
                self.session_output.moveCursor(QTextCursor.MoveOperation.End)

        if detected and self.main_tabs.currentIndex() != 3:
            self.main_tabs.setCurrentIndex(3)
            # Tampilkan notifikasi di console (bukan output session)
            self.console_output.insertHtml(
                '<span style="color:#ffaa00;">[!] Session detected! Check Sessions tab.</span><br>'
        )

    def _filter_context_output(self, text: str) -> str:
        if not text:
            return ""

        clean = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
        clean = re.sub(r"\x1b\][^\x07]*\x07", "", clean)
        clean = re.sub(r"\x1b[=><]", "", clean)
        clean = clean.replace("\x1b", "")

        lines = clean.split("\n")
        filtered_lines = []

        keep_patterns = [
            r"Discovered open port \d+/\w+ on \d+\.\d+\.\d+\.\d+",
            r"\[\+\] Scan completed",
            r"Open ports:",
            r"Target:",
            r"Mode:",
            r"Ports:",
            r"Scan completed!",
            r"✓",
            r"[+]",
        ]

        skip_patterns = [
            r"^Resolving:",
            r"^> nmap",
            r"^Starting Nmap",
            r"WARNING:",
            r"Completed ARP Ping Scan",
            r"Initiating",
            r"Scanning \d+ hosts",
            r"rate:",
            r"%",
            r"waiting",
            r"^$",
            r"^─+$",
            r"^╭",
            r"^╰",
            r"^├",
            r"^│",
            r"^╞",
            r"^╡",
            r"^╔",
            r"^╚",
            r"^═+$",
            r"^┌",
            r"^└",
            r"^┐",
            r"^┘",
        ]

        for line in lines:
            line = line.strip()

            if not line:
                continue

            skip = False
            for pattern in skip_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    skip = True
                    break

            if skip:
                continue

            keep = False
            for pattern in keep_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    keep = True
                    break

            if keep:
                filtered_lines.append(line)
            else:
                if re.search(r"\d+\.\d+\.\d+\.\d+", line):
                    filtered_lines.append(line)
                elif any(kw in line.lower() for kw in ["open", "closed", "filtered", "found"]):
                    filtered_lines.append(line)

        if not filtered_lines:
            return ""

        result = []

        target = None
        mode = None
        open_ports = []

        for line in filtered_lines:
            if "Target:" in line:
                target = line
            elif "Mode:" in line:
                mode = line
            elif "Open ports:" in line or "Ports:" in line:
                ports_match = re.search(r"[0-9, ]+", line)
                if ports_match:
                    open_ports = ports_match.group().strip().split(", ")
            elif "Discovered open port" in line:
                port_match = re.search(r"port (\d+)/\w+ on (\d+\.\d+\.\d+\.\d+)", line)
                if port_match:
                    port = port_match.group(1)
                    ip = port_match.group(2)
                    if f"{ip}:{port}" not in open_ports:
                        open_ports.append(f"{ip}:{port}")
            elif "Scan completed!" in line or "[+] Scan completed" in line:
                if open_ports:
                    result.append(
                        f"[+] Scan completed! Open ports: {', '.join(open_ports)}"
                    )
                else:
                    result.append("[+] Scan completed! (No open ports found)")

        summary = []
        if target:
            summary.append(target)
        if mode:
            summary.append(mode)
        if open_ports:
            summary.append(f"Open ports: {', '.join(open_ports)}")

        if summary:
            return "\n".join(summary)

        return "\n".join(filtered_lines[:10])

    def strip_ansi_sequences(self, text):
        import re

        text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
        text = re.sub(r"\x1b\][^\x07]*\x07", "", text)
        text = re.sub(r"\x1b[=><]", "", text)
        text = text.replace("\x1b", "")
        return text

    def rich_to_html_with_matrix(self, text):
        import re, html as _html

        COLOR = {
            "black": "#000000",
            "red": "#ff5555",
            "green": "#00ff00",
            "yellow": "#ffff00",
            "blue": "#5555ff",
            "magenta": "#ff00ff",
            "cyan": "#00ffff",
            "white": "#ffffff",
            "orange": "#ffaa00",
            "bright_green": "#88ff88",
            "bright_cyan": "#88ffff",
            "dim": "#558855",
            "success": "#00ff00",
            "error": "#ff5555",
            "warning": "#ffff00",
            "info": "#00ffff",
            "session": "#ffaa00",
            "matrix_green": "#00ff00",
            "matrix_cyan": "#00ffff",
        }
        ANSI = {
            "0": "reset",
            "1": "bold",
            "30": "black",
            "31": "red",
            "32": "green",
            "33": "yellow",
            "34": "blue",
            "35": "magenta",
            "36": "cyan",
            "37": "white",
            "90": "black",
            "91": "red",
            "92": "bright_green",
            "93": "yellow",
            "94": "blue",
            "95": "magenta",
            "96": "bright_cyan",
            "97": "white",
        }

        text = re.sub(r"\x1b\][^\x07\x1b]*[\x07]", "", text)
        text = re.sub(r"\x1b[=><]", "", text)

        def ansi_to_rich(m):
            codes = m.group(1).split(";")
            out = ""
            for c in codes:
                if c in ("0", ""):
                    out += "[/]"
                elif c == "1":
                    out += "[bold]"
                elif c in ANSI:
                    out += f"[{ANSI[c]}]"
            return out

        text = re.sub(r"(?:\x1b)?\[([0-9;]+)[mG]", ansi_to_rich, text)
        text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
        text = text.replace("\x1b", "")

        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        def color_nmap_line(line):
            line = re.sub(
                r"\b(open)\b",
                r'<span style="color:#00ff00;font-weight:bold;text-shadow:0 0 6px #00ff00">\1</span>',
                line,
            )
            line = re.sub(
                r"\b(closed)\b",
                r'<span style="color:#ff5555;opacity:0.7">\1</span>',
                line,
            )
            line = re.sub(
                r"\b(filtered)\b",
                r'<span style="color:#ffff00;font-weight:bold">\1</span>',
                line,
            )
            line = re.sub(
                r"(\d+/(?:tcp|udp))", r'<span style="color:#00ffff">\1</span>', line
            )
            line = re.sub(
                r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
                r'<span style="color:#88ffff">\1</span>',
                line,
            )
            return line

        lines = text.split("\n")
        lines = [color_nmap_line(l) for l in lines]
        text = "\n".join(lines)

        stack = []
        out = ""
        i = 0
        while i < len(text):
            if text[i] == "[":
                end = text.find("]", i)
                if end != -1:
                    tag = text[i + 1: end].strip()
                    if tag == "/" or tag.startswith("/"):
                        if stack:
                            stack.pop()
                        out += "</span>"
                        i = end + 1
                        continue

                    parts = [p.strip() for p in tag.replace(",", " ").split() if p.strip()]
                    color_name = None
                    is_bold = False
                    is_dim = False
                    for p in parts:
                        if p == "bold":
                            is_bold = True
                        elif p == "dim":
                            is_dim = True
                        elif p in COLOR:
                            color_name = p

                    if color_name or is_bold or is_dim:
                        stack.append(tag)
                        styles = []
                        if color_name:
                            c = COLOR[color_name]
                            styles.append(f"color:{c}")
                            styles.append(f"text-shadow:0 0 6px {c}")
                        elif is_bold and not is_dim:
                            styles.append("color:#00ff00")
                        if is_bold:
                            styles.append("font-weight:bold")
                        if is_dim:
                            if not color_name:
                                styles.append("color:#558855")
                            styles.append("opacity:0.75")
                        style_str = ";".join(styles)
                        out += f'<span style="{style_str}">'
                        i = end + 1
                        continue
            out += text[i]
            i += 1

        while stack:
            stack.pop()
            out += "</span>"

        for ch, col in [
            ("│", "#00ff00"),
            ("─", "#00ff00"),
            ("┌", "#00ff00"),
            ("┐", "#00ff00"),
            ("└", "#00ff00"),
            ("┘", "#00ff00"),
            ("├", "#00ff00"),
            ("┤", "#00ff00"),
            ("┬", "#00ff00"),
            ("┴", "#00ff00"),
            ("┼", "#00ff00"),
        ]:
            out = out.replace(ch, f'<span style="color:{col}">{ch}</span>')

        out = out.replace("\n", "<br>")

        return f"<span style=\"font-family:'Courier New',monospace;color:#00ff00;white-space:pre-wrap;word-wrap:break-word;line-height:1.5\">{out}</span>"

    def detect_content_type(self, text):
        text_lower = text.lower()

        if any(pattern in text_lower for pattern in ["session", "meterpreter", "shell", "reverse"]):
            return "session"
        elif any(pattern in text_lower for pattern in ["error", "failed", "✗", "[-]"]):
            return "error"
        elif any(pattern in text_lower for pattern in ["success", "✓", "[+]", "loaded"]):
            return "success"
        elif any(pattern in text_lower for pattern in ["warning", "⚠", "[!]"]):
            return "warning"
        elif any(pattern in text_lower for pattern in ["info", "[*]", "scanning", "detected"]):
            return "info"
        elif any(pattern in text_lower for pattern in ["matrix", "hack", "cyber"]):
            return "matrix"
        elif any(pattern in text_lower for pattern in ["command", ">", "$"]):
            return "command"
        else:
            return "normal"

    def apply_content_styling(self, char, content_type, full_text, position):
        base_style = "color: #00ff00;"

        if content_type == "session":
            return f'<span style="{base_style} color: #ffaa00; text-shadow: 0 0 6px #ffaa00; font-weight: bold;">{char}</span>'
        elif content_type == "error":
            return f'<span style="{base_style} color: #ff5555; text-shadow: 0 0 6px #ff5555; font-weight: bold;">{char}</span>'
        elif content_type == "success":
            return f'<span style="{base_style} color: #00ff00; text-shadow: 0 0 8px #00ff00, 0 0 12px #00ff00; font-weight: bold;">{char}</span>'
        elif content_type == "warning":
            return f'<span style="{base_style} color: #ffff00; text-shadow: 0 0 6px #ffff00; font-weight: bold;">{char}</span>'
        elif content_type == "info":
            return f'<span style="{base_style} color: #00ffff; text-shadow: 0 0 6px #00ffff; font-weight: bold;">{char}</span>'
        elif content_type == "matrix":
            return f'<span style="{base_style} color: #00ff00; text-shadow: 0 0 10px #00ff00, 0 0 20px #00ff00; font-weight: bold; font-family: "Courier New", monospace;">{char}</span>'
        elif content_type == "command":
            return f'<span style="{base_style} color: #ffff00; text-shadow: 0 0 5px #ffff00; font-weight: bold;">{char}</span>'
        else:
            return f'<span style="{base_style}">{char}</span>'

    def format_unicode_table(self, text):
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        lines = safe.split("\n")
        if not lines:
            return ""

        max_len = max(len(line) for line in lines)
        normalized = []

        for line in lines:
            if len(line) < max_len:
                line = line + (" " * (max_len - len(line)))
            elif len(line) > max_len:
                line = line[:max_len]
            normalized.append(line)

        styled_lines = [self.style_matrix_table_line(line) for line in normalized]
        styled_text = "<br>".join(styled_lines)

        html = f"""
        <div style="
            max-width: 100%;
            overflow-x: auto;
            padding: 8px;
            margin: 5px 0;
            background: rgba(0, 255, 0, 0.05);
            border: 1px solid #008800;
            border-radius: 3px;
        ">
            <div style="
                font-family: 'Courier New', monospace;
                font-size: 11px;
                white-space: pre-wrap;
                word-wrap: break-word;
                margin: 0;
                color: #00ff00;
                line-height: 1.4;
            ">{styled_text}</div>
        </div>
        """
        return html

    def style_matrix_table_line(self, line):
        border_chars = ["─", "│", "┌", "┐", "└", "┘", "┬", "┴", "├", "┤", "┼"]

        if all(char in border_chars + [" "] for char in line):
            return f'<span style="color: #00ff00; text-shadow: 0 0 5px #00ff00;">{line}</span>'

        return self.colorize_matrix_table_content(line)

    def colorize_matrix_table_content(self, line):
        result = []
        i = 0

        while i < len(line):
            char = line[i]

            if char in ["─", "│", "┌", "┐", "└", "┘", "┬", "┴", "├", "┤", "┼"]:
                result.append(
                    f'<span style="color: #00ff00; text-shadow: 0 0 5px #00ff00;">{char}</span>'
                )
            else:
                context_color = self.get_matrix_content_color(line, i)
                result.append(
                    f'<span style="color: {context_color}; text-shadow: 0 0 3px {context_color};">{char}</span>'
                )

            i += 1

        return "".join(result)

    def get_matrix_content_color(self, line, position):
        words = line.split()
        current_word = ""

        start_pos = position
        while start_pos > 0 and line[start_pos - 1] not in [
            " ",
            "│",
            "┌",
            "┐",
            "└",
            "┘",
            "├",
            "┤",
        ]:
            start_pos -= 1

        end_pos = position
        while end_pos < len(line) - 1 and line[end_pos + 1] not in [
            " ",
            "│",
            "┌",
            "┐",
            "└",
            "┘",
            "├",
            "┤",
        ]:
            end_pos += 1

        current_word = line[start_pos: end_pos + 1].lower().strip()

        if any(keyword in current_word for keyword in [
            "success", "active", "open", "running", "enabled", "true", "yes"
        ]):
            return "#00ff00"
        elif any(keyword in current_word for keyword in [
            "failed", "error", "closed", "stopped", "disabled", "false", "no"
        ]):
            return "#ff5555"
        elif any(keyword in current_word for keyword in [
            "warning", "pending", "unknown", "filtered"
        ]):
            return "#ffff00"
        elif any(keyword in current_word for keyword in [
            "name", "host", "port", "status", "type", "id", "service"
        ]):
            return "#00ffff"
        elif current_word.replace(".", "").replace(":", "").isdigit():
            return "#ffaa00"
        else:
            return "#88ff88"

    def create_new_session(self, match, raw_text):
        try:
            print(f"DEBUG: Session match groups: {match.groups()}")

            if len(match.groups()) >= 3:
                sess_id = match.group(1)
                source = match.group(2)
                destination = match.group(3)

                if ":" in source:
                    src_ip, src_port = source.split(":")
                else:
                    src_ip, src_port = "unknown", "unknown"

                if ":" in destination:
                    dst_ip, dst_port = destination.split(":")
                else:
                    dst_ip, dst_port = "unknown", "unknown"
            else:
                sess_id = f"session_{len(self.sessions) + 1}"
                src_ip = "unknown"
                src_port = "unknown"
                dst_ip = self.framework.session.get("LHOST", "0.0.0.0")
                dst_port = self.framework.session.get("LPORT", 4444)

            detected_os = "unknown"
            detected_hostname = "unknown"
            text_lower = raw_text.lower()

            hostname_patterns = [
                r"hostname[=:]\s*([a-zA-Z0-9_\-\.]+)",
                r"computer[_\s]*name[=:]\s*([a-zA-Z0-9_\-\.]+)",
                r"\[([a-zA-Z0-9_\-\.]+)@",
                r"([a-zA-Z0-9_\-\.]+)@[\w\.\-]+",
                r"@([a-zA-Z0-9_\-\.]+)[:~\s]",
                r"([a-zA-Z0-9_\-\.]+)[>\\]",
                r"hostname\s+(\S+)",
                r"Hostname\s*:\s*(\S+)",
                r"(\w[\w\-\.]+)(?:\.local|\.lan|\.internal)",
            ]

            for pattern in hostname_patterns:
                match_host = re.search(pattern, raw_text, re.IGNORECASE)
                if match_host:
                    potential_hostname = match_host.group(1)
                    if len(potential_hostname) < 50 and len(potential_hostname) > 1:
                        if not potential_hostname.startswith(
                            ("session", "reverse", "shell", "connection")
                        ):
                            detected_hostname = potential_hostname
                            break

            lines = raw_text.split("\n")
            for line in lines[:10]:
                line = line.strip()
                if "hostname" in line.lower():
                    parts = line.split()
                    for part in parts:
                        if "." in part and len(part) < 50 and len(part) > 3:
                            if not part.startswith(
                                ("http", "www", "192.", "10.", "172.", "127.")
                            ):
                                detected_hostname = part
                                break
                        elif re.match(r"^[a-zA-Z][a-zA-Z0-9\-]{2,20}$", part):
                            detected_hostname = part
                            break

            if any(keyword in text_lower for keyword in [
                "linux", "unix", "ubuntu", "debian", "centos", "kali", "parrot", "arch", "fedora"
            ]):
                detected_os = "linux"
            elif any(keyword in text_lower for keyword in [
                "windows", "microsoft", "cmd.exe", "powershell", "win32", "win64"
            ]):
                detected_os = "windows"
            elif any(keyword in text_lower for keyword in [
                "macos", "darwin", "apple", "mac os"
            ]):
                detected_os = "macos"

            session_data = {
                "id": sess_id,
                "type": "reverse_tcp",
                "lhost": dst_ip,
                "lport": dst_port,
                "rhost": src_ip,
                "rport": src_port,
                "ip": src_ip,
                "port": src_port,
                "os": detected_os,
                "hostname": (
                    detected_hostname
                    if detected_hostname != "unknown"
                    else f"target_{sess_id[-4:]}"
                ),
                "output": f"[*] Session {sess_id} created\nType: reverse_tcp\nOS: {detected_os}\nHostname: {detected_hostname}\nSource: {src_ip}:{src_port}\nDestination: {dst_ip}:{dst_port}\n{raw_text}\n\n",
                "status": "alive",
                "created": time.strftime("%H:%M:%S"),
                "socket": None,
                "handler": None,
            }

            with self.session_lock:
                self.sessions[sess_id] = session_data

            QTimer.singleShot(300, lambda: self.create_session_tab(sess_id, session_data))

            self.selected_session_id = sess_id
            self.active_session_id = sess_id

            self.update_sessions_ui()
            self.update_session_info()
            QTimer.singleShot(
                800, lambda: self.safe_ui_update(self.sync_sessions_from_reverse_tcp)
            )
            QTimer.singleShot(
                1200, lambda: self.safe_ui_update(self.update_session_info)
            )

            os_icons = {"linux": "🐧", "windows": "🪟", "macos": "🍎", "unknown": "💻"}
            icon = os_icons.get(detected_os, "💻")
            os_names = {
                "linux": "Linux",
                "windows": "Windows",
                "macos": "macOS",
                "unknown": "Unknown",
            }
            os_name = os_names.get(detected_os, "Unknown")

            self.append_output(
                f"[bold green][+] {icon} {os_name} Session {sess_id} Auto-detected![/]"
            )
            if detected_hostname != "unknown":
                self.append_output(f"[green]✓ Hostname: {detected_hostname}[/]")
            self.append_output(f"[green]✓ Auto-selected new session[/]")

        except Exception as e:
            self.append_output(f"[red]Session creation error: {e}[/]")

    def update_sessions_ui(self):
        try:
            self.session_list.clear()

            os_icons = {
                "linux": "🐧",
                "windows": "🪟",
                "macos": "🍎",
                "unknown": "💻",
            }

            for sess_id, sess in self.sessions.items():
                os_type = sess.get("os", "unknown")
                hostname = sess.get("hostname", "")
                icon = os_icons.get(os_type, "💻")

                if hostname and hostname != "unknown":
                    item_text = f"{icon} {hostname[:20]} | {sess.get('ip', '?.?.?.?')}:{sess.get('port', '?')} | {sess.get('type', 'unknown')}"
                else:
                    item_text = f"{icon} {sess_id[:12]} | {sess.get('ip', '?.?.?.?')}:{sess.get('port', '?')} | {sess.get('type', 'unknown')}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, sess_id)

                color_map = {
                    "reverse_tcp": "#50fa7b",
                    "meterpreter": "#ff79c6",
                    "bash": "#8be9fd",
                    "python": "#ffb86c",
                    "powershell": "#bd93f9",
                    "shell": "#f1fa8c",
                }

                os_color_map = {
                    "linux": "#50fa7b",
                    "windows": "#ff79c6",
                    "macos": "#ffb86c",
                    "unknown": "#6272a4",
                }
                base_color = color_map.get(sess.get("type", ""), "#ffffff")
                item.setForeground(QColor(os_color_map.get(os_type, "#6272a4")))
                self.session_list.addItem(item)

            if self.session_list.count() > 0 and not self.selected_session_id:
                self.session_list.setCurrentRow(0)
                self.on_session_selected(self.session_list.currentItem())

            elif self.selected_session_id and self.selected_session_id in self.sessions:
                for i in range(self.session_list.count()):
                    item = self.session_list.item(i)
                    if (item and item.data(Qt.ItemDataRole.UserRole) == self.selected_session_id):
                        self.session_list.setCurrentItem(item)
                        self.on_session_selected(item)
                        break

        except Exception as e:
            self.append_output(f"[red]Session UI Error: {e}[/]")

    def sync_sessions_from_reverse_tcp(self):
        try:
            from modules.payload.reverse.reverse_tcp import SESSIONS, SESSIONS_LOCK

            if (self.framework.loaded_module and
                hasattr(self.framework.loaded_module, "module") and
                hasattr(self.framework.loaded_module.module, "SESSIONS")):
                _active_mod = self.framework.loaded_module.module
                SESSIONS = _active_mod.SESSIONS
                SESSIONS_LOCK = _active_mod.SESSIONS_LOCK
            else:
                import modules.payload.reverse.reverse_tcp as rtcp
                SESSIONS = rtcp.SESSIONS
                SESSIONS_LOCK = rtcp.SESSIONS_LOCK

            with SESSIONS_LOCK:
                for sess_id, rev_sess in SESSIONS.items():
                    sock = None
                    if hasattr(rev_sess, "socket"):
                        sock = rev_sess.socket
                    elif isinstance(rev_sess, dict) and "socket" in rev_sess:
                        sock = rev_sess["socket"]

                    rev_hostname = getattr(rev_sess, "hostname", "unknown")
                    rev_os = getattr(rev_sess, "os", "unknown")

                    if sess_id not in self.sessions:
                        self.sessions[sess_id] = {
                            "id": sess_id,
                            "type": getattr(rev_sess, "type", "reverse_tcp"),
                            "ip": getattr(rev_sess, "rhost", "unknown"),
                            "port": getattr(rev_sess, "rport", "unknown"),
                            "lhost": getattr(rev_sess, "lhost", "unknown"),
                            "lport": getattr(rev_sess, "lport", "unknown"),
                            "os": rev_os,
                            "hostname": (
                                rev_hostname
                                if rev_hostname != "unknown"
                                else f"target_{sess_id[-4:]}"
                            ),
                            "output": f"[*] Session {sess_id} synced from reverse_tcp\n",
                            "status": getattr(rev_sess, "status", "alive"),
                            "created": getattr(
                                rev_sess, "created", time.strftime("%H:%M:%S")
                            ),
                            "socket": sock,
                            "handler": rev_sess,
                        }
                        # Tampilkan di console TAPI sebagai log sistem, bukan output session
                        self.console_output.insertHtml(
                            f'<span style="color:#50fa7b;">✓ Added session {sess_id} (hostname: {rev_hostname})</span><br>'
                        )
                    else:
                        self.sessions[sess_id]["socket"] = sock
                        self.sessions[sess_id]["handler"] = rev_sess
                        self.sessions[sess_id]["status"] = getattr(
                            rev_sess, "status", "alive"
                        )
                        if rev_os != "unknown":
                            self.sessions[sess_id]["os"] = rev_os
                        if rev_hostname != "unknown":
                            self.sessions[sess_id]["hostname"] = rev_hostname

            self.update_sessions_ui()
            self.update_session_info()
            if hasattr(self, "network_map_widget"):
                self.network_map_widget.refresh_map()

            if len(SESSIONS) > 0:
                if (not self.selected_session_id or
                    self.selected_session_id not in self.sessions):
                    first_sess = list(SESSIONS.keys())[0]
                    self.selected_session_id = first_sess
                    self.active_session_id = first_sess

        except Exception as e:
            self.console_output.insertHtml(
                f'<span style="color:#ff5555;">Sync error: {e}</span><br>'
            )

    def _parse_reverse_tcp_output(self, text):
        if not text or "[*] Session" not in text:
            return

        try:
            import re

            pattern = r"\[\*\]\s+Session\s+(\d+)\s+opened\s+\(([0-9.]+):(\d+)\s+->\s+([0-9.]+):(\d+)\)"
            match = re.search(pattern, text)

            if match:
                sess_id = match.group(1)
                src_ip = match.group(2)
                src_port = match.group(3)
                dst_ip = match.group(4)
                dst_port = match.group(5)

                if sess_id not in self.sessions:
                    self.sessions[sess_id] = {
                        "id": sess_id,
                        "type": "reverse_tcp",
                        "status": "active",
                        "os": "Unknown",
                        "hostname": f"target_{sess_id[-4:]}",
                        "src": f"{src_ip}:{src_port}",
                        "dst": f"{dst_ip}:{dst_port}",
                        "ip": src_ip,
                        "port": src_port,
                        "lhost": dst_ip,
                        "lport": dst_port,
                        "output": f"[*] Session {sess_id} detected from module output\n",
                    }

                    self.update_sessions_ui()
                    self.update_session_info()

                    self.append_output(
                        f"[bold green][✓] Session {sess_id} detected: {src_ip}:{src_port} -> {dst_ip}:{dst_port}[/]"
                    )

        except Exception as e:
            pass

    def append_session_output(self, session_id, text):
        if QThread.currentThread() != QApplication.instance().thread():
            self.session_output_signal.emit(session_id, str(text))
            return

        try:
            if session_id in self.sessions:
                session = self.sessions[session_id]

                if not text or not str(text).strip():
                    return
                import re

                clean_text = text

                # ANSI / control
                clean_text = re.sub(r"\x1b\][^\x07\x1b]*(\x07|\x1b\\)", "", clean_text)
                clean_text = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", clean_text)
                clean_text = re.sub(r"\x1b[=><]", "", clean_text)
                clean_text = re.sub(r"\x1b.", "", clean_text)
                clean_text = clean_text.replace("\r\n", "\n").replace("\r", "\n")
                clean_text = re.sub(r"\[\??[0-9;]*[a-zA-Z]", "", clean_text)
                clean_text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", clean_text)

                # Hapus blok prompt Kali 2-baris + jarak kosong di tengah
                clean_text = re.sub(
                    r"[┌╭].*?[㉿@].*?\n+\s*[└╰]─\s*[#$%>].*",
                    "",
                    clean_text,
                    flags=re.MULTILINE,
                )
                clean_text = re.sub(
                    r"[┌╭]──.*\n+\s*[└╰]─\s*[#$%>].*",
                    "",
                    clean_text,
                    flags=re.MULTILINE,
                )

                # Filter baris prompt sisa + collapse blank
                lines = []
                prev_blank = False
                for line in clean_text.split("\n"):
                    line = line.strip()
                    if not line:
                        if prev_blank:
                            continue
                        lines.append("")
                        prev_blank = True
                        continue
                    if re.match(r"^[┌╭└╰].*", line):
                        continue
                    if "㉿" in line:
                        continue
                    if re.match(r"^└─\s*[#$%>]", line):
                        continue
                    if re.match(r"^[\s]*[#$%>]\s*$", line):
                        continue
                    if re.match(r"^[\w\-]+@[\w\.-]+[:~].*[#$%>]\s*$", line):
                        continue
                    if re.search(r"\(.*㉿.*\)", line):
                        continue
                    if re.match(r"^\[.*@.*\]", line) and len(line) < 80:
                        continue
                    if re.match(r"^[\[\]0-9;mCHJKABCD]*$", line):
                        continue
                    lines.append(line)
                    prev_blank = False

                clean_text = "\n".join(lines).strip()
                if not clean_text:
                    return

                if clean_text.startswith("$ "):
                    formatted_text = f"\n🔹 {clean_text}"
                elif any(indicator in clean_text for indicator in ["drwx", "-rw", "total "]):
                    formatted_text = f"  {clean_text}"
                elif clean_text.startswith("/") and "/" in clean_text:
                    formatted_text = f"📁 {clean_text}"
                else:
                    formatted_text = clean_text

                session["output"] += formatted_text + "\n"

                if self.active_session_id == session_id:
                    current_text = self.session_output.toPlainText()
                    self.session_output.setPlainText(
                        current_text + formatted_text + "\n"
                    )
                    self.session_output.moveCursor(QTextCursor.MoveOperation.End)

        except Exception as e:
            self.append_output(f"[red]Session Output Error: {e}[/]")

    def format_session_output(self, text):
        import re

        clean_text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
        clean_text = re.sub(
            r"[┌╭].*?[㉿@].*?\n+\s*[└╰]─\s*[#$%>].*",
            "",
            clean_text,
            flags=re.MULTILINE,
        )
        clean_text = re.sub(
            r"[┌╭]──.*\n+\s*[└╰]─\s*[#$%>].*",
            "",
            clean_text,
            flags=re.MULTILINE,
        )
        lines = []
        for line in clean_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            if re.match(r"^[┌╭└╰].*", line) or "㉿" in line:
                continue
            if re.match(r"^[\s]*[#$%>]\s*$", line):
                continue
            lines.append(line)
        clean_text = "\n".join(lines).strip()
        if not clean_text:
            return ""

        if clean_text.startswith("$ "):
            return f"\n🔹 {clean_text}"
        elif any(indicator in clean_text for indicator in ["drwx", "-rw", "total "]):
            return f"  {clean_text}"
        elif clean_text.startswith("/") and "/" in clean_text:
            return f"📁 {clean_text}"
        else:
            return clean_text

    def switch_to_sessions_tab(self):
        try:
            self.tabs.setCurrentIndex(3)
        except Exception as e:
            print("Tab switch error:", e)

    def debug_session_storage(self):
        self.append_output("[yellow]=== SESSION STORAGE DEBUG ===[/]")

        try:
            if (self.framework.loaded_module and
                hasattr(self.framework.loaded_module, "module") and
                hasattr(self.framework.loaded_module.module, "SESSIONS")):
                _active_mod = self.framework.loaded_module.module
                SESSIONS = _active_mod.SESSIONS
                SESSIONS_LOCK = _active_mod.SESSIONS_LOCK
            else:
                SESSIONS = _rtcp_mod.SESSIONS
                SESSIONS_LOCK = _rtcp_mod.SESSIONS_LOCK

            with SESSIONS_LOCK:
                reverse_sessions = SESSIONS.copy()

            self.append_output(f"ReverseTCP SESSIONS: {len(reverse_sessions)}")
            for sess_id, sess in reverse_sessions.items():
                has_socket = sess.get("socket") is not None
                socket_status = "✓" if has_socket else "❌"
                self.append_output(f"  {socket_status} {sess_id}")

            self.append_output(f"GUI sessions: {len(self.sessions)}")
            for sess_id, sess in self.sessions.items():
                has_socket = sess.get("socket") is not None
                socket_status = "✓" if has_socket else "❌"
                self.append_output(f"  {socket_status} {sess_id}")

            reverse_ids = set(reverse_sessions.keys())
            gui_ids = set(self.sessions.keys())

            self.append_output(f"✓ Matching sessions: {list(reverse_ids & gui_ids)}")
            self.append_output(f"⚠️ Only in ReverseTCP: {list(reverse_ids - gui_ids)}")
            self.append_output(f"⚠️ Only in GUI: {list(gui_ids - reverse_ids)}")

            if reverse_ids & gui_ids:
                common_session = list(reverse_ids & gui_ids)[0]
                reverse_socket = reverse_sessions[common_session].get("socket")
                gui_socket = self.sessions[common_session].get("socket")

                self.append_output(f"Socket comparison for {common_session}:")
                self.append_output(f"  ReverseTCP socket: {reverse_socket}")
                self.append_output(f"  GUI socket: {gui_socket}")
                self.append_output(f"  Same object: {reverse_socket is gui_socket}")

        except Exception as e:
            self.append_output(f"[red]Debug error: {e}[/]")

        self.append_output("[yellow]================================[/]")

    def on_session_selected(self, item):
        try:
            if item is None:
                return

            session_id = item.data(Qt.ItemDataRole.UserRole)

            self.selected_session_id = session_id
            self.active_session_id = session_id

            if session_id in self.sessions:
                session = self.sessions[session_id]

                self.session_output.setPlainText(session["output"])
                self.session_output.moveCursor(QTextCursor.MoveOperation.End)

                os_type = session.get("os", "unknown")
                hostname = session.get("hostname", "")

                os_display = {
                    "linux": "Linux",
                    "windows": "Windows",
                    "macos": "macOS",
                    "unknown": "Unknown OS",
                }.get(os_type, "Unknown OS")
                if hostname and hostname != "unknown":
                    placeholder_text = f"Enter command for {hostname} ({os_display}) Session {session_id}..."
                else:
                    placeholder_text = f"Enter command for {os_display} Session {session_id} ({session['type']})..."

                self.session_cmd_input.setPlaceholderText(placeholder_text)

                for i in range(self.session_list.count()):
                    list_item = self.session_list.item(i)
                    if (list_item and list_item.data(Qt.ItemDataRole.UserRole) == session_id):
                        list_item.setBackground(QColor("#0078d4"))
                        list_item.setForeground(QColor("#ffffff"))
                    else:
                        if list_item:
                            list_item.setBackground(QColor("transparent"))
                            sess_os = self.sessions.get(
                                list_item.data(Qt.ItemDataRole.UserRole), {}
                            ).get("os", "unknown")
                            os_color_map = {
                                "linux": "#50fa7b",
                                "windows": "#ff79c6",
                                "macos": "#ffb86c",
                                "unknown": "#6272a4",
                            }
                            list_item.setForeground(
                                QColor(os_color_map.get(sess_os, "#6272a4"))
                            )

                os_icons = {
                    "linux": "🐧",
                    "windows": "🪟",
                    "macos": "🍎",
                    "unknown": "💻",
                }
                icon = os_icons.get(os_type, "💻")
                if hostname and hostname != "unknown":
                    self.append_output(
                        f"[green]✓ Selected {icon} {hostname} ({os_display}) Session {session_id}[/]"
                    )
                else:
                    self.append_output(
                        f"[green]✓ Selected {icon} {os_display} Session {session_id}[/]"
                    )

        except Exception as e:
            self.append_output(f"Session selection error: {e}")

    def send_session_command(self):
        if not self.sessions:
            self.append_output("[yellow]No sessions, trying to sync...[/]")
            self.sync_sessions_from_reverse_tcp()

        if not self.sessions:
            self.append_output("[red]❌ No sessions available![/]")
            return

        if not self.selected_session_id:
            first_session_id = list(self.sessions.keys())[0]
            self.selected_session_id = first_session_id
            self.active_session_id = first_session_id
            self.append_output(
                f"[yellow]⚠️ Auto-selected session: {first_session_id}[/]"
            )
            self.update_sessions_ui()

        session_id = self.selected_session_id
        cmd = self.session_cmd_input.text().strip()

        if not cmd:
            self.append_output("[yellow]Please enter a command[/]")
            return

        #self.append_output(f"[yellow]Sending to session {session_id}: {cmd}[/]")
        self.append_session_output(session_id, f"$ {cmd}")

        success = False

        if session_id in self.sessions:
            session = self.sessions[session_id]
            sock = session.get("socket")

            if sock:
                try:
                    import select

                    ready = select.select([], [sock], [], 0.5)
                    if ready[1]:
                        sock.send((cmd + "\n").encode())
                        success = True
                        self.append_output("[green]✓ Command sent via GUI socket[/]")

                        def read_response():
                            try:
                                time.sleep(0.3)
                                ready_read = select.select([sock], [], [], 5)
                                if ready_read[0]:
                                    data = sock.recv(8192).decode(
                                        "utf-8", errors="ignore"
                                    )
                                    if data:
                                        self.session_output_signal.emit(
                                            session_id, data
                                        )
                                else:
                                    self.append_output(
                                        "[dim]No immediate response (command may be running)[/]"
                                    )
                            except Exception as e:
                                self.append_output(f"[red]Response error: {e}[/]")

                        threading.Thread(target=read_response, daemon=True).start()
                    else:
                        self.append_output(
                            "[yellow]Socket not writable, trying alternate method[/]"
                        )
                except Exception as e:
                    self.append_output(f"[red]Socket send error: {e}[/]")

        if not success and session_id in self.sessions:
            session = self.sessions[session_id]
            handler = session.get("handler")

            if handler and hasattr(handler, "send_command"):
                try:
                    result = handler.send_command(cmd)
                    success = True
                    self.append_output("[green]✓ Command sent via handler[/]")
                    if result:
                        self.append_session_output(session_id, result)
                except Exception as e:
                    self.append_output(f"[yellow]Handler error: {e}[/]")

        if not success:
            try:
                _active_sess_obj = None
                if (self.framework.loaded_module and
                    hasattr(self.framework.loaded_module, "module") and
                    hasattr(self.framework.loaded_module.module, "SESSIONS")):
                    _SESS = self.framework.loaded_module.module.SESSIONS
                    _active_sess_obj = _SESS.get(session_id)

                if _active_sess_obj and hasattr(_active_sess_obj, "send_command"):
                    def _do_send(sess_obj, command, sid):
                        try:
                            result = sess_obj.send_command(command)
                            if result:
                                self.session_output_signal.emit(sid, result)
                        except Exception as ex:
                            self.console_output_signal.emit(
                                f"[red]Response read error: {ex}[/]"
                            )

                    threading.Thread(
                        target=_do_send,
                        args=(_active_sess_obj, cmd, session_id),
                        daemon=True,
                    ).start()
                    success = True
                    self.append_output(
                        "[green]✓ Command sent via reverse_tcp function[/]"
                    )
                else:
                    if (self.framework.loaded_module and
                        hasattr(self.framework.loaded_module, "module") and
                        hasattr(self.framework.loaded_module.module,
                                "send_command_to_session")):
                        _fn = self.framework.loaded_module.module.send_command_to_session
                    else:
                        _fn = _rtcp_mod.send_command_to_session
                    success = _fn(session_id, cmd)
                    if success:
                        self.append_output(
                            "[green]✓ Command sent (no response capture)[/]"
                        )
            except Exception as e:
                self.append_output(f"[yellow]reverse_tcp function error: {e}[/]")

        if not success:
            self.append_output("[red]❌ Failed to send command[/]")
            self.append_output(
                "[yellow]Debug: Run sync_sessions_from_reverse_tcp() first[/]"
            )
            self.append_output("[dim]Try: self.sync_sessions_from_reverse_tcp()[/]")

        self.session_cmd_input.clear()

    def send_command_direct_socket(self, session_id, command):
        try:
            session = self.sessions[session_id]
            sock = session.get("socket")

            if not sock:
                self.append_output("[red]❌ No socket in GUI session[/]")
                return False

            import select

            ready = select.select([], [sock], [], 0.1)
            if not ready[1]:
                self.append_output("[red]❌ Socket not writable[/]")
                return False

            full_command = command + "\n"
            bytes_sent = sock.send(full_command.encode())

            self.append_output(
                f"[green]✓ Method 3: Direct socket send ({bytes_sent} bytes)[/]"
            )
            return True

        except Exception as e:
            self.append_output(f"[red]❌ Direct socket error: {e}[/]")
            return False

    def verify_session_sync(self):
        self.append_output("[yellow]=== SESSION SYNC VERIFICATION ===[/]")

        try:
            if (self.framework.loaded_module and
                hasattr(self.framework.loaded_module, "module") and
                hasattr(self.framework.loaded_module.module, "SESSIONS")):
                _active_mod = self.framework.loaded_module.module
                SESSIONS = _active_mod.SESSIONS
                SESSIONS_LOCK = _active_mod.SESSIONS_LOCK
            else:
                SESSIONS = _rtcp_mod.SESSIONS
                SESSIONS_LOCK = _rtcp_mod.SESSIONS_LOCK

            with SESSIONS_LOCK:
                reverse_sessions = set(SESSIONS.keys())
            gui_sessions = set(self.sessions.keys())

            self.append_output(f"GUI sessions: {len(gui_sessions)}")
            self.append_output(f"ReverseTCP sessions: {len(reverse_sessions)}")

            matches = reverse_sessions & gui_sessions
            only_in_gui = gui_sessions - reverse_sessions
            only_in_reverse = reverse_sessions - gui_sessions

            self.append_output(f"✓ Synced sessions: {len(matches)}")
            self.append_output(f"⚠️ Only in GUI: {len(only_in_gui)}")
            self.append_output(f"⚠️ Only in ReverseTCP: {len(only_in_reverse)}")

            if only_in_gui:
                self.append_output(
                    f"[yellow]Sessions only in GUI: {list(only_in_gui)}[/]"
                )

            if only_in_reverse:
                self.append_output(
                    f"[yellow]Sessions only in ReverseTCP: {list(only_in_reverse)}[/]"
                )

            for sess_id in matches:
                gui_has_socket = (
                    "socket" in self.sessions[sess_id] and
                    self.sessions[sess_id]["socket"] is not None
                )
                reverse_has_socket = (
                    "socket" in SESSIONS[sess_id] and
                    SESSIONS[sess_id]["socket"] is not None
                )

                self.append_output(f"Session {sess_id}:")
                self.append_output(f"  GUI socket: {'✓' if gui_has_socket else '❌'}")
                self.append_output(
                    f"  ReverseTCP socket: {'✓' if reverse_has_socket else '❌'}"
                )

        except Exception as e:
            self.append_output(f"[red]Verification error: {e}[/]")

        self.append_output("[yellow]================================[/]")

    def force_sync_sessions(self):
        self.append_output("[yellow]=== FORCE SESSION SYNC ===[/]")

        try:
            if (self.framework.loaded_module and
                hasattr(self.framework.loaded_module, "module") and
                hasattr(self.framework.loaded_module.module, "SESSIONS")):
                _active_mod = self.framework.loaded_module.module
                SESSIONS = _active_mod.SESSIONS
                SESSIONS_LOCK = _active_mod.SESSIONS_LOCK
            else:
                SESSIONS = _rtcp_mod.SESSIONS
                SESSIONS_LOCK = _rtcp_mod.SESSIONS_LOCK

            with SESSIONS_LOCK:
                reverse_sessions = SESSIONS.copy()

            added_to_gui = 0
            for sess_id, reverse_sess in reverse_sessions.items():
                if sess_id not in self.sessions:
                    self.sessions[sess_id] = {
                        "id": sess_id,
                        "type": reverse_sess.get("type", "reverse_tcp"),
                        "ip": reverse_sess.get("rhost", "unknown"),
                        "port": reverse_sess.get("rport", "unknown"),
                        "lhost": reverse_sess.get("lhost", "unknown"),
                        "lport": reverse_sess.get("lport", "unknown"),
                        "output": f"[*] Session {sess_id} synced from reverse_tcp\n",
                        "handler": None,
                        "status": "alive",
                        "created": time.strftime("%H:%M:%S"),
                        "socket": reverse_sess.get("socket"),
                    }
                    added_to_gui += 1

            added_to_reverse = 0
            for sess_id, gui_sess in self.sessions.items():
                if sess_id not in reverse_sessions:
                    self.append_output(
                        f"[yellow]Cannot add {sess_id} to reverse_tcp (requires handler)[/]"
                    )

            self.append_output(f"[green]✓ Added {added_to_gui} sessions to GUI[/]")
            self.append_output(f"[green]✓ Force sync completed[/]")

            self.update_sessions_ui()

        except Exception as e:
            self.append_output(f"[red]Force sync error: {e}[/]")

        self.append_output("[yellow]========================[/]")

    def debug_session_connection(self):
        self.append_output(f"[yellow]=== SESSION CONNECTION DEBUG ===[/]")

        if not self.selected_session_id:
            self.append_output("[red]❌ No session selected[/]")
            return

        session_id = self.selected_session_id
        self.append_output(f"Selected Session: {session_id}")

        if session_id in self.sessions:
            session = self.sessions[session_id]
            self.append_output(f"✓ Found in GUI sessions")
            self.append_output(f"  Type: {session.get('type')}")
            self.append_output(f"  Status: {session.get('status')}")
            self.append_output(f"  IP: {session.get('ip')}")
            self.append_output(f"  Port: {session.get('port')}")
            self.append_output(
                f"  Has socket: {'socket' in session and session['socket'] is not None}"
            )
        else:
            self.append_output("[red]❌ Session not found in GUI sessions[/]")

        try:
            if (self.framework.loaded_module and
                hasattr(self.framework.loaded_module, "module") and
                hasattr(self.framework.loaded_module.module, "SESSIONS")):
                _active_mod = self.framework.loaded_module.module
                SESSIONS = _active_mod.SESSIONS
                SESSIONS_LOCK = _active_mod.SESSIONS_LOCK
            else:
                SESSIONS = _rtcp_mod.SESSIONS
                SESSIONS_LOCK = _rtcp_mod.SESSIONS_LOCK

            with SESSIONS_LOCK:
                if session_id in SESSIONS:
                    reverse_session = SESSIONS[session_id]
                    self.append_output(f"✓ Found in reverse_tcp sessions")
                    self.append_output(
                        f"  Has socket: {'socket' in reverse_session and reverse_session['socket'] is not None}"
                    )
                    if reverse_session.get("socket"):
                        sock = reverse_session["socket"]
                        self.append_output(
                            f"  Socket alive: {not sock._closed if hasattr(sock, '_closed') else 'Unknown'}"
                        )
                else:
                    self.append_output(
                        "[red]❌ Session not found in reverse_tcp sessions[/]"
                    )
        except Exception as e:
            self.append_output(f"[red]Error checking reverse_tcp: {e}[/]")

        self.append_output(f"[yellow]================================[/]")

    def test_session_communication(self):
        if not self.selected_session_id:
            self.append_output("[red]❌ Please select a session first![/]")
            return

        session_id = self.selected_session_id
        self.append_output(f"[yellow]Testing session: {session_id}[/]")

        test_cmd = "echo 'SESSION_TEST_SUCCESS'"
        self.append_session_output(session_id, f"$ {test_cmd}")

        try:
            from modules.payload.reverse.reverse_tcp import send_command_to_session

            self.append_output(f"[yellow]Sending command via reverse_tcp...[/]")

            success = send_command_to_session(session_id, test_cmd)

            if success:
                self.append_output(
                    "[green]✓ Command sent successfully via reverse_tcp[/]"
                )
                self.append_output("[yellow]Waiting for response...[/]")
            else:
                self.append_output("[red]❌ reverse_tcp reported failure[/]")

        except Exception as e:
            self.append_output(f"[red]❌ Error calling reverse_tcp: {e}[/]")
            import traceback
            self.append_output(f"[red]Traceback: {traceback.format_exc()}[/]")

    def kill_session(self):
        if not self.active_session_id or self.active_session_id not in self.sessions:
            self.append_output("[red]No active session selected[/]")
            return

        session_id = self.active_session_id
        session = self.sessions[session_id]

        self.append_output(f"[yellow][*] Killing Session {session_id}...[/]")

        try:
            if session.get("socket"):
                try:
                    session["socket"].close()
                    self.append_output(f"[green]✓ Socket connection closed[/]")
                except:
                    pass

            session["status"] = "killed"
            session["output"] += f"\n[Session {session_id} terminated by user]\n"

            with self.session_lock:
                del self.sessions[session_id]

            self.update_sessions_ui()

            self.active_session_id = None
            self.session_output.clear()
            self.session_cmd_input.setPlaceholderText(
                "Enter command for selected session..."
            )

            self.append_output(
                f"[green][+] Session {session_id} successfully terminated[/]"
            )

        except Exception as e:
            self.append_output(f"[red]Error killing session: {e}[/]")
            try:
                with self.session_lock:
                    del self.sessions[session_id]
                self.update_sessions_ui()
                self.active_session_id = None
            except:
                pass

    def kill_selected_session(self):
        item = self.session_list.currentItem()
        if not item:
            return
        sess_id = item.data(Qt.ItemDataRole.UserRole)

        if (hasattr(self.framework, "loaded_module") and
            "reverse_tcp" in self.framework.loaded_module.name.lower()):
            import importlib
            mod = importlib.import_module("modules.payloads.reverse.reverse_tcp")
            if hasattr(mod, "kill_session"):
                mod.kill_session(sess_id)

    def upgrade_session(self):
        if not self.active_session_id or self.active_session_id not in self.sessions:
            self.append_output("[red]No active session selected[/red]")
            return

        session = self.sessions[self.active_session_id]

        if session["type"] == "meterpreter":
            self.append_output("[yellow]Session is already Meterpreter[/yellow]")
            return

        self.append_output(
            f"[yellow][*] Attempting to upgrade Session {self.active_session_id} to Meterpreter...[/yellow]"
        )

        session["type"] = "meterpreter"
        session["output"] += "[+] Session upgraded to Meterpreter\n"

        self.update_sessions_ui()
        self.session_output.setPlainText(session["output"])
        self.session_output.moveCursor(QTextCursor.MoveOperation.End)

    def kill_selected_session(self):
        item = self.session_list.currentItem()
        if not item:
            self.append_output("[red]❌ No session selected[/red]")
            return

        sess_id = item.data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self,
            "Kill Session",
            f"Are you sure you want to kill session {sess_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.append_output(f"[yellow][*] Killing session {sess_id}...[/]")

        success = False

        try:
            target_module = None
            if (self.framework.loaded_module and
                "reverse_tcp" in self.framework.loaded_module.name.lower()):
                target_module = self.framework.loaded_module.module
            else:
                import modules.payload.reverse.reverse_tcp as rtcp
                target_module = rtcp

            if target_module and hasattr(target_module, "kill_session"):
                success = target_module.kill_session(sess_id)
                if success:
                    self.append_output(
                        f"[green]✓ Session {sess_id} killed via module[/]"
                    )
        except Exception as e:
            self.append_output(f"[yellow]Module kill error: {e}[/]")

        if sess_id in self.sessions:
            try:
                session = self.sessions[sess_id]
                if session.get("socket"):
                    try:
                        session["socket"].close()
                    except:
                        pass

                with self.session_lock:
                    if sess_id in self.sessions:
                        del self.sessions[sess_id]

                success = True
                self.append_output(f"[green]✓ Session {sess_id} removed from GUI[/]")
            except Exception as e:
                self.append_output(f"[red]Manual cleanup error: {e}[/]")

        if success:
            self.update_sessions_ui()
            self.update_session_info()

            if self.active_session_id == sess_id:
                self.active_session_id = None
                self.selected_session_id = None
                self.session_output.clear()
                self.session_cmd_input.setPlaceholderText(
                    "Enter command for selected session..."
                )

            if hasattr(self, "network_map_widget"):
                self.network_map_widget.cleanup()
                self.network_map_widget.refresh_map()
                self.append_output("[dim]Network map refreshed[/]")

            self.session_killed_signal.emit(sess_id)

            self.append_output(
                f"[green][+] Session {sess_id} successfully terminated[/]"
            )
        else:
            self.append_output(f"[red]❌ Failed to kill session {sess_id}[/]")
            self.append_output(
                f"[yellow]Available sessions: {list(self.sessions.keys())}[/]"
            )

    def send_session_command_direct(self, command):
        if not self.selected_session_id:
            return

        self.session_cmd_input.setText(command)
        self.send_session_command()

    def append_banner(self, text):
        if not text or not text.strip():
            return

        text = text.replace("\\", "\\\\")
        text = text.replace("\n", "<br>")

        i = 0
        output = ""
        tag_stack = []

        while i < len(text):
            if text[i:i + 2] == "\x1b":
                end = text.find("m", i)
                if end == -1:
                    output += text[i:]
                    break
                code = text[i + 2:end]
                i = end + 1

                if code == "0":
                    while tag_stack:
                        output += "</span>"
                        tag_stack.pop()
                elif code == "1":
                    output += '<span style="font-weight: bold;">'
                    tag_stack.append("b")
                elif code == "2":
                    output += '<span style="opacity: 0.6;">'
                    tag_stack.append("dim")
                elif code in ["31", "91"]:
                    output += '<span style="color: #ff5555;">'
                    tag_stack.append("red")
                elif code in ["32", "92"]:
                    output += '<span style="color: #50fa7b;">'
                    tag_stack.append("green")
                elif code in ["33", "93"]:
                    output += '<span style="color: #f1fa8c;">'
                    tag_stack.append("yellow")
                elif code in ["34", "94"]:
                    output += '<span style="color: #6272a4;">'
                    tag_stack.append("blue")
                elif code in ["35", "95"]:
                    output += '<span style="color: #ff79c6;">'
                    tag_stack.append("magenta")
                elif code in ["36", "96"]:
                    output += '<span style="color: #8be9fd;">'
                    tag_stack.append("cyan")
                elif code == "97":
                    output += '<span style="color: #ffffff;">'
                    tag_stack.append("white")
                else:
                    continue
            else:
                char = text[i]
                if char == "<":
                    output += "&lt;"
                elif char == ">":
                    output += "&gt;"
                elif char == "&":
                    output += "&amp;"
                else:
                    output += char
                i += 1

        while tag_stack:
            output += "</span>"
            tag_stack.pop()

        cursor = self.console_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(output)
        self.console_output.ensureCursorVisible()

        if hasattr(self, "ai_widget") and self.ai_widget:
            self.ai_widget.inject_output(text)

    def cmd_show_banner(self, args=None):
        try:
            from core import load_banners_from_folder, get_random_banner

            load_banners_from_folder()
            raw_banner = get_random_banner()

            if not raw_banner:
                self.append_output("[yellow]No banner found in 'banner/' folder[/yellow]")
                return

            import re
            clean_banner = re.sub(r'\[/?[a-zA-Z0-9_]*\]', '', raw_banner)
            clean_banner = re.sub(r'\x1b\[[0-9;]*[mG]', '', clean_banner)

            current_font = self.console_output.font()
            banner_font = QFont("DejaVu Sans Mono", 9)
            self.console_output.setFont(banner_font)

            cursor = self.console_output.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(clean_banner)
            cursor.insertText("\n\n")

            self.console_output.setFont(current_font)

            self.append_output("LazyFramework GUI v2.6")
            self.append_output("Type 'help' or click modules to start")
            self.append_output("Auto Tor IP rotation enabled (every 5 minutes)")

        except Exception as e:
            self.append_output(f"Banner error: {e}")

    # ==================== MODULE CATEGORY METHODS ====================

    _CAT_META = {
        "recon": {"color": "#8be9fd", "icon": "📡", "label": "Recon"},
        "scan": {"color": "#50fa7b", "icon": "🔍", "label": "Scan"},
        "exploit": {"color": "#ff5555", "icon": "⚡", "label": "Exploit"},
        "post": {"color": "#f1fa8c", "icon": "🎯", "label": "Post"},
        "privesc": {"color": "#ffb86c", "icon": "⬆️", "label": "Privesc"},
        "persistence": {"color": "#bd93f9", "icon": "🔒", "label": "Persistence"},
        "lateral": {"color": "#ff79c6", "icon": "🔄", "label": "Lateral"},
        "web": {"color": "#00ffff", "icon": "🌐", "label": "Web"},
        "cloud": {"color": "#ffffff", "icon": "☁️", "label": "Cloud"},
        "mobile": {"color": "#aaffaa", "icon": "📱", "label": "Mobile"},
        "aux": {"color": "#888888", "icon": "🛠️", "label": "Aux"},
        "payloads": {"color": "#bd93f9", "icon": "💣", "label": "Payloads"},
        "evasion": {"color": "#ffaa00", "icon": "👻", "label": "Evasion"},
        "report": {"color": "#4a90e2", "icon": "📊", "label": "Report"},
        "other": {"color": "#6272a4", "icon": "📦", "label": "Other"},
    }

    def _detect_category(self, module_path: str) -> str:
        p = module_path.lower()
        if "/recon/" in p:
            return "recon"
        if "/scan/" in p:
            return "scan"
        if "/exploit/" in p:
            return "exploit"
        if "/post/" in p:
            return "post"
        if "/privesc/" in p:
            return "privesc"
        if "/persistence/" in p:
            return "persistence"
        if "/lateral/" in p:
            return "lateral"
        if "/web/" in p:
            return "web"
        if "/cloud/" in p:
            return "cloud"
        if "/mobile/" in p:
            return "mobile"
        if "/aux/" in p:
            return "aux"
        if "/payload/" in p:
            return "payloads"
        if "/evasion/" in p:
            return "evasion"
        if "/report/" in p:
            return "report"
        return "other"

    def _make_folder_icon(self, color_hex: str) -> "QIcon":
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QLinearGradient, QPen
        from PyQt6.QtCore import Qt, QPointF

        size = 20
        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)

        painter = QPainter(px)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        base_color = QColor("#0078d4")
        light_color = QColor("#4aa3ff")
        dark_color = QColor("#005a9e")

        gradient = QLinearGradient(QPointF(0, 6), QPointF(0, 18))
        gradient.setColorAt(0, light_color)
        gradient.setColorAt(1, dark_color)

        painter.setBrush(gradient)
        painter.setPen(QPen(QColor("#003d6b"), 1.2))
        painter.drawRoundedRect(2, 7, 16, 12, 2, 2)

        tab_gradient = QLinearGradient(QPointF(0, 3), QPointF(0, 7))
        tab_gradient.setColorAt(0, light_color.lighter(160))
        tab_gradient.setColorAt(1, base_color)

        painter.setBrush(tab_gradient)
        painter.setPen(QPen(QColor("#003d6b"), 1))
        painter.drawRoundedRect(2, 4, 9, 5, 2, 2)

        painter.setPen(QPen(QColor(255, 255, 255, 80), 1))
        painter.drawLine(4, 5, 9, 5)

        painter.end()
        return QIcon(px)

    def load_all_modules(self):
        from collections import defaultdict

        self.module_tree.clear()
        modules = self.framework.metadata

        tree_data = defaultdict(lambda: defaultdict(list))
        for module_path, meta in sorted(modules.items()):
            if not meta.get("options"):
                continue
            cat = self._detect_category(module_path)
            rel = module_path.replace("modules/", "")
            parts = rel.split("/")
            sub_key = "/".join(parts[1:-1]) if len(parts) > 2 else ""
            tree_data[cat][sub_key].append((module_path, parts[-1], meta))

        CAT_ORDER = [
            "recon", "scan", "exploit", "post", "privesc",
            "persistence", "lateral", "web", "cloud", "mobile",
            "aux", "payloads", "evasion", "report", "other"
        ]

        for cat in CAT_ORDER:
            if cat not in tree_data:
                continue
            cm = self._CAT_META[cat]
            color = cm["color"]
            emoji = cm["icon"]
            label = cm["label"]
            mod_count = sum(len(v) for v in tree_data[cat].values())

            folder_icon = self._make_folder_icon(color)
            root_item = QTreeWidgetItem(self.module_tree)
            root_item.setText(0, f"  {emoji}  {label}  [{mod_count}]")
            root_item.setIcon(0, folder_icon)
            root_item.setData(0, Qt.ItemDataRole.UserRole, None)
            root_item.setData(0, Qt.ItemDataRole.UserRole + 1, cat)
            root_item.setForeground(0, QColor("#ffffff"))
            root_item.setFont(0, QFont("DejaVu Sans Mono", 10, QFont.Weight.Bold))
            root_item.setExpanded(False)

            for sub_key in sorted(tree_data[cat].keys()):
                mods = tree_data[cat][sub_key]

                if sub_key:
                    sub_item = QTreeWidgetItem(root_item)
                    sub_item.setText(0, f"  {sub_key}  [{len(mods)}]")
                    sub_item.setIcon(0, self._make_folder_icon(color))
                    sub_item.setData(0, Qt.ItemDataRole.UserRole, None)
                    sub_item.setData(0, Qt.ItemDataRole.UserRole + 1, cat)
                    sub_item.setForeground(0, QColor("#ffffff"))
                    sub_item.setFont(0, QFont("Hack", 10))
                    sub_item.setExpanded(False)
                    parent_item = sub_item
                else:
                    parent_item = root_item

                mod_icon = self._make_module_icon(color)
                leaf_font = QFont("DejaVu Sans Mono", 9)
                for module_path, mod_name, meta in sorted(mods, key=lambda x: x[1]):
                    desc = meta.get("description", "")
                    rank = meta.get("rank", "Normal")
                    leaf = QTreeWidgetItem(parent_item)
                    leaf.setText(0, f"  {mod_name}")
                    leaf.setIcon(0, mod_icon)
                    leaf.setData(0, Qt.ItemDataRole.UserRole, module_path)
                    leaf.setData(0, Qt.ItemDataRole.UserRole + 1, cat)
                    leaf.setForeground(0, QColor("#ffffff"))
                    leaf.setFont(0, leaf_font)
                    if desc:
                        leaf.setToolTip(0, f"[{rank}] {desc}")

        self.update_session_info()

    def _make_module_icon(self, color_hex: str) -> "QIcon":
        from PyQt6.QtGui import QPixmap, QPainter, QColor

        px = QPixmap(12, 12)
        px.fill(QColor(0, 0, 0, 0))
        painter = QPainter(px)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor(0, 120, 212, 180))
        painter.setPen(QColor(0, 120, 212))
        painter.drawEllipse(1, 1, 10, 10)
        painter.end()
        return QIcon(px)

    def on_category_click(self):
        button = self.sender()
        category = button.property("category")
        self.filter_modules_by_category(category)

    def filter_modules_by_category(self, category):
        root = self.module_tree.invisibleRootItem()
        for i in range(root.childCount()):
            cat_item = root.child(i)
            item_cat = cat_item.data(0, Qt.ItemDataRole.UserRole + 1) or ""
            if category == "all":
                cat_item.setHidden(False)
                cat_item.setExpanded(False)
            else:
                matches = (item_cat == category) or (
                    category == "payloads" and item_cat == "payloads"
                )
                cat_item.setHidden(not matches)
                if matches:
                    cat_item.setExpanded(False)

    def search_modules(self):
        search_text = self.search_input.text().lower().strip()

        def _traverse(item):
            module_path = item.data(0, Qt.ItemDataRole.UserRole)
            if module_path is None:
                any_visible = False
                for j in range(item.childCount()):
                    if _traverse(item.child(j)):
                        any_visible = True
                item.setHidden(not any_visible)
                if any_visible and search_text:
                    item.setExpanded(False)
                return any_visible
            else:
                if not search_text:
                    item.setHidden(False)
                    return True
                meta = self.framework.metadata.get(module_path, {})
                desc = meta.get("description", "").lower()
                matches = search_text in module_path.lower() or search_text in desc
                item.setHidden(not matches)
                return matches

        root = self.module_tree.invisibleRootItem()
        for i in range(root.childCount()):
            _traverse(root.child(i))

        if not search_text:
            for i in range(root.childCount()):
                root.child(i).setHidden(False)
                root.child(i).setExpanded(True)

    def perform_search(self):
        search_text = self.search_input.text()
        if search_text:
            self.execute_command("search", [search_text])

    def load_selected_module(self, item):
        if not item:
            return
        module_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not module_path:
            item.setExpanded(not item.isExpanded())
            return
        self._update_toolbar_module(module_path, active=True)
        self.load_module_info_to_main_tab(module_path)
        self.open_module_in_tab(module_path)

    def load_module_info_to_main_tab(self, module_path: str):
        try:
            if module_path not in self.framework.modules:
                return

            self.main_tabs.setCurrentIndex(2)

            import io, contextlib

            output_buffer = io.StringIO()

            old_module = self.framework.loaded_module
            module_file = self.framework.modules[module_path]
            spec = importlib.util.spec_from_file_location(
                module_path.replace("/", "_"), module_file
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            from bin.console import ModuleInstance
            temp_instance = ModuleInstance(module_path, mod)
            self.framework.loaded_module = temp_instance

            with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(
                output_buffer
            ):
                self.framework.cmd_info([])

            self.framework.loaded_module = old_module

            info_output = output_buffer.getvalue()
            if info_output.strip():
                html = self.create_simple_module_info(info_output)
                self.module_detail_info.setHtml(html)
            else:
                self.module_detail_info.setPlainText("No information available.")

        except Exception as e:
            self.module_detail_info.setPlainText(f"Error loading module info:\n{e}")
            print(f"[ERROR] load_module_info: {e}")

    def show_module_info_in_tab(self):
        try:
            import contextlib
            import io

            output_buffer = io.StringIO()

            with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(
                output_buffer
            ):
                self.framework.cmd_info([])

            info_output = output_buffer.getvalue()

            if info_output.strip():
                html_output = self.create_simple_module_info(info_output)
                self.module_detail_info.setHtml(html_output)

            self.main_tabs.setCurrentIndex(2)

        except Exception as e:
            self.module_detail_info.setPlainText(f"Error loading module info: {e}")

    def create_simple_module_info(self, text):
        import re

        clean_text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
        colored_text = self.add_rank_colors(clean_text)

        html = f"""
        <html>
        <head>
        <style>
            body {{
                font-family: 'Fira Code';
                font-weight: bold;
                font-size: 12px;
                background: #000;
                color: #ffffff;
                margin: 0;
                padding: 15px;
                line-height: 1.3;
            }}
            .module-header {{
                color: #00ffff;
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 15px;
                border-bottom: 1px solid #00ffff;
                padding-bottom: 5px;
            }}
            .section {{
                margin: 10px 0;
                padding: 10px;
                background: #252525;
                border: 1px solid #404040;
                border-radius: 3px;
            }}
            .option-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 5px 0;
                font-size: 11px;
            }}
            .option-table th {{
                background: #2d2d2d;
                color: #ff79c6;
                padding: 6px 8px;
                text-align: left;
                border: 1px solid #404040;
            }}
            .option-table td {{
                padding: 6px 8px;
                border: 1px solid #404040;
                color: #d4d4d4;
            }}
            .name {{ color: #8be9fd; font-weight: bold; }}
            .current {{ color: #f1fa8c; }}
            .required-yes {{ color: #50fa7b; }}
            .required-no {{ color: #ff5555; }}
            pre {{
                font-family: 'DejaVu Sans Mono', 'Courier New', monospace;
                white-space: pre-wrap;
                margin: 0;
                color: #d4d4d4;
            }}
            .rank-excellent {{ color: #ff5555; font-weight: bold; }}
            .rank-great {{ color: #ff79c6; font-weight: bold; }}
            .rank-good {{ color: #f1fa8c; font-weight: bold; }}
            .rank-normal {{ color: #50fa7b; font-weight: bold; }}
            .rank-average {{ color: #8be9fd; font-weight: bold; }}
            .rank-low {{ color: #bd93f9; font-weight: bold; }}
            .rank-manual {{ color: #ffb86c; font-weight: bold; }}
            .info-name {{ color: #8be9fd; font-weight: bold; }}
            .info-module {{ color: #ff79c6; }}
            .info-type {{ color: #50fa7b; }}
            .info-platform {{ color: #f1fa8c; }}
            .info-arch {{ color: #bd93f9; }}
            .info-author {{ color: #ffb86c; }}
            .info-license {{ color: #ff5555; }}
        </style>
        </head>
        <body>
            <div class="module-header">LAZYFRAMEWORK MODULE INFORMATION</div>
            <pre>{colored_text}</pre>
        </body>
        </html>
        """

        return html

    def add_rank_colors(self, text):
        lines = text.split("\n")
        colored_lines = []

        for line in lines:
            colored_line = line

            if "Rank:" in line:
                if "Excellent" in line:
                    colored_line = line.replace(
                        "Excellent", '<span class="rank-excellent">Excellent</span>'
                    )
                elif "Great" in line:
                    colored_line = line.replace(
                        "Great", '<span class="rank-great">Great</span>'
                    )
                elif "Good" in line:
                    colored_line = line.replace(
                        "Good", '<span class="rank-good">Good</span>'
                    )
                elif "Normal" in line:
                    colored_line = line.replace(
                        "Normal", '<span class="rank-normal">Normal</span>'
                    )
                elif "Average" in line:
                    colored_line = line.replace(
                        "Average", '<span class="rank-average">Average</span>'
                    )
                elif "Low" in line:
                    colored_line = line.replace(
                        "Low", '<span class="rank-low">Low</span>'
                    )
                elif "Manual" in line:
                    colored_line = line.replace(
                        "Manual", '<span class="rank-manual">Manual</span>'
                    )

            elif "Name:" in line:
                colored_line = line.replace(
                    "Name:", '<span class="info-name">Name:</span>'
                )
            elif "Module:" in line:
                colored_line = line.replace(
                    "Module:", '<span class="info-module">Module:</span>'
                )
            elif "Type:" in line:
                colored_line = line.replace(
                    "Type:", '<span class="info-type">Type:</span>'
                )
            elif "Platform:" in line:
                colored_line = line.replace(
                    "Platform:", '<span class="info-platform">Platform:</span>'
                )
            elif "Arch:" in line:
                colored_line = line.replace(
                    "Arch:", '<span class="info-arch">Arch:</span>'
                )
            elif "Author:" in line:
                colored_line = line.replace(
                    "Author:", '<span class="info-author">Author:</span>'
                )
            elif "License:" in line:
                colored_line = line.replace(
                    "License:", '<span class="info-license">License:</span>'
                )

            elif "Module options" in line or "Module parameters" in line:
                colored_line = (
                    f'<span style="color: #ff5555; font-weight: bold;">{line}</span>'
                )
            elif "Description:" in line:
                colored_line = (
                    f'<span style="color: #50fa7b; font-weight: bold;">{line}</span>'
                )

            colored_lines.append(colored_line)

        return "\n".join(colored_lines)

    def execute_command(self, command=None, args=None):
        import io
        import re

        if command is None:
            full_command = self.command_input.text().strip()
            if not full_command:
                return

            self.command_history.append(full_command)
            self.history_index = len(self.command_history)

            parts = full_command.split()
            command = parts[0]
            args = parts[1:] if len(parts) > 1 else []

            self.command_input.clear()

        if command != "use" or not args or "modules/" not in args[0]:
            self.append_output(f"> {command} {' '.join(args)}")

        try:
            if hasattr(self.framework, f"cmd_{command}"):
                output_buffer = io.StringIO()

                with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                    getattr(self.framework, f"cmd_{command}")(args)

                output = output_buffer.getvalue()
                if output.strip():
                    if command == "info":
                        clean_info = re.sub(r"\x1b\[[0-9;]*[mG]", "", output)
                        self.module_detail_info.setPlainText(clean_info)
                        self.main_tabs.setCurrentIndex(2)
                    else:
                        self.append_output(output)

                if command == "use":
                    self.on_module_loaded()
                elif command == "back":
                    self.on_module_unloaded()

            else:
                self.append_output(f"Unknown command: {command}")

        except Exception as e:
            self.append_output(f"Error executing command: {e}")

        self.update_session_info()

    def load_module_to_main_tab(self, module_path: str):
        try:
            args = [module_path]
            self.framework.cmd_use(args)

            if self.framework.loaded_module:
                display_path = module_path
                if display_path.startswith("modules/"):
                    display_path = display_path[8:]

                self.current_module_label.setText(display_path)
                self.current_module_label.setStyleSheet(
                    "color: #50fa7b; font-weight: bold;"
                )

                self.run_btn.setEnabled(True)
                self.back_btn.setEnabled(True)

                self.load_module_options()
                self.show_module_info_in_tab()
                self.update_session_info()

                if hasattr(self, "ai_tab") and self.ai_tab.api_key_input.text().strip():
                    self.ai_tab.run_agent_mode(self.framework.loaded_module)

                self.main_tabs.setCurrentIndex(0)

        except Exception as e:
            self.append_output(f"[red]Error loading module: {e}[/]")

    def on_module_unloaded(self):
        self.current_module = None
        self.current_module_label.setText("No module loaded module")
        self.current_module_label.setStyleSheet("color: #ff5555; font-weight: bold;")

        self.run_btn.setEnabled(False)
        self.back_btn.setEnabled(False)

        self.clear_options_tab()
        self.module_detail_info.clear()

    def on_module_loaded(self):
        if self.framework.loaded_module:
            module_full_path = self.framework.loaded_module.name

            if module_full_path.endswith(".py"):
                module_full_path = module_full_path[:-3]

            if module_full_path.startswith("modules/"):
                module_full_path = module_full_path[8:]

            self.current_module = module_full_path
            self.current_module_label.setText(module_full_path)
            self.current_module_label.setStyleSheet(
                "color: #50fa7b; font-weight: bold;"
            )

            self.run_btn.setEnabled(True)
            self.back_btn.setEnabled(True)

            self.load_module_options()
            self.show_module_info_in_tab()
            self.update_session_info()

            if hasattr(self, "ai_tab") and self.ai_tab.api_key_input.text().strip():
                self.ai_tab.run_agent_mode(self.framework.loaded_module)

    def load_module(self, module_path: str):
        import importlib.util

        if module_path not in self.modules:
            return None

        module_file = self.modules[module_path]

        spec = importlib.util.spec_from_file_location(
            module_path.replace("/", "_"), module_file
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        from bin.console import ModuleInstance
        inst = ModuleInstance(module_path, mod)

        if hasattr(mod, "OPTIONS"):
            for k, meta in mod.OPTIONS.items():
                if "default" in meta:
                    inst.options[k] = meta["default"]

        return inst

    def load_module_options(self):
        self.clear_options_tab()

        if not self.framework.loaded_module:
            return

        opts = self.framework.loaded_module.get_options()

        full_meta_src = None
        inner = getattr(self.framework.loaded_module, "module", None)
        if inner:
            full_meta_src = getattr(inner, "OPTIONS", None)
        if not full_meta_src:
            full_meta_src = getattr(self.framework.loaded_module, "OPTIONS", None)

        self.option_widgets = {}

        INPUT_STYLE = """
            QLineEdit, QComboBox {
                background: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                border-radius: 2px;
                padding: 3px 6px;
                font-size: 11px;
                min-height: 22px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #007acc;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #858585;
                width: 0; height: 0;
                margin-right: 6px;
            }
            QComboBox QAbstractItemView {
                background: #252526;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                selection-background-color: #094771;
                selection-color: #ffffff;
            }
        """

        for name, info in opts.items():
            value = str(info.get("value") or info.get("default") or "")
            required = info.get("required", False)
            description = info.get("description", "")

            choices = info.get("choices", None)
            if not choices and full_meta_src and name in full_meta_src:
                choices = full_meta_src[name].get("choices", None)

            label = QLabel(name)
            if required:
                label.setStyleSheet(
                    "color: #cccccc; font-size: 11px; font-weight: bold;"
                )
            else:
                label.setStyleSheet("color: #858585; font-size: 11px;")
            if description:
                label.setToolTip(description)

            if choices and isinstance(choices, (list, tuple)) and len(choices) > 0:
                widget = QComboBox()
                widget.setStyleSheet(INPUT_STYLE)
                widget.setMinimumWidth(220)
                for ch in choices:
                    widget.addItem(str(ch))
                idx = widget.findText(value)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
                widget.setToolTip(description)

                def _make_combo_updater(n):
                    def _upd(val):
                        self.framework.loaded_module.set_option(n, val)
                    return _upd

                widget.currentTextChanged.connect(_make_combo_updater(name))

            elif value.lower() in ("true", "false") and not choices:
                widget = QComboBox()
                widget.setStyleSheet(INPUT_STYLE)
                widget.setMinimumWidth(220)
                widget.addItem("True")
                widget.addItem("False")
                widget.setCurrentIndex(0 if value.lower() == "true" else 1)
                widget.setToolTip(description)

                def _make_bool_updater(n):
                    def _upd(val):
                        self.framework.loaded_module.set_option(n, val == "True")
                    return _upd

                widget.currentTextChanged.connect(_make_bool_updater(name))

            else:
                widget = QLineEdit(value)
                widget.setStyleSheet(INPUT_STYLE)
                widget.setMinimumWidth(220)
                if description:
                    widget.setPlaceholderText(description[:50])
                widget.setToolTip(description)

                def _make_text_updater(n):
                    def _upd(val):
                        if self.framework.loaded_module:
                            self.framework.loaded_module.set_option(n, val)
                    return _upd

                widget.textChanged.connect(_make_text_updater(name))

            self.options_layout.addRow(label, widget)
            self.option_widgets[name] = widget

        self.main_tabs.setCurrentIndex(1)

    def clear_options_tab(self):
        for i in reversed(range(self.options_layout.count())):
            item = self.options_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

    # ==================== GLITCH EFFECT ====================

    def start_title_glitch(self):
        if hasattr(self, "_glitch_timer"):
            self._glitch_timer.stop()

        self.original_title = self.windowTitle()
        glitch_chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンΣΨΩΔΘΛΞΠ"

        def glitch_step(count=0):
            if count > 12:
                self.setWindowTitle(self.original_title)
                return

            garbage = "".join(
                random.choice(glitch_chars) for _ in range(random.randint(5, 15))
            )
            glitch_title = self.original_title
            pos = random.randint(0, len(glitch_title))
            glitch_title = (
                glitch_title[:pos] + f"[red bold]{garbage}[/]" + glitch_title[pos:]
            )

            self.setWindowTitle(glitch_title)

            QTimer.singleShot(random.randint(80, 160), lambda: glitch_step(count + 1))

        glitch_step()

    def stop_title_glitch(self):
        if hasattr(self, "_glitch_timer"):
            self._glitch_timer.stop()
        if hasattr(self, "original_title"):
            self.setWindowTitle(self.original_title)

    # ==================== RUN MODULE ====================

    def run_module(self):
        if not self.framework.loaded_module:
            self.append_output("No module loaded")
            return

        for name, widget in self.option_widgets.items():
            if isinstance(widget, QComboBox):
                value = widget.currentText().strip()
            else:
                value = widget.text().strip()
            self.framework.session[name] = value
            if value:
                try:
                    self.framework.loaded_module.set_option(name, value)
                    self.append_output(f"Set {name} => {value}")
                except Exception as e:
                    self.append_output(f"Error setting {name}: {e}")

        if "reverse_tcp" in self.framework.loaded_module.name:
            self.framework.session["gui_sessions"] = {
                "dict": self.sessions,
                "lock": self.session_lock,
            }
            self.framework.session["gui_instance"] = self
            lhost = self.framework.session.get("LHOST", "0.0.0.0")
            lport = self.framework.session.get("LPORT", 4444)
            with self.listener_lock:
                listener_key = f"{lhost}:{lport}"
                if listener_key not in self.active_listeners:
                    self.active_listeners.append({
                        "lhost": lhost,
                        "lport": lport,
                        "status": "active",
                        "started": time.strftime("%H:%M:%S"),
                    })

        self.run_btn.setEnabled(True)
        self.run_btn.setText("STOP")
        self.run_btn.setProperty("action", "stop")

        self.update_session_info()
        if hasattr(self, "network_map_widget"):
            self.network_map_widget.stop_refresh()

        self.module_runner = ModuleRunner(self.framework, self.framework.loaded_module)
        self.module_runner.output.connect(self.append_output, Qt.ConnectionType.QueuedConnection)
        self.module_runner.finished.connect(self.on_module_finished)

        self.module_runner.output.connect(self.append_output, Qt.ConnectionType.QueuedConnection)

        self.module_runner.start()

        QTimer.singleShot(
            1500, lambda: self.safe_ui_update(self.sync_sessions_from_reverse_tcp)
        )
        QTimer.singleShot(2500, lambda: self.safe_ui_update(self.update_session_info))

    def on_module_finished(self):
        if hasattr(self, "network_map_widget"):
            self.network_map_widget.start_refresh()

        if self.module_runner:
            self.module_runner.quit()
            self.module_runner.wait(1500)
            self.module_runner = None

        self.run_btn.setEnabled(True)
        self.run_btn.setText("START")
        self.run_btn.setProperty("action", "run")

        self.append_output("\n[bold white]────────────────────────────────────────────────────────────────────────────────[/]")
        self.append_output("[bold matrix_cyan][+] Module execution finished[/]")
        self.append_output("[bold white]────────────────────────────────────────────────────────────────────────────────[/]\n")
        self.update_session_info()

        if (hasattr(self, "ai_tab") and
            hasattr(self.ai_tab, "api_key_input") and
            self.ai_tab.api_key_input.text().strip()):
            console_text = self.console_output.toPlainText()
            recent_output = console_text[-3500:].strip()
            if recent_output:
                self.ai_tab.inject_output(recent_output)
                try:
                    ai_index = self.main_tabs.indexOf(self.ai_tab)
                    if ai_index >= 0:
                        self.main_tabs.setCurrentIndex(ai_index)
                except:
                    pass

                self.ai_tab.send_message(
                    "Module telah selesai dijalankan. Analisis output berikut, "
                    "identifikasi temuan penting, potensi vulnerability, "
                    "dan rekomendasikan langkah selanjutnya:\n\n" + recent_output
                )

        self.module_runner = None

    def unload_module(self):
        self.execute_command("back", [])
        self._update_toolbar_module("", active=False)

    def quick_command(self, command):
        if command == "show_banner":
            self.cmd_show_banner()
        else:
            self.execute_command(command, [])

    # ==================== MODULE WATCHER ====================

    def start_module_watcher(self):
        try:
            project_root = Path(__file__).resolve().parent.parent
            module_root = str(project_root / "modules")

            if not Path(module_root).exists():
                self.append_output(
                    f"[yellow]Modules directory not found: {module_root}[/]"
                )
                return
            dirs_to_watch = [module_root]
            for d in Path(module_root).rglob("*"):
                if d.is_dir() and "__pycache__" not in d.parts:
                    dirs_to_watch.append(str(d.resolve()))
            dirs_to_watch = list(set(dirs_to_watch))
            self._module_watcher = QFileSystemWatcher(self)
            self._module_watcher.addPaths(dirs_to_watch)

            self._module_refresh_timer = QTimer(self)
            self._module_refresh_timer.setSingleShot(True)
            self._module_refresh_timer.setInterval(1500)
            self._module_refresh_timer.timeout.connect(self._do_auto_refresh_modules)

            self._module_watcher.directoryChanged.connect(self._on_module_dir_changed)
            self._module_watcher.fileChanged.connect(self._on_module_file_changed)

            self.append_output(
                f"[cyan]👁️ Module watcher aktif: {len(dirs_to_watch)} folder dipantau[/]"
            )
            self.append_output(f"[dim]Monitoring: {module_root}[/]")

        except Exception as e:
            self.append_output(f"[red]Module watcher error: {e}[/]")

    def _on_module_dir_changed(self, path):
        try:
            for d in Path(path).iterdir():
                if d.is_dir() and "__pycache__" not in d.parts:
                    dp = str(d.resolve())
                    if dp not in self._module_watcher.directories():
                        self._module_watcher.addPath(dp)
        except Exception:
            pass
        if not self._module_refresh_timer.isActive():
            self._module_refresh_timer.start()

    def _on_module_file_changed(self, path):
        if not self._module_refresh_timer.isActive():
            self._module_refresh_timer.start()

    def _do_auto_refresh_modules(self):
        try:
            self.framework.scan_modules()
            self.load_all_modules()
            total = len(self.framework.modules)
            if hasattr(self, "show_cyber_toast"):
                self.show_cyber_toast(
                    f"🔄 {total} modules terscan otomatis",
                    title="Module Auto-Refresh",
                    duration_ms=3000,
                    level="info",
                )
            self.append_output(f"[green]✓ Auto-refresh: {total} modules ditemukan[/]")
            self.update_session_info()
        except Exception as e:
            self.append_output(f"[red]Auto-refresh error: {e}[/]")
            import traceback
            self.append_output(f"[red]{traceback.format_exc()}[/]")

    def refresh_modules(self):
        self.framework.scan_modules()
        self.load_all_modules()
        self.append_output("Modules refreshed")

    def clear_console(self):
        self.console_output.clear()

    def change_font(self):
        font, ok = QFontDialog.getFont(self)
        if ok:
            self.console_output.setFont(font)
            self.module_detail_info.setFont(font)
            self.session_info.setFont(font)

            if hasattr(self, "module_tree"):
                def _set_cf(node):
                    node.setFont(0, font)
                    for j in range(node.childCount()):
                        _set_cf(node.child(j))

                cf_root = self.module_tree.invisibleRootItem()
                for i in range(cf_root.childCount()):
                    _set_cf(cf_root.child(i))

            for widget in getattr(self, "option_widgets", {}).values():
                widget.setFont(font)

            self.framework.session["font"] = font.family()
            self.framework.session["font_size"] = font.pointSize()

    def update_session_info(self):
        if not hasattr(self, "session_info"):
            return
        import socket, platform
        import requests
        from datetime import datetime

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "0.0.0.0"

        if (not self.framework.session.get("public_ip") or
            self.framework.session.get("public_ip") == "N/A"):
            try:
                import requests
                public_ip = requests.get("https://api.ipify.org", timeout=4).text
                self.framework.session["public_ip"] = public_ip
            except:
                public_ip = "N/A"
        else:
            public_ip = self.framework.session.get("public_ip", "N/A")

        user = self.framework.session.get("user", "unknown")

        with self.listener_lock:
            active_listeners_count = len(self.active_listeners)

        total_sess = len(self.sessions)
        online_sess = sum(
            1 for s in self.sessions.values() if s.get("status") == "alive"
        )

        target_os_stats = {"linux": 0, "windows": 0, "macos": 0, "unknown": 0}
        hostnames_list = []

        for sess_id, sess in self.sessions.items():
            os_type = sess.get("os", "unknown")
            status = sess.get("status", "alive")
            hostname = sess.get("hostname", "")

            if status == "alive":
                if os_type in target_os_stats:
                    target_os_stats[os_type] += 1
                else:
                    target_os_stats["unknown"] += 1

                if (hostname and hostname != "unknown" and
                    hostname not in hostnames_list):
                    hostnames_list.append(hostname)

        os_icons = {"linux": "🐧", "windows": "🪟", "macos": "🍎", "unknown": "💻"}
        os_display = []

        for os_type, count in target_os_stats.items():
            if count > 0:
                icon = os_icons.get(os_type, "💻")
                os_display.append(f"{icon}×{count}")

        os_summary = " | ".join(os_display) if os_display else "No active targets"
        hostnames_summary = ", ".join(hostnames_list[:3]) if hostnames_list else "None"
        if len(hostnames_list) > 3:
            hostnames_summary += f" +{len(hostnames_list)-3} more"

        uptime_sec = int(
            time.time() - self.framework.session.get("start_time", time.time())
        )
        d = uptime_sec // 86400
        h = (uptime_sec % 86400) // 3600
        m = (uptime_sec % 3600) // 60
        s = uptime_sec % 60
        uptime_str = f"{d}d {h:02d}h {m:02d}m" if d else f"{h:02d}h {m:02d}m {s:02d}s"

        proxy_status = "ONLINE" if self.proxy_enabled else "OFFLINE"
        proxy_color = "#50fa7b" if self.proxy_enabled else "#ff5555"
        proxy_detail = ""
        if self.proxy_enabled and self.current_proxy:
            p = self.current_proxy
            proxy_detail = f"{p['server']}:{p['port']} <small style='color:#ff8a80;'>({p['type'].upper()})</small>"

        current_module = self.current_module or "IDLE"
        if "reverse_tcp" in current_module.lower() and active_listeners_count > 0:
            current_module = f"🚀 {current_module}"

        usernames_list = []
        for sess_id, sess in self.sessions.items():
            status = sess.get("status", "alive")
            username = sess.get("username", "")
            if status == "alive" and username and username != "unknown":
                if username not in usernames_list:
                    usernames_list.append(username)

        usernames_summary = ", ".join(usernames_list[:3]) if usernames_list else "None"
        if len(usernames_list) > 3:
            usernames_summary += f" +{len(usernames_list)-3} more"
        total_sess = len(self.sessions)
        online_sess = sum(1 for s in self.sessions.values() if s.get("status") == "alive")
        html = f"""
        <div style="line-height:1.5;">
            <div style="text-align:center; color:#ff1744; font-size:11pt; letter-spacing:1px; margin-bottom:8px;">
                <b>SESSION CONTROL</b>
                <span style="color:#50fa7b; font-size:10pt;">[{online_sess}/{total_sess} online]</span>
            </div>
            <hr style="border:1px solid #7d0101; margin:8px 0;">

            <b style="color:#ff5252;">OPERATOR</b>     : <span style="color:#ffffff;">{user}</span><br>
            <b style="color:#ff5252;">LHOST</b>        : <span style="color:#f1fa8c;">{local_ip}</span><br>
            <b style="color:#ff5252;">PUBLIC IP</b>    : <span style="color:#ff79c6;">{public_ip}</span><br>
            <b style="color:#ff5252;">LISTENERS</b>    : <span style="color:#8be9fd;">{active_listeners_count} ACTIVE</span><br>
            <b style="color:#ff5252;">SESSIONS</b>     : <span style="color:#bd93f9;">{total_sess} TOTAL</span> | <span style="color:#50fa7b;">{online_sess} ALIVE</span><br>
            <b style="color:#ff5252;">TARGET OS</b>    : <span style="color:#ffffff;">{os_summary}</span><br>
            <b style="color:#ff5252;">HOSTNAMES</b>    : <span style="color:#50fa7b;">{hostnames_summary}</span><br>
            <b style="color:#ff5252;">MODULES</b>      : <span style="color:#ffffff;">{len(self.framework.modules)}</span><br>
            <b style="color:#ff5252;">CURRENT</b>      : <span style="color:#ff5552;">{current_module}</span><br>
            <b style="color:#ff5252;">PROXY</b>        : <span style="color:{proxy_color};">{proxy_status}</span> {proxy_detail}<br>
            <b style="color:#ff5252;">UPTIME</b>       : <span style="color:#ffb86c;">{uptime_str}</span><br>
            <b style="color:#ff5252;">PLATFORM</b>     : <span style="color:#6272a4;">{platform.system()} {platform.machine()}</span><br>
            
            <div style="margin-top:10px; font-size:8pt; color:#444; text-align:center;">
                Monitoring •
            </div>
        </div>
        """

        self.session_info.setHtml(html)

    def update_listener_status(self, active, lhost=None, lport=None):
        self.framework.session["LISTENER_ACTIVE"] = active

        if lhost:
            self.framework.session["LHOST"] = lhost
        if lport:
            self.framework.session["LPORT"] = lport

        self.update_session_info()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Q and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.close()
            return

        if event.key() == Qt.Key.Key_X and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.clear_console()
            return

        if event.key() == Qt.Key.Key_F5:
            self.refresh_modules()
            return

        if event.key() == Qt.Key.Key_P and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.show_proxy_settings()
            return

        if event.key() == Qt.Key.Key_E and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.enable_proxy()
            return

        if event.key() == Qt.Key.Key_A and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.open_ai_payload_dialog()
            return

        if event.key() == Qt.Key.Key_Up:
            if self.command_history and self.history_index > 0:
                self.history_index -= 1
                if hasattr(self, 'command_input') and self.command_input:
                    self.command_input.setText(self.command_history[self.history_index])
            return

        if event.key() == Qt.Key.Key_Down:
            if self.command_history and self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                if hasattr(self, 'command_input') and self.command_input:
                    self.command_input.setText(self.command_history[self.history_index])
            elif self.history_index == len(self.command_history) - 1:
                self.history_index = len(self.command_history)
                if hasattr(self, 'command_input') and self.command_input:
                    self.command_input.clear()
            return

        super().keyPressEvent(event)

    def closeEvent(self, event):
        """Cleanup saat aplikasi ditutup"""
        try:
            # ===== STOP LISTENER =====
            try:
                from modules.payload.reverse.reverse_tcp import stop_listener
                stop_listener()
                print("[+] Listener stopped on exit")
            except Exception as e:
                print(f"Listener stop error: {e}")
            
            # ===== STOP MODULE RUNNER =====
            if self.module_runner and self.module_runner.isRunning():
                self.module_runner.stop()
                self.module_runner.wait(1000)
            
            # ===== CLOSE BROWSER =====
            if hasattr(self, "browser") and self.browser:
                self.browser.deleteLater()
            
            # ===== CLEAR SESSIONS =====
            try:
                from modules.payload.reverse.reverse_tcp import SESSIONS, SESSIONS_LOCK
                with SESSIONS_LOCK:
                    SESSIONS.clear()
            except:
                pass
            
        except Exception as e:
            print(f"Cleanup error: {e}")

        event.accept()

    def open_in_browser(self, url):
        if self.browser:
            self.browser_controls_widget.show()
            self.browser.show()
            self.browser_placeholder.hide()
            self.open_browser_btn.setEnabled(False)
            self.close_browser_btn.setEnabled(True)
            self.append_output("[dim]Browser panel shown[/]")
            self.update_browser_buttons()
            return

        self.browser = QWebEngineView()
        self.browser.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, False)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, False)
        settings.setAttribute(QWebEngineSettings.AutoLoadIconsForPage, False)
        settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, False)
        settings.setAttribute(QWebEngineSettings.ScreenCaptureEnabled, False)

        if not self.browser or not self.browser.isVisible():
            self.open_browser_panel()
            QTimer.singleShot(500, lambda: self._load_url(url))
        else:
            self._load_url(url)

    def _load_url(self, url):
        try:
            self.browser.setUrl(QUrl(url))
            self.append_output(f"[green]Opened in browser: {url}[/]")
        except Exception as e:
            self.append_output(f"[red]Failed to open URL: {e}[/]")


def run_gui():
    import platform

    system = platform.system()

    if system == "Linux":
        wayland_display = os.environ.get("WAYLAND_DISPLAY")
        xdg_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

        if wayland_display and (
            "gnome" in xdg_desktop or "kde" in xdg_desktop or "mate" in xdg_desktop
        ):
            os.environ["QT_QPA_PLATFORM"] = "wayland"
            print("Using Wayland backend")
        else:
            os.environ["QT_QPA_PLATFORM"] = "xcb"
            print("Using XCB backend")

    elif system == "Windows":
        os.environ["QT_QPA_PLATFORM"] = "windows"
        print("Using Windows backend")

    elif system == "Darwin":
        os.environ["QT_QPA_PLATFORM"] = "cocoa"
        print("Using macOS Cocoa backend")
    else:
        os.environ["QT_QPA_PLATFORM"] = "xcb"
        print("Using fallback XCB backend")

    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox --disable-gpu-sandbox --disable-gpu --disable-software-rasterizer --disable-dev-shm-usage"
    os.environ["QT_QUICK_BACKEND"] = "software"
    os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"

    if platform.system() == "Linux":
        os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
        cert_paths = [
            "/etc/ssl/certs/ca-certificates.crt",
            "/etc/ssl/certs/ca-bundle.crt",
            "/etc/pki/tls/certs/ca-bundle.crt",
        ]
        for cert_path in cert_paths:
            if os.path.exists(cert_path):
                os.environ["SSL_CERT_FILE"] = cert_path
                os.environ["REQUESTS_CA_BUNDLE"] = cert_path
                break

    app = QApplication(sys.argv)
    app.setApplicationName("LazyFramework GUI")
    app.setApplicationVersion("2.0")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 10, 10))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 80, 80))
    palette.setColor(QPalette.ColorRole.Base, QColor(20, 5, 5))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(40, 15, 15))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 60, 60))
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, QColor(255, 100, 100))
    palette.setColor(QPalette.ColorRole.Button, QColor(80, 20, 20))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 120, 120))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 50, 50))
    palette.setColor(QPalette.ColorRole.Link, QColor(255, 80, 80))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(180, 30, 30))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(palette)

    win = LazyFrameworkGUI()
    win.show()

    def cleanup():
        try:
            win.closeEvent(None)
        except Exception:
            pass

    app.aboutToQuit.connect(cleanup)

    result = app.exec()
    sys.exit(result)


if __name__ == "__main__":
    run_gui()