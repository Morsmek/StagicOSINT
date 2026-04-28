/**
 * GraphCanvas3D — react-force-graph-3d
 * Glowing coloured spheres, SpriteText labels, animated edge particles.
 */
import React, { useCallback, useEffect, useRef, useMemo } from 'react'
import ForceGraph3D from 'react-force-graph-3d'
import SpriteText   from 'three-spritetext'
import { useStore } from '../store'
import api           from '../api/client'

const TYPE_COLORS = {
  Domain:'#3b82f6', IPAddress:'#ef4444', EmailAddress:'#f59e0b',
  Username:'#8b5cf6', Person:'#06b6d4', Organization:'#10b981',
  URL:'#6366f1', SocialMedia:'#ec4899', Hash:'#64748b',
  SSLCertificate:'#0ea5e9', Subdomain:'#7c3aed', Location:'#16a34a',
  ASNumber:'#b45309', Network:'#be123c', MXRecord:'#0369a1',
  NSRecord:'#0891b2', Nameserver:'#0d9488', HTTPHeader:'#4f46e5',
  PhoneNumber:'#ca8a04', Document:'#9333ea',
}
const getColor = t => TYPE_COLORS[t] || '#475569'

/* Node object: let the library render the sphere,
   we only extend it with a SpriteText label below. */
function makeNodeLabel(node) {
  const label   = node.label || node.value || ''
  const display = label.length > 22 ? label.slice(0, 20) + '…' : label
  const color   = getColor(node.type)

  const sprite = new SpriteText(display)
  sprite.color           = '#cbd5e1'
  sprite.textHeight      = 2.6
  sprite.fontFace        = '-apple-system, BlinkMacSystemFont, sans-serif'
  sprite.fontWeight      = '600'
  sprite.backgroundColor = 'rgba(6,12,24,0.7)'
  sprite.padding         = 2
  sprite.borderRadius    = 3
  sprite.borderWidth     = 0.4
  sprite.borderColor     = color
  sprite.position.y      = -10
  return sprite
}

export function GraphCanvas() {
  const activeGraph          = useStore(s => s.activeGraph)
  const selectedEntityId     = useStore(s => s.selectedEntityId)
  const selectEntity         = useStore(s => s.selectEntity)
  const updateEntityPosition = useStore(s => s.updateEntityPosition)
  const refreshActiveGraph   = useStore(s => s.refreshActiveGraph)
  const showToast            = useStore(s => s.showToast)
  const fgRef                = useRef()

  const graphData = useMemo(() => {
    if (!activeGraph) return { nodes: [], links: [] }
    return {
      nodes: (activeGraph.entities || []).map(e => ({
        id: e.id, type: e.type, value: e.value,
        label: e.label || e.value,
        _selected: e.id === selectedEntityId,
      })),
      links: (activeGraph.edges || []).map(edge => ({
        id: edge.id, source: edge.source_id,
        target: edge.target_id, relation: edge.relation,
      })),
    }
  }, [activeGraph, selectedEntityId])

  // Re-heat simulation on data change
  useEffect(() => {
    fgRef.current?.d3ReheatSimulation()
  }, [graphData.nodes.length, graphData.links.length])

  // Fly to selected node
  useEffect(() => {
    if (!selectedEntityId || !fgRef.current) return
    const node = graphData.nodes.find(n => n.id === selectedEntityId)
    if (node?.x != null) {
      fgRef.current.cameraPosition(
        { x: node.x + 80, y: node.y + 40, z: node.z + 80 },
        node, 800
      )
    }
  }, [selectedEntityId])

  const onNodeClick        = useCallback(node => selectEntity(node.id), [selectEntity])
  const onBackgroundClick  = useCallback(() => selectEntity(null),       [selectEntity])

  if (!activeGraph) {
    return (
      <div style={{ flex:1, display:'flex', alignItems:'center', justifyContent:'center',
        background:'#060c18', flexDirection:'column', gap:16 }}>
        <div style={{ fontSize:56 }}>🕸️</div>
        <div style={{ color:'#334155', fontSize:15, fontWeight:500 }}>
          Select or create a graph to begin
        </div>
      </div>
    )
  }

  return (
    <div style={{ flex:1, height:'100%', position:'relative', background:'#060c18' }}>
      <ForceGraph3D
        ref={fgRef}
        graphData={graphData}
        backgroundColor="#060c18"

        /* Nodes — library renders the sphere, we extend with a label sprite */
        nodeColor={n => n._selected ? '#60a5fa' : getColor(n.type)}
        nodeOpacity={0.92}
        nodeRelSize={5}
        nodeThreeObjectExtend={true}
        nodeThreeObject={makeNodeLabel}
        nodeLabel={n => `[${n.type}]  ${n.value}`}

        /* Edges */
        linkColor={() => '#1e3a5f'}
        linkWidth={1.2}
        linkOpacity={0.7}
        linkCurvature={0.2}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        linkDirectionalArrowColor={() => '#334155'}
        linkDirectionalParticles={2}
        linkDirectionalParticleWidth={2}
        linkDirectionalParticleSpeed={0.005}
        linkDirectionalParticleColor={l => {
          const srcId = typeof l.source === 'object' ? l.source.id : l.source
          const src   = graphData.nodes.find(n => n.id === srcId)
          return src ? getColor(src.type) : '#475569'
        }}

        /* Interaction */
        onNodeClick={onNodeClick}
        onBackgroundClick={onBackgroundClick}

        /* Simulation */
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
        cooldownTicks={120}
      />

      <div style={{
        position:'absolute', bottom:16, left:'50%',
        transform:'translateX(-50%)',
        color:'#334155', fontSize:11, pointerEvents:'none',
        background:'rgba(6,12,24,0.8)', padding:'4px 14px',
        borderRadius:20, border:'1px solid #1e293b', whiteSpace:'nowrap',
      }}>
        Drag to orbit · Scroll to zoom · Click to inspect
      </div>
    </div>
  )
}

export const nodeTypes = {}
