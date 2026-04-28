import React from 'react'
import { useStore } from '../store'

export function Toast() {
  const toast = useStore(s => s.toast)
  if (!toast) return null
  const colors = {
    success: { bg:'#0a0308', border:'#e91e8c', text:'#f9a8d4' },
    error:   { bg:'#0a0308', border:'#ef4444', text:'#fca5a5' },
    info:    { bg:'#0a0308', border:'#e91e8c', text:'#f9a8d4' },
  }
  const c = colors[toast.type] || colors.info
  return (
    <div style={{
      position:'fixed', bottom:24, right:24,
      background: c.bg, border:`1px solid ${c.border}`,
      borderRadius:8, padding:'10px 18px', color: c.text,
      fontSize:13, fontWeight:600, zIndex:1000,
      boxShadow:`0 4px 24px ${c.border}33`,
      maxWidth:320,
    }}>
      {toast.message}
    </div>
  )
}
