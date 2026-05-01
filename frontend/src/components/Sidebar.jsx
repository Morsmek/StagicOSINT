import React from 'react'
import { useStore } from '../store'
import { GraphsPanel }    from './panels/GraphsPanel'
import { EntityPanel }    from './panels/EntityPanel'
import { TransformPanel } from './panels/TransformPanel'
import { ApiKeysPanel }   from './panels/ApiKeysPanel'

const VIEWS = [
  { key: 'graphs',     icon: '🗂',  label: 'Cases' },
  { key: 'entity',     icon: '🔍',  label: 'Entity' },
  { key: 'transforms', icon: '⚡',  label: 'Transforms' },
  { key: 'apikeys',    icon: '🔑',  label: 'API Keys' },
]

const PINK = '#ffd165'

export function Sidebar() {
  const sidebarView    = useStore(s => s.sidebarView)
  const setSidebarView = useStore(s => s.setSidebarView)

  return (
    <div style={{
      width: 310, display: 'flex', flexDirection: 'column',
      background: '#060C18', borderRight: '1px solid rgba(151, 174, 207, 0.16)', flexShrink: 0,
    }}>
      {/* Tab bar */}
      <div style={{ display: 'flex', borderBottom: '1px solid rgba(151, 174, 207, 0.16)', background: '#051426' }}>
        {VIEWS.map(v => {
          const active = sidebarView === v.key
          return (
            <button key={v.key} onClick={() => setSidebarView(v.key)} title={v.label}
              style={{
                flex: 1, padding: '9px 4px',
                    background: active ? 'rgba(255, 209, 101, 0.08)' : 'transparent',
                border: 'none',
                borderBottom: `2px solid ${active ? PINK : 'transparent'}`,
                color: active ? PINK : '#334155',
                cursor: 'pointer', fontSize: 16,
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
                transition: 'all 0.15s',
              }}>
              <span>{v.icon}</span>
              <span style={{ fontSize: 8, letterSpacing: 0.8, fontWeight: 700 }}>
                {v.label.toUpperCase()}
              </span>
            </button>
          )
        })}
      </div>

      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {sidebarView === 'graphs'     && <GraphsPanel />}
        {sidebarView === 'entity'     && <EntityPanel />}
        {sidebarView === 'transforms' && <TransformPanel />}
        {sidebarView === 'apikeys'    && <ApiKeysPanel />}
      </div>
    </div>
  )
}
