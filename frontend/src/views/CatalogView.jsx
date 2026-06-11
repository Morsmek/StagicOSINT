import React, { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { C, Card, Badge, Input, Spinner, bandColor, fmtNum } from '../components/ui'
import { Header, Center } from './Dashboard'

const sevBand = (s) => (s >= 4 ? 'Critical' : s >= 3 ? 'High' : 'Medium')

export function CatalogView() {
  const [data, setData] = useState(null)
  const [q, setQ] = useState('')
  const [layer, setLayer] = useState('all')

  useEffect(() => { api.catalog().then(setData).catch(() => {}) }, [])
  if (!data) return <Center><Spinner size={22} /></Center>

  const breaches = data.breaches.filter((b) =>
    (layer === 'all' || b.layer === layer) &&
    (!q || b.name.toLowerCase().includes(q.toLowerCase()) || b.domain.toLowerCase().includes(q.toLowerCase())))

  const totalRecords = data.breaches.reduce((s, b) => s + b.accounts, 0)

  return (
    <div>
      <Header title="Threat Intelligence Catalog"
        sub={`Reference corpus of ${data.breaches.length} documented breaches (${fmtNum(totalRecords)} records) correlated across ${data.layers.length} intelligence layers.`} />

      <div style={{ display: 'flex', gap: 12, marginBottom: 18, flexWrap: 'wrap' }}>
        <Input value={q} onChange={setQ} placeholder="Search breaches…" style={{ maxWidth: 280 }} />
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {[['all', 'All Layers'], ...data.layers.map((l) => [l.id, l.name])].map(([id, lbl]) => (
            <button key={id} onClick={() => setLayer(id)} style={{
              padding: '7px 13px', borderRadius: 7, fontSize: 12, fontWeight: 600, cursor: 'pointer',
              background: layer === id ? C.gold + '22' : 'transparent',
              border: `1px solid ${layer === id ? C.gold + '66' : C.border2}`,
              color: layer === id ? C.gold : C.muted,
            }}>{lbl}</button>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 10 }}>
        {breaches.map((b) => (
          <Card key={b.id} pad={16} hover>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontSize: 15, fontWeight: 700, color: C.text }}>{b.name}</div>
                <div style={{ fontSize: 12, color: C.faint, marginTop: 2 }}>{b.domain} · {b.year}</div>
              </div>
              <Badge color={bandColor(sevBand(b.severity))}>{sevBand(b.severity)}</Badge>
            </div>
            <div style={{ display: 'flex', gap: 16, marginTop: 12 }}>
              <div>
                <div style={{ fontSize: 18, fontWeight: 800, color: C.gold }}>{fmtNum(b.accounts)}</div>
                <div style={{ fontSize: 10.5, color: C.faint }}>records</div>
              </div>
              <div style={{ borderLeft: `1px solid ${C.border}`, paddingLeft: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: C.muted, marginTop: 2 }}>{b.layer_name}</div>
                <div style={{ fontSize: 10.5, color: C.faint }}>primary layer</div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 5, marginTop: 12, flexWrap: 'wrap' }}>
              {b.data_classes.map((dc) => (
                <span key={dc} style={{
                  fontSize: 10.5, color: C.muted, background: C.bg, border: `1px solid ${C.border}`,
                  borderRadius: 5, padding: '2px 7px',
                }}>{dc}</span>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
