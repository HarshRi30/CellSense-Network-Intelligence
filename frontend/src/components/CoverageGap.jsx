import { useEffect, useState } from 'react'
import axios from 'axios'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import './CoverageGap.css'

const API = 'http://127.0.0.1:8000'

export default function CoverageGap() {
  const [data,    setData]    = useState([])
  const [loading, setLoading] = useState(true)
  const [sort,    setSort]    = useState('gap_rank')

  useEffect(() => {
    axios.get(`${API}/api/coverage-gap`)
      .then(res => setData(res.data))
      .finally(() => setLoading(false))
  }, [])

  const sorted = [...data].sort((a, b) => {
    if (sort === 'gap_rank')     return a.gap_rank - b.gap_rank
    if (sort === 'total_towers') return b.total_towers - a.total_towers
    if (sort === 'towers_5g')    return b.towers_5g - a.towers_5g
    return 0
  })

  const top10gap = sorted.slice(0, 10)

  if (loading) return <div className="gap-loading">Loading coverage data...</div>

  return (
    <div className="gap-page">
      <div className="gap-header">
        <h2 className="gap-title">COVERAGE GAP ANALYSIS</h2>
        <div className="gap-sort">
          <span>Sort by:</span>
          {['gap_rank', 'total_towers', 'towers_5g'].map(s => (
            <button key={s} className={sort === s ? 'sort-btn active' : 'sort-btn'} onClick={() => setSort(s)}>
              {s === 'gap_rank' ? 'Gap Score' : s === 'total_towers' ? 'Tower Count' : '5G Towers'}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="gap-chart-wrap">
        <div className="chart-title">Top 10 Most Underserved States (sqkm per tower)</div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={top10gap} margin={{ top: 10, right: 20, left: 0, bottom: 60 }}>
            <XAxis dataKey="state_circle" tick={{ fill: '#7a9bc0', fontSize: 10 }} angle={-35} textAnchor="end" />
            <YAxis tick={{ fill: '#7a9bc0', fontSize: 10 }} />
            <Tooltip
              contentStyle={{ background: '#0e1420', border: '1px solid #1e2d45', borderRadius: 4 }}
              labelStyle={{ color: '#00d4ff' }}
              itemStyle={{ color: '#e2eaf5' }}
            />
            <Bar dataKey="sqkm_per_tower" radius={[3,3,0,0]}>
              {top10gap.map((_, i) => (
                <Cell key={i} fill={i === 0 ? '#ff4444' : i < 3 ? '#ff8800' : '#00d4ff'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Table */}
      <div className="gap-table-wrap">
        <table className="gap-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>State</th>
              <th>Total</th>
              <th>Jio</th>
              <th>Airtel</th>
              <th>Vi</th>
              <th>BSNL</th>
              <th>5G Towers</th>
              <th>sqkm/tower</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, i) => (
              <tr key={row.state_circle} className={i < 3 ? 'critical' : ''}>
                <td className="mono">#{row.gap_rank}</td>
                <td>{row.state_circle}</td>
                <td className="mono">{Number(row.total_towers).toLocaleString()}</td>
                <td className="mono jio">{Number(row.jio_towers).toLocaleString()}</td>
                <td className="mono airtel">{Number(row.airtel_towers).toLocaleString()}</td>
                <td className="mono vi">{Number(row.vi_towers).toLocaleString()}</td>
                <td className="mono">{Number(row.bsnl_towers || 0).toLocaleString()}</td>
                <td className="mono g5">{Number(row.towers_5g || 0).toLocaleString()}</td>
                <td className="mono">{row.sqkm_per_tower}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
