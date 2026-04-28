"""
OGI Base Transform
All transforms inherit from BaseTransform.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
import uuid

from models import Entity, Edge, EntityType, TransformResult, TransformInfo


class BaseTransform(ABC):
    NAME: str = ""
    DISPLAY_NAME: str = ""
    DESCRIPTION: str = ""
    INPUT_TYPES: list[EntityType] = []
    OUTPUT_TYPES: list[EntityType] = []
    REQUIRES_API_KEY: bool = False
    API_KEY_NAME: str | None = None
    OPTIONS_SCHEMA: dict[str, Any] = {}

    def info(self) -> TransformInfo:
        return TransformInfo(
            name=self.NAME,
            display_name=self.DISPLAY_NAME,
            description=self.DESCRIPTION,
            input_types=self.INPUT_TYPES,
            output_types=self.OUTPUT_TYPES,
            requires_api_key=self.REQUIRES_API_KEY,
            api_key_name=self.API_KEY_NAME,
            options_schema=self.OPTIONS_SCHEMA,
        )

    @abstractmethod
    async def run(
        self,
        entity: dict,
        options: dict,
        api_keys: dict,
    ) -> TransformResult:
        """Execute the transform and return discovered entities + edges."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_entity(self, type_: EntityType, value: str, label: str | None = None, **props) -> Entity:
        return Entity(
            id=str(uuid.uuid4()),
            type=type_,
            value=value,
            label=label or value,
            properties=props,
        )

    def _make_edge(self, source_id: str, target_id: str, relation: str = "related_to", **props) -> Edge:
        return Edge(
            id=str(uuid.uuid4()),
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            properties=props,
        )

    def _result(
        self,
        input_entity_id: str,
        entities: list[Entity] | None = None,
        edges: list[Edge] | None = None,
        messages: list[str] | None = None,
    ) -> TransformResult:
        return TransformResult(
            transform_name=self.NAME,
            input_entity_id=input_entity_id,
            entities=entities or [],
            edges=edges or [],
            messages=messages or [],
            success=True,
        )
