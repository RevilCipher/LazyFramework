#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Commix Module - Command Injection Exploiter
Automated tool for finding and exploiting command injection vulnerabilities
"""

import os
import sys
import subprocess
import shutil
import re
import time
import json
from pathlib import Path

# Check if commix is installed
COMMIX_CMD = shutil.which("commix")

# Module metadata
MODULE_INFO = {
    "name": "Commix",
    "description": "Command Injection Exploiter - Automated tool for finding and exploiting command injection vulnerabilities",
    "author": "LazyFramework Team (Based on Commix by Anastasios Stasinopoulos)",
    "license": "GPLv3",
    "platform": "Linux,Windows,Macos",
    "arch": "all",
    "rank": "Great",
    "dependencies": [],
    "references": [
        "https://github.com/commixproject/commix",
        "https://www.kali.org/tools/commix/"
    ]
}

# Module options
OPTIONS = {
    # Target
    "URL": {
        "description": "Target URL (e.g., http://target.com/page.php?id=1 or https://target.com/page.php?id=1)",
        "required": True,
        "default": ""
    },
    "FORCE_SSL": {
        "description": "Force usage of SSL/HTTPS",
        "required": False,
        "default": "false"
    },
    "DATA": {
        "description": "Data string to be sent through POST",
        "required": False,
        "default": ""
    },
    "METHOD": {
        "description": "Force usage of given HTTP method (GET, POST, PUT, etc.)",
        "required": False,
        "default": "GET",
        "choices": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
    },
    
    # Request
    "COOKIE": {
        "description": "HTTP Cookie header",
        "required": False,
        "default": ""
    },
    "USER_AGENT": {
        "description": "HTTP User-Agent header",
        "required": False,
        "default": ""
    },
    "RANDOM_AGENT": {
        "description": "Use a randomly selected HTTP User-Agent header",
        "required": False,
        "default": "false"
    },
    "REFERER": {
        "description": "HTTP Referer header",
        "required": False,
        "default": ""
    },
    "HEADERS": {
        "description": "Extra headers (e.g., 'Accept-Language: fr\\nETag: 123')",
        "required": False,
        "default": ""
    },
    "HOST": {
        "description": "HTTP Host header",
        "required": False,
        "default": ""
    },
    "PROXY": {
        "description": "Use a proxy to connect to the target URL (e.g., http://127.0.0.1:8080)",
        "required": False,
        "default": ""
    },
    "TOR": {
        "description": "Use the Tor network",
        "required": False,
        "default": "false"
    },
    "TOR_PORT": {
        "description": "Set Tor proxy port (default: 8118)",
        "required": False,
        "default": "8118"
    },
    "TIMEOUT": {
        "description": "Seconds to wait before timeout connection (default: 30)",
        "required": False,
        "default": "30"
    },
    "RETRIES": {
        "description": "Retries when the connection timeouts (default: 3)",
        "required": False,
        "default": "3"
    },
    "IGNORE_REDIRECTS": {
        "description": "Ignore redirection attempts",
        "required": False,
        "default": "false"
    },
    "AUTH_TYPE": {
        "description": "HTTP authentication type (Basic, Digest, Bearer)",
        "required": False,
        "default": "",
        "choices": ["", "Basic", "Digest", "Bearer"]
    },
    "AUTH_CRED": {
        "description": "HTTP authentication credentials (e.g., 'admin:password')",
        "required": False,
        "default": ""
    },
    
    # Injection
    "TEST_PARAMETER": {
        "description": "Testable parameter(s) (e.g., 'id,page')",
        "required": False,
        "default": ""
    },
    "SKIP": {
        "description": "Skip testing for given parameter(s)",
        "required": False,
        "default": ""
    },
    "PREFIX": {
        "description": "Injection payload prefix string",
        "required": False,
        "default": ""
    },
    "SUFFIX": {
        "description": "Injection payload suffix string",
        "required": False,
        "default": ""
    },
    "TECHNIQUE": {
        "description": "Specify injection technique(s) to use",
        "required": False,
        "default": "",
        "choices": ["", "classic", "eval-based", "time-based", "file-based"]
    },
    "DELAY": {
        "description": "Seconds to delay between each HTTP request",
        "required": False,
        "default": ""
    },
    "TIME_SEC": {
        "description": "Seconds to delay the OS response",
        "required": False,
        "default": ""
    },
    "TAMPER": {
        "description": "Use given script(s) for tampering injection data",
        "required": False,
        "default": ""
    },
    "SKIP_WAF": {
        "description": "Skip heuristic detection of WAF/IPS protection",
        "required": False,
        "default": "false"
    },
    "LEVEL": {
        "description": "Level of tests to perform (1-3, default: 1)",
        "required": False,
        "default": "1"
    },
    
    # Enumeration
    "ALL": {
        "description": "Retrieve everything (current user, hostname, system info, etc.)",
        "required": False,
        "default": "false"
    },
    "CURRENT_USER": {
        "description": "Retrieve current user name",
        "required": False,
        "default": "false"
    },
    "HOSTNAME": {
        "description": "Retrieve current hostname",
        "required": False,
        "default": "false"
    },
    "SYS_INFO": {
        "description": "Retrieve system information",
        "required": False,
        "default": "false"
    },
    "USERS": {
        "description": "Retrieve system users",
        "required": False,
        "default": "false"
    },
    "PASSWORDS": {
        "description": "Retrieve system users password hashes",
        "required": False,
        "default": "false"
    },
    "PRIVILEGES": {
        "description": "Retrieve system users privileges",
        "required": False,
        "default": "false"
    },
    "IS_ROOT": {
        "description": "Check if the current user has root privileges",
        "required": False,
        "default": "false"
    },
    "IS_ADMIN": {
        "description": "Check if the current user has admin privileges",
        "required": False,
        "default": "false"
    },
    
    # File Access
    "FILE_READ": {
        "description": "Read a file from the target host (e.g., /etc/passwd)",
        "required": False,
        "default": ""
    },
    "FILE_WRITE": {
        "description": "Write to a file on the target host",
        "required": False,
        "default": ""
    },
    "FILE_UPLOAD": {
        "description": "Upload a file on the target host",
        "required": False,
        "default": ""
    },
    "FILE_DEST": {
        "description": "Host's absolute filepath to write and/or upload to",
        "required": False,
        "default": ""
    },
    
    # Command Execution
    "OS_CMD": {
        "description": "Execute a single operating system command",
        "required": False,
        "default": ""
    },
    "OS": {
        "description": "Force back-end operating system (Windows or Unix)",
        "required": False,
        "default": "",
        "choices": ["", "Windows", "Unix"]
    },
    "ALTER_SHELL": {
        "description": "Use an alternative os-shell (e.g., 'Python')",
        "required": False,
        "default": ""
    },
    
    # General
    "VERBOSE": {
        "description": "Verbosity level (0-4, default: 0)",
        "required": False,
        "default": "0"
    },
    "BATCH": {
        "description": "Never ask for user input, use the default behaviour",
        "required": False,
        "default": "true"
    },
    "SESSION_FILE": {
        "description": "Load session from a stored (.sqlite) file",
        "required": False,
        "default": ""
    },
    "SAVE_OUTPUT": {
        "description": "Save output to file",
        "required": False,
        "default": ""
    },
    "OUTPUT_DIR": {
        "description": "Set custom output directory path",
        "required": False,
        "default": ""
    },
    "IGNORE_PROXY": {
        "description": "Ignore system default proxy settings",
        "required": False,
        "default": "false"
    }
}


def check_dependencies():
    """Check if commix is installed"""
    if COMMIX_CMD is None:
        print("[!] Commix not found.")
        print("[!] Install on Kali: sudo apt install commix")
        print("[!] Or from: https://github.com/commixproject/commix")
        return False
    
    # Check version
    try:
        result = subprocess.run([COMMIX_CMD, "--version"], 
                               capture_output=True, text=True, timeout=5)
        version_line = result.stdout.strip() or result.stderr.strip()
        if version_line:
            print(f"[*] Using: {version_line.splitlines()[0]}")
        else:
            print(f"[*] Using: {COMMIX_CMD}")
    except Exception as e:
        print(f"[!] Error checking commix version: {e}")
        return False
    
    return True


def build_command(options, session):
    """
    Build commix command based on options
    """
    cmd = [COMMIX_CMD]
    
    # --- Target ---
    url = options.get("URL", "")
    if url:
        # If URL is HTTP and force_ssl is true, convert to HTTPS
        force_ssl = options.get("FORCE_SSL", "false").lower() == "true"
        if force_ssl and url.startswith("http://"):
            url = url.replace("http://", "https://")
            print(f"[*] Forcing SSL: {url}")
        cmd.append("-u")
        cmd.append(url)
    else:
        print("[!] URL is required")
        return None
    
    # Force SSL flag
    if options.get("FORCE_SSL", "false").lower() == "true":
        cmd.append("--force-ssl")
    
    # Data (POST)
    data = options.get("DATA", "")
    if data:
        cmd.append("--data")
        cmd.append(data)
    
    # Method
    method = options.get("METHOD", "GET").upper()
    if method and method != "GET":
        cmd.append("--method")
        cmd.append(method)
    
    # --- Request ---
    cookie = options.get("COOKIE", "")
    if cookie:
        cmd.append("--cookie")
        cmd.append(cookie)
    
    user_agent = options.get("USER_AGENT", "")
    if user_agent:
        cmd.append("--user-agent")
        cmd.append(user_agent)
    
    if options.get("RANDOM_AGENT", "false").lower() == "true":
        cmd.append("--random-agent")
    
    referer = options.get("REFERER", "")
    if referer:
        cmd.append("--referer")
        cmd.append(referer)
    
    headers = options.get("HEADERS", "")
    if headers:
        cmd.append("--headers")
        cmd.append(headers)
    
    host = options.get("HOST", "")
    if host:
        cmd.append("--host")
        cmd.append(host)
    
    proxy = options.get("PROXY", "")
    if proxy:
        cmd.append("--proxy")
        cmd.append(proxy)
    
    # Tor
    if options.get("TOR", "false").lower() == "true":
        cmd.append("--tor")
        tor_port = options.get("TOR_PORT", "8118")
        if tor_port and tor_port != "8118":
            cmd.append("--tor-port")
            cmd.append(str(tor_port))
    
    timeout = options.get("TIMEOUT", "30")
    cmd.append("--timeout")
    cmd.append(str(timeout))
    
    retries = options.get("RETRIES", "3")
    cmd.append("--retries")
    cmd.append(str(retries))
    
    if options.get("IGNORE_REDIRECTS", "false").lower() == "true":
        cmd.append("--ignore-redirects")
    
    if options.get("IGNORE_PROXY", "false").lower() == "true":
        cmd.append("--ignore-proxy")
    
    # Authentication
    auth_type = options.get("AUTH_TYPE", "")
    if auth_type:
        cmd.append("--auth-type")
        cmd.append(auth_type)
    
    auth_cred = options.get("AUTH_CRED", "")
    if auth_cred:
        cmd.append("--auth-cred")
        cmd.append(auth_cred)
    
    # --- Injection ---
    test_param = options.get("TEST_PARAMETER", "")
    if test_param:
        cmd.append("-p")
        cmd.append(test_param)
    
    skip = options.get("SKIP", "")
    if skip:
        cmd.append("--skip")
        cmd.append(skip)
    
    prefix = options.get("PREFIX", "")
    if prefix:
        cmd.append("--prefix")
        cmd.append(prefix)
    
    suffix = options.get("SUFFIX", "")
    if suffix:
        cmd.append("--suffix")
        cmd.append(suffix)
    
    technique = options.get("TECHNIQUE", "")
    if technique:
        cmd.append("--technique")
        cmd.append(technique)
    
    delay = options.get("DELAY", "")
    if delay:
        cmd.append("--delay")
        cmd.append(str(delay))
    
    time_sec = options.get("TIME_SEC", "")
    if time_sec:
        cmd.append("--time-sec")
        cmd.append(str(time_sec))
    
    tamper = options.get("TAMPER", "")
    if tamper:
        cmd.append("--tamper")
        cmd.append(tamper)
    
    if options.get("SKIP_WAF", "false").lower() == "true":
        cmd.append("--skip-waf")
    
    level = options.get("LEVEL", "1")
    if level and int(level) > 1:
        cmd.append("--level")
        cmd.append(str(level))
    
    # --- Enumeration ---
    if options.get("ALL", "false").lower() == "true":
        cmd.append("--all")
    else:
        if options.get("CURRENT_USER", "false").lower() == "true":
            cmd.append("--current-user")
        if options.get("HOSTNAME", "false").lower() == "true":
            cmd.append("--hostname")
        if options.get("SYS_INFO", "false").lower() == "true":
            cmd.append("--sys-info")
        if options.get("USERS", "false").lower() == "true":
            cmd.append("--users")
        if options.get("PASSWORDS", "false").lower() == "true":
            cmd.append("--passwords")
        if options.get("PRIVILEGES", "false").lower() == "true":
            cmd.append("--privileges")
        if options.get("IS_ROOT", "false").lower() == "true":
            cmd.append("--is-root")
        if options.get("IS_ADMIN", "false").lower() == "true":
            cmd.append("--is-admin")
    
    # --- File Access ---
    file_read = options.get("FILE_READ", "")
    if file_read:
        cmd.append("--file-read")
        cmd.append(file_read)
    
    file_write = options.get("FILE_WRITE", "")
    if file_write:
        cmd.append("--file-write")
        cmd.append(file_write)
    
    file_upload = options.get("FILE_UPLOAD", "")
    if file_upload:
        cmd.append("--file-upload")
        cmd.append(file_upload)
    
    file_dest = options.get("FILE_DEST", "")
    if file_dest:
        cmd.append("--file-dest")
        cmd.append(file_dest)
    
    # --- Command Execution ---
    os_cmd = options.get("OS_CMD", "")
    if os_cmd:
        cmd.append("--os-cmd")
        cmd.append(os_cmd)
    
    os_type = options.get("OS", "")
    if os_type:
        cmd.append("--os")
        cmd.append(os_type)
    
    alter_shell = options.get("ALTER_SHELL", "")
    if alter_shell:
        cmd.append("--alter-shell")
        cmd.append(alter_shell)
    
    # --- General ---
    verbose = options.get("VERBOSE", "0")
    if verbose and int(verbose) > 0:
        cmd.append("-v")
        cmd.append(str(verbose))
    
    if options.get("BATCH", "true").lower() == "true":
        cmd.append("--batch")
    
    session_file = options.get("SESSION_FILE", "")
    if session_file:
        cmd.append("-s")
        cmd.append(session_file)
    
    output_dir = options.get("OUTPUT_DIR", "")
    if output_dir:
        cmd.append("--output-dir")
        cmd.append(output_dir)
    
    return cmd


def parse_output(output_text):
    """
    Parse commix output and extract structured information
    """
    results = {
        "vulnerable": False,
        "injection_points": [],
        "command_output": "",
        "enumeration": {},
        "file_operations": {},
        "errors": [],
        "technique_used": "",
        "target_info": {}
    }
    
    lines = output_text.splitlines()
    
    # Look for injection success indicators
    success_patterns = [
        r"\[+\].*vulnerable",
        r"\[+\].*injection",
        r"\[+\].*command",
        r"\[+\].*executed",
        r"\[+\].*found",
        r"\[+\].*success",
        r"The injection is (exploitable|vulnerable)",
        r"Command injection vulnerable",
        r"Parameter '(\w+)' seems vulnerable",
        r"Vulnerable to command injection",
        r"\[+\].*parameter.*vulnerable",
        r"\[+\].*exploitable",
    ]
    
    # Look for parameter extraction
    param_pattern = r"Parameter '(\w+)' seems vulnerable"
    
    # Look for technique used
    technique_pattern = r"\[+\].*technique.*:?\s*(\w+)"
    
    # Look for target info
    target_patterns = {
        "url": r"Target URL:\s*(.+)$",
        "host": r"Host:\s*(.+)$",
        "os": r"Operating system:\s*(.+)$",
        "web_server": r"Web server:\s*(.+)$",
        "tech": r"Technique:\s*(.+)$",
    }
    
    for line in lines:
        # Check for vulnerability indicators
        for pattern in success_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                results["vulnerable"] = True
                param_match = re.search(param_pattern, line)
                if param_match:
                    results["injection_points"].append(param_match.group(1))
                break
        
        # Check for technique
        tech_match = re.search(technique_pattern, line, re.IGNORECASE)
        if tech_match:
            results["technique_used"] = tech_match.group(1)
        
        # Target info
        for key, pattern in target_patterns.items():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                results["target_info"][key] = match.group(1)
        
        # Capture command output
        if "[+] Command output:" in line or "Command output:" in line:
            results["command_output"] = line
        elif results["command_output"] and line.strip() and not line.startswith("["):
            results["command_output"] += "\n" + line.strip()
        
        # Capture enumeration data
        if "current user" in line.lower() and ":" in line:
            results["enumeration"]["current_user"] = line
        elif "hostname" in line.lower() and ":" in line:
            results["enumeration"]["hostname"] = line
        elif "system info" in line.lower() or "os" in line.lower():
            results["enumeration"]["system_info"] = line
        elif "users" in line.lower() and ":" in line:
            results["enumeration"]["users"] = line
        elif "password" in line.lower() and ":" in line:
            results["enumeration"]["passwords"] = line
        
        # Capture file operations
        if "file read" in line.lower() or "read file" in line.lower():
            results["file_operations"]["read"] = line
        elif "file write" in line.lower() or "write file" in line.lower():
            results["file_operations"]["write"] = line
        elif "upload" in line.lower():
            results["file_operations"]["upload"] = line
    
    return results


def print_results(results, options):
    """
    Print structured results in a readable format
    """
    print("\n" + "=" * 70)
    print("C O M M I X   R E S U L T S")
    print("=" * 70)
    
    # Target info
    if results.get("target_info"):
        print("\n[*] Target Information:")
        for key, value in results["target_info"].items():
            if value:
                print(f"    {key.replace('_', ' ').title()}: {value}")
    
    # Vulnerability status
    if results.get("vulnerable", False):
        print("\n[+] VULNERABLE TO COMMAND INJECTION!")
        if results.get("injection_points"):
            print(f"[+] Injection points found: {', '.join(results['injection_points'])}")
        if results.get("technique_used"):
            print(f"[+] Technique used: {results['technique_used']}")
    else:
        print("\n[!] No command injection vulnerability detected")
        print("[*] Try different parameters, techniques, or payloads")
        print("[*] Consider:")
        print("    - Using --level 2 or --level 3 for deeper testing")
        print("    - Specifying testable parameters with -p")
        print("    - Using custom prefixes/suffixes")
        print("    - Trying different injection techniques")
    
    # Command output
    if results.get("command_output"):
        print("\n" + "-" * 70)
        print("[*] Command Output:")
        print("-" * 70)
        print(results["command_output"])
    
    # Enumeration results
    if results.get("enumeration"):
        print("\n" + "-" * 70)
        print("[*] Enumeration Results:")
        print("-" * 70)
        for key, value in results["enumeration"].items():
            if value:
                print(f"  {key.replace('_', ' ').title()}: {value}")
    
    # File operations
    if results.get("file_operations"):
        print("\n" + "-" * 70)
        print("[*] File Operations:")
        print("-" * 70)
        for key, value in results["file_operations"].items():
            if value:
                print(f"  {key.title()}: {value}")
    
    # Save output if requested
    save_output = options.get("SAVE_OUTPUT", "")
    if save_output:
        try:
            with open(save_output, 'w') as f:
                f.write(json.dumps(results, indent=2))
            print(f"\n[*] Results saved to: {save_output}")
        except Exception as e:
            print(f"[!] Error saving output: {e}")
    
    print("\n" + "=" * 70)


def run(session, options):
    """
    Main entry point for the module
    
    Args:
        session: Framework session dictionary
        options: Module options dictionary
    
    Returns:
        dict: Results from the commix execution
    """
    # Check dependencies
    if not check_dependencies():
        return {"error": "Commix not installed"}
    
    # Build command
    cmd = build_command(options, session)
    if cmd is None:
        return {"error": "Failed to build command"}
    
    print(f"[*] Running: {' '.join(cmd)}")
    print("[*] Scanning for command injection vulnerabilities...")
    print("[*] (This may take some time depending on target and techniques)")
    
    # Run commix
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        full_output = []
        
        # Print output in real-time
        for line in process.stdout:
            print(line.rstrip())
            full_output.append(line)
        
        process.wait()
        
        # Parse output
        output_text = "".join(full_output)
        results = parse_output(output_text)
        
        # Print structured results
        print_results(results, options)
        
        # Save to session
        session["commix_results"] = results
        
        return results
        
    except Exception as e:
        print(f"[!] Error running commix: {e}")
        return {"error": str(e)}