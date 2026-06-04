"""
CyberGhost OSINT Enterprise — Certificate Transparency
crt.sh + certstream + Censys integration
One of the most powerful OSINT sources — was completely absent before
"""
from __future__ import annotations

import asyncio
import re
from datetime import datetime
from typing import Any

import aiohttp
import structlog
from aiohttp import ClientTimeout

log = structlog.get_logger(__name__)


class CertificateTransparency:
    """
    Query Certificate Transparency logs via crt.sh and Censys.
    Finds subdomains, email addresses, and historical infrastructure.
    """

    TIMEOUT = ClientTimeout(total=30)
    CRT_SH_URL = "https://crt.sh/"

    async def lookup(self, domain: str) -> dict[str, Any]:
        """
        Look up all certificates for a domain in CT logs.
        Returns subdomains, email addresses, and certificate metadata.
        """
        log.info("cert_transparency_started", domain=domain)

        async with aiohttp.ClientSession(timeout=self.TIMEOUT) as session:
            results = await asyncio.gather(
                self._query_crt_sh(session, domain),
                self._query_crt_sh(session, f"%.{domain}"),  # All subdomains
                return_exceptions=True,
            )

        main_certs = results[0] if not isinstance(results[0], Exception) else []
        sub_certs = results[1] if not isinstance(results[1], Exception) else []

        all_certs = main_certs + sub_certs

        # Deduplicate and extract
        subdomains = self._extract_subdomains(all_certs, domain)
        emails = self._extract_emails(all_certs)
        orgs = self._extract_organizations(all_certs)
        cert_summary = self._summarize_certs(all_certs)

        log.info(
            "cert_transparency_completed",
            domain=domain,
            total_certs=len(all_certs),
            subdomains=len(subdomains),
        )

        return {
            "domain": domain,
            "total_certificates": len(all_certs),
            "subdomains": sorted(subdomains),
            "email_addresses": sorted(emails),
            "organizations": sorted(orgs),
            "certificate_summary": cert_summary,
            "certificates": all_certs[:50],  # Top 50
        }

    async def _query_crt_sh(
        self, session: aiohttp.ClientSession, query: str
    ) -> list[dict[str, Any]]:
        """Query crt.sh for certificate transparency data."""
        params = {
            "q": query,
            "output": "json",
            "deduplicate": "Y",
        }
        headers = {"User-Agent": "CyberGhost-OSINT/8.0 (Security Research)"}

        try:
            async with session.get(
                self.CRT_SH_URL, params=params, headers=headers
            ) as resp:
                if resp.status != 200:
                    log.warning("crt_sh_error", status=resp.status, query=query)
                    return []

                data = await resp.json(content_type=None)
                if not isinstance(data, list):
                    return []

                return [
                    {
                        "id": cert.get("id"),
                        "logged_at": cert.get("entry_timestamp"),
                        "not_before": cert.get("not_before"),
                        "not_after": cert.get("not_after"),
                        "common_name": cert.get("common_name", ""),
                        "name_value": cert.get("name_value", ""),
                        "issuer_name": cert.get("issuer_name", ""),
                    }
                    for cert in data
                ]
        except Exception as e:
            log.warning("crt_sh_request_failed", error=str(e), query=query)
            return []

    def _extract_subdomains(
        self, certs: list[dict[str, Any]], base_domain: str
    ) -> set[str]:
        """Extract all unique subdomains from certificate data."""
        subdomains: set[str] = set()
        domain_pattern = re.compile(
            rf"([a-zA-Z0-9*._-]+\.{re.escape(base_domain)})", re.IGNORECASE
        )

        for cert in certs:
            # Check common_name
            cn = cert.get("common_name", "")
            for match in domain_pattern.findall(cn):
                clean = match.lower().lstrip("*.")
                if clean and clean != base_domain:
                    subdomains.add(clean)

            # Check name_value (SANs)
            name_value = cert.get("name_value", "")
            for name in name_value.split("\n"):
                name = name.strip().lower().lstrip("*.")
                for match in domain_pattern.findall(name):
                    clean = match.lower().lstrip("*.")
                    if clean and clean != base_domain:
                        subdomains.add(clean)

        return subdomains

    def _extract_emails(self, certs: list[dict[str, Any]]) -> set[str]:
        """Extract email addresses found in certificates."""
        emails: set[str] = set()
        email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

        for cert in certs:
            text = f"{cert.get('common_name', '')} {cert.get('name_value', '')} {cert.get('issuer_name', '')}"
            for email in email_pattern.findall(text):
                emails.add(email.lower())

        return emails

    def _extract_organizations(self, certs: list[dict[str, Any]]) -> set[str]:
        """Extract organization names from issuer data."""
        orgs: set[str] = set()
        org_pattern = re.compile(r"O=([^,]+)")

        for cert in certs:
            issuer = cert.get("issuer_name", "")
            for match in org_pattern.findall(issuer):
                org = match.strip().strip('"')
                if org and len(org) > 2:
                    orgs.add(org)

        return orgs

    def _summarize_certs(self, certs: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate summary statistics from certificates."""
        if not certs:
            return {}

        issuers: dict[str, int] = {}
        for cert in certs:
            issuer = cert.get("issuer_name", "Unknown")
            # Extract O= value
            match = re.search(r"O=([^,]+)", issuer)
            org = match.group(1).strip() if match else "Unknown"
            issuers[org] = issuers.get(org, 0) + 1

        return {
            "total": len(certs),
            "top_issuers": sorted(issuers.items(), key=lambda x: x[1], reverse=True)[:10],
        }
