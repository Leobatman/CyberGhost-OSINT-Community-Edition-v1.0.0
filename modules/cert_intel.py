import aiohttp
from typing import List
from core.models import OsintResult
from core.http_client import fetch_url

async def scan_certs(session: aiohttp.ClientSession, target: str) -> OsintResult:
    """Query crt.sh for certificate transparency data."""
    url = f"https://crt.sh/?q=%25.{target}&output=json"
    data = await fetch_url(session, url, timeout=20, as_json=True)
    
    if data is None:
        return OsintResult(
            source="crt.sh",
            category="Certificates",
            target=target,
            status="warning",
            data={},
            errors=["source timeout (crt.sh) or API unavailable"]
        )
        
    if not isinstance(data, list) or not data:
        return OsintResult(
            source="crt.sh",
            category="Certificates",
            target=target,
            status="success",
            data={"certificates": []}
        )

    seen = set()
    certs = []
    subdomains = set()
    
    for cert in data:
        name = cert.get('name_value', '').replace('\n', ', ')
        if name and name not in seen:
            seen.add(name)
            certs.append(name)
        
        # Extract subdomains while we are at it
        for n in name.split(', '):
            n = n.strip().lower().lstrip('*.')
            if n.endswith(target) and n != target and '*' not in n:
                subdomains.add(n)
                
        if len(certs) >= 50:
            break
            
    return OsintResult(
        source="crt.sh",
        category="Certificates",
        target=target,
        status="success",
        data={
            "certificates": certs,
            "subdomains_discovered": sorted(list(subdomains))[:50]
        }
    )

async def run_cert_module(target: str) -> List[OsintResult]:
    """Run certificate intelligence module."""
    connector = aiohttp.TCPConnector(ssl=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        result = await scan_certs(session, target)
        return [result]
