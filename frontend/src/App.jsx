import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import './App.css'
import { API_ENDPOINTS } from './config/api'

function App() {
  const [backendHealth, setBackendHealth] = useState(false)

  useEffect(() => {
    fetch(API_ENDPOINTS.health)
      .then(res => res.json())
      .then(data => setBackendHealth(data.pipeline_ready))
      .catch(err => console.log('Backend not running yet...'))
  }, [])

  return (
    <div className="App">
      <Dashboard />
      {backendHealth && (
        <div className="backend-status">✅ Backend Connected</div>
      )}
    </div>
  )
}

export default App
