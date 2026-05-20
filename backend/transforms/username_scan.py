"""
Username Site Scan Transform
Checks 200+ websites for the presence of a given username.
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


class UsernameScanTransform(BaseTransform):
    NAME = "username_scan"
    DISPLAY_NAME = "Username Site Scan"
    DESCRIPTION = "Search 200+ sites (social, gaming, dev, music…) for this username"
    INPUT_TYPES = [EntityType.USERNAME]
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
        username = entity["value"]
        no_nsfw = bool(options.get("no_nsfw", False))

        try:
            results = await asyncio.to_thread(self._scan, username, no_nsfw)
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
            url = r.url or f"https://{r.site_name.lower().replace(' ', '')}.com/{username}"
            ent = self._make_entity(
                EntityType.SOCIAL_MEDIA,
                value=url,
                label=r.site_name,
                site=r.site_name,
                category=r.category or "",
                username=username,
            )
            edges.append(self._make_edge(entity["id"], ent.id, relation="found_on"))
            entities.append(ent)
            messages.append(f"{r.site_name} ({r.category or 'unknown'}): {url}")

        return self._result(
            entity["id"],
            entities=entities,
            edges=edges,
            messages=messages or [f"No profiles found for '{username}'"],
        )

    # ------------------------------------------------------------------
    # Sync worker — runs in a thread via asyncio.to_thread
    # ------------------------------------------------------------------
    @staticmethod
    def _scan(username: str, no_nsfw: bool):
        from user_scanner.core.orchestrator import run_user_full
        from user_scanner.core.helpers import ScanConfig
        cfg = ScanConfig(only_found=False, no_nsfw=no_nsfw, allow_loud=True)
        return run_user_full(username, cfg)
