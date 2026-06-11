import React, { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { C, Card, Badge, Button, Spinner, fmtTime, Empty } from '../components/ui'
import { Header, Center } from './Dashboard'

const EVENT_LABELS = {
  scan: 'Breach Scan', asset_added: 'Asset Added', asset_removed: 'Asset Removed',
  rescan: 'Asset Rescan', vendor_added: 'Vendor Added', vendor_removed: 'Vendor Removed',
  vendor_scan: 'Vendor Scan', alert_ack: 'Alert Acknowledged',
}

export function AuditView({ toast }) {
  const [entries, setEntries] = useState(null)
  const [chain, setChain] = useState(null)

  const load = () => {
    api.audit(150).then(setEntries).catch(() => setEntries([]))
    api.verifyAudit().then(setChain).catch(() => {})
  }
  useEffect(() => { load() }, [])

  async function verify() {
    const r = await api.verifyAudit()
    setChain(r)
    toast(r.valid ? `Chain verified — ${r.entries} entries intact` : 'Chain integrity broken!', r.valid ? 'success' : 'error')
  }

  return (
    <div>
      <Header title="Immutable Audit Ledger"
        sub="Every action is recorded in a SHA-256 hash chain. Each entry seals the previous one, producing a tamper-evident, blockchain-style record." />

      <Card style={{ marginBottom: 22, display: 'flex', alignItems: 'center', gap: 18 }}>
        <div style={{
          width: 56, height: 56, borderRadius: 14, display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 26, background: chain?.valid ? C.clear + '1e' : C.surface2,
          border: `1px solid ${chain?.valid ? C.clear : C.border2}66`,
          color: chain?.valid ? C.clear : C.faint,
        }}>{chain?.valid ? '⬡' : '⬡'}</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: chain?.valid ? C.clear : C.text }}>
            {chain ? (chain.valid ? 'Chain Verified' : `Chain Broken at entry #${chain.broken_at}`) : 'Ledger'}
          </div>
          <div style={{ fontSize: 12.5, color: C.faint, marginTop: 3 }}>
            {chain ? `${chain.entries} immutable entries` : 'Loading…'}
          </div>
        </div>
        <Button onClick={verify}>Verify Integrity</Button>
      </Card>

      {!entries ? <Center><Spinner size={22} /></Center>
        : entries.length === 0 ? (
          <Card><Empty icon="⬡" title="Ledger empty"
            sub="Audit entries are appended automatically as you scan and monitor." /></Card>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {entries.map((e, i) => (
              <div key={e.id} style={{ display: 'flex', gap: 14, position: 'relative' }}>
                {/* chain rail */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 24 }}>
                  <div style={{ width: 11, height: 11, borderRadius: 999, background: C.gold, marginTop: 18, flexShrink: 0, boxShadow: `0 0 0 3px ${C.gold}22` }} />
                  {i < entries.length - 1 && <div style={{ width: 2, flex: 1, background: C.border }} />}
                </div>
                <Card pad={14} style={{ flex: 1, marginBottom: 9 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                    <Badge color={C.gold}>{EVENT_LABELS[e.event_type] || e.event_type}</Badge>
                    {e.ref && <code style={{ fontSize: 11.5, color: C.muted, fontFamily: 'monospace' }}>ref {e.ref}</code>}
                    <span style={{ fontSize: 11.5, color: C.faint, marginLeft: 'auto' }}>{fmtTime(e.ts)}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 18, marginTop: 10, flexWrap: 'wrap' }}>
                    <Field label="Txn Key" value={e.txn_key} accent />
                    <Field label="Entry Hash" value={e.entry_hash.slice(0, 20) + '…'} />
                    <Field label="Prev Hash" value={e.prev_hash.slice(0, 16) + '…'} />
                  </div>
                </Card>
              </div>
            ))}
          </div>
        )}
    </div>
  )
}

function Field({ label, value, accent }) {
  return (
    <div>
      <div style={{ fontSize: 10, color: C.faint, textTransform: 'uppercase', letterSpacing: 0.6 }}>{label}</div>
      <code style={{ fontSize: 12, fontFamily: 'monospace', color: accent ? C.gold : C.muted }}>{value}</code>
    </div>
  )
}
