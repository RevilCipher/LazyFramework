#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patator Module - Multi-purpose brute-force tool
Based on Patator 1.1.0 by lanjelot
"""

import os
import sys
import subprocess
import shutil
import re
import time
import threading
import queue
from pathlib import Path

# Check if patator is installed
PATATOR_CMD = shutil.which("patator")

# Module metadata
MODULE_INFO = {
    "name": "Patator",
    "description": "Multi-purpose brute-force tool supporting FTP, SSH, HTTP, SMTP, SMB, MySQL, and many more protocols",
    "author": "LazyFramework Team (Based on Patator by lanjelot)",
    "license": "GPLv2",
    "platform": "linux,windows,macos",
    "arch": "all",
    "rank": "Great",
    "dependencies": [],
    "references": [
        "https://github.com/lanjelot/patator",
        "https://www.kali.org/tools/patator/"
    ]
}

# Module options
OPTIONS = {
    "MODULE": {
        "description": "Patator module to use",
        "required": True,
        "default": "ftp_login",
        "choices": [
            "ftp_login", "ssh_login", "telnet_login", "smtp_login", "smtp_vrfy",
            "smtp_rcpt", "finger_lookup", "http_fuzz", "rdp_gateway", "ajp_fuzz",
            "pop_login", "pop_passd", "imap_login", "ldap_login", "dcom_login",
            "smb_login", "smb_lookupsid", "rlogin_login", "vmauthd_login",
            "mssql_login", "oracle_login", "mysql_login", "mysql_query",
            "rdp_login", "pgsql_login", "vnc_login", "dns_forward", "dns_reverse",
            "snmp_login", "ike_enum", "unzip_pass", "keystore_pass",
            "sqlcipher_pass", "umbraco_crack", "tcp_fuzz", "dummy_test"
        ]
    },
    "HOST": {
        "description": "Target host (IP or domain)",
        "required": True,
        "default": "127.0.0.1"
    },
    "PORT": {
        "description": "Target port (auto-detected if not specified)",
        "required": False,
        "default": ""
    },
    "USER_FILE": {
        "description": "Path to username wordlist (use with user and/or pass file)",
        "required": False,
        "default": ""
    },
    "PASS_FILE": {
        "description": "Path to password wordlist (use with user and/or pass file)",
        "required": False,
        "default": ""
    },
    "USER": {
        "description": "Single username to use (if no USER_FILE provided)",
        "required": False,
        "default": "admin"
    },
    "PASS": {
        "description": "Single password to use (if no PASS_FILE provided)",
        "required": False,
        "default": ""
    },
    "THREADS": {
        "description": "Number of threads",
        "required": False,
        "default": "5"
    },
    "TIMEOUT": {
        "description": "Connection timeout in seconds",
        "required": False,
        "default": "10"
    },
    "MAX_RETRIES": {
        "description": "Maximum retries per attempt",
        "required": False,
        "default": "3"
    },
    "VERBOSE": {
        "description": "Verbose output",
        "required": False,
        "default": "false"
    },
    "URL": {
        "description": "URL for HTTP fuzzing (http_fuzz module)",
        "required": False,
        "default": ""
    },
    "METHOD": {
        "description": "HTTP method (GET/POST) for http_fuzz",
        "required": False,
        "default": "GET"
    },
    "DATA": {
        "description": "POST data template for http_fuzz (e.g., 'user=FILE0&pass=FILE1')",
        "required": False,
        "default": ""
    },
    "HEADER": {
        "description": "HTTP headers for http_fuzz (e.g., 'Cookie: session=123')",
        "required": False,
        "default": ""
    },
    "SNMP_COMMUNITY": {
        "description": "SNMP community string (snmp_login)",
        "required": False,
        "default": "public"
    },
    "IKE_TRANSFORMS": {
        "description": "IKE transforms file (ike_enum)",
        "required": False,
        "default": ""
    },
    "ZIP_FILE": {
        "description": "Encrypted ZIP file path (unzip_pass)",
        "required": False,
        "default": ""
    },
    "KEYSTORE_FILE": {
        "description": "Java keystore file path (keystore_pass)",
        "required": False,
        "default": ""
    },
    "QUERY": {
        "description": "SQL query for mysql_query module",
        "required": False,
        "default": "SELECT version()"
    },
    "DB_NAME": {
        "description": "Database name (mysql_login, mssql_login, pgsql_login)",
        "required": False,
        "default": ""
    },
    "DOMAIN": {
        "description": "Domain for SMB login (smb_login)",
        "required": False,
        "default": ""
    },
    "EXTRA_ARGS": {
        "description": "Additional command-line arguments (use with caution)",
        "required": False,
        "default": ""
    },
    "IGNORE_CODES": {
        "description": "Status codes to ignore (e.g., '530,500')",
        "required": False,
        "default": ""
    },
    "HITS_FILE": {
        "description": "Save found credentials to file",
        "required": False,
        "default": ""
    }
}


def check_dependencies():
    """Check if patator is installed"""
    if PATATOR_CMD is None:
        print("[!] Patator not found. Install with: pip install patator")
        print("[!] Or from: https://github.com/lanjelot/patator")
        return False
    
    # Check version
    try:
        result = subprocess.run([PATATOR_CMD, "--version"], 
                               capture_output=True, text=True, timeout=5)
        version_line = result.stdout.splitlines()[0] if result.stdout else "unknown"
        print(f"[*] Using patator: {version_line}")
    except Exception as e:
        print(f"[!] Error checking patator version: {e}")
    
    return True


def build_command(options, session):
    """Build patator command based on options"""
    
    # Convert options dict to plain values
    module = options.get("MODULE", "ftp_login")
    host = options.get("HOST", "127.0.0.1")
    port = options.get("PORT", "")
    user_file = options.get("USER_FILE", "")
    pass_file = options.get("PASS_FILE", "")
    user = options.get("USER", "admin")
    password = options.get("PASS", "")
    threads = options.get("THREADS", "5")
    timeout = options.get("TIMEOUT", "10")
    max_retries = options.get("MAX_RETRIES", "3")
    verbose = options.get("VERBOSE", "false").lower() == "true"
    extra_args = options.get("EXTRA_ARGS", "")
    ignore_codes = options.get("IGNORE_CODES", "")
    hits_file = options.get("HITS_FILE", "")
    
    # Command base
    cmd = [PATATOR_CMD, module]
    
    # Module options (use key=value format - CORRECT FOR PATATOR)
    
    # --- Common options for most modules ---
    common_mods = [
        "ftp_login", "ssh_login", "telnet_login", "pop_login", 
        "imap_login", "ldap_login", "dcom_login", "smb_login",
        "rlogin_login", "vmauthd_login", "mssql_login", "oracle_login",
        "mysql_login", "pgsql_login", "rdp_login", "vnc_login",
        "smtp_login", "smtp_vrfy", "smtp_rcpt"
    ]
    
    if module in common_mods:
        cmd.extend([f"host={host}"])
        if port:
            cmd.extend([f"port={port}"])
    
    # --- HTTP fuzzing ---
    elif module == "http_fuzz":
        url = options.get("URL", "")
        if url:
            cmd.extend([f"url={url}"])
        else:
            cmd.extend([f"url=http://{host}:{port or '80'}/"])
        cmd.extend([f"method={options.get('METHOD', 'GET')}"])
        
        data = options.get("DATA", "")
        if data:
            cmd.extend([f"data={data}"])
        
        header = options.get("HEADER", "")
        if header:
            cmd.extend([f"header={header}"])
    
    # --- DNS ---
    elif module in ["dns_forward", "dns_reverse"]:
        cmd.extend([f"host={host}"])
    
    # --- SNMP ---
    elif module == "snmp_login":
        cmd.extend([f"host={host}"])
        community = options.get("SNMP_COMMUNITY", "public")
        cmd.extend([f"community={community}"])
    
    # --- IKE ---
    elif module == "ike_enum":
        cmd.extend([f"host={host}"])
        transforms = options.get("IKE_TRANSFORMS", "")
        if transforms:
            cmd.extend([f"transforms={transforms}"])
    
    # --- Unzip ---
    elif module == "unzip_pass":
        zip_file = options.get("ZIP_FILE", "")
        if zip_file:
            cmd.extend([f"zip={zip_file}"])
        else:
            print("[!] ZIP_FILE option required for unzip_pass module")
            return None
    
    # --- Keystore ---
    elif module == "keystore_pass":
        keystore_file = options.get("KEYSTORE_FILE", "")
        if keystore_file:
            cmd.extend([f"keystore={keystore_file}"])
        else:
            print("[!] KEYSTORE_FILE option required for keystore_pass module")
            return None
    
    # --- MySQL Query ---
    elif module == "mysql_query":
        cmd.extend([f"host={host}"])
        if port:
            cmd.extend([f"port={port}"])
        query = options.get("QUERY", "SELECT version()")
        cmd.extend([f"query={query}"])
        db_name = options.get("DB_NAME", "")
        if db_name:
            cmd.extend([f"database={db_name}"])
    
    # --- Authentication options (CORRECT FORMAT) ---
    has_auth = False
    
    # Handle user/pass combinations
    if user_file and os.path.exists(user_file):
        # Use wordlist file
        cmd.append(f"user=FILE0")
        cmd.append(f"0={user_file}")
        has_auth = True
    elif user:
        cmd.append(f"user={user}")
        has_auth = True
    
    if pass_file and os.path.exists(pass_file):
        if has_auth:
            # If we already have user file, use FILE1 for password
            cmd.append(f"password=FILE1")
            cmd.append(f"1={pass_file}")
        else:
            # Only password file (for modules that only need password)
            cmd.append(f"password=FILE0")
            cmd.append(f"0={pass_file}")
        has_auth = True
    elif password:
        cmd.append(f"password={password}")
        has_auth = True
    
    # If no auth options, suggest using single user/pass
    if not has_auth and module not in ["dns_forward", "dns_reverse", "ike_enum"]:
        cmd.append(f"user={user}")
        if password:
            cmd.append(f"password={password}")
        else:
            print("[!] Warning: No password provided. Use PASS or PASS_FILE.")
            print("[!] For wordlist: set USER_FILE and/or PASS_FILE")
    
    # --- Module-specific additional options ---
    if module == "smb_login":
        domain = options.get("DOMAIN", "")
        if domain:
            cmd.append(f"domain={domain}")
    
    if module in ["mysql_login", "mssql_login", "pgsql_login"]:
        db_name = options.get("DB_NAME", "")
        if db_name:
            cmd.append(f"database={db_name}")
    
    # --- Global options ---
    cmd.extend([f"--threads={threads}"])
    cmd.extend([f"--timeout={timeout}"])
    cmd.extend([f"--max-retries={max_retries}"])
    
    # Ignore codes
    if ignore_codes:
        for code in ignore_codes.split(','):
            code = code.strip()
            if code:
                cmd.append(f"-x ignore:code={code}")
    
    # Hits file
    if hits_file:
        cmd.extend([f"--hits={hits_file}"])
    
    # Verbose
    if verbose:
        cmd.append("--debug")
    
    # Extra arguments
    if extra_args:
        cmd.extend(extra_args.split())
    
    return cmd


def parse_output(output):
    """Parse patator output and extract relevant information"""
    results = {
        "found_credentials": [],
        "statistics": {},
        "errors": [],
        "raw_hits": []
    }
    
    # Parse for successful credentials
    cred_patterns = [
        r"(?:Login|Password|Credential)s? found:?\s*(\S+)\s*[:=]\s*(\S+)",
        r"Found:?\s*(\S+)\s*[:=]\s*(\S+)",
        r"(\S+)\s*[:=]\s*(\S+)\s+\(valid\)",
        r"SUCCESS:\s+(\S+)\s*[-:]\s*(\S+)",
        r"valid\s+(\S+)\s*[:=]\s*(\S+)",
        r"(\S+)\s+as\s+(\S+)\s+\(valid\)",
        r"\[(?:SUCCESS|FOUND)\]\s+(\S+)\s*[:=]\s*(\S+)",
        r"(\S+)\s+\(password:\s*(\S+)\)",
        r"user[:=]\s*(\S+)\s+password[:=]\s*(\S+)",
        r"USER[:=]\s*(\S+)\s+PASS[:=]\s*(\S+)",
    ]
    
    for line in output.splitlines():
        # Check for hits/valid credentials
        for pattern in cred_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                username = match.group(1).strip()
                password = match.group(2).strip()
                if username and password:
                    results["found_credentials"].append((username, password))
                    results["raw_hits"].append(line.strip())
                    break
        
        # Also check for lines with "valid" or "success"
        if "valid" in line.lower() or "success" in line.lower():
            # Try to extract username:password from line
            parts = re.split(r'\s+', line)
            for part in parts:
                if ':' in part and len(part.split(':')) == 2:
                    u, p = part.split(':', 1)
                    if u.strip() and p.strip():
                        results["found_credentials"].append((u.strip(), p.strip()))
                        results["raw_hits"].append(line.strip())
                        break
    
    # Parse statistics
    stats_patterns = [
        (r"Statistics:\s*(\d+)\s+attempts", "attempts"),
        (r"(\d+)\s+valid\s+credentials", "valid_credentials"),
        (r"(\d+)\s+errors", "errors"),
        (r"Time:\s+([\d.]+)s", "time_seconds"),
        (r"Speed:\s+([\d.]+)\s+attempts/s", "speed_attempts_per_sec"),
        (r"(\d+)\s+attempts\s+in\s+([\d.]+)s", "attempts"),
        (r"\[Processed\]\s*(\d+)\s*records", "processed_records"),
        (r"\[Candidates\]\s*(\d+)", "candidates"),
    ]
    
    for pattern, key in stats_patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            results["statistics"][key] = match.group(1)
    
    # Parse errors
    for line in output.splitlines():
        if "error" in line.lower() or "failed" in line.lower() or "exception" in line.lower():
            if "WARNING" not in line:
                results["errors"].append(line.strip())
    
    return results


def run(session, options):
    """
    Main entry point for the module
    
    Args:
        session: Framework session dictionary
        options: Module options dictionary
    
    Returns:
        dict: Results from the patator execution
    """
    # Check dependencies
    if not check_dependencies():
        return {"error": "Patator not installed"}
    
    # Build command
    cmd = build_command(options, session)
    if cmd is None:
        return {"error": "Failed to build command"}
    
    print(f"[*] Running: {' '.join(cmd)}")
    print("[*] Patator is a powerful brute-forcing tool. Use responsibly!")
    print("[*] Target: {}".format(options.get("HOST", "unknown")))
    print("[*] Module: {}".format(options.get("MODULE", "unknown")))
    
    # Run patator
    try:
        # Use subprocess with real-time output
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
            # Skip the initial usage help if it's just showing usage
            if "Usage:" in line and "Examples:" not in line:
                continue
            print(line.rstrip())
            full_output.append(line)
        
        process.wait()
        
        # Parse output
        output_text = "".join(full_output)
        results = parse_output(output_text)
        
        # Print summary
        print("\n" + "=" * 60)
        print("P A T A T O R   S U M M A R Y")
        print("=" * 60)
        
        if results["found_credentials"]:
            print(f"\n[+] Found {len(results['found_credentials'])} credential(s):")
            for username, password in results["found_credentials"]:
                print(f"    USER: {username}  PASS: {password}")
        else:
            print("\n[!] No credentials found")
        
        if results["statistics"]:
            print("\n[*] Statistics:")
            for key, value in results["statistics"].items():
                print(f"    {key}: {value}")
        
        if results["errors"]:
            print(f"\n[!] {len(results['errors'])} error(s) encountered")
            for error in results["errors"][:5]:
                print(f"    {error}")
        
        # Check if hits file was created
        hits_file = options.get("HITS_FILE", "")
        if hits_file and os.path.exists(hits_file):
            print(f"\n[*] Results saved to: {hits_file}")
            try:
                with open(hits_file, 'r') as f:
                    hits_content = f.read().strip()
                    if hits_content:
                        print("[*] Hits content:")
                        print(hits_content)
            except Exception:
                pass
        
        print("=" * 60)
        
        # Save results to session
        session["patator_results"] = results
        
        return results
        
    except Exception as e:
        print(f"[!] Error running patator: {e}")
        return {"error": str(e)}


def test_module(session, options):
    """Test module with dummy_test module"""
    options["MODULE"] = "dummy_test"
    options["HOST"] = "127.0.0.1"
    return run(session, options)