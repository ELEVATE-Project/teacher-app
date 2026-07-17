function SuggestionCard({ suggestion, onAsk, onSkip, loading = false }) {
  const getDifficultyClass = (difficulty) => {
    switch (difficulty) {
      case 'easy': return 'dash-badge-easy'
      case 'hard': return 'dash-badge-hard'
      default: return 'dash-badge-medium'
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

  if (loading) {
    return (
      <div className="dash-suggestion-card">
        <div className="dash-loading-container" style={{ minHeight: '300px' }}>
          <div className="dash-spinner"></div>
          <p>Finding next student...</p>
        </div>
      </div>
    )
  }

  if (!suggestion) {
    return (
      <div className="dash-suggestion-card">
        <div className="dash-empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M8 15h8"/>
            <circle cx="9" cy="9" r="1" fill="currentColor"/>
            <circle cx="15" cy="9" r="1" fill="currentColor"/>
          </svg>
          <p>All students have been called!</p>
          <span>Great participation in this session.</span>
        </div>
      </div>
    )
  }

  return (
    <div className="dash-suggestion-card dash-scale-in">
      <div className="dash-suggestion-header">
        <span className="dash-suggestion-label">Ask Next</span>
        <span className={`dash-badge dash-badge-lg ${getDifficultyClass(suggestion.difficulty)}`}>
          {suggestion.difficulty}
        </span>
      </div>
      
      <div className="dash-suggestion-student">
        <div 
          className="dash-suggestion-avatar" 
          style={{ backgroundColor: getAvatarColor(suggestion.student_name) }}
        >
          {getInitials(suggestion.student_name)}
        </div>
        <div className="dash-suggestion-name">{suggestion.student_name}</div>
      </div>
      
      {suggestion.question_text && (
        <div className="dash-suggestion-question">
          <div className="dash-question-label">Suggested Question</div>
          <div className="dash-question-text">"{suggestion.question_text}"</div>
        </div>
      )}
      
      <div className="dash-suggestion-reason">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 16v-4"/>
          <path d="M12 8h.01"/>
        </svg>
        <span>{suggestion.reason}</span>
      </div>
      
      <div className="dash-suggestion-actions">
        <button className="dash-btn dash-btn-secondary dash-btn-lg" onClick={onSkip}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
            <path d="M5 4l10 8-10 8V4z"/>
            <line x1="19" y1="5" x2="19" y2="19"/>
          </svg>
          Skip
        </button>
        <button className="dash-btn dash-btn-primary dash-btn-lg" onClick={onAsk}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          Ask Question
        </button>
      </div>
    </div>
  )
}

export default SuggestionCard

