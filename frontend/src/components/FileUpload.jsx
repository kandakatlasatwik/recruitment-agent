import { useRef, useState } from 'react'
import '../styles/FileUpload.css'

export default function FileUpload({ onUpload, loading }) {
  const fileInputRef = useRef(null)
  const [fileName, setFileName] = useState('')
  const [candidateInfo, setCandidateInfo] = useState({
    name: '',
    email: '',
    linkedin: ''
  })

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setFileName(file.name)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const file = fileInputRef.current?.files?.[0]
    if (file) {
      onUpload(file, candidateInfo)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setCandidateInfo(prev => ({
      ...prev,
      [name]: value
    }))
  }

  return (
    <form onSubmit={handleSubmit} className="file-upload">
      <div className="form-group">
        <label>Candidate Info (Optional)</label>
        <input
          type="text"
          name="name"
          placeholder="Full Name"
          value={candidateInfo.name}
          onChange={handleInputChange}
          className="form-input"
        />
        <input
          type="email"
          name="email"
          placeholder="Email"
          value={candidateInfo.email}
          onChange={handleInputChange}
          className="form-input"
        />
        <input
          type="text"
          name="linkedin"
          placeholder="LinkedIn URL"
          value={candidateInfo.linkedin}
          onChange={handleInputChange}
          className="form-input"
        />
      </div>

      <div className="drop-zone">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          disabled={loading}
          id="file-input"
          className="file-input"
        />
        <label htmlFor="file-input" className="drop-label">
          <p className="drop-icon">📄</p>
          <p className="drop-text">
            {fileName || 'Drag PDF or click to upload'}
          </p>
          <p className="drop-hint">Max 10MB</p>
        </label>
      </div>

      <button
        type="submit"
        disabled={loading || !fileName}
        className="submit-button"
      >
        {loading ? '⏳ Processing...' : '🚀 Analyze Resume'}
      </button>
    </form>
  )
}
