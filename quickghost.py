import sys
import socket
import urllib.request
import urllib.error
import json
import subprocess
import time
import platform

# Cores ANSI
C = "\033[1;36m"
G = "\033[1;32m"
R = "\033[1;31m"
Y = "\033[1;33m"
NC = "\033[0m"

def print_banner(target):
    print(f"{C}╔══════════════════════════════════════════════════════════════════╗{NC}")
    print(f"{C}║     QUICKGHOST OSINT - MODO RÁPIDO STANDALONE                    ║{NC}")
    print(f"{C}║     Alvo: {target:<54} ║{NC}")
    print(f"{C}╚══════════════════════════════════════════════════════════════════╝{NC}")
    print("")

def get_dns(target):
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
    print(f"\n{Y}🔐 CERTIFICADOS (crt.sh):{NC}")
    try:
        url = f"https://crt.sh/?q={target}&output=json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            if not data:
                print("   Nenhum certificado encontrado.")
                return
            
            # Pega os 5 mais recentes únicos
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
    print(f"\n{Y}📡 REGISTRO (RDAP / WHOIS):{NC}")
    try:
        # Usa a API RDAP pública para obter informações formatadas do domínio
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
    print(f"\n{Y}⚡ PING (Conectividade):{NC}")
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    try:
        # Timeout e capture_output para não poluir demais a tela
        result = subprocess.run(["ping", param, "4", target], capture_output=True, text=True, timeout=10)
        lines = result.stdout.split('\n')
        
        # Filtra linhas para um resumo bonito
        useful = [l.strip() for l in lines if 'Pinging' in l or 'PING' in l or 'ms' in l or 'loss' in l or 'perda' in l]
        
        if useful:
            for l in useful[-3:]:  # Pega as estatísticas finais
                if l:
                    print(f"   {l}")
        else:
            print(f"   {R}O host não respondeu ao ping.{NC}")
    except subprocess.TimeoutExpired:
        print(f"   {R}Ping excedeu o tempo limite.{NC}")
    except Exception as e:
        print(f"   {R}Erro ao executar ping: {e}{NC}")

def main():
    if sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass
            
    if len(sys.argv) < 2:
        print(f"{R}Uso: python quickghost.py <dominio_ou_ip>{NC}")
        sys.exit(1)
        
    target = sys.argv[1].replace('https://', '').replace('http://', '').split('/')[0]
    
    start_time = time.time()
    print_banner(target)
    
    get_dns(target)
    get_certs(target)
    
    # Executa RDAP apenas se não for um IP direto (RDAP para IPs tem outro endpoint, focaremos em domínios)
    if not target.replace('.', '').isdigit():
        get_whois_rdap(target)
        
    do_ping(target)
    
    elapsed = time.time() - start_time
    print(f"\n{G}✅ Scan concluído em {elapsed:.2f} segundos.{NC}")

if __name__ == "__main__":
    main()
