import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { classesApi, studentsApi } from '../../api/dashboardApi'
import StudentCard from '../../components/dashboard/StudentCard'
import StarRating from '../../components/dashboard/StarRating'
import ClassDashboard from '../../components/dashboard/ClassDashboard'

function ColdStartSetup() {
  const navigate = useNavigate()
  const [classes, setClasses] = useState([])
  const [selectedClass, setSelectedClass] = useState(null)
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [showClassForm, setShowClassForm] = useState(false)
  const [showStudentForm, setShowStudentForm] = useState(false)
  const [editingStudent, setEditingStudent] = useState(null)
  const [activeTab, setActiveTab] = useState('dashboard')
  
  // Form states
  const [className, setClassName] = useState('')
  const [classSubject, setClassSubject] = useState('')
  const [studentName, setStudentName] = useState('')
  const [studentLevel, setStudentLevel] = useState('medium')
  const [studentConfidence, setStudentConfidence] = useState(2.5)
  
  useEffect(() => {
    loadClasses()
  }, [])
  
  useEffect(() => {
    if (selectedClass) {
      loadStudents(selectedClass.id)
    }
  }, [selectedClass])
  
  const loadClasses = async () => {
    try {
      const data = await classesApi.getAll()
      setClasses(data.classes || [])
    } catch (error) {
      console.error('Failed to load classes:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const loadStudents = async (classId) => {
    try {
      const data = await studentsApi.getByClass(classId)
      setStudents(data || [])
    } catch (error) {
      console.error('Failed to load students:', error)
    }
  }
  
  const handleCreateClass = async (e) => {
    e.preventDefault()
    if (!className.trim() || !classSubject.trim()) return
    
    try {
      const newClass = await classesApi.create({
        name: className.trim(),
        subject: classSubject.trim()
      })
      setClasses([...classes, newClass])
      setSelectedClass(newClass)
      setClassName('')
      setClassSubject('')
      setShowClassForm(false)
    } catch (error) {
      console.error('Failed to create class:', error)
    }
  }
  
  const handleDeleteClass = async (classId) => {
    if (!confirm('Delete this class and all its students?')) return
    
    try {
      await classesApi.delete(classId)
      setClasses(classes.filter(c => c.id !== classId))
      if (selectedClass?.id === classId) {
        setSelectedClass(null)
        setStudents([])
      }
    } catch (error) {
      console.error('Failed to delete class:', error)
    }
  }
  
  const handleAddStudent = async (e) => {
    e.preventDefault()
    if (!studentName.trim() || !selectedClass) return
    
    try {
      const newStudent = await studentsApi.create(selectedClass.id, {
        name: studentName.trim(),
        level: studentLevel,
        confidence: studentConfidence
      })
      setStudents([...students, newStudent])
      resetStudentForm()
    } catch (error) {
      console.error('Failed to add student:', error)
    }
  }
  
  const handleUpdateStudent = async (e) => {
    e.preventDefault()
    if (!editingStudent) return
    
    try {
      const updated = await studentsApi.update(editingStudent.id, {
        name: studentName.trim(),
        level: studentLevel,
        confidence: studentConfidence
      })
      setStudents(students.map(s => s.id === updated.id ? updated : s))
      resetStudentForm()
    } catch (error) {
      console.error('Failed to update student:', error)
    }
  }
  
  const handleDeleteStudent = async (studentId) => {
    if (!confirm('Delete this student?')) return
    
    try {
      await studentsApi.delete(studentId)
      setStudents(students.filter(s => s.id !== studentId))
    } catch (error) {
      console.error('Failed to delete student:', error)
    }
  }
  
  const startEditStudent = (student) => {
    setEditingStudent(student)
    setStudentName(student.name)
    setStudentLevel(student.level)
    setStudentConfidence(student.confidence)
    setShowStudentForm(true)
  }
  
  const resetStudentForm = () => {
    setStudentName('')
    setStudentLevel('medium')
    setStudentConfidence(2.5)
    setEditingStudent(null)
    setShowStudentForm(false)
  }
  
  const handleStartSession = () => {
    if (selectedClass && students.length > 0) {
      navigate(`/dashboard/questions/${selectedClass.id}`)
    }
  }
  
  if (loading) {
    return (
      <div className="dash-loading-container">
        <div className="dash-spinner"></div>
        <p>Loading...</p>
      </div>
    )
  }

  return (
    <div className="dash-fade-in">
      <div className="dash-page-header">
        <div>
          <h1>Classroom Setup</h1>
          <p>Create your class and add students to get started</p>
        </div>
      </div>
      
      <div className="dash-setup-grid">
        {/* Classes Panel */}
        <div className="dash-panel">
          <div className="dash-panel-header">
            <h2>Your Classes</h2>
            <button 
              className="dash-btn dash-btn-primary"
              onClick={() => setShowClassForm(true)}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Add Class
            </button>
          </div>
          
          {showClassForm && (
            <form className="dash-card dash-fade-in" style={{ margin: 'var(--dash-space-md)' }} onSubmit={handleCreateClass}>
              <h3 style={{ marginBottom: 'var(--dash-space-md)', fontSize: '1.125rem' }}>New Class</h3>
              <div className="dash-form-group">
                <label>Class Name</label>
                <input
                  className="dash-input"
                  type="text"
                  value={className}
                  onChange={(e) => setClassName(e.target.value)}
                  placeholder="e.g., Class 8-A"
                  autoFocus
                />
              </div>
              <div className="dash-form-group">
                <label>Subject</label>
                <input
                  className="dash-input"
                  type="text"
                  value={classSubject}
                  onChange={(e) => setClassSubject(e.target.value)}
                  placeholder="e.g., Science"
                />
              </div>
              <div className="dash-form-actions">
                <button type="button" className="dash-btn dash-btn-secondary" onClick={() => setShowClassForm(false)}>
                  Cancel
                </button>
                <button type="submit" className="dash-btn dash-btn-primary">
                  Create Class
                </button>
              </div>
            </form>
          )}
          
          <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--dash-space-md)' }}>
            {classes.length === 0 ? (
              <div className="dash-empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
                <p>No classes yet</p>
                <span>Create your first class to begin</span>
              </div>
            ) : (
              classes.map((cls) => (
                <div 
                  key={cls.id}
                  className={`dash-class-item ${selectedClass?.id === cls.id ? 'selected' : ''}`}
                  onClick={() => setSelectedClass(cls)}
                >
                  <div className="dash-class-info">
                    <h3>{cls.name}</h3>
                    <span>{cls.subject}</span>
                    <span className="dash-student-count">{cls.student_count} students</span>
                  </div>
                  <button 
                    className="dash-btn-icon"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteClass(cls.id)
                    }}
                    style={{ width: '32px', height: '32px', padding: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '2px solid #000', background: 'transparent', cursor: 'pointer' }}
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                      <polyline points="3 6 5 6 21 6"/>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
        
        {/* Students Panel */}
        <div className="dash-panel">
          {selectedClass ? (
            <>
              <div className="dash-panel-header">
                <div>
                  <h2>{selectedClass.name}</h2>
                  <span className="dash-badge" style={{ marginTop: 'var(--dash-space-xs)' }}>{selectedClass.subject}</span>
                </div>
                <div style={{ display: 'flex', gap: 'var(--dash-space-sm)' }}>
                  {students.length > 0 && (
                    <button 
                      className="dash-btn dash-btn-accent"
                      onClick={handleStartSession}
                    >
                      Start Class
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                      </svg>
                    </button>
                  )}
                </div>
              </div>
              
              {/* Tabs */}
              <div className="dash-tabs">
                <button 
                  className={`dash-tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
                  onClick={() => setActiveTab('dashboard')}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 3v18h18"/>
                    <path d="M18 17V9"/>
                    <path d="M13 17V5"/>
                    <path d="M8 17v-3"/>
                  </svg>
                  Dashboard
                </button>
                <button 
                  className={`dash-tab-btn ${activeTab === 'students' ? 'active' : ''}`}
                  onClick={() => setActiveTab('students')}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                  </svg>
                  Students ({students.length})
                </button>
              </div>
              
              {/* Dashboard Tab */}
              {activeTab === 'dashboard' && (
                <div className="dash-tab-content">
                  <ClassDashboard classId={selectedClass.id} />
                </div>
              )}
              
              {/* Students Tab */}
              {activeTab === 'students' && (
                <div className="dash-tab-content">
                  <div style={{ padding: 'var(--dash-space-md)', display: 'flex', justifyContent: 'flex-end' }}>
                    <button 
                      className="dash-btn dash-btn-secondary"
                      onClick={() => setShowStudentForm(true)}
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                        <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                        <circle cx="8.5" cy="7" r="4"/>
                        <line x1="20" y1="8" x2="20" y2="14"/>
                        <line x1="23" y1="11" x2="17" y2="11"/>
                      </svg>
                      Add Student
                    </button>
                  </div>
                  
                  {showStudentForm && (
                    <form 
                      className="dash-card dash-fade-in" 
                      style={{ margin: 'var(--dash-space-md)' }}
                      onSubmit={editingStudent ? handleUpdateStudent : handleAddStudent}
                    >
                      <h3 style={{ marginBottom: 'var(--dash-space-md)', fontSize: '1.125rem' }}>{editingStudent ? 'Edit Student' : 'Add New Student'}</h3>
                      
                      <div className="dash-form-group">
                        <label>Student Name</label>
                        <input
                          className="dash-input"
                          type="text"
                          value={studentName}
                          onChange={(e) => setStudentName(e.target.value)}
                          placeholder="Enter student name"
                          autoFocus
                        />
                      </div>
                      
                      <div className="dash-form-group">
                        <label>Initial Level</label>
                        <div className="dash-level-buttons">
                          {['weak', 'medium', 'strong'].map((level) => (
                            <button
                              key={level}
                              type="button"
                              className={`dash-level-btn ${studentLevel === level ? 'active' : ''} ${level}`}
                              onClick={() => setStudentLevel(level)}
                            >
                              {level.charAt(0).toUpperCase() + level.slice(1)}
                            </button>
                          ))}
                        </div>
                      </div>
                      
                      <div className="dash-form-group">
                        <label>Initial Confidence</label>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--dash-space-md)' }}>
                          <StarRating 
                            value={Math.round(studentConfidence)}
                            onChange={setStudentConfidence}
                            size="medium"
                          />
                          <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--dash-accent)', minWidth: '40px' }}>{studentConfidence.toFixed(1)}</span>
                        </div>
                      </div>
                      
                      <div className="dash-form-actions">
                        <button type="button" className="dash-btn dash-btn-secondary" onClick={resetStudentForm}>
                          Cancel
                        </button>
                        <button type="submit" className="dash-btn dash-btn-primary">
                          {editingStudent ? 'Update' : 'Add Student'}
                        </button>
                      </div>
                    </form>
                  )}
                  
                  <div style={{ flex: 1, overflowY: 'auto', padding: '0 var(--dash-space-md) var(--dash-space-md)', display: 'flex', flexDirection: 'column', gap: 'var(--dash-space-sm)' }}>
                    {students.length === 0 ? (
                      <div className="dash-empty-state">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                          <circle cx="12" cy="7" r="4"/>
                        </svg>
                        <p>No students yet</p>
                        <span>Add students to this class</span>
                      </div>
                    ) : (
                      students.map((student) => (
                        <StudentCard
                          key={student.id}
                          student={student}
                          onUpdate={startEditStudent}
                          onDelete={handleDeleteStudent}
                        />
                      ))
                    )}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="dash-select-prompt">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M15 18l-6-6 6-6"/>
              </svg>
              <p>Select a class to view students</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ColdStartSetup

