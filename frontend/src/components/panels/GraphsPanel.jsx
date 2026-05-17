import React, { useEffect, useState } from 'react'
import { useStore } from '../../store'

const PINK = '#e91e8c'

export function GraphsPanel() {
  const graphs         = useStore(s => s.graphs)
  const activeGraphId  = useStore(s => s.activeGraphId)
  const fetchGraphs    = useStore(s => s.fetchGraphs)
  const createGraph    = useStore(s => s.createGraph)
  const setActiveGraph = useStore(s => s.setActiveGraph)
  const deleteGraph    = useStore(s => s.deleteGraph)
  const showToast      = useStore(s => s.showToast)

  const [newName, setNewName] = useState('')
  const [creating, setCreating] = useState(false)

  useEffect(() => { fetchGraphs() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!newName.trim()) return
    setCreating(true)
    const name = newName.trim()
    // Retry once — backend may be waking up on Render's free tier
    for (let attempt = 1; attempt <= 2; attempt++) {
      try {
        if (attempt === 2) showToast('Backend waking up, retrying…', 'info')
        const graph = await createGraph(name)
        setNewName('')
        await setActiveGraph(graph.id)
        showToast(`"${graph.name}" created`, 'success')
        setCreating(false)
        return
      } catch (err) {
        if (attempt < 2) {
          await new Promise(r => setTimeout(r, 3000))
        } else {
          showToast('Failed — backend unreachable. Try again in a moment.', 'error')
        }
      }
    }
    setCreating(false)
  }

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100%', overflow:'hidden' }}>
      {/* Create form */}
      <form onSubmit={handleCreate} style={{ padding:'12px', borderBottom:'1px solid #110508' }}>
        <div style={{ fontSize:10, color:'#4a1530', marginBottom:6, letterSpacing:1, fontWeight:700 }}>
          NEW INVESTIGATION
        </div>
        <div style={{ display:'flex', gap:6 }}>
          <input
            value={newName}
            onChange={e => setNewName(e.target.value)}
            placeholder="Investigation name..."
            style={inputStyle}
          />
          <button type="submit" disabled={creating || !newName.trim()} style={{
            background: PINK, border:'none', borderRadius:6,
            color:'#fff', padding:'6px 14px', fontSize:16,
            cursor: creating || !newName.trim() ? 'not-allowed' : 'pointer',
            fontWeight:700, opacity: creating || !newName.trim() ? 0.5 : 1,
            flexShrink: 0,
          }}>+</button>
        </div>
      </form>

      {/* List */}
      <div style={{ flex:1, overflowY:'auto', padding:8 }}>
        {graphs.length === 0 && (
          <div style={{ color:'#2a1020', fontSize:13, textAlign:'center', marginTop:24 }}>
            No investigations yet
          </div>
        )}
        {graphs.map(g => (
          <div key={g.id} onClick={() => setActiveGraph(g.id)} style={{
            padding:'8px 10px', marginBottom:4, borderRadius:6,
            background: g.id === activeGraphId ? '#1a0510' : '#0a0308',
            border: `1px solid ${g.id === activeGraphId ? PINK : 'transparent'}`,
            cursor:'pointer', display:'flex', alignItems:'center', gap:8,
            transition:'all 0.15s',
          }}>
            <div style={{ flex:1, minWidth:0 }}>
              <div style={{ color:'#e2e8f0', fontSize:13, fontWeight:500,
                overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                {g.name}
              </div>
              <div style={{ color:'#4a1530', fontSize:11, marginTop:2 }}>
                {g.entity_count} nodes · {g.edge_count} edges
              </div>
            </div>
            <button onClick={e => { e.stopPropagation(); deleteGraph(g.id) }}
              style={{ background:'none', border:'none', color:'#4a1530',
                cursor:'pointer', fontSize:13, padding:2, opacity:0.6 }}>✕</button>
          </div>
        ))}
      </div>
    </div>
  )
}

const inputStyle = {
  flex:1, background:'#0a0308', border:'1px solid #1a0510',
  borderRadius:6, color:'#e2e8f0', padding:'6px 10px',
  fontSize:13, outline:'none',
}
