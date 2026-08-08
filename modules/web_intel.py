import aiohttp
import re
from typing import List
from core.models import OsintResult
from core.http_client import fetch_url

async def scan_security_headers(session: aiohttp.ClientSession, target: str) -> OsintResult:
    """Check HTTP security headers."""
    url = f"https://{target}"
    findings = []
    headers_to_check = {'User-Agent': 'CyberGhost OSINT (Community Edition) - Research Tool'}

    status = "success"
    try:
        async with session.head(url, headers=headers_to_check, timeout=aiohttp.ClientTimeout(total=5), allow_redirects=True) as resp:
            hdrs = resp.headers
            if not hdrs.get('Strict-Transport-Security'):
                findings.append("Missing: Strict-Transport-Security (HSTS)")
            if not hdrs.get('Content-Security-Policy'):
                findings.append("Missing: Content-Security-Policy (CSP)")
            if not hdrs.get('X-Frame-Options'):
                findings.append("Missing: X-Frame-Options (Clickjacking)")
            if not hdrs.get('X-Content-Type-Options'):
                findings.append("Missing: X-Content-Type-Options")

            server = hdrs.get('Server', '')
            if server:
                findings.append(f"Server: {server}")
            powered = hdrs.get('X-Powered-By', '')
            if powered:
                findings.append(f"X-Powered-By: {powered}")
    except Exception as e:
        return OsintResult(
            source="Security Headers", category="Web", target=target,
            status="failed", data={}, errors=[f"Could not check HTTPS headers: {e}"]
        )

    # Try HTTP too
    try:
        async with session.head(f"http://{target}", headers=headers_to_check, timeout=aiohttp.ClientTimeout(total=5), allow_redirects=False) as resp:
            if resp.status not in [301, 302, 308]:
                findings.append("WARNING: HTTP does not redirect to HTTPS")
    except Exception:
        pass

    return OsintResult(
        source="Security Headers", category="Web", target=target,
        status=status, data={"findings": findings if findings else ["All major security headers present"]}
    )

async def scan_robots(session: aiohttp.ClientSession, target: str) -> OsintResult:
    """Check robots.txt for hidden paths."""
    findings = []
    url = f"https://{target}/robots.txt"
    text = await fetch_url(session, url, timeout=5)

    if text and '<html' not in text.lower():
        disallowed = re.findall(r'Disallow:\s*(/\S+)', text)
        if disallowed:
            unique = list(set(disallowed))[:10]
            findings.extend(unique)
    else:
        text_http = await fetch_url(session, f"http://{target}/robots.txt", timeout=5)
        if text_http and '<html' not in text_http.lower():
            disallowed = re.findall(r'Disallow:\s*(/\S+)', text_http)
            if disallowed:
                unique = list(set(disallowed))[:10]
                findings.extend(unique)

    return OsintResult(
        source="robots.txt", category="Web", target=target,
        status="success", data={"disallowed_paths": findings}
    )

async def scan_emails(session: aiohttp.ClientSession, target: str) -> OsintResult:
    """Scrape homepage for exposed email addresses."""
    url = f"https://{target}"
    html = await fetch_url(session, url, timeout=10)
    if not html:
        html = await fetch_url(session, f"http://{target}", timeout=10)
    
    if not html:
        return OsintResult(
            source="Email Harvester", category="Web", target=target,
            status="failed", data={}, errors=["Could not fetch homepage"]
        )

    emails = re.findall(r'[a-zA-Z0-9.\-+_]+@[a-zA-Z0-9.\-+_]+\.[a-zA-Z]+', html)
    emails = list(set([e for e in emails if not e.startswith('u00') and '@' in e]))
    
    return OsintResult(
        source="Email Harvester", category="Web", target=target,
        status="success", data={"emails": emails[:10] if emails else []}
    )

async def generate_dorks(target: str) -> OsintResult:
    """Generate Google dorks for passive breach intel."""
    dorks = [
        f'site:pastebin.com "{target}"',
        f'site:trello.com "{target}"',
        f'"@{target}" ext:txt | ext:csv | ext:sql',
        f'site:github.com "{target}" "password" | "secret"',
    ]
    return OsintResult(
        source="Google Dorks", category="Intelligence", target=target,
        status="success", data={"dorks": dorks}
    )

async def run_web_module(target: str) -> List[OsintResult]:
    """Run all web intelligence checks."""
    connector = aiohttp.TCPConnector(ssl=True, limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        results = await asyncio.gather(
            scan_security_headers(session, target),
            scan_robots(session, target),
            scan_emails(session, target),
            generate_dorks(target),
            return_exceptions=True
        )
        
        final_results = []
        for r in results:
            if isinstance(r, Exception):
                final_results.append(OsintResult(
                    source="Web Module", category="Web", target=target,
                    status="failed", data={}, errors=[str(r)]
                ))
            else:
                final_results.append(r)
                
        return final_results
