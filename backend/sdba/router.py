"""
SDBA REST API.  Mounted under {API_PREFIX}/sdba.
"""
from __future__ import annotations

import json
import time
from typing import List, Optional

import aiosqlite as _aiosqlite
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import database as _ogi_db
from . import db as store
from . import intel
from . import live_intel

router = APIRouter(prefix="/sdba", tags=["sdba"])


async def _get_hibp_key() -> Optional[str]:
    """Read HIBP API key from the main ogi.db api_keys table (name='hibp')."""
    try:
        async with _aiosqlite.connect(str(_ogi_db.DB_PATH)) as db:
            db.row_factory = _aiosqlite.Row
            return await _ogi_db.db_get_api_key(db, "hibp")
    except Exception:
        return None


def _merge_findings(catalog: List[dict], live: List[dict]) -> List[dict]:
    """
    Merge live and catalog findings. Live findings are authoritative; catalog
    entries with the same breach name are suppressed to avoid duplication.
    """
    seen = {f["breach_name"].lower() for f in live}
    merged = live + [f for f in catalog if f["breach_name"].lower() not in seen]
    merged.sort(key=lambda f: (f.get("severity", 0), f.get("year", 0)), reverse=True)
    return merged


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ScanRequest(BaseModel):
    # Zero-knowledge: the client hashes the identifier locally and sends only
    # the hash + a masked label. `identifier` is accepted for API convenience
    # (server-side hashing) but the UI always sends `hash`.
    hash: Optional[str] = None
    identifier: Optional[str] = None
    label: Optional[str] = None
    kind: str = "email"
    monitor: bool = False  # also register as a monitored asset


class VendorCreate(BaseModel):
    name: str
    domain: str


class AssetCreate(BaseModel):
    hash: Optional[str] = None
    identifier: Optional[str] = None
    label: Optional[str] = None
    kind: str = "email"


def _mask(identifier: str, kind: str) -> str:
    identifier = identifier.strip()
    if kind == "email" and "@" in identifier:
        local, _, domain = identifier.partition("@")
        shown = local[0] if local else ""
        return f"{shown}{'*' * max(2, len(local) - 1)}@{domain}"
    return identifier


def _severity_band_to_alert(band: str) -> str:
    return {"Critical": "critical", "High": "high", "Medium": "medium",
            "Low": "low", "Clear": "info"}.get(band, "info")


# ---------------------------------------------------------------------------
# Scan  (the core zero-knowledge breach scan)
# ---------------------------------------------------------------------------
@router.post("/scan")
async def scan(req: ScanRequest):
    if req.hash:
        id_hash = req.hash.strip().lower()
        if len(id_hash) != 64 or any(c not in "0123456789abcdef" for c in id_hash):
            raise HTTPException(400, "hash must be a 64-char SHA-256 hex digest")
        label = req.label or (id_hash[:10] + "…")
    elif req.identifier:
        id_hash = intel.sha256_hex(req.identifier)
        label = req.label or _mask(req.identifier, req.kind)
    else:
        raise HTTPException(400, "provide either `hash` or `identifier`")

    catalog_findings = intel.correlate(id_hash)
    live_findings: List[dict] = []
    if req.identifier:
        hibp_key = await _get_hibp_key()
        live_findings = await live_intel.live_scan(req.identifier, req.kind, hibp_key)
    findings = _merge_findings(catalog_findings, live_findings)

    risk = intel.score_risk(findings)
    ts = store.now()

    async with store.connect() as db:
        await db.execute(
            """INSERT INTO scans (asset_id, id_hash, label, kind, risk_score, risk_band, findings, created_at)
               VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)""",
            (id_hash, label, req.kind, risk["score"], risk["band"], json.dumps(findings), ts),
        )

        asset_id = None
        if req.monitor:
            asset_id = await _upsert_asset(db, req.kind, label, id_hash, risk, len(findings), ts)

        # Raise alerts for credential / dark-web findings
        await _raise_alerts(db, label, "asset", findings, risk)

        audit = await store.append_audit(
            db, "scan", id_hash[:12],
            {"hash": id_hash, "kind": req.kind, "risk": risk["score"], "findings": len(findings)},
        )
        await db.commit()

    return {
        "scanned_at": ts,
        "label": label,
        "kind": req.kind,
        "id_hash": id_hash,
        "risk": risk,
        "findings": findings,
        "layers": intel.LAYERS,
        "monitored": req.monitor,
        "asset_id": asset_id,
        "txn_key": audit["txn_key"],
    }


async def _upsert_asset(db, kind, label, id_hash, risk, breach_count, ts) -> int:
    cur = await db.execute("SELECT id FROM assets WHERE id_hash = ?", (id_hash,))
    row = await cur.fetchone()
    if row:
        await db.execute(
            """UPDATE assets SET risk_score=?, risk_band=?, breach_count=?, last_scan=? WHERE id=?""",
            (risk["score"], risk["band"], breach_count, ts, row["id"]),
        )
        return row["id"]
    cur = await db.execute(
        """INSERT INTO assets (kind, label, id_hash, risk_score, risk_band, breach_count, last_scan, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (kind, label, id_hash, risk["score"], risk["band"], breach_count, ts, ts),
    )
    return cur.lastrowid


async def _raise_alerts(db, asset_label, kind, findings, risk):
    ts = store.now()
    high = [f for f in findings if f["layer"] in ("dark_web", "forum") or f["password_exposed"]]
    for f in high:
        sev = "critical" if f["layer"] == "dark_web" else ("high" if f["password_exposed"] else "medium")
        title = f"{asset_label} exposed in {f['breach_name']}"
        detail = (f"Surfaced on {f['layer_name']} ({f['year']}). "
                  f"Exposed: {', '.join(f['data_classes'])}.")
        await db.execute(
            """INSERT INTO alerts (asset_label, kind, severity, title, detail, layer, acknowledged, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 0, ?)""",
            (asset_label, kind, sev, title, detail, f["layer_name"], ts),
        )


# ---------------------------------------------------------------------------
# Assets (monitored identities)
# ---------------------------------------------------------------------------
@router.get("/assets")
async def list_assets():
    async with store.connect() as db:
        cur = await db.execute("SELECT * FROM assets ORDER BY risk_score DESC, created_at DESC")
        return [dict(r) for r in await cur.fetchall()]


@router.post("/assets")
async def add_asset(req: AssetCreate):
    if req.hash:
        id_hash = req.hash.strip().lower()
        label = req.label or (id_hash[:10] + "…")
    elif req.identifier:
        id_hash = intel.sha256_hex(req.identifier)
        label = req.label or _mask(req.identifier, req.kind)
    else:
        raise HTTPException(400, "provide either `hash` or `identifier`")

    catalog_findings = intel.correlate(id_hash)
    live_findings: List[dict] = []
    if req.identifier:
        hibp_key = await _get_hibp_key()
        live_findings = await live_intel.live_scan(req.identifier, req.kind, hibp_key)
    findings = _merge_findings(catalog_findings, live_findings)

    risk = intel.score_risk(findings)
    ts = store.now()
    async with store.connect() as db:
        try:
            asset_id = await _upsert_asset(db, req.kind, label, id_hash, risk, len(findings), ts)
        except Exception:
            raise HTTPException(409, "asset already monitored")
        await _raise_alerts(db, label, "asset", findings, risk)
        await store.append_audit(db, "asset_added", id_hash[:12],
                                 {"hash": id_hash, "kind": req.kind})
        await db.commit()
        cur = await db.execute("SELECT * FROM assets WHERE id=?", (asset_id,))
        return dict(await cur.fetchone())


@router.post("/assets/{asset_id}/rescan")
async def rescan_asset(asset_id: int):
    async with store.connect() as db:
        cur = await db.execute("SELECT * FROM assets WHERE id=?", (asset_id,))
        a = await cur.fetchone()
        if not a:
            raise HTTPException(404, "asset not found")
        findings = intel.correlate(a["id_hash"])
        risk = intel.score_risk(findings)
        ts = store.now()
        await db.execute(
            "UPDATE assets SET risk_score=?, risk_band=?, breach_count=?, last_scan=? WHERE id=?",
            (risk["score"], risk["band"], len(findings), ts, asset_id),
        )
        await _raise_alerts(db, a["label"], "asset", findings, risk)
        await store.append_audit(db, "rescan", a["id_hash"][:12], {"risk": risk["score"]})
        await db.commit()
        cur = await db.execute("SELECT * FROM assets WHERE id=?", (asset_id,))
        return {"asset": dict(await cur.fetchone()), "findings": findings, "risk": risk}


@router.delete("/assets/{asset_id}")
async def delete_asset(asset_id: int):
    async with store.connect() as db:
        await db.execute("DELETE FROM assets WHERE id=?", (asset_id,))
        await store.append_audit(db, "asset_removed", str(asset_id), {"id": asset_id})
        await db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Vendors / Scan-by-Proxy (supply-chain intelligence)
# ---------------------------------------------------------------------------
def _scan_domain(domain: str) -> dict:
    h = intel.sha256_hex(domain)
    findings = intel.correlate(h)
    risk = intel.score_risk(findings)
    # Estimated exposed accounts for this domain (deterministic).
    exposed = (intel._hash_int(h, "exposed") % 48000) + len(findings) * 1500
    return {"findings": findings, "risk": risk, "exposed": exposed}


@router.get("/vendors")
async def list_vendors():
    async with store.connect() as db:
        cur = await db.execute("SELECT * FROM vendors ORDER BY risk_score DESC, created_at DESC")
        return [dict(r) for r in await cur.fetchall()]


@router.post("/vendors")
async def add_vendor(req: VendorCreate):
    domain = req.domain.strip().lower()
    res = _scan_domain(domain)
    ts = store.now()
    async with store.connect() as db:
        try:
            cur = await db.execute(
                """INSERT INTO vendors (name, domain, risk_score, risk_band, exposed, breach_count, last_scan, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (req.name.strip(), domain, res["risk"]["score"], res["risk"]["band"],
                 res["exposed"], len(res["findings"]), ts, ts),
            )
        except Exception:
            raise HTTPException(409, "vendor already tracked")
        vid = cur.lastrowid
        await _raise_alerts(db, f"{req.name} ({domain})", "vendor", res["findings"], res["risk"])
        await store.append_audit(db, "vendor_added", domain, {"domain": domain, "risk": res["risk"]["score"]})
        await db.commit()
        cur = await db.execute("SELECT * FROM vendors WHERE id=?", (vid,))
        return dict(await cur.fetchone())


@router.post("/vendors/{vendor_id}/scan")
async def scan_vendor(vendor_id: int):
    async with store.connect() as db:
        cur = await db.execute("SELECT * FROM vendors WHERE id=?", (vendor_id,))
        v = await cur.fetchone()
        if not v:
            raise HTTPException(404, "vendor not found")
        res = _scan_domain(v["domain"])
        ts = store.now()
        await db.execute(
            "UPDATE vendors SET risk_score=?, risk_band=?, exposed=?, breach_count=?, last_scan=? WHERE id=?",
            (res["risk"]["score"], res["risk"]["band"], res["exposed"],
             len(res["findings"]), ts, vendor_id),
        )
        await _raise_alerts(db, f"{v['name']} ({v['domain']})", "vendor", res["findings"], res["risk"])
        await store.append_audit(db, "vendor_scan", v["domain"], {"risk": res["risk"]["score"]})
        await db.commit()
        cur = await db.execute("SELECT * FROM vendors WHERE id=?", (vendor_id,))
        return {"vendor": dict(await cur.fetchone()), "findings": res["findings"], "risk": res["risk"]}


@router.delete("/vendors/{vendor_id}")
async def delete_vendor(vendor_id: int):
    async with store.connect() as db:
        await db.execute("DELETE FROM vendors WHERE id=?", (vendor_id,))
        await store.append_audit(db, "vendor_removed", str(vendor_id), {"id": vendor_id})
        await db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------
@router.get("/alerts")
async def list_alerts(unacknowledged: bool = False):
    q = "SELECT * FROM alerts"
    if unacknowledged:
        q += " WHERE acknowledged = 0"
    q += " ORDER BY created_at DESC LIMIT 200"
    async with store.connect() as db:
        cur = await db.execute(q)
        return [dict(r) for r in await cur.fetchall()]


@router.post("/alerts/{alert_id}/ack")
async def ack_alert(alert_id: int):
    async with store.connect() as db:
        await db.execute("UPDATE alerts SET acknowledged=1 WHERE id=?", (alert_id,))
        await store.append_audit(db, "alert_ack", str(alert_id), {"id": alert_id})
        await db.commit()
    return {"ok": True}


@router.post("/alerts/ack-all")
async def ack_all():
    async with store.connect() as db:
        await db.execute("UPDATE alerts SET acknowledged=1 WHERE acknowledged=0")
        await db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Audit ledger
# ---------------------------------------------------------------------------
@router.get("/audit")
async def get_audit(limit: int = 100):
    async with store.connect() as db:
        cur = await db.execute("SELECT * FROM audit ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in await cur.fetchall()]


@router.get("/audit/verify")
async def verify_audit():
    async with store.connect() as db:
        return await store.verify_chain(db)


# ---------------------------------------------------------------------------
# Catalog + Dashboard
# ---------------------------------------------------------------------------
@router.get("/catalog")
async def catalog():
    return {
        "layers": intel.LAYERS,
        "breaches": [
            {
                "id": b.id, "name": b.name, "domain": b.domain, "year": b.year,
                "accounts": b.accounts, "severity": b.severity, "layer": b.layer,
                "layer_name": intel.LAYER_BY_ID[b.layer]["name"],
                "data_classes": b.data_classes,
            }
            for b in sorted(intel.CATALOG, key=lambda x: x.accounts, reverse=True)
        ],
    }


@router.get("/dashboard")
async def dashboard():
    async with store.connect() as db:
        async def scalar(q, *a):
            cur = await db.execute(q, a)
            r = await cur.fetchone()
            return list(r)[0] if r else 0

        assets = await scalar("SELECT COUNT(*) FROM assets")
        vendors = await scalar("SELECT COUNT(*) FROM vendors")
        scans = await scalar("SELECT COUNT(*) FROM scans")
        open_alerts = await scalar("SELECT COUNT(*) FROM alerts WHERE acknowledged=0")
        total_alerts = await scalar("SELECT COUNT(*) FROM alerts")
        critical = await scalar("SELECT COUNT(*) FROM alerts WHERE severity='critical' AND acknowledged=0")
        avg_risk = await scalar("SELECT COALESCE(AVG(risk_score),0) FROM assets")

        # Risk distribution across monitored assets
        dist = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Clear": 0}
        cur = await db.execute("SELECT risk_band, COUNT(*) c FROM assets GROUP BY risk_band")
        for r in await cur.fetchall():
            dist[r["risk_band"]] = dist.get(r["risk_band"], 0) + r["c"]

        # Findings per layer across all scans
        layer_counts = {l["id"]: 0 for l in intel.LAYERS}
        cur = await db.execute("SELECT findings FROM scans ORDER BY id DESC LIMIT 500")
        for r in await cur.fetchall():
            for f in json.loads(r["findings"]):
                layer_counts[f["layer"]] = layer_counts.get(f["layer"], 0) + 1

        cur = await db.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 6")
        recent_alerts = [dict(x) for x in await cur.fetchall()]

        chain = await store.verify_chain(db)

    return {
        "metrics": {
            "monitored_assets": assets,
            "tracked_vendors": vendors,
            "total_scans": scans,
            "open_alerts": open_alerts,
            "total_alerts": total_alerts,
            "critical_alerts": critical,
            "avg_risk": round(avg_risk, 1),
        },
        # Headline figures from the SDBA whitepaper
        "platform": {
            "detection_time": "2.4h",
            "accuracy": "97.3%",
            "false_positive_rate": "1.8%",
            "monitored_layers": len(intel.LAYERS),
        },
        "risk_distribution": dist,
        "layer_findings": [
            {"id": l["id"], "name": l["name"], "count": layer_counts[l["id"]]}
            for l in intel.LAYERS
        ],
        "recent_alerts": recent_alerts,
        "ledger": chain,
    }
