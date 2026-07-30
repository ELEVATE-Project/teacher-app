import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { studentsApi, analyticsApi } from '../../api/dashboardApi'
import StarRating from '../../components/dashboard/StarRating'

function StudentProfile() {
  const { studentId } = useParams()
  const navigate = useNavigate()

  const [profile, setProfile] = useState(null)
  const [progress, setProgress] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadData()
  }, [studentId])

  const loadData = async () => {
    try {
      const [profileData, progressData] = await Promise.all([
        studentsApi.getProfile(studentId),
        analyticsApi.getStudentProgress(studentId)
      ])
      setProfile(profileData)
      setProgress(progressData)
    } catch (error) {
      console.error('Failed to load student data:', error)
      setError('Student not found')
    } finally {
      setLoading(false)
    }
  }

  const getLevelBadgeClass = (level) => {
    switch (level) {
      case 'weak': return 'dash-badge-weak'
      case 'strong': return 'dash-badge-strong'
      default: return 'dash-badge-medium-level'
    }
  }

  const getInitials = (name) => {
    return name
      .split(' ')
      .map(part => part[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  const getAvatarColor = (name) => {
    const colors = [
      '#E57373', '#81C784', '#64B5F6', '#FFD54F',
      '#BA68C8', '#4DB6AC', '#FF8A65', '#A1887F'
    ]
    const index = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
    return colors[index % colors.length]
  }

  const getTrendIcon = (trend) => {
    if (trend > 0) {
      return (
        <svg className="dash-trend-up" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
          <polyline points="17 6 23 6 23 12" />
        </svg>
      )
    } else if (trend < 0) {
      return (
        <svg className="dash-trend-down" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
          <polyline points="17 18 23 18 23 12" />
        </svg>
      )
    }
    return (
      <svg className="dash-trend-stable" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="5" y1="12" x2="19" y2="12" />
      </svg>
    )
  }

  if (loading) {
    return (
      <div className="dash-loading-container">
        <div className="dash-spinner"></div>
        <p>Loading student profile...</p>
      </div>
    )
  }

  if (error || !profile) {
    return (
      <div className="dash-error-container">
        <h2>{error || 'Student not found'}</h2>
        <button className="dash-btn dash-btn-primary" onClick={() => navigate('/dashboard')}>
          Go Back
        </button>
      </div>
    )
  }

  const student = profile.student

  return (
    <div className="dash-fade-in" style={{ maxWidth: '900px', margin: '0 auto' }}>
      <div className="dash-page-header">
        <button className="dash-btn dash-btn-secondary" onClick={() => navigate(-1)}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
            <path d="M19 12H5" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          Back
        </button>
      </div>

      {/* Profile Header */}
      <div className="dash-profile-header">
        <div
          className="dash-profile-avatar"
          style={{ backgroundColor: getAvatarColor(student.name) }}
        >
          {getInitials(student.name)}
        </div>

        <div className="dash-profile-info">
          <h1>{student.name}</h1>
          <div className="dash-profile-meta">
            <span className={`dash-badge dash-badge-lg ${getLevelBadgeClass(student.level)}`}>
              {student.level}
            </span>
            <span className="dash-confidence-display">
              <span className="dash-confidence-label">Confidence:</span>
              <StarRating value={Math.round(student.confidence)} readonly size="small" />
              <span className="dash-confidence-value">{student.confidence.toFixed(1)}</span>
            </span>
          </div>
        </div>

        <div className="dash-profile-trend">
          {getTrendIcon(profile.improvement_trend)}
          <span style={{ fontWeight: 600, fontSize: '0.875rem', color: profile.improvement_trend > 0 ? 'var(--dash-success)' : profile.improvement_trend < 0 ? 'var(--dash-error)' : 'var(--dash-text-muted)' }}>
            {profile.improvement_trend > 0 ? 'Improving' : profile.improvement_trend < 0 ? 'Declining' : 'Stable'}
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--dash-space-md)', marginBottom: 'var(--dash-space-xl)' }}>
        <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: 'var(--dash-space-md)', padding: 'var(--dash-space-lg)' }}>
          <div style={{ width: '48px', height: '48px', border: '2px solid #000', background: 'var(--dash-surface-elevated)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="24" height="24">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '1.75rem', fontWeight: 700, lineHeight: 1 }}>{profile.total_responses}</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--dash-text-muted)', marginTop: 'var(--dash-space-xs)' }}>Total Responses</span>
          </div>
        </div>

        <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: 'var(--dash-space-md)', padding: 'var(--dash-space-lg)' }}>
          <div style={{ width: '48px', height: '48px', border: '2px solid #000', background: 'rgba(253, 224, 71, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#D97706' }}>
            <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '1.75rem', fontWeight: 700, lineHeight: 1 }}>{profile.average_rating.toFixed(1)}</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--dash-text-muted)', marginTop: 'var(--dash-space-xs)' }}>Average Rating</span>
          </div>
        </div>

        <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: 'var(--dash-space-md)', padding: 'var(--dash-space-lg)' }}>
          <div style={{ width: '48px', height: '48px', border: '2px solid #000', background: 'rgba(59, 130, 246, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--dash-info)' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="24" height="24">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '1.75rem', fontWeight: 700, lineHeight: 1 }}>{profile.participation_rate.toFixed(0)}%</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--dash-text-muted)', marginTop: 'var(--dash-space-xs)' }}>Participation Rate</span>
          </div>
        </div>

        <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: 'var(--dash-space-md)', padding: 'var(--dash-space-lg)' }}>
          <div style={{ width: '48px', height: '48px', border: '2px solid #000', background: 'rgba(34, 197, 94, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--dash-success)' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="24" height="24">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '1.75rem', fontWeight: 700, lineHeight: 1 }}>
              {student.consecutive_correct > 0 ? student.consecutive_correct : student.consecutive_wrong}
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--dash-text-muted)', marginTop: 'var(--dash-space-xs)' }}>
              {student.consecutive_correct > 0 ? 'Correct Streak' : 'Needs Help'}
            </span>
          </div>
        </div>
      </div>

      {/* Topic Performance - Top 3 */}
      <div className="dash-section-card">
        <h2>Top Topic Performance</h2>
        {student.topic_performance && Object.keys(student.topic_performance).length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 'var(--dash-space-md)' }}>
            {Object.entries(student.topic_performance)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 3)
              .map(([topic, score], index) => (
                <div key={topic} style={{
                  display: 'flex',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: 'var(--dash-space-md)',
                  padding: 'var(--dash-space-md)',
                  background: 'var(--dash-surface-elevated)',
                  border: '2px solid #000',
                  width: '100%',
                  boxSizing: 'border-box'
                }}>
                  <span style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--dash-primary)', flexShrink: 0 }}>#{index + 1}</span>
                  <span style={{ fontWeight: 600, flex: 1, minWidth: '120px' }}>{topic}</span>
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 'var(--dash-space-sm)',
                    flexShrink: 0,
                    background: 'var(--dash-surface)',
                    padding: '4px 8px',
                    border: '2px solid #000'
                  }}>
                    <StarRating value={Math.round(score)} readonly size="small" />
                    <span style={{ fontWeight: 700, color: 'var(--dash-accent)', fontSize: '0.875rem' }}>{score.toFixed(1)}</span>
                  </span>
                </div>
              ))}
          </div>
        ) : (
          <p style={{ color: 'var(--dash-text-muted)', textAlign: 'center', padding: 'var(--dash-space-lg)' }}>No topic performance data yet. Start a session to track topics!</p>
        )}
      </div>

      {/* Recent History */}
      <div className="dash-section-card">
        <h2>Recent Activity</h2>
        {!profile.recent_history?.length ? (
          <p style={{ color: 'var(--dash-text-muted)', textAlign: 'center', padding: 'var(--dash-space-lg)' }}>No recent activity</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--dash-space-sm)' }}>
            {profile.recent_history.map((item, index) => (
              <div key={index} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--dash-space-sm)', padding: 'var(--dash-space-md)', background: 'var(--dash-surface-elevated)', border: '2px solid #000' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                  <div>
                    <StarRating value={item.rating} readonly size="small" />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--dash-space-md)' }}>
                    {item.topic && (
                      <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--dash-surface)', background: 'var(--dash-primary)', padding: '2px 8px', whiteSpace: 'nowrap', maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.topic}</span>
                    )}
                    <span className={`dash-badge dash-badge-${item.difficulty}`}>
                      {item.difficulty}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--dash-text-muted)' }}>
                      {item.answered_at
                        ? new Date(item.answered_at).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })
                        : 'Unknown date'
                      }
                    </span>
                  </div>
                </div>
                {item.question_text && (
                  <div style={{ fontSize: '0.875rem', color: 'var(--dash-text-secondary)', padding: 'var(--dash-space-sm) var(--dash-space-md)', background: 'var(--dash-surface)', border: '2px solid #000', borderLeft: '4px solid var(--dash-accent)', lineHeight: 1.4 }}>
                    <span style={{ fontWeight: 700, color: 'var(--dash-accent)', marginRight: 'var(--dash-space-xs)' }}>Q:</span> {item.question_text}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Progress Timeline */}
      {progress && progress.progress?.length > 0 && (
        <div className="dash-section-card">
          <h2>Progress Timeline</h2>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 'var(--dash-space-md)', padding: 'var(--dash-space-lg) 0', overflowX: 'auto' }}>
            {progress.progress.slice(-10).map((item, index) => (
              <div
                key={index}
                style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--dash-space-sm)', minWidth: '50px' }}
              >
                <div style={{
                  width: '40px',
                  height: '40px',
                  border: '2px solid #000',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  color: 'white',
                  background: item.rating >= 4 ? 'var(--dash-success)' : item.rating <= 2 ? 'var(--dash-error)' : 'var(--dash-warning)'
                }}>
                  {item.rating}
                </div>
                <span style={{ fontSize: '0.625rem', textTransform: 'uppercase', color: 'var(--dash-text-muted)' }}>{item.difficulty}</span>
              </div>
            ))}
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--dash-text-muted)', textAlign: 'center', marginTop: 'var(--dash-space-sm)' }}>Last {Math.min(10, progress.progress.length)} responses</p>
        </div>
      )}
    </div>
  )
}

export default StudentProfile

