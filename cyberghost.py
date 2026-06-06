import sys
import socket
import json
import asyncio
import time
import argparse
import platform
import os
import math
import random
import re
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import importlib.util
from datetime import datetime
import traceback

import aiohttp
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.text import Text
from rich import print as rprint

console = Console()

# ---------------------------------------------------------
# SETUP & GLOBALS
# ---------------------------------------------------------
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

APP_DIR = Path.home() / ".cyberghost"
CACHE_DIR = APP_DIR / "cache"
PLUGINS_DIR = APP_DIR / "plugins"

for d in [APP_DIR, CACHE_DIR, PLUGINS_DIR]:
    d.mkdir(exist_ok=True, parents=True)

# ANSI Colors for Legacy Output
C = "\033[1;36m"
G = "\033[1;32m"
R = "\033[1;31m"
Y = "\033[1;33m"
M = "\033[1;35m"
NC = "\033[0m"

# Dark Mode Colors
DARK_RED = "\033[38;2;139;0;0m"      
BLOOD_RED = "\033[38;2;255;0;0m"     
DARK_GRAY = "\033[38;2;64;64;64m"     
GHOST_GRAY = "\033[38;2;169;169;169m" 
BLACK = "\033[38;2;0;0;0m"           
WHITE = "\033[38;2;255;255;255m"      
BLOOD_DRIP = "\033[38;2;139;0;0m"     

# Premium Colors
GOLD = "\033[38;2;255;215;0m"
NEON_RED = "\033[38;2;255;0;0m"
CYAN = "\033[38;2;0;255;255m"

# ---------------------------------------------------------
# VISUALS & LOGOS (GOD MODE V13)
# ---------------------------------------------------------
ASCII_ART = """
╔═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                                   ║
║      ██████╗██╗   ██╗██████╗ ███████╗██████╗  ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗                          ║
║     ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝                          ║
║     ██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝██║  ███╗███████║██║   ██║███████╗   ██║                             ║
║     ██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗██║   ██║██╔══██║██║   ██║╚════██║   ██║                             ║
║     ╚██████╗   ██║   ██████╔╝███████╗██║  ██║╚██████╔╝██║  ██║╚██████╔╝███████║   ██║                             ║
║      ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝                             ║
║                                                                                                                   ║
║                              ██████╗ ███████╗██╗     ██╗ ██████╗██╗  ██╗████████╗                                ║
║                             ██╔════╝ ██╔════╝██║     ██║██╔════╝██║  ██║╚══██╔══╝                                ║
║                             ██║  ███╗█████╗  ██║     ██║██║     ███████║   ██║                                   ║
║                             ██║   ██║██╔══╝  ██║     ██║██║     ██╔══██║   ██║                                   ║
║                             ╚██████╔╝███████╗███████╗██║╚██████╗██║  ██║   ██║                                   ║
║                              ╚═════╝ ╚══════╝╚══════╝╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝                                   ║
║                                                                                                                   ║
║  ╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗ ║
║  ║                                                                                                              ║ ║
║  ║                            ██████╗  ██████╗ ██████╗     ███╗   ███╗ ██████╗ ██████╗ ███████╗                 ║ ║
║  ║                           ██╔════╝ ██╔═══██╗██╔══██╗    ████╗ ████║██╔═══██╗██╔══██╗██╔════╝                 ║ ║
║  ║                           ██║  ███╗██║   ██║██║  ██║    ██╔████╔██║██║   ██║██║  ██║█████╗                   ║ ║
║  ║                           ██║   ██║██║   ██║██║  ██║    ██║╚██╔╝██║██║   ██║██║  ██║██╔══╝                   ║ ║
║  ║                           ╚██████╔╝╚██████╔╝██████╔╝    ██║ ╚═╝ ██║╚██████╔╝██████╔╝███████╗                 ║ ║
║  ║                            ╚═════╝  ╚═════╝ ╚═════╝     ╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝                 ║ ║
║  ║                                                                                                              ║ ║
║  ╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝ ║
║                                                                                                                   ║
║                    ╔══════════════════════════════════════════════════════════════════════════════╗               ║
║                    ║  v13.0 "GOD MODE" • HYPER OSINT ENGINE • WAF BYPASS • THREAT INTEL • AI       ║               ║
║                    ╚══════════════════════════════════════════════════════════════════════════════╝               ║
║                                                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
"""

ASCII_ART_DARK = """
╔═══════════════════════════════════════💀═══════════════════════════════════════╗
║                                                                               ║
║     ██████╗░██╗░░░██╗██████╗░███████╗██████╗░░█████╗░░█████╗░██████╗░████████╗║
║     ██╔══██╗╚██╗░██╔╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝║
║     ██████╔╝░╚████╔╝░██║░░██║█████╗░░██████╦╝██║░░╚═╝██║░░██║██████╔╝░░░██║░░░║
║     ██╔══██╗░░╚██╔╝░░██║░░██║██╔══╝░░██╔══██╗██║░░██╗██║░░██║██╔══██╗░░░██║░░░║
║     ██████╔╝░░░██║░░░██████╔╝███████╗██║░░██║╚█████╔╝╚█████╔╝██║░░██║░░░██║░░░║
║     ╚═════╝░░░░╚═╝░░░╚═════╝░╚══════╝╚═╝░░╚═╝░╚════╝░░╚════╝░╚═╝░░╚═╝░░░╚═╝░░░║
║                                                                               ║
║                        ██████╗░██████╗░██████╗░                               ║
║                       ██╔════╝██╔═══██╗██╔══██╗                               ║
║                       ██║░███╗██║░░░██║██║░░██║                               ║
║                       ██║░░██║██║░░░██║██║░░██║                               ║
║                       ╚██████╔╝╚██████╔╝██████╔╝                              ║
║                        ╚═════╝░░╚═════╝░╚═════╝░                              ║
║                                                                               ║
╚═══════════════════════════════════════💀═══════════════════════════════════════╝
"""

ASCII_BLOOD_DRIP = """
║     ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ ║
║     ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ ║
║     ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ ║
"""

def print_premium_logo(style="premium", animate=False, glow=False):
    shadow = DARK_RED if glow else NEON_RED
    main = NEON_RED if style == "premium" else DARK_RED
    accent = GOLD if style == "premium" else DARK_RED
    cyan = CYAN if style == "premium" else BLOOD_RED
    
    logo = f"""
{shadow}╔═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗{NC}
{shadow}║{NC}                                                                                                                           {shadow}║{NC}
{shadow}║{NC}     {main}██████{shadow}╗{main}██{shadow}╗   {main}██{shadow}╗{main}██████{shadow}╗{main} ███████{shadow}╗{main}██████{shadow}╗ {main} ██████{shadow}╗{main} ██{shadow}╗  {main}██{shadow}╗{main} ██████{shadow}╗{main} ███████{shadow}╗{main}████████{shadow}╗{NC}                     {shadow}║{NC}
{shadow}║{NC}     {main}██{shadow}╔════{main}╝{shadow} ╚██╗ ██╔{main}╝{shadow} {main}██╔══██╗{shadow}{main}██╔════╝{shadow}{main}██╔══██╗{shadow}{main}██╔════╝{shadow} {main}██║{shadow}  {main}██║{shadow}{main}██╔═══██╗{shadow}{main}██╔════╝{shadow}{main}╚══██╔══╝{NC}                     {shadow}║{NC}
{shadow}║{NC}     {main}██║{shadow}     {main}╚████╔╝{shadow} {main}██████╔╝{shadow}{main}█████╗{shadow}  {main}██████╔╝{shadow}{main}██║{shadow}  {main}███╗{shadow}{main}███████║{shadow}{main}██║{shadow}   {main}██║{shadow}{main}███████╗{shadow}   {main}██║{NC}                        {shadow}║{NC}
{shadow}║{NC}     {main}██║{shadow}      {main}╚██╔╝{shadow}  {main}██╔══██╗{shadow}{main}██╔══╝{shadow}  {main}██╔══██╗{shadow}{main}██║{shadow}   {main}██║{shadow}{main}██╔══██║{shadow}{main}██║{shadow}   {main}██║{shadow}{main}╚════██║{shadow}   {main}██║{NC}                        {shadow}║{NC}
{shadow}║{NC}     {main}╚██████╗{shadow}   {main}██║{shadow}   {main}██████╔╝{shadow}{main}███████╗{shadow}{main}██║{shadow}  {main}██║{shadow}{main}╚██████╔╝{shadow}{main}██║{shadow}  {main}██║{shadow}{main}╚██████╔╝{shadow}{main}███████║{shadow}   {main}██║{NC}                        {shadow}║{NC}
{shadow}║{NC}      {main}╚═════╝{shadow}   {main}╚═╝{shadow}   {main}╚═════╝{shadow} {main}╚══════╝{shadow}{main}╚═╝{shadow}  {main}╚═╝{shadow} {main}╚═════╝{shadow} {main}╚═╝{shadow}  {main}╚═╝{shadow} {main}╚═════╝{shadow} {main}╚══════╝{shadow}   {main}╚═╝{NC}                        {shadow}║{NC}
{shadow}║{NC}                                                                                                                           {shadow}║{NC}
{shadow}║{NC}                             {accent}██████╗  ██████╗ ██████╗{NC}                                                              {shadow}║{NC}
{shadow}║{NC}                            {accent}██╔════╝ ██╔═══██╗██╔══██╗{NC}                                                             {shadow}║{NC}
{shadow}║{NC}                            {accent}██║  ███╗██║   ██║██║  ██║{NC}                                                             {shadow}║{NC}
{shadow}║{NC}                            {accent}██║   ██║██║   ██║██║  ██║{NC}                                                             {shadow}║{NC}
{shadow}║{NC}                            {accent}╚██████╔╝╚██████╔╝██████╔╝{NC}                                                             {shadow}║{NC}
{shadow}║{NC}                             {accent}╚═════╝  ╚═════╝ ╚═════╝{NC}                                                              {shadow}║{NC}
{shadow}║{NC}                                                                                                                           {shadow}║{NC}
{shadow}║{NC}                      {accent}✦{NC} {cyan}CYBERGHOST OSINT v13.0{NC} {accent}-{NC} {cyan}\"GOD MODE\" EDITION{NC} {accent}✦{NC}                                             {shadow}║{NC}
{shadow}║{NC}                                                                                                                           {shadow}║{NC}
{shadow}║{NC}                      {accent}╔══════════════════════════════════════════════════════════════════════════╗{NC}               {shadow}║{NC}
{shadow}║{NC}                      {accent}║{NC}  {cyan}🔥 MILITARY GRADE RECON & VULNERABILITY SCANNER 🔥{NC}          {accent}║{NC}               {shadow}║{NC}
{shadow}║{NC}                      {accent}╚══════════════════════════════════════════════════════════════════════════╝{NC}               {shadow}║{NC}
{shadow}║{NC}                                                                                                                           {shadow}║{NC}
{shadow}╚═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝{NC}
"""
    if animate:
        lines = logo.strip("\n").split("\n")
        print("\n")
        for line in lines:
            parts = line.split('\033')
            for i, part in enumerate(parts):
                if i == 0 and not part.startswith('['):
                    for char in part:
                        print(char, end="", flush=True)
                        time.sleep(0.001)
                else:
                    idx = part.find('m')
                    if idx != -1:
                        print('\033' + part[:idx+1], end="", flush=True)
                        for char in part[idx+1:]:
                            print(char, end="", flush=True)
                            time.sleep(0.001)
                    else:
                        print('\033' + part, end="", flush=True)
            print()
            time.sleep(0.02)
    else:
        print("\n" + logo.strip("\n") + "\n")

def print_logo_normal(style="matrix", animate=False):
    colors = {
        "matrix": {"text": "\033[38;2;0;255;0m", "border": "\033[38;2;0;200;0m", "highlight": "\033[38;2;255;255;255m"},
        "cyber": {"text": "\033[38;2;0;255;255m", "border": "\033[38;2;255;0;255m", "highlight": "\033[38;2;255;255;0m"},
        "red": {"text": "\033[38;2;255;0;0m", "border": "\033[38;2;100;0;0m", "highlight": "\033[38;2;255;255;255m"},
    }
    
    if style == "minimal":
        print(f"\n{C}╔══════════════════════════════════════════════════════════════════╗")
        print(f"║     CYBERGHOST OSINT v13.0 - \"GOD MODE\"                          ║")
        print(f"╚══════════════════════════════════════════════════════════════════╝{NC}\n")
        return

    lines = ASCII_ART.strip("\n").split("\n")
    
    if style == "rainbow":
        for i, line in enumerate(lines):
            out = ""
            for j, char in enumerate(line):
                r = int(math.sin(0.1 * j + 0) * 127 + 128)
                g = int(math.sin(0.1 * j + 2) * 127 + 128)
                b = int(math.sin(0.1 * j + 4) * 127 + 128)
                if char in "╔═╗╚╝║":
                    out += f"\033[38;2;{r//2};{g//2};{b//2}m{char}"
                else:
                    out += f"\033[38;2;{r};{g};{b}m{char}"
            print(out + "\033[0m", flush=True)
            if animate: time.sleep(0.02)
        print()
        return

    c = colors.get(style, colors["matrix"])
    for line in lines:
        out = ""
        for char in line:
            if char in "╔═╗╚╝║":
                out += f"{c['border']}{char}"
            elif char in "v1.0SHADOWWARRIORMEGAOSINTENGINERECONTHREATINTELAI":
                out += f"{c['highlight']}{char}"
            else:
                out += f"{c['text']}{char}"
        
        if animate:
            print(out + "\033[0m", flush=True)
            time.sleep(0.01)
        else:
            print(out + "\033[0m")
    print()

def print_logo_dark(style="dark", animate=False, blood_drip=False):
    lines = ASCII_ART_DARK.strip("\n").split("\n")
    if blood_drip:
        lines.extend(ASCII_BLOOD_DRIP.strip("\n").split("\n"))
        
    c_text = DARK_RED if style == "dark" else BLOOD_RED if style == "blood" else GHOST_GRAY
    c_border = DARK_GRAY
    
    if animate:
        for _ in range(3):
            print(f"\033[2J\033[H", end="") 
            print(f"{WHITE}╔═══════════════════════════════════════💀═══════════════════════════════════════╗{NC}")
            time.sleep(0.05)
            print(f"\033[2J\033[H", end="")
            time.sleep(0.05)
            
    print(f"\n{BLOOD_RED}Iniciando a invocação GOD MODE...{NC}")
    if animate: time.sleep(0.5)
    
    for line in lines:
        out = ""
        for char in line:
            if char in "╔═╗╚╝║💀":
                out += f"{c_border}{char}"
            elif char == "░":
                out += f"{BLOOD_DRIP if blood_drip else c_border}{char}"
            else:
                out += f"{c_text}{char}"
        
        if animate:
            for char_idx, char in enumerate(out.split('\033')):
                if char_idx == 0 and not char.startswith('['):
                    print(char, end='', flush=True)
                else:
                    print('\033' + char, end='', flush=True)
                    if random.random() < 0.05:  
                        time.sleep(0.03)
            print("\033[0m")
        else:
            print(out + "\033[0m")
            
    warning = f"""{DARK_RED}
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                      ⚠️  WARNING: GOD MODE ACTIVE  ⚠️                          ║
║                                                                               ║
║           Ferramentas de nível militar acionadas. Use com cautela.            ║
║                                                                               ║
║                        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                       ║
║                        ░  ENTER AT YOUR OWN RISK  ░                       ║
║                        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                       ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝{NC}
"""
    print(warning)
    if animate: time.sleep(1)

# ---------------------------------------------------------
# CORE HTTP ENGINE (AIOHTTP)
# ---------------------------------------------------------
async def fetch_url_async(session, url, method="GET", timeout=15, headers=None, as_json=False):
    if headers is None:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) CyberGhost/13.0 GODMODE'}
    try:
        async with session.request(method, url, headers=headers, timeout=timeout, ssl=False) as response:
            if response.status == 200:
                if as_json:
                    return await response.json()
                return await response.text()
            return None
    except Exception:
        return None

# ---------------------------------------------------------
# OSINT MODULES (STANDARD & MOSTRUOSO)
# ---------------------------------------------------------
async def get_dns(target):
    results = {}
    try:
        ip = await asyncio.to_thread(socket.gethostbyname, target)
        results['A'] = ip
        try:
            addrinfo = await asyncio.to_thread(socket.getaddrinfo, target, None, socket.AF_INET6)
            results['AAAA'] = addrinfo[0][4][0]
        except: pass
    except: pass
    return results

async def get_subdomains(session, target):
    data = await fetch_url_async(session, f"https://crt.sh/?q=%25.{target}&output=json", as_json=True)
    subs = set()
    if data and isinstance(data, list):
        for cert in data:
            name = cert.get('name_value', '')
            for n in name.split('\n'):
                if n.endswith(target) and '*' not in n: 
                    subs.add(n)
    return list(subs)[:100]

async def scan_port(target, port, timeout=2):
    try:
        conn = asyncio.open_connection(target, port)
        reader, writer = await asyncio.wait_for(conn, timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return port
    except:
        return None

async def scan_ports_hyper(target):
    # Expanded critical ports
    ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 9200, 27017]
    try:
        ip = await asyncio.to_thread(socket.gethostbyname, target)
    except: 
        return []
    tasks = [scan_port(ip, p) for p in ports]
    results = await asyncio.gather(*tasks)
    open_ports = [p for p in results if p is not None]
    port_map = {21:"FTP", 22:"SSH", 23:"Telnet", 25:"SMTP", 53:"DNS", 80:"HTTP", 110:"POP3", 443:"HTTPS", 445:"SMB", 1433:"MSSQL", 3306:"MySQL", 3389:"RDP", 5432:"PostgreSQL", 5900:"VNC", 6379:"Redis", 8080:"HTTP-Alt", 9200:"Elastic", 27017:"MongoDB"}
    return [f"{p}/{port_map.get(p, 'Unknown')}" for p in open_ports]

async def detect_tech(session, target):
    techs = {}
    url = f"http://{target}" if not target.startswith('http') else target
    try:
        async with session.head(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5, ssl=False, allow_redirects=True) as response:
            headers = response.headers
            if 'Server' in headers: techs['Web Server'] = headers['Server']
            if 'X-Powered-By' in headers: techs['Framework'] = headers['X-Powered-By']
            if 'X-AspNet-Version' in headers: techs['ASP.NET'] = headers['X-AspNet-Version']
            if 'X-Generator' in headers: techs['Generator'] = headers['X-Generator']
    except: pass
    return techs

async def ip_reputation(target):
    try: 
        ip = await asyncio.to_thread(socket.gethostbyname, target)
    except: 
        return {"DNSBL": "Não foi possível resolver IP"}
    reverse_ip = ".".join(reversed(ip.split(".")))
    results = {}
    for bl in ["zen.spamhaus.org", "b.barracudacentral.org", "bl.spamcop.net"]:
        try:
            await asyncio.to_thread(socket.gethostbyname, f"{reverse_ip}.{bl}")
            results[bl] = "[red]⚠️ LISTADO[/red]"
        except socket.gaierror:
            results[bl] = "[green]✅ CLEAN[/green]"
    return results

async def wayback_urls(session, target):
    data = await fetch_url_async(session, f"http://web.archive.org/cdx/search/cdx?url=*.{target}/*&output=json&limit=15", as_json=True)
    urls = []
    if data and isinstance(data, list) and len(data) > 1:
        urls = [f"{row[1][:4]}-{row[1][4:6]}-{row[1][6:8]}: {row[2]}" for row in data[1:]]
    return urls

async def get_asn_info(session, target):
    try:
        ip = await asyncio.to_thread(socket.gethostbyname, target)
        data = await fetch_url_async(session, f"https://stat.ripe.net/data/whois/data.json?resource={ip}", as_json=True)
        if data:
            records = data.get("data", {}).get("records", [])
            for r in records:
                for attr in r:
                    if attr.get("key") in ["netname", "descr"]:
                        return [f"{attr['key'].upper()}: {attr['value']}"]
    except: pass
    return []

async def cloud_enum(target):
    clouds = {
        "aws": f"{target}.s3.amazonaws.com", 
        "gcp": f"{target}.storage.googleapis.com",
        "azure": f"{target}.blob.core.windows.net",
        "digitalocean": f"{target}.nyc3.digitaloceanspaces.com"
    }
    results = []
    for provider, domain in clouds.items():
        try:
            await asyncio.to_thread(socket.gethostbyname, domain)
            results.append(f"[yellow]{provider.upper()}: ENCONTRADO ({domain})[/yellow]")
        except: pass
    return results

async def spider_js_secrets(session, target):
    secrets_found = []
    url = f"http://{target}" if not target.startswith('http') else target
    html = await fetch_url_async(session, url)
    if not html: return ["Falha ao acessar o site para spidering."]
    
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')
    
    js_urls = []
    for s in scripts:
        src = s.get('src')
        if src:
            if src.startswith('http'): js_urls.append(src)
            elif src.startswith('/'): js_urls.append(f"http://{target}{src}")
                
    patterns = {
        "Google API": r'AIza[0-9A-Za-z-_]{35}',
        "AWS Access Key": r'AKIA[0-9A-Z]{16}',
        "Stripe Standard": r'sk_live_[0-9a-zA-Z]{24}',
        "JWT Token": r'ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*',
        "Generic Bearer": r'Bearer\s+[A-Za-z0-9\-\._~+/]+'
    }
    
    async def analyze_js(js_url):
        js_content = await fetch_url_async(session, js_url, timeout=5)
        findings = []
        if js_content:
            for name, pattern in patterns.items():
                matches = re.findall(pattern, js_content)
                if matches:
                    findings.append(f"[red]⚠️ {name}[/red] encontrado em {js_url.split('/')[-1]}")
            endpoints = re.findall(r'["\'](/api/v[0-9]/[a-zA-Z0-9_\-]+)["\']', js_content)
            if endpoints:
                findings.append(f"[cyan]Endpoints (API)[/cyan]: {', '.join(set(endpoints[:3]))}")
        return findings

    tasks = [analyze_js(u) for u in js_urls[:10]]
    results = await asyncio.gather(*tasks)
    
    for r in results:
        secrets_found.extend(r)
        
    if not secrets_found: return ["[green]Nenhum segredo no Frontend JS.[/green]"]
    return list(set(secrets_found))

async def vuln_scan_misconfig(session, target):
    vulns = []
    paths = [('/.git/config', 'Git Repository Expsto'), ('/.env', 'Arquivo .env Exposto'), ('/server-status', 'Apache Server Status'), ('/actuator/env', 'Spring Boot Actuator Env')]
    
    async def check_path(path, name):
        url = f"http://{target}{path}"
        try:
            async with session.get(url, timeout=3, ssl=False, allow_redirects=False) as resp:
                if resp.status == 200 and 'html' not in resp.headers.get('Content-Type', '').lower():
                    return f"[red]CRÍTICO: {name} ({url})[/red]"
        except: pass
        return None

    tasks = [check_path(p, n) for p, n in paths]
    res = await asyncio.gather(*tasks)
    vulns = [r for r in res if r]
    
    url = f"http://{target}"
    try:
        async with session.get(url, headers={'Origin': 'https://evil.com'}, timeout=3, ssl=False) as resp:
            if resp.headers.get('Access-Control-Allow-Origin') == 'https://evil.com':
                vulns.append("[yellow]ALERTA: CORS Misconfiguration Permitindo Qualquer Origem[/yellow]")
    except: pass
    
    if not vulns: return ["[green]Nenhuma misconfiguration crítica detectada.[/green]"]
    return vulns


# ---------------------------------------------------------
# GOD MODE MODULES
# ---------------------------------------------------------
async def detect_waf(session, target):
    """
    Tenta injetar um payload malicioso e analisa a resposta para identificar WAF.
    """
    url = f"http://{target}/?q=<script>alert(1)</script>"
    try:
        async with session.get(url, timeout=5, ssl=False) as resp:
            server = resp.headers.get('Server', '').lower()
            if resp.status in [403, 406]:
                if 'cloudflare' in server: return ["[red]CRÍTICO: Cloudflare WAF Detectado[/red]"]
                if 'akamai' in server: return ["[red]CRÍTICO: Akamai WAF Detectado[/red]"]
                if 'imperva' in server or 'incapsula' in server: return ["[red]CRÍTICO: Imperva WAF Detectado[/red]"]
                if 'awselb' in server: return ["[red]CRÍTICO: AWS WAF Detectado[/red]"]
                return ["[yellow]ALERTA: WAF Genérico / Bloqueio Detectado (Status 403 em Payload)[/yellow]"]
            else:
                return ["[green]Nenhum WAF estrito detectado para payloads básicos.[/green]"]
    except:
        return []

async def check_subdomain_takeover(session, subdomains):
    """
    Resolve subdomínios descobertos e busca por assinaturas de serviços órfãos (S3, Github).
    """
    signatures = {
        's3.amazonaws.com': 'The specified bucket does not exist',
        'github.io': "There isn't a GitHub Pages site here",
        'herokuapp.com': 'No such app',
        'ghost.io': 'The thing you were looking for is no longer here'
    }
    
    async def check_sub(sub):
        try:
            url = f"http://{sub}"
            async with session.get(url, timeout=4, ssl=False) as resp:
                text = await resp.text()
                for provider, sig in signatures.items():
                    if sig in text:
                        return f"[bold red]💥 CRÍTICO: Takeover Possível em {sub} ({provider})[/bold red]"
        except: pass
        return None

    tasks = [check_sub(s) for s in subdomains[:50]]
    results = await asyncio.gather(*tasks)
    findings = [r for r in results if r]
    if not findings: return ["[green]Nenhum takeover óbvio detectado nos subdomínios listados.[/green]"]
    return findings

async def fast_fuzz(session, target):
    """
    Dirbusting ultra-rápido para diretórios críticos.
    """
    findings = []
    paths = ['/admin', '/login', '/api', '/backup.zip', '/config.php', '/wp-admin', '/dashboard', '/test']
    
    async def check_path(path):
        url = f"http://{target}{path}"
        try:
            async with session.get(url, timeout=3, ssl=False, allow_redirects=False) as resp:
                if resp.status in [200, 301, 302, 403] and resp.status != 404:
                    return f"[yellow]Descoberto: {path} (Status: {resp.status})[/yellow]"
        except: pass
        return None

    tasks = [check_path(p) for p in paths]
    res = await asyncio.gather(*tasks)
    findings = [r for r in res if r]
    if not findings: return ["[green]Nenhum diretório comum oculto encontrado.[/green]"]
    return findings

async def email_harvester(session, target):
    """
    Scrape básico para coletar emails expostos no index.
    """
    url = f"http://{target}"
    try:
        html = await fetch_url_async(session, url)
        if not html: return []
        emails = re.findall(r'[a-zA-Z0-9.\-+_]+@[a-zA-Z0-9.\-+_]+\.[a-zA-Z]+', html)
        emails = list(set([e for e in emails if not e.startswith('u00')]))
        if emails:
            return [f"[cyan]Emails Encontrados:[/cyan] {', '.join(emails[:10])}"]
        return ["[green]Nenhum email corporativo exposto na home page.[/green]"]
    except: return []

async def shodan_query(target):
    """
    Usa Shodan se SHODAN_API_KEY estiver presente.
    """
    api_key = os.getenv("SHODAN_API_KEY")
    if not api_key:
        return ["[dim]SHODAN_API_KEY não configurada. Pulo de varredura global CVE.[/dim]"]
    
    try:
        import shodan
        api = shodan.Shodan(api_key)
        ip = await asyncio.to_thread(socket.gethostbyname, target)
        host = await asyncio.to_thread(api.host, ip)
        res = []
        if host.get('vulns'):
            res.append(f"[bold red]CVEs (SHODAN):[/bold red] {', '.join(host['vulns'])}")
        ports = host.get('ports', [])
        res.append(f"[cyan]Portas Ativas Globais:[/cyan] {', '.join(map(str, ports))}")
        org = host.get('org', '')
        if org: res.append(f"[yellow]Organização Registrada:[/yellow] {org}")
        return res
        return res
    except Exception as e:
        return [f"[red]Erro Shodan: {e}[/red]"]

async def check_dns_sec(target):
    """
    Verifica postura de segurança do domínio (SPF, DMARC) passivamente via DNS.
    """
    import dns.resolver
    results = []
    
    # SPF
    try:
        answers = dns.resolver.resolve(target, 'TXT')
        spf = [r.to_text() for r in answers if 'v=spf1' in r.to_text().lower()]
        if spf: results.append(f"[green]SPF Configurado:[/green] {spf[0][:50]}...")
        else: results.append("[red]ALERTA: Registro SPF ausente (Risco de Spoofing)[/red]")
    except:
        results.append("[red]ALERTA: Falha ao obter SPF[/red]")
        
    # DMARC
    try:
        answers = dns.resolver.resolve(f"_dmarc.{target}", 'TXT')
        dmarc = [r.to_text() for r in answers if 'v=dmarc1' in r.to_text().lower()]
        if dmarc: results.append(f"[green]DMARC Configurado:[/green] {dmarc[0][:50]}...")
        else: results.append("[red]ALERTA: Registro DMARC ausente[/red]")
    except:
        results.append("[red]ALERTA: Falha ao obter DMARC[/red]")
        
    return results

async def harvest_robots(session, target):
    """
    Busca passiva por paths ocultos no robots.txt e checa se sitemap.xml existe.
    """
    findings = []
    
    # Robots.txt
    url_robots = f"http://{target}/robots.txt"
    html = await fetch_url_async(session, url_robots, timeout=4)
    if html and "<html" not in html.lower():
        disallowed = re.findall(r'Disallow:\s*(/.*)', html)
        if disallowed:
            findings.append(f"[yellow]Paths Ocultos (Robots):[/yellow] {', '.join(set(disallowed[:5]))} ...")
        else:
            findings.append("[dim]Robots.txt vazio ou sem restrições[/dim]")
    else:
         findings.append("[dim]Sem robots.txt[/dim]")
         
    # Sitemap
    url_sitemap = f"http://{target}/sitemap.xml"
    try:
        async with session.head(url_sitemap, timeout=3, ssl=False) as resp:
            if resp.status == 200:
                findings.append(f"[cyan]Sitemap Detectado:[/cyan] {url_sitemap}")
    except: pass
    
    return findings if findings else ["[green]Nada oculto encontrado em arquivos padrão.[/green]"]

async def analyze_security_headers(session, target):
    """
    Inspeciona cabeçalhos de resposta HTTP para postura defensiva.
    """
    url = f"http://{target}"
    findings = []
    try:
        async with session.head(url, timeout=5, ssl=False, allow_redirects=True) as resp:
            headers = resp.headers
            hsts = headers.get('Strict-Transport-Security')
            csp = headers.get('Content-Security-Policy')
            xframe = headers.get('X-Frame-Options')
            
            if not hsts: findings.append("[red]Falta: Strict-Transport-Security (HSTS)[/red]")
            if not csp: findings.append("[red]Falta: Content-Security-Policy (CSP)[/red]")
            if not xframe: findings.append("[yellow]Falta: X-Frame-Options (Clickjacking)[/yellow]")
            
            if not findings:
                return ["[green]Excelente: Principais headers de segurança configurados.[/green]"]
            return findings
    except:
        return ["[dim]Não foi possível checar headers.[/dim]"]

async def generate_dorks_and_breaches(target):
    """
    Gera dorks de busca avançada para vazamentos de dados passivos.
    """
    dorks = [
        f"site:pastebin.com \"{target}\"",
        f"site:trello.com \"{target}\"",
        f"\"@{target}\" ext:txt | ext:csv | ext:sql",
        f"site:github.com \"{target}\" \"password\" | \"secret\""
    ]
    return [f"[cyan]Busque no Google:[/cyan] {d}" for d in dorks]

async def check_tech_cves(tech_results):
    """
    Baseado nas tecnologias detectadas, emite alertas genéricos passivos.
    """
    if not tech_results: return ["[dim]Nenhuma tecnologia específica para buscar CVEs.[/dim]"]
    
    alerts = []
    for k, v in tech_results.items():
        val = v.lower()
        if 'apache' in val and '2.4.49' in val:
            alerts.append(f"[bold red]ALERTA CVE: {v} é vulnerável a Path Traversal (CVE-2021-41773)[/bold red]")
        elif 'nginx/1.1' in val:
            alerts.append(f"[yellow]Aviso: Versões Nginx 1.1x podem ter exploits públicos.[/yellow]")
        elif 'php/5' in val or 'php/7.0' in val or 'php/7.1' in val or 'php/7.2' in val:
             alerts.append(f"[bold red]ALERTA: {v} descontinuado e vulnerável![/bold red]")
             
    if not alerts: return ["[green]Nenhuma versão criticamente exposta detectada (Passivo).[/green]"]
    return alerts
# ---------------------------------------------------------
# EXPORT
# ---------------------------------------------------------
def generate_html_report(target, data):
    filename = f"report_{target}_{int(time.time())}.html"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CyberGhost OSINT Report - {target}</title>
        <style>
            body {{ font-family: 'Courier New', Courier, monospace; background-color: #121212; color: #00ff00; margin: 40px; }}
            h1 {{ color: #ff0000; text-align: center; border-bottom: 2px solid #ff0000; padding-bottom: 10px; }}
            h2 {{ color: #00ffff; margin-top: 30px; }}
            .card {{ background-color: #1e1e1e; padding: 20px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #333; }}
            ul {{ list-style-type: square; }}
            .warning {{ color: #ff5555; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>💀 CyberGhost OSINT Report: {target} 💀</h1>
        <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    """
    
    for section, content in data.items():
        if not content: continue
        html += f"<div class='card'><h2>{section.upper()}</h2><ul>"
        if isinstance(content, dict):
            for k, v in content.items():
                html += f"<li><strong>{k}:</strong> {v}</li>"
        elif isinstance(content, list):
            for item in content:
                # Strip rich tags for HTML
                clean_item = re.sub(r'\[.*?\]', '', str(item))
                html += f"<li>{clean_item}</li>"
        else:
             html += f"<li>{content}</li>"
        html += "</ul></div>"
        
    html += "</body></html>"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    return filename


# ---------------------------------------------------------
# PLUGIN SYSTEM
# ---------------------------------------------------------
async def run_plugins(target, plugins):
    results = {}
    for p in plugins:
        p_path = PLUGINS_DIR / f"plugin_{p}.py"
        if p_path.exists():
            spec = importlib.util.spec_from_file_location(f"plugin_{p}", p_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, 'run'):
                try: results[p] = await mod.run(target)
                except Exception as e: results[p] = f"Error: {e}"
        else:
            results[p] = "Plugin não encontrado."
    return results

# ---------------------------------------------------------
# ORCHESTRATOR & UI
# ---------------------------------------------------------
async def wrapper(key, coro):
    try: return key, await coro
    except: return key, None

async def run_scan(target, profile="standard", plugins=None, is_dark=False):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        # Pre-requisites for later tasks
        subs = await get_subdomains(session, target)
        
        tasks_dict = {
            "DNS": get_dns(target), 
            "Tech Detection": detect_tech(session, target), 
            "Subdomains (CT)": get_subdomains(session, target) # cached basically
        }
        
        if profile in ["standard", "full", "mostruoso", "godmode"]:
            tasks_dict.update({
                "Open Ports": scan_ports_hyper(target),
                "Cloud Enum": cloud_enum(target),
                "Wayback Archive": wayback_urls(session, target)
            })
            
        if profile in ["full", "mostruoso", "godmode"]:
            tasks_dict.update({
                "IP Reputation": ip_reputation(target),
                "ASN / BGP": get_asn_info(session, target)
            })
            
        if profile in ["mostruoso", "godmode"]:
            tasks_dict.update({
                "JS Spidering (Secrets)": spider_js_secrets(session, target),
                "Vuln Scanner": vuln_scan_misconfig(session, target)
            })
            
        if profile == "godmode":
            tasks_dict.update({
                "WAF Detection": detect_waf(session, target),
                "Subdomain Takeovers": check_subdomain_takeover(session, subs),
                "Dirbuster (Fuzzing)": fast_fuzz(session, target),
                "Email Harvester": email_harvester(session, target),
                "Shodan Native Recon": shodan_query(target),
                "DNS Security Posture": check_dns_sec(target),
                "Robots & Sitemap": harvest_robots(session, target),
                "Security Headers": analyze_security_headers(session, target),
                "Passive OSINT Dorks": generate_dorks_and_breaches(target),
                "Tech CVE Mapper": check_tech_cves(tasks_dict["Tech Detection"])
            })
            
        if plugins:
            tasks_dict["Plugins"] = run_plugins(target, plugins)

        results = {}
        
        print("\n")
        with Progress(
            SpinnerColumn(spinner_name="dots2" if is_dark else "bouncingBar"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="red" if is_dark else "cyan"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task_name = f"[{'red' if is_dark else 'cyan'}]Invocando Fantasmas no alvo {target}..."
            if profile == "godmode": task_name = f"[bold yellow]⚡ EXECUTANDO GOD MODE ⚡ {target}...[/]"
            
            task_id = progress.add_task(task_name, total=len(tasks_dict))
            
            pending = [wrapper(k, v) for k, v in tasks_dict.items()]
            for f in asyncio.as_completed(pending):
                k, res = await f
                results[k] = res
                progress.advance(task_id)

        print("\n")
        
        # Override subs result with the pre-fetched one if it was lost in async race
        results["Subdomains (CT)"] = subs
        return results

# ---------------------------------------------------------
# CLI MAIN
# ---------------------------------------------------------
def display_results_rich(results, is_dark):
    border_style = "red" if is_dark else "cyan"
    title_style = "bold red" if is_dark else "bold cyan"
    
    for section, content in results.items():
        if not content: continue
        
        table = Table(show_header=False, box=None, border_style=border_style, padding=(0, 2))
        table.add_column("Data", style="white")
        
        if isinstance(content, dict):
            for k, v in content.items():
                table.add_row(f"[bold]{k}:[/bold] {v}")
        elif isinstance(content, list):
            for item in content:
                table.add_row(f"• {item}")
        else:
            table.add_row(str(content))
            
        panel = Panel(table, title=f"[{title_style}]{section.upper()}[/]", border_style=border_style, expand=False)
        console.print(panel)


def main():
    parser = argparse.ArgumentParser(description="CyberGhost OSINT V13 GOD MODE")
    parser.add_argument("target", nargs='?', help="Alvo (ex: example.com)")
    parser.add_argument("--profile", choices=["quick", "standard", "full", "mostruoso", "godmode"], default="godmode", help="Nível de profundidade (Padrão: godmode)")
    parser.add_argument("--export-html", action="store_true", help="Gera um relatório HTML no final")
    parser.add_argument("--plugin", action="append", help="Nome do plugin na pasta ~/.cyberghost/plugins/")
    parser.add_argument("--logo", choices=["matrix", "cyber", "red", "rainbow", "minimal", "none", "dark", "blood", "ghost", "premium", "premium-dark"], default="matrix", help="Estilo da logo")
    parser.add_argument("--animate", action="store_true", help="Anima a logo na entrada")
    parser.add_argument("--blood-drip", action="store_true", help="Adiciona efeito de sangue escorrendo no modo dark")
    parser.add_argument("--glow", action="store_true", help="Adiciona efeito de brilho/sombra 3D aos logos premium")
    
    args = parser.parse_args()
    
    start_time = time.time()

    if not args.target:
        console.print(f"[bold red]Erro: Especifique um alvo. Use --help.[/bold red]")
        sys.exit(1)
        
    target = args.target.replace('https://', '').replace('http://', '').split('/')[0]
    
    is_dark_mode = args.logo in ["dark", "blood", "ghost", "premium-dark"]

    if args.logo != "none":
        if args.logo in ["premium", "premium-dark"]:
            print_premium_logo(style=args.logo, animate=args.animate, glow=args.glow)
        elif args.logo in ["dark", "blood", "ghost"]:
            print_logo_dark(style=args.logo, animate=args.animate, blood_drip=args.blood_drip)
        else:
            print_logo_normal(style=args.logo, animate=args.animate)

    results = asyncio.run(run_scan(target, args.profile, args.plugin, is_dark_mode))

    display_results_rich(results, is_dark_mode)

    if args.export_html:
        report_path = generate_html_report(target, results)
        console.print(f"\n[bold green]✅ Relatório HTML gerado com sucesso: {report_path}[/bold green]")

    elapsed = time.time() - start_time
    if args.profile == "godmode":
         console.print(f"\n[bold yellow]👑 GOD MODE SCAN COMPLETED IN {elapsed:.2f}s 👑[/bold yellow]")
    elif is_dark_mode:
        console.print(f"\n[bold red]💀 SCAN COMPLETED IN SHADOW MODE ({elapsed:.2f}s) 💀[/bold red]")
    else:
        console.print(f"\n[bold cyan]╔═════ SCAN CONCLUÍDO ({elapsed:.2f}s) ═════╗[/bold cyan]")

if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
