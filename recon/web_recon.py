"""
CyberGhost OSINT Enterprise — Web Reconnaissance
"""
from __future__ import annotations

import asyncio
import re
import ssl
from typing import Any

import aiohttp
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

log = structlog.get_logger(__name__)

GLOBAL_SSL_CONTEXT = ssl.create_default_context()

class WebRecon:
    """Performs HTTP-based reconnaissance: Tech, WAF, Fuzzing, Robots, Headers."""
    
    async def analyze(self, target: str) -> dict[str, Any]:
        """Runs all web recon tasks."""
        log.info("web_recon_started", target=target)
        results: dict[str, Any] = {}

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=GLOBAL_SSL_CONTEXT)) as session:
            tasks = [
                self.detect_tech(session, target),
                self.detect_waf(session, target),
                self.harvest_robots(session, target),
                self.analyze_security_headers(session, target),
                self.fast_fuzz(session, target)
            ]
            res = await asyncio.gather(*tasks, return_exceptions=True)
            
            results['tech'] = res[0] if not isinstance(res[0], Exception) else {}
            results['waf'] = res[1] if not isinstance(res[1], Exception) else []
            results['robots'] = res[2] if not isinstance(res[2], Exception) else []
            results['headers'] = res[3] if not isinstance(res[3], Exception) else []
            results['fuzz'] = res[4] if not isinstance(res[4], Exception) else []

        log.info("web_recon_completed", target=target)
        return results

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(aiohttp.ClientError))
    async def fetch_url_async(self, session: aiohttp.ClientSession, url: str, timeout: int = 15) -> str | None:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) CyberGhost/8.0.0 GODMODE'}
        try:
            async with session.get(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    return await response.text()
        except Exception:
            pass
        return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(aiohttp.ClientError))
    async def detect_tech(self, session: aiohttp.ClientSession, target: str) -> dict[str, str]:
        """Detect web technologies from headers."""
        techs = {}
        url = f"http://{target}" if not target.startswith('http') else target
        try:
            async with session.head(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5, allow_redirects=True) as response:
                headers = response.headers
                if 'Server' in headers: techs['Web Server'] = headers['Server']
                if 'X-Powered-By' in headers: techs['Framework'] = headers['X-Powered-By']
                if 'X-AspNet-Version' in headers: techs['ASP.NET'] = headers['X-AspNet-Version']
                if 'X-Generator' in headers: techs['Generator'] = headers['X-Generator']
        except Exception:
            pass
        return techs

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(aiohttp.ClientError))
    async def detect_waf(self, session: aiohttp.ClientSession, target: str) -> list[str]:
        """Inject basic payload to detect WAF."""
        url = f"http://{target}/?q=<script>alert(1)</script>"
        try:
            async with session.get(url, timeout=5) as resp:
                server = resp.headers.get('Server', '').lower()
                if resp.status in [403, 406]:
                    if 'cloudflare' in server: return ["[red]CRÍTICO: Cloudflare WAF Detectado[/red]"]
                    if 'akamai' in server: return ["[red]CRÍTICO: Akamai WAF Detectado[/red]"]
                    if 'imperva' in server or 'incapsula' in server: return ["[red]CRÍTICO: Imperva WAF Detectado[/red]"]
                    if 'awselb' in server: return ["[red]CRÍTICO: AWS WAF Detectado[/red]"]
                    return ["[yellow]ALERTA: WAF Genérico / Bloqueio Detectado (Status 403 em Payload)[/yellow]"]
                else:
                    return ["[green]Nenhum WAF estrito detectado para payloads básicos.[/green]"]
        except Exception:
            return ["[dim]Falha ao testar WAF.[/dim]"]

    async def fast_fuzz(self, session: aiohttp.ClientSession, target: str) -> list[str]:
        """Dirbusting ultra-rápido para diretórios críticos."""
        paths = ['/admin', '/login', '/api', '/backup.zip', '/config.php', '/wp-admin', '/dashboard', '/test']
        
        async def check_path(path: str) -> str | None:
            url = f"http://{target}{path}"
            try:
                async with session.get(url, timeout=3, allow_redirects=False) as resp:
                    if resp.status in [200, 301, 302, 403] and resp.status != 404:
                        return f"[yellow]Descoberto: {path} (Status: {resp.status})[/yellow]"
            except Exception:
                pass
            return None

        tasks = [check_path(p) for p in paths]
        res = await asyncio.gather(*tasks)
        return [r for r in res if r]

    async def harvest_robots(self, session: aiohttp.ClientSession, target: str) -> list[str]:
        """Busca passiva por paths ocultos no robots.txt e checa se sitemap.xml existe."""
        findings = []
        
        # Robots.txt
        url_robots = f"http://{target}/robots.txt"
        html = await self.fetch_url_async(session, url_robots, timeout=4)
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
            async with session.head(url_sitemap, timeout=3) as resp:
                if resp.status == 200:
                    findings.append(f"[cyan]Sitemap Detectado:[/cyan] {url_sitemap}")
        except Exception:
            pass
        
        return findings if findings else ["[green]Nada oculto encontrado em arquivos padrão.[/green]"]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(aiohttp.ClientError))
    async def analyze_security_headers(self, session: aiohttp.ClientSession, target: str) -> list[str]:
        """Inspeciona cabeçalhos de resposta HTTP para postura defensiva."""
        url = f"http://{target}"
        findings = []
        try:
            async with session.head(url, timeout=5, allow_redirects=True) as resp:
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
        except Exception:
            return ["[dim]Não foi possível checar headers.[/dim]"]
