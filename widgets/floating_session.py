from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QLineEdit, QPushButton, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
import re
import os
import base64
from pathlib import Path


class FloatingSessionWindow(QMainWindow):
    """Jendela terpisah untuk SessionTab yang di-detach - dengan output lengkap"""

    closed = pyqtSignal(str)   # session_id saat window ditutup

    def __init__(self, session_tab, parent=None):
        super().__init__(parent)
        self.session_id = session_tab.session_id
        self.session_tab = session_tab
        self.parent_gui = parent
        self.command_history = []
        self.history_index = -1
        self._pending_download = None
        self._last_output = ""

        self.setWindowTitle(f"📡 Session — {self.session_id}")
        self.setMinimumSize(600, 500)
        self.resize(800, 600)

        self.setStyleSheet("""
            QMainWindow {
                background: #1e1e1e;
            }
            QTextEdit {
                background: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px;
                font-family: 'DejaVu Sans Mono', 'Courier New', monospace;
            }
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
            QPushButton {
                background: #0e639c;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1177bb;
            }
            QPushButton#close_btn {
                background: transparent;
                color: #858585;
                font-size: 12px;
            }
            QPushButton#close_btn:hover {
                background: #c72e2e;
                color: #ffffff;
            }
            QLabel {
                color: #50fa7b;
                font-size: 10pt;
                font-weight: bold;
            }
        """)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # ── Header ──
        header_layout = QHBoxLayout()
        
        self.info_label = QLabel()
        header_layout.addWidget(self.info_label)
        header_layout.addStretch()
        
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
        header_layout.addWidget(self.upload_btn)
        
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
        header_layout.addWidget(self.download_btn)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("close_btn")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.clicked.connect(self.close)
        header_layout.addWidget(self.close_btn)
        
        layout.addLayout(header_layout)

        # ── Output Area ──
        # BUAT output_area BARU (tidak pakai dari session_tab)
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
        layout.addWidget(self.output_area, 3)

        # ── Command Input ──
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

        self.setCentralWidget(central)

        # Update info
        self._update_info()

        # Sembunyikan tombol float di mode floating
        if hasattr(self.session_tab, "float_btn"):
            self.session_tab.float_btn.hide()

        # ===== CONNECT SIGNAL DARI SESSION_TAB KE OUTPUT =====
        # Ini penting! Output dari session_tab harus diteruskan ke floating window
        if hasattr(self.session_tab, 'append_output'):
            # Simpan method asli
            self._original_append = self.session_tab.append_output
            # Override dengan method yang meneruskan ke floating window
            self.session_tab.append_output = self._forward_output
        
        # Juga terima sinyal dari command_sent
        if hasattr(self.session_tab, 'command_sent'):
            self.session_tab.command_sent.connect(self._on_command_sent)

        # Tampilkan pesan awal
        self._append_output(f"[*] Floating session: {self.session_id}")
        self._append_output(f"[*] Target: {self.session_tab.session_data.get('ip', '?')}:{self.session_tab.session_data.get('port', '?')}")
        self._append_output(f"[*] OS: {self.session_tab.session_data.get('os', 'unknown')}")
        self._append_output("[*] Type 'help' for commands")
        self._append_output("[*] Use ⬆ Upload / ⬇ Download for file transfer")
        self._append_output("")

    def _forward_output(self, text):
        """Forward output dari session_tab ke floating window"""
        if not text:
            return
        
        # ===== TAMBAHKAN CEK DUPLIKAT =====
        if text == self._last_output:
            return
        self._last_output = text
        
        # Tampilkan di floating window
        self._append_output(text)
        
        if hasattr(self, '_original_append') and self._original_append:
            try:
                self._original_append(text)
            except:
                pass

    def _update_info(self):
        ip = self.session_tab.session_data.get('ip', '?')
        port = self.session_tab.session_data.get('port', '?')
        os_type = self.session_tab.session_data.get('os', 'unknown')
        hostname = self.session_tab.session_data.get('hostname', '')
        os_icons = {
            'linux': '🐧', 'windows': '🪟', 'macos': '🍎',
            'kali': '🐉', 'ubuntu': '🔶', 'debian': '🌀',
            'unknown': '💻'
        }
        icon = os_icons.get(os_type, '💻')
        if hostname and hostname != 'unknown':
            self.info_label.setText(f"{icon} {hostname} | {ip}:{port} | {os_type.upper()}")
        else:
            self.info_label.setText(f"{icon} {ip}:{port} | {os_type.upper()}")

    def _clean_output(self, text):
        if not text:
            return ""

        # 1. Full ESC sequences
        text = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', text)
        text = re.sub(r'\x1b\][^\x07\x1b]*(\x07|\x1b\\)', '', text)
        text = re.sub(r'\x1b[=>()]', '', text)
        text = re.sub(r'\x1b.', '', text)  # sisa ESC + 1 char

        # 2. ANSI TANPA escape (paling sering di shell Kali)
        #    [0m  [1;32m  [30;44m  [;94m  [?2004h  dll
        text = re.sub(r'\[[\d;?]*[a-zA-Z]', '', text)
        text = re.sub(r'\[\?[0-9]+[hl]', '', text)

        # 3. Control chars (kecuali \n \t)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

        # 4. Cursor junk sisa: [C  [A  [K
        text = re.sub(r'\[[ABCDKHJ]', '', text)

        lines = text.split('\n')
        cleaned = []
        for line in lines:
            raw = line
            line = line.strip()

            # Skip kosong
            if not line:
                continue

            # Prompt Kali / oh-my-zsh / bash
            if re.match(r'^[┌└].*', line):
                continue
            if '㉿' in line or '┌──' in line or '└─' in line:
                continue
            if re.match(r'^[\s]*[#$%>]\s*$', line):
                continue
            if re.match(r'^.*@.*[:~].*[#$]\s*$', line):
                continue
            # root@kali / (root㉿kali)
            if re.search(r'\(.*㉿.*\)', line):
                continue
            if re.match(r'^\[.*@.*\].*', line) and len(line) < 80:
                continue

            # Baris yang cuma sisa kode warna
            if re.match(r'^[\[\]0-9;mC]*$', line):
                continue

            cleaned.append(line)

        # 5. Dedup baris berurutan
        result = []
        prev = None
        for line in cleaned:
            if line == prev:
                continue
            result.append(line)
            prev = line

        # 6. Dedup block besar (output ls dobel)
        text_out = '\n'.join(result)
        # Jika separuh kedua == separuh pertama → potong
        half = len(text_out) // 2
        if half > 40:
            a, b = text_out[:half].strip(), text_out[half:].strip()
            # normalisasi spasi untuk banding
            if re.sub(r'\s+', ' ', a) == re.sub(r'\s+', ' ', b):
                text_out = a

        return text_out.strip()

    def _append_output(self, text):
        """Append output ke floating window"""
        if not text:
            return
        
        # Cek apakah ini base64 untuk download
        if self._pending_download is not None:
            clean = self._clean_output(text)
            b64_candidate = re.sub(r"\s+", "", clean)
            if re.fullmatch(r"[A-Za-z0-9+/=]+", b64_candidate) and len(b64_candidate) > 16:
                self._pending_download["buffer"] += b64_candidate
                try:
                    data = base64.b64decode(self._pending_download["buffer"])
                    local = self._pending_download["local"]
                    with open(local, "wb") as f:
                        f.write(data)
                    self.output_area.append(f"[+] Saved → {local} ({len(data)} bytes)")
                    self._pending_download = None
                except Exception:
                    pass
                return

        # Tampilkan output
        if text.startswith('[') and text.endswith(']'):
            # Pesan sistem
            self.output_area.append(text)
        else:
            # Output dari command, bersihkan dulu
            clean_text = self._clean_output(text)
            if clean_text:
                self.output_area.append(clean_text)
            else:
                # Jika kosong setelah dibersihkan, tampilkan original
                self.output_area.append(text)
        
        # Scroll ke bawah
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_area.setTextCursor(cursor)

    def _send_command(self):
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return
        
        # Tampilkan command yang dikirim
        self._append_output(f"$ {cmd}")
        
        # Kirim command melalui session_tab
        if hasattr(self.session_tab, 'command_sent'):
            self.session_tab.command_sent.emit(self.session_id, cmd)
        else:
            # Fallback: langsung ke parent GUI
            if self.parent_gui and hasattr(self.parent_gui, '_on_session_command'):
                self.parent_gui._on_session_command(self.session_id, cmd)
        
        self.cmd_input.clear()
        self.command_history.append(cmd)
        self.history_index = len(self.command_history)

    def _on_command_sent(self, session_id, command):
        """Handle command_sent signal dari session_tab"""
        # Output sudah ditangani oleh _forward_output
        pass

    def _upload_file(self):
        if hasattr(self.session_tab, '_upload_file'):
            self.session_tab._upload_file()

    def _download_file(self):
        if hasattr(self.session_tab, '_download_file'):
            self.session_tab._download_file()

    def eventFilter(self, obj, event):
        if obj == self.cmd_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Up:
                if self.command_history and self.history_index > 0:
                    self.history_index -= 1
                    self.cmd_input.setText(self.command_history[self.history_index])
                return True
            elif event.key() == Qt.Key.Key_Down:
                if self.command_history and self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    self.cmd_input.setText(self.command_history[self.history_index])
                elif self.history_index == len(self.command_history) - 1:
                    self.history_index = len(self.command_history)
                    self.cmd_input.clear()
                return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        # Kembalikan append_output asli ke session_tab
        if hasattr(self, '_original_append') and self._original_append:
            self.session_tab.append_output = self._original_append
        
        self.closed.emit(self.session_id)
        event.accept()