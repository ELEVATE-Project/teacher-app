import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { sessionsApi } from '../../api/dashboardApi'
import SuggestionCard from '../../components/dashboard/SuggestionCard'
import RatingPopup from '../../components/dashboard/RatingPopup'

function LiveSession() {
  const { sessionId } = useParams()
  const navigate = useNavigate()

  const [session, setSession] = useState(null)
  const [suggestion, setSuggestion] = useState(null)
  const [loading, setLoading] = useState(true)
  const [fetchingNext, setFetchingNext] = useState(false)
  const [showRating, setShowRating] = useState(false)
  const [questionsAsked, setQuestionsAsked] = useState(0)
  const [sessionEnded, setSessionEnded] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadSession()
  }, [sessionId])

  const loadSession = async () => {
    try {
      const data = await sessionsApi.get(sessionId)
      setSession(data)
      if (data.is_active) {
        fetchNextSuggestion()
      } else {
        setSessionEnded(true)
        setLoading(false)
      }
    } catch (error) {
      console.error('Failed to load session:', error)
      setError('Session not found')
      setLoading(false)
    }
  }

  const fetchNextSuggestion = useCallback(async () => {
    setFetchingNext(true)
    try {
      const data = await sessionsApi.getNext(sessionId)
      setSuggestion(data)
      setError(null)
    } catch (error) {
      if (error.message.includes('No more students')) {
        setSuggestion(null)
      } else {
        console.error('Failed to get suggestion:', error)
      }
    } finally {
      setFetchingNext(false)
      setLoading(false)
    }
  }, [sessionId])

  const handleAsk = () => {
    setShowRating(true)
  }

  const handleSkip = async () => {
    if (!suggestion) return

    try {
      // Pass the difficulty from the suggestion
      await sessionsApi.skip(sessionId, suggestion.student_id, suggestion.difficulty)
      fetchNextSuggestion()
    } catch (error) {
      console.error('Failed to skip:', error)
    }
  }

  const handleRatingSubmit = async (rating) => {
    if (!suggestion) return

    try {
      await sessionsApi.respond(sessionId, {
        student_id: suggestion.student_id,
        question_id: suggestion.question_id,
        rating: rating,
        difficulty_asked: suggestion.difficulty,
        skipped: false
      })

      setQuestionsAsked(prev => prev + 1)
      setShowRating(false)
      fetchNextSuggestion()
    } catch (error) {
      console.error('Failed to submit response:', error)
    }
  }

  const handleEndSession = async () => {
    if (!confirm('End this class session?')) return

    try {
      await sessionsApi.end(sessionId)
      setSessionEnded(true)
      navigate(`/dashboard/summary/${sessionId}`)
    } catch (error) {
      console.error('Failed to end session:', error)
    }
  }

  const handleViewSummary = () => {
    navigate(`/dashboard/summary/${sessionId}`)
  }

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (showRating) return

      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        if (suggestion) handleAsk()
      } else if (e.key === 's' || e.key === 'S') {
        e.preventDefault()
        if (suggestion) handleSkip()
      } else if (e.key === 'Escape') {
        e.preventDefault()
        handleEndSession()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [suggestion, showRating])

  if (loading) {
    return (
      <div className="dash-loading-container">
        <div className="dash-spinner"></div>
        <p>Loading session...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dash-error-container">
        <h2>{error}</h2>
        <button className="dash-btn dash-btn-primary" onClick={() => navigate('/dashboard')}>
          Go Back
        </button>
      </div>
    )
  }

  return (
    <div className="dash-fade-in" style={{ minHeight: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
      {/* Session Header */}
      <div className="dash-session-header">
        <div className="dash-session-info">
          <h1>{session?.topic}</h1>
          <div className="dash-session-stats">
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--dash-primary)', lineHeight: 1 }}>{questionsAsked}</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--dash-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: 'var(--dash-space-xs)' }}>Questions Asked</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <div className={`dash-status-indicator ${session?.is_active ? 'active' : ''}`}>
                <span className="dash-pulse"></span>
                {session?.is_active ? 'Live' : 'Ended'}
              </div>
            </div>
          </div>
        </div>

        <button
          className="dash-btn dash-btn-secondary"
          onClick={sessionEnded ? handleViewSummary : handleEndSession}
        >
          {sessionEnded ? (
            <>
              View Summary
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </>
          ) : (
            <>
              End Session
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
              </svg>
            </>
          )}
        </button>
      </div>

      {/* Main Content */}
      <div className="dash-session-content">
        {sessionEnded ? (
          <div className="dash-session-ended">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            <h2>Session Complete!</h2>
            <p>You asked {questionsAsked} questions in this session.</p>
            <button className="dash-btn dash-btn-primary dash-btn-lg" onClick={handleViewSummary}>
              View Class Summary
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>
          </div>
        ) : (
          <>
            <SuggestionCard
              suggestion={suggestion}
              loading={fetchingNext}
              onAsk={handleAsk}
              onSkip={handleSkip}
            />

            {/* Keyboard Shortcuts Help */}
            <div className="dash-shortcuts-help">
              <span><span className="dash-kbd">Enter</span> Ask</span>
              <span><span className="dash-kbd">S</span> Skip</span>
              <span><span className="dash-kbd">Esc</span> End Session</span>
            </div>
          </>
        )}
      </div>

      {/* Rating Popup */}
      {showRating && suggestion && (
        <RatingPopup
          studentName={suggestion.student_name}
          difficulty={suggestion.difficulty}
          onSubmit={handleRatingSubmit}
          onCancel={() => setShowRating(false)}
        />
      )}
    </div>
  )
}

export default LiveSession

