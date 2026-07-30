import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:3000";

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // Include cookies in requests
  timeout: 600000, // 600 seconds (10 minutes) for long-running operations
});

// Add request interceptor to include token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  signup: (userData) => {
    return apiClient.post("/api/auth/signup", userData);
  },
  login: (credentials) => {
    return apiClient.post("/api/auth/login", credentials);
  },
};

export const discussAPI = {
  list: (skip = 0, limit = 20) =>
    apiClient.get("/api/discuss", { params: { skip, limit } }),
  get: (postId) => apiClient.get(`/api/discuss/${postId}`),
  createPost: (body, location = null, tags = []) =>
    apiClient.post("/api/discuss", { body, location, tags }),
  createReply: (postId, body) =>
    apiClient.post(`/api/discuss/${postId}/reply`, { body }),
  askChanakya: (postId, query) =>
    apiClient.post(`/api/discuss/${postId}/chanakya`, { body: query }),
  upvote: (postId) => apiClient.post(`/api/discuss/${postId}/upvote`),
};

export default apiClient;
