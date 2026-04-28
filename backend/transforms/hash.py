"""
Hash Transforms
  - HashVirusTotal:  Hash -> malware info (requires VT API key)
  - HashFileType:    Hash -> detect type from known hash databases
"""
import httpx

from transforms.base import BaseTransform
from models import Entity, Edge, EntityType, TransformResult


class HashVirusTotal(BaseTransform):
    NAME = "hash_virustotal"
    DISPLAY_NAME = "VirusTotal Hash Lookup"
    DESCRIPTION = "Look up a file hash on VirusTotal for malware analysis."
    INPUT_TYPES = [EntityType.HASH]
    OUTPUT_TYPES = [EntityType.DOCUMENT]
    REQUIRES_API_KEY = True
    API_KEY_NAME = "VIRUSTOTAL_API_KEY"

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        api_key = api_keys.get("VIRUSTOTAL_API_KEY")
        if not api_key:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error="VIRUSTOTAL_API_KEY not configured",
            )

        hash_val = entity["value"]
        messages: list[str] = []
        entities: list[Entity] = []
        edges: list[Edge] = []

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"https://www.virustotal.com/api/v3/files/{hash_val}",
                    headers={"x-apikey": api_key},
                )
                if resp.status_code == 404:
                    return TransformResult(
                        transform_name=self.NAME, input_entity_id=entity["id"],
                        success=False, error="Hash not found on VirusTotal",
                    )
                data = resp.json()

            attrs = data.get("data", {}).get("attributes", {})
            name = attrs.get("meaningful_name") or attrs.get("name", hash_val)
            detections = attrs.get("last_analysis_stats", {})
            malicious = detections.get("malicious", 0)
            total = sum(detections.values())

            doc_entity = self._make_entity(
                EntityType.DOCUMENT, name,
                hash=hash_val,
                malicious=malicious,
                total_engines=total,
                type_description=attrs.get("type_description", ""),
                size=attrs.get("size"),
                source="virustotal",
            )
            entities.append(doc_entity)
            edges.append(self._make_edge(entity["id"], doc_entity.id, "file_hash"))
            messages.append(f"Detections: {malicious}/{total} engines flagged as malicious")

        except Exception as e:
            return TransformResult(
                transform_name=self.NAME, input_entity_id=entity["id"],
                success=False, error=str(e),
            )

        return self._result(entity["id"], entities, edges, messages)
