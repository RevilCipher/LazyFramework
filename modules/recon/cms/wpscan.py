#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WPScan Module – LazyFramework (Metasploit Style)
WordPress vulnerability scanner with API token and bruteforce support
"""

import subprocess
import shutil
import os
import re
from typing import Dict, Any
from rich.table import Table
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.style import Style

console = Console()

MODULE_INFO = {
    "name": "Wordpress Scanner",
    "description": "WordPress scanner + API token + bruteforce",
    "author": "RevilCipher",
    "category": "recon",
    "license": "GPLv2+",
    "platform": "All",
    "arch": "all",
    "rank": "Great",
    "dependencies": [],
    "references": [
      "https://github.com/wpscanteam/wpscan/",
      "https://wpscan.com/"
    ]
}

OPTIONS = {
    "URL": {
        "default": "",
        "required": True,
        "description": "Target URL http/https",
    },
    "MODE": {
        "default": "",
        "required": True,
        "choices": ["QUICK", "STANDARD", "AGGRESSIVE", "BRUTEFORCE"],
        "description": "Scan mode",
    },
    "UPDATE_DB": {
        "default": "NO",
        "choices": ["YES", "NO"],
        "description": "Update database? (YES to update, NO to skip)",
    },
    "MAX_THREADS": {
        "default": "10",
        "description": "thread (5-50)",
    },
    "WORDLIST": {
        "default": "",
        "required": False,
        "description": "Path to wordlist (required for BRUTEFORCE mode)",
    },
    "USERNAMES": {
        "default": "admin",
        "required": False,
        "description": "Username user,admin,example",
    },
    "API_TOKEN": {
        "default": "",
        "required": False,
        "description": "WPScan API Token",
    },
    "FOLLOW_REDIRECT": {
        "default": "YES",
        "choices": ["YES", "NO"],
        "description": "Follow redirects to final URL",
    },
}


def strip_ansi(text: str) -> str:
    """Hapus ANSI escape codes dari teks"""
    ansi_pattern = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
    text = ansi_pattern.sub("", text)
    raw_ansi_pattern = re.compile(r"\[\d+m")
    text = raw_ansi_pattern.sub("", text)
    bracket_pattern = re.compile(r"\[\d+\]\[[+\-!*]\]\[\d+\]")
    text = bracket_pattern.sub("", text)

    for code in [
        "[32m",
        "[34m",
        "[33m",
        "[31m",
        "[35m",
        "[36m",
        "[37m",
        "[0m",
        "[91m",
        "[92m",
        "[93m",
        "[94m",
        "[95m",
        "[96m",
        "[97m",
    ]:
        text = text.replace(code, "")

    return text


def colorize_output(line: str) -> str:
    """Colorize output untuk Rich console"""
    line = strip_ansi(line)

    if not line:
        return line

    if "[+]" in line or line.startswith("+"):
        return f"[green]{line}[/]"
    elif "[!]" in line or "Scan Aborted" in line or "Warning" in line:
        return f"[yellow]{line}[/]"
    elif "[X]" in line or "Error" in line or "failed" in line.lower():
        return f"[red]{line}[/]"
    elif "[*]" in line or "Updating" in line or "Enumerating" in line:
        return f"[dim]{line}[/]"
    elif "Interesting Finding" in line or "Found By" in line:
        return f"[cyan]{line}[/]"
    elif "Finished" in line or "Scan selesai" in line or "Completed" in line:
        return f"[bold green]{line}[/]"
    elif "http://" in line or "https://" in line:
        return f"[blue]{line}[/]"
    else:
        return line


def print_rich_banner(
    title: str, 
    url: str, 
    mode: str, 
    api_token: str = "", 
    update_db: bool = False,
    threads: str = "10",
    wordlist: str = "",
    usernames: str = "admin",
    follow_redirect: bool = True
):
    """Print Metasploit-style banner using Rich"""
    
    # Status indicators
    api_status = "[green]● Active[/]" if api_token else "[dim]● Not used[/]"
    update_status = "[green]● Yes[/]" if update_db else "[dim]● No[/]"
    redirect_status = "[green]● Yes[/]" if follow_redirect else "[dim]● No[/]"
    
    # Create table for module info
    table = Table(
        box=box.SIMPLE,
        show_header=False,
        show_footer=False,
        expand=False,
        padding=(0, 2)
    )
    table.add_column(style="bold cyan", width=14)
    table.add_column(style="white", width=40)
    
    table.add_row("Name", f"[bold green]{title}[/]")
    table.add_row("Target", f"[blue]{url}[/]")
    table.add_row("Mode", f"[bold yellow]{mode}[/]")
    table.add_row("Threads", f"[white]{threads}[/]")
    table.add_row("Update DB", update_status)
    table.add_row("API Token", api_status)
    table.add_row("Follow Redirect", redirect_status)
    
    if wordlist:
        table.add_row("Wordlist", f"[dim]{wordlist}[/]")
    if usernames:
        table.add_row("Usernames", f"[dim]{usernames}[/]")
    
    # Create main panel with border
    panel = Panel(
        table,
        title=f"[bold red]▣ {title}[/]",
        title_align="center",
        border_style="red",
        padding=(1, 2),
        width=62
    )
    
    # Center the panel
    centered = Align.center(panel)
    console.print(centered)
    console.print("")


def run(session: Dict[str, Any], options: Dict[str, Any]):
    raw_url = options.get("URL", "").strip()
    mode = options.get("MODE", "STANDARD").upper()
    update_db = options.get("UPDATE_DB", "NO").upper() == "YES"
    threads = options.get("MAX_THREADS", "10")
    wordlist = options.get("WORDLIST", "").strip()
    usernames = options.get("USERNAMES", "admin").strip()
    api_token = options.get("API_TOKEN", "").strip()
    follow_redirect = options.get("FOLLOW_REDIRECT", "YES").upper() == "YES"

    # Normalisasi URL
    if not raw_url:
        console.print("[bold red][X] URL is required![/]")
        return

    if not raw_url.startswith(("http://", "https://")):
        url = "https://" + raw_url
    else:
        url = raw_url
    url = url.rstrip("/") + "/"

    # Cek wpscan
    wpscan = shutil.which("wpscan")
    if not wpscan:
        console.print("[bold red][X] wpscan tidak terinstall![/]")
        console.print("[yellow]Install: gem install wpscan[/]")
        console.print("[yellow]Atau: sudo gem install wpscan[/]")
        return

    # === UPDATE DATABASE (ONLY IF UPDATE_DB = YES) ===
    if update_db:
        console.print("[cyan][*] Updating WPScan database...[/]")
        try:
            subprocess.run(
                [wpscan, "--update"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=120,
            )
            console.print("[green][+] Database updated successfully![/]")
        except subprocess.TimeoutExpired:
            console.print("[yellow][!] Update timeout, continuing with existing database...[/]")
        except Exception as e:
            console.print(f"[yellow][!] Update error: {e}, continuing...[/]")
    else:
        console.print("[dim][*] Skipping database update (UPDATE_DB = NO)[/]")

    # === DETECT FINAL URL IF FOLLOW_REDIRECT ===
    final_url = url
    if follow_redirect:
        console.print("[dim][*] Checking for redirects...[/]")
        try:
            import requests
            try:
                # Try to follow redirects with HEAD first
                resp = requests.head(url, timeout=10, allow_redirects=True, verify=False)
                final_url = resp.url
                if final_url != url:
                    console.print(f"[yellow][!] Redirect detected: {url} → {final_url}[/]")
                    console.print("[green][+] Using final URL for scan[/]")
                    url = final_url
                else:
                    console.print("[dim][*] No redirect detected[/]")
            except:
                # Fallback to GET if HEAD fails
                resp = requests.get(url, timeout=10, allow_redirects=True, verify=False)
                final_url = resp.url
                if final_url != url:
                    console.print(f"[yellow][!] Redirect detected: {url} → {final_url}[/]")
                    console.print("[green][+] Using final URL for scan[/]")
                    url = final_url
        except Exception as e:
            console.print(f"[yellow][!] Could not check redirects: {e}[/]")
            console.print("[dim][*] Continuing with original URL...[/]")

    # Command utama - gunakan URL yang sudah di-follow redirect
    cmd = [
        wpscan,
        "--url",
        url,
        "--no-banner",
        "--force",
        "--scope",
        "--ignore-main-redirect",  # Keep this just in case
        "--random-user-agent",
        "--max-threads",
        str(threads),
        "--format",
        "cli",
    ]

    # Add follow redirect flag if needed
    if follow_redirect:
        cmd.append("--ignore-main-redirect")

    if api_token:
        cmd.extend(["--api-token", api_token])

    # Mode handling
    if mode == "QUICK":
        cmd.extend(["--detection-mode", "passive"])
        cmd.extend(["--enumerate", "vp"])
    elif mode == "STANDARD":
        cmd.extend(["--enumerate", "vp,vt,u"])
    elif mode == "AGGRESSIVE":
        cmd.extend(
            ["--enumerate", "vp,vt,u,cb,dbe", "--plugins-detection", "aggressive"]
        )
    elif mode == "BRUTEFORCE":
        if not wordlist or not os.path.isfile(wordlist):
            console.print("[bold red][X] WORDLIST tidak ditemukan![/]")
            console.print(f"[yellow]Path: {wordlist}[/]")
            console.print("[yellow]Set path yang benar ke file wordlist[/]")
            return
        cmd.extend(["--passwords", wordlist])
        if usernames:
            cmd.extend(["--usernames", usernames])
        else:
            cmd.extend(["--usernames", "admin"])

    # === RICH BANNER ===
    print_rich_banner(
        title="Wordpress Scanner",
        url=url,
        mode=mode,
        api_token=api_token,
        update_db=update_db,
        threads=threads,
        wordlist=wordlist,
        usernames=usernames,
        follow_redirect=follow_redirect
    )

    console.print(f"[dim]Executing Wordpress Scanner ...[/]\n")

    try:
        env = os.environ.copy()
        env["NO_COLOR"] = "1"
        env["TERM"] = "dumb"

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env,
        )

        for line in process.stdout:
            line = line.rstrip()
            if not line:
                continue

            # Skip progress bar
            if "|" in line and ("=" in line or "-" in line):
                if len(line) > 80 and line.count("|") > 5:
                    continue

            # Skip progress percentage noise
            if "%" in line and "[" in line and "]" in line:
                if line.count("[") > 2:
                    continue

            clean_line = colorize_output(line)
            console.print(clean_line)

        process.wait()

        if process.returncode == 0:
            console.print("\n[bold green][+] WPScan completed successfully![/]")
        else:
            console.print(
                f"\n[yellow][!] WPScan finished with code: {process.returncode}[/]"
            )

    except KeyboardInterrupt:
        console.print("\n[bold red][X] Cancelled by user[/]")
        if "process" in locals():
            process.terminate()
    except Exception as e:
        console.print(f"[bold red][X] Error: {e}[/]")
        import traceback

        console.print(f"[dim]{traceback.format_exc()}[/]")