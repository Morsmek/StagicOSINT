# OGI - Open Graph Intelligence

An open-source link analysis and OSINT framework built with FastAPI (backend) and React (frontend). Discover relationships between entities through intelligent transforms.

## Features

- **Graph-based entity modeling**: Nodes (entities) and edges (relationships)
- **9+ transform modules**: DNS, IP geolocation, SSL certificates, email discovery, social media, hashes, web scraping, and more
- **Interactive visualization**: React Flow-based graph canvas with drag-and-drop
- **Multi-graph workspace**: Manage multiple investigations simultaneously
- **API key management**: Securely store keys for external services (Shodan, VirusTotal, Hunter.io, etc.)
- **MTGX export/import**: Portable graph format for sharing
- **Force-directed layout**: Auto-arrange nodes for clarity
- **Dark theme UI**: Modern, easy-on-the-eyes interface

## Quick Start

### Using Docker Compose (recommended)

```bash
docker-compose up
```

Then open http://localhost:5173 in your browser.

Backend API: http://localhost:8000
Frontend: http://localhost:5173

### Local Development

**Backend:**
```bash
cd backend
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
ogi/
├── backend/
│   ├── config.py           # Configuration and settings
│   ├── models.py           # Pydantic data models
│   ├── database.py         # SQLite async database layer
│   ├── graph_engine.py     # Graph analysis (centrality, paths, layout)
│   ├── transform_engine.py # Transform discovery and execution
│   ├── main.py             # FastAPI app entry point
│   ├── cli.py              # Command-line interface
│   ├── routers/            # API route handlers
│   │   ├── graphs.py
│   │   ├── entities.py
│   │   ├── transforms.py
│   │   └── api_keys.py
│   ├── transforms/         # Transform modules (plugins)
│   │   ├── base.py
│   │   ├── dns.py
│   │   ├── ip.py
│   │   ├── ssl.py
│   │   ├── email.py
│   │   ├── hash.py
│   │   ├── web.py
│   │   └── social.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api/
│   │   │   └── client.js   # Axios API client
│   │   ├── store/
│   │   │   └── index.js    # Zustand state store
│   │   └── components/
│   │       ├── Toolbar.jsx
│   │       ├── Sidebar.jsx
│   │       ├── GraphCanvas.jsx
│   │       ├── EntityNode.jsx
│   │       ├── Toast.jsx
│   │       └── panels/
│   │           ├── GraphsPanel.jsx
│   │           ├── EntityPanel.jsx
│   │           ├── TransformPanel.jsx
│   │           └── ApiKeysPanel.jsx
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
├── docker-compose.yml
└── README.md
```

## Available Transforms

### DNS
- **dns_resolve**: Domain → IP addresses
- **dns_reverse**: IP address → Domain (reverse DNS)
- **dns_mx**: Domain → MX records
- **dns_ns**: Domain → Nameservers
- **dns_subdomains**: Domain → Subdomains (brute-force common list)

### IP / Network
- **ip_geolocate**: IP → Location + ISP (ip-api.com, free)
- **ip_whois**: IP → Organization + CIDR blocks (requires ipwhois library)
- **ip_shodan**: IP → Open ports + services (requires SHODAN_API_KEY)

### SSL / TLS
- **ssl_certificate**: Domain/IP → SSL certificate + subject + SANs

### Email
- **email_domain**: Email → Domain
- **email_verify**: Email → MX records (verification)
- **email_hunter**: Domain → Email addresses (requires HUNTER_API_KEY)
- **email_prospeo**: Person → Professional email address using Prospeo Enrich Person API (requires PROSPEO_API_KEY). Add person/company details as entity properties such as `full_name`, `company_name`, `company_website`, or `linkedin_url`.

### Hashes
- **hash_virustotal**: File hash → Malware info (requires VIRUSTOTAL_API_KEY)

### Web
- **web_scrape**: URL → Linked domains, emails, social profiles
- **web_headers**: URL → HTTP headers

### Social Media
- **username_search**: Username → Profiles across platforms

## API Endpoints

All endpoints under `/api/v1/`:

### Graphs
- `GET /graphs` - List all graphs
- `POST /graphs` - Create graph
- `GET /graphs/{id}` - Get graph with entities + edges
- `DELETE /graphs/{id}` - Delete graph
- `GET /graphs/{id}/stats` - Graph statistics
- `GET /graphs/{id}/layout` - Compute force-directed layout
- `GET /graphs/{id}/path?source_id=X&target_id=Y` - Shortest path
- `POST /graphs/{id}/import` - Import MTGX JSON
- `GET /graphs/{id}/export` - Export MTGX JSON

### Entities
- `POST /graphs/{id}/entities` - Create entity
- `GET /graphs/{id}/entities` - List entities
- `PATCH /graphs/{id}/entities/{eid}` - Update entity
- `DELETE /graphs/{id}/entities/{eid}` - Delete entity

### Edges
- `POST /graphs/{id}/edges` - Create edge
- `DELETE /graphs/{id}/edges/{eid}` - Delete edge

### Transforms
- `GET /transforms` - List all available transforms
- `GET /transforms/for/{type}` - List transforms for entity type
- `POST /transforms/run` - Execute a transform

### API Keys
- `GET /api-keys` - List stored keys (masked)
- `POST /api-keys` - Add/update key
- `DELETE /api-keys/{id}` - Delete key

## Configuration

Backend configuration via environment variables or `.env`:

```env
# Core
APP_NAME=OGI - Open Graph Intelligence
APP_VERSION=1.0.0
DEBUG=True

# Database
DATABASE_URL=sqlite+aiosqlite:///./ogi.db

# CORS
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# Optional API Keys
SHODAN_API_KEY=
VIRUSTOTAL_API_KEY=
HUNTER_API_KEY=
PROSPEO_API_KEY=
IPINFO_TOKEN=
OPENCAGE_API_KEY=

# Optional: AI features
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

## Architecture

### Backend Stack
- **FastAPI**: Modern async Python web framework
- **Pydantic**: Data validation and serialization
- **aiosqlite**: Async SQLite with async/await syntax
- **httpx**: Async HTTP client for external API calls

### Frontend Stack
- **React 18**: UI library with hooks
- **Vite**: Fast build tool and dev server
- **React Flow**: Interactive graph visualization
- **Zustand**: Lightweight state management
- **Axios**: HTTP client
- **Tailwind CSS**: Utility-first styling (via inline styles in this version)

## License

MIT License. See LICENSE file for details.

## Contributing

Contributions welcome! Please submit pull requests and open issues for bugs or feature requests.
