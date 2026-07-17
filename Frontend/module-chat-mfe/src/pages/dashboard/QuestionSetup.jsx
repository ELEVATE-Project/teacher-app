import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { classesApi, questionsApi, sessionsApi } from '../../api/dashboardApi'

function QuestionSetup() {
  const { classId } = useParams()
  const navigate = useNavigate()

  const [classInfo, setClassInfo] = useState(null)
  const [topic, setTopic] = useState('')
  const [questions, setQuestions] = useState({ easy: [], medium: [], hard: [] })
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingQuestion, setEditingQuestion] = useState(null)

  const [questionCounts, setQuestionCounts] = useState({ easy: 3, medium: 3, hard: 3 })

  const [newQuestionText, setNewQuestionText] = useState('')
  const [newQuestionDifficulty, setNewQuestionDifficulty] = useState('medium')

  useEffect(() => {
    loadClassInfo()
  }, [classId])

  const loadClassInfo = async () => {
    try {
      const data = await classesApi.get(classId)
      setClassInfo(data)
    } catch (error) {
      console.error('Failed to load class:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadQuestionsForTopic = async (topicName) => {
    try {
      const data = await questionsApi.getByTopic(topicName)
      setQuestions(data)
    } catch (error) {
      console.error('Failed to load questions:', error)
      setQuestions({ easy: [], medium: [], hard: [] })
    }
  }

  const updateQuestionCount = (difficulty, delta) => {
    setQuestionCounts(prev => ({
      ...prev,
      [difficulty]: Math.max(0, Math.min(10, prev[difficulty] + delta))
    }))
  }

  const handleGenerateQuestions = async () => {
    if (!topic.trim() || !classInfo) return

    setGenerating(true)
    try {
      const data = await questionsApi.generate({
        topic: topic.trim(),
        subject: classInfo.subject,
        easy_count: questionCounts.easy,
        medium_count: questionCounts.medium,
        hard_count: questionCounts.hard
      })
      setQuestions(data)
    } catch (error) {
      console.error('Failed to generate questions:', error)
      await loadQuestionsForTopic(topic.trim())
    } finally {
      setGenerating(false)
    }
  }

  const handleAddQuestion = async (e) => {
    e.preventDefault()
    if (!newQuestionText.trim() || !topic.trim()) return

    try {
      const newQuestion = await questionsApi.create({
        topic: topic.trim(),
        difficulty: newQuestionDifficulty,
        text: newQuestionText.trim()
      })

      setQuestions(prev => ({
        ...prev,
        [newQuestionDifficulty]: [...prev[newQuestionDifficulty], newQuestion]
      }))

      setNewQuestionText('')
      setShowAddForm(false)
    } catch (error) {
      console.error('Failed to add question:', error)
    }
  }

  const handleUpdateQuestion = async (e) => {
    e.preventDefault()
    if (!editingQuestion || !newQuestionText.trim()) return

    try {
      const updated = await questionsApi.update(editingQuestion.id, {
        topic: topic.trim(),
        difficulty: newQuestionDifficulty,
        text: newQuestionText.trim()
      })

      setQuestions(prev => {
        const newQuestions = { ...prev }
        Object.keys(newQuestions).forEach(diff => {
          newQuestions[diff] = newQuestions[diff].filter(q => q.id !== editingQuestion.id)
        })
        newQuestions[updated.difficulty] = [...newQuestions[updated.difficulty], updated]
        return newQuestions
      })

      resetForm()
    } catch (error) {
      console.error('Failed to update question:', error)
    }
  }

  const handleDeleteQuestion = async (questionId, difficulty) => {
    try {
      await questionsApi.delete(questionId)
      setQuestions(prev => ({
        ...prev,
        [difficulty]: prev[difficulty].filter(q => q.id !== questionId)
      }))
    } catch (error) {
      console.error('Failed to delete question:', error)
    }
  }

  const startEditQuestion = (question) => {
    setEditingQuestion(question)
    setNewQuestionText(question.text)
    setNewQuestionDifficulty(question.difficulty)
    setShowAddForm(true)
  }

  const resetForm = () => {
    setNewQuestionText('')
    setNewQuestionDifficulty('medium')
    setEditingQuestion(null)
    setShowAddForm(false)
  }

  const handleStartClass = async () => {
    if (!topic.trim()) return

    const totalQuestions = questions.easy.length + questions.medium.length + questions.hard.length
    if (totalQuestions === 0) {
      alert('Please add at least one question before starting the class')
      return
    }

    try {
      // Use classId directly as MongoDB uses string ObjectIds
      const session = await sessionsApi.start({
        class_id: classId,
        topic: topic.trim()
      })
      navigate(`/dashboard/session/${session.id}`)
    } catch (error) {
      console.error('Failed to start session:', error)
    }
  }

  const getTotalQuestions = () => {
    return questions.easy.length + questions.medium.length + questions.hard.length
  }

  if (loading) {
    return (
      <div className="dash-loading-container">
        <div className="dash-spinner"></div>
        <p>Loading class...</p>
      </div>
    )
  }

  if (!classInfo) {
    return (
      <div className="dash-error-container">
        <h2>Class not found</h2>
        <button className="dash-btn dash-btn-primary" onClick={() => navigate('/dashboard')}>
          Go Back
        </button>
      </div>
    )
  }

  return (
    <div className="dash-fade-in">
      <div className="dash-page-header">
        <button className="dash-btn dash-btn-secondary" onClick={() => navigate('/dashboard')}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
            <path d="M19 12H5" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          Back
        </button>
        <div>
          <h1>Question Setup</h1>
          <p>{classInfo.name} • {classInfo.subject}</p>
        </div>
      </div>

      {/* Topic Input */}
      <div className="dash-card" style={{ marginBottom: 'var(--dash-space-xl)' }}>
        <h2 style={{ marginBottom: 'var(--dash-space-md)', fontSize: '1.25rem' }}>Today's Topic</h2>
        <div style={{ display: 'flex', gap: 'var(--dash-space-md)' }}>
          <input
            className="dash-input"
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g., Rotational Motion, Photosynthesis, Fractions..."
            style={{ flex: 1, fontSize: '1.125rem', padding: 'var(--dash-space-md)' }}
          />
          <button
            className="dash-btn dash-btn-primary dash-btn-lg"
            onClick={handleGenerateQuestions}
            disabled={!topic.trim() || generating}
          >
            {generating ? (
              <>
                <span className="dash-spinner" style={{ width: '18px', height: '18px', borderWidth: '2px' }}></span>
                Generating...
              </>
            ) : (
              <>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
                  <path d="M12 2L2 7l10 5 10-5-10-5z" />
                  <path d="M2 17l10 5 10-5" />
                  <path d="M2 12l10 5 10-5" />
                </svg>
                Generate Questions
              </>
            )}
          </button>
        </div>

        {/* Question Count Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--dash-space-lg)', marginTop: 'var(--dash-space-lg)', paddingTop: 'var(--dash-space-lg)', borderTop: '2px solid #000', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--dash-text-secondary)' }}>Questions to generate:</span>
          <div style={{ display: 'flex', gap: 'var(--dash-space-md)', flex: 1 }}>
            {['easy', 'medium', 'hard'].map((diff) => (
              <div key={diff} style={{ display: 'flex', alignItems: 'center', gap: 'var(--dash-space-sm)', padding: 'var(--dash-space-xs) var(--dash-space-sm)', border: `2px solid ${diff === 'easy' ? 'var(--dash-easy)' : diff === 'medium' ? 'var(--dash-medium)' : 'var(--dash-hard)'}`, background: 'var(--dash-surface-elevated)' }}>
                <span className={`dash-badge dash-badge-${diff}`}>{diff}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--dash-space-xs)' }}>
                  <button
                    type="button"
                    style={{ width: '28px', height: '28px', border: '2px solid #000', background: '#fff', fontSize: '1.25rem', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 0 }}
                    onClick={() => updateQuestionCount(diff, -1)}
                    disabled={questionCounts[diff] <= 0}
                  >
                    −
                  </button>
                  <span style={{ fontSize: '1.125rem', fontWeight: 700, minWidth: '24px', textAlign: 'center' }}>{questionCounts[diff]}</span>
                  <button
                    type="button"
                    style={{ width: '28px', height: '28px', border: '2px solid #000', background: '#fff', fontSize: '1.25rem', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 0 }}
                    onClick={() => updateQuestionCount(diff, 1)}
                    disabled={questionCounts[diff] >= 10}
                  >
                    +
                  </button>
                </div>
              </div>
            ))}
          </div>
          <span style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--dash-primary)', background: 'var(--dash-accent)', padding: 'var(--dash-space-xs) var(--dash-space-md)', border: '2px solid #000' }}>
            Total: {questionCounts.easy + questionCounts.medium + questionCounts.hard}
          </span>
        </div>
      </div>

      {/* Questions Lists */}
      {topic && (
        <div className="dash-fade-in" style={{ marginTop: 'var(--dash-space-xl)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--dash-space-lg)' }}>
            <h2 style={{ fontSize: '1.5rem' }}>Questions for: {topic}</h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--dash-space-md)' }}>
              <span style={{ fontSize: '0.875rem', color: 'var(--dash-text-muted)', background: 'var(--dash-surface-elevated)', padding: 'var(--dash-space-xs) var(--dash-space-md)', border: '2px solid #000' }}>
                {getTotalQuestions()} questions
              </span>
              <button className="dash-btn dash-btn-secondary" onClick={() => setShowAddForm(true)}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                Add Question
              </button>
            </div>
          </div>

          {showAddForm && (
            <form
              className="dash-card dash-fade-in"
              style={{ marginBottom: 'var(--dash-space-xl)' }}
              onSubmit={editingQuestion ? handleUpdateQuestion : handleAddQuestion}
            >
              <h3 style={{ marginBottom: 'var(--dash-space-md)', fontSize: '1.125rem' }}>{editingQuestion ? 'Edit Question' : 'Add New Question'}</h3>

              <div className="dash-form-group">
                <label>Question Text</label>
                <textarea
                  className="dash-textarea"
                  value={newQuestionText}
                  onChange={(e) => setNewQuestionText(e.target.value)}
                  placeholder="Enter your question..."
                  rows={3}
                  autoFocus
                />
              </div>

              <div className="dash-form-group">
                <label>Difficulty</label>
                <div className="dash-level-buttons">
                  {['easy', 'medium', 'hard'].map((diff) => (
                    <button
                      key={diff}
                      type="button"
                      className={`dash-level-btn ${newQuestionDifficulty === diff ? 'active' : ''} ${diff}`}
                      onClick={() => setNewQuestionDifficulty(diff)}
                    >
                      {diff.charAt(0).toUpperCase() + diff.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              <div className="dash-form-actions">
                <button type="button" className="dash-btn dash-btn-secondary" onClick={resetForm}>
                  Cancel
                </button>
                <button type="submit" className="dash-btn dash-btn-primary">
                  {editingQuestion ? 'Update' : 'Add Question'}
                </button>
              </div>
            </form>
          )}

          <div className="dash-questions-grid">
            {['easy', 'medium', 'hard'].map((difficulty) => (
              <div key={difficulty} className={`dash-questions-column ${difficulty}`}>
                <div className="dash-column-header">
                  <span className={`dash-badge dash-badge-${difficulty}`}>{difficulty}</span>
                  <span style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--dash-text-muted)' }}>{questions[difficulty].length}</span>
                </div>

                <div className="dash-questions-list">
                  {questions[difficulty].length === 0 ? (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '150px', color: 'var(--dash-text-muted)', fontSize: '0.875rem' }}>
                      <p>No {difficulty} questions</p>
                    </div>
                  ) : (
                    questions[difficulty].map((q) => (
                      <div key={q.id} className="dash-question-item">
                        <p>{q.text}</p>
                        <div className="dash-question-actions">
                          <button
                            className="dash-action-btn"
                            onClick={() => startEditQuestion(q)}
                            title="Edit"
                          >
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                            </svg>
                          </button>
                          <button
                            className="dash-action-btn delete"
                            onClick={() => handleDeleteQuestion(q.id, difficulty)}
                            title="Delete"
                          >
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <polyline points="3 6 5 6 21 6" />
                              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Start Class Button */}
          <div style={{ display: 'flex', justifyContent: 'center', padding: 'var(--dash-space-xl) 0' }}>
            <button
              className="dash-btn dash-btn-accent dash-btn-lg"
              onClick={handleStartClass}
              disabled={getTotalQuestions() === 0}
              style={{ minWidth: '280px' }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="24" height="24">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              Start Class Session
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default QuestionSetup

