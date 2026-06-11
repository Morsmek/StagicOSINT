import React, { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { C, Card, Badge, Button, Input, Spinner, bandColor, fmtNum, fmtTime, Empty } from '../components/ui'
import { Header, Center } from './Dashboard'

export function SupplyChainView({ toast, refreshAlerts }) {
  const [vendors, setVendors] = useState(null)
  const [name, setName] = useState('')
  const [domain, setDomain] = useState('')
  const [busy, setBusy] = useState(false)

  const load = () => api.vendors().then(setVendors).catch(() => setVendors([]))
  useEffect(() => { load() }, [])

  async function add() {
    if (!name.trim() || !domain.trim()) return
    setBusy(true)
    try {
      await api.addVendor(name, domain)
      setName(''); setDomain('')
      await load(); refreshAlerts()
      toast('Vendor added — scan-by-proxy active', 'success')
    } catch (e) {
      toast(e.response?.data?.detail || 'Failed to add vendor', 'error')
    } finally { setBusy(false) }
  }

  async function scan(id) {
    try { await api.scanVendor(id); await load(); refreshAlerts(); toast('Vendor rescanned', 'success') }
    catch { toast('Scan failed', 'error') }
  }
  async function remove(id) {
    try { await api.deleteVendor(id); await load(); toast('Vendor removed') }
    catch { toast('Failed to remove', 'error') }
  }

  const totalExposed = (vendors || []).reduce((s, v) => s + (v.exposed || 0), 0)
  const atRisk = (vendors || []).filter((v) => ['High', 'Critical'].includes(v.risk_band)).length

  return (
    <div>
      <Header title="Supply-Chain Intelligence"
        sub="Scan-by-Proxy extends monitoring to vendors and partners. 62% of enterprise breaches originate through third-party compromise." />

      {vendors && vendors.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14, marginBottom: 18 }}>
          <Mini label="Tracked Vendors" value={vendors.length} />
          <Mini label="Exposed Accounts" value={fmtNum(totalExposed)} color={C.high} />
          <Mini label="High-Risk Vendors" value={atRisk} color={atRisk > 0 ? C.critical : C.clear} />
        </div>
      )}

      <Card style={{ marginBottom: 22 }}>
        <div style={{ display: 'flex', gap: 12 }}>
          <Input value={name} onChange={setName} placeholder="Vendor name (e.g. Acme Cloud)" style={{ flex: 1 }} />
          <Input value={domain} onChange={setDomain} onEnter={add} placeholder="vendor-domain.com" style={{ flex: 1 }} />
          <Button onClick={add} disabled={busy || !name.trim() || !domain.trim()} style={{ whiteSpace: 'nowrap' }}>
            {busy ? <Spinner color="#1a1a12" /> : '+ Track'}
          </Button>
        </div>
      </Card>

      {!vendors ? <Center><Spinner size={22} /></Center>
        : vendors.length === 0 ? (
          <Card><Empty icon="⛓" title="No vendors tracked"
            sub="Add a supplier or partner domain to monitor third-party breach exposure." /></Card>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {vendors.map((v) => (
              <Card key={v.id} pad={16} hover>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                      <span style={{ fontSize: 14.5, fontWeight: 700, color: C.text }}>{v.name}</span>
                      <Badge color={bandColor(v.risk_band)}>{v.risk_band}</Badge>
                    </div>
                    <div style={{ fontSize: 12, color: C.faint, marginTop: 4 }}>
                      {v.domain} · {fmtNum(v.exposed)} exposed accounts · {v.breach_count} breaches · scanned {fmtTime(v.last_scan)}
                    </div>
                    {/* third-party risk bar */}
                    <div style={{ height: 6, background: C.bg, borderRadius: 999, marginTop: 10, overflow: 'hidden', maxWidth: 320 }}>
                      <div style={{ width: `${v.risk_score}%`, height: '100%', background: bandColor(v.risk_band), transition: 'width .5s' }} />
                    </div>
                  </div>
                  <div style={{ textAlign: 'right', marginRight: 4 }}>
                    <div style={{ fontSize: 22, fontWeight: 800, color: bandColor(v.risk_band), lineHeight: 1 }}>{v.risk_score}</div>
                    <div style={{ fontSize: 10.5, color: C.faint }}>3rd-party risk</div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => scan(v.id)}>Scan</Button>
                  <Button variant="danger" size="sm" onClick={() => remove(v.id)}>Remove</Button>
                </div>
              </Card>
            ))}
          </div>
        )}
    </div>
  )
}

function Mini({ label, value, color }) {
  return (
    <Card pad={16}>
      <div style={{ fontSize: 11, color: C.faint, textTransform: 'uppercase', letterSpacing: 0.7 }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 800, color: color || C.text, marginTop: 6 }}>{value}</div>
    </Card>
  )
}
