"""
OGI Database Layer
Uses aiosqlite via SQLAlchemy async for lightweight local storage.
Swap DATABASE_URL in config.py for PostgreSQL in production.
"""
import sys
import json
from datetime import datetime
from typing import Optional, Any
import aiosqlite
from pathlib import Path

# When running as a PyInstaller .exe, store the DB next to the executable.
# In dev mode, store it in the backend folder.
if getattr(sys, 'frozen', False):
    DB_PATH = Path(sys.executable).parent / "ogi.db"
else:
    DB_PATH = Path(__file__).parent / "ogi.db"


async def get_db() -> aiosqlite.Connection:
    """Dependency: yields an open DB connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_db():
    """Create all tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS graphs (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                description TEXT,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS entities (
                id          TEXT PRIMARY KEY,
                graph_id    TEXT NOT NULL REFERENCES graphs(id) ON DELETE CASCADE,
                type        TEXT NOT NULL,
                value       TEXT NOT NULL,
                label       TEXT,
                properties  TEXT DEFAULT '{}',
                tags        TEXT DEFAULT '[]',
                x           REAL DEFAULT 0,
                y           REAL DEFAULT 0,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS edges (
                id          TEXT PRIMARY KEY,
                graph_id    TEXT NOT NULL REFERENCES graphs(id) ON DELETE CASCADE,
                source_id   TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                target_id   TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                relation    TEXT DEFAULT 'related_to',
                properties  TEXT DEFAULT '{}',
                weight      REAL DEFAULT 1.0,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS api_keys (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL UNIQUE,
                key_value   TEXT NOT NULL,
                description TEXT,
                created_at  TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_entities_graph ON entities(graph_id);
            CREATE INDEX IF NOT EXISTS idx_edges_graph    ON edges(graph_id);
            CREATE INDEX IF NOT EXISTS idx_edges_source   ON edges(source_id);
            CREATE INDEX IF NOT EXISTS idx_edges_target   ON edges(target_id);
        """)
        await db.commit()


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.utcnow().isoformat()

def _dumps(obj: Any) -> str:
    return json.dumps(obj)

def _loads(s: str) -> Any:
    if s is None:
        return {}
    try:
        return json.loads(s)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Graph CRUD
# ---------------------------------------------------------------------------

async def db_create_graph(db: aiosqlite.Connection, graph_id: str, name: str, description: Optional[str]) -> dict:
    now = _now()
    await db.execute(
        "INSERT INTO graphs (id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (graph_id, name, description, now, now)
    )
    await db.commit()
    return {"id": graph_id, "name": name, "description": description, "created_at": now, "updated_at": now}


async def db_get_graphs(db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute("""
        SELECT g.id, g.name, g.description, g.created_at, g.updated_at,
               COUNT(DISTINCT e.id) as entity_count,
               COUNT(DISTINCT ed.id) as edge_count
        FROM graphs g
        LEFT JOIN entities e  ON e.graph_id = g.id
        LEFT JOIN edges ed    ON ed.graph_id = g.id
        GROUP BY g.id
        ORDER BY g.updated_at DESC
    """)
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def db_get_graph(db: aiosqlite.Connection, graph_id: str) -> Optional[dict]:
    cursor = await db.execute("SELECT * FROM graphs WHERE id = ?", (graph_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def db_delete_graph(db: aiosqlite.Connection, graph_id: str):
    await db.execute("DELETE FROM graphs WHERE id = ?", (graph_id,))
    await db.commit()


# ---------------------------------------------------------------------------
# Entity CRUD
# ---------------------------------------------------------------------------

async def db_create_entity(db: aiosqlite.Connection, graph_id: str, entity: dict) -> dict:
    now = _now()
    await db.execute("""
        INSERT INTO entities (id, graph_id, type, value, label, properties, tags, x, y, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        entity["id"], graph_id, entity["type"], entity["value"],
        entity.get("label"), _dumps(entity.get("properties", {})),
        _dumps(entity.get("tags", [])),
        entity.get("x", 0), entity.get("y", 0),
        now, now
    ))
    await db.commit()
    return {**entity, "created_at": now, "updated_at": now}


async def db_get_entities(db: aiosqlite.Connection, graph_id: str) -> list[dict]:
    cursor = await db.execute("SELECT * FROM entities WHERE graph_id = ?", (graph_id,))
    rows = await cursor.fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["properties"] = _loads(d["properties"])
        d["tags"] = _loads(d["tags"])
        result.append(d)
    return result


async def db_get_entity(db: aiosqlite.Connection, entity_id: str) -> Optional[dict]:
    cursor = await db.execute("SELECT * FROM entities WHERE id = ?", (entity_id,))
    row = await cursor.fetchone()
    if not row:
        return None
    d = dict(row)
    d["properties"] = _loads(d["properties"])
    d["tags"] = _loads(d["tags"])
    return d


async def db_update_entity(db: aiosqlite.Connection, entity_id: str, updates: dict):
    now = _now()
    sets = []
    values = []
    for k, v in updates.items():
        if k in ("properties", "tags"):
            v = _dumps(v)
        sets.append(f"{k} = ?")
        values.append(v)
    sets.append("updated_at = ?")
    values.append(now)
    values.append(entity_id)
    await db.execute(f"UPDATE entities SET {', '.join(sets)} WHERE id = ?", values)
    await db.commit()


async def db_delete_entity(db: aiosqlite.Connection, entity_id: str):
    await db.execute("DELETE FROM entities WHERE id = ?", (entity_id,))
    await db.commit()


# ---------------------------------------------------------------------------
# Edge CRUD
# ---------------------------------------------------------------------------

async def db_create_edge(db: aiosqlite.Connection, graph_id: str, edge: dict) -> dict:
    now = _now()
    await db.execute("""
        INSERT INTO edges (id, graph_id, source_id, target_id, relation, properties, weight, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        edge["id"], graph_id, edge["source_id"], edge["target_id"],
        edge.get("relation", "related_to"), _dumps(edge.get("properties", {})),
        edge.get("weight", 1.0), now
    ))
    await db.commit()
    return {**edge, "created_at": now}


async def db_get_edges(db: aiosqlite.Connection, graph_id: str) -> list[dict]:
    cursor = await db.execute("SELECT * FROM edges WHERE graph_id = ?", (graph_id,))
    rows = await cursor.fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["properties"] = _loads(d["properties"])
        result.append(d)
    return result


async def db_delete_edge(db: aiosqlite.Connection, edge_id: str):
    await db.execute("DELETE FROM edges WHERE id = ?", (edge_id,))
    await db.commit()


# ---------------------------------------------------------------------------
# API Keys CRUD
# ---------------------------------------------------------------------------

async def db_set_api_key(db: aiosqlite.Connection, key_id: str, name: str, value: str, description: Optional[str]):
    now = _now()
    await db.execute("""
        INSERT INTO api_keys (id, name, key_value, description, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET key_value = excluded.key_value, description = excluded.description
    """, (key_id, name, value, description, now))
    await db.commit()


async def db_get_api_key(db: aiosqlite.Connection, name: str) -> Optional[str]:
    cursor = await db.execute("SELECT key_value FROM api_keys WHERE name = ?", (name,))
    row = await cursor.fetchone()
    return row[0] if row else None


async def db_list_api_keys(db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute("SELECT id, name, key_value, description, created_at FROM api_keys")
    rows = await cursor.fetchall()
    result = []
    for r in rows:
        d = dict(r)
        key = d.pop("key_value", "")
        d["key_masked"] = f"{'*' * (len(key) - 4)}{key[-4:]}" if len(key) > 4 else "****"
        result.append(d)
    return result


async def db_delete_api_key(db: aiosqlite.Connection, key_id: str):
    await db.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
    await db.commit()
