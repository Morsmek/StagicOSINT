import React, { useState } from 'react'
import { useStore } from '../../store'

const PINK = '#e91e8c'

const ENTITY_TYPES = [
  'Domain','IPAddress','EmailAddress','Username','Person','Organization',
  'URL','SocialMedia','Hash','PhoneNumber','Document','Location',
  'ASNumber','Network','MXRecord','NSRecord','Nameserver',
  'SSLCertificate','Subdomain','HTTPHeader',
]

export function EntityPanel() {
  const activeGraph      = useStore(s => s.activeGraph)
  const selectedEntityId = useStore(s => s.selectedEntityId)
  const addEntity        = useStore(s => s.addEntity)
  const deleteEntity     = useStore(s => s.deleteEntity)
  const setSidebarView   = useStore(s => s.setSidebarView)
  const showToast        = useStore(s => s.showToast)

  const [type, setType]   = useState('Domain')
  const [value, setValue] = useState('')
  const [label, setLabel] = useState('')
  const [adding, setAdding] = useState(false)

  const selectedEntity = activeGraph?.entities?.find(e => e.id === selectedEntityId)

  const handleAdd = async (e) => {
    e.preventDefault()
    if (!value.trim()) return
    setAdding(true)
    try {
      await addEntity(type, value.trim(), label.trim() || undefined)
      setValue(''); setLabel('')
      showToast('Entity added', 'success')
    } catch { showToast('Failed to add entity', 'error') }
    finally { setAdding(false) }
  }

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100%', overflow:'hidden' }}>
      <form onSubmit={handleAdd} style={{ padding:'12px', borderBottom:'1px solid #110508' }}>
        <div style={{ fontSize:10, color:'#4a1530', marginBottom:8, letterSpacing:1, fontWeight:700 }}>
          ADD ENTITY
        </div>
        <select value={type} onChange={e => setType(e.target.value)}
          style={{ ...inputStyle, width:'100%', marginBottom:6 }}>
          {ENTITY_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <input value={value} onChange={e => setValue(e.target.value)}
          placeholder="Value (e.g. stagic.pl)"
          style={{ ...inputStyle, width:'100%', marginBottom:6 }} />
        <input value={label} onChange={e => setLabel(e.target.value)}
          placeholder="Label (optional)"
          style={{ ...inputStyle, width:'100%', marginBottom:8 }} />
        <button type="submit" disabled={adding || !value.trim() || !activeGraph}
          style={{ ...btnStyle, width:'100%' }}>
          {adding ? 'Adding…' : 'Add Entity'}
        </button>
      </form>

      <div style={{ flex:1, overflowY:'auto', padding:12 }}>
        {selectedEntity ? (
          <>
            <div style={{ fontSize:10, color:'#4a1530', marginBottom:8, letterSpacing:1, fontWeight:700 }}>
              SELECTED ENTITY
            </div>
            <div style={cardStyle}>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:8 }}>
                <span style={{ background: PINK, color:'#fff', borderRadius:4,
                  padding:'2px 7px', fontSize:10, fontWeight:700 }}>{selectedEntity.type}</span>
                <div style={{ display:'flex', gap:4 }}>
                  <button onClick={() => setSidebarView('transforms')}
                    style={iconBtn} title="Run transforms">⚡</button>
                  <button onClick={() => deleteEntity(selectedEntity.id)}
                    style={{ ...iconBtn, color:'#ef4444' }} title="Delete">🗑</button>
                </div>
              </div>
              <div style={labelStyle}>Value</div>
              <div style={valueStyle}>{selectedEntity.value}</div>
              {Object.entries(selectedEntity.properties || {}).length > 0 && (
                <>
                  <div style={{ ...labelStyle, marginTop:8 }}>Properties</div>
                  {Object.entries(selectedEntity.properties).map(([k, v]) => (
                    <div key={k} style={{ display:'flex', gap:8, marginBottom:4 }}>
                      <span style={{ color:'#4a1530', fontSize:11, minWidth:80 }}>{k}</span>
                      <span style={{ color:'#94a3b8', fontSize:12, wordBreak:'break-all' }}>
                        {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                      </span>
                    </div>
                  ))}
                </>
              )}
            </div>
          </>
        ) : (
          <div style={{ color:'#2a1020', fontSize:13, textAlign:'center', marginTop:24 }}>
            Click a node to inspect it
          </div>
        )}
      </div>
    </div>
  )
}

const inputStyle = {
  background:'#0a0308', border:'1px solid #1a0510',
  borderRadius:6, color:'#e2e8f0', padding:'6px 10px',
  fontSize:13, outline:'none',
}
const btnStyle = {
  background: '#e91e8c', border:'none', borderRadius:6,
  color:'#fff', padding:'8px 12px', fontSize:13,
  cursor:'pointer', fontWeight:700, opacity:1,
}
const cardStyle = {
  background:'#0a0308', borderRadius:8, padding:12, border:'1px solid #1a0510',
}
const labelStyle = {
  fontSize:10, color:'#4a1530', letterSpacing:0.5, marginBottom:2, textTransform:'uppercase',
}
const valueStyle = { fontSize:13, color:'#cbd5e1', marginBottom:8, wordBreak:'break-all' }
const iconBtn    = { background:'none', border:'none', cursor:'pointer', fontSize:16, color:'#94a3b8', padding:2 }
