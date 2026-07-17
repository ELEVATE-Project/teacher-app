import { Link } from 'react-router-dom'
import StarRating from './StarRating'

function StudentCard({ student, onUpdate, onDelete, showActions = true }) {
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

  return (
    <div className="dash-student-card">
      <div className="dash-student-avatar" style={{ backgroundColor: getAvatarColor(student.name) }}>
        {getInitials(student.name)}
      </div>
      
      <div className="dash-student-info">
        <Link to={`/dashboard/student/${student.id}`} className="dash-student-name">
          {student.name}
        </Link>
        
        <div className="dash-student-meta">
          <span className={`dash-badge ${getLevelBadgeClass(student.level)}`}>
            {student.level}
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--dash-text-muted)' }}>
            Confidence: {student.confidence.toFixed(1)}
          </span>
        </div>
        
        <div>
          <StarRating 
            value={Math.round(student.confidence)} 
            readonly 
            size="small" 
          />
        </div>
      </div>
      
      {showActions && (
        <div className="dash-student-actions">
          {onUpdate && (
            <button 
              className="dash-btn-icon dash-btn-secondary" 
              onClick={() => onUpdate(student)}
              title="Edit student"
              style={{ width: '36px', height: '36px', padding: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '2px solid #000', background: '#fff', cursor: 'pointer' }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
          )}
          {onDelete && (
            <button 
              className="dash-btn-icon dash-btn-secondary" 
              onClick={() => onDelete(student.id)}
              title="Delete student"
              style={{ width: '36px', height: '36px', padding: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '2px solid #000', background: '#fff', cursor: 'pointer' }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default StudentCard

