"""
CyberGhost OSINT Enterprise — DNS Intelligence
"""
from __future__ import annotations

import asyncio
import socket
from typing import Any

import dns.resolver
import structlog

log = structlog.get_logger(__name__)


class DNSIntelligence:
    """DNS enumeration and security posture (SPF, DMARC) class."""

    async def analyze(self, target: str) -> dict[str, Any]:
        """Runs full DNS intelligence on the target."""
        log.info("dns_intel_started", target=target)
        results = {}

        # Basic A / AAAA resolution
        try:
            ip = await asyncio.to_thread(socket.gethostbyname, target)
            results['A'] = ip
            try:
                addrinfo = await asyncio.to_thread(socket.getaddrinfo, target, None, socket.AF_INET6)
                results['AAAA'] = addrinfo[0][4][0]
            except Exception:
                pass
        except Exception as e:
            log.debug("dns_resolution_failed", target=target, error=str(e))

        # Security Posture (SPF, DMARC)
        results['security'] = await self.check_dns_sec(target)

        log.info("dns_intel_completed", target=target)
        return results

    async def check_dns_sec(self, target: str) -> list[str]:
        """Check SPF and DMARC records asynchronously via threads."""
        results = []
        
        # SPF
        try:
            answers = await asyncio.to_thread(dns.resolver.resolve, target, 'TXT')
            spf = [r.to_text() for r in answers if 'v=spf1' in r.to_text().lower()]
            if spf: 
                results.append(f"[green]SPF Configurado:[/green] {spf[0][:50]}...")
            else: 
                results.append("[red]ALERTA: Registro SPF ausente (Risco de Spoofing)[/red]")
        except Exception:
            results.append("[red]ALERTA: Falha ao obter SPF[/red]")
            
        # DMARC
        try:
            answers = await asyncio.to_thread(dns.resolver.resolve, f"_dmarc.{target}", 'TXT')
            dmarc = [r.to_text() for r in answers if 'v=dmarc1' in r.to_text().lower()]
            if dmarc: 
                results.append(f"[green]DMARC Configurado:[/green] {dmarc[0][:50]}...")
            else: 
                results.append("[red]ALERTA: Registro DMARC ausente[/red]")
        except Exception:
            results.append("[red]ALERTA: Falha ao obter DMARC[/red]")
            
        return results
