"""
IP / Network Transforms
  - IpGeolocate:  IPAddress -> Location + properties
  - IpAsn:        IPAddress -> ASNumber
  - IpWhois:      IPAddress -> Organization
  - IpShodan:     IPAddress -> open ports, services (requires Shodan API key)
"""
import asyncio
import httpx

from transforms.base import BaseTransform
from models import Entity, Edge, EntityType, TransformResult


class IpGeolocate(BaseTransform):
    NAME = "ip_geolocate"
    DISPLAY_NAME = "IP Geolocation"
    DESCRIPTION = "Get geolocation and ISP info for an IP address (uses ip-api.com, no key required)."
    INPUT_TYPES = [EntityType.IP_ADDRESS]
    OUTPUT_TYPES = [EntityType.LOCATION, EntityType.ORGANIZATION, EntityType.AS_NUMBER]

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        ip = entity["value"]
        entities: list[Entity] = []
        edges: list[Edge] = []
        messages: list[str] = []

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"http://ip-api.com/json/{ip}",
                    params={"fields": "status,country,regionName,city,lat,lon,isp,org,as,asname"}
                )
                data = resp.json()

            if data.get("status") != "success":
                raise ValueError(data.get("message", "ip-api returned non-success"))

            # Location
            city = data.get("city", "")
            country = data.get("country", "")
            loc_label = f"{city}, {country}".strip(", ")
            if loc_label:
                loc_entity = self._make_entity(
                    EntityType.LOCATION, loc_label,
                    lat=data.get("lat"),
                    lon=data.get("lon"),
                    country=country,
                    region=data.get("regionName"),
                    city=city,
                )
                entities.append(loc_entity)
                edges.append(self._make_edge(entity["id"], loc_entity.id, "located_in"))
                messages.append(f"Location: {loc_label}")

            # Organization / ISP
            org_name = data.get("org") or data.get("isp")
            if org_name:
                org_entity = self._make_entity(EntityType.ORGANIZATION, org_name, isp=data.get("isp"))
                entities.append(org_entity)
                edges.append(self._make_edge(entity["id"], org_entity.id, "belongs_to"))

            # ASN
            as_raw = data.get("as", "")
            if as_raw:
                asn = as_raw.split(" ")[0]  # e.g. "AS12345 Name"
                asn_entity = self._make_entity(
                    EntityType.AS_NUMBER, asn,
                    asname=data.get("asname"),
                )
                entities.append(asn_entity)
                edges.append(self._make_edge(entity["id"], asn_entity.id, "in_asn"))

        except Exception as e:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error=str(e),
            )

        return self._result(entity["id"], entities, edges, messages)


class IpWhois(BaseTransform):
    NAME = "ip_whois"
    DISPLAY_NAME = "IP WHOIS"
    DESCRIPTION = "Perform a WHOIS lookup on an IP address to find registration info."
    INPUT_TYPES = [EntityType.IP_ADDRESS]
    OUTPUT_TYPES = [EntityType.ORGANIZATION, EntityType.NETWORK]

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        try:
            import ipwhois  # pip install ipwhois
        except ImportError:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error="ipwhois not installed. Run: pip install ipwhois",
            )

        ip = entity["value"]
        entities: list[Entity] = []
        edges: list[Edge] = []

        try:
            loop = asyncio.get_event_loop()
            obj = ipwhois.IPWhois(ip)
            results = await loop.run_in_executor(None, lambda: obj.lookup_rdap(depth=1))

            # Organisation
            org_name = (
                results.get("network", {}).get("name")
                or results.get("asn_description", "")
            )
            if org_name:
                org_entity = self._make_entity(
                    EntityType.ORGANIZATION, org_name,
                    country=results.get("asn_country_code"),
                )
                entities.append(org_entity)
                edges.append(self._make_edge(entity["id"], org_entity.id, "registered_to"))

            # Network CIDR
            cidr = results.get("network", {}).get("cidr")
            if cidr:
                net_entity = self._make_entity(EntityType.NETWORK, cidr)
                entities.append(net_entity)
                edges.append(self._make_edge(entity["id"], net_entity.id, "within_network"))

        except Exception as e:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error=str(e),
            )

        return self._result(entity["id"], entities, edges)


class IpShodan(BaseTransform):
    NAME = "ip_shodan"
    DISPLAY_NAME = "Shodan Host Lookup"
    DESCRIPTION = "Query Shodan for open ports and services on an IP address."
    INPUT_TYPES = [EntityType.IP_ADDRESS]
    OUTPUT_TYPES = [EntityType.NETWORK]
    REQUIRES_API_KEY = True
    API_KEY_NAME = "SHODAN_API_KEY"
    OPTIONS_SCHEMA = {}

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        api_key = api_keys.get("SHODAN_API_KEY")
        if not api_key:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error="SHODAN_API_KEY not configured",
            )

        ip = entity["value"]
        messages: list[str] = []

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"https://api.shodan.io/shodan/host/{ip}",
                    params={"key": api_key}
                )
                if resp.status_code != 200:
                    raise ValueError(f"Shodan returned {resp.status_code}: {resp.text}")
                data = resp.json()

            ports = data.get("ports", [])
            hostnames = data.get("hostnames", [])
            org = data.get("org", "")
            os_ = data.get("os", "")

            # Update input entity properties
            messages.append(f"Open ports: {ports}")
            if org:
                messages.append(f"Org: {org}")
            if os_:
                messages.append(f"OS: {os_}")

            entities: list[Entity] = []
            edges: list[Edge] = []

            for hostname in hostnames:
                dom = self._make_entity(EntityType.DOMAIN, hostname, source="shodan")
                entities.append(dom)
                edges.append(self._make_edge(entity["id"], dom.id, "hostname"))

        except Exception as e:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error=str(e),
            )

        return self._result(entity["id"], entities, edges, messages)
