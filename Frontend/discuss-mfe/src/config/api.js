/**
 * API Configuration - Unified Server on Port 3000
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:3000";

export const API_ENDPOINTS = {
  // Query endpoints
  query: `${API_BASE_URL}/api/query/query`,
  queryStatus: `${API_BASE_URL}/api/query/status`,
  queryTools: `${API_BASE_URL}/api/query/tools`,

  // Auth endpoints
  signup: `${API_BASE_URL}/api/auth/signup`,
  login: `${API_BASE_URL}/api/auth/login`,
  logout: `${API_BASE_URL}/api/auth/logout`,

  // User endpoints
  profile: `${API_BASE_URL}/api/users/profile`,

  // Health check
  health: `${API_BASE_URL}/health`,
};

export default API_ENDPOINTS;
