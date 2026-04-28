"""
Email Transforms
  - EmailDomain:     EmailAddress -> Domain
  - EmailVerify:     EmailAddress -> verify MX + SMTP reachability
  - EmailHunter:     Domain -> EmailAddress list (requires Hunter.io API key)
"""
import asyncio
import re
import httpx

from transforms.base import BaseTransform
from models import Entity, Edge, EntityType, TransformResult


class EmailDomain(BaseTransform):
    NAME = "email_domain"
    DISPLAY_NAME = "Email to Domain"
    DESCRIPTION = "Extract the domain from an email address."
    INPUT_TYPES = [EntityType.EMAIL]
    OUTPUT_TYPES = [EntityType.DOMAIN]

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        email = entity["value"]
        if "@" not in email:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error="Not a valid email address",
            )
        domain = email.split("@", 1)[1].strip()
        domain_entity = self._make_entity(EntityType.DOMAIN, domain)
        edge = self._make_edge(entity["id"], domain_entity.id, "email_domain")
        return self._result(entity["id"], [domain_entity], [edge], [f"Domain: {domain}"])


class EmailVerify(BaseTransform):
    NAME = "email_verify"
    DISPLAY_NAME = "Email Verify (MX)"
    DESCRIPTION = "Verify an email address by checking MX records for its domain."
    INPUT_TYPES = [EntityType.EMAIL]
    OUTPUT_TYPES = [EntityType.MX_RECORD]

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        try:
            import dns.resolver
        except ImportError:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error="dnspython not installed.",
            )

        email = entity["value"]
        if "@" not in email:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error="Invalid email",
            )

        domain = email.split("@", 1)[1]
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
                    priority=rdata.preference,
                )
                entities.append(mx_entity)
                edges.append(self._make_edge(entity["id"], mx_entity.id, "mx_record"))
        except Exception as e:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error=str(e),
            )

        return self._result(entity["id"], entities, edges, [f"Found {len(entities)} MX record(s)"])


class EmailHunter(BaseTransform):
    NAME = "email_hunter"
    DISPLAY_NAME = "Hunter.io Email Finder"
    DESCRIPTION = "Find email addresses associated with a domain using Hunter.io."
    INPUT_TYPES = [EntityType.DOMAIN]
    OUTPUT_TYPES = [EntityType.EMAIL]
    REQUIRES_API_KEY = True
    API_KEY_NAME = "HUNTER_API_KEY"

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        api_key = api_keys.get("HUNTER_API_KEY")
        if not api_key:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error="HUNTER_API_KEY not configured",
            )

        domain = entity["value"]
        entities: list[Entity] = []
        edges: list[Edge] = []

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://api.hunter.io/v2/domain-search",
                    params={"domain": domain, "api_key": api_key, "limit": 20}
                )
                data = resp.json()

            emails = data.get("data", {}).get("emails", [])
            for item in emails:
                addr = item.get("value", "")
                if addr:
                    email_entity = self._make_entity(
                        EntityType.EMAIL, addr,
                        first_name=item.get("first_name"),
                        last_name=item.get("last_name"),
                        position=item.get("position"),
                        confidence=item.get("confidence"),
                        source="hunter.io",
                    )
                    entities.append(email_entity)
                    edges.append(self._make_edge(entity["id"], email_entity.id, "email_found"))

        except Exception as e:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error=str(e),
            )

        return self._result(entity["id"], entities, edges, [f"Found {len(entities)} email(s)"])
