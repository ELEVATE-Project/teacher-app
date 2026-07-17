/**
 * Dashboard API - Unified Server on Port 3000
 * All endpoints now use /api/dashboard prefix which proxies to /api
 */
const API_BASE = '/api/dashboard'

async function handleResponse(response) {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP error ${response.status}`)
  }
  return response.json()
}

// Classes API
export const classesApi = {
  getAll: () =>
    fetch(`${API_BASE}/classes`).then(handleResponse),

  get: (id) =>
    fetch(`${API_BASE}/classes/${id}`).then(handleResponse),

  create: (data) =>
    fetch(`${API_BASE}/classes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse),

  update: (id, data) =>
    fetch(`${API_BASE}/classes/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse),

  delete: (id) =>
    fetch(`${API_BASE}/classes/${id}`, { method: 'DELETE' }).then(handleResponse)
}

// Students API
export const studentsApi = {
  getByClass: (classId) =>
    fetch(`${API_BASE}/students/class/${classId}`).then(handleResponse),

  get: (id) =>
    fetch(`${API_BASE}/students/${id}`).then(handleResponse),

  getProfile: (id) =>
    fetch(`${API_BASE}/students/${id}/profile`).then(handleResponse),

  create: (classId, data) =>
    fetch(`${API_BASE}/students/class/${classId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse),

  createBulk: (classId, students) =>
    fetch(`${API_BASE}/students/class/${classId}/bulk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ students })
    }).then(handleResponse),

  update: (id, data) =>
    fetch(`${API_BASE}/students/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse),

  delete: (id) =>
    fetch(`${API_BASE}/students/${id}`, { method: 'DELETE' }).then(handleResponse)
}

// Questions API
export const questionsApi = {
  getByTopic: (topic) =>
    fetch(`${API_BASE}/questions/topic/${encodeURIComponent(topic)}`).then(handleResponse),

  getAll: (skip = 0, limit = 100) =>
    fetch(`${API_BASE}/questions?skip=${skip}&limit=${limit}`).then(handleResponse),

  generate: (data) =>
    fetch(`${API_BASE}/questions/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse),

  create: (data) =>
    fetch(`${API_BASE}/questions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse),

  createBulk: (questions) =>
    fetch(`${API_BASE}/questions/bulk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ questions })
    }).then(handleResponse),

  delete: (id) =>
    fetch(`${API_BASE}/questions/${id}`, { method: 'DELETE' }).then(handleResponse),

  update: (id, data) =>
    fetch(`${API_BASE}/questions/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse),

  deleteByTopic: (topic) =>
    fetch(`${API_BASE}/questions/topic/${encodeURIComponent(topic)}`, { method: 'DELETE' }).then(handleResponse)
}

// Sessions API - Updated for new backend structure
export const sessionsApi = {
  get: (id) =>
    fetch(`${API_BASE}/sessions/${id}`).then(handleResponse),

  getActive: (classId) =>
    fetch(`${API_BASE}/sessions/active/${classId}`).then(handleResponse),

  // Changed from /sessions/start to POST /sessions
  start: (data) =>
    fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse),

  // Changed from /sessions/{id}/next to /sessions/{id}/suggest
  getNext: (sessionId) =>
    fetch(`${API_BASE}/sessions/${sessionId}/suggest`).then(handleResponse),

  // Changed from /sessions/{id}/respond to /sessions/{id}/response
  respond: (sessionId, data) =>
    fetch(`${API_BASE}/sessions/${sessionId}/response`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse),

  // Skip now uses response endpoint with skipped: true
  skip: (sessionId, studentId, difficultyAsked = 'medium') =>
    fetch(`${API_BASE}/sessions/${sessionId}/response`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: studentId,
        rating: 1,
        difficulty_asked: difficultyAsked,
        skipped: true
      })
    }).then(handleResponse),

  end: (sessionId) =>
    fetch(`${API_BASE}/sessions/${sessionId}/end`, {
      method: 'POST'
    }).then(handleResponse),

  // Get session history for a class
  getHistory: (classId, limit = 20) =>
    fetch(`${API_BASE}/sessions/class/${classId}/history?limit=${limit}`).then(handleResponse),

  // Get session summary
  getSummary: (sessionId) =>
    fetch(`${API_BASE}/sessions/${sessionId}/summary`).then(handleResponse)
}

// Analytics API - Updated for new backend structure
export const analyticsApi = {
  // Changed from /analytics/session/{id}/summary to /sessions/{id}/summary
  getSessionSummary: (sessionId) =>
    fetch(`${API_BASE}/sessions/${sessionId}/summary`).then(handleResponse),

  // Changed to /analytics/class/{id}/overview
  getClassDashboard: (classId) =>
    fetch(`${API_BASE}/analytics/class/${classId}/overview`).then(handleResponse),

  // Get class session history via sessions endpoint
  getClassHistory: (classId, limit = 10) =>
    fetch(`${API_BASE}/sessions/class/${classId}/history?limit=${limit}`).then(handleResponse),

  // Changed to /students/{id}/profile for student progress
  getStudentProgress: (studentId) =>
    fetch(`${API_BASE}/students/${studentId}/profile`).then(handleResponse),

  // Additional analytics endpoints
  getStudentsPerformance: (classId) =>
    fetch(`${API_BASE}/analytics/class/${classId}/students/performance`).then(handleResponse),

  getTopicAnalytics: (classId) =>
    fetch(`${API_BASE}/analytics/class/${classId}/topics`).then(handleResponse),

  getAttentionNeeded: (classId) =>
    fetch(`${API_BASE}/analytics/class/${classId}/attention-needed`).then(handleResponse),

  getEngagement: (classId, days = 30) =>
    fetch(`${API_BASE}/analytics/class/${classId}/engagement?days=${days}`).then(handleResponse)
}

// Reflection API - New
export const reflectionApi = {
  create: (data) =>
    fetch(`${API_BASE}/reflection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(handleResponse),

  get: (id) =>
    fetch(`${API_BASE}/reflection/${id}`).then(handleResponse),

  getHistory: (skip = 0, limit = 20) =>
    fetch(`${API_BASE}/reflection/history?skip=${skip}&limit=${limit}`).then(handleResponse),

  getBySubject: (subject, skip = 0, limit = 20) =>
    fetch(`${API_BASE}/reflection/subject/${encodeURIComponent(subject)}?skip=${skip}&limit=${limit}`).then(handleResponse),

  delete: (id) =>
    fetch(`${API_BASE}/reflection/${id}`, { method: 'DELETE' }).then(handleResponse),

  reanalyze: (id) =>
    fetch(`${API_BASE}/reflection/${id}/reanalyze`, { method: 'POST' }).then(handleResponse)
}


