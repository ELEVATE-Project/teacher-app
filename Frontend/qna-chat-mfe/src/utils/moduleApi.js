import apiClient from "./apiClient";

/**
 * MODULE API client for lesson and assignment generation
 */
export const moduleAPI = {
  // Topic Selection APIs
  getClasses: () => apiClient.get("/api/module/topics"),
  
  getSubjects: (className) => 
    apiClient.get(`/api/module/topics/${encodeURIComponent(className)}/subjects`),
  
  getTopics: (className, subject) => 
    apiClient.get(`/api/module/topics/${encodeURIComponent(className)}/${encodeURIComponent(subject)}`),

  // Lesson Generation APIs
  generateLesson: (data) => 
    apiClient.post("/api/module/generate", data),
  
  getLessons: () => 
    apiClient.get("/api/module/lessons"),
  
  getLesson: (lessonId) => 
    apiClient.get(`/api/module/lessons/${lessonId}`),
  
  deleteLesson: (lessonId) => 
    apiClient.delete(`/api/module/lessons/${lessonId}`),

  // Export APIs
  exportLessonPdf: (lessonId) => 
    apiClient.get(`/api/module/lessons/${lessonId}/export/pdf`, { responseType: "blob" }),
  
  exportLessonDoc: (lessonId) => 
    apiClient.get(`/api/module/lessons/${lessonId}/export/doc`, { responseType: "blob" }),
  
  exportLessonPpt: (lessonId) => 
    apiClient.get(`/api/module/lessons/${lessonId}/export/ppt`, { responseType: "blob" }),
  
  // Note: Assignment export uses lesson_id, not assignment_id
  exportAssignmentPdf: (lessonId, includeAnswers = false) => 
    apiClient.get(`/api/module/assignments/${lessonId}/export/pdf`, { 
      params: { include_answers: includeAnswers },
      responseType: "blob" 
    }),
  
  exportAssignmentDoc: (lessonId, includeAnswers = false) => 
    apiClient.get(`/api/module/assignments/${lessonId}/export/doc`, { 
      params: { include_answers: includeAnswers },
      responseType: "blob" 
    }),
};

export default moduleAPI;
