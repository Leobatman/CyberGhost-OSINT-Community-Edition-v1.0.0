import aiohttp
import asyncio
import socket
from typing import List
from core.models import OsintResult
from core.http_client import fetch_url

async def scan_whois(session: aiohttp.ClientSession, target: str) -> OsintResult:
    """RDAP/WHOIS lookup."""
    url = f"https://rdap.org/domain/{target}"
    data = await fetch_url(session, url, timeout=10, as_json=True)
    if not data:
        return OsintResult(
            source="RDAP", category="Network", target=target,
            status="failed", data={}, errors=["Failed to fetch RDAP data"]
        )

    info = {'handle': data.get('handle', 'N/A')}
    for ent in data.get('entities', []):
        roles = ", ".join(ent.get('roles', []))
        if 'vcardArray' in ent:
            vcard = ent['vcardArray'][1]
            for prop in vcard:
                if prop[0] == 'fn':
                    info[roles.capitalize()] = prop[3]
                    
    return OsintResult(
        source="RDAP", category="Network", target=target,
        status="success", data=info
    )

async def scan_ip_reputation(target: str) -> OsintResult:
    """Check IP against DNS blacklists."""
    try:
        ip = await asyncio.to_thread(socket.gethostbyname, target)
    except socket.gaierror:
        return OsintResult(
            source="DNSBL", category="Reputation", target=target,
            status="failed", data={}, errors=["Could not resolve IP"]
        )

    reverse_ip = ".".join(reversed(ip.split(".")))
    results = {}
    for bl in ["zen.spamhaus.org", "b.barracudacentral.org", "bl.spamcop.net"]:
        try:
            await asyncio.to_thread(socket.gethostbyname, f"{reverse_ip}.{bl}")
            results[bl] = "LISTED"
        except socket.gaierror:
            results[bl] = "CLEAN"
            
    return OsintResult(
        source="DNSBL", category="Reputation", target=target,
        status="success", data=results
    )

async def scan_ports(target: str) -> OsintResult:
    """Async port scan on common ports."""
    ports = [21, 22, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 5432, 8080, 8443]
    port_map = {
        21: "FTP", 22: "SSH", 25: "SMTP", 53: "DNS", 80: "HTTP",
        110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
        3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
        8080: "HTTP-Alt", 8443: "HTTPS-Alt"
    }

    try:
        ip = await asyncio.to_thread(socket.gethostbyname, target)
    except socket.gaierror:
        return OsintResult(
            source="Port Scan", category="Network", target=target,
            status="failed", data={}, errors=["Could not resolve IP"]
        )

    async def check_port(port: int) -> str | None:
        try:
            conn = asyncio.open_connection(ip, port)
            reader, writer = await asyncio.wait_for(conn, timeout=2)
            writer.close()
            await writer.wait_closed()
            return f"{port}/{port_map.get(port, 'Unknown')}"
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return None

    sem = asyncio.Semaphore(10)

    async def limited_check(port: int):
        async with sem:
            return await check_port(port)

    results = await asyncio.gather(*[limited_check(p) for p in ports])
    open_ports = [r for r in results if r]
    
    return OsintResult(
        source="Port Scan", category="Network", target=target,
        status="success", data={"open_ports": open_ports}
    )

async def run_network_module(target: str) -> List[OsintResult]:
    """Run all network intelligence checks."""
    connector = aiohttp.TCPConnector(ssl=True, limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        results = await asyncio.gather(
            scan_whois(session, target),
            scan_ip_reputation(target),
            scan_ports(target),
            return_exceptions=True
        )
        
        final_results = []
        for r in results:
            if isinstance(r, Exception):
                final_results.append(OsintResult(
                    source="Network Module", category="Network", target=target,
                    status="failed", data={}, errors=[str(r)]
                ))
            else:
                final_results.append(r)
                
        return final_results
