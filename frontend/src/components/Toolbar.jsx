import React, { useState } from 'react'
import { useStore } from '../store'
import api from '../api/client'

export function Toolbar() {
  const activeGraph        = useStore(s => s.activeGraph)
  const activeGraphId      = useStore(s => s.activeGraphId)
  const refreshActiveGraph = useStore(s => s.refreshActiveGraph)
  const showToast          = useStore(s => s.showToast)
  const [layoutting, setLayoutting] = useState(false)

  const handleAutoLayout = async () => {
    if (!activeGraphId) return
    setLayoutting(true)
    try {
      const { layout } = await api.computeLayout(activeGraphId, { iterations: 80 })
      for (const [entityId, pos] of Object.entries(layout))
        await api.updateEntity(activeGraphId, entityId, { x: pos.x, y: pos.y })
      await refreshActiveGraph()
      showToast('Layout applied', 'success')
    } catch { showToast('Layout failed', 'error') }
    finally { setLayoutting(false) }
  }

  const handleExport = async () => {
    if (!activeGraphId) return
    const data = await api.exportGraph(activeGraphId)
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url; a.download = `${activeGraph?.name || 'graph'}.json`; a.click()
    URL.revokeObjectURL(url)
    showToast('Exported', 'success')
  }

  const handleImport = () => {
    const input = document.createElement('input')
    input.type = 'file'; input.accept = '.json'
    input.onchange = async (e) => {
      const file = e.target.files[0]; if (!file) return
      const data = JSON.parse(await file.text())
      await api.importGraph(activeGraphId, data)
      await refreshActiveGraph()
      showToast('Imported', 'success')
    }
    input.click()
  }

  return (
    <div style={{
      height: 50, background: '#000',
      borderBottom: '1px solid #1a0a0f',
      display: 'flex', alignItems: 'center',
      padding: '0 18px', gap: 16, flexShrink: 0,
    }}>
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
        {/* Eye icon */}
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <circle cx="14" cy="14" r="13" stroke="#e91e8c" strokeWidth="1.8" />
          <circle cx="14" cy="14" r="8" stroke="#e91e8c" strokeWidth="1.2" opacity="0.5" />
          <ellipse cx="14" cy="14" rx="6" ry="4" stroke="#e91e8c" strokeWidth="1.4" />
          <circle cx="14" cy="14" r="2.5" fill="#e91e8c" />
        </svg>
        {/* Wordmark */}
        <span style={{ fontSize: 17, fontWeight: 800, letterSpacing: 0.5, userSelect: 'none' }}>
          <span style={{ color: '#fff' }}>Stagic</span>
          <span style={{
            background: 'linear-gradient(90deg, #e91e8c, #ff4d6d)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>OSINT</span>
        </span>
      </div>

      {/* Divider */}
      <div style={{ width: 1, height: 20, background: '#1e293b' }} />

      {/* Active graph name */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {activeGraph ? (
          <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600,
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {activeGraph.name}
            </span>
            <span style={{ color: '#334155', fontSize: 11, flexShrink: 0 }}>
              {activeGraph.entities?.length || 0} nodes · {activeGraph.edges?.length || 0} edges
            </span>
          </span>
        ) : (
          <span style={{ color: '#1e293b', fontSize: 12 }}>No investigation selected</span>
        )}
      </div>

      {/* Actions */}
      {activeGraph && (
        <div style={{ display: 'flex', gap: 6 }}>
          <Btn onClick={handleAutoLayout} disabled={layoutting}>
            {layoutting ? '⟳' : '⊹'} Layout
          </Btn>
          <Btn onClick={handleExport}>↓ Export</Btn>
          <Btn onClick={handleImport}>↑ Import</Btn>
        </div>
      )}
    </div>
  )
}

function Btn({ children, onClick, disabled }) {
  const [hover, setHover] = useState(false)
  return (
    <button onClick={onClick} disabled={disabled}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        background: 'transparent',
        border: `1px solid ${hover && !disabled ? '#e91e8c' : '#1e293b'}`,
        borderRadius: 5, color: disabled ? '#334155' : hover ? '#e91e8c' : '#64748b',
        padding: '4px 11px', fontSize: 11, fontWeight: 600,
        letterSpacing: 0.3, cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.15s',
      }}>
      {children}
    </button>
  )
}
