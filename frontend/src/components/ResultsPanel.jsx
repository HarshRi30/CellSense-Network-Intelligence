import './ResultsPanel.css'

const OP_COLORS = {
  Jio:    '#00d4ff',
  Airtel: '#ff6b35',
  Vi:     '#cc0066',
  BSNL:   '#00cc44',
}

const QUALITY_COLOR = {
  'Excellent': '#00ff88',
  'Good':      '#7dff7d',
  'Fair':      '#ffd700',
  'Poor':      '#ff8800',
  'No Signal': '#ff4444',
}

function SignalBars({ dbm }) {
  const strength = dbm >= -70 ? 4 : dbm >= -85 ? 3 : dbm >= -100 ? 2 : 1
  return (
    <div className="signal-bars">
      {[1,2,3,4].map(i => (
        <div key={i} className={`bar ${i <= strength ? 'active' : ''}`}
          style={{ height: `${i * 5 + 4}px`, background: i <= strength ? '#00ff88' : '#1e2d45' }}
        />
      ))}
    </div>
  )
}

export default function ResultsPanel({ results, loading }) {
  if (loading) return (
    <div className="results-panel">
      <div className="loading">
        <div className="spinner" />
        <span>Scanning towers...</span>
      </div>
    </div>
  )

  if (!results) return null

  return (
    <div className="results-panel">
      <div className="results-header">
        <span className="results-title">NETWORK SCAN</span>
        <span className="results-meta">{results.towers_checked?.toLocaleString()} towers analysed</span>
      </div>

      <div className="results-coords">
        {results.lat?.toFixed(4)}°N, {results.lng?.toFixed(4)}°E
      </div>

      <div className="operators-list">
        {results.ranked_operators?.map((op, i) => (
          <div key={op.operator} className={`operator-card ${i === 0 ? 'winner' : ''}`}>
            {i === 0 && <div className="winner-badge">BEST</div>}
            <div className="op-left">
              <div className="op-name" style={{ color: OP_COLORS[op.operator] || '#fff' }}>
                {op.operator}
              </div>
              <div className="op-radio">{op.radio_type} · {op.frequency_mhz} MHz</div>
              <div className="op-distance">{op.distance_km} km away</div>
            </div>
            <div className="op-right">
              <SignalBars dbm={op.signal_dbm} />
              <div className="op-dbm">{op.signal_dbm} dBm</div>
              <div className="op-quality" style={{ color: QUALITY_COLOR[op.quality] }}>
                {op.quality}
              </div>
              {op.predicted_speed_mbps && (
                <div className="op-speed">{op.predicted_speed_mbps} Mbps</div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="recommendation">
        ◈ Recommended: <strong style={{ color: OP_COLORS[results.recommendation] }}>
          {results.recommendation}
        </strong>
      </div>
    </div>
  )
}
