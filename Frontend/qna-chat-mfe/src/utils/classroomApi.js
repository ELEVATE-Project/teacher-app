import apiClient from './apiClient'

// Use feedback_system backend URL - adjust if different
const FEEDBACK_BACKEND_URL = import.meta.env.VITE_FEEDBACK_BACKEND_URL || 'http://localhost:3000'

// Create a separate axios instance for feedback_system backend
import axios from 'axios'
const feedbackApiClient = axios.create({
  baseURL: FEEDBACK_BACKEND_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

const API_BASE = '/api'

// Classes API
export const classesApi = {
  getAll: async () => {
    const response = await feedbackApiClient.get(`${API_BASE}/classes/`)
    // Backend returns { classes: [...] }
    return response.data
  },
  
  get: async (id) => {
    const response = await feedbackApiClient.get(`${API_BASE}/classes/${id}`)
    return response.data
  },
  
  create: async (data) => {
    const response = await feedbackApiClient.post(`${API_BASE}/classes/`, data)
    // Backend returns ClassResponse directly
    return response.data
  },
  
  update: async (id, data) => {
    const response = await feedbackApiClient.put(`${API_BASE}/classes/${id}`, data)
    return response.data
  },
  
  delete: async (id) => {
    const response = await feedbackApiClient.delete(`${API_BASE}/classes/${id}`)
    return response.data
  }
}

// Students API
export const studentsApi = {
  getByClass: async (classId) => {
    const response = await feedbackApiClient.get(`${API_BASE}/students/class/${classId}`)
    // Backend returns List[StudentResponse] directly
    return response.data
  },
  
  get: async (id) => {
    const response = await feedbackApiClient.get(`${API_BASE}/students/${id}`)
    return response.data
  },
  
  getProfile: async (id) => {
    const response = await feedbackApiClient.get(`${API_BASE}/students/${id}/profile`)
    return response.data
  },
  
  create: async (classId, data) => {
    const response = await feedbackApiClient.post(`${API_BASE}/students/class/${classId}`, data)
    return response.data
  },
  
  createBulk: async (classId, students) => {
    const response = await feedbackApiClient.post(`${API_BASE}/students/class/${classId}/bulk`, { students })
    return response.data
  },
  
  update: async (id, data) => {
    const response = await feedbackApiClient.put(`${API_BASE}/students/${id}`, data)
    return response.data
  },
  
  delete: async (id) => {
    const response = await feedbackApiClient.delete(`${API_BASE}/students/${id}`)
    return response.data
  }
}

// Questions API
export const questionsApi = {
  getByTopic: async (topic) => {
    const response = await feedbackApiClient.get(`${API_BASE}/questions/topic/${encodeURIComponent(topic)}`)
    return response.data
  },
  
  getTopics: async () => {
    const response = await feedbackApiClient.get(`${API_BASE}/questions/topics`)
    return response.data
  },
  
  generate: async (data) => {
    const response = await feedbackApiClient.post(`${API_BASE}/questions/generate`, data)
    return response.data
  },
  
  create: async (data) => {
    const response = await feedbackApiClient.post(`${API_BASE}/questions`, data)
    return response.data
  },
  
  createBulk: async (questions) => {
    const response = await feedbackApiClient.post(`${API_BASE}/questions/bulk`, { questions })
    return response.data
  },
  
  update: async (id, data) => {
    const response = await feedbackApiClient.put(`${API_BASE}/questions/${id}`, data)
    return response.data
  },
  
  delete: async (id) => {
    const response = await feedbackApiClient.delete(`${API_BASE}/questions/${id}`)
    return response.data
  }
}

// Sessions API
export const sessionsApi = {
  get: async (id) => {
    const response = await feedbackApiClient.get(`${API_BASE}/sessions/${id}`)
    return response.data
  },
  
  getActive: async (classId) => {
    const response = await feedbackApiClient.get(`${API_BASE}/sessions/active/${classId}`)
    return response.data
  },
  
  start: async (data) => {
    const response = await feedbackApiClient.post(`${API_BASE}/sessions/start`, data)
    return response.data
  },
  
  getNext: async (sessionId) => {
    const response = await feedbackApiClient.get(`${API_BASE}/sessions/${sessionId}/next`)
    return response.data
  },
  
  respond: async (sessionId, data) => {
    const response = await feedbackApiClient.post(`${API_BASE}/sessions/${sessionId}/respond`, data)
    return response.data
  },
  
  skip: async (sessionId, studentId) => {
    const response = await feedbackApiClient.post(`${API_BASE}/sessions/${sessionId}/skip`, null, {
      params: { student_id: studentId }
    })
    return response.data
  },
  
  end: async (sessionId) => {
    const response = await feedbackApiClient.post(`${API_BASE}/sessions/${sessionId}/end`)
    return response.data
  }
}

// Analytics API
export const analyticsApi = {
  getSessionSummary: async (sessionId) => {
    const response = await feedbackApiClient.get(`${API_BASE}/analytics/session/${sessionId}/summary`)
    return response.data
  },
  
  getClassDashboard: async (classId) => {
    const response = await feedbackApiClient.get(`${API_BASE}/analytics/class/${classId}/dashboard`)
    return response.data
  },
  
  getClassHistory: async (classId, limit = 10) => {
    const response = await feedbackApiClient.get(`${API_BASE}/analytics/class/${classId}/history`, {
      params: { limit }
    })
    return response.data
  },
  
  getStudentProgress: async (studentId) => {
    const response = await feedbackApiClient.get(`${API_BASE}/analytics/student/${studentId}/progress`)
    return response.data
  }
}

export default { classesApi, studentsApi, questionsApi, sessionsApi, analyticsApi }
