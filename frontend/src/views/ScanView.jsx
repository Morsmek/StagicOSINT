import React, { useState } from 'react'
import { api, sha256Hex } from '../lib/api'
import { C, Card, Badge, Button, Input, Spinner, RiskRing, bandColor, fmtNum } from '../components/ui'
import { Header, SectionTitle } from './Dashboard'

const SAMPLES = ['john.doe@acme.com', 'admin@company.com', 'ceo@bigcorp.com']
const LAYER_ORDER = ['surface_web', 'legacy_db', 'deep_web_db', 'forum', 'dark_web']

export function ScanView({ toast, refreshAlerts, go }) {
  const [identifier, setIdentifier] = useState('')
  const [kind, setKind] = useState('email')
  const [monitor, setMonitor] = useState(false)
  const [hashPreview, setHashPreview] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  async function onChange(v) {
    setIdentifier(v)
    if (v.trim()) setHashPreview(await sha256Hex(v))
    else setHashPreview('')
  }

  async function runScan() {
    if (!identifier.trim()) return
    setLoading(true); setResult(null)
    try {
      const r = await api.scan({ identifier, kind, monitor })
      setResult(r)
      refreshAlerts()
      const band = r.risk.band
      toast(`Scan complete — ${band} risk (${r.findings.length} exposures)`,
        band === 'Clear' || band === 'Low' ? 'success' : 'error')
    } catch (e) {
      toast('Scan failed: ' + (e.response?.data?.detail || e.message), 'error')
    } finally { setLoading(false) }
  }

  return (
    <div>
      <Header title="Zero-Knowledge Breach Scan"
        sub="Correlate an identity against five intelligence layers. The plaintext value is hashed in your browser — only the SHA-256 digest is transmitted." />

      <Card style={{ marginBottom: 22 }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
          {['email', 'domain'].map((k) => (
            <button key={k} onClick={() => setKind(k)} style={{
              padding: '6px 16px', borderRadius: 8, fontSize: 12.5, fontWeight: 700, cursor: 'pointer',
              textTransform: 'capitalize',
              background: kind === k ? C.gold + '22' : 'transparent',
              border: `1px solid ${kind === k ? C.gold + '66' : C.border2}`,
              color: kind === k ? C.gold : C.muted,
            }}>{k}</button>
          ))}
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <Input value={identifier} onChange={onChange} onEnter={runScan}
            placeholder={kind === 'email' ? 'name@company.com' : 'company.com'} />
          <Button onClick={runScan} disabled={loading || !identifier.trim()} size="lg" style={{ whiteSpace: 'nowrap' }}>
            {loading ? <Spinner color="#1a1a12" /> : 'Run Scan'}
          </Button>
        </div>

        {/* Zero-knowledge hash preview */}
        {hashPreview && (
          <div style={{
            marginTop: 14, padding: '10px 14px', background: C.bg, borderRadius: 8,
            border: `1px solid ${C.border}`, display: 'flex', alignItems: 'center', gap: 10,
          }}>
            <Badge color={C.clear}>ZK</Badge>
            <span style={{ fontSize: 11.5, color: C.faint }}>Transmitted digest:</span>
            <code style={{ fontSize: 11.5, color: C.gold, fontFamily: 'monospace', wordBreak: 'break-all' }}>
              {hashPreview.slice(0, 32)}…
            </code>
          </div>
        )}

        <label style={{ display: 'flex', alignItems: 'center', gap: 9, marginTop: 14, cursor: 'pointer', width: 'fit-content' }}>
          <input type="checkbox" checked={monitor} onChange={(e) => setMonitor(e.target.checked)}
            style={{ accentColor: C.gold, width: 15, height: 15 }} />
          <span style={{ fontSize: 12.5, color: C.muted }}>Add to continuous monitoring after scan</span>
        </label>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 11.5, color: C.faint }}>Try:</span>
          {SAMPLES.map((s) => (
            <button key={s} onClick={() => onChange(s)} style={{
              background: C.surface2, border: `1px solid ${C.border2}`, borderRadius: 6,
              color: C.muted, fontSize: 11.5, padding: '4px 10px', cursor: 'pointer',
            }}>{s}</button>
          ))}
        </div>
      </Card>

      {result && <ScanResult result={result} />}
    </div>
  )
}

function ScanResult({ result }) {
  const { risk, findings, label } = result
  const byLayer = LAYER_ORDER.map((lid) => ({
    layer: result.layers.find((l) => l.id === lid),
    hits: findings.filter((f) => f.layer === lid),
  }))

  return (
    <div style={{ animation: 'fadeIn .3s ease' }}>
      {/* Summary */}
      <Card style={{ marginBottom: 18, display: 'flex', alignItems: 'center', gap: 26 }}>
        <RiskRing score={risk.score} band={risk.band} size={104} />
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 18, fontWeight: 800, color: C.text }}>{label}</span>
            <Badge color={bandColor(risk.band)} filled>{risk.band} Risk</Badge>
          </div>
          <div style={{ fontSize: 13.5, color: C.muted, marginTop: 8 }}>
            {findings.length === 0
              ? 'No exposures found across monitored layers.'
              : `Found in ${findings.length} breach${findings.length > 1 ? 'es' : ''} across ${risk.exposed_layers.length} intelligence layer${risk.exposed_layers.length > 1 ? 's' : ''}.`}
          </div>
          <div style={{ display: 'flex', gap: 18, marginTop: 14 }}>
            <Stat label="Exposures" value={findings.length} />
            <Stat label="Credentials Leaked" value={risk.credentials_exposed ? 'Yes' : 'No'}
              color={risk.credentials_exposed ? C.critical : C.clear} />
            <Stat label="Ledger Txn" value={result.txn_key?.slice(0, 12) + '…'} mono />
          </div>
        </div>
      </Card>

      {/* Multi-layer breakdown */}
      <SectionTitle>Multi-Layer Scan Results</SectionTitle>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: 10, margin: '14px 0 22px' }}>
        {byLayer.map(({ layer, hits }) => (
          <div key={layer.id} style={{
            background: C.surface, borderRadius: 10, padding: 14,
            border: `1px solid ${hits.length ? bandColor('High') + '44' : C.border}`,
          }}>
            <div style={{ fontSize: 11, color: C.faint, textTransform: 'uppercase', letterSpacing: 0.5, minHeight: 28 }}>{layer.name}</div>
            <div style={{ fontSize: 26, fontWeight: 800, color: hits.length ? C.high : C.clear, marginTop: 6 }}>{hits.length}</div>
            <div style={{ fontSize: 11, color: C.faint }}>{hits.length ? 'exposures' : 'clear'}</div>
          </div>
        ))}
      </div>

      {/* Findings detail */}
      {findings.length > 0 && (
        <>
          <SectionTitle>Exposure Detail</SectionTitle>
          <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
            {findings.map((f) => (
              <Card key={f.breach_id} pad={16}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                      <span style={{ fontSize: 15, fontWeight: 700, color: C.text }}>{f.breach_name}</span>
                      <Badge color={C.faint}>{f.layer_name}</Badge>
                      {f.password_exposed && <Badge color={C.critical}>Credentials</Badge>}
                    </div>
                    <div style={{ fontSize: 12, color: C.faint, marginTop: 5 }}>
                      {f.domain} · {f.year} · {fmtNum(f.accounts)} accounts · discovered {f.discovered}
                    </div>
                    <div style={{ display: 'flex', gap: 6, marginTop: 10, flexWrap: 'wrap' }}>
                      {f.data_classes.map((dc) => (
                        <span key={dc} style={{
                          fontSize: 11, color: C.muted, background: C.bg, border: `1px solid ${C.border}`,
                          borderRadius: 5, padding: '2px 8px',
                        }}>{dc}</span>
                      ))}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 2 }}>
                    {[1, 2, 3, 4, 5].map((i) => (
                      <span key={i} style={{
                        width: 5, height: 18, borderRadius: 2,
                        background: i <= f.severity ? bandColor(f.severity >= 4 ? 'Critical' : f.severity >= 3 ? 'High' : 'Medium') : C.border,
                      }} />
                    ))}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function Stat({ label, value, color, mono }) {
  return (
    <div>
      <div style={{ fontSize: 10.5, color: C.faint, textTransform: 'uppercase', letterSpacing: 0.6 }}>{label}</div>
      <div style={{ fontSize: 15, fontWeight: 700, color: color || C.text, marginTop: 3, fontFamily: mono ? 'monospace' : 'inherit' }}>{value}</div>
    </div>
  )
}
