# SDBA — Stagic Data Breach Alert

A proactive, **zero-knowledge** data-breach detection platform. SDBA correlates
identities against five layers of breach intelligence — surface web, legacy
breach databases, deep-web databases, underground forums and dark-web markets —
without the plaintext identifier ever leaving the browser.

Built with FastAPI (backend) and React + Vite (frontend), implementing the core
capabilities from the SDBA Enterprise Whitepaper.

## Features

- **Zero-Knowledge Breach Scan** — identifiers are hashed with SHA-256 in the
  browser (Web Crypto API); only the digest is transmitted to the server.
- **Multi-Layer Intelligence** — every scan is correlated across five layers:
  Surface Web, Legacy Breach DB, Deep Web Database, Underground Forum and Dark
  Web Market.
- **Risk Scoring** — a 0–100 score (Clear → Critical) weighted by severity,
  recency, exposed data classes and the layer a finding surfaced on.
- **Continuous Monitoring** — register employee emails or company domains as
  monitored assets; only their hashes are stored.
- **Scan-by-Proxy (Supply Chain)** — track vendor / partner domains and score
  third-party breach exposure. 62% of enterprise breaches start with a vendor.
- **Breach Alerts** — incidents raised automatically when an identity surfaces
  on a high-risk layer or has credentials exposed; acknowledge and triage.
- **Immutable Audit Ledger** — every action is sealed into a SHA-256 hash chain
  with a per-entry "blockchain transaction key", verifiable for tamper-evidence.
- **Threat Intelligence Catalog** — a reference corpus of 20 documented breaches
  (3.8B+ records) browsable by layer.
- **Logo-matched theme** — the SDBA gray (`#b8b8b0`) and champagne-gold
  (`#d8c898`) palette is used throughout.

## Quick Start

### Docker Compose
```bash
docker-compose up
```
Open http://localhost:5173 (frontend) — the backend API runs on http://localhost:8000.

### Local Development

**Backend**
```bash
cd backend
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. The Vite dev server proxies `/api` to the backend.

### Single-process (backend serves the built UI)
```bash
cd frontend && npm install && npm run build
cd ../backend && uvicorn main:app --port 8000
```
Open http://localhost:8000 — FastAPI serves the React build and the API together.

## How the Zero-Knowledge Scan Works

1. You type an email or domain in the browser.
2. The client computes `SHA-256(lowercased identifier)` via the Web Crypto API.
3. Only the 64-char hex digest + a masked label (e.g. `j*****@acme.com`) is sent.
4. The server correlates the digest against the breach catalog and returns
   findings, a risk score and a multi-layer breakdown.

The plaintext identifier never leaves your machine, and monitored assets are
persisted by hash only.

## API

All SDBA endpoints live under `/api/v1/sdba`:

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/scan` | Zero-knowledge breach scan (`hash` or `identifier`) |
| `GET`  | `/dashboard` | Aggregate metrics, risk distribution, layer findings |
| `GET`/`POST`/`DELETE` | `/assets` … | Monitored identities |
| `POST` | `/assets/{id}/rescan` | Re-run correlation for an asset |
| `GET`/`POST`/`DELETE` | `/vendors` … | Supply-chain (scan-by-proxy) |
| `POST` | `/vendors/{id}/scan` | Re-scan a vendor domain |
| `GET`  | `/alerts` · `POST /alerts/{id}/ack` | Breach alerts |
| `GET`  | `/audit` · `GET /audit/verify` | Hash-chain audit ledger |
| `GET`  | `/catalog` | Breach intelligence catalog |

Interactive docs: http://localhost:8000/docs

## Architecture

```
backend/
├── main.py              # FastAPI entry point (mounts SDBA router + React build)
├── config.py
└── sdba/
    ├── intel.py         # Breach catalog + deterministic correlation + risk scoring
    ├── db.py            # Async SQLite persistence + SHA-256 audit hash chain
    └── router.py        # SDBA REST API

frontend/
├── public/sdba-logo.png # App logo (used as wordmark + favicon)
└── src/
    ├── App.jsx          # Sidebar shell, navigation, toasts
    ├── lib/api.js       # API client + browser-side SHA-256 hashing
    ├── components/ui.jsx# Themed primitives (logo palette)
    └── views/           # Dashboard, ScanView, AssetsView, SupplyChainView,
                         #   AlertsView, AuditView, CatalogView
```

> **Note on the intelligence engine:** breach correlation is *deterministic* —
> a given identifier hash always yields the same findings — using a curated
> catalog of real, publicly documented breaches. This makes the demo fully
> functional offline. Wiring in a live source (e.g. an HIBP-style k-anonymity
> range API) is a drop-in replacement for `intel.correlate()`.

## License

MIT License.
