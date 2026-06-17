"""
SDBA Live Intelligence Engine
==============================
Real HTTP-based breach and dark-web intelligence gathering.
All sources are legally usable in a commercial security product.

Sources implemented (in order of depth):

  Layer 1 — Surface / legacy breach DBs
    * XposedOrNot  (free, no key) – real breach membership lookup
    * HIBP         (optional API key) – authoritative breach data

  Layer 2 – Paste sites
    * Pastebin     (public scrape API, no key) – recent paste mentions

  Layer 3 – Dark-web clearnet indexer
    * Ahmia.fi     (free, no key, no Tor) – indexes .onion content via HTTPS

Results are merged with the deterministic catalog in router.py.
"""
from __future__ import annotations

import asyncio
import hashlib
import re
import time
from typing import List, Optional

import httpx

# ── timeouts ──────────────────────────────────────────────────────────────────
_TIMEOUT = httpx.Timeout(12.0, connect=6.0)
_LONG    = httpx.Timeout(25.0, connect=8.0)    # Ahmia can be slow

# ── shared headers ────────────────────────────────────────────────────────────
_UA = "Mozilla/5.0 (compatible; SDBA-Scanner/1.0; security-research)"


# =============================================================================
# XposedOrNot  –  https://xposedornot.com
# Free, no API key.  Returns the breach names an email appeared in.
# =============================================================================
async def check_xposedornot(email: str) -> List[dict]:
    """
    Query XposedOrNot's free breach API.
    Returns a list of finding dicts compatible with intel.CATALOG format.
    """
    url = f"https://api.xposedornot.com/v1/check-email/{email}"
    findings = []
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(url, headers={"User-Agent": _UA})
        if r.status_code == 404:
            return []   # clean – email not in any breach
        if r.status_code != 200:
            return []
        data = r.json()
        breaches = data.get("ExposedBreaches", {}).get("breaches_details", [])
        for b in breaches:
            name = b.get("breach") or b.get("name") or "Unknown"
            year = _parse_year(b.get("year") or b.get("xposed_date") or "")
            records = _parse_int(b.get("xposed_records", 0))
            data_classes = b.get("xposed_data", "Email addresses").split(",")
            data_classes = [d.strip() for d in data_classes if d.strip()]
            password_exposed = any("password" in d.lower() for d in data_classes)
            findings.append({
                "breach_id": f"xon_{name.lower().replace(' ', '_')}",
                "breach_name": name,
                "domain": b.get("domain", ""),
                "year": year,
                "accounts": records,
                "severity": _severity_from_classes(data_classes),
                "layer": "legacy_db",
                "layer_name": "Legacy Breach DB",
                "data_classes": data_classes,
                "password_exposed": password_exposed,
                "discovered": str(year) + "-01-01",
                "source": "XposedOrNot",
                "live": True,
            })
    except Exception:
        pass
    return findings


# =============================================================================
# Have I Been Pwned  –  https://haveibeenpwned.com
# Requires hibp_api_key (stored in SDBA API keys, optional).
# =============================================================================
async def check_hibp(email: str, api_key: str) -> List[dict]:
    """
    Query the HIBP v3 breachedaccount endpoint.
    API key available at https://haveibeenpwned.com/API/Key (~€3/month).
    """
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
    findings = []
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(url, headers={
                "User-Agent": _UA,
                "hibp-api-key": api_key,
            }, params={"truncateResponse": "false"})
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            return []
        for b in r.json():
            data_classes = b.get("DataClasses", [])
            password_exposed = any("Passwords" in d for d in data_classes)
            year = _parse_year(b.get("BreachDate", ""))
            findings.append({
                "breach_id": f"hibp_{b['Name'].lower()}",
                "breach_name": b.get("Title", b["Name"]),
                "domain": b.get("Domain", ""),
                "year": year,
                "accounts": b.get("PwnCount", 0),
                "severity": _severity_from_classes(data_classes),
                "layer": "legacy_db",
                "layer_name": "Legacy Breach DB",
                "data_classes": data_classes,
                "password_exposed": password_exposed,
                "discovered": b.get("BreachDate", str(year) + "-01-01"),
                "source": "HIBP",
                "live": True,
            })
    except Exception:
        pass
    return findings


# =============================================================================
# Pastebin public scrape  –  https://pastebin.com
# No API key needed.  Scans the most recent 250 public pastes for mentions.
# =============================================================================
async def check_pastebin(identifier: str) -> List[dict]:
    """
    Search recent public Pastebin pastes for the identifier (email or domain).
    Returns paste-site findings (surface_web layer).
    """
    findings = []
    try:
        async with httpx.AsyncClient(timeout=_LONG) as client:
            # fetch recent public pastes index
            r = await client.get(
                "https://scrape.pastebin.com/api_scraping.php?limit=250",
                headers={"User-Agent": _UA},
            )
            if r.status_code != 200:
                return []
            pastes = r.json()

        domain = identifier.split("@")[-1] if "@" in identifier else identifier
        pattern = re.compile(re.escape(identifier) + "|" + re.escape(domain), re.I)
        hits = [p for p in pastes if pattern.search(p.get("key", "") + p.get("title", ""))]

        # Fetch content of up to 5 matching pastes
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            tasks = [
                client.get(f"https://scrape.pastebin.com/api_scrape_item.php?i={p['key']}",
                           headers={"User-Agent": _UA})
                for p in hits[:5]
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

        content_hits = []
        for p, resp in zip(hits[:5], responses):
            if isinstance(resp, Exception):
                continue
            if resp.status_code == 200 and pattern.search(resp.text):
                content_hits.append(p)

        if content_hits:
            findings.append({
                "breach_id": "pastebin_live",
                "breach_name": f"Pastebin — {len(content_hits)} paste(s)",
                "domain": "pastebin.com",
                "year": time.localtime().tm_year,
                "accounts": len(content_hits),
                "severity": 3,
                "layer": "surface_web",
                "layer_name": "Surface Web",
                "data_classes": ["Email addresses", "Plaintext data"],
                "password_exposed": False,
                "discovered": _today(),
                "source": "Pastebin",
                "live": True,
                "paste_urls": [f"https://pastebin.com/{p['key']}" for p in content_hits],
            })
    except Exception:
        pass
    return findings


# =============================================================================
# Ahmia.fi  –  https://ahmia.fi
# Free, no API key, no Tor daemon.  Clearnet dark-web search engine.
# Indexes .onion sites and makes them searchable over HTTPS.
# =============================================================================
async def check_ahmia(identifier: str) -> List[dict]:
    """
    Search Ahmia's clearnet dark-web index for the identifier.
    Results indicate the identifier has been mentioned on .onion services.
    """
    findings = []
    try:
        async with httpx.AsyncClient(timeout=_LONG, follow_redirects=True) as client:
            r = await client.get(
                "https://ahmia.fi/search/",
                params={"q": identifier},
                headers={"User-Agent": _UA},
            )
        if r.status_code != 200:
            return []

        # Count result entries in the HTML (each result has class="result")
        count = len(re.findall(r'class=["\']result["\']', r.text))
        if count == 0:
            # fallback: count <h4> tags which wrap result titles
            count = len(re.findall(r'<h4>', r.text))

        if count > 0:
            # extract .onion domains mentioned
            onion_domains = list(set(re.findall(r'[\w-]+\.onion', r.text)))[:8]
            findings.append({
                "breach_id": "ahmia_live",
                "breach_name": f"Dark Web — {count} result(s) on Ahmia",
                "domain": "ahmia.fi",
                "year": time.localtime().tm_year,
                "accounts": count,
                "severity": 4,
                "layer": "dark_web",
                "layer_name": "Dark Web Market",
                "data_classes": ["Email addresses", "Leaked data"],
                "password_exposed": False,
                "discovered": _today(),
                "source": "Ahmia (dark-web indexer)",
                "live": True,
                "onion_domains": onion_domains,
            })
    except Exception:
        pass
    return findings


# =============================================================================
# Orchestrator
# =============================================================================
async def live_scan(
    identifier: str,
    kind: str = "email",
    hibp_api_key: Optional[str] = None,
) -> List[dict]:
    """
    Run all live intelligence sources concurrently and return merged findings.
    Safe to call even when sources are unavailable — errors are swallowed.
    """
    tasks = [
        check_xposedornot(identifier) if kind == "email" else asyncio.coroutine(lambda: [])(),
        check_hibp(identifier, hibp_api_key) if (kind == "email" and hibp_api_key) else _noop(),
        check_pastebin(identifier),
        check_ahmia(identifier),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    merged: List[dict] = []
    seen_ids: set = set()
    for chunk in results:
        if isinstance(chunk, Exception) or not chunk:
            continue
        for f in chunk:
            bid = f.get("breach_id", "")
            if bid not in seen_ids:
                seen_ids.add(bid)
                merged.append(f)
    merged.sort(key=lambda f: (f.get("severity", 0), f.get("year", 0)), reverse=True)
    return merged


# ── helpers ───────────────────────────────────────────────────────────────────
async def _noop():
    return []


def _parse_year(s: str) -> int:
    m = re.search(r'(\d{4})', str(s))
    return int(m.group(1)) if m else time.localtime().tm_year


def _parse_int(v) -> int:
    try:
        return int(str(v).replace(",", "").replace(".", ""))
    except Exception:
        return 0


def _severity_from_classes(data_classes: List[str]) -> int:
    dc = " ".join(data_classes).lower()
    if any(w in dc for w in ["password", "ssn", "social security", "credit card", "passport"]):
        return 4
    if any(w in dc for w in ["phone", "address", "date of birth", "dob"]):
        return 3
    if "email" in dc:
        return 2
    return 2


def _today() -> str:
    t = time.localtime()
    return f"{t.tm_year}-{t.tm_mon:02d}-{t.tm_mday:02d}"
