"""
Breach threat-intelligence catalog and the deterministic correlation engine.

The catalog below is a curated set of well-documented, real-world breaches used
as the reference intelligence for the demo. Correlation is *deterministic*: a
given identifier hash always yields the same findings, but different hashes
yield different, plausible results. This mirrors how a real platform correlates
an identity against many sources without storing the plaintext identity.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import List


# The five intelligence layers SDBA monitors (whitepaper: Multi-Layer Framework)
LAYERS = [
    {"id": "surface_web",  "name": "Surface Web",          "weight": 1.0},
    {"id": "legacy_db",    "name": "Legacy Breach DB",     "weight": 1.2},
    {"id": "deep_web_db",  "name": "Deep Web Database",    "weight": 1.6},
    {"id": "forum",        "name": "Underground Forum",    "weight": 2.0},
    {"id": "dark_web",     "name": "Dark Web Market",      "weight": 2.4},
]
LAYER_BY_ID = {l["id"]: l for l in LAYERS}


@dataclass
class Breach:
    id: str
    name: str
    domain: str
    year: int
    accounts: int          # records exposed
    severity: int          # 1-5
    prevalence: int        # 0-100, how commonly an identity appears here
    layer: str             # primary layer this breach surfaces on
    data_classes: List[str] = field(default_factory=list)


# Curated reference catalog (figures are public, widely reported approximations).
CATALOG: List[Breach] = [
    Breach("collection1", "Collection #1", "various", 2019, 772_904_991, 4, 55,
           "forum", ["Email addresses", "Passwords"]),
    Breach("linkedin2021", "LinkedIn Scrape", "linkedin.com", 2021, 700_000_000, 3, 42,
           "deep_web_db", ["Email addresses", "Names", "Phone numbers", "Geolocation"]),
    Breach("facebook2019", "Facebook", "facebook.com", 2019, 533_000_000, 3, 40,
           "surface_web", ["Email addresses", "Names", "Phone numbers", "Genders"]),
    Breach("adobe2013", "Adobe", "adobe.com", 2013, 152_000_000, 4, 30,
           "legacy_db", ["Email addresses", "Password hints", "Passwords"]),
    Breach("canva2019", "Canva", "canva.com", 2019, 137_000_000, 2, 22,
           "surface_web", ["Email addresses", "Names", "Usernames", "Geolocation"]),
    Breach("dropbox2012", "Dropbox", "dropbox.com", 2012, 68_700_000, 3, 18,
           "legacy_db", ["Email addresses", "Passwords"]),
    Breach("myspace2008", "MySpace", "myspace.com", 2008, 359_000_000, 2, 20,
           "legacy_db", ["Email addresses", "Passwords", "Usernames"]),
    Breach("tumblr2013", "Tumblr", "tumblr.com", 2013, 65_000_000, 2, 15,
           "legacy_db", ["Email addresses", "Passwords"]),
    Breach("twitter2023", "Twitter", "twitter.com", 2023, 200_000_000, 3, 25,
           "deep_web_db", ["Email addresses", "Names", "Usernames", "Follower counts"]),
    Breach("ticketmaster24", "Ticketmaster", "ticketmaster.com", 2024, 560_000_000, 4, 17,
           "dark_web", ["Email addresses", "Names", "Phone numbers", "Partial card data"]),
    Breach("at_t_2024", "AT&T", "att.com", 2024, 73_000_000, 4, 12,
           "dark_web", ["Email addresses", "Names", "Phone numbers", "SSNs", "Account data"]),
    Breach("zynga2019", "Zynga", "zynga.com", 2019, 172_000_000, 2, 14,
           "deep_web_db", ["Email addresses", "Passwords", "Usernames", "Phone numbers"]),
    Breach("wattpad2020", "Wattpad", "wattpad.com", 2020, 270_000_000, 2, 13,
           "forum", ["Email addresses", "Passwords", "Names", "Geolocation"]),
    Breach("chegg2018", "Chegg", "chegg.com", 2018, 40_000_000, 2, 9,
           "legacy_db", ["Email addresses", "Passwords", "Usernames"]),
    Breach("evite2019", "Evite", "evite.com", 2019, 101_000_000, 2, 8,
           "deep_web_db", ["Email addresses", "Names", "Phone numbers", "Dates of birth"]),
    Breach("dubsmash2018", "Dubsmash", "dubsmash.com", 2018, 162_000_000, 2, 10,
           "forum", ["Email addresses", "Passwords", "Usernames"]),
    Breach("lastpass2022", "LastPass", "lastpass.com", 2022, 30_000_000, 5, 6,
           "dark_web", ["Email addresses", "Encrypted vaults", "Billing addresses"]),
    Breach("experian2015", "Experian / T-Mobile", "experian.com", 2015, 15_000_000, 5, 5,
           "dark_web", ["Names", "SSNs", "Dates of birth", "ID document numbers"]),
    Breach("marriott2018", "Marriott", "marriott.com", 2018, 500_000_000, 4, 11,
           "deep_web_db", ["Email addresses", "Names", "Passport numbers", "Travel data"]),
    Breach("yahoo2013", "Yahoo", "yahoo.com", 2013, 3_000_000_000, 4, 35,
           "legacy_db", ["Email addresses", "Passwords", "Security questions", "Dates of birth"]),
]
CATALOG_BY_ID = {b.id: b for b in CATALOG}


def _hash_int(*parts: str) -> int:
    """Stable 0..2^256 integer from the given string parts."""
    h = hashlib.sha256("::".join(parts).encode()).hexdigest()
    return int(h, 16)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()


def correlate(identifier_hash: str) -> List[dict]:
    """
    Deterministically correlate an identifier hash against the catalog.

    Returns a list of finding dicts. The same hash always returns the same set,
    different hashes return different, plausible sets.
    """
    findings: List[dict] = []
    for b in CATALOG:
        roll = _hash_int(identifier_hash, b.id) % 100
        if roll >= b.prevalence:
            continue
        # Spread the discovery date deterministically across the months since the breach.
        month = (_hash_int(identifier_hash, b.id, "m") % 12) + 1
        day = (_hash_int(identifier_hash, b.id, "d") % 27) + 1
        password_exposed = any("Password" in dc for dc in b.data_classes)
        findings.append({
            "breach_id": b.id,
            "breach_name": b.name,
            "domain": b.domain,
            "year": b.year,
            "accounts": b.accounts,
            "severity": b.severity,
            "layer": b.layer,
            "layer_name": LAYER_BY_ID[b.layer]["name"],
            "data_classes": b.data_classes,
            "password_exposed": password_exposed,
            "discovered": f"{b.year}-{month:02d}-{day:02d}",
        })
    # Most severe / most recent first
    findings.sort(key=lambda f: (f["severity"], f["year"]), reverse=True)
    return findings


def score_risk(findings: List[dict]) -> dict:
    """
    Compute a 0-100 risk score and band from a set of findings.

    Weighted by severity, the layer the finding surfaced on (dark web counts
    far more than surface web) and whether credentials were exposed.
    """
    if not findings:
        return {"score": 0, "band": "Clear", "exposed_layers": [], "credentials_exposed": False}

    raw = 0.0
    layers = set()
    creds = False
    for f in findings:
        layers.add(f["layer"])
        lw = LAYER_BY_ID[f["layer"]]["weight"]
        sev = f["severity"]
        contrib = sev * lw
        if f["password_exposed"]:
            contrib *= 1.3
            creds = True
        raw += contrib

    # Compress with diminishing returns so a handful of findings doesn't peg 100.
    score = int(round(100 * (1 - 0.965 ** raw)))
    score = max(1, min(100, score))

    if score >= 80:
        band = "Critical"
    elif score >= 55:
        band = "High"
    elif score >= 25:
        band = "Medium"
    else:
        band = "Low"

    return {
        "score": score,
        "band": band,
        "exposed_layers": sorted(layers),
        "credentials_exposed": creds,
    }
