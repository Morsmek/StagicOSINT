"""
SDBA - Stagic Data Breach Alert platform.

A privacy-preserving, multi-layer breach detection engine implementing the
core capabilities described in the SDBA Enterprise Whitepaper:

  * Zero-knowledge scanning   - identifiers are hashed (SHA-256) in the client;
                                the plaintext never reaches the server.
  * Multi-layer intelligence  - surface web, legacy breach DBs, deep web DBs,
                                underground forums and dark-web markets.
  * Risk scoring              - weighted by severity, recency, exposed data
                                classes and the layer a finding surfaced on.
  * Scan-by-Proxy             - third-party / supply-chain monitoring.
  * Immutable audit ledger    - tamper-evident SHA-256 hash chain with a
                                "blockchain transaction key" per entry.
"""
