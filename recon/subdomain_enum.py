"""
CyberGhost OSINT Enterprise — Subdomain Enumeration & Takeover
"""
from __future__ import annotations

import asyncio
import ssl
from typing import Any

import aiohttp
import structlog

log = structlog.get_logger(__name__)

GLOBAL_SSL_CONTEXT = ssl.create_default_context()

class SubdomainEnumerator:
    """Enumerate subdomains and check for possible takeovers."""
    
    def __init__(self) -> None:
        self.signatures = {
            'github': 'There isn\'t a GitHub Pages site here.',
            'heroku': 'No such app',
            'aws_s3': 'The specified bucket does not exist',
            'azure': '404 Web Site not found'
        }

    async def enumerate(self, target: str) -> dict[str, Any]:
        """Runs subdomain enumeration and takeover checks."""
        log.info("subdomain_enum_started", target=target)
        results: dict[str, Any] = {}

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=GLOBAL_SSL_CONTEXT)) as session:
            # 1. Enumerate Subdomains
            subdomains = await self.get_subdomains(session, target)
            results['subdomains'] = subdomains
            
            # 2. Check for Takeovers
            takeovers = await self.check_subdomain_takeover(session, subdomains)
            results['takeovers'] = takeovers

        log.info("subdomain_enum_completed", target=target, count=len(subdomains))
        return results

    async def get_subdomains(self, session: aiohttp.ClientSession, target: str) -> list[str]:
        """Fetch subdomains from crt.sh."""
        url = f"https://crt.sh/?q=%25.{target}&output=json"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) CyberGhost/8.0.0 GODMODE'}
        
        try:
            async with session.get(url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    subs = set()
                    if isinstance(data, list):
                        for cert in data:
                            name = cert.get('name_value', '')
                            for n in name.split('\n'):
                                if n.endswith(target) and '*' not in n: 
                                    subs.add(n)
                    return list(subs)[:100]
        except Exception as e:
            log.debug("subdomain_enum_failed", error=str(e))
        return []

    async def check_subdomain_takeover(self, session: aiohttp.ClientSession, subdomains: list[str]) -> list[str]:
        """Check a list of subdomains for known takeover signatures."""
        findings = []
        
        async def check_sub(sub: str) -> str | None:
            try:
                url = f"http://{sub}"
                async with session.get(url, timeout=4) as resp:
                    text = await resp.text()
                    for provider, sig in self.signatures.items():
                        if sig in text:
                            return f"[red]ALERTA: Possível Takeover em {sub} ({provider})[/red]"
            except Exception:
                pass
            return None

        tasks = [check_sub(sub) for sub in subdomains[:30]]
        results = await asyncio.gather(*tasks)
        
        for r in results:
            if r: 
                findings.append(r)
            
        if not findings: 
            return ["[green]Nenhum subdomain takeover detectado nas amostras.[/green]"]
        return findings
