"""
Entity CRUD routes
POST   /graphs/{id}/entities        - add entity
GET    /graphs/{id}/entities        - list entities
GET    /graphs/{id}/entities/{eid}  - get entity
PATCH  /graphs/{id}/entities/{eid}  - update entity (label, position, properties)
DELETE /graphs/{id}/entities/{eid}  - delete entity
POST   /graphs/{id}/edges           - add edge
DELETE /graphs/{id}/edges/{edgeid}  - delete edge
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from database import (
    get_db, db_create_entity, db_get_entities, db_get_entity,
    db_update_entity, db_delete_entity, db_create_edge, db_get_edges, db_delete_edge
)
from models import EntityCreate, Entity, EdgeCreate, Edge

router = APIRouter(tags=["entities"])


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

@router.post("/graphs/{graph_id}/entities", response_model=Entity, status_code=201)
async def create_entity(
    graph_id: str,
    body: EntityCreate,
    db: aiosqlite.Connection = Depends(get_db),
):
    entity = Entity(id=str(uuid.uuid4()), **body.dict())
    row = await db_create_entity(db, graph_id, entity.dict())
    return entity


@router.get("/graphs/{graph_id}/entities", response_model=list[Entity])
async def list_entities(graph_id: str, db: aiosqlite.Connection = Depends(get_db)):
    return await db_get_entities(db, graph_id)


@router.get("/graphs/{graph_id}/entities/{entity_id}", response_model=Entity)
async def get_entity(graph_id: str, entity_id: str, db: aiosqlite.Connection = Depends(get_db)):
    entity = await db_get_entity(db, entity_id)
    if not entity or entity.get("graph_id") != graph_id:
        raise HTTPException(404, "Entity not found")
    return entity


@router.patch("/graphs/{graph_id}/entities/{entity_id}", response_model=Entity)
async def update_entity(
    graph_id: str,
    entity_id: str,
    body: dict,
    db: aiosqlite.Connection = Depends(get_db),
):
    entity = await db_get_entity(db, entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
    allowed = {"label", "x", "y", "properties", "tags", "value"}
    updates = {k: v for k, v in body.items() if k in allowed}
    await db_update_entity(db, entity_id, updates)
    return await db_get_entity(db, entity_id)


@router.delete("/graphs/{graph_id}/entities/{entity_id}", status_code=204)
async def delete_entity(graph_id: str, entity_id: str, db: aiosqlite.Connection = Depends(get_db)):
    entity = await db_get_entity(db, entity_id)
    if not entity:
        raise HTTPException(404, "Entity not found")
    await db_delete_entity(db, entity_id)


# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------

@router.post("/graphs/{graph_id}/edges", response_model=Edge, status_code=201)
async def create_edge(graph_id: str, body: EdgeCreate, db: aiosqlite.Connection = Depends(get_db)):
    edge = Edge(id=str(uuid.uuid4()), **body.dict())
    await db_create_edge(db, graph_id, edge.dict())
    return edge


@router.get("/graphs/{graph_id}/edges", response_model=list[Edge])
async def list_edges(graph_id: str, db: aiosqlite.Connection = Depends(get_db)):
    return await db_get_edges(db, graph_id)


@router.delete("/graphs/{graph_id}/edges/{edge_id}", status_code=204)
async def delete_edge(graph_id: str, edge_id: str, db: aiosqlite.Connection = Depends(get_db)):
    await db_delete_edge(db, edge_id)
