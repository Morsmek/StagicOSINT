"""
Email Transforms
  - EmailDomain:          EmailAddress -> Domain
  - EmailVerify:          EmailAddress -> verify MX records
  - EmailHunter:          Domain -> EmailAddress list (requires Hunter.io API key)
  - EmailProspeoFinder:   Person -> EmailAddress using Prospeo Enrich Person API
"""
import asyncio
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


class EmailProspeoFinder(BaseTransform):
    NAME = "email_prospeo"
    DISPLAY_NAME = "Prospeo Email Finder"
    DESCRIPTION = "Find a professional email address for a person using Prospeo's Enrich Person API."
    INPUT_TYPES = [EntityType.PERSON]
    OUTPUT_TYPES = [EntityType.EMAIL]
    REQUIRES_API_KEY = True
    API_KEY_NAME = "PROSPEO_API_KEY"
    OPTIONS_SCHEMA = {
        "type": "object",
        "properties": {
            "full_name": {"type": "string", "description": "Person full name; defaults to the entity value."},
            "first_name": {"type": "string", "description": "Person first name."},
            "last_name": {"type": "string", "description": "Person last name."},
            "linkedin_url": {"type": "string", "description": "Person public LinkedIn URL."},
            "company_name": {"type": "string", "description": "Company name."},
            "company_website": {"type": "string", "description": "Company website or domain."},
            "company_linkedin_url": {"type": "string", "description": "Company public LinkedIn URL."},
            "person_id": {"type": "string", "description": "Prospeo person_id from Search Person API."},
            "only_verified_email": {"type": "boolean", "description": "Only return records with a verified email.", "default": True},
        },
    }

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        api_key = api_keys.get("PROSPEO_API_KEY")
        if not api_key:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error="PROSPEO_API_KEY not configured",
            )

        props = entity.get("properties") or {}
        data = self._build_payload_data(entity, props, options or {})
        if not self._has_minimum_matching_data(data):
            return TransformResult(
                transform_name=self.NAME,
                input_entity_id=entity["id"],
                success=False,
                error=(
                    "Prospeo requires a person_id, linkedin_url, email, or a person name "
                    "plus company_name, company_website, or company_linkedin_url. Add these "
                    "as entity properties or transform options."
                ),
            )

        payload = {
            "only_verified_email": bool(options.get("only_verified_email", True)),
            "data": data,
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.prospeo.io/enrich-person",
                    headers={"X-KEY": api_key, "Content-Type": "application/json"},
                    json=payload,
                )
                response_data = resp.json()

            if resp.status_code >= 400 or response_data.get("error"):
                error_code = response_data.get("error_code") or f"HTTP_{resp.status_code}"
                detail = response_data.get("message") or response_data.get("filter_error") or response_data.get("error_message") or response_data.get("error")
                return TransformResult(
                    transform_name=self.NAME,
                    input_entity_id=entity["id"],
                    success=False,
                    error=f"Prospeo API error {error_code}: {detail}",
                )

            person = response_data.get("person") or {}
            company = response_data.get("company") or {}
            email_data = person.get("email") or {}
            email_address = email_data.get("email") if isinstance(email_data, dict) else email_data
            if not email_address:
                return self._result(entity["id"], [], [], ["Prospeo matched the person but did not return an email address."])

            email_entity = self._make_entity(
                EntityType.EMAIL,
                email_address,
                first_name=person.get("first_name"),
                last_name=person.get("last_name"),
                full_name=person.get("full_name"),
                position=person.get("current_job_title"),
                linkedin_url=person.get("linkedin_url"),
                prospeo_person_id=person.get("person_id"),
                company_name=company.get("name") or data.get("company_name"),
                company_website=company.get("website") or data.get("company_website"),
                email_status=email_data.get("status") if isinstance(email_data, dict) else None,
                email_revealed=email_data.get("revealed") if isinstance(email_data, dict) else None,
                verification_method=email_data.get("verification_method") if isinstance(email_data, dict) else None,
                email_mx_provider=email_data.get("email_mx_provider") if isinstance(email_data, dict) else None,
                source="prospeo.io",
                only_verified_email=payload["only_verified_email"],
                free_enrichment=response_data.get("free_enrichment"),
            )
            edge = self._make_edge(entity["id"], email_entity.id, "email_found", source="prospeo.io")
            return self._result(entity["id"], [email_entity], [edge], ["Found 1 email with Prospeo"])

        except Exception as e:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error=str(e),
            )

    def _build_payload_data(self, entity: dict, props: dict, options: dict) -> dict:
        data = {}
        field_aliases = {
            "first_name": ["first_name", "firstName"],
            "last_name": ["last_name", "lastName"],
            "full_name": ["full_name", "fullName", "name"],
            "linkedin_url": ["linkedin_url", "linkedin", "linkedinUrl"],
            "email": ["email"],
            "company_name": ["company_name", "company", "organization", "org", "companyName"],
            "company_website": ["company_website", "company_domain", "domain", "website", "companyWebsite"],
            "company_linkedin_url": ["company_linkedin_url", "company_linkedin", "companyLinkedinUrl"],
            "person_id": ["person_id", "prospeo_person_id", "personId"],
        }
        for target, aliases in field_aliases.items():
            value = self._first_value(options, props, aliases)
            if value:
                data[target] = value

        if not data.get("full_name") and not (data.get("first_name") and data.get("last_name")):
            data["full_name"] = entity.get("value", "").strip()

        if data.get("full_name") and not (data.get("first_name") and data.get("last_name")):
            first_name, last_name = self._split_name(data["full_name"])
            data.setdefault("first_name", first_name)
            if last_name:
                data.setdefault("last_name", last_name)

        return {key: value for key, value in data.items() if value}

    def _first_value(self, options: dict, props: dict, aliases: list[str]) -> str | None:
        for source in (options, props):
            for alias in aliases:
                value = source.get(alias)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return None

    def _split_name(self, full_name: str) -> tuple[str, str | None]:
        parts = [part for part in full_name.strip().split() if part]
        if len(parts) >= 2:
            return parts[0], " ".join(parts[1:])
        if parts:
            return parts[0], None
        return "", None

    def _has_minimum_matching_data(self, data: dict) -> bool:
        if data.get("person_id") or data.get("linkedin_url") or data.get("email"):
            return True
        has_company = any(data.get(field) for field in ("company_name", "company_website", "company_linkedin_url"))
        has_name = bool(data.get("full_name") or (data.get("first_name") and data.get("last_name")))
        return has_name and has_company
