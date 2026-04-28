"""
DNS Transforms
  - DnsResolve:       Domain -> IPAddress records
  - DnsReverse:       IPAddress -> Domain
  - DnsMx:           Domain -> MXRecord
  - DnsNs:           Domain -> NSRecord / Nameserver
  - DnsSubdomains:   Domain -> Subdomain (via brute-force wordlist)
"""
import asyncio
from typing import Any

from transforms.base import BaseTransform
from models import Entity, Edge, EntityType, TransformResult


# ---------------------------------------------------------------------------
# Resolve Domain -> A / AAAA records
# ---------------------------------------------------------------------------

class DnsResolve(BaseTransform):
    NAME = "dns_resolve"
    DISPLAY_NAME = "DNS Resolve"
    DESCRIPTION = "Resolve a domain to its A/AAAA IP addresses."
    INPUT_TYPES = [EntityType.DOMAIN, EntityType.SUBDOMAIN]
    OUTPUT_TYPES = [EntityType.IP_ADDRESS]

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        import socket
        domain = entity["value"]
        entities: list[Entity] = []
        edges: list[Edge] = []
        messages: list[str] = []

        try:
            loop = asyncio.get_event_loop()
            infos = await loop.run_in_executor(
                None, lambda: socket.getaddrinfo(domain, None)
            )
            seen: set[str] = set()
            for info in infos:
                ip = info[4][0]
                if ip not in seen:
                    seen.add(ip)
                    ip_entity = self._make_entity(EntityType.IP_ADDRESS, ip)
                    entities.append(ip_entity)
                    edges.append(self._make_edge(entity["id"], ip_entity.id, "resolves_to"))
            messages.append(f"Found {len(entities)} IP(s) for {domain}")
        except Exception as e:
            return TransformResult(
                transform_name=self.NAME,
                input_entity_id=entity["id"],
                success=False,
                error=str(e),
            )

        return self._result(entity["id"], entities, edges, messages)


# ---------------------------------------------------------------------------
# Reverse DNS: IPAddress -> Domain
# ---------------------------------------------------------------------------

class DnsReverse(BaseTransform):
    NAME = "dns_reverse"
    DISPLAY_NAME = "Reverse DNS"
    DESCRIPTION = "Perform a reverse DNS lookup on an IP address."
    INPUT_TYPES = [EntityType.IP_ADDRESS]
    OUTPUT_TYPES = [EntityType.DOMAIN]

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        import socket
        ip = entity["value"]
        try:
            loop = asyncio.get_event_loop()
            hostname, _, _ = await loop.run_in_executor(
                None, lambda: socket.gethostbyaddr(ip)
            )
            domain_entity = self._make_entity(EntityType.DOMAIN, hostname)
            edge = self._make_edge(entity["id"], domain_entity.id, "reverse_dns")
            return self._result(entity["id"], [domain_entity], [edge], [f"Reverse DNS: {hostname}"])
        except Exception as e:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error=str(e),
            )


# ---------------------------------------------------------------------------
# MX Records: Domain -> MXRecord
# ---------------------------------------------------------------------------

class DnsMx(BaseTransform):
    NAME = "dns_mx"
    DISPLAY_NAME = "DNS MX Records"
    DESCRIPTION = "Fetch MX records for a domain."
    INPUT_TYPES = [EntityType.DOMAIN]
    OUTPUT_TYPES = [EntityType.MX_RECORD]

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        try:
            import dns.resolver  # dnspython
        except ImportError:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error="dnspython not installed. Run: pip install dnspython",
            )

        domain = entity["value"]
        entities: list[Entity] = []
        edges: list[Edge] = []
        try:
            loop = asyncio.get_event_loop()
            answers = await loop.run_in_executor(
                None, lambda: dns.resolver.resolve(domain, "MX")
            )
            for rdata in answers:
                mx_val = str(rdata.exchange).rstrip(".")
                mx_entity = self._make_entity(
                    EntityType.MX_RECORD, mx_val,
                    priority=rdata.preference
                )
                entities.append(mx_entity)
                edges.append(self._make_edge(entity["id"], mx_entity.id, "mx_record"))
        except Exception as e:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error=str(e),
            )
        return self._result(entity["id"], entities, edges, [f"Found {len(entities)} MX record(s)"])


# ---------------------------------------------------------------------------
# NS Records: Domain -> Nameserver
# ---------------------------------------------------------------------------

class DnsNs(BaseTransform):
    NAME = "dns_ns"
    DISPLAY_NAME = "DNS NS Records"
    DESCRIPTION = "Fetch nameservers for a domain."
    INPUT_TYPES = [EntityType.DOMAIN]
    OUTPUT_TYPES = [EntityType.NAMESERVER]

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        try:
            import dns.resolver
        except ImportError:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error="dnspython not installed.",
            )

        domain = entity["value"]
        entities: list[Entity] = []
        edges: list[Edge] = []
        try:
            loop = asyncio.get_event_loop()
            answers = await loop.run_in_executor(
                None, lambda: dns.resolver.resolve(domain, "NS")
            )
            for rdata in answers:
                ns_val = str(rdata.target).rstrip(".")
                ns_entity = self._make_entity(EntityType.NAMESERVER, ns_val)
                entities.append(ns_entity)
                edges.append(self._make_edge(entity["id"], ns_entity.id, "nameserver"))
        except Exception as e:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error=str(e),
            )
        return self._result(entity["id"], entities, edges, [f"Found {len(entities)} nameserver(s)"])


# ---------------------------------------------------------------------------
# Subdomain Brute-force: Domain -> Subdomain
# ---------------------------------------------------------------------------

COMMON_SUBDOMAINS = [
    "www", "mail", "ftp", "smtp", "pop", "imap", "vpn", "remote",
    "api", "dev", "staging", "test", "admin", "portal", "dashboard",
    "cdn", "static", "media", "images", "shop", "blog", "help",
    "support", "docs", "app", "auth", "login", "secure", "ns1", "ns2",
]

class DnsSubdomains(BaseTransform):
    NAME = "dns_subdomains"
    DISPLAY_NAME = "DNS Subdomain Bruteforce"
    DESCRIPTION = "Brute-force common subdomains for a domain."
    INPUT_TYPES = [EntityType.DOMAIN]
    OUTPUT_TYPES = [EntityType.SUBDOMAIN]
    OPTIONS_SCHEMA = {
        "wordlist": {"type": "array", "description": "Custom subdomain wordlist (optional)"}
    }

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        import socket
        domain = entity["value"]
        wordlist = options.get("wordlist", COMMON_SUBDOMAINS)
        entities: list[Entity] = []
        edges: list[Edge] = []

        async def check(sub: str):
            fqdn = f"{sub}.{domain}"
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: socket.gethostbyname(fqdn))
                return fqdn
            except Exception:
                return None

        tasks = [check(sub) for sub in wordlist]
        results = await asyncio.gather(*tasks)

        for fqdn in results:
            if fqdn:
                sub_entity = self._make_entity(EntityType.SUBDOMAIN, fqdn)
                entities.append(sub_entity)
                edges.append(self._make_edge(entity["id"], sub_entity.id, "subdomain_of"))

        return self._result(entity["id"], entities, edges, [f"Found {len(entities)} subdomains"])
