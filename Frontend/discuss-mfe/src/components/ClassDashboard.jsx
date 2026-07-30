import { useState, useEffect } from 'react'
import { analyticsApi } from '../utils/classroomApi'
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
      <div className="flex flex-col items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#000000] mb-4"></div>
        <p className="text-[#000000] opacity-70">Loading statistics...</p>
      </div>
    )
  }
  
  if (!dashboard || !dashboard.has_data) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <svg className="w-16 h-16 text-[#000000] opacity-30 mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 3v18h18"/>
          <path d="M18 17V9"/>
          <path d="M13 17V5"/>
          <path d="M8 17v-3"/>
        </svg>
        <p className="text-lg font-medium text-[#000000] mb-1">No session data yet</p>
        <span className="text-sm text-[#000000] opacity-70">Start a class session to see statistics</span>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border-2 border-[#000000] rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-[#000000] mb-1">{dashboard.total_students}</div>
          <div className="text-sm text-[#000000] opacity-70">Students</div>
        </div>
        <div className="bg-white border-2 border-[#000000] rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-[#000000] mb-1">{dashboard.avg_confidence.toFixed(1)}</div>
          <div className="text-sm text-[#000000] opacity-70">Avg Confidence</div>
        </div>
        <div className="bg-white border-2 border-[#000000] rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-[#000000] mb-1">{dashboard.total_sessions}</div>
          <div className="text-sm text-[#000000] opacity-70">Sessions</div>
        </div>
        <div className="bg-white border-2 border-[#000000] rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-[#000000] mb-1">{dashboard.all_time_avg_rating.toFixed(1)}</div>
          <div className="text-sm text-[#000000] opacity-70">Avg Rating</div>
        </div>
      </div>
      
      {/* Level Distribution */}
      <div className="bg-white border-2 border-[#000000] rounded-lg p-6">
        <h4 className="text-lg font-bold text-[#000000] mb-4">Student Levels</h4>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <span className="w-16 text-sm font-medium text-[#000000]">Weak</span>
            <div className="flex-1 h-6 bg-gray-200 rounded-full overflow-hidden border border-[#000000]">
              <div 
                className="h-full bg-red-500 rounded-full transition-all"
                style={{ width: `${(dashboard.level_distribution.weak / dashboard.total_students) * 100}%` }}
              />
            </div>
            <span className="w-8 text-sm font-medium text-[#000000] text-right">{dashboard.level_distribution.weak}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="w-16 text-sm font-medium text-[#000000]">Medium</span>
            <div className="flex-1 h-6 bg-gray-200 rounded-full overflow-hidden border border-[#000000]">
              <div 
                className="h-full bg-yellow-500 rounded-full transition-all"
                style={{ width: `${(dashboard.level_distribution.medium / dashboard.total_students) * 100}%` }}
              />
            </div>
            <span className="w-8 text-sm font-medium text-[#000000] text-right">{dashboard.level_distribution.medium}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="w-16 text-sm font-medium text-[#000000]">Strong</span>
            <div className="flex-1 h-6 bg-gray-200 rounded-full overflow-hidden border border-[#000000]">
              <div 
                className="h-full bg-green-500 rounded-full transition-all"
                style={{ width: `${(dashboard.level_distribution.strong / dashboard.total_students) * 100}%` }}
              />
            </div>
            <span className="w-8 text-sm font-medium text-[#000000] text-right">{dashboard.level_distribution.strong}</span>
          </div>
        </div>
      </div>
      
      {/* Improvement Section */}
      {dashboard.improvement && (
        <div className="bg-white border-2 border-[#000000] rounded-lg p-6">
          <h4 className="text-lg font-bold text-[#000000] mb-4">Improvement from Last Session</h4>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className={`p-4 rounded-lg border-2 ${
              dashboard.improvement.participation_improved 
                ? 'bg-green-50 border-green-300' 
                : 'bg-red-50 border-red-300'
            }`}>
              <div className="flex items-center gap-3">
                <div className={`${dashboard.improvement.participation_improved ? 'text-green-600' : 'text-red-600'}`}>
                  {dashboard.improvement.participation_improved ? (
                    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                      <polyline points="17 6 23 6 23 12"/>
                    </svg>
                  ) : (
                    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/>
                      <polyline points="17 18 23 18 23 12"/>
                    </svg>
                  )}
                </div>
                <div>
                  <div className="text-2xl font-bold text-[#000000]">
                    {dashboard.improvement.participation_change > 0 ? '+' : ''}
                    {dashboard.improvement.participation_change}
                  </div>
                  <div className="text-sm text-[#000000] opacity-70">Participation</div>
                </div>
              </div>
            </div>
            
            <div className={`p-4 rounded-lg border-2 ${
              dashboard.improvement.rating_improved 
                ? 'bg-green-50 border-green-300' 
                : 'bg-red-50 border-red-300'
            }`}>
              <div className="flex items-center gap-3">
                <div className={`${dashboard.improvement.rating_improved ? 'text-green-600' : 'text-red-600'}`}>
                  <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  </svg>
                </div>
                <div>
                  <div className="text-2xl font-bold text-[#000000]">
                    {dashboard.improvement.rating_change > 0 ? '+' : ''}
                    {dashboard.improvement.rating_change.toFixed(1)}
                  </div>
                  <div className="text-sm text-[#000000] opacity-70">Avg Rating</div>
                </div>
              </div>
            </div>
          </div>
          <p className="text-sm text-[#000000] opacity-70">
            Compared to: {dashboard.improvement.previous_session.topic} 
            ({new Date(dashboard.improvement.previous_session.date).toLocaleDateString()})
          </p>
        </div>
      )}
      
      {/* Last Session */}
      {dashboard.last_session && (
        <div className="bg-white border-2 border-[#000000] rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-bold text-[#000000]">Last Session</h4>
            <button 
              className="px-4 py-2 bg-[#DDD6FE] border-2 border-[#000000] rounded-lg text-sm font-medium text-[#000000] hover:bg-[#C4B5FD] transition-colors flex items-center gap-2"
              onClick={loadSessionHistory}
              disabled={loadingHistory}
            >
              {loadingHistory ? 'Loading...' : showAllSessions ? 'Hide History' : 'See All Sessions'}
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points={showAllSessions ? "18 15 12 9 6 15" : "6 9 12 15 18 9"} />
              </svg>
            </button>
          </div>
          <div className="bg-[#EFF0C6] border-2 border-[#000000] rounded-lg p-4 mb-4">
            <div className="font-bold text-lg text-[#000000] mb-2">{dashboard.last_session.topic}</div>
            <div className="text-sm text-[#000000] opacity-70 mb-3">
              {new Date(dashboard.last_session.date).toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'short',
                day: 'numeric'
              })}
            </div>
            <div className="flex items-center gap-4 flex-wrap">
              <span className="text-sm text-[#000000]">{dashboard.last_session.total_questions} questions</span>
              <span className="text-sm text-[#000000]">{dashboard.last_session.participation}/{dashboard.total_students} participated</span>
              <StarRating value={Math.round(dashboard.last_session.avg_rating)} readonly size="small" />
            </div>
          </div>
          
          {/* Session History List */}
          {showAllSessions && sessionHistory.length > 0 && (
            <div className="space-y-2">
              <h5 className="font-bold text-[#000000] mb-3">All Sessions</h5>
              {sessionHistory.map((session) => (
                <div key={session.session_id} className="bg-[#EFF0C6] border-2 border-[#000000] rounded-lg p-4 flex items-center justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-[#000000] mb-1">{session.topic}</div>
                    <div className="text-sm text-[#000000] opacity-70">
                      {new Date(session.started_at).toLocaleDateString('en-US', {
                        weekday: 'short',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-white border border-[#000000] rounded text-xs text-[#000000]">
                      {session.questions_asked} Q
                    </span>
                    <span className="px-2 py-1 bg-white border border-[#000000] rounded text-xs text-[#000000] flex items-center gap-1">
                      <StarRating value={Math.round(session.average_rating)} readonly size="small" />
                      {session.average_rating.toFixed(1)}
                    </span>
                    {session.is_active && (
                      <span className="px-2 py-1 bg-green-100 border border-green-300 rounded text-xs text-green-800">
                        Active
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      
      {/* Top Performers & Needs Attention */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {dashboard.top_performers.length > 0 && (
          <div className="bg-white border-2 border-[#000000] rounded-lg p-6">
            <h4 className="text-lg font-bold text-[#000000] mb-4 flex items-center gap-2">
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
              Top Performers
            </h4>
            <div className="space-y-2">
              {dashboard.top_performers.map((s, index) => (
                <div key={s.id} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-[#000000] w-6">#{index + 1}</span>
                    <span className="text-[#000000]">{s.name}</span>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium border ${
                    s.level === 'strong' ? 'bg-green-100 text-green-800 border-green-300' :
                    s.level === 'medium' ? 'bg-yellow-100 text-yellow-800 border-yellow-300' :
                    'bg-red-100 text-red-800 border-red-300'
                  }`}>
                    {s.confidence.toFixed(1)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {dashboard.needs_attention.length > 0 && (
          <div className="bg-white border-2 border-[#000000] rounded-lg p-6">
            <h4 className="text-lg font-bold text-[#000000] mb-4 flex items-center gap-2">
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              Needs Attention
            </h4>
            <div className="space-y-2">
              {dashboard.needs_attention.slice(0, 3).map((s) => (
                <div key={s.id} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                  <span className="text-[#000000]">{s.name}</span>
                  <span className="text-xs text-[#000000] opacity-70">
                    {s.consecutive_wrong >= 2 ? `${s.consecutive_wrong} wrong streak` : `Low: ${s.confidence.toFixed(1)}`}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ClassDashboard
