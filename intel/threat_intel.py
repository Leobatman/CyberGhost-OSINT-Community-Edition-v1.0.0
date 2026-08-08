"""
CyberGhost OSINT Enterprise — Threat Intelligence Engine
Parallel API calls with aiohttp — replaces sequential bash curl loops
Before: 10 APIs × ~2s each = ~20s sequential
After:  10 APIs in parallel = ~2s total
"""
from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import re
from typing import Any

import aiohttp
import structlog
from aiohttp import ClientTimeout

from backend.core.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

log = structlog.get_logger(__name__)

# ── IOC Type Detection ────────────────────────────────────────────────────────

_IP_RE = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
_DOMAIN_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)
_EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
_URL_RE = re.compile(r"^https?://")
_MD5_RE = re.compile(r"^[a-fA-F0-9]{32}$")
_SHA1_RE = re.compile(r"^[a-fA-F0-9]{40}$")
_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")


def detect_ioc_type(target: str) -> str:
    """Detect IOC type from target string."""
    target = target.strip().lower()
    if _IP_RE.match(target):
        try:
            ipaddress.ip_address(target)
            return "ip"
        except ValueError:
            pass
    if _EMAIL_RE.match(target):
        return "email"
    if _URL_RE.match(target):
        return "url"
    if _MD5_RE.match(target):
        return "hash_md5"
    if _SHA1_RE.match(target):
        return "hash_sha1"
    if _SHA256_RE.match(target):
        return "hash_sha256"
    if _DOMAIN_RE.match(target):
        return "domain"
    return "unknown"


# ── Threat Intelligence Engine ────────────────────────────────────────────────


class ThreatIntelligence:
    """
    Aggregates threat intelligence from multiple sources in parallel.
    All API calls use aiohttp with timeouts and error isolation.
    """

    TIMEOUT = ClientTimeout(total=15, connect=5)

    def __init__(self) -> None:
        self.api_keys = settings.api_keys

    async def enrich(self, target: str) -> dict[str, Any]:
        """
        Enrich a target with threat intelligence from all available sources.
        Sources run in parallel — total time ≈ slowest single API call.
        """
        ioc_type = detect_ioc_type(target)
        log.info("threat_intel_started", target=target, ioc_type=ioc_type)

        async with aiohttp.ClientSession(timeout=self.TIMEOUT) as session:
            # Build task list based on IOC type and available API keys
            tasks: dict[str, Any] = {}

            if self.api_keys.virustotal:
                tasks["virustotal"] = self._check_virustotal(session, target, ioc_type)

            if self.api_keys.abuseipdb and ioc_type == "ip":
                tasks["abuseipdb"] = self._check_abuseipdb(session, target)

            if self.api_keys.greynoise and ioc_type == "ip":
                tasks["greynoise"] = self._check_greynoise(session, target)

            # AlienVault OTX — free tier (no key required for basic)
            tasks["alienvault"] = self._check_alienvault(session, target, ioc_type)

            if self.api_keys.shodan and ioc_type == "ip":
                tasks["shodan"] = self._check_shodan(session, target)

            if ioc_type in ("url",):
                tasks["urlhaus"] = self._check_urlhaus(session, target)

            tasks["threatminer"] = self._check_threatminer(session, target, ioc_type)

            if self.api_keys.ibm_xforce_key:
                tasks["ibm_xforce"] = self._check_ibm_xforce(session, target, ioc_type)

            # Execute ALL in parallel
            names = list(tasks.keys())
            coroutines = list(tasks.values())

            raw_results = await asyncio.gather(*coroutines, return_exceptions=True)

            results: dict[str, Any] = {
                "target": target,
                "ioc_type": ioc_type,
            }

            for name, result in zip(names, raw_results):
                if isinstance(result, Exception):
                    log.warning("threat_intel_source_failed", source=name, error=str(result))
                    results[name] = {"error": str(result), "available": False}
                else:
                    results[name] = result

        # Calculate composite reputation score
        results["reputation"] = self._calculate_reputation(results)
        results["malicious"] = results["reputation"]["score"] >= 70

        log.info(
            "threat_intel_completed",
            target=target,
            sources=len(tasks),
            malicious=results["malicious"],
            score=results["reputation"]["score"],
        )
        return results

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=60), retry=retry_if_exception_type(aiohttp.ClientError))
    async def _check_virustotal(
        self, session: aiohttp.ClientSession, target: str, ioc_type: str
    ) -> dict[str, Any]:
        """Query VirusTotal API v3."""
        if not self.api_keys.virustotal:
            return {"available": False}

        endpoint_map = {
            "ip": "ip_addresses",
            "domain": "domains",
            "url": "urls",
            "hash_md5": "files",
            "hash_sha1": "files",
            "hash_sha256": "files",
        }
        endpoint = endpoint_map.get(ioc_type)
        if not endpoint:
            return {"available": False, "reason": "unsupported_ioc_type"}

        # For URLs, use ID (base64 encoded)
        lookup_target = target
        if ioc_type == "url":
            import base64
            lookup_target = base64.urlsafe_b64encode(target.encode()).decode().rstrip("=")

        url = f"https://www.virustotal.com/api/v3/{endpoint}/{lookup_target}"
        headers = {"x-apikey": self.api_keys.virustotal.get_secret_value()}

        async with session.get(url, headers=headers) as resp:
            if resp.status == 404:
                return {"available": True, "found": False}
            if resp.status != 200:
                return {"available": True, "error": f"HTTP {resp.status}"}

            data = await resp.json()
            attrs = data.get("data", {}).get("attributes", {})
            stats = attrs.get("last_analysis_stats", {})

            return {
                "available": True,
                "found": True,
                "malicious": stats.get("malicious", 0),
                "suspicious": stats.get("suspicious", 0),
                "harmless": stats.get("harmless", 0),
                "undetected": stats.get("undetected", 0),
                "total": sum(stats.values()),
                "reputation": attrs.get("reputation", 0),
                "last_analysis": attrs.get("last_analysis_date"),
                "community_score": attrs.get("total_votes", {}).get("malicious", 0),
            }

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=60), retry=retry_if_exception_type(aiohttp.ClientError))
    async def _check_abuseipdb(
        self, session: aiohttp.ClientSession, ip: str
    ) -> dict[str, Any]:
        """Query AbuseIPDB API v2."""
        if not self.api_keys.abuseipdb:
            return {"available": False}

        url = "https://api.abuseipdb.com/api/v2/check"
        headers = {
            "Key": self.api_keys.abuseipdb.get_secret_value(),
            "Accept": "application/json",
        }
        params = {"ipAddress": ip, "maxAgeInDays": 90, "verbose": "true"}

        async with session.get(url, headers=headers, params=params) as resp:
            if resp.status != 200:
                return {"available": True, "error": f"HTTP {resp.status}"}

            data = await resp.json()
            d = data.get("data", {})
            return {
                "available": True,
                "abuse_score": d.get("abuseConfidenceScore", 0),
                "total_reports": d.get("totalReports", 0),
                "country": d.get("countryCode"),
                "isp": d.get("isp"),
                "domain": d.get("domain"),
                "last_reported": d.get("lastReportedAt"),
                "is_public": d.get("isPublic", True),
                "is_tor": d.get("isTor", False),
            }

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=60), retry=retry_if_exception_type(aiohttp.ClientError))
    async def _check_greynoise(
        self, session: aiohttp.ClientSession, ip: str
    ) -> dict[str, Any]:
        """Query GreyNoise API v3."""
        if not self.api_keys.greynoise:
            return {"available": False}

        url = f"https://api.greynoise.io/v3/community/{ip}"
        headers = {"key": self.api_keys.greynoise.get_secret_value()}

        async with session.get(url, headers=headers) as resp:
            if resp.status == 404:
                return {"available": True, "found": False}
            if resp.status != 200:
                return {"available": True, "error": f"HTTP {resp.status}"}

            data = await resp.json()
            return {
                "available": True,
                "found": True,
                "noise": data.get("noise", False),
                "riot": data.get("riot", False),
                "classification": data.get("classification", "unknown"),
                "name": data.get("name"),
                "last_seen": data.get("last_seen"),
                "message": data.get("message"),
            }

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=60), retry=retry_if_exception_type(aiohttp.ClientError))
    async def _check_alienvault(
        self, session: aiohttp.ClientSession, target: str, ioc_type: str
    ) -> dict[str, Any]:
        """Query AlienVault OTX — free tier."""
        endpoint_map = {
            "ip": f"IPv4/{target}/general",
            "domain": f"domain/{target}/general",
            "hash_md5": f"file/{target}/general",
            "hash_sha1": f"file/{target}/general",
            "hash_sha256": f"file/{target}/general",
            "url": f"url/{target}/general",
        }
        path = endpoint_map.get(ioc_type)
        if not path:
            return {"available": False}

        headers: dict[str, str] = {}
        if self.api_keys.alienvault_otx:
            headers["X-OTX-API-KEY"] = self.api_keys.alienvault_otx.get_secret_value()

        url = f"https://otx.alienvault.com/api/v1/indicators/{path}"

        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return {"available": True, "error": f"HTTP {resp.status}"}

            data = await resp.json()
            pulse_info = data.get("pulse_info", {})
            return {
                "available": True,
                "pulse_count": pulse_info.get("count", 0),
                "pulses": [
                    {"name": p.get("name"), "tags": p.get("tags", [])}
                    for p in pulse_info.get("pulses", [])[:5]  # Top 5 pulses
                ],
                "malware_families": data.get("malware_families", []),
            }

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=60), retry=retry_if_exception_type(aiohttp.ClientError))
    async def _check_shodan(
        self, session: aiohttp.ClientSession, ip: str
    ) -> dict[str, Any]:
        """Query Shodan API."""
        if not self.api_keys.shodan:
            return {"available": False}

        url = f"https://api.shodan.io/shodan/host/{ip}"
        params = {"key": self.api_keys.shodan.get_secret_value()}

        async with session.get(url, params=params) as resp:
            if resp.status == 404:
                return {"available": True, "found": False}
            if resp.status != 200:
                return {"available": True, "error": f"HTTP {resp.status}"}

            data = await resp.json()
            return {
                "available": True,
                "found": True,
                "ports": data.get("ports", []),
                "vulnerabilities": list(data.get("vulns", {}).keys()),
                "hostnames": data.get("hostnames", []),
                "org": data.get("org"),
                "os": data.get("os"),
                "country": data.get("country_name"),
                "city": data.get("city"),
                "isp": data.get("isp"),
                "asn": data.get("asn"),
                "services": [
                    {"port": s.get("port"), "product": s.get("product"), "version": s.get("version")}
                    for s in data.get("data", [])[:10]  # Top 10 services
                ],
            }

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=60), retry=retry_if_exception_type(aiohttp.ClientError))
    async def _check_urlhaus(
        self, session: aiohttp.ClientSession, url: str
    ) -> dict[str, Any]:
        """Query URLhaus (abuse.ch)."""
        api_url = "https://urlhaus-api.abuse.ch/v1/url/"
        data = {"url": url}

        async with session.post(api_url, data=data) as resp:
            if resp.status != 200:
                return {"available": True, "error": f"HTTP {resp.status}"}

            result = await resp.json()
            if result.get("query_status") == "no_results":
                return {"available": True, "found": False}

            return {
                "available": True,
                "found": True,
                "url_status": result.get("url_status"),
                "threat": result.get("threat"),
                "tags": result.get("tags", []),
                "date_added": result.get("date_added"),
                "blacklists": result.get("blacklists", {}),
            }

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=60), retry=retry_if_exception_type(aiohttp.ClientError))
    async def _check_threatminer(
        self, session: aiohttp.ClientSession, target: str, ioc_type: str
    ) -> dict[str, Any]:
        """Query ThreatMiner."""
        endpoint_map = {"ip": "host", "domain": "domain"}
        endpoint = endpoint_map.get(ioc_type)
        if not endpoint:
            return {"available": False}

        url = f"https://api.threatminer.org/v2/{endpoint}.php"
        params = {"q": target, "rt": "2"}

        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                return {"available": True, "error": f"HTTP {resp.status}"}

            data = await resp.json()
            if data.get("status_code") != "200":
                return {"available": True, "found": False}

            return {
                "available": True,
                "found": True,
                "results": data.get("results", [])[:10],
            }

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=60), retry=retry_if_exception_type(aiohttp.ClientError))
    async def _check_ibm_xforce(
        self, session: aiohttp.ClientSession, target: str, ioc_type: str
    ) -> dict[str, Any]:
        """Query IBM X-Force Exchange."""
        if not self.api_keys.ibm_xforce_key or not self.api_keys.ibm_xforce_pass:
            return {"available": False}

        import base64
        creds = base64.b64encode(
            f"{self.api_keys.ibm_xforce_key.get_secret_value()}:{self.api_keys.ibm_xforce_pass.get_secret_value()}".encode()
        ).decode()
        headers = {
            "Authorization": f"Basic {creds}",
            "Accept": "application/json",
        }

        endpoint_map = {"ip": "ipr", "domain": "url", "hash_md5": "malware", "hash_sha256": "malware"}
        endpoint = endpoint_map.get(ioc_type)
        if not endpoint:
            return {"available": False}

        url = f"https://api.xforce.ibmcloud.com/{endpoint}/{target}"

        async with session.get(url, headers=headers) as resp:
            if resp.status == 404:
                return {"available": True, "found": False}
            if resp.status != 200:
                return {"available": True, "error": f"HTTP {resp.status}"}

            data = await resp.json()
            return {
                "available": True,
                "found": True,
                "score": data.get("score", 0),
                "categories": list(data.get("cats", {}).keys()),
                "family": data.get("family", [{}])[0].get("name") if data.get("family") else None,
            }

    def _calculate_reputation(self, results: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate composite reputation score (0-100).
        Higher = more malicious.
        Weighted average across available sources.
        """
        scores: list[float] = []
        weights: list[float] = []

        # VirusTotal (weight: 40%)
        vt = results.get("virustotal", {})
        if vt.get("available") and vt.get("found"):
            total = vt.get("total", 1) or 1
            malicious = vt.get("malicious", 0)
            scores.append((malicious / total) * 100)
            weights.append(40)

        # AbuseIPDB (weight: 25%)
        abuse = results.get("abuseipdb", {})
        if abuse.get("available") and "abuse_score" in abuse:
            scores.append(abuse["abuse_score"])
            weights.append(25)

        # GreyNoise (weight: 20%)
        gn = results.get("greynoise", {})
        if gn.get("available") and gn.get("found"):
            gn_score = 80 if gn.get("classification") == "malicious" else 0
            gn_score = max(gn_score, 30 if gn.get("noise") else 0)
            scores.append(gn_score)
            weights.append(20)

        # AlienVault (weight: 10%)
        otx = results.get("alienvault", {})
        if otx.get("available"):
            pulse_count = otx.get("pulse_count", 0)
            otx_score = min(pulse_count * 10, 100)
            scores.append(otx_score)
            weights.append(10)

        # Shodan vulnerabilities (bonus weight: 5%)
        shodan = results.get("shodan", {})
        if shodan.get("available") and shodan.get("found"):
            vuln_count = len(shodan.get("vulnerabilities", []))
            vuln_score = min(vuln_count * 20, 100)
            scores.append(vuln_score)
            weights.append(5)

        if not scores:
            return {"score": 0, "risk_level": "unknown", "confidence": 0}

        total_weight = sum(weights)
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
        score = round(weighted_score)

        if score >= 75:
            risk_level = "critical"
        elif score >= 50:
            risk_level = "high"
        elif score >= 25:
            risk_level = "medium"
        elif score > 0:
            risk_level = "low"
        else:
            risk_level = "clean"

        confidence = min(int((len(scores) / 5) * 100), 100)

        return {
            "score": score,
            "risk_level": risk_level,
            "confidence": confidence,
            "sources_used": len(scores),
        }

