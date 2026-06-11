import React from 'react'

export const C = {
  bg: '#0e0f0d', surface: '#1b1c16', surface2: '#232419',
  border: '#33342a', border2: '#44453a',
  text: '#ecebe1', muted: '#b8b8b0', faint: '#7a7a70',
  gold: '#d8c898', gold2: '#c9b57a',
  critical: '#e3756b', high: '#e0a35c', medium: '#d8c898', low: '#8fae8f', clear: '#6f9d8a',
}

export const bandColor = (band) => ({
  Critical: C.critical, High: C.high, Medium: C.medium, Low: C.low, Clear: C.clear,
}[band] || C.faint)

export const sevColor = (sev) => ({
  critical: C.critical, high: C.high, medium: C.medium, low: C.low, info: C.faint,
}[sev] || C.faint)

export function Logo({ height = 30 }) {
  return <img src="/sdba-logo.png" alt="SDBA" style={{ height, display: 'block' }} />
}

export function Card({ children, style, pad = 20, hover, onClick }) {
  return (
    <div
      onClick={onClick}
      style={{
        background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12,
        padding: pad, transition: 'border-color .15s, transform .15s',
        cursor: onClick ? 'pointer' : 'default', ...style,
      }}
      onMouseEnter={hover ? (e) => (e.currentTarget.style.borderColor = C.gold2) : undefined}
      onMouseLeave={hover ? (e) => (e.currentTarget.style.borderColor = C.border) : undefined}
    >
      {children}
    </div>
  )
}

export function Badge({ children, color = C.gold, filled }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      fontSize: 11, fontWeight: 700, letterSpacing: 0.3,
      padding: '3px 9px', borderRadius: 999,
      color: filled ? C.bg : color,
      background: filled ? color : `${color}1e`,
      border: `1px solid ${color}55`, textTransform: 'uppercase', whiteSpace: 'nowrap',
    }}>{children}</span>
  )
}

export function Button({ children, onClick, variant = 'primary', disabled, style, size = 'md' }) {
  const sizes = { sm: '6px 12px', md: '9px 18px', lg: '12px 24px' }
  const variants = {
    primary: { background: C.gold, color: '#1a1a12', border: `1px solid ${C.gold}` },
    ghost: { background: 'transparent', color: C.muted, border: `1px solid ${C.border2}` },
    danger: { background: 'transparent', color: C.critical, border: `1px solid ${C.critical}66` },
  }
  return (
    <button
      onClick={onClick} disabled={disabled}
      style={{
        ...variants[variant], padding: sizes[size], borderRadius: 8, fontWeight: 700,
        fontSize: 13, cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1, transition: 'filter .15s, opacity .15s', ...style,
      }}
      onMouseEnter={(e) => !disabled && (e.currentTarget.style.filter = 'brightness(1.12)')}
      onMouseLeave={(e) => (e.currentTarget.style.filter = 'none')}
    >{children}</button>
  )
}

export function Input({ value, onChange, placeholder, onEnter, style, type = 'text' }) {
  return (
    <input
      type={type} value={value} placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={(e) => e.key === 'Enter' && onEnter?.()}
      style={{
        background: C.bg, border: `1px solid ${C.border2}`, borderRadius: 8,
        color: C.text, padding: '11px 14px', fontSize: 14, outline: 'none', width: '100%',
        transition: 'border-color .15s', ...style,
      }}
      onFocus={(e) => (e.currentTarget.style.borderColor = C.gold)}
      onBlur={(e) => (e.currentTarget.style.borderColor = C.border2)}
    />
  )
}

export function Spinner({ size = 16, color = C.gold }) {
  return (
    <span style={{
      width: size, height: size, border: `2px solid ${color}33`, borderTopColor: color,
      borderRadius: '50%', display: 'inline-block', animation: 'spin .7s linear infinite',
    }} />
  )
}

export function RiskRing({ score, band, size = 88 }) {
  const r = size / 2 - 7
  const circ = 2 * Math.PI * r
  const color = bandColor(band)
  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={C.border} strokeWidth="6" />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth="6"
          strokeLinecap="round" strokeDasharray={circ}
          strokeDashoffset={circ * (1 - score / 100)} style={{ transition: 'stroke-dashoffset .6s ease' }} />
      </svg>
      <div style={{
        position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <div style={{ fontSize: size * 0.3, fontWeight: 800, color }}>{score}</div>
        <div style={{ fontSize: 9, color: C.faint, letterSpacing: 1, textTransform: 'uppercase' }}>risk</div>
      </div>
    </div>
  )
}

export function Empty({ icon = '◇', title, sub }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      padding: '60px 20px', gap: 8, color: C.faint, textAlign: 'center',
    }}>
      <div style={{ fontSize: 34, opacity: 0.5 }}>{icon}</div>
      <div style={{ fontSize: 15, fontWeight: 600, color: C.muted }}>{title}</div>
      {sub && <div style={{ fontSize: 13, maxWidth: 360, lineHeight: 1.5 }}>{sub}</div>}
    </div>
  )
}

export const fmtNum = (n) => {
  if (n == null) return '0'
  if (n >= 1e9) return (n / 1e9).toFixed(1).replace(/\.0$/, '') + 'B'
  if (n >= 1e6) return (n / 1e6).toFixed(1).replace(/\.0$/, '') + 'M'
  if (n >= 1e3) return (n / 1e3).toFixed(1).replace(/\.0$/, '') + 'K'
  return String(n)
}

export const fmtTime = (ts) => {
  if (!ts) return '—'
  const d = new Date(ts * 1000)
  return d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
