import axios from 'axios'

const http = axios.create({ baseURL: '/api/v1/sdba' })

/**
 * Zero-knowledge hashing: the identifier is hashed with SHA-256 in the browser
 * using the Web Crypto API. Only the resulting digest ever leaves the client.
 */
export async function sha256Hex(value) {
  const data = new TextEncoder().encode(value.trim().toLowerCase())
  const buf = await crypto.subtle.digest('SHA-256', data)
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

export function maskEmail(email) {
  const e = email.trim()
  if (!e.includes('@')) return e
  const [local, domain] = e.split('@')
  const shown = local[0] || ''
  return `${shown}${'*'.repeat(Math.max(2, local.length - 1))}@${domain}`
}

export const api = {
  dashboard: () => http.get('/dashboard').then((r) => r.data),
  catalog: () => http.get('/catalog').then((r) => r.data),

  // Zero-knowledge scan: hash locally, send only the digest + masked label.
  scan: async ({ identifier, kind = 'email', monitor = false }) => {
    const hash = await sha256Hex(identifier)
    const label = kind === 'email' ? maskEmail(identifier) : identifier.trim().toLowerCase()
    return http.post('/scan', { hash, label, kind, monitor }).then((r) => r.data)
  },

  assets: () => http.get('/assets').then((r) => r.data),
  addAsset: async ({ identifier, kind = 'email' }) => {
    const hash = await sha256Hex(identifier)
    const label = kind === 'email' ? maskEmail(identifier) : identifier.trim().toLowerCase()
    return http.post('/assets', { hash, label, kind }).then((r) => r.data)
  },
  rescanAsset: (id) => http.post(`/assets/${id}/rescan`).then((r) => r.data),
  deleteAsset: (id) => http.delete(`/assets/${id}`).then((r) => r.data),

  vendors: () => http.get('/vendors').then((r) => r.data),
  addVendor: (name, domain) => http.post('/vendors', { name, domain }).then((r) => r.data),
  scanVendor: (id) => http.post(`/vendors/${id}/scan`).then((r) => r.data),
  deleteVendor: (id) => http.delete(`/vendors/${id}`).then((r) => r.data),

  alerts: (unacknowledged = false) =>
    http.get('/alerts', { params: { unacknowledged } }).then((r) => r.data),
  ackAlert: (id) => http.post(`/alerts/${id}/ack`).then((r) => r.data),
  ackAll: () => http.post('/alerts/ack-all').then((r) => r.data),

  audit: (limit = 100) => http.get('/audit', { params: { limit } }).then((r) => r.data),
  verifyAudit: () => http.get('/audit/verify').then((r) => r.data),
}
