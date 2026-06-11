import React, { useState, useEffect, createContext, useContext, useCallback } from 'react'
import { C, Logo } from './components/ui'
import { Dashboard } from './views/Dashboard'
import { ScanView } from './views/ScanView'
import { AssetsView } from './views/AssetsView'
import { SupplyChainView } from './views/SupplyChainView'
import { AlertsView } from './views/AlertsView'
import { AuditView } from './views/AuditView'
import { CatalogView } from './views/CatalogView'
import { api } from './lib/api'

const ToastCtx = createContext(null)
export const useToast = () => useContext(ToastCtx)

const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: '◳', desc: 'Overview' },
  { id: 'scan', label: 'Breach Scan', icon: '⌖', desc: 'Zero-knowledge scan' },
  { id: 'assets', label: 'Monitored Assets', icon: '◉', desc: 'Identities' },
  { id: 'supply', label: 'Supply Chain', icon: '⛓', desc: 'Scan-by-Proxy' },
  { id: 'alerts', label: 'Alerts', icon: '⚑', desc: 'Incidents' },
  { id: 'audit', label: 'Audit Ledger', icon: '⬡', desc: 'Hash chain' },
  { id: 'catalog', label: 'Intelligence', icon: '☷', desc: 'Breach catalog' },
]

export default function App() {
  const [view, setView] = useState('dashboard')
  const [toasts, setToasts] = useState([])
  const [alertCount, setAlertCount] = useState(0)
  const [navKey, setNavKey] = useState(0) // bump to refresh active view

  const toast = useCallback((msg, kind = 'info') => {
    const id = Math.random().toString(36).slice(2)
    setToasts((t) => [...t, { id, msg, kind }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3600)
  }, [])

  const refreshAlerts = useCallback(() => {
    api.alerts(true).then((a) => setAlertCount(a.length)).catch(() => {})
  }, [])

  useEffect(() => {
    refreshAlerts()
    const i = setInterval(refreshAlerts, 15000)
    return () => clearInterval(i)
  }, [refreshAlerts])

  const go = (id) => { setView(id); setNavKey((k) => k + 1) }

  const sharedProps = { toast, refreshAlerts, go, key: `${view}-${navKey}` }
  const views = {
    dashboard: <Dashboard {...sharedProps} />,
    scan: <ScanView {...sharedProps} />,
    assets: <AssetsView {...sharedProps} />,
    supply: <SupplyChainView {...sharedProps} />,
    alerts: <AlertsView {...sharedProps} />,
    audit: <AuditView {...sharedProps} />,
    catalog: <CatalogView {...sharedProps} />,
  }

  return (
    <ToastCtx.Provider value={toast}>
      <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
        {/* Sidebar */}
        <aside style={{
          width: 248, flexShrink: 0, background: C.surface, borderRight: `1px solid ${C.border}`,
          display: 'flex', flexDirection: 'column', padding: '22px 14px',
        }}>
          <div style={{ padding: '4px 8px 22px' }}>
            <Logo height={30} />
            <div style={{ fontSize: 10.5, color: C.faint, letterSpacing: 1.4, marginTop: 8, textTransform: 'uppercase' }}>
              Stagic Data Breach Alert
            </div>
          </div>

          <nav style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {NAV.map((n) => {
              const active = view === n.id
              return (
                <button key={n.id} onClick={() => go(n.id)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px',
                    background: active ? C.gold + '18' : 'transparent',
                    border: `1px solid ${active ? C.gold + '44' : 'transparent'}`,
                    borderRadius: 9, cursor: 'pointer', textAlign: 'left', width: '100%',
                    transition: 'background .15s',
                  }}
                  onMouseEnter={(e) => !active && (e.currentTarget.style.background = C.surface2)}
                  onMouseLeave={(e) => !active && (e.currentTarget.style.background = 'transparent')}>
                  <span style={{ fontSize: 16, color: active ? C.gold : C.faint, width: 18, textAlign: 'center' }}>{n.icon}</span>
                  <span style={{ flex: 1 }}>
                    <span style={{ display: 'block', fontSize: 13.5, fontWeight: active ? 700 : 600, color: active ? C.text : C.muted }}>{n.label}</span>
                    <span style={{ display: 'block', fontSize: 10.5, color: C.faint }}>{n.desc}</span>
                  </span>
                  {n.id === 'alerts' && alertCount > 0 && (
                    <span style={{
                      background: C.critical, color: '#1a1a12', fontSize: 10.5, fontWeight: 800,
                      borderRadius: 999, padding: '1px 7px', minWidth: 18, textAlign: 'center',
                    }}>{alertCount}</span>
                  )}
                </button>
              )
            })}
          </nav>

          <div style={{ marginTop: 'auto', padding: '14px 10px 4px', borderTop: `1px solid ${C.border}` }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ width: 7, height: 7, borderRadius: 999, background: C.clear, boxShadow: `0 0 8px ${C.clear}` }} />
              <span style={{ fontSize: 11.5, color: C.muted }}>Zero-Knowledge mode active</span>
            </div>
            <div style={{ fontSize: 10.5, color: C.faint, marginTop: 6, lineHeight: 1.5 }}>
              Identifiers are hashed in your browser. Plaintext never leaves the client.
            </div>
          </div>
        </aside>

        {/* Main */}
        <main style={{ flex: 1, overflowY: 'auto', background: C.bg }}>
          <div style={{ maxWidth: 1180, margin: '0 auto', padding: '30px 38px 60px', animation: 'fadeIn .25s ease' }}>
            {views[view]}
          </div>
        </main>

        {/* Toasts */}
        <div style={{ position: 'fixed', bottom: 22, right: 22, display: 'flex', flexDirection: 'column', gap: 10, zIndex: 100 }}>
          {toasts.map((t) => (
            <div key={t.id} style={{
              background: C.surface2, border: `1px solid ${t.kind === 'error' ? C.critical : t.kind === 'success' ? C.clear : C.border2}`,
              borderLeft: `3px solid ${t.kind === 'error' ? C.critical : t.kind === 'success' ? C.clear : C.gold}`,
              borderRadius: 9, padding: '12px 18px', color: C.text, fontSize: 13, fontWeight: 500,
              boxShadow: '0 10px 30px rgba(0,0,0,.5)', animation: 'fadeIn .2s ease', maxWidth: 340,
            }}>{t.msg}</div>
          ))}
        </div>
      </div>
    </ToastCtx.Provider>
  )
}
