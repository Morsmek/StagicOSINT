import React, { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { C, Card, Badge, Button, Input, Spinner, bandColor, fmtTime, Empty } from '../components/ui'
import { Header, Center } from './Dashboard'

export function AssetsView({ toast, refreshAlerts }) {
  const [assets, setAssets] = useState(null)
  const [identifier, setIdentifier] = useState('')
  const [kind, setKind] = useState('email')
  const [busy, setBusy] = useState(false)

  const load = () => api.assets().then(setAssets).catch(() => setAssets([]))
  useEffect(() => { load() }, [])

  async function add() {
    if (!identifier.trim()) return
    setBusy(true)
    try {
      await api.addAsset({ identifier, kind })
      setIdentifier('')
      await load(); refreshAlerts()
      toast('Asset added to monitoring', 'success')
    } catch (e) {
      toast(e.response?.data?.detail || 'Failed to add asset', 'error')
    } finally { setBusy(false) }
  }

  async function rescan(id) {
    try { await api.rescanAsset(id); await load(); refreshAlerts(); toast('Rescanned', 'success') }
    catch { toast('Rescan failed', 'error') }
  }
  async function remove(id) {
    try { await api.deleteAsset(id); await load(); toast('Asset removed') }
    catch { toast('Failed to remove', 'error') }
  }

  return (
    <div>
      <Header title="Monitored Assets"
        sub="Continuously tracked identities. Only hashed digests are stored — never the plaintext identifier." />

      <Card style={{ marginBottom: 22 }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
          {['email', 'domain'].map((k) => (
            <button key={k} onClick={() => setKind(k)} style={{
              padding: '5px 14px', borderRadius: 7, fontSize: 12, fontWeight: 700, cursor: 'pointer',
              textTransform: 'capitalize', background: kind === k ? C.gold + '22' : 'transparent',
              border: `1px solid ${kind === k ? C.gold + '66' : C.border2}`, color: kind === k ? C.gold : C.muted,
            }}>{k}</button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <Input value={identifier} onChange={setIdentifier} onEnter={add}
            placeholder={kind === 'email' ? 'employee@company.com' : 'company.com'} />
          <Button onClick={add} disabled={busy || !identifier.trim()} style={{ whiteSpace: 'nowrap' }}>
            {busy ? <Spinner color="#1a1a12" /> : '+ Monitor'}
          </Button>
        </div>
      </Card>

      {!assets ? <Center><Spinner size={22} /></Center>
        : assets.length === 0 ? (
          <Card><Empty icon="◉" title="No monitored assets"
            sub="Add an employee email or company domain to begin continuous breach monitoring." /></Card>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {assets.map((a) => (
              <Card key={a.id} pad={16} hover>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div style={{
                    width: 44, height: 44, borderRadius: 10, flexShrink: 0,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18,
                    background: bandColor(a.risk_band) + '1e', color: bandColor(a.risk_band),
                    border: `1px solid ${bandColor(a.risk_band)}55`,
                  }}>{a.kind === 'email' ? '✉' : '🌐'}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                      <span style={{ fontSize: 14.5, fontWeight: 700, color: C.text }}>{a.label}</span>
                      <Badge color={bandColor(a.risk_band)}>{a.risk_band}</Badge>
                    </div>
                    <div style={{ fontSize: 11.5, color: C.faint, marginTop: 4, fontFamily: 'monospace' }}>
                      {a.id_hash?.slice(0, 24)}… · last scan {fmtTime(a.last_scan)}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right', marginRight: 6 }}>
                    <div style={{ fontSize: 22, fontWeight: 800, color: bandColor(a.risk_band), lineHeight: 1 }}>{a.risk_score}</div>
                    <div style={{ fontSize: 10.5, color: C.faint }}>{a.breach_count} breaches</div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => rescan(a.id)}>Rescan</Button>
                  <Button variant="danger" size="sm" onClick={() => remove(a.id)}>Remove</Button>
                </div>
              </Card>
            ))}
          </div>
        )}
    </div>
  )
}
