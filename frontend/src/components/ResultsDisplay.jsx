import '../styles/ResultsDisplay.css'

export default function ResultsDisplay({ result }) {
  if (!result) return null

  const candidateInfo = result.candidate_info || {}
  const atsCheck = result.ats_check || {}
  const dimensions = result.dimension_scores || {}
  const finalScore = typeof result.final_score === 'number' ? result.final_score : 0

  const scoreColor = finalScore >= 0.7 ? 'green' : finalScore >= 0.5 ? 'orange' : 'red'

  return (
    <div className="results-display">
      <h2>📊 Results</h2>

      <div className="results-grid">
        {/* Candidate Info */}
        <div className="result-card">
          <h3>👤 Candidate Info</h3>
          <p><strong>Name:</strong> {candidateInfo.name || 'N/A'}</p>
          <p><strong>Email:</strong> {candidateInfo.email || 'N/A'}</p>
          <p><strong>Phone:</strong> {candidateInfo.phone || 'N/A'}</p>
        </div>

        {/* ATS Check */}
        <div className="result-card">
          <h3>✅ ATS Check</h3>
          <p><strong>Passed:</strong> {atsCheck.passed ? 'Yes' : 'No'}</p>
          {atsCheck.reasons && atsCheck.reasons.length > 0 && (
            <div className="ats-reasons">
              <strong>Reasons:</strong>
              <ul>
                {atsCheck.reasons.map((reason, i) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Dimension Scores */}
        <div className="result-card">
          <h3>📈 Dimensions</h3>
          {Object.keys(dimensions).length === 0 ? (
            <p>N/A</p>
          ) : (
            <ul>
              {Object.entries(dimensions).map(([key, value]) => (
                <li key={key}>
                  <strong>{key}:</strong> {typeof value === 'number' ? value.toFixed(2) : String(value)}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Final Score */}
        <div className="result-card final-score">
          <h3>🏆 Final Score</h3>
          <p style={{ color: scoreColor, fontWeight: 'bold', fontSize: '1.25rem' }}>
            {(finalScore * 100).toFixed(0)}%
          </p>
        </div>
      </div>
    </div>
  )
}
