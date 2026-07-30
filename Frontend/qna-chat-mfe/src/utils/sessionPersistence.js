/**
 * Session Persistence Service for Active Listening
 * =================================================
 * 
 * Handles crash recovery and persistence for STT transcripts.
 * Uses localStorage for browser-side persistence and optional backend sync.
 * 
 * Features:
 * - Auto-saves transcript chunks to localStorage
 * - Recovers session after crash/reload
 * - Syncs with backend for server-side backup
 * - Handles offline scenarios gracefully
 */

const STORAGE_KEYS = {
  SESSION: 'chanakya_active_listening_session',
  CHUNKS: 'chanakya_stt_chunks',
  PENDING_SYNC: 'chanakya_pending_sync'
};

/**
 * Session data structure
 * @typedef {Object} ListeningSession
 * @property {string} sessionId - Unique session identifier
 * @property {string} topic - Class topic
 * @property {string} subject - Subject name
 * @property {string} classLevel - Class level (e.g., "Class 6")
 * @property {string} transcript - Accumulated transcript
 * @property {number} chunkCount - Number of processed chunks
 * @property {number} startTime - Session start timestamp
 * @property {number} lastUpdate - Last update timestamp
 * @property {boolean} isActive - Whether session is still active
 */

/**
 * Generate a unique session ID
 */
export function generateSessionId() {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Save session to localStorage
 * @param {ListeningSession} session 
 */
export function saveSession(session) {
  try {
    const sessionData = {
      ...session,
      lastUpdate: Date.now()
    };
    localStorage.setItem(STORAGE_KEYS.SESSION, JSON.stringify(sessionData));
    console.log('[SessionPersistence] Session saved:', session.sessionId);
    return true;
  } catch (error) {
    console.error('[SessionPersistence] Failed to save session:', error);
    return false;
  }
}

/**
 * Load session from localStorage
 * @returns {ListeningSession|null}
 */
export function loadSession() {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.SESSION);
    if (!data) return null;
    
    const session = JSON.parse(data);
    console.log('[SessionPersistence] Session loaded:', session.sessionId);
    return session;
  } catch (error) {
    console.error('[SessionPersistence] Failed to load session:', error);
    return null;
  }
}

/**
 * Clear session from localStorage
 */
export function clearSession() {
  try {
    localStorage.removeItem(STORAGE_KEYS.SESSION);
    localStorage.removeItem(STORAGE_KEYS.CHUNKS);
    localStorage.removeItem(STORAGE_KEYS.PENDING_SYNC);
    console.log('[SessionPersistence] Session cleared');
    return true;
  } catch (error) {
    console.error('[SessionPersistence] Failed to clear session:', error);
    return false;
  }
}

/**
 * Check if there's a recoverable session
 * @returns {boolean}
 */
export function hasRecoverableSession() {
  const session = loadSession();
  if (!session) return false;
  
  // Session is recoverable if:
  // 1. It was active
  // 2. It has some transcript
  // 3. It's not too old (less than 24 hours)
  const MAX_AGE_MS = 24 * 60 * 60 * 1000; // 24 hours
  const age = Date.now() - session.lastUpdate;
  
  return session.isActive && 
         session.transcript?.trim().length > 0 && 
         age < MAX_AGE_MS;
}

/**
 * Save a transcript chunk to localStorage (for crash recovery)
 * @param {string} sessionId 
 * @param {string} chunkText 
 * @param {number} chunkNumber 
 */
export function saveChunk(sessionId, chunkText, chunkNumber) {
  try {
    const chunksData = localStorage.getItem(STORAGE_KEYS.CHUNKS);
    const chunks = chunksData ? JSON.parse(chunksData) : {};
    
    if (!chunks[sessionId]) {
      chunks[sessionId] = [];
    }
    
    chunks[sessionId].push({
      number: chunkNumber,
      text: chunkText,
      timestamp: Date.now()
    });
    
    localStorage.setItem(STORAGE_KEYS.CHUNKS, JSON.stringify(chunks));
    console.log(`[SessionPersistence] Chunk ${chunkNumber} saved`);
    return true;
  } catch (error) {
    console.error('[SessionPersistence] Failed to save chunk:', error);
    return false;
  }
}

/**
 * Get all chunks for a session
 * @param {string} sessionId 
 * @returns {Array}
 */
export function getChunks(sessionId) {
  try {
    const chunksData = localStorage.getItem(STORAGE_KEYS.CHUNKS);
    if (!chunksData) return [];
    
    const chunks = JSON.parse(chunksData);
    return chunks[sessionId] || [];
  } catch (error) {
    console.error('[SessionPersistence] Failed to get chunks:', error);
    return [];
  }
}

/**
 * Update transcript in session
 * @param {string} sessionId 
 * @param {string} newTranscript 
 * @param {number} chunkCount 
 */
export function updateSessionTranscript(sessionId, newTranscript, chunkCount) {
  const session = loadSession();
  if (!session || session.sessionId !== sessionId) return false;
  
  session.transcript = newTranscript;
  session.chunkCount = chunkCount;
  return saveSession(session);
}

/**
 * Mark session as completed (not active)
 * @param {string} sessionId 
 */
export function completeSession(sessionId) {
  const session = loadSession();
  if (!session || session.sessionId !== sessionId) return false;
  
  session.isActive = false;
  session.endTime = Date.now();
  return saveSession(session);
}

/**
 * Create a new active listening session
 * @param {Object} classInfo - { topic, subject, classLevel }
 * @returns {ListeningSession}
 */
export function createSession(classInfo) {
  const session = {
    sessionId: generateSessionId(),
    topic: classInfo.topic,
    subject: classInfo.subject,
    classLevel: classInfo.classLevel,
    transcript: '',
    chunkCount: 0,
    startTime: Date.now(),
    lastUpdate: Date.now(),
    isActive: true
  };
  
  saveSession(session);
  return session;
}

/**
 * Sync session to backend (for server-side persistence)
 * This is called periodically or when chunks are processed
 * @param {string} sessionId 
 * @param {string} transcript 
 * @param {Object} classInfo 
 */
export async function syncToBackend(apiClient, sessionId, transcript, classInfo) {
  try {
    await apiClient.post('/api/listening/sync', {
      session_id: sessionId,
      topic: classInfo.topic,
      subject: classInfo.subject,
      class_level: classInfo.classLevel,
      transcript: transcript,
      timestamp: Date.now()
    });
    console.log('[SessionPersistence] Synced to backend');
    return true;
  } catch (error) {
    // Store for later sync when online
    addPendingSync(sessionId, transcript, classInfo);
    console.warn('[SessionPersistence] Backend sync failed, queued for later:', error.message);
    return false;
  }
}

/**
 * Add to pending sync queue (for offline recovery)
 */
function addPendingSync(sessionId, transcript, classInfo) {
  try {
    const pendingData = localStorage.getItem(STORAGE_KEYS.PENDING_SYNC);
    const pending = pendingData ? JSON.parse(pendingData) : [];
    
    // Replace existing entry for same session
    const existingIdx = pending.findIndex(p => p.sessionId === sessionId);
    const syncData = {
      sessionId,
      transcript,
      classInfo,
      timestamp: Date.now()
    };
    
    if (existingIdx >= 0) {
      pending[existingIdx] = syncData;
    } else {
      pending.push(syncData);
    }
    
    localStorage.setItem(STORAGE_KEYS.PENDING_SYNC, JSON.stringify(pending));
  } catch (error) {
    console.error('[SessionPersistence] Failed to add pending sync:', error);
  }
}

/**
 * Process pending syncs when back online
 */
export async function processPendingSyncs(apiClient) {
  try {
    const pendingData = localStorage.getItem(STORAGE_KEYS.PENDING_SYNC);
    if (!pendingData) return;
    
    const pending = JSON.parse(pendingData);
    if (pending.length === 0) return;
    
    console.log(`[SessionPersistence] Processing ${pending.length} pending syncs`);
    
    const successful = [];
    for (const sync of pending) {
      try {
        await syncToBackend(apiClient, sync.sessionId, sync.transcript, sync.classInfo);
        successful.push(sync.sessionId);
      } catch (error) {
        console.warn(`[SessionPersistence] Sync still failing for ${sync.sessionId}`);
      }
    }
    
    // Remove successful syncs
    const remaining = pending.filter(p => !successful.includes(p.sessionId));
    localStorage.setItem(STORAGE_KEYS.PENDING_SYNC, JSON.stringify(remaining));
    
    console.log(`[SessionPersistence] Processed syncs: ${successful.length} successful, ${remaining.length} remaining`);
  } catch (error) {
    console.error('[SessionPersistence] Failed to process pending syncs:', error);
  }
}

/**
 * Hook for detecting online/offline status
 */
export function setupOnlineListener(apiClient) {
  const handleOnline = () => {
    console.log('[SessionPersistence] Back online, processing pending syncs...');
    processPendingSyncs(apiClient);
  };
  
  window.addEventListener('online', handleOnline);
  
  // Return cleanup function
  return () => {
    window.removeEventListener('online', handleOnline);
  };
}

/**
 * Auto-save interval (call this to set up periodic saving)
 * @param {Function} getTranscript - Function to get current transcript
 * @param {Function} getSessionInfo - Function to get session info
 * @param {number} intervalMs - Save interval in milliseconds
 */
export function setupAutoSave(getTranscript, getSessionInfo, intervalMs = 5000) {
  const intervalId = setInterval(() => {
    const sessionInfo = getSessionInfo();
    if (!sessionInfo?.sessionId || !sessionInfo.isActive) return;
    
    const transcript = getTranscript();
    updateSessionTranscript(sessionInfo.sessionId, transcript, sessionInfo.chunkCount);
  }, intervalMs);
  
  // Return cleanup function
  return () => clearInterval(intervalId);
}

export default {
  generateSessionId,
  saveSession,
  loadSession,
  clearSession,
  hasRecoverableSession,
  saveChunk,
  getChunks,
  updateSessionTranscript,
  completeSession,
  createSession,
  syncToBackend,
  processPendingSyncs,
  setupOnlineListener,
  setupAutoSave
};