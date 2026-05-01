/**
 * API Keys Panel - manage external service keys
 */
import React, { useEffect, useState } from 'react'
import { useStore } from '../../store'

const KEY_PRESETS = [
  { name: 'SHODAN_API_KEY', label: 'Shodan', description: 'Host/port scanning (ip_shodan transform)' },
  { name: 'VIRUSTOTAL_API_KEY', label: 'VirusTotal', description: 'File hash malware lookup' },
  { name: 'HUNTER_API_KEY', label: 'Hunter.io', description: 'Email discovery from domains' },
  { name: 'PROSPEO_API_KEY', label: 'Prospeo', description: 'Professional email finder from person and company data' },
  { name: 'IPINFO_TOKEN', label: 'IPInfo', description: 'Detailed IP geolocation' },
  { name: 'OPENCAGE_API_KEY', label: 'OpenCage', description: 'Geocoding for locations' },
]

export function ApiKeysPanel() {
  const apiKeys = useStore(s => s.apiKeys)
  const fetchApiKeys = useStore(s => s.fetchApiKeys)
  const addApiKey = useStore(s => s.addApiKey)
  const deleteApiKey = useStore(s => s.deleteApiKey)
  const showToast = useStore(s => s.showToast)

  const [form, setForm] = useState({ name: KEY_PRESETS[0].name, key: '', description: '' })
  const [saving, setSaving] = useState(false)

  useEffect(() => { fetchApiKeys() }, [])

  const storedNames = new Set(apiKeys.map(k => k.name))

  const handleSave = async (e) => {
    e.preventDefault()
    if (!form.key.trim()) return
    setSaving(true)
    try {
      await addApiKey(form.name, form.key.trim(), form.description)
      setForm(f => ({ ...f, key: '', description: '' }))
      showToast(`API key saved`, 'success')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Form */}
      <form onSubmit={handleSave} style={{ padding: 12, borderBottom: '1px solid #1e293b' }}>
        <div style={{ fontSize: 11, color: '#64748b', marginBottom: 8, letterSpacing: 0.5 }}>ADD API KEY</div>

        <select
          value={form.name}
          onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          style={{ ...inputStyle, width: '100%', marginBottom: 6 }}
        >
          {KEY_PRESETS.map(p => (
            <option key={p.name} value={p.name}>{p.label} ({p.name})</option>
          ))}
        </select>

        <input
          type="password"
          value={form.key}
          onChange={e => setForm(f => ({ ...f, key: e.target.value }))}
          placeholder="API key value"
          style={{ ...inputStyle, width: '100%', marginBottom: 8 }}
        />

        <button
          type="submit"
          disabled={saving || !form.key.trim()}
          style={{ background: '#3b82f6', border: 'none', borderRadius: 6, color: '#fff', padding: '7px 12px', fontSize: 13, cursor: 'pointer', width: '100%', fontWeight: 600 }}
        >
          {saving ? 'Saving…' : 'Save Key'}
        </button>
      </form>

      {/* Stored keys */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
        <div style={{ fontSize: 11, color: '#64748b', marginBottom: 8, letterSpacing: 0.5, paddingLeft: 4 }}>
          CONFIGURED KEYS
        </div>
        {KEY_PRESETS.map(preset => {
          const stored = apiKeys.find(k => k.name === preset.name)
          return (
            <div
              key={preset.name}
              style={{
                background: '#1e293b',
                borderRadius: 6,
                padding: '8px 10px',
                marginBottom: 6,
                border: `1px solid ${stored ? '#065f46' : '#334155'}`,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>{preset.label}</span>
                    {stored ? (
                      <span style={{ fontSize: 10, color: '#10b981', background: '#064e3b', padding: '1px 5px', borderRadius: 4 }}>✓ SET</span>
                    ) : (
                      <span style={{ fontSize: 10, color: '#6b7280', background: '#1f2937', padding: '1px 5px', borderRadius: 4 }}>NOT SET</span>
                    )}
                  </div>
                  <div style={{ color: '#475569', fontSize: 11, marginTop: 2 }}>{preset.description}</div>
                  {stored && (
                    <div style={{ color: '#6b7280', fontSize: 11, fontFamily: 'monospace', marginTop: 2 }}>
                      {stored.key_masked}
                    </div>
                  )}
                </div>
                {stored && (
                  <button
                    onClick={() => deleteApiKey(stored.id)}
                    style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: 14 }}
                    title="Remove key"
                  >
                    ✕
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

const inputStyle = {
  background: '#1e293b',
  border: '1px solid #334155',
  borderRadius: 6,
  color: '#e2e8f0',
  padding: '6px 10px',
  fontSize: 13,
  outline: 'none',
}
