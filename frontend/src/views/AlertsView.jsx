import React, { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { C, Card, Badge, Button, Spinner, sevColor, fmtTime, Empty } from '../components/ui'
import { Header, Center } from './Dashboard'

export function AlertsView({ toast, refreshAlerts }) {
  const [alerts, setAlerts] = useState(null)
  const [filter, setFilter] = useState('open')

  const load = () => api.alerts(false).then(setAlerts).catch(() => setAlerts([]))
  useEffect(() => { load() }, [])

  async function ack(id) {
    try { await api.ackAlert(id); await load(); refreshAlerts() }
    catch { toast('Failed to acknowledge', 'error') }
  }
  async function ackAll() {
    try { await api.ackAll(); await load(); refreshAlerts(); toast('All alerts acknowledged', 'success') }
    catch { toast('Failed', 'error') }
  }

  const shown = (alerts || []).filter((a) => filter === 'all' || !a.acknowledged)
  const openCount = (alerts || []).filter((a) => !a.acknowledged).length

  return (
    <div>
      <Header title="Breach Alerts"
        sub="Incidents raised when an identity surfaces on a high-risk layer or has credentials exposed." />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          {[['open', 'Open'], ['all', 'All']].map(([id, lbl]) => (
            <button key={id} onClick={() => setFilter(id)} style={{
              padding: '6px 16px', borderRadius: 8, fontSize: 12.5, fontWeight: 700, cursor: 'pointer',
              background: filter === id ? C.gold + '22' : 'transparent',
              border: `1px solid ${filter === id ? C.gold + '66' : C.border2}`,
              color: filter === id ? C.gold : C.muted,
            }}>{lbl}{id === 'open' && openCount > 0 ? ` (${openCount})` : ''}</button>
          ))}
        </div>
        {openCount > 0 && <Button variant="ghost" size="sm" onClick={ackAll}>Acknowledge all</Button>}
      </div>

      {!alerts ? <Center><Spinner size={22} /></Center>
        : shown.length === 0 ? (
          <Card><Empty icon="⚑" title={filter === 'open' ? 'No open alerts' : 'No alerts'}
            sub="Breach detections will appear here as they surface across monitored layers." /></Card>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
            {shown.map((a) => (
              <Card key={a.id} pad={15} style={{ opacity: a.acknowledged ? 0.55 : 1, borderLeft: `3px solid ${sevColor(a.severity)}` }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 9, flexWrap: 'wrap' }}>
                      <Badge color={sevColor(a.severity)} filled>{a.severity}</Badge>
                      <span style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{a.title}</span>
                      {a.kind === 'vendor' && <Badge color={C.faint}>Supply Chain</Badge>}
                    </div>
                    <div style={{ fontSize: 12.5, color: C.muted, marginTop: 6 }}>{a.detail}</div>
                    <div style={{ fontSize: 11, color: C.faint, marginTop: 6 }}>{fmtTime(a.created_at)}</div>
                  </div>
                  {a.acknowledged
                    ? <Badge color={C.clear}>Acknowledged</Badge>
                    : <Button variant="ghost" size="sm" onClick={() => ack(a.id)}>Acknowledge</Button>}
                </div>
              </Card>
            ))}
          </div>
        )}
    </div>
  )
}
