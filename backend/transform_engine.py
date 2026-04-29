"""
OGI Transform Engine
Discovers, registers, and runs transforms against graph entities.
"""
from __future__ import annotations
import importlib
import logging
import pkgutil
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

from models import EntityType, TransformResult, TransformInfo

if TYPE_CHECKING:
    from transforms.base import BaseTransform


class TransformRegistry:
    """
    Auto-discovers all transforms in the `transforms` package and
    provides a central lookup.
    """

    def __init__(self):
        self._registry: dict[str, "BaseTransform"] = {}
        self._discover()

    def _discover(self):
        import transforms as pkg
        for _, module_name, _ in pkgutil.iter_modules(pkg.__path__):
            if module_name == "base":
                continue
            try:
                module = importlib.import_module(f"transforms.{module_name}")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and hasattr(attr, "NAME")
                        and attr.__name__ != "BaseTransform"
                    ):
                        instance = attr()
                        self._registry[instance.NAME] = instance
            except Exception as e:
                logger.warning("Failed to load transforms.%s: %s", module_name, e)

    def get(self, name: str) -> "BaseTransform | None":
        return self._registry.get(name)

    def list_all(self) -> list[TransformInfo]:
        return [t.info() for t in self._registry.values()]

    def list_for_type(self, entity_type: EntityType) -> list[TransformInfo]:
        return [
            t.info()
            for t in self._registry.values()
            if entity_type in t.INPUT_TYPES
        ]

    async def run(
        self,
        name: str,
        entity: dict,
        options: dict | None = None,
        api_keys: dict | None = None,
    ) -> TransformResult:
        transform = self.get(name)
        if transform is None:
            return TransformResult(
                transform_name=name,
                input_entity_id=entity["id"],
                success=False,
                error=f"Transform '{name}' not found",
            )

        entity_type = EntityType(entity["type"])
        if entity_type not in transform.INPUT_TYPES:
            return TransformResult(
                transform_name=name,
                input_entity_id=entity["id"],
                success=False,
                error=f"Transform '{name}' does not support entity type '{entity_type}'",
            )

        try:
            return await transform.run(entity, options or {}, api_keys or {})
        except Exception as e:
            return TransformResult(
                transform_name=name,
                input_entity_id=entity["id"],
                success=False,
                error=str(e),
            )


# Singleton
registry = TransformRegistry()
