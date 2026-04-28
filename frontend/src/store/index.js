/**
 * OGI Zustand Store
 */
import { create } from 'zustand'
import api from '../api/client'

export const useStore = create((set, get) => ({
  // ----- Graphs -----
  graphs: [],
  activeGraphId: null,
  activeGraph: null,
  loadingGraph: false,

  fetchGraphs: async () => {
    const graphs = await api.listGraphs()
    set({ graphs })
  },

  createGraph: async (name, description) => {
    const graph = await api.createGraph(name, description)
    set(s => ({ graphs: [graph, ...s.graphs] }))
    return graph
  },

  setActiveGraph: async (id) => {
    if (!id) return set({ activeGraphId: null, activeGraph: null })
    set({ loadingGraph: true, activeGraphId: id })
    const graph = await api.getGraph(id)
    set({ activeGraph: graph, loadingGraph: false })
    return graph
  },

  refreshActiveGraph: async () => {
    const id = get().activeGraphId
    if (!id) return
    const graph = await api.getGraph(id)
    set({ activeGraph: graph })
  },

  deleteGraph: async (id) => {
    await api.deleteGraph(id)
    set(s => ({
      graphs: s.graphs.filter(g => g.id !== id),
      activeGraphId: s.activeGraphId === id ? null : s.activeGraphId,
      activeGraph: s.activeGraphId === id ? null : s.activeGraph,
    }))
  },

  // ----- Entities -----
  selectedEntityId: null,

  selectEntity: (id) => set({ selectedEntityId: id }),

  addEntity: async (type, value, label) => {
    const graphId = get().activeGraphId
    if (!graphId) return
    const entity = await api.createEntity(graphId, { type, value, label: label || value })
    set(s => ({
      activeGraph: s.activeGraph
        ? { ...s.activeGraph, entities: [...(s.activeGraph.entities || []), entity] }
        : s.activeGraph,
    }))
    return entity
  },

  deleteEntity: async (entityId) => {
    const graphId = get().activeGraphId
    if (!graphId) return
    await api.deleteEntity(graphId, entityId)
    set(s => ({
      activeGraph: s.activeGraph ? {
        ...s.activeGraph,
        entities: s.activeGraph.entities.filter(e => e.id !== entityId),
        edges: s.activeGraph.edges.filter(e => e.source_id !== entityId && e.target_id !== entityId),
      } : s.activeGraph,
      selectedEntityId: s.selectedEntityId === entityId ? null : s.selectedEntityId,
    }))
  },

  updateEntityPosition: async (entityId, x, y) => {
    const graphId = get().activeGraphId
    if (!graphId) return
    await api.updateEntity(graphId, entityId, { x, y })
    set(s => ({
      activeGraph: s.activeGraph ? {
        ...s.activeGraph,
        entities: s.activeGraph.entities.map(e => e.id === entityId ? { ...e, x, y } : e),
      } : s.activeGraph,
    }))
  },

  // ----- Transforms -----
  transforms: [],
  runningTransform: false,
  lastTransformResult: null,

  fetchTransforms: async () => {
    const transforms = await api.listTransforms()
    set({ transforms })
  },

  runTransform: async (entityId, transformName, options = {}) => {
    const graphId = get().activeGraphId
    if (!graphId) return
    set({ runningTransform: true, lastTransformResult: null })
    try {
      const result = await api.runTransform(graphId, entityId, transformName, options)
      set({ lastTransformResult: result })
      if (result.success) {
        await get().refreshActiveGraph()
      }
      return result
    } finally {
      set({ runningTransform: false })
    }
  },

  // ----- API Keys -----
  apiKeys: [],

  fetchApiKeys: async () => {
    const keys = await api.listApiKeys()
    set({ apiKeys: keys })
  },

  addApiKey: async (name, key, description) => {
    const apiKey = await api.addApiKey(name, key, description)
    set(s => ({ apiKeys: [...s.apiKeys, apiKey] }))
  },

  deleteApiKey: async (id) => {
    await api.deleteApiKey(id)
    set(s => ({ apiKeys: s.apiKeys.filter(k => k.id !== id) }))
  },

  // ----- UI State -----
  sidebarView: 'graphs',   // 'graphs' | 'entity' | 'transforms' | 'apikeys'
  setSidebarView: (view) => set({ sidebarView: view }),

  toast: null,
  showToast: (message, type = 'info') => {
    set({ toast: { message, type, id: Date.now() } })
    setTimeout(() => set({ toast: null }), 3500)
  },
}))
