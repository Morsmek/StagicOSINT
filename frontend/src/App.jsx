import React from 'react'
import { Toolbar }     from './components/Toolbar'
import { Sidebar }     from './components/Sidebar'
import { GraphCanvas } from './components/GraphCanvas'
import { Toast }       from './components/Toast'
import { OnboardingSplash } from './components/OnboardingSplash'

class GraphErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { error: null } }
  static getDerivedStateFromError(e) { return { error: e } }
  render() {
    if (this.state.error) {
      return (
        <div style={{ flex:1, display:'flex', alignItems:'center', justifyContent:'center',
          flexDirection:'column', gap:12, background:'#060c18', color:'#475569' }}>
          <div style={{ fontSize:40 }}>⚠️</div>
          <div style={{ fontSize:14, fontWeight:600, color:'#ef4444' }}>3D canvas error</div>
          <div style={{ fontSize:12, maxWidth:340, textAlign:'center', lineHeight:1.6 }}>
            {this.state.error?.message || 'Unknown error'}
          </div>
          <button onClick={() => this.setState({ error: null })}
            style={{ marginTop:8, background:'#1e293b', border:'1px solid #334155',
              borderRadius:6, color:'#94a3b8', padding:'6px 16px', cursor:'pointer', fontSize:12 }}>
            Retry
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

export default function App() {
  return (
    <div style={{ display:'flex', flexDirection:'column',
      height:'100vh', width:'100vw', overflow:'hidden', background:'#060c18' }}>
      <Toolbar />
      <div style={{ display:'flex', flex:1, overflow:'hidden' }}>
        <Sidebar />
        <GraphErrorBoundary>
          <GraphCanvas />
        </GraphErrorBoundary>
      </div>
      <Toast />
      <OnboardingSplash />
    </div>
  )
}
