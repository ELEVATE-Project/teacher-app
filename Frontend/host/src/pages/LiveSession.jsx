import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { sessionsApi } from '../utils/classroomApi'
import SuggestionCard from '../components/SuggestionCard'
import RatingPopup from '../components/RatingPopup'

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
      if (error.response?.data?.detail?.includes('No more students') || error.message?.includes('No more students')) {
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
      await sessionsApi.skip(sessionId, suggestion.student_id)
      fetchNextSuggestion()
    } catch (error) {
      console.error('Failed to skip:', error)
      alert('Failed to skip student. Make sure the backend is running.')
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
      alert('Failed to submit rating. Make sure the backend is running.')
    }
  }
  
  const handleEndSession = async () => {
    if (!window.confirm('End this class session?')) return
    
    try {
      await sessionsApi.end(sessionId)
      setSessionEnded(true)
      navigate(`/summary/${sessionId}`)
    } catch (error) {
      console.error('Failed to end session:', error)
      alert('Failed to end session. Make sure the backend is running.')
    }
  }
  
  const handleViewSummary = () => {
    navigate(`/summary/${sessionId}`)
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
      <div className="min-h-screen bg-[#EFF0C6] grid-texture flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#000000] mx-auto mb-4"></div>
          <p className="text-[#000000] font-medium">Loading session...</p>
        </div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="min-h-screen bg-[#EFF0C6] grid-texture flex items-center justify-center">
        <div className="bg-[#DDD6FE] border-2 border-[#000000] rounded-lg p-8 text-center">
          <h2 className="text-2xl font-bold text-[#000000] mb-4">{error}</h2>
          <button 
            className="px-6 py-3 bg-[#EFF0C6] border-2 border-[#000000] rounded-lg text-[#000000] font-medium hover:bg-[#E8E9B0] transition-colors"
            onClick={() => navigate('/personalized-support')}
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#EFF0C6] grid-texture">
      <div className="container mx-auto px-4 md:px-8 py-6 md:py-10">
        {/* Session Header */}
        <div className="bg-[#fff3f3] border-2 border-[#000000] rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex-1">
              <h1 
                className="text-3xl md:text-4xl font-bold text-[#000000] mb-4"
                style={{
                  fontFamily: "TT Firs Neue, sans-serif",
                  fontWeight: 700,
                }}
              >
                {session?.topic}
              </h1>
              <div className="flex items-center gap-6 flex-wrap">
                <div className="flex flex-col">
                  <span className="text-2xl font-bold text-[#000000]">{questionsAsked}</span>
                  <span className="text-sm text-[#000000] opacity-70">Questions Asked</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${session?.is_active ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
                  <span className="text-sm font-medium text-[#000000]">
                    {session?.is_active ? 'Live' : 'Ended'}
                  </span>
                </div>
              </div>
            </div>
            
            <button 
              className="px-6 py-3 bg-white border-2 border-[#000000] rounded-lg text-[#000000] font-medium hover:bg-gray-50 transition-colors flex items-center gap-2"
              onClick={sessionEnded ? handleViewSummary : handleEndSession}
            >
              {sessionEnded ? (
                <>
                  View Summary
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="9 18 15 12 9 6"/>
                  </svg>
                </>
              ) : (
                <>
                  End Session
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                  </svg>
                </>
              )}
            </button>
          </div>
        </div>
        
        {/* Main Content */}
        <div className="max-w-3xl mx-auto">
          {sessionEnded ? (
            <div className="bg-[#DDD6FE] border-2 border-[#000000] rounded-lg p-12 text-center">
              <svg className="w-16 h-16 text-[#000000] mx-auto mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              <h2 className="text-3xl font-bold text-[#000000] mb-4">Session Complete!</h2>
              <p className="text-lg text-[#000000] opacity-80 mb-6">You asked {questionsAsked} questions in this session.</p>
              <button 
                className="px-8 py-4 bg-[#EFF0C6] border-2 border-[#000000] rounded-lg text-lg font-bold text-[#000000] hover:bg-[#E8E9B0] transition-colors flex items-center gap-3 mx-auto shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1"
                onClick={handleViewSummary}
              >
                View Class Summary
                <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="9 18 15 12 9 6"/>
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
              <div className="mt-6 flex items-center justify-center gap-6 flex-wrap text-sm text-[#000000] opacity-70">
                <span className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-white border-2 border-[#000000] rounded text-xs font-mono">Enter</kbd>
                  Ask
                </span>
                <span className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-white border-2 border-[#000000] rounded text-xs font-mono">S</kbd>
                  Skip
                </span>
                <span className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-white border-2 border-[#000000] rounded text-xs font-mono">Esc</kbd>
                  End Session
                </span>
              </div>
            </>
          )}
        </div>
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
