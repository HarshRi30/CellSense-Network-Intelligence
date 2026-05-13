import { useState } from 'react'
import Map from './components/Map'
import SearchPanel from './components/SearchPanel'
import ResultsPanel from './components/ResultsPanel'
import CoverageGap from './components/CoverageGap'
import './App.css'

export default function App() {
  const [view, setView]       = useState('network')   // 'network' | 'gap'
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [marker, setMarker]   = useState(null)

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="logo">
          <span className="logo-icon">◈</span>
          <span className="logo-text">CellSense</span>
          <span className="logo-tag">India Network Intelligence</span>
        </div>
        <nav className="nav">
          <button className={view === 'network' ? 'nav-btn active' : 'nav-btn'} onClick={() => setView('network')}>Network Selector</button>
          <button className={view === 'gap'     ? 'nav-btn active' : 'nav-btn'} onClick={() => setView('gap')}>Coverage Gap</button>
        </nav>
      </header>

      {/* Main */}
      <main className="main">
        {view === 'network' ? (
          <>
            <SearchPanel setResults={setResults} setLoading={setLoading} setMarker={setMarker} />
            <div className="map-area">
              <Map marker={marker} setMarker={setMarker} setResults={setResults} setLoading={setLoading} />
            </div>
            {(results || loading) && <ResultsPanel results={results} loading={loading} />}
          </>
        ) : (
          <CoverageGap />
        )}
      </main>
    </div>
  )
}
