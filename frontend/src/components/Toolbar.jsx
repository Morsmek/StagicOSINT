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
      height: 58, background: '#060C18',
      borderBottom: '1px solid rgba(151, 174, 207, 0.16)',
      display: 'flex', alignItems: 'center',
      padding: '0 18px', gap: 16, flexShrink: 0,
    }}>
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
        <img
          src="/stagic-logo-gold-transparent.png"
          alt="StagicOSINT"
          style={{ height: 34, width: 178, objectFit: 'contain', objectPosition: 'left center', filter: 'drop-shadow(0 0 10px rgba(255, 209, 101, 0.12))' }}
        />
      </div>

      {/* Divider */}
      <div style={{ width: 1, height: 24, background: 'rgba(151, 174, 207, 0.16)' }} />

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
        border: `1px solid ${hover && !disabled ? '#ffd165' : 'rgba(151, 174, 207, 0.16)'}`,
        borderRadius: 5, color: disabled ? '#334155' : hover ? '#ffd165' : '#94a3b8',
        padding: '4px 11px', fontSize: 11, fontWeight: 600,
        letterSpacing: 0.3, cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.15s',
      }}>
      {children}
    </button>
  )
}
