"""
Email Site Scan Transform
Checks 150+ websites for a registered email address.
Powered by the user-scanner library (bundled in backend/user_scanner).
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

# Ensure the backend root is on sys.path so user_scanner is importable
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from transforms.base import BaseTransform
from models import EntityType, TransformResult


class EmailOsintTransform(BaseTransform):
    NAME = "email_osint"
    DISPLAY_NAME = "Email Site Scan"
    DESCRIPTION = "Search 150+ sites (social, shopping, gaming…) for a registered email"
    INPUT_TYPES = [EntityType.EMAIL]
    OUTPUT_TYPES = [EntityType.SOCIAL_MEDIA, EntityType.URL]
    REQUIRES_API_KEY = False
    OPTIONS_SCHEMA = {
        "no_nsfw": {
            "type": "boolean",
            "default": False,
            "description": "Skip adult/NSFW sites",
        }
    }

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        email = entity["value"]
        no_nsfw = bool(options.get("no_nsfw", False))

        try:
            results = await asyncio.to_thread(self._scan, email, no_nsfw)
        except Exception as e:
            return TransformResult(
                transform_name=self.NAME,
                input_entity_id=entity["id"],
                success=False,
                error=f"Scan failed: {e}",
            )

        entities, edges, messages = [], [], []

        for r in results:
            if not r.is_found():
                continue
            url = r.url or f"https://{r.site_name.lower().replace(' ', '')}.com"
            ent = self._make_entity(
                EntityType.SOCIAL_MEDIA,
                value=url,
                label=r.site_name,
                site=r.site_name,
                category=r.category or "",
                email=email,
            )
            edges.append(self._make_edge(entity["id"], ent.id, relation="registered_on"))
            entities.append(ent)
            messages.append(f"{r.site_name} ({r.category or 'unknown'}): registered")

        return self._result(
            entity["id"],
            entities=entities,
            edges=edges,
            messages=messages or [f"No registrations found for '{email}'"],
        )

    # ------------------------------------------------------------------
    # Sync worker — runs in a thread via asyncio.to_thread
    # ------------------------------------------------------------------
    @staticmethod
    def _scan(email: str, no_nsfw: bool):
        from user_scanner.core.email_orchestrator import run_email_full_batch
        from user_scanner.core.helpers import ScanConfig
        cfg = ScanConfig(only_found=False, no_nsfw=no_nsfw, allow_loud=True)
        return run_email_full_batch(email, cfg)
