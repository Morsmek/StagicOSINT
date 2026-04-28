/**
 * OGI API Client
 */
import axios from 'axios'

const BASE = '/api/v1'

const http = axios.create({ baseURL: BASE })

// -------------------------------------------------------------------------
// Graphs
// -------------------------------------------------------------------------
export const api = {
  // Graphs
  listGraphs: () => http.get('/graphs').then(r => r.data),
  createGraph: (name, description = '') => http.post('/graphs', { name, description }).then(r => r.data),
  getGraph: (id) => http.get(`/graphs/${id}`).then(r => r.data),
  deleteGraph: (id) => http.delete(`/graphs/${id}`),
  graphStats: (id) => http.get(`/graphs/${id}/stats`).then(r => r.data),
  computeLayout: (id, opts = {}) => http.get(`/graphs/${id}/layout`, { params: opts }).then(r => r.data),
  shortestPath: (graphId, sourceId, targetId) =>
    http.get(`/graphs/${graphId}/path`, { params: { source_id: sourceId, target_id: targetId } }).then(r => r.data),
  exportGraph: (id) => http.get(`/graphs/${id}/export`).then(r => r.data),
  importGraph: (id, data) => http.post(`/graphs/${id}/import`, data).then(r => r.data),

  // Entities
  listEntities: (graphId) => http.get(`/graphs/${graphId}/entities`).then(r => r.data),
  createEntity: (graphId, entity) => http.post(`/graphs/${graphId}/entities`, entity).then(r => r.data),
  updateEntity: (graphId, entityId, updates) => http.patch(`/graphs/${graphId}/entities/${entityId}`, updates).then(r => r.data),
  deleteEntity: (graphId, entityId) => http.delete(`/graphs/${graphId}/entities/${entityId}`),

  // Edges
  createEdge: (graphId, edge) => http.post(`/graphs/${graphId}/edges`, edge).then(r => r.data),
  deleteEdge: (graphId, edgeId) => http.delete(`/graphs/${graphId}/edges/${edgeId}`),

  // Transforms
  listTransforms: () => http.get('/transforms').then(r => r.data),
  transformsForType: (type) => http.get(`/transforms/for/${type}`).then(r => r.data),
  runTransform: (graphId, entityId, transformName, options = {}) =>
    http.post('/transforms/run', { graph_id: graphId, entity_id: entityId, transform_name: transformName, options }).then(r => r.data),

  // API Keys
  listApiKeys: () => http.get('/api-keys').then(r => r.data),
  addApiKey: (name, key, description = '') => http.post('/api-keys', { name, key, description }).then(r => r.data),
  deleteApiKey: (id) => http.delete(`/api-keys/${id}`),
}

export default api
