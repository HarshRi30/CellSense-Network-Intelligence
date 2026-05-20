import { useState } from 'react'
import axios from 'axios'
import './SearchPanel.css'

const API = 'https://cellsense-network-intelligence.onrender.com'
export default function SearchPanel({ setResults, setLoading, setMarker }) {
  const [query, setQuery] = useState('')
  const [indoor, setIndoor] = useState(false)
  const [radius, setRadius] = useState(5000)

  async function geocode(address) {
    const res = await axios.get(
      `https://nominatim.openstreetmap.org/search`,
      { params: { q: address + ', India', format: 'json', limit: 1 } }
    )
    if (!res.data.length) throw new Error('Location not found')
    return { lat: parseFloat(res.data[0].lat), lng: parseFloat(res.data[0].lon) }
  }

  async function handleSearch() {
    if (!query.trim()) return
    setLoading(true)
    setResults(null)
    try {
      const { lat, lng } = await geocode(query)
      setMarker({ lat, lng })
      const res = await axios.post(`${API}/api/best-network`, { lat, lng, radius_m: radius, indoor }, { timeout: 60000 })
      setResults(res.data)
    } catch (e) {
      alert(e.message || 'Error fetching data')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="search-panel">
      <div className="search-row">
        <input
          className="search-input"
          placeholder="Enter city, area or landmark..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
        />
        <button className="search-btn" onClick={handleSearch}>SCAN</button>
      </div>
      <div className="search-options">
        <label className="toggle">
          <input type="checkbox" checked={indoor} onChange={e => setIndoor(e.target.checked)} />
          <span>Indoor</span>
        </label>
        <label className="toggle">
          <span>Radius:</span>
          <select value={radius} onChange={e => setRadius(Number(e.target.value))}>
            <option value={2000}>2 km</option>
            <option value={5000}>5 km</option>
            <option value={10000}>10 km</option>
          </select>
        </label>
      </div>
    </div>
  )
}
