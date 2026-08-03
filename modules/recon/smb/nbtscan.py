#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NBTscan Module - NetBIOS name scanner
Scans IP networks for NetBIOS name information
"""

import os
import sys
import subprocess
import shutil
import re
import time
import ipaddress
from pathlib import Path

# Check if nbtscan is installed
NBTSCAN_CMD = shutil.which("nbtscan")

# Module metadata
MODULE_INFO = {
    "name": "NBTscan",
    "description": "NetBIOS name scanner - enumerate hosts, domains, and services via NetBIOS",
    "author": "RevilCipher",
    "license": "GPLv2+",
    "platform": "All",
    "arch": "all",
    "rank": "Great",
    "dependencies": [],
    "references": [
        "https://github.com/Steve-White/nbtscan",
        "https://www.kali.org/tools/nbtscan/"
    ]
}

# Module options
OPTIONS = {
    "TARGET": {
        "description": "Target range (CIDR: 192.168.1.0/24 or range: 192.168.1.1-100)",
        "required": True,
        "default": ""
    },
    "TIMEOUT": {
        "description": "Wait timeout in milliseconds for response (default: 1000)",
        "required": False,
        "default": "1000"
    },
    "RETRANSMITS": {
        "description": "Number of retransmits (default: 0)",
        "required": False,
        "default": "0"
    },
    "BANDWIDTH": {
        "description": "Bandwidth throttling in bps (slow down output)",
        "required": False,
        "default": ""
    },
    "FORMAT": {
        "description": "Output format: normal|hosts|lmhosts|script",
        "required": False,
        "default": "normal",
        "choices": ["normal", "hosts", "lmhosts", "script"]
    },
    "SEPARATOR": {
        "description": "Field separator for script format (e.g., ':', ',', '|')",
        "required": False,
        "default": ":"
    },
    "VERBOSE": {
        "description": "Verbose output - print all names received from each host",
        "required": False,
        "default": "false"
    },
    "HUMAN_NAMES": {
        "description": "Print human-readable names for services (use with verbose)",
        "required": False,
        "default": "false"
    },
    "USE_LOCAL_PORT": {
        "description": "Use local port 137 for scans (requires root)",
        "required": False,
        "default": "false"
    },
    "DUMP_PACKETS": {
        "description": "Dump packet contents (debug)",
        "required": False,
        "default": "false"
    },
    "FILE_INPUT": {
        "description": "File containing IP addresses to scan (one per line)",
        "required": False,
        "default": ""
    },
    "SAVE_OUTPUT": {
        "description": "Save output to file",
        "required": False,
        "default": ""
    }
}


def check_dependencies():
    """Check if nbtscan is installed"""
    if NBTSCAN_CMD is None:
        print("[!] NBTscan not found.")
        print("[!] Install on Kali: sudo apt install nbtscan")
        print("[!] Or from: https://github.com/Steve-White/nbtscan")
        return False
    
    # Check version - nbtscan doesn't support --version
    try:
        # Just run with -h to check if it works
        result = subprocess.run([NBTSCAN_CMD, "-h"], 
                               capture_output=True, text=True, timeout=5)
        # If we get output, it's working
        print(f"[*] Using: {NBTSCAN_CMD}")
    except Exception as e:
        print(f"[!] Error checking nbtscan: {e}")
        return False
    
    return True


def build_command(options, session):
    """
    Build nbtscan command based on options
    """
    target = options.get("TARGET", "192.168.1.0/24")
    timeout = options.get("TIMEOUT", "1000")
    retransmits = options.get("RETRANSMITS", "0")
    bandwidth = options.get("BANDWIDTH", "")
    format_type = options.get("FORMAT", "normal").lower()
    separator = options.get("SEPARATOR", ":")
    verbose = options.get("VERBOSE", "false").lower() == "true"
    human_names = options.get("HUMAN_NAMES", "false").lower() == "true"
    use_local_port = options.get("USE_LOCAL_PORT", "false").lower() == "true"
    dump_packets = options.get("DUMP_PACKETS", "false").lower() == "true"
    file_input = options.get("FILE_INPUT", "")
    save_output = options.get("SAVE_OUTPUT", "")
    
    cmd = [NBTSCAN_CMD]
    
    # --- Options ---
    
    # Verbose
    if verbose:
        cmd.append("-v")
    
    # Dump packets
    if dump_packets:
        cmd.append("-d")
    
    # Human-readable names (requires verbose)
    if human_names and verbose:
        cmd.append("-h")
    elif human_names and not verbose:
        print("[!] -h (human names) requires -v (verbose). Enabling verbose.")
        cmd.append("-v")
        cmd.append("-h")
    
    # Use local port 137
    if use_local_port:
        cmd.append("-r")
        print("[*] Using local port 137 (may require root privileges)")
    
    # Suppress banners
    cmd.append("-q")
    
    # Timeout
    cmd.append("-t")
    cmd.append(str(timeout))
    
    # Retransmits
    if retransmits and int(retransmits) > 0:
        cmd.append("-m")
        cmd.append(str(retransmits))
    
    # Bandwidth throttling
    if bandwidth:
        cmd.append("-b")
        cmd.append(str(bandwidth))
    
    # Output format
    if format_type == "hosts":
        cmd.append("-e")
    elif format_type == "lmhosts":
        cmd.append("-l")
    elif format_type == "script":
        cmd.append("-s")
        cmd.append(separator)
    
    # File input or target
    if file_input:
        if file_input == "-":
            # Read from stdin
            cmd.append("-f")
            cmd.append("-")
            print("[*] Reading IPs from stdin")
        elif os.path.exists(file_input):
            cmd.append("-f")
            cmd.append(file_input)
            print(f"[*] Reading IPs from file: {file_input}")
        else:
            print(f"[!] File not found: {file_input}")
            return None
    else:
        cmd.append(target)
        print(f"[*] Target: {target}")
    
    return cmd


def parse_output(output_text):
    """
    Parse nbtscan output and extract structured information
    """
    results = {
        "hosts": [],
        "statistics": {
            "total_hosts": 0,
            "responding_hosts": 0
        }
    }
    
    lines = output_text.splitlines()
    
    # Parse each line
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip banner/summary lines
        if line.startswith("NBTscan") or line.startswith("Doing"):
            continue
        
        # Skip summary lines
        if "done" in line.lower() or "hosts responded" in line.lower():
            # Parse statistics
            match = re.search(r"(\d+)\s+hosts responded", line)
            if match:
                results["statistics"]["responding_hosts"] = int(match.group(1))
            match = re.search(r"(\d+)\s+hosts", line)
            if match:
                results["statistics"]["total_hosts"] = int(match.group(1))
            continue
        
        # Parse host entries - look for IP at start of line
        ip_match = re.match(r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
        if ip_match:
            host_info = parse_host_line(line)
            if host_info:
                results["hosts"].append(host_info)
    
    return results


def parse_host_line(line):
    """
    Parse a single host line from nbtscan output
    """
    host_info = {
        "ip": "",
        "names": [],
        "services": []
    }
    
    parts = line.split()
    if not parts:
        return None
    
    # First part is the IP
    ip = parts[0]
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
        host_info["ip"] = ip
    else:
        return None
    
    # Parse names and services from the rest of the line
    # Format examples:
    # 192.168.1.1    MYDOMAIN        <00>  <00>  <20>
    # 192.168.1.1    MYDOMAIN<00>   UNIQUE  REGISTERED
    # 192.168.1.1    MYDOMAIN       <00>  UNIQUE  REGISTERED
    
    suffix_pattern = r"<([0-9A-Fa-f]{2})>"
    current_name = None
    
    for part in parts[1:]:
        # Skip status words
        if part.upper() in ["UNIQUE", "GROUP", "REGISTERED", "STATUS"]:
            continue
        
        # Check for NetBIOS suffix
        suffix_match = re.search(suffix_pattern, part)
        if suffix_match:
            suffix = suffix_match.group(1)
            # Check if it's a name with suffix (e.g., MYDOMAIN<00>)
            name_match = re.match(r"^([A-Za-z0-9_\-\.]+)" + suffix_pattern, part)
            if name_match:
                name = name_match.group(1)
                suffix = name_match.group(2)
                service_name = get_service_name(suffix)
                name_entry = {
                    "name": name,
                    "suffix": suffix,
                    "service": service_name,
                    "type": "UNIQUE" if suffix in ["00", "03", "20", "21", "22", "23", "24"] else "GROUP"
                }
                if name_entry not in host_info["names"]:
                    host_info["names"].append(name_entry)
                if service_name not in host_info["services"]:
                    host_info["services"].append(service_name)
                current_name = None
            else:
                # Just a suffix marker (e.g., <00>) with previous name
                if current_name:
                    service_name = get_service_name(suffix)
                    name_entry = {
                        "name": current_name,
                        "suffix": suffix,
                        "service": service_name,
                        "type": "UNIQUE" if suffix in ["00", "03", "20", "21", "22", "23", "24"] else "GROUP"
                    }
                    if name_entry not in host_info["names"]:
                        host_info["names"].append(name_entry)
                    if service_name not in host_info["services"]:
                        host_info["services"].append(service_name)
                    current_name = None
        else:
            # Just a name - store for later
            if part and not part.upper() in ["UNIQUE", "GROUP", "REGISTERED", "STATUS", "IP", "ADDRESS"]:
                current_name = part
    
    return host_info


def get_service_name(suffix):
    """
    Get human-readable service name from NetBIOS suffix
    """
    service_map = {
        "00": "Workstation/Redirector",
        "01": "Messenger",
        "03": "Messenger/Logon",
        "06": "RAS",
        "1B": "Domain Master Browser",
        "1C": "Domain Controllers",
        "1D": "Master Browser",
        "1E": "Browser Service Elections",
        "20": "File Server",
        "21": "RAS Client",
        "22": "Exchange Interchange",
        "23": "Exchange Store",
        "24": "Exchange Directory",
        "2B": "Lotus Notes",
        "2F": "Lotus Notes",
        "33": "DCE",
        "3A": "Replication",
        "3D": "Netscape",
        "42": "SMB",
        "43": "SMB",
        "44": "SMB",
        "45": "SMB",
        "46": "SMB",
        "4C": "DHCP",
    }
    return service_map.get(suffix.upper(), f"Unknown ({suffix})")


def print_results(results, options):
    """
    Print structured results in a readable format
    """
    print("\n" + "=" * 70)
    print("N B T S C A N   R E S U L T S")
    print("=" * 70)
    
    hosts = results.get("hosts", [])
    stats = results.get("statistics", {})
    
    if not hosts:
        print("[!] No hosts responded")
        print("\n[*] Possible reasons:")
        print("    - No NetBIOS hosts on the network")
        print("    - Firewall blocking port 137 (UDP)")
        print("    - Hosts are not in the same subnet")
        print("    - Try using '-r' option for Win95/NT hosts")
        return
    
    print(f"\n[+] Found {len(hosts)} responding host(s):")
    print("-" * 70)
    
    for host in hosts:
        ip = host.get("ip", "unknown")
        names = host.get("names", [])
        
        # Group names by type
        computer_names = []
        domain_names = []
        user_names = []
        other_names = []
        
        for name_info in names:
            name = name_info.get("name", "")
            service = name_info.get("service", "")
            suffix = name_info.get("suffix", "")
            
            if not name:
                continue
            
            # Clean up name
            name = name.strip()
            
            if suffix in ["00", "20", "21"]:
                computer_names.append(f"{name} ({service})")
            elif suffix in ["1B", "1C", "1D", "1E"]:
                domain_names.append(f"{name} ({service})")
            elif suffix == "03":
                user_names.append(f"{name} ({service})")
            else:
                other_names.append(f"{name} ({service})")
        
        print(f"\n  IP: {ip}")
        if computer_names:
            print(f"    Computer Names: {', '.join(computer_names)}")
        if domain_names:
            print(f"    Domain Names: {', '.join(domain_names)}")
        if user_names:
            print(f"    User Names: {', '.join(user_names)}")
        if other_names:
            print(f"    Other: {', '.join(other_names)}")
        if not names:
            print("    No NetBIOS names found")
    
    print("\n" + "-" * 70)
    print(f"Statistics:")
    if stats.get('total_hosts', 0) > 0:
        print(f"  Total hosts scanned: {stats.get('total_hosts', 0)}")
    print(f"  Responding hosts: {stats.get('responding_hosts', len(hosts))}")
    print("=" * 70)


def run(session, options):
    """
    Main entry point for the module
    
    Args:
        session: Framework session dictionary
        options: Module options dictionary
    
    Returns:
        dict: Results from the nbtscan execution
    """
    # Check dependencies
    if not check_dependencies():
        return {"error": "NBTscan not installed"}
    
    # Build command
    cmd = build_command(options, session)
    if cmd is None:
        return {"error": "Failed to build command"}
    
    print(f"[*] Running: {' '.join(cmd)}")
    print("[*] Scanning NetBIOS names...")
    print("[*] (This may take a moment depending on network size)")
    
    # Run nbtscan
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
            # Filter out banner/header lines
            if line.startswith("NBTscan") or line.startswith("Doing"):
                continue
            print(line.rstrip())
            full_output.append(line)
        
        process.wait()
        
        # Parse output
        output_text = "".join(full_output)
        results = parse_output(output_text)
        
        # Print structured results
        print_results(results, options)
        
        # Save output if requested
        save_output = options.get("SAVE_OUTPUT", "")
        if save_output:
            try:
                with open(save_output, 'w') as f:
                    f.write(output_text)
                print(f"\n[*] Output saved to: {save_output}")
            except Exception as e:
                print(f"[!] Error saving output: {e}")
        
        # Save to session
        session["nbtscan_results"] = results
        
        return results
        
    except Exception as e:
        print(f"[!] Error running nbtscan: {e}")
        return {"error": str(e)}