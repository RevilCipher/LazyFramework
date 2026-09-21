#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LinEnum - Linux Local Enumeration & Privilege Escalation Script
"""

import subprocess
import os
import re
import time
import base64
import tempfile
import shutil

MODULE_INFO = {
    "name": "linenum",
    "description": "LinEnum - Linux Local Enumeration & Privilege Escalation Script. Enumerates system info, users, jobs, networking, services, and interesting files.",
    "author": "Revil Cipher",
    "license": "GPL v3",
    "platform": "linux",
    "rank": "great",
    "dependencies": [],
    "references": ["https://github.com/rebootuser/LinEnum"],
}

OPTIONS = {
    "RHOST": {"description": "Target IP address", "required": True, "default": ""},
    "PORT": {"description": "SSH port", "required": False, "default": "22"},
    "USER": {"description": "SSH username", "required": True, "default": ""},
    "PASSWORD": {"description": "SSH password", "required": True, "default": ""},
    "OUTPUT_DIR": {
        "description": "Output directory for results",
        "required": False,
        "default": "/tmp/linenum_results",
    },
    "THOROUGH": {
        "description": "Enable thorough (lengthy) tests including slow checks (-t flag)",
        "required": False,
        "default": "False",
    },
    "KEYWORD": {
        "description": "Search keyword in .conf, .php, .log, .ini files",
        "required": False,
        "default": "",
    },
    "USE_STEALTH": {
        "description": "Suppress verbose output (noise filtering)",
        "required": False,
        "default": "True",
    },
    "TIMEOUT": {
        "description": "SSH session timeout in seconds",
        "required": False,
        "default": "300",
    },
}


def run(session, options):
    rhost = options.get("RHOST", "").strip()
    port = options.get("PORT", "22").strip()
    user = options.get("USER", "").strip()
    password = options.get("PASSWORD", "").strip()
    output_dir = options.get("OUTPUT_DIR", "/tmp/linenum_results")
    thorough = options.get("THOROUGH", "False").lower() == "true"
    keyword = options.get("KEYWORD", "").strip()
    use_stealth = options.get("USE_STEALTH", "True").lower() == "true"
    timeout = int(options.get("TIMEOUT", "300"))

    if not rhost or not user or not password:
        print("[!] RHOST, USER, and PASSWORD are required")
        return False

    print(f"""
[+] LinEnum Scanner
[+] Target:   {user}@{rhost}:{port}
[+] Output:   {output_dir}
[+] Thorough: {thorough}
[+] Keyword:  {keyword if keyword else '(not set)'}
[+] Stealth:  {use_stealth}
[+] Timeout:  {timeout}s
    """)

    os.makedirs(output_dir, exist_ok=True)

    # Build params
    params = []
    if thorough:
        params.append("-t")  # enable thorough (lengthy) tests
    if keyword:
        params.extend(["-k", keyword])  # search keyword

    # Get linenum content
    linenum_content = get_linenum_content()
    if not linenum_content:
        return False

    encoded = base64.b64encode(linenum_content.encode()).decode()

    # Command to run — sentinel dicetak setelah linenum selesai
    SENTINEL = "[LinEnum Done]"

    # Generate report name
    report_name = f"LinEnum-{time.strftime('%d-%m-%y')}"

    remote_cmd = (
        f"TEMP_DIR=$(mktemp -d); cd $TEMP_DIR; "
        f"echo '{encoded}' | base64 -d > l.sh; chmod +x l.sh; "
        f"./l.sh {' '.join(params)} -r {report_name}; "
        f"cat {report_name} 2>/dev/null; "
        f"echo '{SENTINEL}'; "
        f"cd /; rm -rf $TEMP_DIR"
    )

    # Run with expect
    return run_expect(
        rhost, port, user, password, remote_cmd, output_dir, timeout, SENTINEL
    )


def run_expect(
    rhost, port, user, password, remote_cmd, output_dir, timeout=300, sentinel=None
):
    """Run SSH using expect script"""

    # Escape characters for expect
    cmd_escaped = (
        remote_cmd.replace('"', '\\"')
        .replace("$", "\\$")
        .replace("`", "\\`")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )
    pass_escaped = password.replace('"', '\\"')

    expect_script = f"""#!/usr/bin/expect -f
set timeout {timeout}
log_user 1
fconfigure stdout -buffering line
set stty_init -echo
set cmd_sent 0
spawn ssh -p {port} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {user}@{rhost}
expect {{
    "yes/no" {{
        send "yes\\r"
        exp_continue
    }}
    "password:" {{
        send "{pass_escaped}\\r"
        exp_continue
    }}
    "Password:" {{
        send "{pass_escaped}\\r"
        exp_continue
    }}
    -re {{[$#] $}} {{
        if {{$cmd_sent == 0}} {{
            set cmd_sent 1
            send "{cmd_escaped}\\r"
        }}
        exp_continue
    }}
    timeout {{
        send_user "\\nTimeout waiting for response\\n"
        exit 1
    }}
    eof
}}
"""

    # Write expect script to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".exp", delete=False) as f:
        f.write(expect_script)
        expect_file = f.name

    os.chmod(expect_file, 0o755)

    print(f"[+] Connecting to {rhost}:{port}...")
    print("[+] Running LinEnum (this may take several minutes)...\n")

    # Strip ANSI escape codes untuk keperluan filter
    _ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHF]|\x1b\[[0-9]*[A-Z]")

    # Pattern SSH handshake noise yang harus disuppress
    skip_patterns = [
        "spawn ssh",
        "Warning:",
        "Last login:",
        "Debian GNU/Linux",
        "absolutely NO WARRANTY",
        "permitted by applicable law",
        "failed to read",
        "Authentication failed",
        "The programs included",
        "individual files in",
        "comes with ABSOLUTELY",
        "password:",
        "Password:",
    ]

    # Pattern untuk highlight temuan penting
    highlight_patterns = [
        (r"\[\+\]", "[green][+][/green]"),
        (r"\[\!\]", "[red][!][/red]"),
        (r"\[\-\]", "[yellow][-][/yellow]"),
        (r"\[\*\]", "[cyan][*][/cyan]"),
        (r"Possible sudo pwnage", "[bold red]POSSIBLE SUDO PWNAGE[/bold red]"),
        (r"SUID files", "[bold yellow]SUID FILES[/bold yellow]"),
        (r"SGID files", "[bold yellow]SGID FILES[/bold yellow]"),
        (r"World-writable", "[bold red]WORLD-WRITABLE[/bold red]"),
        (r"private SSH keys", "[bold red]PRIVATE SSH KEYS[/bold red]"),
        (r"password", "[bold red]PASSWORD[/bold red]"),
        (r"credential", "[bold red]CREDENTIAL[/bold red]"),
    ]

    def is_noise(line: str) -> bool:
        clean = _ANSI_RE.sub("", line).strip()
        # Shell prompt: lazy@debian:~$ atau root@host:#
        if re.match(r"^\S+@\S+:[~\w/$-]*[#$]\s*$", clean):
            return True
        return any(p.lower() in clean.lower() for p in skip_patterns)

    def highlight_line(line: str) -> str:
        for pattern, replacement in highlight_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return re.sub(pattern, replacement, line, flags=re.IGNORECASE)
        return line

    try:
        # stdbuf -oL paksa expect output line-buffered ke pipe
        stdbuf = shutil.which("stdbuf")
        cmd = ["stdbuf", "-oL", expect_file] if stdbuf else [expect_file]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        clean_lines = []
        start = time.time()
        in_report = False
        report_buffer = []

        # Stream each line as it arrives
        for raw_line in iter(process.stdout.readline, ""):
            if time.time() - start > timeout + 30:
                process.kill()
                os.unlink(expect_file)
                print(f"\n[-] Timeout after {timeout}s — try increasing TIMEOUT")
                return False

            # Sentinel terdeteksi → linenum selesai
            if sentinel and sentinel in raw_line:
                print("\n[+] LinEnum completed.", flush=True)
                process.kill()
                break

            # Detect start of report
            if "### SCAN COMPLETE" in raw_line:
                in_report = False
                # Print remaining report buffer
                for line in report_buffer:
                    print(line, flush=True)
                    clean_lines.append(line)
                report_buffer = []
                print(raw_line.rstrip("\n"), flush=True)
                clean_lines.append(raw_line.rstrip("\n"))
                continue

            # Buffer report lines for better organization
            if "###" in raw_line and not in_report:
                in_report = True
                report_buffer = []

            # Strip SSH handshake noise
            if is_noise(raw_line):
                continue

            line = raw_line.rstrip("\n")
            if not line.strip():
                continue

            # Highlight important findings
            highlighted = highlight_line(line)

            if in_report:
                report_buffer.append(highlighted)
            else:
                print(highlighted, flush=True)
                clean_lines.append(line)

        process.wait()

        # Cleanup
        os.unlink(expect_file)

        if process.returncode != 0:
            stderr_out = process.stderr.read()
            print(f"[-] Connection failed (code: {process.returncode})")
            if stderr_out:
                print(f"[-] Error: {stderr_out[:300]}")
            return False

        clean_output = "\n".join(clean_lines)

        # Save to file
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"linenum_{rhost}_{timestamp}.txt")

        with open(output_file, "w") as f:
            f.write(f"LinEnum Report\n")
            f.write(f"Target: {rhost}:{port}\n")
            f.write(f"User: {user}\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n\n")
            f.write(clean_output)

        print(f"\n[+] Results saved to: {output_file}")

        # Print summary
        print_summary(clean_output)

        return True

    except subprocess.TimeoutExpired:
        process.kill()
        os.unlink(expect_file)
        print(f"[-] Timeout after {timeout}s — try increasing TIMEOUT")
        return False
    except Exception as e:
        print(f"[-] Error: {e}")
        return False


def get_linenum_content():
    """Get linenum.sh content — cek lokal dulu, jika tidak ada gunakan yang sudah disediakan."""
    # Direktori module itu sendiri (taruh linenum.sh di sebelah linenum.py)
    module_dir = os.path.dirname(os.path.abspath(__file__))

    local_paths = [
        os.path.join(module_dir, "linenum.sh"),  # ← prioritas utama
        os.path.join(module_dir, "LinEnum.sh"),
        "./linenum.sh",
        "./LinEnum.sh",
        "/usr/local/bin/linenum.sh",
        "/opt/linenum/linenum.sh",
        os.path.expanduser("~/linenum.sh"),
        os.path.expanduser("~/tools/LinEnum/LinEnum.sh"),
    ]

    for path in local_paths:
        if os.path.exists(path):
            print(f"[+] Using local: {path}")
            with open(path, "r") as f:
                content = f.read()
                # Fix shebang if needed
                if not content.startswith("#!/bin/bash"):
                    content = "#!/bin/bash\n" + content
                return content

    # If no local file found, use the embedded script from the provided content
    print("[+] Using embedded LinEnum script")
    return get_embedded_linenum()


def get_embedded_linenum():
    """Return the embedded LinEnum script content"""
    return """#!/bin/bash
#A script to enumerate local information from a Linux host
version="version 0.982"
#@rebootuser

#help function
usage () 
{ 
echo -e "\\n\\e[00;31m#########################################################\\e[00m" 
echo -e "\\e[00;31m#\\e[00m" "\\e[00;33mLocal Linux Enumeration & Privilege Escalation Script\\e[00m" "\\e[00;31m#\\e[00m"
echo -e "\\e[00;31m#########################################################\\e[00m"
echo -e "\\e[00;33m# www.rebootuser.com | @rebootuser \\e[00m"
echo -e "\\e[00;33m# $version\\e[00m\\n"
echo -e "\\e[00;33m# Example: ./LinEnum.sh -k keyword -r report -e /tmp/ -t \\e[00m\\n"

        echo "OPTIONS:"
        echo "-k      Enter keyword"
        echo "-e      Enter export location"
        echo "-s      Supply user password for sudo checks (INSECURE)"
        echo "-t      Include thorough (lengthy) tests"
        echo "-r      Enter report name" 
        echo "-h      Displays this help text"
        echo -e "\\n"
        echo "Running with no options = limited scans/no output file"
        
echo -e "\\e[00;31m#########################################################\\e[00m"        
}

header()
{
echo -e "\\n\\e[00;31m#########################################################\\e[00m" 
echo -e "\\e[00;31m#\\e[00m" "\\e[00;33mLocal Linux Enumeration & Privilege Escalation Script\\e[00m" "\\e[00;31m#\\e[00m" 
echo -e "\\e[00;31m#########################################################\\e[00m" 
echo -e "\\e[00;33m# www.rebootuser.com\\e[00m" 
echo -e "\\e[00;33m# $version\\e[00m\\n" 

}

debug_info()
{

if [ "$keyword" ]; then 
        echo "[+] Searching for the keyword $keyword in conf, php, ini and log files" 
fi

if [ "$report" ]; then 
        echo "[+] Report name = $report" 
fi

if [ "$export" ]; then 
        echo "[+] Export location = $export" 
fi

if [ "$thorough" ]; then 
        echo "[+] Thorough tests = Enabled" 
else 
        echo -e "\\e[00;33m[+] Thorough tests = Disabled\\e[00m" 
fi

sleep 2

if [ "$export" ]; then
  mkdir $export 2>/dev/null
  format=$export/LinEnum-export-`date +"%d-%m-%y"`
  mkdir $format 2>/dev/null
fi

if [ "$sudopass" ]; then 
  echo -e "\\e[00;35m[+] Please enter password - INSECURE - really only for CTF use!\\e[00m"
  read -s userpassword
  echo 
fi

who=`whoami` 2>/dev/null 
echo -e "\\n" 

echo -e "\\e[00;33mScan started at:"; date 
echo -e "\\e[00m\\n" 
}

# useful binaries (thanks to https://gtfobins.github.io/)
binarylist='aria2c\\|arp\\|ash\\|awk\\|base64\\|bash\\|busybox\\|cat\\|chmod\\|chown\\|cp\\|csh\\|curl\\|cut\\|dash\\|date\\|dd\\|diff\\|dmsetup\\|docker\\|ed\\|emacs\\|env\\|expand\\|expect\\|file\\|find\\|flock\\|fmt\\|fold\\|ftp\\|gawk\\|gdb\\|gimp\\|git\\|grep\\|head\\|ht\\|iftop\\|ionice\\|ip$\\|irb\\|jjs\\|jq\\|jrunscript\\|ksh\\|ld.so\\|ldconfig\\|less\\|logsave\\|lua\\|make\\|man\\|mawk\\|more\\|mv\\|mysql\\|nano\\|nawk\\|nc\\|netcat\\|nice\\|nl\\|nmap\\|node\\|od\\|openssl\\|perl\\|pg\\|php\\|pic\\|pico\\|python\\|readelf\\|rlwrap\\|rpm\\|rpmquery\\|rsync\\|ruby\\|run-parts\\|rvim\\|scp\\|script\\|sed\\|setarch\\|sftp\\|sh\\|shuf\\|socat\\|sort\\|sqlite3\\|ssh$\\|start-stop-daemon\\|stdbuf\\|strace\\|systemctl\\|tail\\|tar\\|taskset\\|tclsh\\|tee\\|telnet\\|tftp\\|time\\|timeout\\|ul\\|unexpand\\|uniq\\|unshare\\|vi\\|vim\\|watch\\|wget\\|wish\\|xargs\\|xxd\\|zip\\|zsh'

system_info()
{
echo -e "\\e[00;33m### SYSTEM ##############################################\\e[00m" 

#basic kernel info
unameinfo=`uname -a 2>/dev/null`
if [ "$unameinfo" ]; then
  echo -e "\\e[00;31m[-] Kernel information:\\e[00m\\n$unameinfo" 
  echo -e "\\n" 
fi

procver=`cat /proc/version 2>/dev/null`
if [ "$procver" ]; then
  echo -e "\\e[00;31m[-] Kernel information (continued):\\e[00m\\n$procver" 
  echo -e "\\n" 
fi

#search all *-release files for version info
release=`cat /etc/*-release 2>/dev/null`
if [ "$release" ]; then
  echo -e "\\e[00;31m[-] Specific release information:\\e[00m\\n$release" 
  echo -e "\\n" 
fi

#target hostname info
hostnamed=`hostname 2>/dev/null`
if [ "$hostnamed" ]; then
  echo -e "\\e[00;31m[-] Hostname:\\e[00m\\n$hostnamed" 
  echo -e "\\n" 
fi
}

user_info()
{
echo -e "\\e[00;33m### USER/GROUP ##########################################\\e[00m" 

#current user details
currusr=`id 2>/dev/null`
if [ "$currusr" ]; then
  echo -e "\\e[00;31m[-] Current user/group info:\\e[00m\\n$currusr" 
  echo -e "\\n"
fi

#last logged on user information
lastlogedonusrs=`lastlog 2>/dev/null |grep -v "Never" 2>/dev/null`
if [ "$lastlogedonusrs" ]; then
  echo -e "\\e[00;31m[-] Users that have previously logged onto the system:\\e[00m\\n$lastlogedonusrs" 
  echo -e "\\n" 
fi

#who else is logged on
loggedonusrs=`w 2>/dev/null`
if [ "$loggedonusrs" ]; then
  echo -e "\\e[00;31m[-] Who else is logged on:\\e[00m\\n$loggedonusrs" 
  echo -e "\\n"
fi

#lists all id's and respective group(s)
grpinfo=`for i in $(cut -d":" -f1 /etc/passwd 2>/dev/null);do id $i;done 2>/dev/null`
if [ "$grpinfo" ]; then
  echo -e "\\e[00;31m[-] Group memberships:\\e[00m\\n$grpinfo"
  echo -e "\\n"
fi

#added by phackt - look for adm group (thanks patrick)
adm_users=$(echo -e "$grpinfo" | grep "(adm)")
if [[ ! -z $adm_users ]];
  then
    echo -e "\\e[00;31m[-] It looks like we have some admin users:\\e[00m\\n$adm_users"
    echo -e "\\n"
fi

#checks to see if any hashes are stored in /etc/passwd (depreciated  *nix storage method)
hashesinpasswd=`grep -v '^[^:]*:[x]' /etc/passwd 2>/dev/null`
if [ "$hashesinpasswd" ]; then
  echo -e "\\e[00;33m[+] It looks like we have password hashes in /etc/passwd!\\e[00m\\n$hashesinpasswd" 
  echo -e "\\n"
fi

#contents of /etc/passwd
readpasswd=`cat /etc/passwd 2>/dev/null`
if [ "$readpasswd" ]; then
  echo -e "\\e[00;31m[-] Contents of /etc/passwd:\\e[00m\\n$readpasswd" 
  echo -e "\\n"
fi

#checks to see if the shadow file can be read
readshadow=`cat /etc/shadow 2>/dev/null`
if [ "$readshadow" ]; then
  echo -e "\\e[00;33m[+] We can read the shadow file!\\e[00m\\n$readshadow" 
  echo -e "\\n"
fi

#checks to see if /etc/master.passwd can be read - BSD 'shadow' variant
readmasterpasswd=`cat /etc/master.passwd 2>/dev/null`
if [ "$readmasterpasswd" ]; then
  echo -e "\\e[00;33m[+] We can read the master.passwd file!\\e[00m\\n$readmasterpasswd" 
  echo -e "\\n"
fi

#all root accounts (uid 0)
superman=`grep -v -E "^#" /etc/passwd 2>/dev/null| awk -F: '$3 == 0 { print $1}' 2>/dev/null`
if [ "$superman" ]; then
  echo -e "\\e[00;31m[-] Super user account(s):\\e[00m\\n$superman"
  echo -e "\\n"
fi

#pull out vital sudoers info
sudoers=`grep -v -e '^$' /etc/sudoers 2>/dev/null |grep -v "#" 2>/dev/null`
if [ "$sudoers" ]; then
  echo -e "\\e[00;31m[-] Sudoers configuration (condensed):\\e[00m$sudoers"
  echo -e "\\n"
fi

#can we sudo without supplying a password
sudoperms=`echo '' | sudo -S -l -k 2>/dev/null`
if [ "$sudoperms" ]; then
  echo -e "\\e[00;33m[+] We can sudo without supplying a password!\\e[00m\\n$sudoperms" 
  echo -e "\\n"
fi

#known 'good' breakout binaries (cleaned to parse /etc/sudoers for comma separated values)
sudopwnage=`echo '' | sudo -S -l -k 2>/dev/null | xargs -n 1 2>/dev/null | sed 's/,*$//g' 2>/dev/null | grep -w $binarylist 2>/dev/null`
if [ "$sudopwnage" ]; then
  echo -e "\\e[00;33m[+] Possible sudo pwnage!\\e[00m\\n$sudopwnage" 
  echo -e "\\n"
fi

#who has sudoed in the past
whohasbeensudo=`find /home -name .sudo_as_admin_successful 2>/dev/null`
if [ "$whohasbeensudo" ]; then
  echo -e "\\e[00;31m[-] Accounts that have recently used sudo:\\e[00m\\n$whohasbeensudo" 
  echo -e "\\n"
fi

#checks to see if roots home directory is accessible
rthmdir=`ls -ahl /root/ 2>/dev/null`
if [ "$rthmdir" ]; then
  echo -e "\\e[00;33m[+] We can read root's home directory!\\e[00m\\n$rthmdir" 
  echo -e "\\n"
fi

#displays /home directory permissions - check if any are lax
homedirperms=`ls -ahl /home/ 2>/dev/null`
if [ "$homedirperms" ]; then
  echo -e "\\e[00;31m[-] Are permissions on /home directories lax:\\e[00m\\n$homedirperms" 
  echo -e "\\n"
fi

#looks for files we can write to that don't belong to us
if [ "$thorough" = "1" ]; then
  grfilesall=`find / -writable ! -user \\`whoami\\` -type f ! -path "/proc/*" ! -path "/sys/*" -exec ls -al {} \\; 2>/dev/null`
  if [ "$grfilesall" ]; then
    echo -e "\\e[00;31m[-] Files not owned by user but writable by group:\\e[00m\\n$grfilesall" 
    echo -e "\\n"
  fi
fi

#lists current user's home directory contents
if [ "$thorough" = "1" ]; then
homedircontents=`ls -ahl ~ 2>/dev/null`
        if [ "$homedircontents" ] ; then
                echo -e "\\e[00;31m[-] Home directory contents:\\e[00m\\n$homedircontents" 
                echo -e "\\n" 
        fi
fi
}

environmental_info()
{
echo -e "\\e[00;33m### ENVIRONMENTAL #######################################\\e[00m" 

#env information
envinfo=`env 2>/dev/null | grep -v 'LS_COLORS' 2>/dev/null`
if [ "$envinfo" ]; then
  echo -e "\\e[00;31m[-] Environment information:\\e[00m\\n$envinfo" 
  echo -e "\\n"
fi

#check if selinux is enabled
sestatus=`sestatus 2>/dev/null`
if [ "$sestatus" ]; then
  echo -e "\\e[00;31m[-] SELinux seems to be present:\\e[00m\\n$sestatus"
  echo -e "\\n"
fi

#current path configuration
pathinfo=`echo $PATH 2>/dev/null`
if [ "$pathinfo" ]; then
  echo -e "\\e[00;31m[-] Path information:\\e[00m\\n$pathinfo" 
  echo -e "\\n"
fi

#lists available shells
shellinfo=`cat /etc/shells 2>/dev/null`
if [ "$shellinfo" ]; then
  echo -e "\\e[00;31m[-] Available shells:\\e[00m\\n$shellinfo" 
  echo -e "\\n"
fi

#current umask value with both octal and symbolic output
umaskvalue=`umask -S 2>/dev/null & umask 2>/dev/null`
if [ "$umaskvalue" ]; then
  echo -e "\\e[00;31m[-] Current umask value:\\e[00m\\n$umaskvalue" 
  echo -e "\\n"
fi
}

job_info()
{
echo -e "\\e[00;33m### JOBS/TASKS ##########################################\\e[00m" 

#are there any cron jobs configured
cronjobs=`ls -la /etc/cron* 2>/dev/null`
if [ "$cronjobs" ]; then
  echo -e "\\e[00;31m[-] Cron jobs:\\e[00m\\n$cronjobs" 
  echo -e "\\n"
fi

#can we manipulate these jobs in any way
cronjobwwperms=`find /etc/cron* -perm -0002 -type f -exec ls -la {} \\; -exec cat {} 2>/dev/null \\;`
if [ "$cronjobwwperms" ]; then
  echo -e "\\e[00;33m[+] World-writable cron jobs and file contents:\\e[00m\\n$cronjobwwperms" 
  echo -e "\\n"
fi

#contab contents
crontabvalue=`cat /etc/crontab 2>/dev/null`
if [ "$crontabvalue" ]; then
  echo -e "\\e[00;31m[-] Crontab contents:\\e[00m\\n$crontabvalue" 
  echo -e "\\n"
fi

crontabvar=`ls -la /var/spool/cron/crontabs 2>/dev/null`
if [ "$crontabvar" ]; then
  echo -e "\\e[00;31m[-] Anything interesting in /var/spool/cron/crontabs:\\e[00m\\n$crontabvar" 
  echo -e "\\n"
fi

anacronjobs=`ls -la /etc/anacrontab 2>/dev/null; cat /etc/anacrontab 2>/dev/null`
if [ "$anacronjobs" ]; then
  echo -e "\\e[00;31m[-] Anacron jobs and associated file permissions:\\e[00m\\n$anacronjobs" 
  echo -e "\\n"
fi
}

networking_info()
{
echo -e "\\e[00;33m### NETWORKING  ##########################################\\e[00m" 

#nic information
nicinfo=`/sbin/ifconfig -a 2>/dev/null`
if [ "$nicinfo" ]; then
  echo -e "\\e[00;31m[-] Network and IP info:\\e[00m\\n$nicinfo" 
  echo -e "\\n"
fi

#dns settings
nsinfo=`grep "nameserver" /etc/resolv.conf 2>/dev/null`
if [ "$nsinfo" ]; then
  echo -e "\\e[00;31m[-] Nameserver(s):\\e[00m\\n$nsinfo" 
  echo -e "\\n"
fi

#default route configuration
defroute=`route 2>/dev/null | grep default`
if [ "$defroute" ]; then
  echo -e "\\e[00;31m[-] Default route:\\e[00m\\n$defroute" 
  echo -e "\\n"
fi

#listening TCP
tcpservs=`netstat -ntpl 2>/dev/null`
if [ "$tcpservs" ]; then
  echo -e "\\e[00;31m[-] Listening TCP:\\e[00m\\n$tcpservs" 
  echo -e "\\n"
fi

#listening UDP
udpservs=`netstat -nupl 2>/dev/null`
if [ "$udpservs" ]; then
  echo -e "\\e[00;31m[-] Listening UDP:\\e[00m\\n$udpservs" 
  echo -e "\\n"
fi
}

services_info()
{
echo -e "\\e[00;33m### SERVICES #############################################\\e[00m" 

#running processes
psaux=`ps aux 2>/dev/null`
if [ "$psaux" ]; then
  echo -e "\\e[00;31m[-] Running processes:\\e[00m\\n$psaux" 
  echo -e "\\n"
fi

#anything 'useful' in inetd.conf
inetdread=`cat /etc/inetd.conf 2>/dev/null`
if [ "$inetdread" ]; then
  echo -e "\\e[00;31m[-] Contents of /etc/inetd.conf:\\e[00m\\n$inetdread" 
  echo -e "\\n"
fi

xinetdread=`cat /etc/xinetd.conf 2>/dev/null`
if [ "$xinetdread" ]; then
  echo -e "\\e[00;31m[-] Contents of /etc/xinetd.conf:\\e[00m\\n$xinetdread" 
  echo -e "\\n"
fi

initdread=`ls -la /etc/init.d 2>/dev/null`
if [ "$initdread" ]; then
  echo -e "\\e[00;31m[-] /etc/init.d/ binary permissions:\\e[00m\\n$initdread" 
  echo -e "\\n"
fi
}

interesting_files()
{
echo -e "\\e[00;33m### INTERESTING FILES ####################################\\e[00m" 

#checks to see if various files are installed
echo -e "\\e[00;31m[-] Useful file locations:\\e[00m" ; which nc 2>/dev/null ; which netcat 2>/dev/null ; which wget 2>/dev/null ; which nmap 2>/dev/null ; which gcc 2>/dev/null; which curl 2>/dev/null 
echo -e "\\n" 

#limited search for installed compilers
compiler=`dpkg --list 2>/dev/null| grep compiler |grep -v decompiler 2>/dev/null && yum list installed 'gcc*' 2>/dev/null| grep gcc 2>/dev/null`
if [ "$compiler" ]; then
  echo -e "\\e[00;31m[-] Installed compilers:\\e[00m\\n$compiler" 
  echo -e "\\n"
fi

#manual check - lists out sensitive files, can we read/modify etc.
echo -e "\\e[00;31m[-] Can we read/write sensitive files:\\e[00m" ; ls -la /etc/passwd 2>/dev/null ; ls -la /etc/group 2>/dev/null ; ls -la /etc/profile 2>/dev/null; ls -la /etc/shadow 2>/dev/null ; ls -la /etc/master.passwd 2>/dev/null 
echo -e "\\n" 

#search for suid files
allsuid=`find / -perm -4000 -type f 2>/dev/null`
findsuid=`find $allsuid -perm -4000 -type f -exec ls -la {} 2>/dev/null \\;`
if [ "$findsuid" ]; then
  echo -e "\\e[00;31m[-] SUID files:\\e[00m\\n$findsuid" 
  echo -e "\\n"
fi

#list of 'interesting' suid files - feel free to make additions
intsuid=`find $allsuid -perm -4000 -type f -exec ls -la {} \\; 2>/dev/null | grep -w $binarylist 2>/dev/null`
if [ "$intsuid" ]; then
  echo -e "\\e[00;33m[+] Possibly interesting SUID files:\\e[00m\\n$intsuid" 
  echo -e "\\n"
fi

#search for sgid files
allsgid=`find / -perm -2000 -type f 2>/dev/null`
findsgid=`find $allsgid -perm -2000 -type f -exec ls -la {} 2>/dev/null \\;`
if [ "$findsgid" ]; then
  echo -e "\\e[00;31m[-] SGID files:\\e[00m\\n$findsgid" 
  echo -e "\\n"
fi

#list of 'interesting' sgid files
intsgid=`find $allsgid -perm -2000 -type f  -exec ls -la {} \\; 2>/dev/null | grep -w $binarylist 2>/dev/null`
if [ "$intsgid" ]; then
  echo -e "\\e[00;33m[+] Possibly interesting SGID files:\\e[00m\\n$intsgid" 
  echo -e "\\n"
fi

#list all world-writable files excluding /proc and /sys
if [ "$thorough" = "1" ]; then
wwfiles=`find / ! -path "*/proc/*" ! -path "/sys/*" -perm -2 -type f -exec ls -la {} 2>/dev/null \\;`
        if [ "$wwfiles" ]; then
                echo -e "\\e[00;31m[-] World-writable files (excluding /proc and /sys):\\e[00m\\n$wwfiles" 
                echo -e "\\n"
        fi
fi

#use supplied keyword and cat *.conf files for potential matches - output will show line number within relevant file path where a match has been located
if [ "$keyword" = "" ]; then
  echo -e "[-] Can't search *.conf files as no keyword was entered\\n" 
  else
    confkey=`find / -maxdepth 4 -name *.conf -type f -exec grep -Hn $keyword {} \\; 2>/dev/null`
    if [ "$confkey" ]; then
      echo -e "\\e[00;31m[-] Find keyword ($keyword) in .conf files (recursive 4 levels - output format filepath:identified line number where keyword appears):\\e[00m\\n$confkey" 
      echo -e "\\n" 
     else 
  echo -e "\\e[00;31m[-] Find keyword ($keyword) in .conf files (recursive 4 levels):\\e[00m" 
  echo -e "'$keyword' not found in any .conf files" 
  echo -e "\\n" 
    fi
fi

if [ "$keyword" = "" ]; then
  :
  else
    if [ "$export" ] && [ "$confkey" ]; then
      confkeyfile=`find / -maxdepth 4 -name *.conf -type f -exec grep -lHn $keyword {} \\; 2>/dev/null`
      mkdir --parents $format/keyword_file_matches/config_files/ 2>/dev/null
      for i in $confkeyfile; do cp --parents $i $format/keyword_file_matches/config_files/ ; done 2>/dev/null
  fi
fi

#use supplied keyword and cat *.php files for potential matches - output will show line number within relevant file path where a match has been located
if [ "$keyword" = "" ]; then
  echo -e "[-] Can't search *.php files as no keyword was entered\\n" 
  else
    phpkey=`find / -maxdepth 10 -name *.php -type f -exec grep -Hn $keyword {} \\; 2>/dev/null`
    if [ "$phpkey" ]; then
      echo -e "\\e[00;31m[-] Find keyword ($keyword) in .php files (recursive 10 levels - output format filepath:identified line number where keyword appears):\\e[00m\\n$phpkey" 
      echo -e "\\n" 
     else 
  echo -e "\\e[00;31m[-] Find keyword ($keyword) in .php files (recursive 10 levels):\\e[00m" 
  echo -e "'$keyword' not found in any .php files" 
  echo -e "\\n" 
    fi
fi

if [ "$keyword" = "" ]; then
  :
  else
    if [ "$export" ] && [ "$phpkey" ]; then
    phpkeyfile=`find / -maxdepth 10 -name *.php -type f -exec grep -lHn $keyword {} \\; 2>/dev/null`
      mkdir --parents $format/keyword_file_matches/php_files/ 2>/dev/null
      for i in $phpkeyfile; do cp --parents $i $format/keyword_file_matches/php_files/ ; done 2>/dev/null
  fi
fi

#use supplied keyword and cat *.log files for potential matches - output will show line number within relevant file path where a match has been located
if [ "$keyword" = "" ];then
  echo -e "[-] Can't search *.log files as no keyword was entered\\n" 
  else
    logkey=`find / -maxdepth 4 -name *.log -type f -exec grep -Hn $keyword {} \\; 2>/dev/null`
    if [ "$logkey" ]; then
      echo -e "\\e[00;31m[-] Find keyword ($keyword) in .log files (recursive 4 levels - output format filepath:identified line number where keyword appears):\\e[00m\\n$logkey" 
      echo -e "\\n" 
     else 
  echo -e "\\e[00;31m[-] Find keyword ($keyword) in .log files (recursive 4 levels):\\e[00m" 
  echo -e "'$keyword' not found in any .log files"
  echo -e "\\n" 
    fi
fi

if [ "$keyword" = "" ];then
  :
  else
    if [ "$export" ] && [ "$logkey" ]; then
      logkeyfile=`find / -maxdepth 4 -name *.log -type f -exec grep -lHn $keyword {} \\; 2>/dev/null`
      mkdir --parents $format/keyword_file_matches/log_files/ 2>/dev/null
      for i in $logkeyfile; do cp --parents $i $format/keyword_file_matches/log_files/ ; done 2>/dev/null
  fi
fi

#use supplied keyword and cat *.ini files for potential matches - output will show line number within relevant file path where a match has been located
if [ "$keyword" = "" ];then
  echo -e "[-] Can't search *.ini files as no keyword was entered\\n" 
  else
    inikey=`find / -maxdepth 4 -name *.ini -type f -exec grep -Hn $keyword {} \\; 2>/dev/null`
    if [ "$inikey" ]; then
      echo -e "\\e[00;31m[-] Find keyword ($keyword) in .ini files (recursive 4 levels - output format filepath:identified line number where keyword appears):\\e[00m\\n$inikey" 
      echo -e "\\n" 
     else 
  echo -e "\\e[00;31m[-] Find keyword ($keyword) in .ini files (recursive 4 levels):\\e[00m" 
  echo -e "'$keyword' not found in any .ini files" 
  echo -e "\\n"
    fi
fi

if [ "$keyword" = "" ];then
  :
  else
    if [ "$export" ] && [ "$inikey" ]; then
      inikey=`find / -maxdepth 4 -name *.ini -type f -exec grep -lHn $keyword {} \\; 2>/dev/null`
      mkdir --parents $format/keyword_file_matches/ini_files/ 2>/dev/null
      for i in $inikey; do cp --parents $i $format/keyword_file_matches/ini_files/ ; done 2>/dev/null
  fi
fi
}

footer()
{
echo -e "\\e[00;33m### SCAN COMPLETE ####################################\\e[00m" 
}

call_each()
{
  header
  debug_info
  system_info
  user_info
  environmental_info
  job_info
  networking_info
  services_info
  interesting_files
  docker_checks
  lxc_container_checks
  footer
}

call_keyword()
{
  header
  debug_info

  kw=$(echo "$keyword" | tr '[:upper:]' '[:lower:]')
  matched=0

  # system_info
  case "$kw" in
    kernel|system|hostname|uname|release|os)
      system_info; matched=1 ;;
  esac

  # user_info
  case "$kw" in
    user|sudo|passwd|password|shadow|group|uid|gid|root|adm)
      user_info; matched=1 ;;
  esac

  # environmental_info
  case "$kw" in
    env|environment|path|shell|umask|selinux)
      environmental_info; matched=1 ;;
  esac

  # job_info
  case "$kw" in
    crontab|cron|job|jobs|task|tasks|anacron|scheduler)
      job_info; matched=1 ;;
  esac

  # networking_info
  case "$kw" in
    network|networking|ip|port|dns|netstat|ifconfig|route|tcp|udp|nameserver)
      networking_info; matched=1 ;;
  esac

  # services_info
  case "$kw" in
    service|services|process|processes|ps|inetd|xinetd|init)
      services_info; matched=1 ;;
  esac

  # interesting_files
  case "$kw" in
    suid|sgid|file|files|conf|php|log|ini|keyword|writable|bak|mail|history|compiler)
      interesting_files; matched=1 ;;
  esac

  # docker_checks
  case "$kw" in
    docker|container|dockerfile|compose)
      docker_checks; matched=1 ;;
  esac

  # lxc_container_checks
  case "$kw" in
    lxc|lxd)
      lxc_container_checks; matched=1 ;;
  esac

  # fallback - keyword tidak cocok mapping manapun, jalankan semua
  if [ "$matched" = "0" ]; then
    echo -e "\\e[00;33m[*] Keyword '$keyword' tidak cocok mapping section manapun - menjalankan semua section\\e[00m"
    system_info
    user_info
    environmental_info
    job_info
    networking_info
    services_info
    interesting_files
    docker_checks
    lxc_container_checks
  fi

  footer
}

while getopts "h:k:r:e:st" option; do
 case "${option}" in
    k) keyword=${OPTARG};;
    r) report=${OPTARG}"-"`date +"%d-%m-%y"`;;
    e) export=${OPTARG};;
    s) sudopass=1;;
    t) thorough=1;;
    h) usage; exit;;
    *) usage; exit;;
 esac
done

if [ "$keyword" ]; then
  call_keyword | tee -a $report 2> /dev/null
else
  call_each | tee -a $report 2> /dev/null
fi
#EndOfScript
"""


def print_summary(output):
    """Print summary of findings"""
    print("\n" + "=" * 60)
    print("LINENUM SUMMARY")
    print("=" * 60)

    findings = []

    for line in output.split("\n"):
        line_lower = line.lower()

        if "possible sudo pwnage" in line_lower:
            findings.append(("SUDO PWNAGE", line.strip()))
        elif "suid files" in line_lower and "+" not in line_lower:
            findings.append(("SUID BINARY", line.strip()))
        elif "sgid files" in line_lower and "+" not in line_lower:
            findings.append(("SGID BINARY", line.strip()))
        elif "world-writable" in line_lower:
            findings.append(("WORLD-WRITABLE", line.strip()))
        elif "we can read the shadow file" in line_lower:
            findings.append(("SHADOW READABLE", line.strip()))
        elif "we can read root's home directory" in line_lower:
            findings.append(("ROOT HOME READABLE", line.strip()))
        elif "we can sudo without supplying a password" in line_lower:
            findings.append(("SUDO NOPASSWD", line.strip()))
        elif "password hashes in /etc/passwd" in line_lower:
            findings.append(("PASSWORD HASHES", line.strip()))
        elif "cron" in line_lower and "writable" in line_lower:
            findings.append(("CRON EXPLOIT", line.strip()))

    if findings:
        print("\n[!] IMPORTANT FINDINGS:\n")
        for cat, f in findings[:20]:
            # Truncate long lines
            display = f[:100] + "..." if len(f) > 100 else f
            print(f"  [{cat}] {display}")

        # Check for potential privilege escalation
        if any(
            f[0] in ["SUDO PWNAGE", "SUDO NOPASSWD", "SUID BINARY", "SHADOW READABLE"]
            for f in findings
        ):
            print("\n[!] Potential Privilege Escalation Vectors Detected!")
    else:
        print("\n[+] No critical findings detected")
        print("[*] Check full report for complete results")

    print("\n" + "=" * 60)
