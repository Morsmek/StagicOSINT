import React, { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { C, Card, Badge, Spinner, sevColor, bandColor, fmtTime, Empty } from '../components/ui'

const LAYER_COLORS = ['#8fae8f', '#b8b8b0', '#d8c898', '#e0a35c', '#e3756b']

export function Dashboard({ go }) {
  const [data, setData] = useState(null)
  useEffect(() => { api.dashboard().then(setData).catch(() => {}) }, [])

  if (!data) return <Center><Spinner size={24} /></Center>

  const m = data.metrics
  const p = data.platform
  const maxLayer = Math.max(1, ...data.layer_findings.map((l) => l.count))
  const totalAssets = Object.values(data.risk_distribution).reduce((a, b) => a + b, 0)

  return (
    <div>
      <Header title="Threat Overview"
        sub="Real-time, zero-knowledge breach posture across all monitored layers." />

      {/* Platform headline metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 14 }}>
        <Kpi label="Mean Detection Time" value={p.detection_time} accent
          sub="vs. 194 days industry avg" />
        <Kpi label="Classification Accuracy" value={p.accuracy} sub="1.8% false-positive rate" />
        <Kpi label="Intelligence Layers" value={p.monitored_layers} sub="surface → dark web" />
        <Kpi label="Open Alerts" value={m.open_alerts}
          valueColor={m.open_alerts > 0 ? C.high : C.clear}
          sub={`${m.critical_alerts} critical`} />
      </div>

      {/* Operational counts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 22 }}>
        <Kpi label="Monitored Assets" value={m.monitored_assets} small />
        <Kpi label="Tracked Vendors" value={m.tracked_vendors} small />
        <Kpi label="Total Scans" value={m.total_scans} small />
        <Kpi label="Avg Asset Risk" value={m.avg_risk}
          valueColor={m.avg_risk >= 55 ? C.high : C.medium} small />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.15fr 1fr', gap: 18, marginBottom: 18 }}>
        {/* Layer findings */}
        <Card>
          <SectionTitle>Findings by Intelligence Layer</SectionTitle>
          {data.layer_findings.every((l) => l.count === 0) ? (
            <Empty icon="☷" title="No findings yet" sub="Run a breach scan to populate layer intelligence." />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 13, marginTop: 16 }}>
              {data.layer_findings.map((l, i) => (
                <div key={l.id}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, marginBottom: 5 }}>
                    <span style={{ color: C.muted }}>{l.name}</span>
                    <span style={{ color: C.text, fontWeight: 700 }}>{l.count}</span>
                  </div>
                  <div style={{ height: 7, background: C.bg, borderRadius: 999, overflow: 'hidden' }}>
                    <div style={{
                      width: `${(l.count / maxLayer) * 100}%`, height: '100%',
                      background: LAYER_COLORS[i], borderRadius: 999, transition: 'width .6s ease',
                    }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Risk distribution */}
        <Card>
          <SectionTitle>Asset Risk Distribution</SectionTitle>
          {totalAssets === 0 ? (
            <Empty icon="◉" title="No monitored assets" sub="Add identities to track their breach risk." />
          ) : (
            <div style={{ marginTop: 16 }}>
              <div style={{ display: 'flex', height: 14, borderRadius: 999, overflow: 'hidden', marginBottom: 18 }}>
                {['Critical', 'High', 'Medium', 'Low', 'Clear'].map((b) =>
                  data.risk_distribution[b] > 0 ? (
                    <div key={b} title={`${b}: ${data.risk_distribution[b]}`}
                      style={{ flex: data.risk_distribution[b], background: bandColor(b) }} />
                  ) : null)}
              </div>
              {['Critical', 'High', 'Medium', 'Low', 'Clear'].map((b) => (
                <div key={b} style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 9 }}>
                  <span style={{ width: 9, height: 9, borderRadius: 3, background: bandColor(b) }} />
                  <span style={{ flex: 1, fontSize: 12.5, color: C.muted }}>{b}</span>
                  <span style={{ fontSize: 12.5, fontWeight: 700, color: C.text }}>{data.risk_distribution[b]}</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Recent alerts + ledger */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 18 }}>
        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <SectionTitle>Recent Alerts</SectionTitle>
            <button onClick={() => go('alerts')} style={linkBtn}>View all →</button>
          </div>
          {data.recent_alerts.length === 0 ? (
            <Empty icon="⚑" title="No alerts" sub="You're clear. New breach detections will appear here." />
          ) : (
            <div style={{ marginTop: 12 }}>
              {data.recent_alerts.map((a) => (
                <div key={a.id} style={{
                  display: 'flex', alignItems: 'center', gap: 12, padding: '11px 0',
                  borderBottom: `1px solid ${C.border}`,
                }}>
                  <span style={{ width: 8, height: 8, borderRadius: 999, background: sevColor(a.severity), flexShrink: 0 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, color: C.text, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{a.title}</div>
                    <div style={{ fontSize: 11.5, color: C.faint }}>{a.layer} · {fmtTime(a.created_at)}</div>
                  </div>
                  <Badge color={sevColor(a.severity)}>{a.severity}</Badge>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <SectionTitle>Audit Ledger</SectionTitle>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, marginTop: 18 }}>
            <div style={{
              width: 64, height: 64, borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 30, background: data.ledger.valid ? C.clear + '1e' : C.critical + '1e',
              border: `1px solid ${data.ledger.valid ? C.clear : C.critical}66`,
              color: data.ledger.valid ? C.clear : C.critical,
            }}>{data.ledger.valid ? '⬡' : '⚠'}</div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: data.ledger.valid ? C.clear : C.critical }}>
                {data.ledger.valid ? 'Chain Verified' : 'Chain Tampered'}
              </div>
              <div style={{ fontSize: 12, color: C.faint, marginTop: 3 }}>
                {data.ledger.entries} immutable entries
              </div>
            </div>
            <button onClick={() => go('audit')} style={linkBtn}>Inspect ledger →</button>
          </div>
        </Card>
      </div>
    </div>
  )
}

function Kpi({ label, value, sub, accent, valueColor, small }) {
  return (
    <Card pad={small ? 16 : 20} style={accent ? { borderColor: C.gold + '66', background: `linear-gradient(160deg, ${C.gold}14, ${C.surface})` } : undefined}>
      <div style={{ fontSize: 11, color: C.faint, textTransform: 'uppercase', letterSpacing: 0.8, fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: small ? 26 : 32, fontWeight: 800, color: valueColor || (accent ? C.gold : C.text), marginTop: 6, lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontSize: 11.5, color: C.faint, marginTop: 7 }}>{sub}</div>}
    </Card>
  )
}

export function Header({ title, sub }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <h1 style={{ fontSize: 24, fontWeight: 800, color: C.text, letterSpacing: -0.3 }}>{title}</h1>
      {sub && <p style={{ fontSize: 13.5, color: C.faint, marginTop: 6 }}>{sub}</p>}
    </div>
  )
}

export function SectionTitle({ children }) {
  return <div style={{ fontSize: 12.5, fontWeight: 700, color: C.muted, textTransform: 'uppercase', letterSpacing: 0.8 }}>{children}</div>
}

export function Center({ children }) {
  return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 80 }}>{children}</div>
}

const linkBtn = {
  background: 'none', border: 'none', color: C.gold, fontSize: 12.5, fontWeight: 600,
  cursor: 'pointer', padding: 0,
}
