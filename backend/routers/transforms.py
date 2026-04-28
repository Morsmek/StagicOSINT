"""
Transform routes
GET  /transforms             - list all available transforms
GET  /transforms/{type}      - list transforms for entity type
POST /transforms/run         - run a transform against an entity
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from database import get_db, db_get_entity, db_create_entity, db_create_edge, db_get_api_key
from models import TransformInput, TransformResult, TransformInfo, EntityType
from transform_engine import registry

router = APIRouter(prefix="/transforms", tags=["transforms"])


@router.get("", response_model=list[TransformInfo])
async def list_transforms():
    return registry.list_all()


@router.get("/for/{entity_type}", response_model=list[TransformInfo])
async def transforms_for_type(entity_type: str):
    try:
        et = EntityType(entity_type)
    except ValueError:
        raise HTTPException(400, f"Unknown entity type: {entity_type}")
    return registry.list_for_type(et)


@router.post("/run", response_model=TransformResult)
async def run_transform(body: TransformInput, db: aiosqlite.Connection = Depends(get_db)):
    # Load entity
    entity = await db_get_entity(db, body.entity_id)
    if not entity:
        raise HTTPException(404, f"Entity {body.entity_id} not found")

    # Gather API keys from DB
    api_keys: dict[str, str] = {}
    key_names = ["SHODAN_API_KEY", "VIRUSTOTAL_API_KEY", "IPINFO_TOKEN",
                 "HUNTER_API_KEY", "OPENCAGE_API_KEY"]
    for name in key_names:
        val = await db_get_api_key(db, name)
        if val:
            api_keys[name] = val

    # Run transform
    result = await registry.run(body.transform_name, entity, body.options, api_keys)

    # Persist results into the graph
    if result.success:
        for new_entity in result.entities:
            await db_create_entity(db, entity.get("graph_id", body.graph_id), new_entity.dict())
        for new_edge in result.edges:
            await db_create_edge(db, body.graph_id, new_edge.dict())

    return result
