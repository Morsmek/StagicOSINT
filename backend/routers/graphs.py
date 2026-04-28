"""
Graph CRUD routes
GET    /graphs           - list all graphs
POST   /graphs           - create graph
GET    /graphs/{id}      - get graph with entities + edges
DELETE /graphs/{id}      - delete graph
GET    /graphs/{id}/stats - graph analysis stats
GET    /graphs/{id}/layout - compute force-directed layout
POST   /graphs/{id}/import - import MTGX
GET    /graphs/{id}/export - export MTGX
"""
import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from database import (
    get_db, db_create_graph, db_get_graphs, db_get_graph,
    db_delete_graph, db_get_entities, db_get_edges,
)
from models import GraphCreate, GraphSummary, Graph
from graph_engine import GraphEngine

router = APIRouter(prefix="/graphs", tags=["graphs"])


@router.get("", response_model=list[GraphSummary])
async def list_graphs(db: aiosqlite.Connection = Depends(get_db)):
    rows = await db_get_graphs(db)
    return [GraphSummary(**r) for r in rows]


@router.post("", response_model=Graph, status_code=201)
async def create_graph(body: GraphCreate, db: aiosqlite.Connection = Depends(get_db)):
    graph_id = str(uuid.uuid4())
    row = await db_create_graph(db, graph_id, body.name, body.description)
    return Graph(id=row["id"], name=row["name"], description=row["description"],
                 created_at=row["created_at"], updated_at=row["updated_at"])


@router.get("/{graph_id}", response_model=Graph)
async def get_graph(graph_id: str, db: aiosqlite.Connection = Depends(get_db)):
    row = await db_get_graph(db, graph_id)
    if not row:
        raise HTTPException(404, "Graph not found")
    entities = await db_get_entities(db, graph_id)
    edges = await db_get_edges(db, graph_id)
    return Graph(
        id=row["id"], name=row["name"], description=row["description"],
        created_at=row["created_at"], updated_at=row["updated_at"],
        entities=entities, edges=edges,
    )


@router.delete("/{graph_id}", status_code=204)
async def delete_graph(graph_id: str, db: aiosqlite.Connection = Depends(get_db)):
    row = await db_get_graph(db, graph_id)
    if not row:
        raise HTTPException(404, "Graph not found")
    await db_delete_graph(db, graph_id)


@router.get("/{graph_id}/stats")
async def graph_stats(graph_id: str, db: aiosqlite.Connection = Depends(get_db)):
    entities = await db_get_entities(db, graph_id)
    edges = await db_get_edges(db, graph_id)
    engine = GraphEngine(entities, edges)
    stats = engine.stats()
    centrality = engine.degree_centrality()
    # Top 5 by degree
    top = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
    stats["top_nodes_by_degree"] = [
        {"id": k, "value": entities_map[k]["value"] if (entities_map := {e["id"]: e for e in entities}) else k, "centrality": v}
        for k, v in top
    ]
    return stats


@router.get("/{graph_id}/layout")
async def compute_layout(
    graph_id: str,
    iterations: int = 50,
    width: float = 1200,
    height: float = 800,
    db: aiosqlite.Connection = Depends(get_db)
):
    entities = await db_get_entities(db, graph_id)
    edges = await db_get_edges(db, graph_id)
    engine = GraphEngine(entities, edges)
    layout = engine.compute_layout(iterations=iterations, width=width, height=height)
    return {"layout": {k: {"x": v[0], "y": v[1]} for k, v in layout.items()}}


@router.get("/{graph_id}/path")
async def shortest_path(
    graph_id: str, source_id: str, target_id: str,
    db: aiosqlite.Connection = Depends(get_db)
):
    entities = await db_get_entities(db, graph_id)
    edges = await db_get_edges(db, graph_id)
    engine = GraphEngine(entities, edges)
    path = engine.shortest_path(source_id, target_id)
    if path is None:
        raise HTTPException(404, "No path found between nodes")
    entities_map = {e["id"]: e for e in entities}
    return {
        "path": path,
        "length": len(path) - 1,
        "nodes": [entities_map.get(nid) for nid in path],
    }


@router.post("/{graph_id}/import")
async def import_mtgx(
    graph_id: str,
    body: dict,
    db: aiosqlite.Connection = Depends(get_db)
):
    """Import entities and edges from MTGX-style JSON."""
    from database import db_create_entity, db_create_edge
    entities_data, edges_data = GraphEngine.from_mtgx(body)
    created_entities = 0
    created_edges = 0
    for e in entities_data:
        if "id" not in e:
            e["id"] = str(uuid.uuid4())
        await db_create_entity(db, graph_id, e)
        created_entities += 1
    for edge in edges_data:
        if "id" not in edge:
            edge["id"] = str(uuid.uuid4())
        await db_create_edge(db, graph_id, edge)
        created_edges += 1
    return {"imported_entities": created_entities, "imported_edges": created_edges}


@router.get("/{graph_id}/export")
async def export_mtgx(graph_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Export the graph as MTGX-style JSON."""
    entities = await db_get_entities(db, graph_id)
    edges = await db_get_edges(db, graph_id)
    engine = GraphEngine(entities, edges)
    return engine.to_mtgx()
