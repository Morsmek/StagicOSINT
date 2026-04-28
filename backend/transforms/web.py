"""
Web Transforms
  - WebScrape:       URL -> title, links, emails, social profiles
  - WebHeaders:      URL -> HTTPHeader entities
  - WebUrlsFromDomain: Domain -> URL list (scraped from homepage)
"""
import re
import httpx
from urllib.parse import urljoin, urlparse

from transforms.base import BaseTransform
from models import Entity, Edge, EntityType, TransformResult

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
SOCIAL_PATTERNS = {
    "twitter": re.compile(r"twitter\.com/([A-Za-z0-9_]+)"),
    "linkedin": re.compile(r"linkedin\.com/(?:in|company)/([A-Za-z0-9_\-]+)"),
    "github": re.compile(r"github\.com/([A-Za-z0-9_\-]+)"),
    "facebook": re.compile(r"facebook\.com/([A-Za-z0-9_.\-]+)"),
    "instagram": re.compile(r"instagram\.com/([A-Za-z0-9_.\-]+)"),
}


def _get_html(url: str) -> tuple[str, dict]:
    """Fetch URL and return (body_text, headers)."""
    with httpx.Client(timeout=15, follow_redirects=True, headers={
        "User-Agent": "Mozilla/5.0 (compatible; OGI-Bot/1.0)"
    }) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text, dict(resp.headers)


class WebScrape(BaseTransform):
    NAME = "web_scrape"
    DISPLAY_NAME = "Web Scrape"
    DESCRIPTION = "Scrape a URL for linked domains, emails, and social media profiles."
    INPUT_TYPES = [EntityType.URL, EntityType.DOMAIN]
    OUTPUT_TYPES = [EntityType.URL, EntityType.EMAIL, EntityType.SOCIAL_MEDIA, EntityType.DOMAIN]
    OPTIONS_SCHEMA = {
        "max_links": {"type": "integer", "default": 20, "description": "Max external links to extract"}
    }

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        import asyncio
        value = entity["value"]
        if not value.startswith("http"):
            value = f"https://{value}"

        max_links = int(options.get("max_links", 20))
        entities: list[Entity] = []
        edges: list[Edge] = []
        messages: list[str] = []

        try:
            loop = asyncio.get_event_loop()
            html, headers = await loop.run_in_executor(None, lambda: _get_html(value))
        except Exception as e:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error=str(e),
            )

        base_domain = urlparse(value).netloc

        # Extract emails
        for email in set(EMAIL_RE.findall(html)):
            em = self._make_entity(EntityType.EMAIL, email, source="web_scrape")
            entities.append(em)
            edges.append(self._make_edge(entity["id"], em.id, "found_on_page"))

        # Extract social profiles
        for platform, pattern in SOCIAL_PATTERNS.items():
            for match in pattern.finditer(html):
                profile_url = match.group(0)
                username = match.group(1)
                sm = self._make_entity(
                    EntityType.SOCIAL_MEDIA, profile_url,
                    platform=platform, username=username,
                )
                entities.append(sm)
                edges.append(self._make_edge(entity["id"], sm.id, "social_profile"))

        # Extract external links
        href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.I)
        seen_domains: set[str] = set()
        count = 0
        for href in href_pattern.findall(html):
            if count >= max_links:
                break
            full = urljoin(value, href)
            parsed = urlparse(full)
            if parsed.netloc and parsed.netloc != base_domain:
                domain_val = parsed.netloc
                if domain_val not in seen_domains:
                    seen_domains.add(domain_val)
                    dom = self._make_entity(EntityType.DOMAIN, domain_val, source="web_link")
                    entities.append(dom)
                    edges.append(self._make_edge(entity["id"], dom.id, "links_to"))
                    count += 1

        messages.append(
            f"Extracted: {len([e for e in entities if e.type == EntityType.EMAIL])} emails, "
            f"{len([e for e in entities if e.type == EntityType.SOCIAL_MEDIA])} social profiles, "
            f"{len(seen_domains)} external domains"
        )
        return self._result(entity["id"], entities, edges, messages)


class WebHeaders(BaseTransform):
    NAME = "web_headers"
    DISPLAY_NAME = "HTTP Headers"
    DESCRIPTION = "Fetch HTTP response headers from a URL or domain."
    INPUT_TYPES = [EntityType.URL, EntityType.DOMAIN]
    OUTPUT_TYPES = [EntityType.HTTP_HEADER]

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        import asyncio
        value = entity["value"]
        if not value.startswith("http"):
            value = f"https://{value}"

        try:
            loop = asyncio.get_event_loop()
            _, headers = await loop.run_in_executor(None, lambda: _get_html(value))
        except Exception as e:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error=str(e),
            )

        entities: list[Entity] = []
        edges: list[Edge] = []
        interesting = {"server", "x-powered-by", "x-frame-options", "content-security-policy",
                       "strict-transport-security", "x-content-type-options", "set-cookie"}

        for key, val in headers.items():
            if key.lower() in interesting:
                h = self._make_entity(EntityType.HTTP_HEADER, f"{key}: {val}", header_name=key, header_value=val)
                entities.append(h)
                edges.append(self._make_edge(entity["id"], h.id, "http_header"))

        return self._result(entity["id"], entities, edges, [f"Found {len(entities)} interesting headers"])
