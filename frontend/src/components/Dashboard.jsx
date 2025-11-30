import { useState, useEffect } from 'react'
import FileUpload from './FileUpload'
import JobRoleSelector from './JobRoleSelector'
import ResultsDisplay from './ResultsDisplay'
import { API_ENDPOINTS } from '../config/api'
import '../styles/Dashboard.css'

export default function Dashboard() {
  const [roles, setRoles] = useState([])
  const [selectedRole, setSelectedRole] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchJobRoles()
  }, [])

  const fetchJobRoles = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.jobRoles)
      const data = await response.json()
      setRoles(data.roles || [])
      if (data.roles?.length > 0) {
        setSelectedRole(data.roles[0])
      }
    } catch (err) {
      setError('Failed to fetch job roles')
    }
  }

  const handleFileUpload = async (file, candidateInfo) => {
    if (!selectedRole) {
      setError('Select a job role first')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('job_role', selectedRole)
    if (candidateInfo.name) formData.append('candidate_name', candidateInfo.name)
    if (candidateInfo.email) formData.append('candidate_email', candidateInfo.email)
    if (candidateInfo.linkedin) formData.append('candidate_linkedin', candidateInfo.linkedin)

    try {
      const response = await fetch(API_ENDPOINTS.process, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Processing failed')
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🤖 Recruitment Agent</h1>
        <p>AI-powered resume screening</p>
      </header>

      {error && <div className="error-message">{error}</div>}

      <div className="dashboard-container">
        <div className="upload-panel">
          <h2>📤 Upload Resume</h2>
          <JobRoleSelector
            roles={roles}
            selectedRole={selectedRole}
            onChange={setSelectedRole}
          />
          <FileUpload onUpload={handleFileUpload} loading={loading} />
        </div>

        <div className="stats-panel">
          <h3>📊 Stats</h3>
          <div className="stat-item">
            <span>Job Roles</span>
            <span className="stat-value">{roles.length}</span>
          </div>
          <div className="stat-item">
            <span>Status</span>
            <span className="stat-value">
              {loading ? '⏳ Processing' : '✅ Ready'}
            </span>
          </div>
        </div>
      </div>

      {result && <ResultsDisplay result={result} />}
    </div>
  )
}
