import sys
import socket
import urllib.request
import urllib.error
import urllib.parse
import json
import asyncio
import time
import argparse
import platform
import os
import math
import random
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import importlib.util
from datetime import datetime
import threading

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

# ANSI Colors
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
# VISUALS & LOGOS
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
║  ║    ██████╗ ███████╗██╗████████╗██╗  ██╗ █████╗ ██╗    ██╗██╗   ██╗███████╗██╗     ██╗                     ║ ║
║  ║    ██╔══██╗██╔════╝██║╚══██╔══╝██║  ██║██╔══██╗██║    ██║██║   ██║██╔════╝██║     ██║                     ║ ║
║  ║    ██████╔╝█████╗  ██║   ██║   ███████║███████║██║ █╗ ██║██║   ██║█████╗  ██║     ██║                     ║ ║
║  ║    ██╔══██╗██╔══╝  ██║   ██║   ██╔══██║██╔══██║██║███╗██║╚██╗ ██╔╝██╔══╝  ██║     ██║                     ║ ║
║  ║    ██║  ██║███████╗██║   ██║   ██║  ██║██║  ██║╚███╔███╔╝ ╚████╔╝ ███████╗███████╗██║                     ║ ║
║  ║    ╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝   ╚═══╝  ╚══════╝╚══════╝╚═╝                     ║ ║
║  ║                                                                                                              ║ ║
║  ║                          ██████╗ ███████╗██╗   ██╗███████╗██╗     ██████╗ ██████╗                          ║ ║
║  ║                          ██╔══██╗██╔════╝██║   ██║██╔════╝██║     ██╔══██╗██╔══██╗                         ║ ║
║  ║                          ██████╔╝█████╗  ██║   ██║█████╗  ██║     ██║  ██║██████╔╝                         ║ ║
║  ║                          ██╔══██╗██╔══╝  ╚██╗ ██╔╝██╔══╝  ██║     ██║  ██║██╔══██╗                         ║ ║
║  ║                          ██████╔╝███████╗ ╚████╔╝ ███████╗███████╗██████╔╝██████╔╝                         ║ ║
║  ║                          ╚═════╝ ╚══════╝  ╚═══╝  ╚══════╝╚══════╝╚═════╝ ╚═════╝                          ║ ║
║  ║                                                                                                              ║ ║
║  ╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝ ║
║                                                                                                                   ║
║                    ╔══════════════════════════════════════════════════════════════════════════════╗               ║
║                    ║  v11.0 "SHADOW WARRIOR" • MEGA OSINT ENGINE • RECON • THREAT INTEL • AI       ║               ║
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
║     ░█████╗░██╗░░░██╗██████╗░███████╗██████╗░░█████╗░░█████╗░██████╗░████████╗║
║     ██╔══██╗╚██╗░██╔╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝║
║     ██║░░╚═╝░╚████╔╝░██████╔╝█████╗░░██████╔╝██║░░╚═╝██║░░██║██████╔╝░░░██║░░░║
║     ██║░░██╗░░╚██╔╝░░██╔══██╗██╔══╝░░██╔══██╗██║░░██╗██║░░██║██╔══██╗░░░██║░░░║
║     ╚█████╔╝░░░██║░░░██║░░██║███████╗██║░░██║╚█████╔╝╚█████╔╝██║░░██║░░░██║░░░║
║     ░╚════╝░░░░╚═╝░░░╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝░╚════╝░░╚════╝░╚═╝░░╚═╝░░░╚═╝░░░║
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
{shadow}║{NC}                       {accent}██████╗{NC} {accent}██╗{NC}  {accent}██╗{NC} {accent} ██████╗{NC} {accent}███████╗{NC}{accent}████████╗{NC}                                            {shadow}║{NC}
{shadow}║{NC}                      {accent}██╔════╝{NC} {accent}██║{NC}  {accent}██║{NC}{accent}██╔═══██╗{NC}{accent}██╔════╝{NC}{accent}╚══██╔══╝{NC}                                            {shadow}║{NC}
{shadow}║{NC}                      {accent}██║{NC}  {accent}███╗{NC}{accent}███████║{NC}{accent}██║{NC}   {accent}██║{NC}{accent}█████╗{NC}     {accent}██║{NC}                                               {shadow}║{NC}
{shadow}║{NC}                      {accent}██║{NC}   {accent}██║{NC}{accent}██╔══██║{NC}{accent}██║{NC}   {accent}██║{NC}{accent}██╔══╝{NC}     {accent}██║{NC}                                               {shadow}║{NC}
{shadow}║{NC}                      {accent}╚██████╔╝{NC}{accent}██║{NC}  {accent}██║{NC}{accent}╚██████╔╝{NC}{accent}███████╗{NC}   {accent}██║{NC}                                               {shadow}║{NC}
{shadow}║{NC}                       {accent}╚═════╝{NC} {accent}╚═╝{NC}  {accent}╚═╝{NC} {accent}╚═════╝{NC} {accent}╚══════╝{NC}   {accent}╚═╝{NC}                                               {shadow}║{NC}
{shadow}║{NC}                                                                                                                           {shadow}║{NC}
{shadow}║{NC}                      {accent}✦{NC} {cyan}CYBERGHOST OSINT v11.0{NC} {accent}-{NC} {cyan}\"SHADOW WARRIOR\" EDITION{NC} {accent}✦{NC}                                          {shadow}║{NC}
{shadow}║{NC}                                                                                                                           {shadow}║{NC}
{shadow}║{NC}                      {accent}╔══════════════════════════════════════════════════════════════════════════╗{NC}               {shadow}║{NC}
{shadow}║{NC}                      {accent}║{NC}  {cyan}🔥 THE MOST ADVANCED OSINT PLATFORM ON THE PLANET 🔥{NC}  {accent}║{NC}               {shadow}║{NC}
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
        print(f"║     CYBERGHOST OSINT v11.0 - \"SHADOW WARRIOR\"                    ║")
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
            
    print(f"\n{BLOOD_RED}Iniciando a invocação...{NC}")
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
║                      ⚠️  WARNING: SHADOW MODE ACTIVE  ⚠️                       ║
║                                                                               ║
║           Este modo opera nas sombras. Use apenas em alvos autorizados.       ║
║                     A cyberjustiça não dorme. Você foi avisado.               ║
║                                                                               ║
║                        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                       ║
║                        ░  ENTER AT YOUR OWN RISK  ░                       ║
║                        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                       ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝{NC}
"""
    print(warning)
    if animate: time.sleep(1)


def loading_banner():
    banner = f"""{M}
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                     │
│                                          🔥 CYBERGHOST OSINT v11.0 🔥                                               │
│                                       Carregando módulos de reconhecimento...                                        │
│                                                                                                                     │
│  [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓] 100%                               │
│                                                                                                                     │
│  ✅ DNS Resolver      🔥 CARREGADO                                                                                  │
│  ✅ Cert Scan         🔥 CARREGADO                                                                                  │
│  ✅ Subdomain Enum    🔥 CARREGADO                                                                                  │
│  ✅ Port Scanner      🔥 CARREGADO                                                                                  │
│  ✅ Tech Detect       🔥 CARREGADO                                                                                  │
│  ✅ IP Reputation     🔥 CARREGADO                                                                                  │
│  ✅ Wayback Machine   🔥 CARREGADO                                                                                  │
│  ✅ ASN & BGP         🔥 CARREGADO                                                                                  │
│  ✅ Cloud Enum        🔥 CARREGADO                                                                                  │
│                                                                                                                     │
│                                          🚀 PRONTO PARA ESCANEAR 🚀                                                 │
│                                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘{NC}
"""
    print(banner)
    time.sleep(1.0)

def print_signature(elapsed, is_dark=False):
    if is_dark:
        sig = f"""{DARK_RED}
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                      💀  SCAN COMPLETED IN SHADOW MODE  💀                      ║
║                                                                               ║
║                     O fantasma observou. Os dados foram coletados.            ║
║                          Nada escapa do CYBERGHOST.                           ║
║                                                                               ║
║                           ╔═════════════════════════════╗                     ║
║                           ║  CYBERGHOST OSINT v11.0     ║                     ║
║                           ║  "SHADOW WARRIOR"           ║                     ║
║                           ║  Scan: {elapsed:<15.2f}      ║                     ║
║                           ╚═════════════════════════════╝                     ║
║                                                                               ║
║                         🔒 Use com responsabilidade. 🔒                         ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝{NC}"""
    else:
        sig = f"""{C}
╔═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                                   ║
║                                     ╔═══════════════════════════════════════════╗                                 ║
║                                     ║  CYBERGHOST OSINT v11.0 "SHADOW WARRIOR"   ║                                 ║
║                                     ║  Scan concluído em {elapsed:<23.2f} ║                                 ║
║                                     ║  Desenvolvido por CyberGhost Team          ║                                 ║
║                                     ║  Uso autorizado apenas em alvos próprios   ║                                 ║
║                                     ╚═══════════════════════════════════════════╝                                 ║
║                                                                                                                   ║
║                                   🔒 Uso ético e responsável sempre! 🔒                                           ║
║                                                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝{NC}"""
    print(sig)


# ---------------------------------------------------------
# CORE HELPERS
# ---------------------------------------------------------
async def fetch_url(url, timeout=10, headers=None, method='GET', data=None):
    if headers is None:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) CyberGhost/11.0'}
    req = urllib.request.Request(url, headers=headers, method=method, data=data)
    try:
        response = await asyncio.to_thread(urllib.request.urlopen, req, timeout=timeout)
        return response.read().decode('utf-8', errors='ignore')
    except Exception:
        return None

# ---------------------------------------------------------
# OSINT MODULES
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

async def get_subdomains(target):
    data = await fetch_url(f"https://crt.sh/?q=%25.{target}&output=json", timeout=15)
    subs = set()
    if data:
        try:
            for cert in json.loads(data):
                name = cert.get('name_value', '')
                for n in name.split('\n'):
                    if n.endswith(target) and '*' not in n: subs.add(n)
        except: pass
    return list(subs)[:50]

async def scan_port(target, port, timeout=2):
    try:
        conn = asyncio.open_connection(target, port)
        reader, writer = await asyncio.wait_for(conn, timeout=timeout)
        writer.close(); await writer.wait_closed()
        return port
    except: return None

async def scan_ports(target):
    ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306, 3389, 8080, 8443]
    try:
        ip = await asyncio.to_thread(socket.gethostbyname, target)
    except: return []
    tasks = [scan_port(ip, p) for p in ports]
    results = await asyncio.gather(*tasks)
    open_ports = [p for p in results if p is not None]
    port_map = {21:"FTP", 22:"SSH", 25:"SMTP", 80:"HTTP", 443:"HTTPS", 3306:"MySQL", 3389:"RDP", 8080:"HTTP-Alt"}
    return [f"{p}/{port_map.get(p, 'Unknown')}" for p in open_ports]

async def detect_tech(target):
    techs = {}
    url = f"http://{target}" if not target.startswith('http') else target
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}, method='HEAD')
        response = await asyncio.to_thread(urllib.request.urlopen, req, timeout=5)
        headers = dict(response.info())
        if 'Server' in headers: techs['Web Server'] = headers['Server']
        if 'X-Powered-By' in headers: techs['Framework'] = headers['X-Powered-By']
    except: pass
    return techs

async def ip_reputation(target):
    try: ip = await asyncio.to_thread(socket.gethostbyname, target)
    except: return {"DNSBL": "Não foi possível resolver IP"}
    reverse_ip = ".".join(reversed(ip.split(".")))
    results = {}
    for bl in ["zen.spamhaus.org", "b.barracudacentral.org"]:
        try:
            await asyncio.to_thread(socket.gethostbyname, f"{reverse_ip}.{bl}")
            results[bl] = "⚠️ LISTADO"
        except socket.gaierror:
            results[bl] = "✅ CLEAN"
    return results

async def wayback_urls(target):
    url = f"http://web.archive.org/cdx/search/cdx?url=*.{target}/*&output=json&limit=10"
    data = await fetch_url(url, timeout=10)
    urls = []
    if data:
        try:
            parsed = json.loads(data)
            if len(parsed) > 1:
                urls = [f"{row[1][:4]}-{row[1][4:6]}-{row[1][6:8]}: {row[2]}" for row in parsed[1:]]
        except: pass
    return urls

async def get_asn_info(target):
    try:
        ip = await asyncio.to_thread(socket.gethostbyname, target)
        data = await fetch_url(f"https://stat.ripe.net/data/whois/data.json?resource={ip}")
        if data:
            records = json.loads(data).get("data", {}).get("records", [])
            for r in records:
                for attr in r:
                    if attr.get("key") in ["netname", "descr"]:
                        return [f"{attr['key'].upper()}: {attr['value']}"]
    except: pass
    return []

async def get_reverse_ip(target):
    try:
        ip = await asyncio.to_thread(socket.gethostbyname, target)
        data = await fetch_url(f"https://api.hackertarget.com/reverseiplookup/?q={ip}")
        if data and "error" not in data.lower() and "no dns" not in data.lower():
            return data.strip().split('\n')[:10]
    except: pass
    return []

async def cloud_enum(target):
    clouds = {"aws": f"{target}.s3.amazonaws.com", "gcp": f"{target}.storage.googleapis.com"}
    results = []
    for provider, domain in clouds.items():
        try:
            await asyncio.to_thread(socket.gethostbyname, domain)
            results.append(f"{provider.upper()}: ENCONTRADO ({domain})")
        except: pass
    return results

async def pastebin_dorks(target):
    return [
        f"Google: site:pastebin.com \"{target}\"",
        f"Google: site:github.com \"{target}\" password"
    ]

# ---------------------------------------------------------
# PLUGIN SYSTEM & CACHE
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

def get_cache(target):
    c_file = CACHE_DIR / f"{target}.json"
    if c_file.exists() and (time.time() - c_file.stat().st_mtime < 3600):
        with open(c_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_cache(target, data):
    with open(CACHE_DIR / f"{target}.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def make_diff(old, new):
    diff = {}
    for k in new:
        if isinstance(new[k], list):
            added = list(set(new[k]) - set(old.get(k, [])))
            if added: diff[k] = added
        elif isinstance(new[k], dict):
            added = {dk: dv for dk, dv in new[k].items() if dk not in old.get(k, {}) or old[k][dk] != dv}
            if added: diff[k] = added
        else:
            if old.get(k) != new[k]: diff[k] = new[k]
    return diff

async def trigger_webhook(url, data):
    payload = json.dumps({"text": "CyberGhost Scan Concluído", "results": data}).encode('utf-8')
    await fetch_url(url, method='POST', headers={'Content-Type': 'application/json'}, data=payload)

# ---------------------------------------------------------
# ORCHESTRATOR
# ---------------------------------------------------------
async def wrapper(key, coro):
    try: return key, await coro
    except: return key, None

def print_section(title, content_lines):
    if not content_lines: return
    print(f"\n{C}┌─────────────────────────────────────────────────────────────────┐{NC}")
    print(f"{C}│ {title.ljust(63)} │{NC}")
    print(f"{C}├─────────────────────────────────────────────────────────────────┤{NC}")
    for line in content_lines:
        clean = line.replace(C,'').replace(G,'').replace(R,'').replace(Y,'').replace(M,'').replace(NC,'')
        if len(clean) > 63: line = line[:60] + "..."
        print(f"│ {line}")

def print_section_dark(title, content_lines):
    if not content_lines: return
    print(f"\n{DARK_RED}┌─💀──────────────────────────────────────────────────────────────┐{NC}")
    print(f"{BLOOD_RED}│ {title.ljust(63)} │{NC}")
    print(f"{DARK_RED}├─────────────────────────────────────────────────────────────────┤{NC}")
    for line in content_lines:
        clean = line.replace(C,'').replace(G,'').replace(R,'').replace(Y,'').replace(M,'').replace(NC,'')
        if len(clean) > 63: line = line[:60] + "..."
        print(f"{DARK_RED}│{NC} {GHOST_GRAY}{line}{NC}")
    print(f"{DARK_RED}└─────────────────────────────────────────────────────────────────┘{NC}")


async def run_scan(target, profile="standard", plugins=None, is_dark=False):
    tasks_dict = {"dns": get_dns(target), "tech": detect_tech(target), "certs_sub": get_subdomains(target)}
    
    if profile in ["standard", "full"]:
        tasks_dict.update({
            "ports": scan_ports(target),
            "cloud": cloud_enum(target),
            "wayback": wayback_urls(target)
        })
        
    if profile == "full":
        tasks_dict.update({
            "rep": ip_reputation(target),
            "asn": get_asn_info(target),
            "reverse": get_reverse_ip(target),
            "dorks": pastebin_dorks(target)
        })
        
    if plugins:
        tasks_dict["plugins"] = run_plugins(target, plugins)

    total = len(tasks_dict)
    completed = 0
    results = {}
    
    if is_dark:
        print(f"\n{BLOOD_RED}INVOCANDO FANTASMAS ({profile})...{NC}\n")
    else:
        print(f"\n{M}Iniciando SCAN ({profile})...{NC}\n")
    
    def draw_bar():
        pct = int((completed / total) * 100) if total > 0 else 100
        bar = "█" * (pct // 3) + "░" * (33 - (pct // 3))
        if is_dark:
            sys.stdout.write(f"\r{DARK_RED}[{BLOOD_RED}{bar}{DARK_RED}] {pct}% | {completed}/{total} almas extraídas{NC}")
        else:
            sys.stdout.write(f"\r{C}[{bar}] {pct}% | {completed}/{total} tasks concluídas{NC}")
        sys.stdout.flush()

    draw_bar()
    pending = [wrapper(k, v) for k, v in tasks_dict.items()]
    for f in asyncio.as_completed(pending):
        k, res = await f
        results[k] = res
        completed += 1
        draw_bar()
    
    print("\n")
    return results

# ---------------------------------------------------------
# API SERVER
# ---------------------------------------------------------
class CyberGhostAPI(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/scan':
            query = urllib.parse.parse_qs(parsed.query)
            target = query.get('target', [''])[0]
            if not target:
                self.send_response(400); self.end_headers()
                return
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(run_scan(target, profile="quick"))
            loop.close()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(results).encode('utf-8'))
        else:
            self.send_response(404); self.end_headers()

def run_api_server(port):
    server = HTTPServer(('0.0.0.0', port), CyberGhostAPI)
    print(f"{G}[+] Servidor API CyberGhost rodando em http://localhost:{port}{NC}")
    server.serve_forever()

# ---------------------------------------------------------
# CLI MAIN
# ---------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="CyberGhost OSINT V11")
    parser.add_argument("target", nargs='?', help="Alvo (ex: example.com)")
    parser.add_argument("--profile", choices=["quick", "standard", "full"], default="standard")
    parser.add_argument("--diff", action="store_true", help="Mostra apenas novidades comparado ao cache")
    parser.add_argument("--no-cache", action="store_true", help="Ignora cache existente")
    parser.add_argument("--webhook", help="URL para POST dos resultados JSON")
    parser.add_argument("--plugin", action="append", help="Nome do plugin na pasta ~/.cyberghost/plugins/")
    parser.add_argument("--api", action="store_true", help="Inicia como Servidor REST API")
    parser.add_argument("--port", type=int, default=5000, help="Porta da API")
    parser.add_argument("--logo", choices=["matrix", "cyber", "red", "rainbow", "minimal", "none", "dark", "blood", "ghost", "premium", "premium-dark"], default="matrix", help="Estilo da logo")
    parser.add_argument("--animate", action="store_true", help="Anima a logo na entrada")
    parser.add_argument("--blood-drip", action="store_true", help="Adiciona efeito de sangue escorrendo no modo dark")
    parser.add_argument("--glow", action="store_true", help="Adiciona efeito de brilho/sombra 3D aos logos premium")
    
    args = parser.parse_args()
    
    start_time = time.time()

    if args.api:
        run_api_server(args.port)
        return

    if not args.target:
        print(f"{R}Erro: Especifique um alvo ou inicie a API (--api).{NC}")
        sys.exit(1)
        
    target = args.target.replace('https://', '').replace('http://', '').split('/')[0]
    
    is_dark_mode = args.logo in ["dark", "blood", "ghost", "premium-dark"]

    # Imprime a logo incrível
    if args.logo != "none":
        if args.logo in ["premium", "premium-dark"]:
            print_premium_logo(style=args.logo, animate=args.animate, glow=args.glow)
        elif args.logo in ["dark", "blood", "ghost"]:
            print_logo_dark(style=args.logo, animate=args.animate, blood_drip=args.blood_drip)
        else:
            print_logo_normal(style=args.logo, animate=args.animate)

    if args.profile == "full" and not args.diff and not is_dark_mode:
        loading_banner()

    # Caching Logic
    old_cache = get_cache(target) if not args.no_cache else None
    if old_cache and not args.diff:
        print(f"{G}Usando resultados do cache (menos de 1h). Use --no-cache para forçar novo scan.{NC}")
        results = old_cache
    else:
        results = asyncio.run(run_scan(target, args.profile, args.plugin, is_dark_mode))
        save_cache(target, results)

    # Mostrar Resultados (ou Diff)
    display_data = results
    if args.diff:
        if not old_cache:
            print(f"{Y}Aviso: Não há cache anterior para comparar. Mostrando tudo.{NC}")
        else:
            display_data = make_diff(old_cache, results)
            print(f"\n{M}--- MODO DIFF ATIVADO (MOSTRANDO APENAS NOVIDADES) ---{NC}")

    # Output Helpers
    p_sec = print_section_dark if is_dark_mode else print_section

    if "dns" in display_data: p_sec("🌐 DNS", [f"{k:<5} {v}" for k, v in display_data["dns"].items()])
    if "certs_sub" in display_data: p_sec("🔍 SUBDOMÍNIOS", display_data["certs_sub"])
    if "ports" in display_data: p_sec("🔌 PORTAS ABERTAS", display_data["ports"])
    if "tech" in display_data: p_sec("💻 TECNOLOGIAS", [f"{k}: {v}" for k, v in display_data["tech"].items()])
    if "cloud" in display_data: p_sec("☁️ CLOUD ENUM", display_data["cloud"])
    if "rep" in display_data: p_sec("⚠️ REPUTAÇÃO DO IP", [f"{k}: {v}" for k, v in display_data["rep"].items()])
    if "asn" in display_data: p_sec("🏢 ASN / BGP", display_data["asn"])
    if "reverse" in display_data: p_sec("🔄 REVERSE IP", display_data["reverse"])
    if "wayback" in display_data: p_sec("📜 WAYBACK MACHINE", display_data["wayback"])
    if "dorks" in display_data: p_sec("🕵️ DORKS PRONTAS", display_data["dorks"])
    
    if "plugins" in display_data:
        for pk, pv in display_data["plugins"].items():
            p_sec(f"🧩 PLUGIN: {pk.upper()}", [str(pv)])

    if args.webhook:
        asyncio.run(trigger_webhook(args.webhook, results))
        print(f"\n{G}Webhook enviado para {args.webhook}{NC}")

    # Final Hacker Signature
    elapsed = time.time() - start_time
    print_signature(elapsed, is_dark=is_dark_mode)

if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
