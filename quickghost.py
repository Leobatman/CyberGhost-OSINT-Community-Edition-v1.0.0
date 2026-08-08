import sys
import socket
import urllib.request
import urllib.error
import json
import subprocess
import time
import platform
import argparse

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.live import Live
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

ASCII_ART = """
[bold cyan]
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  ██████╗ ██╗   ██╗██████╗ ███████╗██████╗ ██████╗ ██╗  ██╗██████╗ ███████╗ ║
║ ██╔═══██╗██║   ██║██╔══██╗██╔════╝██╔══██╗██╔════╝ ██║  ██║██╔══██╗██╔════╝ ║
║ ██║   ██║██║   ██║██████╔╝█████╗  ██████╔╝██║  ███╗███████║██║  ██║███████╗ ║
║ ██║▄▄ ██║██║   ██║██╔══██╗██╔══╝  ██╔══██╗██║   ██║██╔══██║██║  ██║╚════██║ ║
║ ╚██████╔╝╚██████╔╝██║  ██║███████╗██║  ██║╚██████╔╝██║  ██║██████╔╝███████║ ║
║  ╚══▀▀═╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚══════╝ ║
║                                                                              ║
║          [italic white]QUICKGHOST v1.0 - MODO STANDALONE (ZERO DEPENDENCIES)[/italic white]         ║
╚══════════════════════════════════════════════════════════════════════════════╝
[/bold cyan]
"""

# Fallback ANSI Colors
C = "\033[1;36m"
G = "\033[1;32m"
R = "\033[1;31m"
Y = "\033[1;33m"
NC = "\033[0m"

def print_banner(target):
    if HAS_RICH:
        console.print(ASCII_ART)
        console.print(f"[bold white]🎯 ALVO:[/bold white] [bold red]{target}[/bold red]\n")
    else:
        print(f"{C}╔══════════════════════════════════════════════════════════════════╗{NC}")
        print(f"{C}║     QUICKGHOST OSINT - MODO RÁPIDO STANDALONE                    ║{NC}")
        print(f"{C}║     Alvo: {target:<54} ║{NC}")
        print(f"{C}╚══════════════════════════════════════════════════════════════════╝{NC}")
        print("")

def get_dns(target):
    if HAS_RICH:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Tipo")
        table.add_column("Endereço IP")
        
        try:
            ip = socket.gethostbyname(target)
            table.add_row("A (IPv4)", f"[bold green]{ip}[/bold green]")
            try:
                addrinfo = socket.getaddrinfo(target, None, socket.AF_INET6)
                ipv6 = addrinfo[0][4][0]
                table.add_row("AAAA (IPv6)", f"[bold blue]{ipv6}[/bold blue]")
            except:
                pass
            console.print(Panel(table, title="[bold yellow]🌐 Resolução DNS[/bold yellow]", expand=False))
        except socket.gaierror:
            console.print("[bold red]Falha ao resolver DNS. Verifique o domínio.[/bold red]")
    else:
        print(f"{Y}🌐 RESOLUÇÃO DNS:{NC}")
        try:
            ip = socket.gethostbyname(target)
            print(f"   A      {ip}")
            try:
                addrinfo = socket.getaddrinfo(target, None, socket.AF_INET6)
                ipv6 = addrinfo[0][4][0]
                print(f"   AAAA   {ipv6}")
            except:
                pass
        except socket.gaierror:
            print(f"   {R}Falha ao resolver DNS. Verifique se o domínio é válido.{NC}")

def get_certs(target):
    if HAS_RICH:
        table = Table(show_header=False)
        table.add_column("Certificado")
        try:
            url = f"https://crt.sh/?q={target}&output=json"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
                if not data:
                    table.add_row("Nenhum certificado encontrado.")
                else:
                    seen = set()
                    count = 0
                    for cert in data:
                        name = cert.get('name_value', '').replace('\n', ', ')
                        if name not in seen:
                            seen.add(name)
                            table.add_row(f"🔒 {name}")
                            count += 1
                        if count >= 5:
                            break
            console.print(Panel(table, title="[bold yellow]🔐 Certificados Recentes (crt.sh)[/bold yellow]", expand=False))
        except Exception as e:
            console.print(f"[bold red]Erro ao buscar certificados:[/bold red] {e}")
    else:
        print(f"\n{Y}🔐 CERTIFICADOS (crt.sh):{NC}")
        try:
            url = f"https://crt.sh/?q={target}&output=json"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
                if not data:
                    print("   Nenhum certificado encontrado.")
                    return
                seen = set()
                count = 0
                for cert in data:
                    name = cert.get('name_value', '').replace('\n', ', ')
                    if name not in seen:
                        seen.add(name)
                        print(f"   - {name}")
                        count += 1
                    if count >= 5:
                        break
        except Exception as e:
            print(f"   {R}Erro ao buscar certificados: {e}{NC}")

def get_whois_rdap(target):
    if HAS_RICH:
        table = Table(show_header=False)
        table.add_column("Propriedade", style="bold cyan")
        table.add_column("Valor")
        try:
            url = f"https://rdap.org/domain/{target}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                handle = data.get('handle', 'N/A')
                table.add_row("Handle", handle)
                
                entities = data.get('entities', [])
                for ent in entities:
                    roles = ", ".join(ent.get('roles', []))
                    if 'vcardArray' in ent:
                        vcard = ent['vcardArray'][1]
                        for prop in vcard:
                            if prop[0] == 'fn':
                                table.add_row(roles.capitalize(), prop[3])
            console.print(Panel(table, title="[bold yellow]📡 Registro RDAP[/bold yellow]", expand=False))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                console.print(f"[bold red]Domínio não encontrado no RDAP ou TLD não suportado.[/bold red]")
            else:
                console.print(f"[bold red]Erro na consulta RDAP: HTTP {e.code}[/bold red]")
        except Exception as e:
            console.print(f"[bold red]Erro na consulta RDAP: {e}[/bold red]")
    else:
        print(f"\n{Y}📡 REGISTRO (RDAP / WHOIS):{NC}")
        try:
            url = f"https://rdap.org/domain/{target}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                handle = data.get('handle', 'N/A')
                print(f"   Handle: {handle}")
                
                entities = data.get('entities', [])
                for ent in entities:
                    roles = ", ".join(ent.get('roles', []))
                    if 'vcardArray' in ent:
                        vcard = ent['vcardArray'][1]
                        for prop in vcard:
                            if prop[0] == 'fn':
                                print(f"   {roles.capitalize()}: {prop[3]}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"   {R}Domínio não encontrado no RDAP ou TLD não suportado.{NC}")
            else:
                print(f"   {R}Erro na consulta RDAP: HTTP {e.code}{NC}")
        except Exception as e:
            print(f"   {R}Erro na consulta RDAP: {e}{NC}")

def do_ping(target):
    if HAS_RICH:
        console.print("\n[bold yellow]⚡ PING (Conectividade):[/bold yellow]")
    else:
        print(f"\n{Y}⚡ PING (Conectividade):{NC}")
        
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    try:
        result = subprocess.run(["ping", param, "4", target], capture_output=True, text=True, timeout=10)
        lines = result.stdout.split('\n')
        useful = [l.strip() for l in lines if 'Pinging' in l or 'PING' in l or 'ms' in l or 'loss' in l or 'perda' in l]
        
        if useful:
            for l in useful[-3:]:
                if l:
                    if HAS_RICH:
                        console.print(f"   {l}")
                    else:
                        print(f"   {l}")
        else:
            if HAS_RICH:
                console.print(f"   [bold red]O host não respondeu ao ping.[/bold red]")
            else:
                print(f"   {R}O host não respondeu ao ping.{NC}")
    except subprocess.TimeoutExpired:
        if HAS_RICH:
            console.print(f"   [bold red]Ping excedeu o tempo limite.[/bold red]")
        else:
            print(f"   {R}Ping excedeu o tempo limite.{NC}")
    except Exception as e:
        if HAS_RICH:
            console.print(f"   [bold red]Erro ao executar ping:[/bold red] {e}")
        else:
            print(f"   {R}Erro ao executar ping: {e}{NC}")

def main():
    if sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    parser = argparse.ArgumentParser(description="QuickGhost OSINT - Modo Rápido Standalone")
    parser.add_argument("target", help="O domínio ou IP alvo a ser dissecado (ex: google.com)")
    args = parser.parse_args()

    target = args.target.replace('https://', '').replace('http://', '').split('/')[0]
    
    import re
    if re.search(r'[;&|\\$><`\n\r]', target):
        if HAS_RICH:
            console.print(f"[bold red]Erro: O alvo contém caracteres inválidos ou perigosos.[/bold red]")
        else:
            print(f"{R}Erro: O alvo contém caracteres inválidos ou perigosos.{NC}")
        sys.exit(1)

    start_time = time.time()
    print_banner(target)
    
    get_dns(target)
    console.print() if HAS_RICH else None
    get_certs(target)
    console.print() if HAS_RICH else None
    
    if not target.replace('.', '').isdigit():
        get_whois_rdap(target)
        
    do_ping(target)
    
    elapsed = time.time() - start_time
    if HAS_RICH:
        console.print(f"\n[bold green]✅ Scan concluído em {elapsed:.2f} segundos.[/bold green]")
    else:
        print(f"\n{G}✅ Scan concluído em {elapsed:.2f} segundos.{NC}")

if __name__ == "__main__":
    main()
