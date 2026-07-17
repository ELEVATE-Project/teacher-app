import { useState } from 'react'
import StarRating from './StarRating'

function RatingPopup({ studentName, difficulty, onSubmit, onCancel }) {
  const [rating, setRating] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  
  const handleSubmit = async () => {
    if (rating === 0) return
    
    setSubmitting(true)
    await onSubmit(rating)
    setSubmitting(false)
  }
  
  const getRatingLabel = (rating) => {
    switch (rating) {
      case 5: return 'Excellent! Perfect answer'
      case 4: return 'Good answer'
      case 3: return 'Acceptable'
      case 2: return 'Needs improvement'
      case 1: return 'Struggled/No answer'
      default: return 'Tap stars to rate'
    }
  }
  
  const getDifficultyClass = (difficulty) => {
    switch (difficulty) {
      case 'easy': return 'dash-badge-easy'
      case 'hard': return 'dash-badge-hard'
      default: return 'dash-badge-medium'
    }
  }

  return (
    <div className="dash-rating-overlay" onClick={onCancel}>
      <div className="dash-rating-popup dash-scale-in" onClick={e => e.stopPropagation()}>
        <div className="dash-rating-header">
          <h3>Rate {studentName}'s Answer</h3>
          <span className={`dash-badge ${getDifficultyClass(difficulty)}`}>
            {difficulty} question
          </span>
        </div>
        
        <div className="dash-rating-content">
          <div className="dash-rating-stars">
            <StarRating 
              value={rating} 
              onChange={setRating}
              size="xlarge"
            />
          </div>
          
          <p className={`dash-rating-label ${rating > 0 ? 'active' : ''}`}>
            {getRatingLabel(rating)}
          </p>
        </div>
        
        <div className="dash-rating-actions">
          <button 
            className="dash-btn dash-btn-secondary"
            onClick={onCancel}
            disabled={submitting}
          >
            Cancel
          </button>
          <button 
            className="dash-btn dash-btn-primary"
            onClick={handleSubmit}
            disabled={rating === 0 || submitting}
          >
            {submitting ? (
              <>
                <span className="dash-spinner" style={{ width: '18px', height: '18px', borderWidth: '2px' }}></span>
                Submitting...
              </>
            ) : (
              <>
                Submit Rating
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default RatingPopup

