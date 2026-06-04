"""
CyberGhost OSINT Enterprise — STIX 2.1 Models & Export
Full STIX 2.1 object creation and TAXII-compatible export
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import stix2
import structlog
from stix2 import (
    AttackPattern,
    Bundle,
    Campaign,
    DomainName,
    EmailAddress,
    File,
    Indicator,
    Infrastructure,
    IntrusionSet,
    IPv4Address,
    IPv6Address,
    Malware,
    ObservedData,
    Relationship,
    Report,
    ThreatActor,
    URL,
    Vulnerability,
)

from backend.models.models import IOC, IOCType, Severity

log = structlog.get_logger(__name__)

# ── TLP Markings ──────────────────────────────────────────────────────────────

TLP_WHITE = stix2.TLP_WHITE
TLP_GREEN = stix2.TLP_GREEN
TLP_AMBER = stix2.TLP_AMBER
TLP_RED = stix2.TLP_RED

TLP_MAP = {
    "WHITE": TLP_WHITE,
    "GREEN": TLP_GREEN,
    "AMBER": TLP_AMBER,
    "RED": TLP_RED,
}


# ── IOC → STIX Object Converter ───────────────────────────────────────────────


class STIXConverter:
    """Convert CyberGhost IOC objects to STIX 2.1 observable objects."""

    IDENTITY = stix2.Identity(
        name="CyberGhost OSINT Enterprise",
        identity_class="system",
        description="CyberGhost OSINT Enterprise Platform",
    )

    def ioc_to_stix_observable(self, ioc: IOC) -> dict[str, Any] | None:
        """Convert an IOC model to a STIX 2.1 observable object."""
        try:
            ioc_type = IOCType(ioc.ioc_type)
            tlp = TLP_MAP.get(ioc.tlp, TLP_AMBER)

            if ioc_type == IOCType.IP:
                observable = IPv4Address(
                    value=ioc.value,
                    object_marking_refs=[tlp],
                )
            elif ioc_type == IOCType.DOMAIN:
                observable = DomainName(
                    value=ioc.value,
                    object_marking_refs=[tlp],
                )
            elif ioc_type == IOCType.URL:
                observable = URL(
                    value=ioc.value,
                    object_marking_refs=[tlp],
                )
            elif ioc_type == IOCType.EMAIL:
                observable = EmailAddress(
                    value=ioc.value,
                    object_marking_refs=[tlp],
                )
            elif ioc_type in (IOCType.HASH_MD5, IOCType.HASH_SHA1, IOCType.HASH_SHA256):
                hash_map = {
                    IOCType.HASH_MD5: "MD5",
                    IOCType.HASH_SHA1: "SHA-1",
                    IOCType.HASH_SHA256: "SHA-256",
                }
                observable = File(
                    hashes={hash_map[ioc_type]: ioc.value},
                    object_marking_refs=[tlp],
                )
            else:
                return None

            return observable.serialize(pretty=True)
        except Exception as e:
            log.error("stix_conversion_failed", ioc_id=str(ioc.id), error=str(e))
            return None

    def ioc_to_indicator(self, ioc: IOC) -> Indicator | None:
        """Create a STIX 2.1 Indicator from an IOC."""
        try:
            ioc_type = IOCType(ioc.ioc_type)
            tlp = TLP_MAP.get(ioc.tlp, TLP_AMBER)

            # Build STIX pattern
            pattern = self._build_stix_pattern(ioc.value, ioc_type)
            if not pattern:
                return None

            severity_to_confidence = {
                Severity.CRITICAL: 90,
                Severity.HIGH: 75,
                Severity.MEDIUM: 60,
                Severity.LOW: 40,
                Severity.INFO: 20,
            }
            confidence = ioc.confidence or severity_to_confidence.get(
                Severity(ioc.severity), 50
            )

            indicator = Indicator(
                id=ioc.stix_id or f"indicator--{uuid4()}",
                name=f"[{ioc_type.upper()}] {ioc.value}",
                description=f"IOC detected by CyberGhost OSINT Enterprise",
                created_by_ref=self.IDENTITY.id,
                pattern=pattern,
                pattern_type="stix",
                valid_from=ioc.first_seen.isoformat(),
                valid_until=ioc.expiry.isoformat() if ioc.expiry else None,
                confidence=confidence,
                labels=ioc.tags or [],
                object_marking_refs=[tlp],
            )
            return indicator
        except Exception as e:
            log.error("indicator_creation_failed", error=str(e))
            return None

    def _build_stix_pattern(self, value: str, ioc_type: IOCType) -> str | None:
        """Build a STIX 2.1 pattern string."""
        patterns = {
            IOCType.IP: f"[ipv4-addr:value = '{value}']",
            IOCType.DOMAIN: f"[domain-name:value = '{value}']",
            IOCType.URL: f"[url:value = '{value}']",
            IOCType.EMAIL: f"[email-addr:value = '{value}']",
            IOCType.HASH_MD5: f"[file:hashes.'MD5' = '{value}']",
            IOCType.HASH_SHA1: f"[file:hashes.'SHA-1' = '{value}']",
            IOCType.HASH_SHA256: f"[file:hashes.'SHA-256' = '{value}']",
        }
        return patterns.get(ioc_type)

    def create_bundle(self, objects: list[Any]) -> Bundle:
        """Create a STIX 2.1 Bundle from a list of objects."""
        return Bundle(
            id=f"bundle--{uuid4()}",
            objects=[self.IDENTITY] + [o for o in objects if o is not None],
        )

    def create_threat_actor(
        self,
        name: str,
        aliases: list[str] | None = None,
        goals: list[str] | None = None,
        sophistication: str = "intermediate",
        resource_level: str = "government",
        primary_motivation: str = "organizational-gain",
        labels: list[str] | None = None,
    ) -> ThreatActor:
        """Create a STIX 2.1 ThreatActor object."""
        return ThreatActor(
            id=f"threat-actor--{uuid4()}",
            name=name,
            aliases=aliases or [],
            goals=goals or [],
            sophistication=sophistication,
            resource_level=resource_level,
            primary_motivation=primary_motivation,
            labels=labels or ["threat-actor"],
            created_by_ref=self.IDENTITY.id,
        )

    def create_malware(
        self,
        name: str,
        malware_types: list[str],
        is_family: bool = True,
        capabilities: list[str] | None = None,
        aliases: list[str] | None = None,
    ) -> Malware:
        """Create a STIX 2.1 Malware object."""
        return Malware(
            id=f"malware--{uuid4()}",
            name=name,
            malware_types=malware_types,
            is_family=is_family,
            capabilities=capabilities or [],
            aliases=aliases or [],
            created_by_ref=self.IDENTITY.id,
        )

    def create_campaign(
        self,
        name: str,
        description: str,
        aliases: list[str] | None = None,
        objective: str | None = None,
    ) -> Campaign:
        """Create a STIX 2.1 Campaign object."""
        return Campaign(
            id=f"campaign--{uuid4()}",
            name=name,
            description=description,
            aliases=aliases or [],
            objective=objective or "",
            created_by_ref=self.IDENTITY.id,
        )

    def create_attack_pattern(
        self,
        name: str,
        description: str,
        external_references: list[dict[str, str]] | None = None,
    ) -> AttackPattern:
        """Create a STIX 2.1 AttackPattern (MITRE ATT&CK technique)."""
        ext_refs = []
        if external_references:
            ext_refs = [
                stix2.ExternalReference(**ref) for ref in external_references
            ]

        return AttackPattern(
            id=f"attack-pattern--{uuid4()}",
            name=name,
            description=description,
            external_references=ext_refs,
            created_by_ref=self.IDENTITY.id,
        )

    def link_ioc_to_threat_actor(
        self, indicator: Indicator, threat_actor: ThreatActor
    ) -> Relationship:
        """Create relationship: indicator → attributed-to → threat-actor."""
        return Relationship(
            id=f"relationship--{uuid4()}",
            relationship_type="attributed-to",
            source_ref=indicator.id,
            target_ref=threat_actor.id,
            created_by_ref=self.IDENTITY.id,
        )

    def export_iocs_as_bundle(self, iocs: list[IOC]) -> str:
        """Export a list of IOCs as a STIX 2.1 Bundle JSON string."""
        stix_objects: list[Any] = []

        for ioc in iocs:
            indicator = self.ioc_to_indicator(ioc)
            if indicator:
                stix_objects.append(indicator)

        bundle = self.create_bundle(stix_objects)
        return bundle.serialize(pretty=True)
