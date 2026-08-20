#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import shutil
import socket
import re
import sys
import time
import xml.etree.ElementTree as ET
import threading
from typing import Dict, Any

# Windows console setup
if sys.platform == "win32":
    os.system("")
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.live import Live

console = Console()

# ==================== MODULE INFO ====================
MODULE_INFO = {
    "name": "Nmap Super Scan",
    "author": "RevilCipher",
    "description": "Network exploration tool and security / port scanner",
    "rank": "Excellent",
    "dependencies": [],
    "platform": "multi",
    "arch": "multi",
}

# ==================== SCAN MODES ====================
SCAN_MODES = {
    "tcp_syn": {"flag": "-sS", "desc": "TCP SYN", "class": "TCP", "root": True},
    "tcp_connect": {
        "flag": "-sT",
        "desc": "TCP Connect",
        "class": "TCP",
        "root": False,
    },
    "tcp_ack": {"flag": "-sA", "desc": "TCP ACK", "class": "TCP", "root": True},
    "tcp_fin": {"flag": "-sF", "desc": "TCP FIN", "class": "TCP", "root": True},
    "tcp_null": {"flag": "-sN", "desc": "TCP NULL", "class": "TCP", "root": True},
    "tcp_xmas": {"flag": "-sX", "desc": "TCP Xmas", "class": "TCP", "root": True},
    "tcp_window": {"flag": "-sW", "desc": "TCP Window", "class": "TCP", "root": True},
    "tcp_maimon": {"flag": "-sM", "desc": "TCP Maimon", "class": "TCP", "root": True},
    "udp_scan": {"flag": "-sU", "desc": "UDP Scan", "class": "UDP", "root": True},
    "udp_version": {"flag": "-sUV", "desc": "UDP + Ver", "class": "UDP", "root": True},
    "sctp_init": {"flag": "-sY", "desc": "SCTP INIT", "class": "SCTP", "root": True},
    "sctp_cookie": {
        "flag": "-sZ",
        "desc": "SCTP COOKIE",
        "class": "SCTP",
        "root": True,
    },
    "ping_scan": {
        "flag": "-sn",
        "desc": "Ping Only",
        "class": "Discovery",
        "root": False,
    },
    "arp_ping": {
        "flag": "-PR",
        "desc": "ARP Ping",
        "class": "Discovery",
        "root": False,
    },
    "version_detect": {
        "flag": "-sV",
        "desc": "Version",
        "class": "Advanced",
        "root": False,
    },
    "os_detect": {"flag": "-O", "desc": "OS Detect", "class": "Advanced", "root": True},
    "script_default": {
        "flag": "-sC",
        "desc": "NSE Scripts",
        "class": "Advanced",
        "root": False,
    },
    "aggressive": {
        "flag": "-A",
        "desc": "Aggressive",
        "class": "Advanced",
        "root": True,
    },
    "ipv6": {"flag": "-6", "desc": "IPv6", "class": "Advanced", "root": False},
    "traceroute": {
        "flag": "--traceroute",
        "desc": "Trace hop path",
        "class": "TCP",
        "root": True,
    },
    "custom": {"flag": "", "desc": "Custom Flags", "class": "Custom", "root": False},
}

MODE_CHOICES = list(SCAN_MODES.keys()) + ["list"]

OPTIONS = {
    "TARGET": {"description": "Target IP / hostname", "required": True, "default": ""},
    "PORTS": {
        "description": "Ports (e.g. 80,443,1-1000)",
        "required": False,
        "default": "",
    },
    "MODE": {
        "description": "Scan mode",
        "required": True,
        "default": "tcp_connect",
        "choices": MODE_CHOICES,
    },
    "CUSTOM_FLAGS": {
        "description": "Custom nmap flags",
        "required": False,
        "default": "",
    },
}


# ==================== COLOR PROGRESS BAR ====================
class AnimatedColorProgress:
    """Real-time animated color progress bar"""

    COLORS = [
        "red",
        "bright_red",
        "orange1",
        "yellow",
        "bright_yellow",
        "green",
        "bright_green",
        "cyan",
        "bright_cyan",
        "blue",
        "bright_blue",
        "magenta",
        "bright_magenta",
    ]

    def __init__(self, total_steps=100, refresh_rate=0.1):
        self.total_steps = total_steps
        self.current_step = 0
        self.refresh_rate = refresh_rate
        self._running = False
        self._thread = None
        self._color_index = 0
        self._stop_event = threading.Event()

    def start_animation(self):
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop_animation(self):
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=0.5)

    def _animate(self):
        while self._running and not self._stop_event.is_set():
            self._color_index = (self._color_index + 1) % len(self.COLORS)
            time.sleep(self.refresh_rate)

    def update(self, step):
        self.current_step = min(step, self.total_steps)

    def get_current_color(self):
        if self.current_step >= self.total_steps:
            return "bright_green"
        return self.COLORS[self._color_index]

    def get_percentage(self):
        return int((self.current_step / self.total_steps) * 100)

    def render(self, width=55):
        percent = self.get_percentage()
        filled_width = int(width * self.current_step / self.total_steps)
        empty_width = width - filled_width
        color = self.get_current_color()

        filled = f"[{color}]" + "=" * filled_width + "[/]"
        empty = "[#444444]" + "-" * empty_width + "[/]"

        if percent == 100:
            pct_text = f"[bold bright_green]✓ {percent}%[/]"
        else:
            pct_text = f"[{color}][{percent:3d}%][/]"

        spinner_chars = ["|", "/", "-", "\\"]
        spinner_char = spinner_chars[self.current_step % len(spinner_chars)]
        spinner = f"[{color}]{spinner_char}[/]"

        return f"{spinner} [{filled}{empty}] {pct_text}"


# ==================== HELPERS ====================
def _resolve(target):
    target = target.strip()
    console.print(f"[dim]Resolving: {target}[/dim]")
    target = re.sub(r"^[a-zA-Z][a-zA-Z0-9+\-.]*://", "", target)
    target = re.split(r"[/?#]", target)[0]
    target = re.sub(r":\d+$", "", target).strip()

    # Check if it's already an IP or network range
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d+)?$", target):
        return target

    try:
        # If it's a hostname with /24 or similar, extract hostname first
        if "/" in target:
            hostname = target.split("/")[0]
            ip = socket.gethostbyname(hostname)
            cidr = target.split("/")[1]
            return f"{ip}/{cidr}"
        else:
            ip = socket.gethostbyname(target)
            console.print(f"[green][+] {target} → {ip}[/green]")
            return ip
    except Exception as e:
        raise ValueError(f"Cannot resolve {target}: {e}")


def _build_cmd(options):
    target = _resolve(options["TARGET"])
    mode_key = options.get("MODE", "tcp_connect").lower()
    ports = options.get("PORTS", "").strip()
    custom = options.get("CUSTOM_FLAGS", "").strip()

    if sys.platform == "win32":
        temp_dir = os.environ.get("TEMP", "C:\\Temp")
        xml_path = f"{temp_dir}\\nmap_scan_{int(time.time())}.xml"
    else:
        xml_path = f"/tmp/nmap_scan_{int(time.time())}.xml"

    if mode_key == "custom":
        flags = custom or "-sS"
        # Check if OS detection (-O) requires root
        if "-O" in flags and os.geteuid() != 0:
            console.print(
                "[yellow]⚠️  OS detection (-O) requires root privileges![/yellow]"
            )
            console.print("[yellow]Run with: sudo lzfconsole[/yellow]")
            console.print("[dim]Continuing without OS detection...[/dim]")
            flags = flags.replace("-O", "").strip()
    else:
        flags = SCAN_MODES.get(mode_key, {"flag": "-sS"})["flag"]
        # Check if mode requires root
        if SCAN_MODES.get(mode_key, {}).get("root", False) and os.geteuid() != 0:
            console.print(
                f"[yellow]⚠️  {mode_key} mode requires root privileges![/yellow]"
            )
            console.print(f"[yellow]Run with: sudo lzfconsole[/yellow]")
            console.print("[dim]Falling back to TCP Connect scan...[/dim]")
            flags = "-sT"

    cmd = f"nmap -v -oX {xml_path} {flags}"

    if ports:
        cmd += f" -p {ports}"
    cmd += f" {target}"

    return cmd, target, xml_path


# ==================== IMPROVED XML PARSER ====================
def _parse_nmap_xml(xml_path, resolved_target):
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    table.add_column("HOST", style="white", width=20)
    table.add_column("PORT", style="yellow", width=12)
    table.add_column("STATE", style="green", width=12)
    table.add_column("SERVICE", style="magenta", width=18)
    table.add_column("VERSION", style="dim", width=30, overflow="fold")

    open_count = 0
    open_ports_list = []

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        for host in root.findall("host"):
            addr_elem = host.find("./address")
            addr = addr_elem.get("addr") if addr_elem is not None else resolved_target

            for port in host.findall(".//port"):
                portid = port.get("portid")
                proto = port.get("protocol", "tcp")
                state_elem = port.find("state")
                state = state_elem.get("state") if state_elem is not None else "unknown"

                service_elem = port.find("service")
                service = (
                    service_elem.get("name", "") if service_elem is not None else ""
                )

                version = ""
                if service_elem is not None:
                    product = service_elem.get("product", "")
                    ver = service_elem.get("version", "")
                    extra = service_elem.get("extrainfo", "")
                    version = f"{product} {ver} {extra}".strip()[:60]

                if state == "open":
                    open_count += 1
                    open_ports_list.append(portid)

                state_display = {
                    "open": "[bold green]OPEN[/]",
                    "filtered": "[yellow]FILTERED[/]",
                    "closed": "[red]CLOSED[/]",
                    "unfiltered": "[yellow]UNFILTERED[/]",
                }.get(state, f"[white]{state.upper()}[/]")

                table.add_row(
                    addr,
                    f"{portid}/{proto}",
                    state_display,
                    service[:18] if service else "-",
                    version if version else "-",
                )
    except Exception as e:
        console.print(f"[red]XML Parse Error: {e}[/]")

    return (
        table,
        open_count,
        sorted(
            set(open_ports_list), key=lambda x: int(x) if str(x).isdigit() else 9999
        ),
    )


# ==================== RUN SCAN WITH LIVE PROGRESS ====================
def _run_scan_with_live_progress(cmd):
    xml_path = None
    match = re.search(r"-oX\s+([^\s]+)", cmd)
    if match:
        xml_path = match.group(1)

    progress = AnimatedColorProgress(total_steps=100)
    status_messages = []
    current_phase = "[yellow]Initializing...[/]"
    found_ports = []
    scan_error = False
    error_message = ""

    def parse_nmap_output(line, progress_bar, status_list, ports_list):
        nonlocal current_phase, scan_error, error_message
        line_lower = line.lower().strip()

        if line_lower:
            status_list.append(line_lower[:75])
            if len(status_list) > 3:
                status_list.pop(0)

        # Check for errors
        if "requires root privileges" in line_lower:
            scan_error = True
            error_message = "Root privileges required!"
            return

        if "failed" in line_lower or "error" in line_lower:
            if "root" in line_lower or "privileges" in line_lower:
                scan_error = True
                error_message = "Root privileges required!"
                return

        # Discovered open port
        if "discovered open port" in line_lower:
            port_match = re.search(r"discovered open port (\d+)/(\w+)", line_lower)
            if port_match:
                port = port_match.group(1)
                if port not in ports_list:
                    ports_list.append(port)
                current_phase = f"[bold green]▶ OPEN: {port}[/]"
                progress_bar.update(10)

        elif "initiating" in line_lower:
            if "ping" in line_lower:
                current_phase = "[cyan]▶ Host Discovery[/]"
                progress_bar.update(15)
            else:
                current_phase = "[cyan]▶ Port Scanning[/]"
                progress_bar.update(10)

        elif "scanning" in line_lower:
            current_phase = "[cyan]▶ Scanning[/]"
            progress_bar.update(5)

        elif "service" in line_lower and "version" in line_lower:
            current_phase = "[yellow]▶ Service Detection[/]"
            progress_bar.update(8)

        elif "completed" in line_lower or "finished" in line_lower:
            current_phase = "[bright_green]▶ Finalizing[/]"
            progress_bar.update(20)

    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        progress.start_animation()

        # Read output and update live display
        output_lines = []
        with Live(console=console, refresh_per_second=10, transient=False) as live:
            for line in proc.stdout:
                output_lines.append(line)
                parse_nmap_output(line, progress, status_messages, found_ports)

                bar_text = progress.render()
                percentage = progress.get_percentage()

                # Border color based on progress
                if percentage < 30:
                    border = "red"
                elif percentage < 60:
                    border = "yellow"
                elif percentage < 90:
                    border = "cyan"
                else:
                    border = "bright_green"

                status_text = (
                    f"\n[dim]> {status_messages[-1][:70]}[/]" if status_messages else ""
                )
                ports_text = (
                    f"\n[dim]Found: [/][green]{', '.join(found_ports[-6:])}[/]"
                    if found_ports
                    else ""
                )
                error_text = f"\n[red]⚠️  {error_message}[/]" if scan_error else ""

                display = Panel(
                    f"{current_phase}\n\n{bar_text}{ports_text}{status_text}{error_text}",
                    title="[bold white] NMAP SCANNER [/]",
                    border_style=border,
                    padding=(1, 2),
                )
                live.update(display)

            proc.wait()

            # If scan error, show error and exit
            if scan_error:
                progress.stop_animation()
                error_panel = Panel(
                    f"[red]✗ SCAN FAILED[/]\n\n"
                    f"[yellow]{error_message}[/]\n\n"
                    f"[dim]Try using 'sudo' or change scan mode[/]",
                    title="[bold red] ERROR [/]",
                    border_style="red",
                    padding=(1, 2),
                )
                live.update(error_panel)
                time.sleep(1.5)
                return None, []

            # Update to 100%
            progress.update(100)

            # Final display
            final_display = Panel(
                f"[bold bright_green]✓ SCAN COMPLETED[/]\n\n"
                f"{progress.render()}\n\n"
                f"[dim]Found {len(found_ports)} open ports[/]",
                title="[bold white] DONE [/]",
                border_style="bright_green",
                padding=(1, 2),
            )
            live.update(final_display)
            time.sleep(0.5)

        progress.stop_animation()
        return xml_path, found_ports

    except KeyboardInterrupt:
        progress.stop_animation()
        console.print("\n[yellow]✗ Scan interrupted[/]")
        return None, []
    except Exception as e:
        progress.stop_animation()
        console.print(f"[red]Scan Error: {e}[/]")
        return None, []


# ==================== MAIN RUN FUNCTION ====================
def run(session: Dict[str, Any], options: Dict[str, Any]):
    console.print(Panel("[bold white]NMAP SCANNER[/]", border_style="cyan"))
    print()

    if not shutil.which("nmap"):
        console.print("[red][!] nmap not found! Please install nmap first.[/]")
        return

    # Check root privileges for certain modes
    mode = options.get("MODE", "tcp_connect").lower()
    if mode in SCAN_MODES and SCAN_MODES[mode].get("root", False) and os.geteuid() != 0:
        console.print(f"[yellow]⚠️  {mode} mode requires root privileges![/yellow]")
        console.print("[yellow]Run with: sudo lzfconsole[/yellow]")
        console.print("[dim]Falling back to TCP Connect scan...[/dim]")
        options["MODE"] = "tcp_connect"

    try:
        cmd, resolved_target, xml_path = _build_cmd(options)
        console.print(f"[dim]> {cmd}[/]\n")

        xml_path, live_ports = _run_scan_with_live_progress(cmd)

        if xml_path and os.path.exists(xml_path):
            print()

            table, open_count, open_ports_list = _parse_nmap_xml(
                xml_path, resolved_target
            )

            if table.row_count > 0:
                console.print(
                    Panel(
                        table,
                        title=f"[bold green]RESULTS: {resolved_target}[/]",
                        border_style="green",
                    )
                )
            else:
                console.print("[yellow][!] No ports detected[/]")

            summary_lines = [
                f"[cyan]Target:[/] [white]{resolved_target}[/]",
                f"[cyan]Mode:[/] [magenta]{options.get('MODE', 'tcp_syn')}[/]",
                f"[cyan]Open ports:[/] [bold green]{open_count}[/]",
            ]
            if open_ports_list:
                summary_lines.append(
                    f"[cyan]Ports:[/] [green]{', '.join(open_ports_list)}[/]"
                )

            console.print(
                Panel(
                    "\n".join(summary_lines),
                    title="[bold yellow]SUMMARY[/]",
                    border_style="yellow",
                )
            )
            console.print(
                f"\n[bold bright_green][+] Scan completed! Open ports: {open_count}[/]"
            )

            try:
                os.remove(xml_path)
            except:
                pass
        else:
            console.print("[red][!] Scan failed or no output generated[/]")

    except KeyboardInterrupt:
        console.print("\n[yellow][!] Scan interrupted[/]")
    except Exception as e:
        console.print(f"[red][!] Error: {e}[/]")
