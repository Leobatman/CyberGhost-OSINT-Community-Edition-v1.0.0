import asyncio
import socket
from typing import List
from core.models import OsintResult

async def check_dns_resolution(target: str) -> OsintResult:
    """Resolve A and AAAA records."""
    data = {}
    errors = []
    status = "success"
    
    try:
        ip = await asyncio.to_thread(socket.gethostbyname, target)
        data['A'] = ip
    except socket.gaierror as e:
        errors.append(f"Failed to resolve A record: {e}")
        status = "partial"

    try:
        addrinfo = await asyncio.to_thread(socket.getaddrinfo, target, None, socket.AF_INET6)
        data['AAAA'] = addrinfo[0][4][0]
    except (socket.gaierror, IndexError, OSError):
        pass

    if not data and errors:
        status = "failed"

    return OsintResult(
        source="Native DNS",
        category="Network",
        target=target,
        status=status,
        data=data,
        errors=errors
    )

async def check_dns_security(target: str) -> OsintResult:
    """Check SPF and DMARC records."""
    data = {}
    errors = []
    status = "success"

    try:
        import dns.resolver
        answers = await asyncio.to_thread(dns.resolver.resolve, target, 'TXT')
        spf = [r.to_text() for r in answers if 'v=spf1' in r.to_text().lower()]
        if spf:
            data['SPF'] = spf[0].strip('"')
        else:
            data['SPF'] = "Missing"
    except ImportError:
        errors.append("dnspython not installed")
        status = "partial"
    except Exception as e:
        data['SPF'] = "Missing or error"
        errors.append(f"SPF error: {e}")

    try:
        import dns.resolver
        answers = await asyncio.to_thread(dns.resolver.resolve, f"_dmarc.{target}", 'TXT')
        dmarc = [r.to_text() for r in answers if 'v=dmarc1' in r.to_text().lower()]
        if dmarc:
            data['DMARC'] = dmarc[0].strip('"')
        else:
            data['DMARC'] = "Missing"
    except ImportError:
        pass
    except Exception as e:
        data['DMARC'] = "Missing or error"
        errors.append(f"DMARC error: {e}")

    return OsintResult(
        source="DNS TXT",
        category="Security",
        target=target,
        status=status,
        data=data,
        errors=errors
    )

async def run_dns_module(target: str) -> List[OsintResult]:
    """Run all DNS intelligence checks."""
    results = await asyncio.gather(
        check_dns_resolution(target),
        check_dns_security(target),
        return_exceptions=True
    )
    
    final_results = []
    for r in results:
        if isinstance(r, Exception):
            final_results.append(OsintResult(
                source="DNS Module",
                category="Network",
                target=target,
                status="failed",
                data={},
                errors=[str(r)]
            ))
        else:
            final_results.append(r)
            
    return final_results
