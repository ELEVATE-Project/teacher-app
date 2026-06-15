/**
 * API Service using Axios - Unified Server on Port 3000
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 180000, // 180 seconds for long-running queries
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // FormData: omit Content-Type so browser sets multipart/form-data with boundary
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * Query the orchestrator
 */
export const queryOrchestrator = async (query, context = {}) => {
  const body = {
    query,
    session_id: context.session_id || `session_${Date.now()}`,
    context: context,
  };
  if (context.document_id) {
    body.document_id = context.document_id;
  }
  const response = await apiClient.post('/api/query/query', body);
  return response.data;
};

/**
 * Upload PDF for compilation (type detection, text/vision, section consolidation).
 * Returns { success, document_id, summary } for chat document Q&A.
 */
export const uploadPdf = async (pdfFile, sessionId) => {
  const formData = new FormData();
  formData.append('pdf', pdfFile);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }
  const response = await apiClient.post('/api/query/pdf', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 900000, // 15 min - PDF compile can be slow with retries and rate-limit delays
  });
  return response.data;
};

/**
 * Get orchestrator status
 */
export const getOrchestratorStatus = async () => {
  const response = await apiClient.get('/api/query/status');
  return response.data;
};

/**
 * Get available tools
 */
export const getAvailableTools = async () => {
  const response = await apiClient.get('/api/query/tools');
  return response.data;
};

/**
 * Health check
 */
export const healthCheck = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

/**
 * Auth - Signup
 */
export const signup = async (userData) => {
  const response = await apiClient.post('/api/auth/signup', userData);
  return response.data;
};

/**
 * Auth - Login
 */
export const login = async (credentials) => {
  const response = await apiClient.post('/api/auth/login', credentials);
  if (response.data.token) {
    localStorage.setItem('access_token', response.data.token);
  }
  return response.data;
};

/**
 * Auth - Logout
 */
export const logout = async () => {
  const response = await apiClient.post('/api/auth/logout');
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  return response.data;
};

/**
 * Get user profile
 */
export const getUserProfile = async () => {
  const response = await apiClient.get('/api/users/me');
  return response.data;
};

/**
 * Chat History - Get recent sessions for authenticated user
 */
export const getChatHistory = async (limit = 20) => {
  const response = await apiClient.get(`/api/chat/history?limit=${limit}`);
  return response.data;
};

/**
 * Chat History - Get specific session messages
 */
export const getSessionMessages = async (sessionId) => {
  const response = await apiClient.get(`/api/chat/session/${sessionId}/messages`);
  return response.data;
};

/**
 * Chat History - Delete a session
 */
export const deleteSession = async (sessionId) => {
  const response = await apiClient.delete(`/api/chat/session/${sessionId}`);
  return response.data;
};

/**
 * Analyze image with Gemini Vision.
 * FormData: Content-Type is omitted by request interceptor so browser sends multipart with boundary.
 */
export const analyzeImage = async (imageFile, query, sessionId, analysisMode = 'general') => {
  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('query', query || 'Please analyze this image');
  formData.append('analysis_mode', analysisMode);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  const response = await apiClient.post('/api/query/vision', formData);
  return response.data;
};

/**
 * Capture image from camera
 */
export const captureFromCamera = () => {
  return new Promise((resolve, reject) => {
    navigator.mediaDevices.getUserMedia({ 
      video: { 
        facingMode: 'environment', // Use back camera on mobile
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      } 
    })
    .then(stream => {
      // Create video element for preview
      const video = document.createElement('video');
      video.srcObject = stream;
      video.style.width = '100%';
      video.style.maxWidth = '400px';
      video.autoplay = true;
      video.playsInline = true;
      
      // Create modal container
      const modal = document.createElement('div');
      modal.style.cssText = `
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.8); z-index: 9999;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        padding: 20px;
      `;
      
      const container = document.createElement('div');
      container.style.cssText = `
        background: white; border-radius: 12px; padding: 20px;
        max-width: 500px; width: 100%;
        display: flex; flex-direction: column; align-items: center;
      `;
      
      const title = document.createElement('h3');
      title.textContent = 'Camera Capture';
      title.style.cssText = 'margin: 0 0 16px 0; color: #333;';
      
      const buttonContainer = document.createElement('div');
      buttonContainer.style.cssText = `
        display: flex; gap: 12px; margin-top: 16px;
      `;
      
      const captureBtn = document.createElement('button');
      captureBtn.textContent = '📸 Capture';
      captureBtn.style.cssText = `
        background: #3b82f6; color: white; border: none;
        border-radius: 8px; padding: 12px 24px;
        cursor: pointer; font-size: 16px;
      `;
      
      const cancelBtn = document.createElement('button');
      cancelBtn.textContent = '❌ Cancel';
      cancelBtn.style.cssText = `
        background: #6b7280; color: white; border: none;
        border-radius: 8px; padding: 12px 24px;
        cursor: pointer; font-size: 16px;
      `;
      
      // Capture handler
      captureBtn.onclick = () => {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);
        
        canvas.toBlob((blob) => {
          // Stop camera
          stream.getTracks().forEach(track => track.stop());
          document.body.removeChild(modal);
          
          // Create file object
          const file = new File([blob], `camera_capture_${Date.now()}.jpg`, {
            type: 'image/jpeg'
          });
          
          resolve(file);
        }, 'image/jpeg', 0.8);
      };
      
      // Cancel handler
      cancelBtn.onclick = () => {
        stream.getTracks().forEach(track => track.stop());
        document.body.removeChild(modal);
        reject(new Error('Camera capture cancelled'));
      };
      
      // Assemble modal
      buttonContainer.appendChild(captureBtn);
      buttonContainer.appendChild(cancelBtn);
      container.appendChild(title);
      container.appendChild(video);
      container.appendChild(buttonContainer);
      modal.appendChild(container);
      document.body.appendChild(modal);
    })
    .catch(error => {
      console.error('Camera access error:', error);
      reject(error);
    });
  });
};

export default apiClient;
