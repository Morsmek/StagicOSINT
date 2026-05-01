import React, { useEffect, useMemo, useState } from 'react'

const STORAGE_KEY = 'stagicosint:onboarding-complete'
const GOLD = '#ffd165'
const GOLD_DARK = '#b89d10'
const NAVY = '#051426'
const CARD = '#0d1c2f'
const CARD_HIGH = '#122033'
const TEXT = '#d5e3fd'
const MUTED = '#d3c5ac'

const phases = [
  {
    icon: 'radar',
    eyebrow: 'Phase 01',
    title: 'Global Intelligence',
    body: 'Commencing data acquisition from unstructured open sources. StagicOSINT indexes and synthesizes global information streams to establish a comprehensive intelligence baseline.',
  },
  {
    icon: 'target',
    eyebrow: 'Phase 02',
    title: 'Target Acquisition',
    body: 'Enter a domain, IP address, hash, e-mail, or username to initiate focused reconnaissance. Entity relationships are mapped into an operational graph for rapid investigation.',
  },
  {
    icon: 'analysis',
    eyebrow: 'Phase 03',
    title: 'Actionable Reporting',
    body: 'Correlate transforms, enrich evidence, and export investigation findings into concise reporting workflows for tactical review and command decisions.',
  },
]

export function OnboardingSplash() {
  const [visible, setVisible] = useState(() => {
    if (typeof window === 'undefined') return false
    return window.localStorage.getItem(STORAGE_KEY) !== 'true'
  })
  const [active, setActive] = useState(0)

  const current = phases[active]
  const isFinal = active === phases.length - 1

  const complete = () => {
    window.localStorage.setItem(STORAGE_KEY, 'true')
    setVisible(false)
  }

  const next = () => {
    if (isFinal) complete()
    else setActive(index => Math.min(index + 1, phases.length - 1))
  }

  useEffect(() => {
    if (!visible) return undefined

    const onKeyDown = event => {
      if (event.key === 'Escape') complete()
      if (event.key === 'ArrowRight' || event.key === 'Enter') next()
      if (event.key === 'ArrowLeft') setActive(index => Math.max(index - 1, 0))
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [visible, active])

  const backgroundNodes = useMemo(() => Array.from({ length: 18 }, (_, index) => ({
    left: `${7 + ((index * 23) % 86)}%`,
    top: `${8 + ((index * 17) % 78)}%`,
    delay: `${(index % 6) * 0.45}s`,
    size: 2 + (index % 3),
  })), [])

  if (!visible) return null

  return (
    <div style={styles.overlay} role="dialog" aria-modal="true" aria-labelledby="onboarding-title">
      <style>{css}</style>

      <div style={styles.gridBackdrop} aria-hidden="true" />
      <div style={styles.scanline} aria-hidden="true" />
      {backgroundNodes.map((node, index) => (
        <span
          key={index}
          style={{
            ...styles.backgroundNode,
            left: node.left,
            top: node.top,
            width: node.size,
            height: node.size,
            animationDelay: node.delay,
          }}
          aria-hidden="true"
        />
      ))}

      <section style={styles.shell}>
        <div style={styles.logoWrap}>
          <img src="/stagic-logo-gold-transparent.png" alt="StagicOSINT" style={styles.logo} />
          <div style={styles.logoGlow} aria-hidden="true" />
        </div>

        <div style={styles.centerStage}>
          <div style={styles.iconBox} aria-hidden="true">
            {current.icon === 'radar' && <RadarIcon />}
            {current.icon === 'target' && <TargetIcon />}
            {current.icon === 'analysis' && <AnalysisIcon />}
          </div>

          <p style={styles.eyebrow}>{current.eyebrow}</p>
          <h1 id="onboarding-title" style={styles.title}>{current.title}</h1>
          <p style={styles.body}>{current.body}</p>

          <div style={styles.dots} aria-label={`Walkthrough phase ${active + 1} of ${phases.length}`}>
            {phases.map((phase, index) => (
              <button
                key={phase.title}
                type="button"
                onClick={() => setActive(index)}
                aria-label={`Go to ${phase.title}`}
                style={{
                  ...styles.dot,
                  ...(active === index ? styles.dotActive : {}),
                }}
              />
            ))}
          </div>
        </div>

        <div style={styles.footer}>
          <button type="button" onClick={complete} style={styles.skipButton}>
            Skip Initialization
          </button>

          <button type="button" onClick={next} style={styles.nextButton}>
            {isFinal ? 'Enter Console' : 'Next Phase'}
            <span style={styles.arrow}>→</span>
          </button>
        </div>
      </section>
    </div>
  )
}

function RadarIcon() {
  return (
    <svg width="42" height="42" viewBox="0 0 42 42" fill="none">
      <circle cx="20" cy="20" r="12" stroke={GOLD} strokeWidth="3" />
      <circle cx="20" cy="20" r="5" stroke={GOLD} strokeWidth="3" />
      <path d="M29 29L37 37" stroke={GOLD} strokeWidth="4" strokeLinecap="round" />
      <path d="M20 20L28 13" stroke={GOLD} strokeWidth="3" strokeLinecap="round" />
      <path d="M14 13C10 17 10 23 14 27" stroke={GOLD} strokeWidth="3" strokeLinecap="round" opacity="0.72" />
    </svg>
  )
}

function TargetIcon() {
  return (
    <svg width="42" height="42" viewBox="0 0 42 42" fill="none">
      <circle cx="21" cy="21" r="13" stroke={GOLD} strokeWidth="3" />
      <circle cx="21" cy="21" r="5" stroke={GOLD} strokeWidth="3" />
      <path d="M21 3V10M21 32V39M3 21H10M32 21H39" stroke={GOLD} strokeWidth="3" strokeLinecap="round" />
      <path d="M27 15L34 8" stroke={GOLD} strokeWidth="3" strokeLinecap="round" />
    </svg>
  )
}

function AnalysisIcon() {
  return (
    <svg width="42" height="42" viewBox="0 0 42 42" fill="none">
      <path d="M7 31L15 22L22 27L34 11" stroke={GOLD} strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="7" cy="31" r="3" fill={GOLD} />
      <circle cx="15" cy="22" r="3" fill={GOLD} />
      <circle cx="22" cy="27" r="3" fill={GOLD} />
      <circle cx="34" cy="11" r="3" fill={GOLD} />
      <path d="M8 37H35" stroke={GOLD} strokeWidth="3" strokeLinecap="round" opacity="0.5" />
    </svg>
  )
}

const styles = {
  overlay: {
    position: 'fixed',
    inset: 0,
    zIndex: 5000,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '32px',
    background: `radial-gradient(circle at 50% 40%, rgba(255, 209, 101, 0.08), transparent 28%), linear-gradient(180deg, #031020 0%, ${NAVY} 48%, #020b18 100%)`,
    color: TEXT,
    overflow: 'hidden',
    fontFamily: 'Inter, Space Grotesk, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },
  gridBackdrop: {
    position: 'absolute',
    inset: 0,
    opacity: 0.24,
    backgroundImage: 'linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)',
    backgroundSize: '72px 72px',
    maskImage: 'radial-gradient(circle at center, black 0%, transparent 68%)',
  },
  scanline: {
    position: 'absolute',
    inset: 0,
    pointerEvents: 'none',
    background: 'linear-gradient(180deg, transparent 0%, rgba(255,209,101,0.035) 48%, transparent 100%)',
    animation: 'stagicScan 5s ease-in-out infinite',
  },
  backgroundNode: {
    position: 'absolute',
    borderRadius: 999,
    background: GOLD,
    boxShadow: `0 0 16px ${GOLD}`,
    opacity: 0.35,
    animation: 'stagicPulse 3.5s ease-in-out infinite',
  },
  shell: {
    position: 'relative',
    width: 'min(100%, 1040px)',
    minHeight: 640,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '64px 74px 48px',
    borderRadius: 8,
    border: '1px solid rgba(151, 174, 207, 0.16)',
    background: `linear-gradient(180deg, rgba(18, 32, 51, 0.96), rgba(10, 25, 43, 0.98)), ${CARD}`,
    boxShadow: '0 34px 90px rgba(0, 0, 0, 0.48), inset 0 1px 0 rgba(255, 255, 255, 0.035), 0 0 0 1px rgba(255, 209, 101, 0.035)',
    overflow: 'hidden',
  },
  logoWrap: {
    position: 'relative',
    width: 'min(330px, 70vw)',
    height: 82,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logo: {
    position: 'relative',
    zIndex: 2,
    maxWidth: '100%',
    maxHeight: 76,
    objectFit: 'contain',
    filter: 'drop-shadow(0 12px 24px rgba(255, 209, 101, 0.12))',
  },
  logoGlow: {
    position: 'absolute',
    inset: '22px 14%',
    borderRadius: 999,
    background: 'rgba(255, 209, 101, 0.13)',
    filter: 'blur(34px)',
  },
  centerStage: {
    width: '100%',
    maxWidth: 790,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    padding: '36px 0 48px',
  },
  iconBox: {
    width: 98,
    height: 98,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    border: '1px solid rgba(255, 209, 101, 0.12)',
    background: `linear-gradient(180deg, rgba(39, 54, 73, 0.86), rgba(18, 32, 51, 0.9)), ${CARD_HIGH}`,
    boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.03), 0 22px 42px rgba(0,0,0,0.28), 0 0 34px rgba(255, 209, 101, 0.06)',
    marginBottom: 34,
  },
  eyebrow: {
    margin: '0 0 12px',
    color: GOLD,
    fontFamily: 'Space Grotesk, Inter, sans-serif',
    fontSize: 12,
    lineHeight: 1,
    fontWeight: 800,
    letterSpacing: '0.22em',
    textTransform: 'uppercase',
  },
  title: {
    margin: 0,
    fontFamily: 'Space Grotesk, Inter, sans-serif',
    color: TEXT,
    fontSize: 'clamp(36px, 5vw, 56px)',
    lineHeight: 1.12,
    letterSpacing: '-0.035em',
    fontWeight: 800,
  },
  body: {
    margin: '28px auto 0',
    maxWidth: 770,
    color: MUTED,
    fontSize: 'clamp(16px, 2vw, 20px)',
    lineHeight: 1.55,
    fontWeight: 500,
  },
  dots: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    marginTop: 58,
  },
  dot: {
    width: 22,
    height: 5,
    padding: 0,
    border: 0,
    borderRadius: 999,
    background: 'rgba(211, 197, 172, 0.18)',
    cursor: 'pointer',
    transition: 'all 180ms ease',
  },
  dotActive: {
    width: 64,
    background: GOLD,
    boxShadow: '0 0 18px rgba(255, 209, 101, 0.65)',
  },
  footer: {
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 20,
    paddingTop: 30,
    borderTop: '1px solid rgba(151, 174, 207, 0.1)',
  },
  skipButton: {
    border: 0,
    background: 'transparent',
    color: MUTED,
    fontFamily: 'Space Grotesk, Inter, sans-serif',
    fontSize: 13,
    fontWeight: 800,
    letterSpacing: '0.16em',
    textTransform: 'uppercase',
    cursor: 'pointer',
    padding: '14px 6px',
  },
  nextButton: {
    minWidth: 198,
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 14,
    border: '1px solid rgba(255, 209, 101, 0.32)',
    borderRadius: 4,
    background: `linear-gradient(180deg, #ffdc72, ${GOLD})`,
    color: '#3f2e00',
    boxShadow: '0 12px 34px rgba(255, 209, 101, 0.15)',
    padding: '15px 26px',
    fontFamily: 'Space Grotesk, Inter, sans-serif',
    fontSize: 13,
    fontWeight: 900,
    letterSpacing: '0.15em',
    textTransform: 'uppercase',
    cursor: 'pointer',
  },
  arrow: {
    fontSize: 24,
    lineHeight: 0,
    transform: 'translateY(-1px)',
  },
}

const css = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@500;600;700;800&display=swap');

  @keyframes stagicPulse {
    0%, 100% { transform: scale(1); opacity: 0.22; }
    50% { transform: scale(1.9); opacity: 0.48; }
  }

  @keyframes stagicScan {
    0%, 100% { transform: translateY(-120%); opacity: 0; }
    25%, 70% { opacity: 1; }
    100% { transform: translateY(120%); opacity: 0; }
  }

  @media (max-width: 720px) {
    [role="dialog"] section {
      min-height: auto !important;
      padding: 40px 24px 28px !important;
    }

    [role="dialog"] section > div:last-child {
      flex-direction: column-reverse !important;
      align-items: stretch !important;
    }

    [role="dialog"] button {
      width: 100%;
    }
  }
`

export const resetOnboarding = () => {
  if (typeof window === 'undefined') return
  window.localStorage.removeItem(STORAGE_KEY)
}
