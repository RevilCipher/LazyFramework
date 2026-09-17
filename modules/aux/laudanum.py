#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Laudanum Module - Collection of injection-ready code
Web shells and payloads for ASP, ASPX, CFM, JSP, PHP, and WordPress
"""

import os
import sys
import subprocess
import shutil
import re
import time
import json
import glob
from pathlib import Path

# Laudanum directory
LAUDANUM_DIR = "/usr/share/laudanum"

# Module metadata
MODULE_INFO = {
    "name": "Laudanum Collection",
    "description": "Collection of injection-ready code for ASP, ASPX, CFM, JSP, PHP, and WordPress",
    "author": "RevilCipher",
    "license": "GPLv2+",
    "platform": "linux",
    "arch": "all",
    "rank": "Great",
    "dependencies": [],
    "references": [
        "https://github.com/jfitz/laudanum",
        "https://www.kali.org/tools/laudanum/"
    ]
}

# Module options
OPTIONS = {
    "ACTION": {
        "description": "Action to perform: list|search|copy|info|generate",
        "required": True,
        "default": "list",
        "choices": ["list", "search", "copy", "info", "generate"]
    },
    "TYPE": {
        "description": "Type: asp|aspx|cfm|jsp|php|wordpress|helpers|all",
        "required": False,
        "default": "all",
        "choices": ["all", "asp", "aspx", "cfm", "jsp", "php", "wordpress", "helpers"]
    },
    "SEARCH": {
        "description": "Search pattern (for search action)",
        "required": False,
        "default": ""
    },
    "SOURCE": {
        "description": "Source file path (for copy action)",
        "required": False,
        "default": ""
    },
    "DEST": {
        "description": "Destination file path (for copy action)",
        "required": False,
        "default": ""
    },
    "SHOW_CONTENT": {
        "description": "Show file content (for info action)",
        "required": False,
        "default": "false"
    },
    "SAVE_OUTPUT": {
        "description": "Save output to file",
        "required": False,
        "default": ""
    },
    "LIST_FILES": {
        "description": "List available files before copy",
        "required": False,
        "default": "false"
    }
}


def check_laudanum_dir():
    """Check if laudanum directory exists"""
    if not os.path.exists(LAUDANUM_DIR):
        print(f"[!] Laudanum directory not found: {LAUDANUM_DIR}")
        print("[!] Install on Kali: sudo apt install laudanum")
        return False
    
    print(f"[*] Laudanum directory: {LAUDANUM_DIR}")
    return True


def find_laudanum_file(filename, file_type="all"):
    """Find a file by name, searching all types"""
    
    if file_type == "all":
        types = ["asp", "aspx", "cfm", "jsp", "php", "wordpress", "helpers"]
    else:
        types = [file_type]
    
    found_files = []
    
    for t in types:
        type_dir = os.path.join(LAUDANUM_DIR, t)
        if not os.path.exists(type_dir):
            continue
        
        # Search recursively
        for root, dirs, files in os.walk(type_dir):
            for file in files:
                if file == filename or file.lower() == filename.lower():
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, LAUDANUM_DIR)
                    found_files.append({
                        "name": file,
                        "path": rel_path,
                        "full_path": full_path,
                        "type": t,
                        "size": os.path.getsize(full_path),
                        "size_str": format_size(os.path.getsize(full_path))
                    })
    
    return found_files


def list_laudanum(file_type="all", show_details=True):
    """List files by type"""
    
    if file_type == "all":
        types = ["asp", "aspx", "cfm", "jsp", "php", "wordpress", "helpers"]
    else:
        types = [file_type]
    
    results = {
        "total_files": 0,
        "files_by_type": {},
        "all_files": []
    }
    
    print("\n" + "=" * 70)
    print("  L A U D A N U M   C O L L E C T I O N")
    print("=" * 70)
    
    for t in types:
        type_dir = os.path.join(LAUDANUM_DIR, t)
        if not os.path.exists(type_dir):
            print(f"\n[!] {t.upper()} directory not found: {type_dir}")
            continue
        
        files = []
        for root, dirs, filenames in os.walk(type_dir):
            for filename in filenames:
                # Skip hidden files
                if filename.startswith('.'):
                    continue
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, LAUDANUM_DIR)
                size = os.path.getsize(full_path)
                files.append({
                    "name": filename,
                    "path": rel_path,
                    "full_path": full_path,
                    "size": size,
                    "size_str": format_size(size)
                })
        
        results["files_by_type"][t] = files
        results["all_files"].extend(files)
        results["total_files"] += len(files)
        
        print(f"\n[bold cyan]── {t.upper()} ({len(files)} files) ──[/]")
        
        if files and show_details:
            # Group by subdirectory
            by_dir = {}
            for f in files:
                dir_name = os.path.dirname(f["path"])
                if dir_name not in by_dir:
                    by_dir[dir_name] = []
                by_dir[dir_name].append(f)
            
            for dir_name, file_list in sorted(by_dir.items()):
                if dir_name == t:
                    print(f"  [dim]{dir_name}/[/]")
                else:
                    print(f"  [dim]{dir_name}/[/]")
                for f in sorted(file_list, key=lambda x: x["name"]):
                    print(f"    {f['name']} [dim]({f['size_str']})[/]")
        else:
            # Simple list
            for f in sorted(files, key=lambda x: x["name"]):
                print(f"  {f['name']}")
    
    print("\n" + "-" * 70)
    print(f"Total files: {results['total_files']}")
    print("=" * 70)
    
    return results


def search_laudanum(pattern, file_type="all"):
    """Search files by pattern in filename and content"""
    
    if not pattern:
        print("[!] Search pattern is required")
        return None
    
    if file_type == "all":
        types = ["asp", "aspx", "cfm", "jsp", "php", "wordpress", "helpers"]
    else:
        types = [file_type]
    
    results = {
        "by_filename": [],
        "by_content": [],
        "total_matches": 0
    }
    
    print("\n" + "=" * 70)
    print(f"  S E A R C H I N G   L A U D A N U M   -   '{pattern}'")
    print("=" * 70)
    
    pattern_lower = pattern.lower()
    
    for t in types:
        type_dir = os.path.join(LAUDANUM_DIR, t)
        if not os.path.exists(type_dir):
            continue
        
        print(f"\n[*] Searching in {t.upper()}...")
        
        for root, dirs, filenames in os.walk(type_dir):
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, LAUDANUM_DIR)
                
                # Check filename
                if pattern_lower in filename.lower():
                    results["by_filename"].append({
                        "file": rel_path,
                        "type": t,
                        "match": "filename",
                        "full_path": full_path
                    })
                    results["total_matches"] += 1
                    print(f"  [green][+] Found in filename: {rel_path}[/]")
                    continue
                
                # Check content (only for small files)
                try:
                    if os.path.getsize(full_path) < 1024 * 100:  # 100KB max
                        with open(full_path, 'r', errors='ignore') as f:
                            content = f.read()
                            if pattern_lower in content.lower():
                                results["by_content"].append({
                                    "file": rel_path,
                                    "type": t,
                                    "match": "content",
                                    "full_path": full_path
                                })
                                results["total_matches"] += 1
                                print(f"  [green][+] Found in content: {rel_path}[/]")
                except:
                    pass
    
    print("\n" + "-" * 70)
    print(f"Total matches: {results['total_matches']}")
    print(f"  Filename matches: {len(results['by_filename'])}")
    print(f"  Content matches: {len(results['by_content'])}")
    print("=" * 70)
    
    return results


def copy_laudanum(source, dest, file_type="all"):
    """Copy a file to destination with improved path handling"""
    
    if not source:
        print("[!] Source file is required")
        return False
    
    if not dest:
        print("[!] Destination path is required")
        return False
    
    # Check if dest is a directory
    if os.path.isdir(dest):
        dest = os.path.join(dest, os.path.basename(source))
        print(f"[*] Destination is directory, using: {dest}")
    
    # Create destination directory if needed
    dest_dir = os.path.dirname(dest)
    if dest_dir and not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
    
    # Try multiple ways to find the source file
    source_path = None
    
    # 1. Check if source is absolute path
    if os.path.exists(source):
        source_path = source
    else:
        # 2. Check if source is relative to laudanum dir
        full_path = os.path.join(LAUDANUM_DIR, source)
        if os.path.exists(full_path):
            source_path = full_path
        else:
            # 3. Check if source is just a filename
            found = find_laudanum_file(source, file_type)
            if found:
                if len(found) == 1:
                    source_path = found[0]["full_path"]
                    print(f"[*] Found file: {found[0]['path']}")
                else:
                    print(f"[!] Multiple files found with name '{source}':")
                    for f in found:
                        print(f"    {f['path']} [dim]({f['size_str']})[/]")
                    print(f"\n[!] Please specify full path or use the exact filename")
                    return False
            else:
                print(f"[!] File not found: {source}")
                print(f"[*] Searched in: {LAUDANUM_DIR}")
                print("[*] Try using 'ACTION list' to see available files")
                return False
    
    if not source_path:
        print(f"[!] Could not locate source file: {source}")
        return False
    
    print(f"[*] Copying: {source_path}")
    print(f"[*] To: {dest}")
    
    try:
        shutil.copy2(source_path, dest)
        print(f"[+] File copied successfully")
        print(f"[*] Size: {format_size(os.path.getsize(dest))}")
        print(f"[*] Destination: {dest}")
        return True
    except Exception as e:
        print(f"[!] Error copying file: {e}")
        return False


def generate_laudanum(file_type="php"):
    """Generate a Laudanum payload (simplified - actually just lists available templates)"""
    
    type_dir = os.path.join(LAUDANUM_DIR, file_type)
    if not os.path.exists(type_dir):
        print(f"[!] Directory not found: {type_dir}")
        return None
    
    print("\n" + "=" * 70)
    print(f"  G E N E R A T I N G   {file_type.upper()}   P A Y L O A D")
    print("=" * 70)
    
    print(f"\n[*] Available templates in {file_type.upper()}:")
    
    templates = []
    for root, dirs, filenames in os.walk(type_dir):
        for filename in filenames:
            if filename.startswith('.'):
                continue
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, LAUDANUM_DIR)
            size = os.path.getsize(full_path)
            templates.append({
                "name": filename,
                "path": rel_path,
                "full_path": full_path,
                "size": size,
                "size_str": format_size(size)
            })
    
    for t in sorted(templates, key=lambda x: x["name"]):
        print(f"  {t['name']} [dim]({t['size_str']})[/]")
    
    print("\n" + "-" * 70)
    print("[*] To use a template:")
    print(f"  ACTION copy SOURCE={file_type}/filename.php DEST=/path/to/dest")
    print("=" * 70)
    
    return templates


def get_laudanum_info(file_path, show_content=False, file_type="all"):
    """Get information about a file"""
    
    if not file_path:
        print("[!] File path is required")
        return None
    
    # Find the file
    full_path = None
    
    # Check if absolute path exists
    if os.path.exists(file_path):
        full_path = file_path
    else:
        # Check relative to laudanum dir
        test_path = os.path.join(LAUDANUM_DIR, file_path)
        if os.path.exists(test_path):
            full_path = test_path
        else:
            # Search by filename
            found = find_laudanum_file(file_path, file_type)
            if found:
                if len(found) == 1:
                    full_path = found[0]["full_path"]
                else:
                    print(f"[!] Multiple files found with name '{file_path}':")
                    for f in found:
                        print(f"    {f['path']} [dim]({f['size_str']})[/]")
                    print(f"\n[!] Please specify full path")
                    return None
            else:
                print(f"[!] File not found: {file_path}")
                return None
    
    if not full_path:
        print(f"[!] Could not locate file: {file_path}")
        return None
    
    print("\n" + "=" * 70)
    print(f"  F I L E   I N F O   -   {os.path.basename(full_path)}")
    print("=" * 70)
    
    # Basic info
    stat = os.stat(full_path)
    rel_path = os.path.relpath(full_path, LAUDANUM_DIR)
    
    print(f"\n[*] File: {rel_path}")
    print(f"[*] Full path: {full_path}")
    print(f"[*] Size: {format_size(stat.st_size)}")
    print(f"[*] Modified: {time.ctime(stat.st_mtime)}")
    print(f"[*] Permissions: {oct(stat.st_mode)[-3:]}")
    
    # Detect type
    ext = os.path.splitext(full_path)[1].lower()
    type_map = {
        '.php': 'PHP',
        '.asp': 'ASP',
        '.aspx': 'ASP.NET',
        '.jsp': 'JSP',
        '.cfm': 'ColdFusion',
        '.pl': 'Perl',
        '.cgi': 'CGI',
        '.sql': 'SQL',
        '.js': 'JavaScript',
        '.txt': 'Text'
    }
    file_type_detected = type_map.get(ext, 'Unknown')
    print(f"[*] Type: {file_type_detected}")
    
    # Try to find description in file
    try:
        with open(full_path, 'r', errors='ignore') as f:
            content = f.read(4096)  # First 4KB
            # Look for common patterns
            patterns = {
                'author': r'(?:author|created by|written by)[:]\s*(.+)$',
                'description': r'(?:description|about|function)[:]\s*(.+)$',
                'version': r'(?:version|v)[:]\s*([\d.]+)',
                'purpose': r'(?:purpose|usage|use)[:]\s*(.+)$',
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if match:
                    print(f"[*] {key.capitalize()}: {match.group(1).strip()}")
    
    except:
        pass
    
    # Show content preview
    if show_content:
        print("\n" + "-" * 70)
        print("C O N T E N T   P R E V I E W")
        print("-" * 70)
        try:
            with open(full_path, 'r', errors='ignore') as f:
                content = f.read(4096)
                print(content)
                if len(content) >= 4096:
                    print("\n[dim]... (truncated, use cat to see full content)[/]")
        except:
            print("[!] Could not read file content")
    
    print("\n" + "=" * 70)
    
    return {
        "file": rel_path,
        "full_path": full_path,
        "size": stat.st_size,
        "size_str": format_size(stat.st_size),
        "type": file_type_detected,
        "modified": time.ctime(stat.st_mtime),
        "permissions": oct(stat.st_mode)[-3:]
    }


def format_size(size):
    """Format file size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def print_banner(action, file_type):
    """Print banner"""
    print("")
    print("=" * 70)
    print("  L A U D A N U M   C O L L E C T I O N")
    print("=" * 70)
    print(f"  Action: {action.upper()}")
    print(f"  Type: {file_type.upper()}")
    print("=" * 70)
    print("")


def run(session, options):
    """
    Main entry point for the module
    
    Args:
        session: Framework session dictionary
        options: Module options dictionary
    
    Returns:
        dict: Results from the laudanum operations
    """
    # Check laudanum directory
    if not check_laudanum_dir():
        return {"error": "Laudanum directory not found"}
    
    # Get options
    action = options.get("ACTION", "list").lower()
    file_type = options.get("TYPE", "all").lower()
    search_pattern = options.get("SEARCH", "").strip()
    source = options.get("SOURCE", "").strip()
    dest = options.get("DEST", "").strip()
    show_content = options.get("SHOW_CONTENT", "false").lower() == "true"
    save_output = options.get("SAVE_OUTPUT", "").strip()
    list_files = options.get("LIST_FILES", "false").lower() == "true"
    
    print_banner(action, file_type)
    
    # If list_files is true, show available files first
    if list_files and action in ["copy", "info"]:
        print("[*] Available files in Laudanum collection:")
        list_laudanum(file_type, show_details=True)
        print("\n")
    
    results = None
    
    # Execute action
    if action == "list":
        results = list_laudanum(file_type)
        
    elif action == "search":
        if not search_pattern:
            print("[!] SEARCH pattern is required")
            return {"error": "Search pattern is required"}
        results = search_laudanum(search_pattern, file_type)
        
    elif action == "copy":
        if not source:
            print("[!] SOURCE is required")
            print("[*] Example: SOURCE=php/simple-backdoor.php")
            print("[*] Or just: SOURCE=simple-backdoor.php")
            return {"error": "Source file is required"}
        if not dest:
            print("[!] DEST is required")
            print("[*] Example: DEST=/home/user/shell.php")
            return {"error": "Destination path is required"}
        
        success = copy_laudanum(source, dest, file_type)
        results = {"success": success, "source": source, "dest": dest}
        
    elif action == "info":
        if not source:
            print("[!] SOURCE is required")
            return {"error": "File path is required"}
        results = get_laudanum_info(source, show_content, file_type)
        
    elif action == "generate":
        results = generate_laudanum(file_type)
        
    else:
        print(f"[!] Unknown action: {action}")
        return {"error": f"Unknown action: {action}"}
    
    # Save output
    if save_output and results:
        try:
            with open(save_output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n[*] Results saved to: {save_output}")
        except Exception as e:
            print(f"[!] Error saving output: {e}")
    
    # Save to session
    session["laudanum_results"] = results
    
    return results