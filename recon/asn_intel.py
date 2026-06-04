"""
CyberGhost OSINT Enterprise — ASN Intelligence
BGP routing + ASN ownership + IP range enumeration
"""
from __future__ import annotations

import asyncio
import ipaddress
from typing import Any

import aiohttp
import structlog
from aiohttp import ClientTimeout

log = structlog.get_logger(__name__)


class ASNIntelligence:
    """
    ASN (Autonomous System Number) intelligence.
    Identifies hosting provider, IP ranges, BGP routing, and abuse contacts.
    """

    TIMEOUT = ClientTimeout(total=15)

    async def lookup(self, target: str) -> dict[str, Any]:
        """
        Look up ASN information for an IP address or ASN number.
        """
        log.info("asn_lookup_started", target=target)

        async with aiohttp.ClientSession(timeout=self.TIMEOUT) as session:
            results = await asyncio.gather(
                self._query_bgp_tools(session, target),
                self._query_ipwhois(session, target),
                self._query_rdap(session, target),
                return_exceptions=True,
            )

        bgp_data = results[0] if not isinstance(results[0], Exception) else {}
        ipwhois_data = results[1] if not isinstance(results[1], Exception) else {}
        rdap_data = results[2] if not isinstance(results[2], Exception) else {}

        # Merge and deduplicate
        merged = self._merge_results(bgp_data, ipwhois_data, rdap_data)

        log.info("asn_lookup_completed", target=target, asn=merged.get("asn"))
        return merged

    async def _query_bgp_tools(
        self, session: aiohttp.ClientSession, target: str
    ) -> dict[str, Any]:
        """Query BGP.tools for routing information."""
        url = f"https://bgp.tools/query/{target}"
        headers = {"Accept": "application/json", "User-Agent": "CyberGhost-OSINT/8.0"}

        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return {}
                data = await resp.json(content_type=None)
                return {
                    "asn": data.get("asn"),
                    "as_name": data.get("as_name"),
                    "prefix": data.get("prefix"),
                    "country": data.get("country"),
                    "rir": data.get("rir"),
                }
        except Exception as e:
            log.debug("bgp_tools_failed", error=str(e))
            return {}

    async def _query_ipwhois(
        self, session: aiohttp.ClientSession, ip: str
    ) -> dict[str, Any]:
        """Query ipwho.is for IP/ASN data."""
        url = f"https://ipwho.is/{ip}"
        headers = {"User-Agent": "CyberGhost-OSINT/8.0"}

        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return {}
                data = await resp.json()
                if not data.get("success", True):
                    return {}

                connection = data.get("connection", {})
                return {
                    "asn": f"AS{connection.get('asn', '')}",
                    "as_name": connection.get("org", ""),
                    "isp": connection.get("isp", ""),
                    "country": data.get("country"),
                    "country_code": data.get("country_code"),
                    "region": data.get("region"),
                    "city": data.get("city"),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude"),
                    "timezone": data.get("timezone", {}).get("id"),
                    "is_eu": data.get("is_eu", False),
                }
        except Exception as e:
            log.debug("ipwhois_failed", error=str(e))
            return {}

    async def _query_rdap(
        self, session: aiohttp.ClientSession, target: str
    ) -> dict[str, Any]:
        """Query RDAP for detailed registration data."""
        try:
            # Try IP lookup first
            ipaddress.ip_address(target)
            url = f"https://rdap.arin.net/registry/ip/{target}"
        except ValueError:
            # Domain or ASN
            if target.upper().startswith("AS"):
                url = f"https://rdap.arin.net/registry/autnum/{target[2:]}"
            else:
                return {}

        headers = {
            "Accept": "application/rdap+json",
            "User-Agent": "CyberGhost-OSINT/8.0",
        }

        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return {}
                data = await resp.json(content_type=None)

                # Extract abuse contact
                abuse_contact = None
                for entity in data.get("entities", []):
                    roles = entity.get("roles", [])
                    if "abuse" in roles:
                        vcards = entity.get("vcardArray", [[], []])[1]
                        for vcard in vcards:
                            if vcard[0] == "email":
                                abuse_contact = vcard[3]
                                break

                return {
                    "name": data.get("name"),
                    "handle": data.get("handle"),
                    "ip_version": data.get("ipVersion"),
                    "start_address": data.get("startAddress"),
                    "end_address": data.get("endAddress"),
                    "prefix_length": data.get("cidr0_cidrs", [{}])[0].get("length"),
                    "abuse_contact": abuse_contact,
                    "registration_date": data.get("events", [{}])[0].get("eventDate"),
                    "rir": data.get("port43", "").split(".")[0].upper(),
                }
        except Exception as e:
            log.debug("rdap_failed", error=str(e))
            return {}

    def _merge_results(self, *results: dict[str, Any]) -> dict[str, Any]:
        """Merge results from multiple sources, preferring non-empty values."""
        merged: dict[str, Any] = {}
        for result in results:
            for key, value in result.items():
                if value and key not in merged:
                    merged[key] = value
        return merged
