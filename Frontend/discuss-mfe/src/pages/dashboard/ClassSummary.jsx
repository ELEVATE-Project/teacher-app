import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { analyticsApi } from '../../api/dashboardApi'
import StarRating from '../../components/dashboard/StarRating'

function ClassSummary() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  useEffect(() => {
    loadSummary()
  }, [sessionId])
  
  const loadSummary = async () => {
    try {
      const data = await analyticsApi.getSessionSummary(sessionId)
      setSummary(data)
    } catch (error) {
      console.error('Failed to load summary:', error)
      setError('Failed to load session summary')
    } finally {
      setLoading(false)
    }
  }
  
  const formatDuration = (minutes) => {
    if (minutes < 1) return 'Less than a minute'
    if (minutes < 60) return `${Math.round(minutes)} minutes`
    const hours = Math.floor(minutes / 60)
    const mins = Math.round(minutes % 60)
    return `${hours}h ${mins}m`
  }
  
  if (loading) {
    return (
      <div className="dash-loading-container">
        <div className="dash-spinner"></div>
        <p>Loading summary...</p>
      </div>
    )
  }
  
  if (error || !summary) {
    return (
      <div className="dash-error-container">
        <h2>{error || 'Summary not found'}</h2>
        <button className="dash-btn dash-btn-primary" onClick={() => navigate('/dashboard')}>
          Go Back
        </button>
      </div>
    )
  }

  return (
    <div className="dash-fade-in">
      <div className="dash-page-header">
        <button className="dash-btn dash-btn-secondary" onClick={() => navigate('/dashboard')}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
            <path d="M19 12H5"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          Back to Classes
        </button>
        <div>
          <h1>Session Summary</h1>
          <p>{summary.topic}</p>
        </div>
      </div>
      
      {/* Key Metrics */}
      <div className="dash-metrics-grid">
        <div className="dash-metric-card">
          <div className="dash-metric-icon participation">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </div>
          <div className="dash-metric-content">
            <span className="dash-metric-value">{summary.participation_percentage.toFixed(0)}%</span>
            <span className="dash-metric-label">Participation</span>
          </div>
          <div className="dash-metric-detail">
            {summary.students_called} of {summary.students_called + summary.students_not_called} students
          </div>
        </div>
        
        <div className="dash-metric-card">
          <div className="dash-metric-icon questions">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
          <div className="dash-metric-content">
            <span className="dash-metric-value">{summary.total_questions_asked}</span>
            <span className="dash-metric-label">Questions Asked</span>
          </div>
          <div className="dash-metric-detail">
            {formatDuration(summary.duration_minutes)}
          </div>
        </div>
        
        <div className="dash-metric-card">
          <div className="dash-metric-icon rating">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
          </div>
          <div className="dash-metric-content">
            <span className="dash-metric-value">{summary.average_rating.toFixed(1)}</span>
            <span className="dash-metric-label">Avg Rating</span>
          </div>
          <div className="dash-metric-detail">
            <StarRating value={Math.round(summary.average_rating)} readonly size="small" />
          </div>
        </div>
        
        <div className="dash-metric-card">
          <div className="dash-metric-icon improved">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
              <polyline points="17 6 23 6 23 12"/>
            </svg>
          </div>
          <div className="dash-metric-content">
            <span className="dash-metric-value">{summary.students_improved.length}</span>
            <span className="dash-metric-label">Students Improved</span>
          </div>
          <div className="dash-metric-detail">
            This session
          </div>
        </div>
      </div>
      
      {/* Difficulty Distribution */}
      <div className="dash-section-card">
        <h2>Difficulty Distribution</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--dash-space-md)' }}>
          {['easy', 'medium', 'hard'].map((diff) => {
            const count = summary.difficulty_distribution[diff] || 0
            const total = summary.total_questions_asked || 1
            const percentage = (count / total) * 100
            
            return (
              <div key={diff} style={{ display: 'flex', alignItems: 'center', gap: 'var(--dash-space-md)' }}>
                <span className={`dash-badge dash-badge-${diff}`} style={{ width: '70px', textAlign: 'center' }}>{diff}</span>
                <div style={{ flex: 1, height: '24px', background: 'var(--dash-surface-elevated)', border: '2px solid #000', overflow: 'hidden' }}>
                  <div 
                    style={{ height: '100%', background: diff === 'easy' ? 'var(--dash-easy)' : diff === 'medium' ? 'var(--dash-medium)' : 'var(--dash-hard)', transition: 'width 0.5s ease', width: `${percentage}%` }}
                  />
                </div>
                <span style={{ fontWeight: 700, width: '30px', textAlign: 'right' }}>{count}</span>
              </div>
            )
          })}
        </div>
      </div>
      
      {/* Student Lists */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--dash-space-lg)', marginBottom: 'var(--dash-space-lg)' }}>
        {/* Students Who Improved */}
        <div className="dash-section-card">
          <h2 style={{ color: 'var(--dash-success)' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
              <polyline points="17 6 23 6 23 12"/>
            </svg>
            Improved
          </h2>
          {summary.students_improved.length === 0 ? (
            <p style={{ color: 'var(--dash-text-muted)', fontSize: '0.875rem', textAlign: 'center', padding: 'var(--dash-space-lg)' }}>No students improved this session</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--dash-space-sm)' }}>
              {summary.students_improved.map((s) => (
                <Link 
                  key={s.student_id}
                  to={`/dashboard/student/${s.student_id}`}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 'var(--dash-space-sm) var(--dash-space-md)', border: '2px solid #000', textDecoration: 'none', color: 'var(--dash-text-primary)', background: 'var(--dash-surface)' }}
                >
                  <span style={{ fontWeight: 600 }}>{s.student_name}</span>
                  <span style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--dash-success)' }}>
                    +{s.confidence_change.toFixed(1)}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>
        
        {/* Students Needing Attention */}
        <div className="dash-section-card">
          <h2 style={{ color: 'var(--dash-warning)' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            Needs Attention
          </h2>
          {summary.students_need_attention.length === 0 ? (
            <p style={{ color: 'var(--dash-text-muted)', fontSize: '0.875rem', textAlign: 'center', padding: 'var(--dash-space-lg)' }}>All students are doing well!</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--dash-space-sm)' }}>
              {summary.students_need_attention.map((s) => (
                <Link 
                  key={s.student_id}
                  to={`/dashboard/student/${s.student_id}`}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 'var(--dash-space-sm) var(--dash-space-md)', border: '2px solid #000', textDecoration: 'none', color: 'var(--dash-text-primary)', background: 'var(--dash-surface)' }}
                >
                  <span style={{ fontWeight: 600 }}>{s.student_name}</span>
                  {s.times_called === 0 ? (
                    <span style={{ fontSize: '0.75rem', color: 'var(--dash-text-muted)', background: 'var(--dash-surface-elevated)', padding: '2px 8px', border: '1px solid #000' }}>Not called</span>
                  ) : (
                    <span style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--dash-error)' }}>
                      {s.confidence_change.toFixed(1)}
                    </span>
                  )}
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
      
      {/* All Students */}
      <div className="dash-section-card">
        <h2>All Student Performance</h2>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr', gap: 'var(--dash-space-md)', padding: 'var(--dash-space-sm) var(--dash-space-md)', fontWeight: 700, fontSize: '0.75rem', color: 'var(--dash-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', borderBottom: '2px solid #000', paddingBottom: 'var(--dash-space-md)', marginBottom: 'var(--dash-space-sm)' }}>
            <span>Student</span>
            <span>Times Called</span>
            <span>Avg Rating</span>
            <span>Change</span>
            <span>Homework</span>
          </div>
          {summary.all_student_summaries.map((s) => {
            const getHomeworkLevel = () => {
              if (s.times_called === 0) return null
              if (s.average_rating < 2.5) return 'easy'
              if (s.average_rating < 4) return 'medium'
              return 'hard'
            }
            const homeworkLevel = getHomeworkLevel()
            
            return (
              <Link 
                key={s.student_id}
                to={`/dashboard/student/${s.student_id}`}
                style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr', gap: 'var(--dash-space-md)', padding: 'var(--dash-space-sm) var(--dash-space-md)', alignItems: 'center', textDecoration: 'none', color: 'var(--dash-text-primary)', border: '2px solid transparent', marginBottom: '2px' }}
              >
                <span style={{ fontWeight: 600 }}>{s.student_name}</span>
                <span>{s.times_called}</span>
                <span>
                  {s.times_called > 0 ? (
                    <StarRating value={Math.round(s.average_rating)} readonly size="small" />
                  ) : (
                    '-'
                  )}
                </span>
                <span style={{ fontWeight: 700, color: s.confidence_change > 0 ? 'var(--dash-success)' : s.confidence_change < 0 ? 'var(--dash-error)' : 'inherit' }}>
                  {s.confidence_change > 0 ? '+' : ''}{s.confidence_change.toFixed(1)}
                </span>
                <span>
                  {homeworkLevel ? (
                    <span className={`dash-badge dash-badge-${homeworkLevel}`} style={{ fontSize: '0.7rem', padding: '4px 10px' }}>
                      {homeworkLevel === 'easy' ? 'Easy' : homeworkLevel === 'medium' ? 'Medium' : 'Hard'}
                    </span>
                  ) : (
                    '-'
                  )}
                </span>
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default ClassSummary

