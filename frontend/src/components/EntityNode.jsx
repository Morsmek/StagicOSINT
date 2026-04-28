/**
 * EntityNode - Maltego-style node
 * Large icon on top, type badge, value label underneath.
 */
import React from 'react'
import { Handle, Position } from '@xyflow/react'

// Emoji icon per entity type
const TYPE_ICONS = {
  Domain:         '🌐',
  IPAddress:      '🖥️',
  EmailAddress:   '✉️',
  Username:       '👤',
  Person:         '🧑',
  Organization:   '🏢',
  URL:            '🔗',
  SocialMedia:    '📱',
  Hash:           '🔢',
  PhoneNumber:    '📞',
  Document:       '📄',
  Location:       '📍',
  ASNumber:       '🔌',
  Network:        '🕸️',
  MXRecord:       '📬',
  NSRecord:       '📡',
  Nameserver:     '🗄️',
  SSLCertificate: '🔒',
  Subdomain:      '🌿',
  HTTPHeader:     '📋',
}

// Accent color per type (used for icon ring + border glow)
const TYPE_COLORS = {
  Domain:         '#3b82f6',
  IPAddress:      '#ef4444',
  EmailAddress:   '#f59e0b',
  Username:       '#8b5cf6',
  Person:         '#06b6d4',
  Organization:   '#10b981',
  URL:            '#6366f1',
  SocialMedia:    '#ec4899',
  Hash:           '#64748b',
  SSLCertificate: '#0ea5e9',
  Subdomain:      '#7c3aed',
  Location:       '#16a34a',
  ASNumber:       '#b45309',
  Network:        '#be123c',
  MXRecord:       '#0369a1',
  NSRecord:       '#0891b2',
  Nameserver:     '#0d9488',
  HTTPHeader:     '#4f46e5',
  PhoneNumber:    '#ca8a04',
  Document:       '#9333ea',
  default:        '#475569',
}

export function EntityNode({ data, selected }) {
  const { entity } = data
  const icon  = TYPE_ICONS[entity.type]  || '❓'
  const color = TYPE_COLORS[entity.type] || TYPE_COLORS.default
  const label = entity.label || entity.value
  const display = label.length > 22 ? label.slice(0, 20) + '…' : label

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 6,
      padding: '4px 2px 6px',
      cursor: 'pointer',
      userSelect: 'none',
      width: 90,
    }}>
      <Handle
        type="target"
        position={Position.Top}
        style={{ background: color, width: 6, height: 6, border: 'none', top: 4 }}
      />

      {/* Icon circle */}
      <div style={{
        width: 54,
        height: 54,
        borderRadius: '50%',
        background: '#0f172a',
        border: `2.5px solid ${color}`,
        boxShadow: selected
          ? `0 0 0 3px ${color}55, 0 0 16px ${color}88`
          : `0 0 8px ${color}44`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 24,
        transition: 'box-shadow 0.2s',
        flexShrink: 0,
      }}>
        {icon}
      </div>

      {/* Type badge */}
      <div style={{
        background: color,
        color: '#fff',
        borderRadius: 3,
        padding: '1px 6px',
        fontSize: 9,
        fontWeight: 700,
        letterSpacing: 0.8,
        textTransform: 'uppercase',
      }}>
        {entity.type}
      </div>

      {/* Value label */}
      <div style={{
        color: selected ? '#e2e8f0' : '#94a3b8',
        fontSize: 11,
        fontWeight: 500,
        textAlign: 'center',
        maxWidth: 90,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        lineHeight: 1.3,
        transition: 'color 0.15s',
      }}>
        {display}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        style={{ background: color, width: 6, height: 6, border: 'none', bottom: 4 }}
      />
    </div>
  )
}

export const nodeTypes = { entity: EntityNode }
