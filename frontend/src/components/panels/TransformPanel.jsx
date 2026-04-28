import React, { useEffect, useState } from 'react'
import { useStore } from '../../store'

const PINK = '#e91e8c'

export function TransformPanel() {
  const transforms         = useStore(s => s.transforms)
  const fetchTransforms    = useStore(s => s.fetchTransforms)
  const selectedEntityId   = useStore(s => s.selectedEntityId)
  const activeGraph        = useStore(s => s.activeGraph)
  const runTransform       = useStore(s => s.runTransform)
  const runningTransform   = useStore(s => s.runningTransform)
  const lastTransformResult = useStore(s => s.lastTransformResult)
  const showToast          = useStore(s => s.showToast)

  const [search, setSearch]  = useState('')
  const [running, setRunning] = useState(null)

  useEffect(() => { fetchTransforms() }, [])

  const selectedEntity     = activeGraph?.entities?.find(e => e.id === selectedEntityId)
  const applicableTransforms = selectedEntity
    ? transforms.filter(t => t.input_types.includes(selectedEntity.type))
    : []
  const filtered = applicableTransforms.filter(t =>
    !search || t.display_name.toLowerCase().includes(search.toLowerCase())
  )

  const handleRun = async (name) => {
    if (!selectedEntityId) return
    setRunning(name)
    try {
      const result = await runTransform(selectedEntityId, name)
      if (result.success)
        showToast(`✓ +${result.entities.length} entities`, 'success')
      else
        showToast(`✗ ${result.error}`, 'error')
    } finally { setRunning(null) }
  }

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100%', overflow:'hidden' }}>
      <div style={{ padding:'12px', borderBottom:'1px solid #110508' }}>
        <div style={{ fontSize:10, color:'#4a1530', marginBottom:8, letterSpacing:1, fontWeight:700 }}>
          TRANSFORMS
        </div>
        {selectedEntity ? (
          <div style={{ background:'#0a0308', borderRadius:6, padding:'5px 10px',
            fontSize:12, color:'#94a3b8', marginBottom:8, border:'1px solid #1a0510' }}>
            <span style={{ color: PINK, fontWeight:700 }}>[{selectedEntity.type}]</span>{' '}
            {selectedEntity.value.length > 28 ? selectedEntity.value.slice(0,26)+'…' : selectedEntity.value}
          </div>
        ) : (
          <div style={{ color:'#2a1020', fontSize:12, marginBottom:8 }}>
            Select a node to see transforms
          </div>
        )}
        <input value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Search transforms…"
          style={{ ...inputStyle, width:'100%' }} />
      </div>

      <div style={{ flex:1, overflowY:'auto', padding:8 }}>
        {selectedEntity && filtered.length === 0 && (
          <div style={{ color:'#2a1020', fontSize:13, textAlign:'center', marginTop:16 }}>
            No transforms for {selectedEntity.type}
          </div>
        )}
        {filtered.map(t => (
          <div key={t.name} style={{
            background:'#0a0308', borderRadius:6, padding:'8px 10px',
            marginBottom:6, border:'1px solid #1a0510',
          }}>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', gap:8 }}>
              <div style={{ flex:1, minWidth:0 }}>
                <div style={{ color:'#e2e8f0', fontSize:13, fontWeight:600, display:'flex', alignItems:'center', gap:6 }}>
                  {t.display_name}
                  {t.requires_api_key && (
                    <span style={{ fontSize:9, color:'#f59e0b', background:'#2a1a00',
                      padding:'1px 5px', borderRadius:4, fontWeight:700 }}>🔑 KEY</span>
                  )}
                </div>
                <div style={{ color:'#4a1530', fontSize:11, marginTop:2 }}>{t.description}</div>
              </div>
              <button onClick={() => handleRun(t.name)}
                disabled={!selectedEntity || running === t.name || runningTransform}
                style={{
                  background: running === t.name ? '#1a0510' : PINK,
                  border:'none', borderRadius:6, color:'#fff',
                  padding:'5px 10px', fontSize:12, cursor: selectedEntity ? 'pointer' : 'not-allowed',
                  flexShrink:0, opacity: !selectedEntity ? 0.4 : 1,
                }}>
                {running === t.name ? '⟳' : '▶'}
              </button>
            </div>
          </div>
        ))}
      </div>

      {lastTransformResult && (
        <div style={{ padding:10, borderTop:'1px solid #110508', background:'#000', maxHeight:110, overflowY:'auto' }}>
          <div style={{ fontSize:10, color:'#4a1530', marginBottom:4, letterSpacing:1, fontWeight:700 }}>
            LAST RESULT
          </div>
          <div style={{ color: lastTransformResult.success ? '#10b981' : '#ef4444', fontSize:12 }}>
            {lastTransformResult.success
              ? `✓ +${lastTransformResult.entities.length} entities, +${lastTransformResult.edges.length} edges`
              : `✗ ${lastTransformResult.error}`}
          </div>
          {lastTransformResult.messages?.map((m, i) => (
            <div key={i} style={{ color:'#4a1530', fontSize:11, marginTop:2 }}>• {m}</div>
          ))}
        </div>
      )}
    </div>
  )
}

const inputStyle = {
  background:'#0a0308', border:'1px solid #1a0510',
  borderRadius:6, color:'#e2e8f0', padding:'6px 10px',
  fontSize:13, outline:'none',
}
