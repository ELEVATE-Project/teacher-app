import { useState } from 'react'

function StarRating({ value = 0, onChange, size = 'medium', readonly = false }) {
  const [hoverValue, setHoverValue] = useState(0)
  
  const handleClick = (rating) => {
    if (!readonly && onChange) {
      onChange(rating)
    }
  }
  
  const handleMouseEnter = (rating) => {
    if (!readonly) {
      setHoverValue(rating)
    }
  }
  
  const handleMouseLeave = () => {
    setHoverValue(0)
  }
  
  const displayValue = hoverValue || value
  
  return (
    <div 
      className={`dash-star-rating ${size} ${readonly ? 'readonly' : ''}`}
      onMouseLeave={handleMouseLeave}
    >
      {[1, 2, 3, 4, 5].map((rating) => (
        <button
          key={rating}
          type="button"
          className={`dash-star-btn ${displayValue >= rating ? 'filled' : ''}`}
          onClick={() => handleClick(rating)}
          onMouseEnter={() => handleMouseEnter(rating)}
          disabled={readonly}
          aria-label={`Rate ${rating} stars`}
        >
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
          </svg>
        </button>
      ))}
    </div>
  )
}

export default StarRating

