import StarRating from './StarRating'

function StudentCard({ student, onUpdate, onDelete, showActions = true }) {
  const getLevelBadgeClass = (level) => {
    switch (level) {
      case 'weak': return 'bg-red-100 text-red-800 border-red-300'
      case 'strong': return 'bg-green-100 text-green-800 border-green-300'
      default: return 'bg-yellow-100 text-yellow-800 border-yellow-300'
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
    <div className="bg-white border-2 border-[#000000] rounded-lg p-4 flex items-center gap-4 hover:shadow-md transition-shadow">
      <div 
        className="w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0"
        style={{ backgroundColor: getAvatarColor(student.name) }}
      >
        {getInitials(student.name)}
      </div>
      
      <div className="flex-1 min-w-0">
        <h3 className="font-bold text-[#000000] text-lg mb-1 truncate">
          {student.name}
        </h3>
        
        <div className="flex items-center gap-3 mb-2 flex-wrap">
          <span className={`px-2 py-1 rounded text-xs font-medium border ${getLevelBadgeClass(student.level)}`}>
            {student.level}
          </span>
          <span className="text-sm text-[#000000] opacity-70">
            Confidence: {student.confidence.toFixed(1)}
          </span>
        </div>
        
        <div className="flex items-center">
          <StarRating 
            value={Math.round(student.confidence)} 
            readonly 
            size="small" 
          />
        </div>
      </div>
      
      {showActions && (
        <div className="flex items-center gap-2 flex-shrink-0">
          {onUpdate && (
            <button 
              className="p-2 bg-white border-2 border-[#000000] rounded-lg hover:bg-[#EFF0C6] transition-colors"
              onClick={() => onUpdate(student)}
              title="Edit student"
            >
              <svg className="w-5 h-5 text-[#000000]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
          )}
          {onDelete && (
            <button 
              className="p-2 bg-white border-2 border-[#000000] rounded-lg hover:bg-red-50 transition-colors"
              onClick={() => onDelete(student.id)}
              title="Delete student"
            >
              <svg className="w-5 h-5 text-red-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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
