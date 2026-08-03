#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Session Tab Widget - Untuk setiap session
Fitur: command shell, upload/download via base64 nowrap
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel, QSplitter,
    QFileDialog, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
import re
import os
import base64
from pathlib import Path


class SessionTab(QWidget):
    """Tab untuk satu session - seperti tab terminal"""

    command_sent = pyqtSignal(str, str)  # session_id, command
    tab_closed = pyqtSignal(str)         # session_id
    detach_requested = pyqtSignal(str)
    def __init__(self, session_id, session_data, parent=None):
        super().__init__(parent)
        self.session_id = session_id
        self.session_data = session_data
        self.command_history = []
        self.history_index = -1
        self._output_buffer = []
        self._last_output = ""
        self._pending_download = None
        

        self._build_ui()
        self._update_info()

    # ─────────────────────────────────────────────────────────────
    # Clean ANSI / prompt noise
    # ─────────────────────────────────────────────────────────────

    def _clean_output(self, text):
        if not text:
            return ""

        text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        text = re.sub(r'\x1b\][^\x07]*\x07', '', text)
        text = re.sub(r'\x1b[=><]', '', text)
        text = re.sub(r'\x1b[\[\]()]', '', text)
        text = re.sub(r'\x1b[P^]', '', text)
        text = re.sub(r'\[\?2004[hl]', '', text)

        lines = text.split('\n')
        cleaned_lines = []
        skip_prompt = False

        for line in lines:
            if not line.strip():
                cleaned_lines.append('')
                continue

            if re.match(r'^[┌└]──.*[㉿\$].*', line):
                skip_prompt = True
                continue

            if re.match(r'^[;\[\]0-9]*[┌└]──.*', line):
                skip_prompt = True
                continue

            if re.match(r'^[;\[\]0-9]*\[.*@.*\].*', line):
                skip_prompt = True
                continue

            if re.match(r'^[\s]*[#$]\s*$', line):
                skip_prompt = True
                continue

            if re.match(r'^[;\[\]0-9]*└─.*', line):
                skip_prompt = True
                continue

            if skip_prompt and line.strip() and not re.match(r'^[;\[\]0-9]*', line):
                skip_prompt = False

            if not skip_prompt:
                clean_line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)
                clean_line = re.sub(r'\[\?2004[hl]', '', clean_line)
                clean_line = re.sub(r'\[[0-9;]*[a-zA-Z]', '', clean_line)
                clean_line = re.sub(r'\[[0-9;]*m', '', clean_line)
                clean_line = re.sub(r'\[[0-9;]*[a-zA-Z]', '', clean_line)
                clean_line = re.sub(r'^[;\[\]0-9]*m', '', clean_line)
                clean_line = re.sub(r'^[;\[\]0-9]*└─.*', '', clean_line)
                clean_line = re.sub(r'^[;\[\]0-9]*┌──.*', '', clean_line)
                clean_line = re.sub(r'^[;\[\]0-9]*\[.*@.*\].*', '', clean_line)

                if clean_line.strip():
                    cleaned_lines.append(clean_line.strip())
                else:
                    cleaned_lines.append('')

        result = '\n'.join(cleaned_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)
        result = result.strip()

        lines = result.split('\n')
        unique_lines = []
        last_line = None
        for line in lines:
            if line == last_line:
                continue
            if re.match(r'^[#$]\s*$', line):
                continue
            unique_lines.append(line)
            last_line = line

        return '\n'.join(unique_lines)

    # ─────────────────────────────────────────────────────────────
    # UI
    # ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # ── Header ──
        header = QHBoxLayout()

        self.info_label = QLabel()
        self.info_label.setStyleSheet(
            "color: #50fa7b; font-size: 10pt; font-weight: bold;"
        )
        header.addWidget(self.info_label)

        header.addStretch()

        # Upload
        self.upload_btn = QPushButton("⬆ Upload")
        self.upload_btn.setFixedHeight(22)
        self.upload_btn.setToolTip("Upload file ke target (base64 nowrap)")
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background: #1f6feb;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 2px 10px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background: #388bfd; }
        """)
        self.upload_btn.clicked.connect(self._upload_file)
        header.addWidget(self.upload_btn)

        # Download
        self.download_btn = QPushButton("⬇ Download")
        self.download_btn.setFixedHeight(22)
        self.download_btn.setToolTip("Download file dari target (base64 nowrap)")
        self.download_btn.setStyleSheet("""
            QPushButton {
                background: #238636;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 2px 10px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background: #2ea043; }
        """)
        self.download_btn.clicked.connect(self._download_file)
        header.addWidget(self.download_btn)

        # Float / Detach button
        self.float_btn = QPushButton("⧉")
        self.float_btn.setFixedSize(22, 22)
        self.float_btn.setToolTip("Float / Detach tab")
        self.float_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #858585;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #3c3c3c;
                color: #ffffff;
                border-radius: 3px;
            }
        """)
        self.float_btn.clicked.connect(
            lambda: self.detach_requested.emit(self.session_id)
        )
        header.addWidget(self.float_btn)

        # Close
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #858585;
                border: none;
                font-size: 10px;
            }
            QPushButton:hover {
                background: #c72e2e;
                color: #ffffff;
                border-radius: 3px;
            }
        """)
        self.close_btn.clicked.connect(
            lambda: self.tab_closed.emit(self.session_id)
        )
        header.addWidget(self.close_btn)

        layout.addLayout(header)

        # ── Output ──
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("DejaVu Sans Mono", 10))
        self.output_area.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px;
                font-family: 'DejaVu Sans Mono', 'Courier New', monospace;
            }
        """)

        self._append_output(f"[*] Session {self.session_id} connected")
        self._append_output(
            f"[*] Target: {self.session_data.get('ip', '?')}:"
            f"{self.session_data.get('port', '?')}"
        )
        self._append_output(
            f"[*] OS: {self.session_data.get('os', 'unknown')}"
        )
        self._append_output("[*] Type 'help' for commands")
        self._append_output("[*] Use ⬆ Upload / ⬇ Download for file transfer")
        self._append_output("")

        layout.addWidget(self.output_area, 3)

        # ── Command input ──
        input_layout = QHBoxLayout()
        input_layout.setSpacing(5)

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText(f"Command for {self.session_id}...")
        self.cmd_input.setFont(QFont("DejaVu Sans Mono", 10))
        self.cmd_input.setStyleSheet("""
            QLineEdit {
                background: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                padding: 5px 8px;
                font-family: 'DejaVu Sans Mono', 'Courier New', monospace;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
        """)
        self.cmd_input.returnPressed.connect(self._send_command)
        self.cmd_input.installEventFilter(self)

        input_layout.addWidget(self.cmd_input, 3)

        self.send_btn = QPushButton("▶ Send")
        self.send_btn.setFixedWidth(70)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: #0e639c;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1177bb;
            }
        """)
        self.send_btn.clicked.connect(self._send_command)
        input_layout.addWidget(self.send_btn)

        layout.addLayout(input_layout)

    def _update_info(self):
        ip = self.session_data.get('ip', '?')
        port = self.session_data.get('port', '?')
        os_type = self.session_data.get('os', 'unknown')
        os_icons = {
            'linux': '🐧',
            'windows': '🪟',
            'macos': '🍎',
            'unknown': '💻'
        }
        icon = os_icons.get(os_type, '💻')
        self.info_label.setText(f"{icon} {ip}:{port} | {os_type.upper()}")

    # ─────────────────────────────────────────────────────────────
    # Output helpers
    # ─────────────────────────────────────────────────────────────

    def _append_output(self, text):
        if not text:
            return
        clean_text = self._clean_output(text) if text else ""
        if clean_text:
            self.output_area.append(clean_text)
        else:
            self.output_area.append(text)

        cursor = self.output_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output_area.setTextCursor(cursor)

    def append_output(self, text):
        """Dipanggil dari luar (GUI) saat ada output session"""
        if not text or not text.strip():
            return

        # Tangkap base64 untuk download
        if self._pending_download is not None:
            clean = self._clean_output(text)
            b64_candidate = re.sub(r"\s+", "", clean)

            if re.fullmatch(r"[A-Za-z0-9+/=]+", b64_candidate) and len(b64_candidate) > 16:
                self._pending_download["buffer"] += b64_candidate
                self._append_output(
                    f"[*] Received {len(b64_candidate)} base64 chars "
                    f"(total {len(self._pending_download['buffer'])})"
                )
                try:
                    data = base64.b64decode(self._pending_download["buffer"])
                    local = self._pending_download["local"]
                    with open(local, "wb") as f:
                        f.write(data)
                    self._append_output(
                        f"[+] Saved → {local} ({len(data)} bytes)"
                    )
                    self._pending_download = None
                except Exception:
                    # belum lengkap / padding kurang, tunggu chunk berikutnya
                    pass
                return

        clean_text = self._clean_output(text)
        if clean_text:
            self._append_output(clean_text)
        else:
            self._append_output(text)

    # ─────────────────────────────────────────────────────────────
    # Command
    # ─────────────────────────────────────────────────────────────

    def _send_command(self):
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return

        self._append_output(f"$ {cmd}")
        self.command_sent.emit(self.session_id, cmd)
        self.cmd_input.clear()

        self.command_history.append(cmd)
        self.history_index = len(self.command_history)

    # ─────────────────────────────────────────────────────────────
    # Upload (local → remote) via base64 nowrap
    # ─────────────────────────────────────────────────────────────

    def _upload_file(self):
        local_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select file to upload",
            str(Path.home()),
            "All Files (*.*)"
        )
        if not local_path:
            return

        remote_path, ok = QInputDialog.getText(
            self,
            "Remote Path",
            "Path di target:\n"
            "(contoh Linux: /tmp/file.bin)\n"
            "(contoh Windows: C:\\Users\\Public\\file.exe)",
            text=os.path.basename(local_path)
        )
        if not ok or not remote_path.strip():
            return

        remote_path = remote_path.strip()

        try:
            with open(local_path, "rb") as f:
                data = f.read()

            size = len(data)
            # Batasi ukuran agar tidak merusak shell buffer
            MAX_SIZE = 200 * 1024  # 200 KB
            if size > MAX_SIZE:
                reply = QMessageBox.question(
                    self,
                    "File besar",
                    f"File {size:,} bytes. Transfer base64 sekali jalan "
                    f"bisa gagal di shell.\nLanjutkan tetap?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            b64 = base64.b64encode(data).decode("ascii")  # nowrap

            self._append_output(
                f"[*] Uploading {os.path.basename(local_path)} "
                f"({size} bytes) → {remote_path}"
            )

            os_type = (self.session_data.get("os") or "unknown").lower()

            if "win" in os_type:
                # PowerShell – FromBase64String
                # Escape single quote di path
                rp = remote_path.replace("'", "''")
                cmd = (
                    f'powershell -nop -ep bypass -c '
                    f'"[IO.File]::WriteAllBytes(\'{rp}\', '
                    f'[Convert]::FromBase64String(\'{b64}\'))"'
                )
            else:
                # Linux: echo + base64 -d
                # Gunakan single-quote agar karakter spesial aman
                cmd = f"echo '{b64}' | base64 -d > '{remote_path}'"

            preview = cmd[:90] + ("..." if len(cmd) > 90 else "")
            self._append_output(f"$ {preview}")
            self.command_sent.emit(self.session_id, cmd)
            self._append_output("[*] Upload command sent (base64 nowrap)")

        except Exception as e:
            self._append_output(f"[!] Upload error: {e}")

    # ─────────────────────────────────────────────────────────────
    # Download (remote → local) via base64 nowrap
    # ─────────────────────────────────────────────────────────────

    def _download_file(self):
        remote_path, ok = QInputDialog.getText(
            self,
            "Remote Path",
            "Path file di target yang mau di-download:"
        )
        if not ok or not remote_path.strip():
            return

        remote_path = remote_path.strip()
        default_name = os.path.basename(remote_path) or "downloaded.bin"

        local_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save downloaded file",
            str(Path.home() / default_name),
            "All Files (*.*)"
        )
        if not local_path:
            return

        self._pending_download = {
            "remote": remote_path,
            "local": local_path,
            "buffer": "",
        }

        os_type = (self.session_data.get("os") or "unknown").lower()

        if "win" in os_type:
            rp = remote_path.replace("'", "''")
            cmd = (
                f'powershell -nop -ep bypass -c '
                f'"[Convert]::ToBase64String('
                f'[IO.File]::ReadAllBytes(\'{rp}\'))"'
            )
        else:
            # -w 0 = nowrap; fallback tr -d '\n'
            cmd = (
                f'base64 -w 0 "{remote_path}" 2>/dev/null || '
                f'base64 "{remote_path}" | tr -d "\\n"'
            )

        self._append_output(f"[*] Downloading {remote_path} ...")
        self._append_output(f"$ {cmd}")
        self.command_sent.emit(self.session_id, cmd)
        self._append_output("[*] Waiting for base64 output...")

    # ─────────────────────────────────────────────────────────────
    # Keyboard history
    # ─────────────────────────────────────────────────────────────

    def eventFilter(self, obj, event):
        if obj == self.cmd_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Up:
                if self.command_history and self.history_index > 0:
                    self.history_index -= 1
                    self.cmd_input.setText(
                        self.command_history[self.history_index]
                    )
                return True
            elif event.key() == Qt.Key.Key_Down:
                if (self.command_history and
                        self.history_index < len(self.command_history) - 1):
                    self.history_index += 1
                    self.cmd_input.setText(
                        self.command_history[self.history_index]
                    )
                elif self.history_index == len(self.command_history) - 1:
                    self.history_index = len(self.command_history)
                    self.cmd_input.clear()
                return True
        return super().eventFilter(obj, event)
