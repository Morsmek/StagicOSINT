import { useState, useEffect } from 'react'
import { useStore } from '../store'
import { apiClient } from '../api/client'

export default function ApiKeysPanel() {
  const { apiKeys, setApiKeys, addToast } = useStore()
  const [form, setForm] = useState({ name: '', key: '', description: '' })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    apiClient.get('/api-keys').then(r => setApiKeys(r.data)).catch(() => {})
  }, [])

  async function handleAdd(e) {
    e.preventDefault()
    if (!form.name || !form.key) return
    setLoading(true)
    try {
      await apiClient.post('/api-keys', form)
      const r = await apiClient.get('/api-keys')
      setApiKeys(r.data)
      setForm({ name: '', key: '', description: '' })
      addToast('API key saved', 'success')
    } catch {
      addToast('Failed to save key', 'error')
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id) {
    try {
      await apiClient.delete(`/api-keys/${id}`)
      setApiKeys(apiKeys.filter(k => k.id !== id))
      addToast('Key removed', 'success')
    } catch {
      addToast('Failed to remove key', 'error')
    }
  }


  return (
    <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

      {/* Header */}
      <div>
        <div style={{ fontSize: '0.6rem', letterSpacing: '0.18em', color: '#e91e8c', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
          Configuration
        </div>
        <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff', letterSpacing: '0.06em' }}>
          API KEYS
        </div>
      </div>

      {/* Add form */}
      <form onSubmit={handleAdd} style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        <input
          placeholder="Key name (e.g. SHODAN_API_KEY)"
          value={form.name}
          onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          style={{
            background: '#110508', border: '1px solid #3a0820', borderRadius: 6,
            color: '#fff', padding: '0.45rem 0.65rem', fontSize: '0.78rem',
            outline: 'none', width: '100%', boxSizing: 'border-box'
          }}
        />
        <input
          placeholder="API key value"
          type="password"
          value={form.key}
          onChange={e => setForm(f => ({ ...f, key: e.target.value }))}
          style={{
            background: '#110508', border: '1px solid #3a0820', borderRadius: 6,
            color: '#fff', padding: '0.45rem 0.65rem', fontSize: '0.78rem',
            outline: 'none', width: '100%', boxSizing: 'border-box'
          }}
        />
        <input
          placeholder="Description (optional)"
          value={form.description}
          onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
          style={{
            background: '#110508', border: '1px solid #3a0820', borderRadius: 6,
            color: '#fff', padding: '0.45rem 0.65rem', fontSize: '0.78rem',
            outline: 'none', width: '100%', boxSizing: 'border-box'
          }}
        />

        <button
          type="submit"
          disabled={loading}
          style={{
            background: loading ? '#3a0820' : 'linear-gradient(90deg, #e91e8c, #c2185b)',
            color: '#fff', border: 'none', borderRadius: 6,
            padding: '0.5rem 0.9rem', fontSize: '0.75rem',
            fontWeight: 700, letterSpacing: '0.1em', cursor: 'pointer',
            textTransform: 'uppercase', transition: 'opacity 0.2s',
            opacity: loading ? 0.6 : 1
          }}
        >
          {loading ? 'Saving…' : '+ Add Key'}
        </button>
      </form>

      {/* Divider */}
      <div style={{ height: 1, background: 'linear-gradient(90deg, #e91e8c33, transparent)' }} />

      {/* Key list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {apiKeys.length === 0 && (
          <div style={{ color: '#66304a', fontSize: '0.75rem', textAlign: 'center', padding: '1rem 0' }}>
            No API keys configured
          </div>
        )}
        {apiKeys.map(k => (
          <div key={k.id} style={{
            background: '#0a0308', border: '1px solid #2a0715',
            borderRadius: 8, padding: '0.6rem 0.75rem',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem'
          }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#e91e8c', marginBottom: '0.1rem' }}>
                {k.name}
              </div>
              {k.description && (
                <div style={{ fontSize: '0.68rem', color: '#88446a', marginBottom: '0.15rem' }}>
                  {k.description}
                </div>
              )}
              <div style={{ fontSize: '0.68rem', color: '#66304a', fontFamily: 'monospace' }}>
                {k.key_masked}
              </div>
            </div>
            <button
              onClick={() => handleDelete(k.id)}
              title="Remove key"
              style={{
                background: 'none', border: '1px solid #3a0820', borderRadius: 5,
                color: '#e91e8c', cursor: 'pointer', padding: '0.25rem 0.5rem',
                fontSize: '0.7rem', flexShrink: 0,
                transition: 'background 0.2s'
              }}
              onMouseEnter={e => e.currentTarget.style.background = '#2a0715'}
              onMouseLeave={e => e.currentTarget.style.background = 'none'}
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      {/* Info note */}
      <div style={{
        background: '#0a0308', border: '1px solid #1a0510',
        borderRadius: 8, padding: '0.65rem 0.75rem',
        fontSize: '0.68rem', color: '#66304a', lineHeight: 1.6
      }}>
        Keys are stored locally in <span style={{ color: '#e91e8c' }}>ogi.db</span> and
        never leave your machine. Set via UI or environment variables.
      </div>

    </div>
  )
}
