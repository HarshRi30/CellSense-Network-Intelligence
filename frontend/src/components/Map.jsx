import { useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import axios from 'axios'
import 'leaflet/dist/leaflet.css'
import './Map.css'

const API = 'https://cellsense-network-intelligence.onrender.com'

// Fix leaflet default icon
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// Custom marker icon
const pinIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  shadowSize: [41, 41],
})

// Component to fly to marker location
function FlyTo({ marker }) {
  const map = useMap()
  useEffect(() => {
    if (marker) map.flyTo([marker.lat, marker.lng], 14, { duration: 1.2 })
  }, [marker])
  return null
}

// Click handler component
function ClickHandler({ setMarker, setResults, setLoading }) {
  const map = useMap()
  useEffect(() => {
    map.on('click', async (e) => {
      const { lat, lng } = e.latlng
      setMarker({ lat, lng })
      setLoading(true)
      setResults(null)
      try {
        const res = await axios.post(`${API}/api/best-network`, { lat, lng, radius_m: 5000, indoor: false })
        setResults(res.data)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    })
    return () => map.off('click')
  }, [])
  return null
}

export default function Map({ marker, setMarker, setResults, setLoading }) {
  return (
    <MapContainer
      center={[20.5937, 78.9629]}
      zoom={5}
      className="leaflet-map"
      zoomControl={false}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
      />
      {marker && (
        <Marker position={[marker.lat, marker.lng]} icon={pinIcon}>
          <Popup>
            <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>
              {marker.lat.toFixed(4)}, {marker.lng.toFixed(4)}
            </span>
          </Popup>
        </Marker>
      )}
      <FlyTo marker={marker} />
      <ClickHandler setMarker={setMarker} setResults={setResults} setLoading={setLoading} />
    </MapContainer>
  )
}
