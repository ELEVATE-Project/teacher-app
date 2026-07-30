import { useState, useRef, useEffect, useCallback } from "react";
import { transcribeAudio } from "../utils/sarvamApi";
import apiClient from "../utils/apiClient";
import {
  createSession,
  loadSession,
  saveSession,
  clearSession,
  hasRecoverableSession,
  saveChunk,
  updateSessionTranscript,
  completeSession,
  syncToBackend,
  setupOnlineListener,
} from "../utils/sessionPersistence";

// Chunk duration in milliseconds (25 seconds, safely under 30s API limit)
const CHUNK_DURATION_MS = 25000;
// Auto-save interval for crash recovery
const AUTO_SAVE_INTERVAL_MS = 5000;

function ActiveListeningMode() {
  // Recording states
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [showOptions, setShowOptions] = useState(false);

  // Session recovery states
  const [showRecoveryDialog, setShowRecoveryDialog] = useState(false);
  const [recoveredSession, setRecoveredSession] = useState(null);
  const sessionIdRef = useRef(null);

  // Chunking states
  const [pendingChunks, setPendingChunks] = useState(0);
  const [processedChunks, setProcessedChunks] = useState(0);
  const [chunkErrors, setChunkErrors] = useState(0);

  // Class metadata form
  const [classInfo, setClassInfo] = useState({
    topic: "",
    subject: "",
    classLevel: "Class 6",
  });

  // Feedback states
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunkIndexRef = useRef(0);
  const chunkIntervalRef = useRef(null);
  const audioChunksRef = useRef([]);
  const autoSaveIntervalRef = useRef(null);

  const classLevels = [
    "Class 1",
    "Class 2",
    "Class 3",
    "Class 4",
    "Class 5",
    "Class 6",
    "Class 7",
    "Class 8",
    "Class 9",
    "Class 10",
    "Class 11",
    "Class 12",
  ];

  const handleInputChange = (field, value) => {
    setClassInfo((prev) => ({ ...prev, [field]: value }));
  };

  const canStartRecording = classInfo.topic.trim() && classInfo.subject.trim();

  // Process a single audio chunk in the background
  const processChunk = useCallback(async (audioBlob, chunkNum) => {
    // Skip extremely small chunks (less than 100 bytes - truly empty)
    if (audioBlob.size < 100) {
      console.log(`Chunk ${chunkNum}: Skipped (empty: ${audioBlob.size} bytes)`);
      return;
    }

    setPendingChunks((prev) => prev + 1);
    console.log(`Chunk ${chunkNum}: Processing (${(audioBlob.size / 1024).toFixed(1)} KB)`);

    try {
      const { transcript: text } = await transcribeAudio(audioBlob, {
        mode: "transcribe",
        languageCode: "unknown",
      });

      if (text?.trim()) {
        setTranscript((prev) => {
          const newText = prev ? `${prev} ${text.trim()}` : text.trim();

          // Save chunk for crash recovery
          if (sessionIdRef.current) {
            saveChunk(sessionIdRef.current, text.trim(), chunkNum);
            // Update session transcript in localStorage
            updateSessionTranscript(sessionIdRef.current, newText, chunkNum);
          }

          return newText;
        });
        setProcessedChunks((prev) => prev + 1);
        console.log(`Chunk ${chunkNum}: Success - "${text.trim().substring(0, 50)}..."`);
      } else {
        console.log(`Chunk ${chunkNum}: Empty transcript`);
      }
    } catch (error) {
      console.error(`Chunk ${chunkNum}: Error -`, error.message);
      setChunkErrors((prev) => prev + 1);
    } finally {
      setPendingChunks((prev) => prev - 1);
    }
  }, []);

  // Create and start a new MediaRecorder instance
  const createAndStartRecorder = useCallback((stream) => {
    const recorderMimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm';

    const mediaRecorder = new MediaRecorder(stream, { mimeType: recorderMimeType });
    audioChunksRef.current = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      // Process the completed recording segment
      if (audioChunksRef.current.length > 0) {
        const chunkNum = ++chunkIndexRef.current;
        // Create blob with proper headers (each segment is a complete recording)
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        console.log(`Segment ${chunkNum}: Complete recording (${(audioBlob.size / 1024).toFixed(1)} KB)`);
        processChunk(audioBlob, chunkNum);
        audioChunksRef.current = [];
      }
    };

    mediaRecorder.onerror = (event) => {
      console.error("MediaRecorder error:", event.error);
    };

    mediaRecorder.start();
    return mediaRecorder;
  }, [processChunk]);

  // Stop current recorder and start a new one (for chunking)
  const rotateRecorder = useCallback(() => {
    if (mediaRecorderRef.current && streamRef.current &&
      mediaRecorderRef.current.state === "recording") {
      // Stop current recorder (triggers onstop which processes the chunk)
      mediaRecorderRef.current.stop();
      // Start a new recorder with the same stream
      mediaRecorderRef.current = createAndStartRecorder(streamRef.current);
      console.log("Rotated to new recorder segment");
    }
  }, [createAndStartRecorder]);

  const startRecording = async () => {
    if (!canStartRecording) {
      alert("Please enter the topic and subject before starting the class.");
      return;
    }

    try {
      // Reset states
      setTranscript("");
      setShowOptions(false);
      setFeedback(null);
      setShowFeedback(false);
      setPendingChunks(0);
      setProcessedChunks(0);
      setChunkErrors(0);
      chunkIndexRef.current = 0;

      // Create a new session for crash recovery
      const session = createSession(classInfo);
      sessionIdRef.current = session.sessionId;
      console.log(`[Session] Created new session: ${session.sessionId}`);

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Create first recorder
      mediaRecorderRef.current = createAndStartRecorder(stream);

      // Set up interval to rotate recorders every 25 seconds
      chunkIntervalRef.current = setInterval(() => {
        rotateRecorder();
      }, CHUNK_DURATION_MS);

      // Set up auto-save interval for crash recovery (every 5 seconds)
      autoSaveIntervalRef.current = setInterval(() => {
        if (sessionIdRef.current) {
          const session = loadSession();
          if (session && session.isActive) {
            // Sync to backend periodically (non-blocking)
            syncToBackend(apiClient, sessionIdRef.current, transcript, classInfo)
              .catch(err => console.warn('[AutoSync] Background sync failed:', err.message));
          }
        }
      }, AUTO_SAVE_INTERVAL_MS);

      setIsRecording(true);
      setIsPaused(false);
      console.log("Recording started with 25s rotation intervals and auto-save enabled");
    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert("Microphone access denied. Please enable microphone permissions.");
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && isRecording && !isPaused &&
      mediaRecorderRef.current.state === "recording") {
      // Clear the rotation interval while paused
      if (chunkIntervalRef.current) {
        clearInterval(chunkIntervalRef.current);
        chunkIntervalRef.current = null;
      }
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      console.log("Recording paused");
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && isRecording && isPaused &&
      mediaRecorderRef.current.state === "paused") {
      mediaRecorderRef.current.resume();
      // Restart the rotation interval
      chunkIntervalRef.current = setInterval(() => {
        rotateRecorder();
      }, CHUNK_DURATION_MS);
      setIsPaused(false);
      console.log("Recording resumed");
    }
  };

  const stopRecording = () => {
    // Clear the rotation interval
    if (chunkIntervalRef.current) {
      clearInterval(chunkIntervalRef.current);
      chunkIntervalRef.current = null;
    }

    // Clear the auto-save interval
    if (autoSaveIntervalRef.current) {
      clearInterval(autoSaveIntervalRef.current);
      autoSaveIntervalRef.current = null;
    }

    if (mediaRecorderRef.current && isRecording) {
      const recorderState = mediaRecorderRef.current.state;
      console.log(`stopRecording called, MediaRecorder state: ${recorderState}`);

      setIsProcessing(true);

      // Mark session as completed (not active) for crash recovery
      if (sessionIdRef.current) {
        completeSession(sessionIdRef.current);
        console.log(`[Session] Marked session ${sessionIdRef.current} as completed`);
      }

      // Only stop if recorder is active (recording or paused)
      if (recorderState === "recording" || recorderState === "paused") {
        // stop() triggers onstop which processes the final chunk
        mediaRecorderRef.current.stop();
      }

      // Stop all audio tracks
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }

      setIsRecording(false);
      setIsPaused(false);
      setShowOptions(true);
      setIsProcessing(false);
      console.log("Recording stopped completely");
    }
  };

  const analyzeTeaching = async () => {
    if (!transcript.trim()) {
      alert("No transcript available for analysis.");
      return;
    }

    // Wait for pending chunks if any
    if (pendingChunks > 0) {
      alert(`Please wait for ${pendingChunks} chunk(s) to finish processing.`);
      return;
    }

    setIsAnalyzing(true);
    try {
      // Updated endpoint to match unified API: POST /api/reflection (not /analyze)
      const response = await apiClient.post("/api/reflection", {
        topic: classInfo.topic,
        subject: classInfo.subject,
        class_level: classInfo.classLevel,
        transcript: transcript,
      });

      setFeedback(response.data.feedback);
      setShowFeedback(true);
      setShowOptions(false);
    } catch (error) {
      console.error("Analysis error:", error);
      alert("Failed to analyze the class. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const resetSession = () => {
    setTranscript("");
    setShowOptions(false);
    setFeedback(null);
    setShowFeedback(false);
    setPendingChunks(0);
    setProcessedChunks(0);
    setChunkErrors(0);
    setShowRecoveryDialog(false);
    setRecoveredSession(null);

    // Clear saved session from localStorage
    clearSession();
    sessionIdRef.current = null;
    console.log("[Session] Session reset and cleared");
  };

  // Handle session recovery
  const recoverSession = () => {
    if (recoveredSession) {
      setClassInfo({
        topic: recoveredSession.topic,
        subject: recoveredSession.subject,
        classLevel: recoveredSession.classLevel,
      });
      setTranscript(recoveredSession.transcript || "");
      setProcessedChunks(recoveredSession.chunkCount || 0);
      sessionIdRef.current = recoveredSession.sessionId;
      setShowOptions(true); // Show options to continue or analyze
      console.log(`[Session] Recovered session: ${recoveredSession.sessionId}`);
    }
    setShowRecoveryDialog(false);
    setRecoveredSession(null);
  };

  // Dismiss recovery (start fresh)
  const dismissRecovery = () => {
    clearSession();
    setShowRecoveryDialog(false);
    setRecoveredSession(null);
    console.log("[Session] Recovery dismissed, starting fresh");
  };

  // Check for recoverable session on mount
  useEffect(() => {
    if (hasRecoverableSession()) {
      const session = loadSession();
      if (session) {
        setRecoveredSession(session);
        setShowRecoveryDialog(true);
        console.log(`[Session] Found recoverable session: ${session.sessionId}`);
      }
    }

    // Set up online listener for sync when back online
    const cleanupOnlineListener = setupOnlineListener(apiClient);

    return () => {
      cleanupOnlineListener();
    };
  }, []);

  // Cleanup on unmount only
  useEffect(() => {
    return () => {
      // Clear rotation interval
      if (chunkIntervalRef.current) {
        clearInterval(chunkIntervalRef.current);
      }
      // Clear auto-save interval
      if (autoSaveIntervalRef.current) {
        clearInterval(autoSaveIntervalRef.current);
      }
      // Stop recorder if active
      if (mediaRecorderRef.current) {
        try {
          if (mediaRecorderRef.current.state !== "inactive") {
            mediaRecorderRef.current.stop();
          }
        } catch (e) {
          // Ignore errors if already stopped
        }
      }
      // Stop all audio tracks
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []); // Empty dependency array - only runs on unmount

  // Recovery Dialog Component
  const RecoveryDialog = () => {
    if (!showRecoveryDialog || !recoveredSession) return null;

    const timeSince = Math.round((Date.now() - recoveredSession.lastUpdate) / 60000);
    const transcriptPreview = recoveredSession.transcript?.substring(0, 150) || "";

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white border-3 border-[#000000] rounded-xl shadow-[6px_6px_0px_0px_#000000] max-w-md w-full p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-[#FEF3C7] border-2 border-[#000000] rounded-full flex items-center justify-center">
              <span className="text-2xl">⚠️</span>
            </div>
            <div>
              <h3 className="text-lg font-bold text-[#000000]" style={{ fontFamily: "TT Firs Neue, sans-serif" }}>
                Session Recovery
              </h3>
              <p className="text-xs text-gray-600">
                Found an interrupted session
              </p>
            </div>
          </div>

          <div className="bg-[#F3F4F6] border-2 border-[#000000] rounded-lg p-3 mb-4">
            <div className="text-xs space-y-1">
              <p><span className="font-semibold">Topic:</span> {recoveredSession.topic}</p>
              <p><span className="font-semibold">Subject:</span> {recoveredSession.subject}</p>
              <p><span className="font-semibold">Class:</span> {recoveredSession.classLevel}</p>
              <p><span className="font-semibold">Chunks recorded:</span> {recoveredSession.chunkCount || 0}</p>
              <p><span className="font-semibold">Last active:</span> {timeSince} minutes ago</p>
            </div>
            {transcriptPreview && (
              <div className="mt-2 pt-2 border-t border-gray-300">
                <p className="text-xs text-gray-600 italic">
                  "{transcriptPreview}..."
                </p>
              </div>
            )}
          </div>

          <div className="flex gap-3">
            <button
              onClick={recoverSession}
              className="flex-1 py-2 px-4 text-sm font-bold bg-[#22C55E] text-white border-2 border-[#000000] rounded-lg shadow-[3px_3px_0px_0px_#000000] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_0px_#000000] transition-all"
            >
              Recover Session
            </button>
            <button
              onClick={dismissRecovery}
              className="flex-1 py-2 px-4 text-sm font-bold bg-white border-2 border-[#000000] rounded-lg shadow-[3px_3px_0px_0px_#000000] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_0px_#000000] transition-all"
            >
              Start Fresh
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Feedback Summary Component
  const FeedbackSummary = ({ feedback, onClose }) => {
    if (!feedback) return null;

    return (
      <div className="space-y-5 animate-in fade-in duration-300">
        <div className="flex items-center justify-between">
          <h2
            className="text-xl font-bold text-[#000000]"
            style={{ fontFamily: "TT Firs Neue, sans-serif" }}
          >
            Class Reflection
          </h2>
          <button
            onClick={onClose}
            className="px-3 py-1 text-xs font-bold bg-white border-2 border-[#000000] rounded-lg shadow-[2px_2px_0px_0px_#000000] hover:bg-gray-100 transition-all"
          >
            New Session
          </button>
        </div>

        {/* Classroom Atmosphere */}
        <div className="bg-[#E0F2FE] border-2 border-[#000000] rounded-lg p-3">
          <p className="text-xs font-semibold text-[#000000] mb-1">
            Classroom Atmosphere
          </p>
          <p className="text-sm font-bold text-[#0369A1]">
            {feedback.classroom_atmosphere}
          </p>
        </div>

        {/* Strengths */}
        <div className="space-y-2">
          <p className="text-xs font-semibold text-[#000000] flex items-center gap-1">
            <span className="w-2 h-2 bg-[#22C55E] rounded-full"></span>
            What went well
          </p>
          <div className="space-y-2">
            {feedback.strengths.map((strength, idx) => (
              <div
                key={idx}
                className="bg-[#DCFCE7] border-2 border-[#000000] rounded-lg px-3 py-2 text-xs text-[#000000]"
              >
                {strength}
              </div>
            ))}
          </div>
        </div>

        {/* Issues */}
        <div className="space-y-2">
          <p className="text-xs font-semibold text-[#000000] flex items-center gap-1">
            <span className="w-2 h-2 bg-[#F59E0B] rounded-full"></span>
            Areas to improve
          </p>
          <div className="space-y-2">
            {feedback.issues.map((issue, idx) => (
              <div
                key={idx}
                className="bg-[#FEF3C7] border-2 border-[#000000] rounded-lg px-3 py-2 text-xs text-[#000000]"
              >
                {issue}
              </div>
            ))}
          </div>
        </div>

        {/* Topic Feedback */}
        {feedback.topic_feedback && feedback.topic_feedback.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-semibold text-[#000000] flex items-center gap-1">
              <span className="w-2 h-2 bg-[#8B5CF6] rounded-full"></span>
              Topic-specific feedback
            </p>
            <div className="space-y-2">
              {feedback.topic_feedback.map((item, idx) => (
                <div
                  key={idx}
                  className="bg-[#EDE9FE] border-2 border-[#000000] rounded-lg px-3 py-2 text-xs text-[#000000]"
                >
                  {item}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actionable Suggestions */}
        <div className="space-y-2">
          <p className="text-xs font-semibold text-[#000000] flex items-center gap-1">
            <span className="w-2 h-2 bg-[#EC4899] rounded-full"></span>
            Action items
          </p>
          <div className="bg-[#FCE7F3] border-2 border-[#000000] rounded-lg p-3 space-y-2">
            {feedback.suggestions.map((suggestion, idx) => (
              <div key={idx} className="flex items-start gap-2 text-xs text-[#000000]">
                <span className="font-bold text-[#BE185D]">{idx + 1}.</span>
                <span>{suggestion}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // Get status message based on current state
  const getStatusMessage = () => {
    if (isAnalyzing) return "Analyzing your class with AI...";
    if (isProcessing && pendingChunks > 0) return `Processing final chunks... (${pendingChunks} remaining)`;
    if (isProcessing) return "Finishing up...";
    if (isRecording && !isPaused) {
      if (pendingChunks > 0) {
        return `Recording... (transcribing ${pendingChunks} chunk${pendingChunks > 1 ? 's' : ''})`;
      }
      return "Recording class... tap End Class when done.";
    }
    if (isRecording && isPaused) return "Paused. Continue when ready.";
    if (!canStartRecording) return "Enter topic and subject to start recording.";
    return "Tap to start recording your class.";
  };

  return (
    <div className="min-h-screen bg-[#FFFFFF] flex flex-col relative overflow-hidden">
      {/* Session Recovery Dialog */}
      <RecoveryDialog />

      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: "url('/background_alternative_wavy.jpg')",
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
          opacity: 0.08,
        }}
      />

      <div className="relative z-10 flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-6xl bg-white border-2 border-[#000000] rounded-2xl shadow-[4px_4px_0px_0px_#000000] px-6 py-6 space-y-6">
          {/* Show Feedback Summary or Recording Interface */}
          {showFeedback && feedback ? (
            <FeedbackSummary feedback={feedback} onClose={resetSession} />
          ) : (
            <>
              {/* Header */}
              <div className="space-y-2 text-center">
                <p className="text-xs font-semibold uppercase tracking-wide text-[#000000] opacity-70">
                  Live Class Reflection
                </p>
                <h1
                  className="text-2xl md:text-3xl font-bold text-[#000000]"
                  style={{
                    fontFamily: "TT Firs Neue, sans-serif",
                    fontWeight: 700,
                  }}
                >
                  Teaching Coach
                </h1>
                <p className="text-sm text-[#000000] opacity-80 max-w-md mx-auto">
                  Record your class, get AI-powered feedback on teaching quality,
                  student engagement, and actionable suggestions.
                </p>
              </div>

              {/* Class Info Form - Only show when not recording */}
              {!isRecording && !showOptions && !isProcessing && (
                <div className="space-y-3 bg-[#F9FAFB] border-2 border-[#000000] rounded-lg p-4">
                  <p className="text-xs font-semibold text-[#000000]">
                    Class Details
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-[10px] font-medium text-[#000000] opacity-70">
                        Topic *
                      </label>
                      <input
                        type="text"
                        value={classInfo.topic}
                        onChange={(e) => handleInputChange("topic", e.target.value)}
                        placeholder="e.g., Photosynthesis"
                        className="w-full mt-1 px-3 py-2 text-xs border-2 border-[#000000] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#FDE047]"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-medium text-[#000000] opacity-70">
                        Subject *
                      </label>
                      <input
                        type="text"
                        value={classInfo.subject}
                        onChange={(e) => handleInputChange("subject", e.target.value)}
                        placeholder="e.g., Science"
                        className="w-full mt-1 px-3 py-2 text-xs border-2 border-[#000000] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#FDE047]"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-[10px] font-medium text-[#000000] opacity-70">
                      Class Level
                    </label>
                    <select
                      value={classInfo.classLevel}
                      onChange={(e) => handleInputChange("classLevel", e.target.value)}
                      className="w-full mt-1 px-3 py-2 text-xs border-2 border-[#000000] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#FDE047] bg-white"
                    >
                      {classLevels.map((level) => (
                        <option key={level} value={level}>
                          {level}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              {/* Recording Controls */}
              <div className="flex flex-col items-center gap-4 pt-2">
                <button
                  onClick={() => {
                    if (!isRecording) {
                      startRecording();
                    }
                  }}
                  disabled={isRecording || isProcessing || isAnalyzing || !canStartRecording}
                  className={`w-16 h-16 rounded-full border-2 border-[#000000] flex items-center justify-center shadow-[3px_3px_0px_0px_#000000] transition-all ${isRecording
                    ? "bg-red-500 cursor-not-allowed"
                    : isProcessing || isAnalyzing
                      ? "bg-gray-300 cursor-not-allowed"
                      : !canStartRecording
                        ? "bg-gray-200 cursor-not-allowed opacity-60"
                        : "bg-[#FDE047] hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-[2px_2px_0px_0px_#000000]"
                    }`}
                  aria-label="Start recording"
                >
                  {isRecording ? (
                    // Pulsing recording indicator
                    <span className="relative flex h-4 w-4">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-4 w-4 bg-white"></span>
                    </span>
                  ) : (
                    <svg
                      className="w-7 h-7 text-[#000000]"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 14a3 3 0 003-3V7a3 3 0 10-6 0v4a3 3 0 003 3z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 11a7 7 0 01-14 0M12 18v3m0 0H9m3 0h3"
                      />
                    </svg>
                  )}
                </button>

                <p className="text-xs font-medium text-[#000000] opacity-80 text-center">
                  {getStatusMessage()}
                </p>

                {/* Chunk processing indicator */}
                {(isRecording || isProcessing) && (processedChunks > 0 || pendingChunks > 0) && (
                  <div className="flex items-center gap-2 text-[10px] text-[#000000] opacity-70">
                    <span className="flex items-center gap-1">
                      <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                      {processedChunks} transcribed
                    </span>
                    {pendingChunks > 0 && (
                      <span className="flex items-center gap-1">
                        <span className="w-1.5 h-1.5 bg-yellow-500 rounded-full animate-pulse"></span>
                        {pendingChunks} processing
                      </span>
                    )}
                    {chunkErrors > 0 && (
                      <span className="flex items-center gap-1">
                        <span className="w-1.5 h-1.5 bg-red-500 rounded-full"></span>
                        {chunkErrors} failed
                      </span>
                    )}
                  </div>
                )}

                {isRecording && (
                  <div className="flex items-center gap-3 mt-2">
                    <button
                      onClick={isPaused ? resumeRecording : pauseRecording}
                      className="px-3 py-1.5 text-xs font-bold bg-white border-2 border-[#000000] rounded-lg shadow-[2px_2px_0px_0px_#000000] hover:bg-[#FDE047] hover:translate-x-0.5 hover:translate-y-0.5 transition-all"
                    >
                      {isPaused ? "Continue" : "Pause"}
                    </button>
                    <button
                      onClick={stopRecording}
                      className="px-3 py-1.5 text-xs font-bold bg-[#F99DA8] border-2 border-[#000000] rounded-lg shadow-[2px_2px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5 transition-all"
                    >
                      End Class
                    </button>
                  </div>
                )}
              </div>

              {/* Transcript Section */}
              <div className="border-t-2 border-dashed border-[#000000] pt-4 space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-xs font-semibold text-[#000000]">
                      Class Transcript
                    </p>
                    {transcript && (
                      <p className="text-[10px] text-[#000000] opacity-50">
                        {transcript.split(/\s+/).filter(Boolean).length} words
                      </p>
                    )}
                  </div>
                  <div className="min-h-[80px] max-h-40 overflow-y-auto bg-[#F9FAFB] border-2 border-[#000000] rounded-lg px-3 py-2 text-xs text-[#000000]">
                    {transcript ? (
                      <>
                        {transcript}
                        {pendingChunks > 0 && (
                          <span className="inline-flex items-center ml-1">
                            <span className="animate-pulse">...</span>
                          </span>
                        )}
                      </>
                    ) : isRecording ? (
                      <span className="opacity-50">
                        Transcript will appear as you speak (updates every 25 seconds)...
                      </span>
                    ) : (
                      "Your class transcript will appear here as you record."
                    )}
                  </div>
                </div>

                {/* Options after recording */}
                {showOptions && (
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-[#000000]">
                      Get feedback on your teaching
                    </p>
                    <button
                      onClick={analyzeTeaching}
                      disabled={isAnalyzing || pendingChunks > 0 || !transcript.trim()}
                      className={`w-full px-4 py-3 text-sm font-bold border-2 border-[#000000] rounded-lg shadow-[3px_3px_0px_0px_#000000] transition-all ${isAnalyzing || pendingChunks > 0 || !transcript.trim()
                        ? "bg-gray-200 cursor-not-allowed"
                        : "bg-[#F99DA8] hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-[2px_2px_0px_0px_#000000]"
                        }`}
                    >
                      {isAnalyzing ? (
                        <span className="flex items-center justify-center gap-2">
                          <svg
                            className="animate-spin h-4 w-4"
                            viewBox="0 0 24 24"
                          >
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                              fill="none"
                            />
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            />
                          </svg>
                          Analyzing with AI...
                        </span>
                      ) : pendingChunks > 0 ? (
                        `Waiting for ${pendingChunks} chunk(s)...`
                      ) : !transcript.trim() ? (
                        "No transcript to analyze"
                      ) : (
                        "Get Teaching Feedback"
                      )}
                    </button>
                    <p className="text-[10px] text-[#000000] opacity-70 text-center">
                      AI will analyze your teaching quality, student engagement,
                      and provide actionable suggestions.
                    </p>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default ActiveListeningMode;
