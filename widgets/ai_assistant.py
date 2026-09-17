#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LazyFramework — AI Assistant Widget with Auto Agent (Fixed Session Detection)
"""

import json
import requests
import threading
import re
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel, QComboBox,
    QFrame, QScrollArea, QCheckBox, QProgressBar,
    QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread, QTimer
from PyQt6.QtGui import QFont, QTextCursor

# ─── PROVIDER CONFIGURATION ────────────────────────────────────────────────────

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
ZENMUX_URL = "https://zenmux.ai/api/v1"

PROVIDERS = {
    "OpenRouter": {
        "url": OPENROUTER_URL,
        "auth_url": "https://openrouter.ai/api/v1/auth/key",
        "models": [
            "deepseek/deepseek-v4-flash:free",
            "google/gemma-4-31b-it:free",
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
            "meta-llama/llama-3.3-8b-instruct:free",
            "microsoft/phi-3.5-mini-128k-instruct:free",
            "qwen/qwen-2.5-72b-instruct:free",
            "openai/gpt-4o-mini",
        ],
    },
    "ZenMux": {
        "url": ZENMUX_URL,
        "auth_url": "https://zenmux.ai/api/v1/models",
        "models": [
            "x-ai/grok-4.5-free",
            "x-ai/grok-4.3",
            "gpt-4o-mini",
            "gpt-4o",
            "claude-3-5-sonnet",
            "claude-3-5-haiku",
            "anthropic/claude-fable-5",
            "deepseek-chat",
            "deepseek-reasoner",
            "gemini-2.0-flash",
            "gemini-2.5-pro",
        ],
    },
}

DEFAULT_MODELS = {
    "OpenRouter": "deepseek/deepseek-v4-flash:free",
    "ZenMux": "gpt-4o-mini",
}

# ========== MODIFIED SYSTEM PROMPT - FOR LEGITIMATE TESTING ==========
SYSTEM_PROMPT = """You are LazyAI, a penetration testing assistant embedded in the Lazy Framework.

Your role:
- Assist with legitimate, authorized security testing and educational purposes
- Provide technical code examples for security research
- Explain security concepts and best practices
- Help with CTF challenges and lab environments
- Generate code for authorized testing scenarios

IMPORTANT GUIDELINES:
1. ONLY provide code for legitimate, authorized testing
2. Include clear warnings about proper authorization requirements
3. Focus on educational content and security awareness
4. Do NOT assist with illegal activities or unauthorized access

When providing code examples:
- Add comments explaining security implications
- Include error handling and best practices
- Mention that proper authorization is required
- Provide educational context

You CAN help with:
- Penetration testing code (for authorized environments)
- Security research and CTF challenges
- Educational networking/security examples
- Reverse engineering for security research
- Exploit development for authorized testing
- Privilege escalation for authorized testing
- Payload generation for authorized testing

You CANNOT help with:
- Unauthorized access or illegal activities
- Creating malware for malicious purposes
- Identity theft or fraud
- Bypassing security without authorization

Always include a warning about requiring explicit authorization for any testing.
"""

# ─── Auto Agent Worker ──────────────────────────────────────────────────────────
class AutoAgentWorker(QObject):
    """Worker thread untuk Auto Agent - dengan session detection yang tepat"""
    output = pyqtSignal(str)
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool)
    error = pyqtSignal(str)
    session_detected = pyqtSignal(str)
    reset_progress = pyqtSignal()
    
    def __init__(self, framework, gui, ai_assistant, module_path=None, auto_chain=True):
        super().__init__()
        self.framework = framework
        self.gui = gui
        self.ai = ai_assistant
        self.module_path = module_path
        self.auto_chain = auto_chain
        self.running = True
        self.max_depth = 2
        self.current_depth = 0
        self.detected_sessions = []
        self.executed_modules = []
        
        # Simpan session count SEBELUM eksekusi
        self.initial_session_count = 0
        self.initial_session_ids = set()
        
    def stop(self):
        self.running = False
        self.reset_progress.emit()
        
    def run(self):
        """Main auto agent execution"""
        try:
            self.output.emit("[bold cyan]╔══════════════════════════════════════════╗[/]")
            self.output.emit("[bold cyan]║      🤖 AUTO AGENT ACTIVATED            ║[/]")
            self.output.emit("[bold cyan]╚══════════════════════════════════════════╝[/]")
            self.output.emit("")
            
            # ── STEP 1: Catat session awal ──
            self._capture_initial_sessions()
            
            # ── STEP 2: Auto-detect target ──
            self.output.emit("[yellow]📡 Phase 1: Auto-detecting target...[/]")
            self.progress.emit(10)
            self.status.emit("Auto-detecting target...")
            
            if self.framework.loaded_module and not self.module_path:
                self.module_path = self.framework.loaded_module.name
                self.output.emit(f"[green]✓ Using loaded module: {self.module_path}[/]")
            elif not self.module_path:
                exploit_modules = self._find_exploit_modules()
                if exploit_modules:
                    self.module_path = exploit_modules[0]
                    self.output.emit(f"[green]✓ Auto-selected: {self.module_path}[/]")
                else:
                    self.error.emit("No exploit modules found.")
                    self.reset_progress.emit()
                    return
            
            if not self.running:
                self.reset_progress.emit()
                return
                
            # ── STEP 3: Load module ──
            if not self._load_module(self.module_path):
                self.reset_progress.emit()
                return
                
            self.progress.emit(25)
            
            # ── STEP 4: AI analyzes module ──
            self.output.emit("[yellow]🔍 Phase 2: AI analyzing module...[/]")
            self.status.emit("AI analyzing module...")
            self.progress.emit(30)
            
            recommendations = self._get_ai_recommendations()
            
            if not self.running:
                self.reset_progress.emit()
                return
                
            # ── STEP 5: Apply recommendations ──
            if recommendations:
                self.output.emit("[green]✓ Applying AI recommendations...[/]")
                self._apply_recommendations(recommendations)
            else:
                self.output.emit("[yellow]⚠️ No AI recommendations, using defaults[/]")
                
            self.progress.emit(50)
            
            # ── STEP 6: Execute module ──
            self.output.emit("[yellow]⚡ Phase 3: Executing exploit...[/]")
            self.status.emit("Executing module...")
            self.progress.emit(60)
            
            # Catat ulang session sebelum eksekusi (untuk berjaga-jaga)
            self._capture_initial_sessions()
            
            success = self._execute_module()
            
            if not self.running:
                self.reset_progress.emit()
                return
                
            self.progress.emit(80)
            
            # ── STEP 7: Wait for NEW sessions only ──
            self.output.emit("[yellow]⏳ Phase 4: Waiting for new session...[/]")
            self.status.emit("Waiting for session...")
            
            session_id = self._wait_for_new_session()
            
            if session_id:
                self.output.emit(f"[bold green]🎯 NEW SESSION DETECTED! ID: {session_id}[/]")
                self.session_detected.emit(session_id)
                
                if self.gui:
                    QTimer.singleShot(100, self.gui.update_sessions_ui)
                    QTimer.singleShot(200, lambda: self.gui.main_tabs.setCurrentIndex(4))
                
                if self.auto_chain and self.current_depth < self.max_depth:
                    self._auto_chain_post_exploit(session_id)
            else:
                self.output.emit("[yellow]⚠️ No new session detected.[/]")
                
            self.progress.emit(100)
            self.status.emit("✅ Completed")
            self.output.emit("")
            self.output.emit("[bold green]✅ Auto Agent completed![/]")
            self.finished.emit(True)
            
            QTimer.singleShot(3000, self.reset_progress.emit)
            
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False)
            self.reset_progress.emit()
            
    def _capture_initial_sessions(self):
        """Capture sessions yang sudah ada SEBELUM eksekusi"""
        self.initial_session_ids = set()
        self.initial_session_count = 0
        
        # Capture dari GUI sessions
        if self.gui and hasattr(self.gui, 'sessions'):
            self.initial_session_ids = set(self.gui.sessions.keys())
            self.initial_session_count = len(self.initial_session_ids)
            
        # Capture dari reverse_tcp module
        try:
            from modules.payload.reverse.reverse_tcp import SESSIONS
            if SESSIONS:
                self.initial_session_ids.update(SESSIONS.keys())
                self.initial_session_count = len(self.initial_session_ids)
        except:
            pass
            
        self.output.emit(f"[dim]📌 Existing sessions: {self.initial_session_count}[/]")
            
    def _get_new_sessions(self):
        """Get sessions that are NEW (not in initial list)"""
        current_sessions = set()
        
        # Get from GUI
        if self.gui and hasattr(self.gui, 'sessions'):
            current_sessions.update(self.gui.sessions.keys())
            
        # Get from reverse_tcp
        try:
            from modules.payload.reverse.reverse_tcp import SESSIONS
            if SESSIONS:
                current_sessions.update(SESSIONS.keys())
        except:
            pass
            
        # Return only NEW sessions
        return current_sessions - self.initial_session_ids
        
    def _find_exploit_modules(self):
        """Find exploit modules (EXCLUDE reverse_tcp and payloads)"""
        exploits = []
        for key in self.framework.modules.keys():
            if "/exploit/" in key.lower():
                if "reverse_tcp" not in key.lower() and "payload" not in key.lower():
                    exploits.append(key)
        return exploits
        
    def _load_module(self, module_path):
        try:
            self.output.emit(f"[dim]Loading: {module_path}[/]")
            self.progress.emit(15)
            
            args = [module_path]
            if hasattr(self.framework, 'cmd_use'):
                self.framework.cmd_use(args)
            else:
                self.framework.use(module_path)
                
            if self.framework.loaded_module:
                self.output.emit(f"[green]✓ Module loaded[/]")
                self.executed_modules.append(module_path)
                
                if self.gui and hasattr(self.gui, 'ai_tab'):
                    QTimer.singleShot(100, lambda: self.gui.ai_tab.run_agent_mode(
                        self.framework.loaded_module
                    ))
                return True
            else:
                self.error.emit("Failed to load module")
                return False
                
        except Exception as e:
            self.error.emit(f"Load error: {e}")
            return False
            
    def _get_ai_recommendations(self):
        if not self.framework.loaded_module:
            return {}
            
        mod = self.framework.loaded_module
        options = {}
        
        if hasattr(mod, 'get_options'):
            options = mod.get_options()
        elif hasattr(mod, 'OPTIONS'):
            options = mod.OPTIONS
            
        if not options:
            return {}
            
        options_text = []
        for name, meta in options.items():
            if isinstance(meta, dict):
                default = meta.get('default', '')
                desc = meta.get('description', '')
                required = meta.get('required', False)
                options_text.append(f"  {name}: {default} (required: {required}) - {desc}")
                
        prompt = f"""
Analyze this penetration testing module and suggest optimal values for authorized testing:

Module: {mod.name}

Options:
{chr(10).join(options_text)}

Provide recommendations in JSON format:
{{"OPTION_NAME": "suggested_value", ...}}
"""
        
        self.output.emit("[dim]🤔 AI analyzing options...[/]")
        
        response = self._get_ai_response(prompt)
        
        if not response:
            return {}
            
        try:
            json_match = re.search(r'\{[^{}]*\}', response)
            if json_match:
                recommendations = json.loads(json_match.group())
                self.output.emit(f"[green]✓ {len(recommendations)} recommendations[/]")
                for name, value in recommendations.items():
                    self.output.emit(f"  • {name} = {value}")
                return recommendations
        except:
            pass
            
        return {}
        
    def _get_ai_response(self, prompt):
        if not self.ai or not hasattr(self.ai, 'send_message'):
            return None
            
        response_ready = threading.Event()
        response_data = [None]
        
        def on_token(token):
            if response_data[0] is None:
                response_data[0] = ""
            response_data[0] += token
            
        def on_done():
            response_ready.set()
            
        if hasattr(self.ai, 'token_received'):
            self.ai.token_received.connect(on_token)
        if hasattr(self.ai, 'finished'):
            self.ai.finished.connect(on_done)
            
        self.ai.send_message(prompt)
        response_ready.wait(timeout=30)
        
        if hasattr(self.ai, 'token_received'):
            self.ai.token_received.disconnect(on_token)
        if hasattr(self.ai, 'finished'):
            self.ai.finished.disconnect(on_done)
            
        return response_data[0]
        
    def _apply_recommendations(self, recommendations):
        if not self.framework.loaded_module:
            return
            
        mod = self.framework.loaded_module
        
        for name, value in recommendations.items():
            try:
                if hasattr(mod, 'set_option'):
                    mod.set_option(name, value)
                elif hasattr(mod, 'options') and isinstance(mod.options, dict):
                    mod.options[name] = value
                self.output.emit(f"[dim]  ✓ {name} = {value}[/]")
            except Exception as e:
                self.output.emit(f"[yellow]  ✗ {name}: {e}[/]")
                
    def _execute_module(self):
        if not self.framework.loaded_module:
            return False
            
        self.progress.emit(65)
        
        if self.gui and hasattr(self.gui, 'run_module'):
            self._start_time = time.time()
            QTimer.singleShot(100, self.gui.run_module)
            self.output.emit("[dim]▶ Module running...[/]")
            return True
        else:
            try:
                result = self.framework.loaded_module.run(self.framework.session)
                self.output.emit(f"[dim]✓ Result: {result}[/]")
                return True
            except Exception as e:
                self.error.emit(f"Execution error: {e}")
                return False
                
    def _wait_for_new_session(self):
        """Wait for NEW sessions only (ignore existing ones)"""
        self.output.emit("[dim]⏳ Waiting for new session (max 30s)...[/]")
        self.progress.emit(85)
        
        timeout = 30
        start = time.time()
        detected_session = None
        
        # Re-capture initial sessions (in case new ones appeared during load)
        self._capture_initial_sessions()
        
        while time.time() - start < timeout:
            if not self.running:
                return None
                
            # Get NEW sessions only
            new_sessions = self._get_new_sessions()
            
            if new_sessions:
                # Get the first new session
                detected_session = list(new_sessions)[0]
                self.output.emit(f"[green]✓ New session detected![/]")
                return detected_session
                
            time.sleep(0.5)
            
        return detected_session
        
    def _auto_chain_post_exploit(self, session_id):
        self.current_depth += 1
        
        if self.current_depth > self.max_depth:
            self.output.emit("[yellow]⚠️ Max depth reached[/]")
            return
            
        self.output.emit("")
        self.output.emit("[yellow]🔗 Auto-chaining to post-exploitation...[/]")
        self.status.emit("Auto-chaining...")
        self.progress.emit(90)
        
        # Find post modules (EXCLUDE reverse_tcp)
        post_modules = []
        for key in self.framework.modules.keys():
            if "/post/" in key.lower() or "/privesc/" in key.lower():
                if "reverse_tcp" not in key.lower():
                    if key not in self.executed_modules:
                        post_modules.append(key)
                    
        if not post_modules:
            self.output.emit("[yellow]No post modules found[/]")
            return
            
        next_module = post_modules[0]
        self.output.emit(f"[cyan]→ Auto-loading: {next_module}[/]")
        
        self.module_path = next_module
        self._load_module(next_module)
        
        if not self.running:
            return
            
        recommendations = self._get_ai_recommendations()
        if recommendations:
            self._apply_recommendations(recommendations)
            
        self.output.emit(f"[cyan]▶ Executing post module...[/]")
        self._execute_module()
        
        time.sleep(2)
        self.output.emit("[green]✓ Auto-chain completed![/]")


# ─── AIAssistantWidget ──────────────────────────────────────────────────────
class AIAssistantWidget(QWidget):

    STATUS_DISCONNECTED = "disconnected"
    STATUS_CONNECTING = "connecting"
    STATUS_CONNECTED = "connected"
    STATUS_AUTH_FAILED = "auth_failed"
    STATUS_CHANNEL_ACTIVE = "channel_active"
    STATUS_AGENT_RUNNING = "agent_running"

    def __init__(self, framework=None, parent=None):
        super().__init__(parent)
        self.framework = framework
        self.gui = parent
        self.chat_history = []
        self.worker = None
        self.worker_thread = None
        self._ai_buf = ""
        self.current_status = self.STATUS_DISCONNECTED
        self._worker_lock = threading.Lock()
        self.agent_running = False
        
        self._build_ui()
        self._load_api_key()
        
        if self.gui:
            self._setup_auto_agent_monitor()

    def _setup_auto_agent_monitor(self):
        """Monitor module load untuk auto-start agent"""
        if hasattr(self.gui, 'module_tree'):
            self.gui.module_tree.itemDoubleClicked.connect(
                self._on_module_loaded_auto
            )
            
        if hasattr(self.gui, 'framework'):
            original_cmd_use = self.gui.framework.cmd_use
            
            def wrapped_cmd_use(args):
                result = original_cmd_use(args)
                if self.gui.framework.loaded_module:
                    QTimer.singleShot(500, self._on_module_loaded_auto)
                return result
                
            self.gui.framework.cmd_use = wrapped_cmd_use

    def _on_module_loaded_auto(self, item=None):
        """Auto trigger agent when module is loaded - SKIP reverse_tcp"""
        if not self.auto_agent_cb.isChecked():
            return
            
        if self.current_status not in [self.STATUS_CONNECTED, self.STATUS_CHANNEL_ACTIVE]:
            return
            
        if self.agent_running:
            return
            
        if self.framework and self.framework.loaded_module:
            module_path = self.framework.loaded_module.name
            
            # SKIP reverse_tcp modules - jangan auto-trigger
            if "reverse_tcp" in module_path.lower() or "payload" in module_path.lower():
                self._append_bubble("system", f"[dim]⏭️ Skipping auto-agent for: {module_path}[/]")
                return
                
            QTimer.singleShot(300, lambda: self._auto_start_agent(module_path))
            
    def _auto_start_agent(self, module_path):
        """Auto start agent - SKIP reverse_tcp"""
        if not self.auto_agent_cb.isChecked():
            return
            
        if self.agent_running:
            return
            
        # Double-check: skip reverse_tcp
        if "reverse_tcp" in module_path.lower() or "payload" in module_path.lower():
            return
            
        self._append_bubble("system", f"🤖 Auto Agent triggered on: {module_path}")
        self.agent_module_input.setText(module_path)
        self._start_agent(module_path)

    # ── Build UI ──
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ── Config bar ──
        cfg = QHBoxLayout()

        self.provider_cb = QComboBox()
        self.provider_cb.addItems(list(PROVIDERS.keys()))
        self.provider_cb.setToolTip("Pilih provider AI")
        self.provider_cb.currentTextChanged.connect(self._on_provider_changed)

        self.model_cb = QComboBox()
        self.model_cb.setEditable(True)
        self.model_cb.setToolTip("Pilih model atau ketik manual.")

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("API Key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.textChanged.connect(self._on_api_key_changed)

        self.show_key_btn = QPushButton("👁")
        self.show_key_btn.setFixedWidth(30)
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.setToolTip("Tampilkan/sembunyikan API key")
        self.show_key_btn.toggled.connect(
            lambda on: self.api_key_input.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )

        self.status_lbl = QLabel("○ Disconnected")
        self.status_lbl.setStyleSheet("color:#6272a4; font-size:11px;")

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setFixedWidth(110)
        self.connect_btn.clicked.connect(self.toggle_connection)
        self._update_button_style_and_text()

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(55)
        clear_btn.clicked.connect(self._clear_chat)

        cfg.addWidget(QLabel("Provider:"))
        cfg.addWidget(self.provider_cb)
        cfg.addWidget(QLabel("Model:"))
        cfg.addWidget(self.model_cb, 2)
        cfg.addWidget(self.api_key_input, 3)
        cfg.addWidget(self.show_key_btn)
        cfg.addWidget(self.status_lbl)
        cfg.addWidget(self.connect_btn)
        cfg.addWidget(clear_btn)
        root.addLayout(cfg)

        # ── Auto Agent Controls ──
        agent_group = QGroupBox("🤖 Auto Agent")
        agent_group.setStyleSheet("""
            QGroupBox {
                color: #00ff00;
                border: 2px solid #00ff00;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px;
                color: #00ff00;
            }
        """)
        
        agent_layout = QHBoxLayout()
        
        self.auto_agent_cb = QCheckBox("Auto Agent")
        self.auto_agent_cb.setChecked(True)
        self.auto_agent_cb.setStyleSheet("color: #00ff00; font-weight: bold;")
        agent_layout.addWidget(self.auto_agent_cb)
        
        agent_layout.addStretch()
        
        self.auto_chain_cb = QCheckBox("Auto-chain")
        self.auto_chain_cb.setChecked(True)
        self.auto_chain_cb.setStyleSheet("color: #cccccc;")
        agent_layout.addWidget(self.auto_chain_cb)
        
        self.agent_stop_btn = QPushButton("⏹ Stop Agent")
        self.agent_stop_btn.setFixedWidth(100)
        self.agent_stop_btn.setStyleSheet("""
            QPushButton {
                background: #cc0000;
                color: white;
                font-weight: bold;
                padding: 4px 12px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background: #ff0000;
            }
            QPushButton:disabled {
                background: #333333;
                color: #666666;
            }
        """)
        self.agent_stop_btn.clicked.connect(self._stop_agent)
        self.agent_stop_btn.setEnabled(False)
        agent_layout.addWidget(self.agent_stop_btn)
        
        agent_group.setLayout(agent_layout)
        root.addWidget(agent_group)

        # ── Module info ──
        module_layout = QHBoxLayout()
        module_layout.addWidget(QLabel("Module:"))
        self.agent_module_input = QLineEdit()
        self.agent_module_input.setPlaceholderText("Auto-detected from loaded module")
        self.agent_module_input.setReadOnly(True)
        self.agent_module_input.setStyleSheet("""
            QLineEdit {
                background: #1a1a1a;
                color: #888888;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 4px 8px;
                font-family: 'Consolas', monospace;
                font-size: 10px;
            }
        """)
        module_layout.addWidget(self.agent_module_input, 2)
        
        self.agent_status_icon = QLabel("🟢 Auto")
        self.agent_status_icon.setStyleSheet("color: #00ff00; font-size: 10px;")
        module_layout.addWidget(self.agent_status_icon)
        
        root.addLayout(module_layout)

        # ── Progress Bar ──
        progress_layout = QHBoxLayout()
        
        self.agent_progress = QProgressBar()
        self.agent_progress.setRange(0, 100)
        self.agent_progress.setValue(0)
        self.agent_progress.setFixedHeight(20)
        self.agent_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333333;
                border-radius: 4px;
                background: #1a1a1a;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00aa00, stop:0.5 #00ff00, stop:1 #00aa00);
                border-radius: 4px;
            }
        """)
        progress_layout.addWidget(self.agent_progress, 2)
        
        self.agent_status_label = QLabel("🟢 Ready")
        self.agent_status_label.setStyleSheet("color: #00ff00; font-size: 10px; font-weight: bold;")
        progress_layout.addWidget(self.agent_status_label)
        
        root.addLayout(progress_layout)

        # ── CHAT ──
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 12))
        self.chat_display.setMinimumHeight(350)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        self._append_bubble(
            "system",
            "🤖 LazyAI Auto Agent\n\n"
            "Auto Agent is ENABLED by default.\n"
            "Double-click any EXPLOIT module → Agent runs automatically!\n"
            "Agent will:\n"
            "1. Detect module loaded\n"
            "2. Ask AI for optimal settings\n"
            "3. Execute exploit\n"
            "4. Detect NEW sessions only\n"
            "5. Auto-chain post-exploitation\n\n"
            "⚠️ LEGAL: Only use for authorized testing!"
        )
        root.addWidget(self.chat_display)

        # ── Input row ──
        input_row = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask anything... (Enter)")
        self.input_box.setFont(QFont("Consolas", 10))
        self.input_box.returnPressed.connect(self.send_message)

        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedWidth(65)
        self.send_btn.clicked.connect(self.send_message)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFixedWidth(55)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_generation)

        input_row.addWidget(self.input_box)
        input_row.addWidget(self.send_btn)
        input_row.addWidget(self.stop_btn)
        root.addLayout(input_row)

        self._on_provider_changed(self.provider_cb.currentText())

    # ── Agent Methods ──
    def _start_agent(self, module_path=None):
        """Start the auto agent"""
        if self.agent_running:
            return
            
        if self.current_status not in [self.STATUS_CONNECTED, self.STATUS_CHANNEL_ACTIVE]:
            self._append_bubble("error", "Please connect to AI provider first!")
            return
            
        if not module_path:
            module_path = self.agent_module_input.text().strip()
            if not module_path and self.framework and self.framework.loaded_module:
                module_path = self.framework.loaded_module.name
                
        if not module_path:
            self._append_bubble("error", "No module loaded!")
            return
            
        # SKIP reverse_tcp
        if "reverse_tcp" in module_path.lower() or "payload" in module_path.lower():
            self._append_bubble("system", f"[dim]⏭️ Skipping agent for: {module_path}[/]")
            return
            
        self.agent_running = True
        self.agent_stop_btn.setEnabled(True)
        self.agent_progress.setValue(0)
        self.agent_progress.setFormat("Starting...")
        self.agent_status_label.setText("🤖 Running")
        self.agent_status_icon.setText("🔴 Running")
        self.agent_status_icon.setStyleSheet("color: #ff4444; font-size: 10px;")
        self.current_status = self.STATUS_AGENT_RUNNING
        self._update_button_style_and_text()
        
        self._append_bubble("system", f"🤖 Auto Agent starting on: {module_path}")
        
        self.agent_worker = AutoAgentWorker(
            self.framework, 
            self.gui, 
            self, 
            module_path,
            self.auto_chain_cb.isChecked()
        )
        
        self.agent_worker.output.connect(self._append_agent_output)
        self.agent_worker.progress.connect(self._on_progress_update)
        self.agent_worker.status.connect(self.agent_status_label.setText)
        self.agent_worker.finished.connect(self._on_agent_finished)
        self.agent_worker.error.connect(self._on_agent_error)
        self.agent_worker.session_detected.connect(self._on_session_detected)
        self.agent_worker.reset_progress.connect(self._reset_progress)
        
        self.agent_worker_thread = QThread()
        self.agent_worker.moveToThread(self.agent_worker_thread)
        self.agent_worker_thread.started.connect(self.agent_worker.run)
        self.agent_worker_thread.start()
        
    def _stop_agent(self):
        """Stop the running agent"""
        if not self.agent_running:
            return
            
        self._append_bubble("system", "⏹ Stopping agent...")
        
        if hasattr(self, 'agent_worker') and self.agent_worker:
            self.agent_worker.stop()
            
        if hasattr(self, 'agent_worker_thread') and self.agent_worker_thread.isRunning():
            self.agent_worker_thread.quit()
            self.agent_worker_thread.wait(2000)
            
        self.agent_running = False
        self.agent_stop_btn.setEnabled(False)
        self.current_status = self.STATUS_CONNECTED
        self._update_button_style_and_text()
        
        self._reset_progress()
        self.agent_status_label.setText("⏹ Stopped")
        self.agent_status_icon.setText("🟢 Auto")
        self.agent_status_icon.setStyleSheet("color: #00ff00; font-size: 10px;")
        
        self._append_bubble("system", "⏹ Agent stopped")
        
    def _on_progress_update(self, value):
        self.agent_progress.setValue(value)
        self.agent_progress.setFormat(f"{value}%")
        
    def _reset_progress(self):
        self.agent_progress.setValue(0)
        self.agent_progress.setFormat("Ready")
        self.agent_progress.repaint()
        
    def _on_agent_finished(self, success):
        self.agent_running = False
        self.agent_stop_btn.setEnabled(False)
        self.current_status = self.STATUS_CONNECTED
        self._update_button_style_and_text()
        
        if success:
            self.agent_status_label.setText("✅ Completed")
            self.agent_status_icon.setText("🟢 Auto")
            self.agent_status_icon.setStyleSheet("color: #00ff00; font-size: 10px;")
            self.agent_progress.setFormat("✅ Done")
        else:
            self.agent_status_label.setText("❌ Failed")
            self.agent_status_icon.setText("🔴 Error")
            self.agent_status_icon.setStyleSheet("color: #ff4444; font-size: 10px;")
            
    def _on_agent_error(self, error_msg):
        self._append_agent_output(f"[red]❌ ERROR: {error_msg}[/]")
        self.agent_status_label.setText("⚠️ Error")
        
    def _on_session_detected(self, session_id):
        self._append_bubble("system", f"🎯 NEW SESSION DETECTED: {session_id}")
        if self.gui:
            QTimer.singleShot(500, lambda: self.gui.main_tabs.setCurrentIndex(4))
            
    def _append_agent_output(self, text):
        if not text:
            return
        clean_text = self._strip_ansi(text)
        self._append_bubble("assistant", clean_text)
        
    def _strip_ansi(self, text):
        import re
        return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)

    # ── Existing Methods ──
    def _lbl(self, text):
        l = QLabel(text)
        l.setStyleSheet("color:#6272a4; font-size:11px; font-weight:bold;")
        return l

    def _on_provider_changed(self, provider_name: str):
        if provider_name in PROVIDERS:
            self.model_cb.clear()
            for model in PROVIDERS[provider_name]["models"]:
                self.model_cb.addItem(model)
            if provider_name in DEFAULT_MODELS:
                idx = self.model_cb.findText(DEFAULT_MODELS[provider_name])
                if idx >= 0:
                    self.model_cb.setCurrentIndex(idx)
            self._append_bubble("system", f"Switched to provider: {provider_name}")
            if self.current_status == self.STATUS_CONNECTED:
                self.current_status = self.STATUS_DISCONNECTED
                self._update_button_style_and_text()

    def _update_button_style_and_text(self):
        if self.current_status == self.STATUS_DISCONNECTED:
            self.connect_btn.setText("Connect")
            self.connect_btn.setEnabled(True)
            self.connect_btn.setStyleSheet("""
                QPushButton { background: #238636; color: white; border: none; 
                border-radius: 4px; padding: 6px; font-weight: bold; }
                QPushButton:hover { background: #2ea043; }
            """)
            self.status_lbl.setStyleSheet("color:#6272a4; font-size:11px;")
            self.status_lbl.setText("○ Disconnected")
        elif self.current_status == self.STATUS_CONNECTING:
            self.connect_btn.setText("Connecting...")
            self.connect_btn.setEnabled(False)
            self.connect_btn.setStyleSheet("""
                QPushButton { background: #f1fa8c; color: #1e1e1e; border: none; 
                border-radius: 4px; padding: 6px; font-weight: bold; }
            """)
            self.status_lbl.setStyleSheet("color:#f1fa8c; font-size:11px;")
            self.status_lbl.setText("◌ Connecting...")
        elif self.current_status == self.STATUS_CONNECTED:
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setEnabled(True)
            self.connect_btn.setStyleSheet("""
                QPushButton { background: #da3633; color: white; border: none; 
                border-radius: 4px; padding: 6px; font-weight: bold; }
                QPushButton:hover { background: #f85149; }
            """)
            self.status_lbl.setStyleSheet("color:#50fa7b; font-size:11px;")
            self.status_lbl.setText("● Connected")
        elif self.current_status == self.STATUS_AUTH_FAILED:
            self.connect_btn.setText("Auth Failed")
            self.connect_btn.setEnabled(True)
            self.connect_btn.setStyleSheet("""
                QPushButton { background: #8B0000; color: #ff8888; border: 1px solid #ff5555; 
                border-radius: 4px; padding: 6px; font-weight: bold; }
                QPushButton:hover { background: #aa0000; }
            """)
            self.status_lbl.setStyleSheet("color:#ff5555; font-size:11px;")
            self.status_lbl.setText("● Auth Failed")
        elif self.current_status == self.STATUS_CHANNEL_ACTIVE:
            self.connect_btn.setText("Channel Active")
            self.connect_btn.setEnabled(True)
            self.connect_btn.setStyleSheet("""
                QPushButton { background: #50fa7b; color: #1e1e1e; border: none; 
                border-radius: 4px; padding: 6px; font-weight: bold; }
                QPushButton:hover { background: #69ff94; }
            """)
            self.status_lbl.setStyleSheet("color:#50fa7b; font-size:11px;")
            self.status_lbl.setText("● Channel Active")
        elif self.current_status == self.STATUS_AGENT_RUNNING:
            self.connect_btn.setText("Agent Running")
            self.connect_btn.setEnabled(False)
            self.connect_btn.setStyleSheet("""
                QPushButton { background: #ff8800; color: #1e1e1e; border: none; 
                border-radius: 4px; padding: 6px; font-weight: bold; }
            """)
            self.status_lbl.setStyleSheet("color:#ff8800; font-size:11px;")
            self.status_lbl.setText("🤖 Agent Running")

    def _reset_from_auth_failed(self):
        if self.current_status == self.STATUS_AUTH_FAILED:
            self.current_status = self.STATUS_DISCONNECTED
            self._update_button_style_and_text()
            self.api_key_input.setEnabled(True)
            self.model_cb.setEnabled(True)
            self.provider_cb.setEnabled(True)
            self.show_key_btn.setEnabled(True)

    def _on_api_key_changed(self):
        if self.current_status == self.STATUS_AUTH_FAILED:
            self.current_status = self.STATUS_DISCONNECTED
            self._update_button_style_and_text()
            self.connect_btn.setEnabled(True)

    def toggle_connection(self):
        if self.current_status in [self.STATUS_CONNECTED, self.STATUS_CHANNEL_ACTIVE]:
            self.disconnect()
        elif self.current_status in [self.STATUS_DISCONNECTED, self.STATUS_AUTH_FAILED]:
            self._connect()

    def _connect(self):
        key = self.api_key_input.text().strip()
        if not key:
            self.current_status = self.STATUS_AUTH_FAILED
            self._update_button_style_and_text()
            self._append_bubble("error", "API key cannot be empty!")
            QTimer.singleShot(3000, self._reset_from_auth_failed)
            return
        self.current_status = self.STATUS_CONNECTING
        self._update_button_style_and_text()
        self.api_key_input.setEnabled(False)
        self.model_cb.setEnabled(False)
        self.provider_cb.setEnabled(False)
        self.show_key_btn.setEnabled(False)

        def check():
            try:
                provider = self.provider_cb.currentText()
                auth_url = PROVIDERS.get(provider, {}).get("auth_url", "")
                if not auth_url:
                    self.current_status = self.STATUS_AUTH_FAILED
                    QTimer.singleShot(0, lambda: self._append_bubble("error", f"Provider {provider} has no auth URL"))
                    QTimer.singleShot(3000, self._reset_from_auth_failed)
                    return
                r = requests.get(auth_url, headers={"Authorization": f"Bearer {key}"}, timeout=8)
                if r.status_code == 200:
                    self.current_status = self.STATUS_CONNECTED
                    self._save_api_key(key)
                    QTimer.singleShot(0, lambda: self._append_bubble("system", f"Connected to {provider}!"))
                else:
                    self.current_status = self.STATUS_AUTH_FAILED
                    QTimer.singleShot(0, lambda: self._append_bubble("error", f"Auth failed ({r.status_code})"))
                    QTimer.singleShot(3000, self._reset_from_auth_failed)
            except Exception as e:
                self.current_status = self.STATUS_AUTH_FAILED
                QTimer.singleShot(0, lambda: self._append_bubble("error", f"Failed: {e}"))
                QTimer.singleShot(3000, self._reset_from_auth_failed)
            finally:
                QTimer.singleShot(0, self._update_ui_after_connect)

        threading.Thread(target=check, daemon=True).start()

    def _update_ui_after_connect(self):
        self._update_button_style_and_text()
        if self.current_status == self.STATUS_CONNECTED:
            self.api_key_input.setEnabled(False)
            self.model_cb.setEnabled(False)
            self.provider_cb.setEnabled(False)
            self.show_key_btn.setEnabled(False)
            QTimer.singleShot(0, lambda: self._append_bubble("assistant", "Channel active. Auto Agent ready!"))
        elif self.current_status == self.STATUS_AUTH_FAILED:
            self.api_key_input.setEnabled(True)
            self.model_cb.setEnabled(True)
            self.provider_cb.setEnabled(True)
            self.show_key_btn.setEnabled(True)

    def disconnect(self):
        self.current_status = self.STATUS_DISCONNECTED
        self._update_button_style_and_text()
        self.api_key_input.setEnabled(True)
        self.model_cb.setEnabled(True)
        self.provider_cb.setEnabled(True)
        self.show_key_btn.setEnabled(True)
        with self._worker_lock:
            if self.worker:
                self.worker.stop()
                self.worker.deleteLater()
                self.worker = None
            if self.worker_thread:
                self.worker_thread.quit()
                self.worker_thread.wait()
                self.worker_thread.deleteLater()
                self.worker_thread = None
        self._append_bubble("system", "Disconnected.")

    def set_channel_active(self, active=True):
        if active:
            self.current_status = self.STATUS_CHANNEL_ACTIVE
            self._append_bubble("system", "Channel active - AI analysis in progress")
        else:
            if self.current_status == self.STATUS_CHANNEL_ACTIVE:
                self.current_status = self.STATUS_CONNECTED
                self._append_bubble("system", "Channel inactive - back to idle")
        self._update_button_style_and_text()

    def _save_api_key(self, key):
        if self.framework:
            self.framework.session["openrouter_api_key"] = key

    def _load_api_key(self):
        if self.framework and "openrouter_api_key" in self.framework.session:
            key = self.framework.session["openrouter_api_key"]
            if key:
                self.api_key_input.setText(key)

    def _append_bubble(self, role, text):
        colors = {"user": "#bd93f9", "assistant": "#50fa7b", "system": "#6272a4", "error": "#ff5555"}
        labels = {"user": "You", "assistant": "LazyAI", "system": "System", "error": "Error"}
        c = colors.get(role, "#fff")
        l = labels.get(role, role)
        self.chat_display.append(f'<span style="color:{c};font-weight:bold;">[{l}]</span>')
        self.chat_display.append(f'<span style="color:#e6edf3;white-space:pre-wrap;">{text}</span><br>')
        self.chat_display.ensureCursorVisible()

    def _clear_chat(self):
        self.chat_history.clear()
        self.chat_display.clear()
        self._ai_buf = ""
        self.chat_display.append('<span style="color:#444;">[ session cleared ]</span><br>')

    def send_message(self, text=None):
        if text is None:
            text = self.input_box.text().strip()
        if not text:
            return
        self.input_box.clear()
        if self.current_status not in [self.STATUS_CONNECTED, self.STATUS_CHANNEL_ACTIVE]:
            self._append_bubble("error", "Not connected. Click 'Connect' first.")
            return
        key = self.api_key_input.text().strip()
        if not key:
            self._append_bubble("error", "API key is empty.")
            return
        self._append_bubble("user", text)
        self.chat_history.append({"role": "user", "content": text})
        self._start_worker(key)

    def _start_worker(self, api_key):
        with self._worker_lock:
            if self.worker:
                self.worker.stop()
                self.worker.deleteLater()
                self.worker = None
            if self.worker_thread:
                self.worker_thread.quit()
                self.worker_thread.wait()
                self.worker_thread.deleteLater()
                self.worker_thread = None
        self.send_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self._ai_buf = ""
        provider = self.provider_cb.currentText()
        self.chat_display.append(f'<span style="color:#50fa7b;font-weight:bold;">[LazyAI ({provider})]</span> ')
        self.worker = AIWorker(
            provider=provider,
            model=self.model_cb.currentText(),
            api_key=api_key,
            messages=list(self.chat_history),
        )
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.token_received.connect(self._on_token)
        self.worker.finished.connect(self._on_done)
        self.worker.error.connect(self._on_error)
        self.worker_thread.start()

    def _on_token(self, token):
        self._ai_buf += token
        c = self.chat_display.textCursor()
        c.movePosition(QTextCursor.MoveOperation.End)
        c.insertText(token)
        self.chat_display.ensureCursorVisible()

    def _on_done(self):
        if self._ai_buf:
            self.chat_history.append({"role": "assistant", "content": self._ai_buf})
        self.chat_display.append("<br>")
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        with self._worker_lock:
            if self.worker_thread:
                self.worker_thread.quit()
                self.worker_thread.wait()
                self.worker_thread.deleteLater()
                self.worker_thread = None
            if self.worker:
                self.worker.deleteLater()
                self.worker = None

    def _on_error(self, msg):
        self.chat_display.append(f'<span style="color:#ff5555;">{msg}</span><br>')
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        with self._worker_lock:
            if self.worker_thread:
                self.worker_thread.quit()
                self.worker_thread.wait()
                self.worker_thread.deleteLater()
                self.worker_thread = None
            if self.worker:
                self.worker.deleteLater()
                self.worker = None

    def _stop_generation(self):
        with self._worker_lock:
            if self.worker:
                self.worker.stop()

    def inject_output(self, text: str):
        if hasattr(self.parent(), "sidebar_context_box"):
            sidebar_current = self.parent().sidebar_context_box.toPlainText()
            sidebar_merged = (sidebar_current + "\n" + text).strip()
            if len(sidebar_merged) > 10000:
                sidebar_merged = sidebar_merged[-10000:]
            self.parent().sidebar_context_box.setPlainText(sidebar_merged)
            scrollbar = self.parent().sidebar_context_box.verticalScrollBar()
            if scrollbar:
                scrollbar.setValue(scrollbar.maximum())

    def ask(self, question: str):
        self.send_message(question)

    def run_agent_mode(self, loaded_module):
        if self.current_status not in [self.STATUS_CONNECTED, self.STATUS_CHANNEL_ACTIVE]:
            return
        try:
            lines = []
            name = getattr(loaded_module, "name", None) or getattr(loaded_module, "NAME", None) or type(loaded_module).__name__
            lines.append(f"Module: {name}")
            desc = getattr(loaded_module, "description", None) or getattr(loaded_module, "DESCRIPTION", None) or getattr(loaded_module, "info", {}).get("description", "")
            if desc:
                lines.append(f"Description: {desc}")
            options = getattr(loaded_module, "options", None) or getattr(loaded_module, "OPTIONS", None)
            if options:
                lines.append("Options:")
                if isinstance(options, dict):
                    for k, v in options.items():
                        if isinstance(v, dict):
                            default = v.get("default", "")
                            desc_opt = v.get("description", "")
                            lines.append(f"  {k}: {default} (Description: {desc_opt})")
                        else:
                            lines.append(f"  {k} = {v}")
                else:
                    lines.append(f"  {options}")
            required = getattr(loaded_module, "required", None) or getattr(loaded_module, "REQUIRED", None)
            if required:
                lines.append(f"Required fields: {required}")
            context_text = "\n".join(lines)
            self.inject_output(context_text)
            prompt = (f"Module '{name}' has been loaded. "
                     "Based on the module info:\n"
                     "1. Briefly explain this module's function for authorized testing\n"
                     "2. Recommend optimal values for each option\n"
                     "3. Provide an example of optimal usage in a lab environment\n"
                     "4. Mention any potential risks or precautions for authorized testing")
            self.send_message(prompt)
        except Exception as e:
            self._append_bubble("error", f"Agent mode error: {e}")


# ─── AI Worker ──────────────────────────────────────────────────────────────────
class AIWorker(QObject):
    token_received = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, provider, model, api_key, messages, site_url="", site_name="Lazy Framework"):
        super().__init__()
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.messages = messages
        self.site_url = site_url
        self.site_name = site_name
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            if self.provider == "ZenMux":
                url = ZENMUX_URL
            else:
                url = OPENROUTER_URL
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.site_url or "https://lazyframework.local",
                "X-Title": self.site_name,
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + self.messages,
                "stream": True,
            }
            if self.provider == "ZenMux":
                payload["max_tokens"] = 4096
                payload["temperature"] = 0.7
            with requests.post(url, headers=headers, json=payload, stream=True, timeout=120) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if self._stop:
                        break
                    if not line or line == b"data: [DONE]":
                        continue
                    raw = line.decode().removeprefix("data: ")
                    try:
                        data = json.loads(raw)
                        if "choices" in data:
                            token = data["choices"][0]["delta"].get("content", "")
                            if token:
                                self.token_received.emit(token)
                    except Exception:
                        pass
        except requests.exceptions.ConnectionError:
            self.error.emit("Tidak bisa terhubung. Cek koneksi internet.")
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response else "?"
            if code == 401:
                self.error.emit("API key tidak valid (401).")
            elif code == 402:
                self.error.emit("Kredit habis (402). Top up di provider.")
            elif code == 403:
                self.error.emit("Akses ditolak (403). Coba model lain atau periksa API key.")
            elif code == 429:
                self.error.emit("Rate limit (429). Tunggu sebentar.")
            else:
                self.error.emit(f"HTTP error {code}: {e}")
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()