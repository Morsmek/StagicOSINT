"""
SDBA persistence layer (async SQLite) and the tamper-evident audit ledger.

The audit ledger is a SHA-256 hash chain: every entry hashes the previous
entry's hash together with its own payload, so any retroactive modification
breaks the chain. Each entry also exposes a 16-char "transaction key" derived
from its hash, standing in for the whitepaper's blockchain transaction key.
"""
from __future__ import annotations

import json
import hashlib
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Optional

import aiosqlite

DB_PATH = Path(__file__).resolve().parent.parent / "sdba.db"

GENESIS_HASH = "0" * 64


@asynccontextmanager
async def connect() -> AsyncIterator[aiosqlite.Connection]:
    """Open a fresh connection scoped to a single request/operation."""
    conn = await aiosqlite.connect(str(DB_PATH))
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        await conn.close()


async def init_db() -> None:
    async with connect() as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS assets (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                kind          TEXT NOT NULL,          -- email | domain
                label         TEXT NOT NULL,          -- masked, human readable
                id_hash       TEXT NOT NULL UNIQUE,   -- sha256 of identifier
                risk_score    INTEGER DEFAULT 0,
                risk_band     TEXT DEFAULT 'Unknown',
                breach_count  INTEGER DEFAULT 0,
                last_scan     REAL,
                created_at    REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS scans (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id      INTEGER,
                id_hash       TEXT NOT NULL,
                label         TEXT NOT NULL,
                kind          TEXT NOT NULL,
                risk_score    INTEGER NOT NULL,
                risk_band     TEXT NOT NULL,
                findings      TEXT NOT NULL,          -- json
                created_at    REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_label   TEXT NOT NULL,
                kind          TEXT NOT NULL,          -- asset | vendor
                severity      TEXT NOT NULL,
                title         TEXT NOT NULL,
                detail        TEXT NOT NULL,
                layer         TEXT,
                acknowledged  INTEGER DEFAULT 0,
                created_at    REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS vendors (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                domain        TEXT NOT NULL UNIQUE,
                risk_score    INTEGER DEFAULT 0,
                risk_band     TEXT DEFAULT 'Unknown',
                exposed       INTEGER DEFAULT 0,      -- exposed accounts estimate
                breach_count  INTEGER DEFAULT 0,
                last_scan     REAL,
                created_at    REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                ts            REAL NOT NULL,
                event_type    TEXT NOT NULL,
                ref           TEXT,
                payload_hash  TEXT NOT NULL,
                prev_hash     TEXT NOT NULL,
                entry_hash    TEXT NOT NULL,
                txn_key       TEXT NOT NULL
            );
            """
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Audit ledger (hash chain)
# ---------------------------------------------------------------------------
async def append_audit(db: aiosqlite.Connection, event_type: str,
                       ref: Optional[str], payload: dict) -> dict:
    cur = await db.execute("SELECT entry_hash FROM audit ORDER BY id DESC LIMIT 1")
    row = await cur.fetchone()
    prev_hash = row["entry_hash"] if row else GENESIS_HASH

    ts = time.time()
    payload_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    entry_hash = hashlib.sha256(
        f"{prev_hash}|{ts}|{event_type}|{ref or ''}|{payload_hash}".encode()
    ).hexdigest()
    txn_key = "0x" + entry_hash[:16]

    await db.execute(
        """INSERT INTO audit (ts, event_type, ref, payload_hash, prev_hash, entry_hash, txn_key)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (ts, event_type, ref, payload_hash, prev_hash, entry_hash, txn_key),
    )
    return {"ts": ts, "event_type": event_type, "txn_key": txn_key, "entry_hash": entry_hash}


async def verify_chain(db: aiosqlite.Connection) -> dict:
    cur = await db.execute("SELECT * FROM audit ORDER BY id ASC")
    rows = await cur.fetchall()
    prev = GENESIS_HASH
    for r in rows:
        recomputed = hashlib.sha256(
            f"{prev}|{r['ts']}|{r['event_type']}|{r['ref'] or ''}|{r['payload_hash']}".encode()
        ).hexdigest()
        if recomputed != r["entry_hash"] or r["prev_hash"] != prev:
            return {"valid": False, "entries": len(rows), "broken_at": r["id"]}
        prev = r["entry_hash"]
    return {"valid": True, "entries": len(rows), "broken_at": None}


# small helper used across routers
def now() -> float:
    return time.time()
