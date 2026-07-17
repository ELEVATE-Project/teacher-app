import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { analyticsApi } from '../../api/dashboardApi'
import StarRating from './StarRating'

function ClassDashboard({ classId }) {
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showAllSessions, setShowAllSessions] = useState(false)
  const [sessionHistory, setSessionHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  
  useEffect(() => {
    if (classId) {
      loadDashboard()
    }
  }, [classId])
  
  const loadDashboard = async () => {
    setLoading(true)
    try {
      const data = await analyticsApi.getClassDashboard(classId)
      setDashboard(data)
    } catch (error) {
      console.error('Failed to load dashboard:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const loadSessionHistory = async () => {
    if (sessionHistory.length > 0) {
      setShowAllSessions(!showAllSessions)
      return
    }
    
    setLoadingHistory(true)
    try {
      const data = await analyticsApi.getClassHistory(classId, 20)
      setSessionHistory(data.history || [])
      setShowAllSessions(true)
    } catch (error) {
      console.error('Failed to load session history:', error)
    } finally {
      setLoadingHistory(false)
    }
  }
  
  if (loading) {
    return (
      <div className="dash-loading-container">
        <div className="dash-spinner"></div>
        <p>Loading statistics...</p>
      </div>
    )
  }
  
  if (!dashboard || !dashboard.has_data) {
    return (
      <div className="dash-empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 3v18h18"/>
          <path d="M18 17V9"/>
          <path d="M13 17V5"/>
          <path d="M8 17v-3"/>
        </svg>
        <p>No session data yet</p>
        <span>Start a class session to see statistics</span>
      </div>
    )
  }

  return (
    <div className="dash-fade-in" style={{ padding: 'var(--dash-space-md)' }}>
      {/* Quick Stats */}
      <div className="dash-stats-row">
        <div className="dash-stat-box">
          <span className="dash-stat-value">{dashboard.total_students}</span>
          <span className="dash-stat-label">Students</span>
        </div>
        <div className="dash-stat-box">
          <span className="dash-stat-value">{dashboard.avg_confidence.toFixed(1)}</span>
          <span className="dash-stat-label">Avg Confidence</span>
        </div>
        <div className="dash-stat-box">
          <span className="dash-stat-value">{dashboard.total_sessions}</span>
          <span className="dash-stat-label">Sessions</span>
        </div>
        <div className="dash-stat-box">
          <span className="dash-stat-value">{dashboard.all_time_avg_rating.toFixed(1)}</span>
          <span className="dash-stat-label">Avg Rating</span>
        </div>
      </div>
      
      {/* Level Distribution */}
      <div style={{ marginBottom: 'var(--dash-space-lg)' }}>
        <h4 style={{ fontSize: '0.875rem', fontWeight: 700, marginBottom: 'var(--dash-space-sm)', color: 'var(--dash-text-secondary)' }}>Student Levels</h4>
        <div className="dash-level-bars">
          <div className="dash-level-bar-row">
            <span className="dash-level-label weak">Weak</span>
            <div className="dash-level-bar-track">
              <div 
                className="dash-level-bar-fill weak" 
                style={{ width: `${(dashboard.level_distribution.weak / dashboard.total_students) * 100}%` }}
              />
            </div>
            <span className="dash-level-count">{dashboard.level_distribution.weak}</span>
          </div>
          <div className="dash-level-bar-row">
            <span className="dash-level-label medium">Medium</span>
            <div className="dash-level-bar-track">
              <div 
                className="dash-level-bar-fill medium" 
                style={{ width: `${(dashboard.level_distribution.medium / dashboard.total_students) * 100}%` }}
              />
            </div>
            <span className="dash-level-count">{dashboard.level_distribution.medium}</span>
          </div>
          <div className="dash-level-bar-row">
            <span className="dash-level-label strong">Strong</span>
            <div className="dash-level-bar-track">
              <div 
                className="dash-level-bar-fill strong" 
                style={{ width: `${(dashboard.level_distribution.strong / dashboard.total_students) * 100}%` }}
              />
            </div>
            <span className="dash-level-count">{dashboard.level_distribution.strong}</span>
          </div>
        </div>
      </div>
      
      {/* Last Session */}
      {dashboard.last_session && (
        <div style={{ marginBottom: 'var(--dash-space-lg)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--dash-space-sm)' }}>
            <h4 style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--dash-text-secondary)', margin: 0 }}>Last Session</h4>
            <button 
              className="dash-btn dash-btn-secondary"
              onClick={loadSessionHistory}
              disabled={loadingHistory}
              style={{ padding: '4px 12px', fontSize: '0.75rem' }}
            >
              {loadingHistory ? 'Loading...' : showAllSessions ? 'Hide History' : 'See All Sessions'}
            </button>
          </div>
          <div className="dash-card" style={{ borderLeft: '4px solid var(--dash-accent)' }}>
            <div style={{ fontWeight: 600, fontSize: '1rem', marginBottom: 'var(--dash-space-xs)' }}>{dashboard.last_session.topic}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--dash-text-muted)', marginBottom: 'var(--dash-space-sm)' }}>
              {new Date(dashboard.last_session.date).toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'short',
                day: 'numeric'
              })}
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--dash-space-sm)', fontSize: '0.75rem', color: 'var(--dash-text-secondary)', marginBottom: 'var(--dash-space-sm)' }}>
              <span>{dashboard.last_session.total_questions} questions</span>
              <span>{dashboard.last_session.participation}/{dashboard.total_students} participated</span>
              <span>
                <StarRating value={Math.round(dashboard.last_session.avg_rating)} readonly size="small" />
              </span>
            </div>
            <Link to={`/dashboard/summary/${dashboard.last_session.session_id}`} style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--dash-text-primary)' }}>
              View Full Summary →
            </Link>
          </div>
          
          {/* Session History List */}
          {showAllSessions && sessionHistory.length > 0 && (
            <div className="dash-card dash-fade-in" style={{ marginTop: 'var(--dash-space-md)' }}>
              <h5 style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--dash-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 'var(--dash-space-sm)' }}>All Sessions</h5>
              {sessionHistory.map((session) => (
                <div key={session.session_id} style={{ display: 'flex', alignItems: 'center', gap: 'var(--dash-space-sm)', padding: 'var(--dash-space-sm)', background: 'var(--dash-surface-elevated)', border: '2px solid #000', marginBottom: 'var(--dash-space-xs)' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>{session.topic}</div>
                    <div style={{ fontSize: '0.625rem', color: 'var(--dash-text-muted)', marginTop: '2px' }}>
                      {new Date(session.started_at).toLocaleDateString('en-US', {
                        weekday: 'short',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--dash-space-xs)' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '2px 8px', background: 'var(--dash-surface)', border: '1px solid #000', fontSize: '0.625rem', fontWeight: 600 }}>
                      {session.questions_asked} Q
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '2px 8px', background: 'var(--dash-accent)', border: '1px solid #000', fontSize: '0.625rem', fontWeight: 600 }}>
                      ★ {session.average_rating.toFixed(1)}
                    </span>
                  </div>
                  <Link to={`/dashboard/summary/${session.session_id}`} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '28px', height: '28px', border: '2px solid #000', background: 'var(--dash-surface)' }}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
                      <path d="M9 18l6-6-6-6"/>
                    </svg>
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      
      {/* Top Performers & Needs Attention */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--dash-space-md)' }}>
        {dashboard.top_performers.length > 0 && (
          <div className="dash-card">
            <h4 style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--dash-success)', marginBottom: 'var(--dash-space-sm)', display: 'flex', alignItems: 'center', gap: 'var(--dash-space-xs)' }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
              Top Performers
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--dash-space-xs)' }}>
              {dashboard.top_performers.map((s, index) => (
                <Link key={s.id} to={`/dashboard/student/${s.id}`} style={{ display: 'flex', alignItems: 'center', gap: 'var(--dash-space-sm)', padding: 'var(--dash-space-xs) var(--dash-space-sm)', background: 'var(--dash-surface-elevated)', border: '1px solid #000', fontSize: '0.75rem', color: 'var(--dash-text-primary)', textDecoration: 'none' }}>
                  <span style={{ fontWeight: 700, color: 'var(--dash-accent)', width: '20px' }}>#{index + 1}</span>
                  <span style={{ flex: 1, fontWeight: 600 }}>{s.name}</span>
                  <span className={`dash-badge ${s.level === 'strong' ? 'dash-badge-strong' : s.level === 'medium' ? 'dash-badge-medium-level' : 'dash-badge-weak'}`}>
                    {s.confidence.toFixed(1)}
                  </span>
                </Link>
              ))}
            </div>
          </div>
        )}
        
        {dashboard.needs_attention.length > 0 && (
          <div className="dash-card">
            <h4 style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--dash-warning)', marginBottom: 'var(--dash-space-sm)', display: 'flex', alignItems: 'center', gap: 'var(--dash-space-xs)' }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              Needs Attention
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--dash-space-xs)' }}>
              {dashboard.needs_attention.slice(0, 3).map((s) => (
                <Link key={s.id} to={`/dashboard/student/${s.id}`} style={{ display: 'flex', alignItems: 'center', gap: 'var(--dash-space-sm)', padding: 'var(--dash-space-xs) var(--dash-space-sm)', background: 'var(--dash-surface-elevated)', border: '1px solid #000', fontSize: '0.75rem', color: 'var(--dash-text-primary)', textDecoration: 'none' }}>
                  <span style={{ flex: 1, fontWeight: 600 }}>{s.name}</span>
                  <span style={{ fontSize: '0.625rem', color: 'var(--dash-warning)' }}>
                    {s.consecutive_wrong >= 2 ? `${s.consecutive_wrong} wrong streak` : `Low: ${s.confidence.toFixed(1)}`}
                  </span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ClassDashboard

