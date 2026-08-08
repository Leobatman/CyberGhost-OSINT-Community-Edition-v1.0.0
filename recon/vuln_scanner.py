"""
CyberGhost OSINT Enterprise — Vulnerability Scanner
"""
from __future__ import annotations

import asyncio
import re
import ssl
from typing import Any

import aiohttp
from bs4 import BeautifulSoup
import structlog

log = structlog.get_logger(__name__)

GLOBAL_SSL_CONTEXT = ssl.create_default_context()

class VulnScanner:
    """Scans for vulnerabilities, misconfigurations, and leaked secrets."""
    
    async def analyze(self, target: str, tech_results: dict[str, str] = None) -> dict[str, Any]:
        """Runs vulnerability scanning tasks."""
        log.info("vuln_scan_started", target=target)
        results: dict[str, Any] = {}

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=GLOBAL_SSL_CONTEXT)) as session:
            tasks = [
                self.spider_js_secrets(session, target),
                self.vuln_scan_misconfig(session, target)
            ]
            res = await asyncio.gather(*tasks, return_exceptions=True)
            
            results['js_secrets'] = res[0] if not isinstance(res[0], Exception) else []
            results['misconfigs'] = res[1] if not isinstance(res[1], Exception) else []
            results['cves'] = self.check_tech_cves(tech_results or {})

        log.info("vuln_scan_completed", target=target)
        return results

    async def fetch_url_async(self, session: aiohttp.ClientSession, url: str, timeout: int = 15) -> str | None:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) CyberGhost/8.0.0 GODMODE'}
        try:
            async with session.get(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    return await response.text()
        except Exception:
            pass
        return None

    async def spider_js_secrets(self, session: aiohttp.ClientSession, target: str) -> list[str]:
        secrets_found = []
        url = f"http://{target}" if not target.startswith('http') else target
        html = await self.fetch_url_async(session, url)
        if not html: 
            return ["Falha ao acessar o site para spidering."]
        
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')
        
        js_urls = []
        for s in scripts:
            src = s.get('src')
            if src:
                if src.startswith('http'): 
                    js_urls.append(src)
                elif src.startswith('/'): 
                    js_urls.append(f"http://{target}{src}")
                    
        patterns = {
            "Google API": r'AIza[0-9A-Za-z-_]{35}',
            "AWS Access Key": r'AKIA[0-9A-Z]{16}',
            "Stripe Standard": r'sk_live_[0-9a-zA-Z]{24}',
            "JWT Token": r'ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*',
            "Generic Bearer": r'Bearer\s+[A-Za-z0-9\-\._~+/]+'
        }
        
        async def analyze_js(js_url: str) -> list[str]:
            js_content = await self.fetch_url_async(session, js_url, timeout=5)
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
            
        if not secrets_found: 
            return ["[green]Nenhum segredo no Frontend JS.[/green]"]
        return list(set(secrets_found))

    async def vuln_scan_misconfig(self, session: aiohttp.ClientSession, target: str) -> list[str]:
        vulns = []
        paths = [
            ('/.git/config', 'Git Repository Exposto'), 
            ('/.env', 'Arquivo .env Exposto'), 
            ('/server-status', 'Apache Server Status'), 
            ('/actuator/env', 'Spring Boot Actuator Env')
        ]
        
        async def check_path(path: str, name: str) -> str | None:
            url = f"http://{target}{path}"
            try:
                async with session.get(url, timeout=3, allow_redirects=False) as resp:
                    if resp.status == 200 and 'html' not in resp.headers.get('Content-Type', '').lower():
                        return f"[red]CRÍTICO: {name} ({url})[/red]"
            except Exception:
                pass
            return None

        tasks = [check_path(p, n) for p, n in paths]
        res = await asyncio.gather(*tasks)
        vulns = [r for r in res if r]
        
        url = f"http://{target}"
        try:
            async with session.get(url, headers={'Origin': 'https://evil.com'}, timeout=3) as resp:
                if resp.headers.get('Access-Control-Allow-Origin') == 'https://evil.com':
                    vulns.append("[yellow]ALERTA: CORS Misconfiguration Permitindo Qualquer Origem[/yellow]")
        except Exception:
            pass
        
        if not vulns: 
            return ["[green]Nenhuma misconfiguration crítica detectada.[/green]"]
        return vulns

    def check_tech_cves(self, tech_results: dict[str, str]) -> list[str]:
        """Baseado nas tecnologias detectadas, emite alertas genéricos passivos."""
        if not tech_results: 
            return ["[dim]Nenhuma tecnologia específica para buscar CVEs.[/dim]"]
        
        alerts = []
        for k, v in tech_results.items():
            val = v.lower()
            if 'apache' in val and '2.4.49' in val:
                alerts.append(f"[bold red]ALERTA CVE: {v} é vulnerável a Path Traversal (CVE-2021-41773)[/bold red]")
            elif 'nginx/1.1' in val:
                alerts.append(f"[yellow]Aviso: Versões Nginx 1.1x podem ter exploits públicos.[/yellow]")
            elif 'php/5' in val or 'php/7.0' in val or 'php/7.1' in val or 'php/7.2' in val:
                 alerts.append(f"[bold red]ALERTA: {v} descontinuado e vulnerável![/bold red]")
                 
        if not alerts: 
            return ["[green]Nenhuma versão criticamente exposta detectada (Passivo).[/green]"]
        return alerts
