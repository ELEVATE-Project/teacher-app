import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import {
  queryOrchestrator,
  getChatHistory,
  getSessionMessages,
  analyzeImage,
  captureFromCamera,
  uploadPdf,
} from "../services/api";
import { useAuth } from "../context/AuthContext";
import { transcribeAudio, textToSpeechAndPlay } from "../utils/sarvamApi";
import ResponseFormatter from "../components/ResponseFormatter";
import Header from "../components/Header";
import LessonPreview from "../components/module/LessonPreview";
import AssignmentPreview from "../components/module/AssignmentPreview";
import ExportControls from "../components/module/ExportControls";

function ChatInterface({ mode }) {
  const { user } = useAuth();

  // Helper to parse mode from prop or URL query params on initial mount
  const getInitialMode = () => {
    const params = new URLSearchParams(window.location.search);
    let activeMode = mode;
    if (params.has("activity")) {
      activeMode = "activity_generator";
    } else if (params.get("mode")) {
      activeMode = params.get("mode");
    }
    return activeMode || "general";
  };

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const [lockedMode, setLockedMode] = useState(() => {
    const initial = getInitialMode();
    return initial === "general" ? null : initial;
  });
  const attachInputRef = useRef(null);
  const imageInputRef = attachInputRef; // alias for backward compatibility

  // PDF document attachment (chat document Q&A)
  const [attachedDocumentId, setAttachedDocumentId] = useState(null);
  const [isUploadingPdf, setIsUploadingPdf] = useState(false);

  // Voice recording states
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessingVoice, setIsProcessingVoice] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const speechSynthesisRef = useRef(null);
  const [speakingMessageId, setSpeakingMessageId] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const nextMessageIdRef = useRef(0);

  // Quick Answer Mode state
  const [quickAnswerMode, setQuickAnswerMode] = useState(false);

  // Image upload states
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [analysisMode, setAnalysisMode] = useState('general');
  const [showAnalysisModes, setShowAnalysisModes] = useState(false);

  // Chat Mode & Artifact Pane states
  const [chatMode, setChatMode] = useState(() => getInitialMode()); // "general" or "module_builder"
  const [showArtifact, setShowArtifact] = useState(false);
  const [activeArtifactLesson, setActiveArtifactLesson] = useState(null);
  const [activeArtifactAssignment, setActiveArtifactAssignment] = useState(null);
  const [activeArtifactTab, setActiveArtifactTab] = useState("lesson");
  const [activeLessonId, setActiveLessonId] = useState(null);
  const [isCollapsibleChatMinimized, setIsCollapsibleChatMinimized] = useState(false);

  // Load chat history on mount and when chatMode changes
  useEffect(() => {
    loadChatHistory();
  }, [chatMode]);

  // Set and lock chat mode based on prop or URL query params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    let activeMode = mode;

    if (params.has("activity")) {
      activeMode = "activity_generator";
    } else if (params.get("mode")) {
      activeMode = params.get("mode");
    }

    if (activeMode) {
      setChatMode(activeMode);
      setLockedMode(activeMode);
      console.log(`[DEBUG] Active Screen: Chat Interface | Route: ${window.location.pathname}${window.location.search} | Mode Activated: ${activeMode}`);
    } else {
      setLockedMode(null);
      setChatMode("general");
      console.log(`[DEBUG] Active Screen: Chat Interface | Route: ${window.location.pathname}${window.location.search} | Mode Activated: Dynamic/General`);
    }
  }, [mode, window.location.pathname, window.location.search]);

  const loadChatHistory = async () => {
    try {
      const response = await getChatHistory(20, chatMode);
      if (response.success && response.sessions) {
        // Sort sessions by updated_at in descending order (most recent first)
        const sortedSessions = [...response.sessions].sort((a, b) => {
          return new Date(b.updated_at) - new Date(a.updated_at);
        });

        // Format sessions for display
        const formattedSessions = sortedSessions.map((session) => {
          const date = new Date(session.updated_at);
          const today = new Date();
          const yesterday = new Date(today);
          yesterday.setDate(yesterday.getDate() - 1);

          let dateStr;
          if (date.toDateString() === today.toDateString()) {
            dateStr = "Today";
          } else if (date.toDateString() === yesterday.toDateString()) {
            dateStr = "Yesterday";
          } else {
            dateStr = date.toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            });
          }

          return {
            id: session.session_id,
            title: session.title || "New conversation",
            date: dateStr,
            message_count: session.message_count,
          };
        });
        setChatHistory(formattedSessions);
      }
    } catch (error) {
      console.error("Error loading chat history:", error);
    }
  };

  const loadSession = async (sessionId) => {
    try {
      const response = await getSessionMessages(sessionId);
      if (response.success && response.messages) {
        // Convert backend messages to frontend format
        let lastModuleMessage = null;
        const formattedMessages = response.messages.map((msg, idx) => {
          const baseMessage = {
            id: `session-${sessionId}-${idx}`,
            from: msg.role === "user" ? "teacher" : "bot",
            text: msg.content,
          };

          // For assistant messages, reconstruct the full data structure from metadata
          if (msg.role === "assistant" && msg.metadata) {
            try {
              const metadata =
                typeof msg.metadata === "string"
                  ? JSON.parse(msg.metadata)
                  : msg.metadata;

              // If we have the full result data in metadata, use it
              if (metadata.result) {
                baseMessage.data = {
                  success: true,
                  tool_used: msg.tool_used || metadata.tool_used,
                  reasoning: metadata.reasoning,
                  result: metadata.result,
                  resources: metadata.resources ?? null,
                  confidence: msg.confidence || metadata.confidence,
                  timestamp: metadata.timestamp,
                };
                baseMessage.tool_used = msg.tool_used || metadata.tool_used;
                baseMessage.confidence = msg.confidence || metadata.confidence;

                // Track the last module generator preview payload
                if (metadata.result.status === "preview_module") {
                  lastModuleMessage = metadata.result;
                }
              }
            } catch (error) {
              console.error("Error parsing message metadata:", error);
            }
          }

          return baseMessage;
        });

        setMessages(formattedMessages);
        setCurrentSessionId(sessionId);

        // Restore active workspace if session had a module
        if (lastModuleMessage) {
          setActiveArtifactLesson(lastModuleMessage.lesson);
          setActiveArtifactAssignment(lastModuleMessage.assignment);
          setActiveLessonId(lastModuleMessage.lesson_id);
          setShowArtifact(true);
          setChatMode("module_builder");
        } else {
          setShowArtifact(false);
          setChatMode(lockedMode || "general");
        }
      }
    } catch (error) {
      console.error("Error loading session:", error);
    }
  };

  const startNewChat = () => {
    setMessages([]);
    setAttachedDocumentId(null);
    // Generate a new session ID
    const newSessionId = `session_${Date.now()}`;
    setCurrentSessionId(newSessionId);
    setInput("");
    setShowArtifact(false);
    setActiveArtifactLesson(null);
    setActiveArtifactAssignment(null);
    setActiveLessonId(null);
    setChatMode(lockedMode || "general");
    setIsCollapsibleChatMinimized(false);
  };

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    // Skip scroll if textarea is focused to prevent unwanted jumps
    const activeElement = document.activeElement;
    const isTextareaFocused = activeElement?.tagName === "TEXTAREA";

    if (!isTextareaFocused) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Handle image selection
  const handleImageSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        alert('Please select a valid image file (JPEG, PNG, GIF, or WebP)');
        return;
      }
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        alert('Image is too large. Maximum size is 10MB.');
        return;
      }
      setSelectedImage(file);
      // Create preview URL
      const previewUrl = URL.createObjectURL(file);
      setImagePreview(previewUrl);
      setShowAnalysisModes(true); // Show analysis mode selector
    }
  };

  // Handle camera capture
  const handleCameraCapture = async () => {
    try {
      const capturedImage = await captureFromCamera();
      setSelectedImage(capturedImage);
      // Create preview URL
      const previewUrl = URL.createObjectURL(capturedImage);
      setImagePreview(previewUrl);
      setShowAnalysisModes(true); // Show analysis mode selector
    } catch (error) {
      if (error.message !== 'Camera capture cancelled') {
        alert('Failed to access camera. Please ensure camera permissions are granted.');
      }
    }
  };

  // PDF upload: attach document for chat Q&A
  const handlePdfSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.type !== "application/pdf") {
      alert("Please select a PDF file.");
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      alert("PDF is too large. Maximum size is 20MB.");
      return;
    }
    const sessionId = currentSessionId || `session_${Date.now()}`;
    if (!currentSessionId) setCurrentSessionId(sessionId);
    const userMsgId = `msg-${Date.now()}-${nextMessageIdRef.current++}`;
    setMessages((m) => [
      ...m,
      { id: userMsgId, from: "teacher", text: `Uploaded: ${file.name}`, pdfName: file.name },
    ]);
    setIsUploadingPdf(true);
    try {
      const data = await uploadPdf(file, sessionId);
      if (data.success && data.document_id) {
        setAttachedDocumentId(data.document_id);
        const botMsgId = `msg-${Date.now()}-${nextMessageIdRef.current++}`;
        setMessages((m) => [
          ...m,
          {
            id: botMsgId,
            from: "bot",
            text: data.summary || "Document ready. You can ask questions about it.",
            data: { success: true, tool_used: "document_ready", result: { summary: data.summary, document_id: data.document_id }, confidence: 0.95 },
            tool_used: "document_ready",
            confidence: 0.95,
          },
        ]);
      } else {
        setMessages((m) => [...m, { id: `msg-${Date.now()}`, from: "bot", text: data.error || "PDF processing failed." }]);
      }
      await loadChatHistory();
    } catch (err) {
      const errMsg = err.response?.data?.detail || err.message || "PDF processing failed.";
      setMessages((m) => [...m, { id: `msg-${Date.now()}`, from: "bot", text: errMsg }]);
    } finally {
      setIsUploadingPdf(false);
      if (attachInputRef.current) attachInputRef.current.value = "";
    }
  };

  // Single attach handler: image or PDF
  const handleAttachChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const isPdf = file.type === "application/pdf";
    const isImage = ["image/jpeg", "image/png", "image/gif", "image/webp"].includes(file.type);
    if (isPdf) {
      await handlePdfSelect({ target: { files: [file] } });
    } else if (isImage) {
      handleImageSelect({ target: { files: [file] } });
    } else {
      alert("Please select an image (JPEG, PNG, GIF, WebP) or a PDF file.");
    }
    e.target.value = "";
  };

  // Clear selected image
  const clearImage = () => {
    setSelectedImage(null);
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
    }
    setImagePreview(null);
    setShowAnalysisModes(false);
    setAnalysisMode('general');
    if (attachInputRef.current) {
      attachInputRef.current.value = '';
    }
  };

  // Convert file to data URL so image stays valid after blob URL is revoked
  const fileToDataUrl = (file) =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => reject(new Error("Failed to read image"));
      reader.readAsDataURL(file);
    });

  // Send message with optional image
  const sendMessage = async () => {
    if ((!input.trim() && !selectedImage) || isLoading || isUploadingPdf) return;

    const userMessage = input.trim();
    const userMessageId = `msg-${Date.now()}-${nextMessageIdRef.current++}`;
    const botMessageId = `msg-${Date.now()}-${nextMessageIdRef.current++}`;

    // Use durable data URL for message so image still renders after we revoke the blob
    let messageImageUrl = imagePreview;
    if (selectedImage) {
      try {
        messageImageUrl = await fileToDataUrl(selectedImage);
      } catch {
        messageImageUrl = imagePreview;
      }
    }

    // Add user message with image (data URL so it persists after clearImage revokes blob)
    setMessages((m) => [
      ...m,
      {
        id: userMessageId,
        from: "teacher",
        text: userMessage || "Please analyze this image",
        image: messageImageUrl || undefined,
        imageName: selectedImage?.name,
      },
    ]);

    const currentImage = selectedImage;
    const currentImagePreview = imagePreview;
    const currentAnalysisMode = analysisMode;

    setInput("");
    clearImage();
    // Add these 3 lines right after setInput("")
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
    }
    setIsLoading(true);

    try {

      // Use existing session ID or create new one
      const sessionId = currentSessionId || `session_${Date.now()}`;
      if (!currentSessionId) {
        setCurrentSessionId(sessionId);
      }

      let data;
      
      // If image is selected, use vision API
      if (currentImage) {
        data = await analyzeImage(
          currentImage,
          userMessage || "Please analyze this image and provide educational insights",
          sessionId,
          currentAnalysisMode
        );
      } else {
        // Call the orchestrator API with session ID (include document_id when PDF is attached)
        const context = {
          session_id: sessionId,
          quick_answer_mode: quickAnswerMode,
        };
        if (attachedDocumentId) context.document_id = attachedDocumentId;
        if (chatMode !== "general") {
          context.selected_tool = chatMode;
          if (chatMode === "module_builder" && activeLessonId) {
            context.lesson_id = activeLessonId;
          }
        }
        data = await queryOrchestrator(userMessage, context);
      }

      // Extract text for fallback display
      let botResponseText = "";
      if (data.success && data.result) {
        if (data.result.response != null && data.tool_used === "vision_analysis") {
          botResponseText = data.result.response;
        } else if (data.result.explanation) {
          botResponseText = data.result.explanation;
        } else if (data.result.activity_name) {
          botResponseText = data.result.description;
        } else if (typeof data.result === "string") {
          botResponseText = data.result;
        } else if (data.result.summary != null && (data.result.web_resources != null || data.result.video_resources != null || data.result.educational_resources != null)) {
          // Resource-finder style: show summary, resources rendered by ResponseFormatter
          botResponseText = data.result.summary;
        } else if (data.result.response != null) {
          botResponseText = data.result.response;
        } else {
          botResponseText = JSON.stringify(data.result, null, 2);
        }
      } else {
        botResponseText =
          data.error || "Sorry, I couldn't process your request.";
      }

      setMessages((m) => [
        ...m,
        {
          id: botMessageId,
          from: "bot",
          text: botResponseText,
          data: data, // Store full response for formatting
          tool_used: data.tool_used,
          confidence: data.confidence,
          from_cache: data.from_cache === true,
        },
      ]);

      // If we got a module builder response with a module draft, load it into the active workspace
      if (data.success && data.result && data.result.status === "preview_module") {
        setActiveArtifactLesson(data.result.lesson);
        setActiveArtifactAssignment(data.result.assignment);
        setActiveLessonId(data.result.lesson_id);
        setShowArtifact(true);
        setActiveArtifactTab("lesson");
      }

      // Refresh chat history to show new conversation
      await loadChatHistory();
    } catch (error) {
      console.error("Error calling orchestrator:", error);

      let errorMessage = "Sorry, I'm having trouble connecting to the server.";
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }

      setMessages((m) => [
        ...m,
        {
          id: `msg-${Date.now()}-${nextMessageIdRef.current++}`,
          from: "bot",
          text: errorMessage,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTopicSelect = async (className, subject, topicName) => {
    setIsLoading(true);
    const userMessage = `Generate module for chapter: ${topicName}`;
    const userMsgId = `msg-${Date.now()}-${nextMessageIdRef.current++}`;
    const botMsgId = `msg-${Date.now()}-${nextMessageIdRef.current++}`;
    
    setMessages((m) => [
      ...m,
      {
        id: userMsgId,
        from: "teacher",
        text: userMessage,
      },
    ]);
    
    const sessionId = currentSessionId || `session_${Date.now()}`;
    if (!currentSessionId) setCurrentSessionId(sessionId);
    
    try {
      const context = {
        session_id: sessionId,
        selected_tool: "module_builder",
        class_name: className,
        subject: subject,
        topic: topicName,
      };
      
      const data = await queryOrchestrator(userMessage, context);
      
      let botResponseText = "";
      if (data.success && data.result) {
        botResponseText = data.result.response || "Module generated.";
      } else {
        botResponseText = data.error || "Sorry, failed to generate module.";
      }
      
      setMessages((m) => [
        ...m,
        {
          id: botMsgId,
          from: "bot",
          text: botResponseText,
          data: data,
          tool_used: data.tool_used,
          confidence: data.confidence,
        },
      ]);
      
      if (data.success && data.result && data.result.status === "preview_module") {
        setActiveArtifactLesson(data.result.lesson);
        setActiveArtifactAssignment(data.result.assignment);
        setActiveLessonId(data.result.lesson_id);
        setShowArtifact(true);
        setActiveArtifactTab("lesson");
      }
      
      await loadChatHistory();
    } catch (error) {
      console.error("Error generating module:", error);
      setMessages((m) => [
        ...m,
        {
          id: `msg-${Date.now()}-${nextMessageIdRef.current++}`,
          from: "bot",
          text: `Error generating module: ${error.message}`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleTextareaChange = (e) => {
    setInput(e.target.value);
    // Auto-resize textarea
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 128)}px`;
  };

  // Reset textarea height when input is cleared (e.g. after send)
  useEffect(() => {
    if (!input.trim() && inputRef.current) {
      inputRef.current.style.height = "auto";
    }
  }, [input]);

  // Start voice recording - using only Sarvam AI
  const startRecording = async () => {
    try {
      // Clear input field when starting new recording
      setInput("");

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/wav",
        });

        if (audioChunksRef.current.length > 0) {
          setIsProcessingVoice(true);
          try {
            const { transcript } = await transcribeAudio(audioBlob, {
              mode: "transcribe",
              languageCode: "unknown",
            });
            if (transcript) {
              setInput(transcript.trim());
            }
          } catch (error) {
            console.error("Sarvam STT error:", error);
            alert("Failed to transcribe audio. Please try again.");
          } finally {
            setIsProcessingVoice(false);
          }
        }

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert("Microphone access denied. Please enable microphone permissions.");
    }
  };

  // Stop voice recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Text-to-Speech handler
  const speakText = async (text, messageId) => {
    // Stop any currently speaking message
    if (speechSynthesisRef.current) {
      if (speechSynthesisRef.current instanceof Audio) {
        speechSynthesisRef.current.pause();
        speechSynthesisRef.current.currentTime = 0;
      }
      speechSynthesisRef.current = null;
    }

    try {
      // Silently limit to 2500 characters (API limit)
      const truncatedText = text.length > 2500
        ? text.substring(0, 2500)
        : text;

      const audio = await textToSpeechAndPlay(truncatedText, {
        onPlay: () => setSpeakingMessageId(messageId),
        onEnd: () => {
          setSpeakingMessageId(null);
          speechSynthesisRef.current = null;
        },
      });
      speechSynthesisRef.current = audio;
    } catch (error) {
      console.error("TTS error:", error);
      alert(`Failed to generate speech: ${error.message}`);
    }
  };

  // Stop speaking
  const stopSpeaking = () => {
    if (speechSynthesisRef.current) {
      if (speechSynthesisRef.current instanceof Audio) {
        speechSynthesisRef.current.pause();
        speechSynthesisRef.current = null;
      } else {
        window.speechSynthesis.cancel();
      }
      setSpeakingMessageId(null);
      speechSynthesisRef.current = null;
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop();
      }
      if (speechSynthesisRef.current) {
        if (speechSynthesisRef.current instanceof Audio) {
          speechSynthesisRef.current.pause();
        }
      }
    };
  }, [isRecording]);

  return (
    <div className="h-full min-h-0 bg-[#FFFFFF] flex flex-col relative overflow-hidden">
      {/* Background Image with very low opacity */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: "url('/background_alternative_wavy.jpg')",
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
          opacity: 0.1,
        }}
      />

      <div className="relative z-10 flex w-full flex-1 min-h-0">
        {/* Sidebar - Chat History */}
        <aside className="hidden md:flex flex-col w-56 bg-[#FFFFFF] border-r-2 border-[#000000]">
          {/* Sidebar Header
          <div className="p-4 border-b-2 border-[#000000]">
            <Link
              to="/"
              className="flex items-center gap-3 text-[#000000] hover:opacity-80 transition"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                />
              </svg>
              <span className="text-base font-bold">Chanakya</span>
            </Link>
          </div> */}

          {/* New Chat Button */}
          <div className="p-3 border-b-2 border-[#000000]">
            <button
              className="w-full bg-[#E0EEEF] border-2 border-[#000000] px-3 py-1.5 font-bold text-[#000000] shadow-[2px_2px_0px_0px_#000000] hover:shadow-[1px_1px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5 transition-all flex items-center justify-center gap-2"
              onClick={startNewChat}
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              New Chat
            </button>
          </div>

          {/* Chat History */}
          <div className="flex-1 overflow-y-auto p-3 max-h-[calc(100vh-140px)]">
            <div className="text-xs font-bold text-[#000000] mb-3 px-2">
              Recent Chats
            </div>
            <div className="space-y-2">
              {chatHistory.map((chat) => (
                <button
                  key={chat.id}
                  className="w-full text-left p-3 rounded-lg border-2 border-[#000000] bg-white hover:bg-[#FDE047] transition-all shadow-[2px_2px_0px_0px_#000000] hover:shadow-[1px_1px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5"
                  onClick={() => loadSession(chat.id)}
                >
                  <div className="flex items-start gap-3">
                    <div className="w-7 h-7 rounded-full bg-[#E8D5FF] border-2 border-[#000000] flex items-center justify-center flex-shrink-0">
                      <svg
                        className="w-4 h-4 text-[#000000]"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                        />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-bold text-[#000000] truncate">
                        {chat.title}
                      </div>
                      <div className="text-xs text-[#000000] opacity-60 mt-1">
                        {chat.date}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Main Chat Area */}
        <main
          className={`${
            showArtifact
              ? isCollapsibleChatMinimized
                ? "w-0 hidden md:flex md:w-16 flex-none"
                : "w-full md:w-[450px] flex-none border-r-0 md:border-r-2 border-[#000000]"
              : "flex-1"
          } flex flex-col bg-[#FFFFFF] min-h-0 transition-all duration-300 relative`}
        >
          {showArtifact && isCollapsibleChatMinimized ? (
            <div className="flex-1 flex flex-col items-center justify-start py-6 gap-6 bg-[#F9F9FB] h-full border-r-2 border-[#000000]">
              <button
                onClick={() => setIsCollapsibleChatMinimized(false)}
                className="p-2.5 border-2 border-[#000000] rounded-xl bg-[#FDE047] hover:bg-[#e0c23a] transition-all shadow-[2px_2px_0px_0px_#000000] hover:shadow-[1px_1px_0px_0px_#000000] hover:translate-y-0.5 text-[#000000]"
                title="Expand Chat"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                </svg>
              </button>
              <div className="flex-1 flex items-center justify-center">
                <span className="transform -rotate-90 whitespace-nowrap font-bold text-sm text-[#000000] tracking-wider uppercase">
                  💬 Chat Assistant
                </span>
              </div>
            </div>
          ) : (
            <>
              {/* Desktop Collapsible Header */}
              {showArtifact && !isCollapsibleChatMinimized && (
                <div className="hidden md:flex items-center justify-between px-4 py-3 border-b-2 border-[#000000] bg-[#F9F9FB] flex-shrink-0">
                  <span className="font-bold text-xs uppercase tracking-wide text-[#000000]">Chat Assistant</span>
                  <button
                    onClick={() => setIsCollapsibleChatMinimized(true)}
                    className="p-1 border-2 border-[#000000] rounded bg-white hover:bg-[#FDE047] transition-all shadow-[1px_1px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5"
                    title="Collapse Chat"
                  >
                    <svg className="w-4 h-4 text-[#000000]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7M19 19l-7-7 7-7" />
                    </svg>
                  </button>
                </div>
              )}

              {/* Mobile Header */}
              <div className="md:hidden flex items-center justify-between px-4 py-3 border-b-2 border-[#000000] bg-[#FFFFFF]">
            <Link to="/" className="text-lg font-bold text-[#000000]">
              Chanakya
            </Link>
            <button
              onClick={startNewChat}
              className="p-1.5 border-2 border-[#000000] rounded"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
            </button>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto px-4 py-8 min-h-0 max-h-[calc(100vh-200px)]">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full max-w-3xl mx-auto">
                <div>
                  <img
                    src="/happy_chanakya.png"
                    alt="Chanakya"
                    className="w-48 h-48 md:w-80 md:h-80 object-contain"
                  />
                </div>

                <div className="text-center mb-8">
                  <h2
                    className="text-2xl md:text-3xl font-bold text-[#000000] mb-1"
                    style={{
                      fontFamily: "TT Firs Neue, sans-serif",
                      fontWeight: 700,
                    }}
                  >
                    How can I help you today, {user?.name || "Teacher"}?
                  </h2>
                </div>

                 {/* Feature Mode Buttons */}
                 <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-2xl">
                   {[
                     {
                       name: "Crisis-Handling Mode",
                       mode: "crisis_handler",
                       color: "#F99DA8",
                       icon: (
                         <svg
                           className="w-4 h-4"
                           fill="none"
                           stroke="currentColor"
                           viewBox="0 0 24 24"
                         >
                           <path
                             strokeLinecap="round"
                             strokeLinejoin="round"
                             strokeWidth={2}
                             d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                           />
                         </svg>
                       ),
                     },
                     {
                       name: "Activity Generator",
                       mode: "activity_generator",
                       color: "#FDE047",
                       icon: (
                         <svg
                           className="w-4 h-4"
                           fill="none"
                           stroke="currentColor"
                           viewBox="0 0 24 24"
                         >
                           <path
                             strokeLinecap="round"
                             strokeLinejoin="round"
                             strokeWidth={2}
                             d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                           />
                         </svg>
                       ),
                     },
                     {
                       name: "Module Creator",
                       mode: "module_builder",
                       color: "#D4F1C5",
                       icon: (
                         <svg
                           className="w-4 h-4"
                           fill="none"
                           stroke="currentColor"
                           viewBox="0 0 24 24"
                         >
                           <path
                             strokeLinecap="round"
                             strokeLinejoin="round"
                             strokeWidth={2}
                             d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                           />
                           <path
                             strokeLinecap="round"
                             strokeLinejoin="round"
                             strokeWidth={2}
                             d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                           />
                         </svg>
                       ),
                     },
                     {
                       name: "Q&A Expert Teacher",
                       mode: "expert_teacher",
                       color: "#A7F3D0",
                       icon: (
                         <svg
                           className="w-4 h-4"
                           fill="none"
                           stroke="currentColor"
                           viewBox="0 0 24 24"
                         >
                           <path
                             strokeLinecap="round"
                             strokeLinejoin="round"
                             strokeWidth={2}
                             d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                           />
                         </svg>
                       ),
                     },
                     {
                       name: "Post-class Planner",
                       mode: "classroom_guidance",
                       color: "#E8D5FF",
                       icon: (
                         <svg
                           className="w-4 h-4"
                           fill="none"
                           stroke="currentColor"
                           viewBox="0 0 24 24"
                         >
                           <path
                             strokeLinecap="round"
                             strokeLinejoin="round"
                             strokeWidth={2}
                             d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                           />
                         </svg>
                       ),
                     },
                   ].filter(feature => {
                      const allowedModes = ["module_builder", "expert_teacher", "activity_generator"];
                      if (!allowedModes.includes(feature.mode)) return false;
                      return !lockedMode ? true : feature.mode === lockedMode;
                    })
                    .map((feature) => (
                     <button
                       key={feature.name}
                       className="p-3 rounded-lg border-2 border-[#000000] text-left transition-all shadow-[2px_2px_0px_0px_#000000] hover:shadow-[1px_1px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5"
                       style={{ backgroundColor: feature.color }}
                       onClick={() => {
                         if (feature.mode === "module_builder") {
                           setChatMode("module_builder");
                           setInput("Create a module for Class 7 Geography");
                         } else if (feature.mode === "crisis_handler") {
                           setChatMode("crisis_handler");
                           setInput("A student is throwing tantrums in class. How should I respond?");
                         } else if (feature.mode === "activity_generator") {
                           setChatMode("activity_generator");
                           setInput("Generate a classroom activity for Class 8 Mathematics");
                         } else if (feature.mode === "classroom_guidance") {
                           setChatMode("classroom_guidance");
                           setInput("I just finished teaching algebra. Plan my next reflection and guidance.");
                         } else if (feature.mode === "expert_teacher") {
                           setChatMode("expert_teacher");
                           setInput("How do you teach quantum physics concepts to high schoolers?");
                         } else {
                           setInput(`Activate ${feature.name}`);
                         }
                       }}
                     >
                       <div className="flex items-center gap-3">
                         <div className="text-[#000000]">{feature.icon}</div>
                         <span className="text-sm font-bold text-[#000000]">
                           {feature.name}
                         </span>
                       </div>
                     </button>
                   ))}
                 </div>
               </div>
            ) : (
              <div className="max-w-4xl mx-auto space-y-8 pb-4">
                {messages.map((message) => (
                  <div key={message.id} className="w-full">
                    {message.from === "teacher" ? (
                      <div className="flex justify-center mb-4">
                        <div className="bg-[#FDE047] border-2 border-[#000000] rounded-lg px-4 py-2 shadow-[2px_2px_0px_0px_#000000] max-w-xl">
                          {/* Show image if present */}
                          {message.image && (
                            <div className="mb-2 flex flex-col items-center">
                              <img
                                src={message.image}
                                alt={message.imageName || "Uploaded image"}
                                className="max-h-64 w-auto max-w-full rounded-lg border-2 border-[#000000] object-contain"
                              />
                              <p className="text-xs text-center mt-1 opacity-70"> {message.imageName}</p>
                            </div>
                          )}
                          <p className="text-sm md:text-base font-medium text-[#000000] text-center">
                            {message.text}
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center gap-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-[#FDE047] border-2 border-[#000000] flex items-center justify-center shadow-[2px_2px_0px_0px_#000000]">
                            <svg
                              className="w-5 h-5 text-[#000000]"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                              />
                            </svg>
                          </div>
                          <span className="text-base font-bold text-[#000000]">
                            Chanakya
                          </span>
                          {message.from_cache && (
                            <span className="text-xs text-[#000000] opacity-70 border border-[#000000] rounded px-2 py-0.5">
                              From cache
                            </span>
                          )}
                          <button
                            onClick={() => {
                              if (speakingMessageId === message.id) {
                                stopSpeaking();
                              } else {
                                // Extract text for TTS
                                let textToSpeak = message.text;
                                if (message.data?.result) {
                                  if (message.data.result.explanation) {
                                    textToSpeak =
                                      message.data.result.explanation;
                                  } else if (
                                    message.data.result.activity_name
                                  ) {
                                    textToSpeak = `Activity: ${message.data.result.activity_name}. ${message.data.result.description}`;
                                  }
                                }
                                speakText(textToSpeak, message.id);
                              }
                            }}
                            className="p-1.5 border-2 border-[#000000] rounded bg-white hover:bg-[#FDE047] transition-all shadow-[2px_2px_0px_0px_#000000] hover:shadow-[1px_1px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5"
                            title={
                              speakingMessageId === message.id
                                ? "Stop speaking"
                                : "Listen to response"
                            }
                            aria-label="Voice output"
                          >
                            {speakingMessageId === message.id ? (
                              <svg
                                className="w-4 h-4 text-[#000000]"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"
                                />
                              </svg>
                            ) : (
                              <svg
                                className="w-4 h-4 text-[#000000]"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                                />
                              </svg>
                            )}
                          </button>
                        </div>
                        <div className="w-full px-1 py-1">
                          <ResponseFormatter
                            toolUsed={message.tool_used}
                            result={message.data?.result}
                            text={message.text}
                            resources={message.data?.resources}
                          />
                          {message.data?.result?.status === "select_topic" && message.data.result.topics && (
                            <div className="mt-4 flex flex-wrap gap-2 justify-start max-w-2xl px-1">
                              {message.data.result.topics.map((topicObj, idx) => (
                                <button
                                  key={idx}
                                  onClick={() => handleTopicSelect(
                                    message.data.result.class_name,
                                    message.data.result.subject,
                                    topicObj.topic_name
                                  )}
                                  className="px-3 py-1.5 bg-[#E8D5FF] hover:bg-[#d4c0f0] border-2 border-[#000000] rounded-lg font-bold text-xs shadow-[2px_2px_0px_0px_#000000] hover:shadow-[1px_1px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5 transition-all text-[#000000]"
                                >
                                  {topicObj.chapter_number ? `Ch ${topicObj.chapter_number}: ` : ""}{topicObj.topic_name}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-4 justify-start">
                    <div className="w-6 h-6 rounded-full bg-[#FDE047] border-2 border-[#000000] flex items-center justify-center flex-shrink-0">
                      <svg
                        className="w-3 h-3 text-[#000000] animate-spin"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                    </div>
                    <div className="bg-[#DDD6FE] border-2 border-[#000000] px-4 py-3 rounded-lg">
                      <div className="flex gap-1">
                        <span className="w-2 h-2 bg-[#000000] rounded-full animate-bounce" />
                        <span
                          className="w-2 h-2 bg-[#000000] rounded-full animate-bounce"
                          style={{ animationDelay: "0.2s" }}
                        />
                        <span
                          className="w-2 h-2 bg-[#000000] rounded-full animate-bounce"
                          style={{ animationDelay: "0.4s" }}
                        />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="flex-shrink-0 border-t-2 border-[#000000] bg-[#FFFFFF] px-4 py-2">
            <div className="max-w-5xl mx-auto">
              {/* Image Preview */}
              {imagePreview && (
                <div className="mb-2 relative inline-block">
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="h-20 w-auto rounded-lg border-2 border-[#000000] shadow-[2px_2px_0px_0px_#000000]"
                  />
                  <button
                    onClick={clearImage}
                    className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full border-2 border-[#000000] flex items-center justify-center hover:bg-red-600 transition-colors"
                    title="Remove image"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                  <span className="absolute bottom-1 left-1 text-xs bg-black bg-opacity-60 text-white px-1 rounded">
                    {selectedImage?.name?.slice(0, 15)}...
                  </span>
                </div>
              )}
              
              {/* Analysis mode selector - appears when image is selected */}
              {showAnalysisModes && (
                <div className="mb-3 p-3 border-2 border-[#000000] rounded-lg bg-[#F0F9FF] shadow-[2px_2px_0px_0px_#000000]">
                  <label className="text-sm font-bold text-[#000000] mb-2 block">
                    🔍 Analysis Mode:
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {[
                      { value: 'general', label: '📚 General', desc: 'All-purpose analysis' },
                      { value: 'ocr', label: '📝 Text Extraction', desc: 'Extract all text' },
                      { value: 'handwriting', label: '✍️ Handwriting', desc: 'Analyze student writing' },
                      { value: 'diagram', label: '📊 Diagram', desc: 'Explain charts/diagrams' },
                      { value: 'grading', label: '📋 Grade Work', desc: 'Grade student work' },
                    ].map((mode) => (
                      <button
                        key={mode.value}
                        onClick={() => setAnalysisMode(mode.value)}
                        className={`p-2 border-2 border-[#000000] rounded-lg text-xs font-bold transition-all shadow-[1px_1px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5 ${
                          analysisMode === mode.value
                            ? 'bg-[#A7F3D0] text-[#000000]'
                            : 'bg-white text-[#000000] hover:bg-[#FDE047]'
                        }`}
                        title={mode.desc}
                      >
                        <div className="text-center">
                          <div className="text-sm mb-1">{mode.label}</div>
                          <div className="text-xs opacity-70">{mode.desc}</div>
                        </div>
                      </button>
                    ))}
                  </div>
                  <p className="text-xs text-[#000000] opacity-60 mt-2 text-center">
                    Choose analysis type for better results
                  </p>
                </div>
              )}
              
              <div className="flex items-end gap-3 border-2 border-[#000000] rounded-lg px-3 py-3 bg-white shadow-[2px_2px_0px_0px_#000000]">
                <input
                  type="file"
                  ref={attachInputRef}
                  onChange={handleAttachChange}
                  accept="image/jpeg,image/png,image/gif,image/webp,.pdf,application/pdf"
                  className="hidden"
                />
                <button
                  onClick={() => attachInputRef.current?.click()}
                  disabled={isUploadingPdf}
                  className={`p-1.5 border-2 border-[#000000] rounded transition-all flex-shrink-0 ${
                    selectedImage || attachedDocumentId ? "bg-[#A7F3D0]" : "bg-white hover:bg-[#FDE047]"
                  } ${isUploadingPdf ? "opacity-60 cursor-not-allowed" : ""}`}
                  title={
                    isUploadingPdf
                      ? "Uploading..."
                      : selectedImage || attachedDocumentId
                        ? "Image or document attached"
                        : "Attach image or PDF"
                  }
                  aria-label="Attach image or PDF"
                >
                  {isUploadingPdf ? (
                    <svg className="w-4 h-4 text-[#000000] animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4 text-[#000000]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                    </svg>
                  )}
                </button>
                {/* Camera capture button */}
                <button
                  onClick={handleCameraCapture}
                  className={`p-1.5 border-2 border-[#000000] rounded transition-all flex-shrink-0 ${
                    selectedImage ? 'bg-[#A7F3D0]' : 'bg-white hover:bg-[#FDE047]'
                  }`}
                  title="Capture from camera"
                  aria-label="Capture from camera"
                >
                  <svg
                    className="w-4 h-4 text-[#000000]"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                </button>
                <button
                  onClick={() => {
                    if (isRecording) {
                      stopRecording();
                    } else if (!isProcessingVoice) {
                      startRecording();
                    }
                  }}
                  disabled={isProcessingVoice}
                  className={`p-1.5 border-2 border-[#000000] rounded transition-all flex-shrink-0 ${isRecording
                    ? "bg-red-500 hover:bg-red-600 animate-pulse"
                    : isProcessingVoice
                      ? "bg-gray-300 cursor-not-allowed"
                      : "bg-white hover:bg-[#FDE047]"
                    }`}
                  title={
                    isRecording
                      ? "Click to stop recording"
                      : "Click to record voice"
                  }
                  aria-label="Voice input"
                >
                  {isProcessingVoice ? (
                    <svg
                      className="w-4 h-4 text-[#000000] animate-spin"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                  ) : (
                    <svg
                      className="w-4 h-4 text-[#000000]"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                      />
                    </svg>
                  )}
                </button>
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={handleTextareaChange}
                  onKeyDown={handleKeyPress}
                  placeholder="Message Chanakya..."
                  rows={1}
                  className="flex-1 bg-transparent text-sm md:text-base text-[#000000] placeholder-gray-500 focus:outline-none resize-none overflow-y-auto"
                  style={{ minHeight: "20px", maxHeight: "128px" }}
                  aria-label="Message input"
                />
                <button
                  type="button"
                  onClick={sendMessage}
                  onMouseDown={(e) => e.preventDefault()}
                  disabled={!input.trim() || isLoading}
                  className="p-1.5 border-2 border-[#000000] rounded bg-[#FDE047] text-[#000000] font-bold hover:bg-[#FDE047] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-x-0 disabled:hover:translate-y-0 flex-shrink-0"
                  title="Send message"
                  aria-label="Send message"
                >
                  <svg
                    className="w-3 h-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                    />
                  </svg>
                </button>
              </div>

              {/* Controls Footer with Mode Selector and Quick Mode */}
              <div className="flex flex-wrap items-center justify-between gap-3 mt-2">
                <div className="flex flex-wrap items-center gap-3">
                  {/* Quick Answer Mode Toggle */}
                  <button
                    onClick={() => setQuickAnswerMode(!quickAnswerMode)}
                    className={`flex items-center gap-2 px-3 py-1.5 border-2 border-[#000000] rounded-lg font-bold text-sm transition-all shadow-[2px_2px_0px_0px_#000000] hover:shadow-[1px_1px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5 ${quickAnswerMode
                      ? "bg-[#A7F3D0] text-[#000000]"
                      : "bg-white text-[#000000]"
                      }`}
                    title={quickAnswerMode ? "Quick Answer Mode: ON" : "Quick Answer Mode: OFF"}
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 10V3L4 14h7v7l9-11h-7z"
                      />
                    </svg>
                    <span>Quick Mode</span>
                    {quickAnswerMode && (
                      <span className="text-xs bg-[#000000] text-white px-2 py-0.5 rounded-full">
                        ON
                      </span>
                    )}
                  </button>

                   {/* Chat Mode Selector Dropdown */}
                   {!lockedMode ? (
                     <div className="flex items-center gap-2">
                       <select
                         value={chatMode}
                         onChange={(e) => {
                           const mode = e.target.value;
                           setChatMode(mode);
                           if (mode === "module_builder") {
                             if (!input.trim()) {
                               setInput("Create a module for Class 7 Geography");
                             }
                           } else if (mode === "crisis_handler") {
                             setInput("A student is throwing tantrums in class. How should I respond?");
                           } else if (mode === "activity_generator") {
                             setInput("Generate a classroom activity for Class 8 Mathematics");
                           } else if (mode === "classroom_guidance") {
                             setInput("I just finished teaching algebra. Plan my next reflection and guidance.");
                           } else if (mode === "teacher_motivation") {
                             setInput("I am feeling a bit burned out today. Give me some encouragement.");
                           } else if (mode === "content_explainer") {
                             setInput("Explain the process of photosynthesis for class 6 students.");
                           } else if (mode === "expert_teacher") {
                             setInput("How do you teach quantum physics concepts to high schoolers?");
                           } else if (mode === "quick_answer") {
                             setInput("What is the capital of France?");
                           } else if (mode === "resource_finder") {
                             setInput("Find educational resources on Newtonian mechanics.");
                           } else if (mode === "feedback_response") {
                             setInput("The student did well but struggled with fractions.");
                           }
                         }}
                         className="px-3 py-1.5 border-2 border-[#000000] rounded-lg font-bold text-sm bg-white text-[#000000] transition-all shadow-[2px_2px_0px_0px_#000000] hover:shadow-[1px_1px_0px_0px_#000000] focus:outline-none cursor-pointer"
                         aria-label="Chat Mode"
                       >
                         <option value="general">💬 General Assistant</option>
                         <option value="module_builder">📚 Module Creator</option>
                         <option value="activity_generator">🪁 Activity Generator</option>
                         <option value="crisis_handler">🚨 Crisis Handler</option>
                         <option value="teacher_motivation">💪 Teacher Motivation</option>
                         <option value="content_explainer">📖 Content Explainer</option>
                         <option value="classroom_guidance">🏫 Classroom Guidance</option>
                         <option value="expert_teacher">🎓 Expert Teacher</option>
                         <option value="quick_answer">⚡ Quick Answer</option>
                         <option value="resource_finder">🔍 Resource Finder</option>
                         <option value="feedback_response">💬 Feedback Response</option>
                       </select>
                     </div>
                   ) : (
                     <div className="flex items-center gap-2 px-3 py-1.5 border-2 border-[#000000] rounded-lg font-bold text-sm bg-[#F3F4F6] text-[#000000] shadow-[2px_2px_0px_0px_#000000]">
                       <span>
                         {lockedMode === "module_builder" && "📚 Module Creator Locked"}
                         {lockedMode === "expert_teacher" && "🎓 Expert Q&A Locked"}
                         {lockedMode === "activity_generator" && "🪁 Activity Generator Locked"}
                         {lockedMode !== "module_builder" && lockedMode !== "expert_teacher" && lockedMode !== "activity_generator" && `🔒 ${lockedMode} Mode Locked`}
                       </span>
                     </div>
                   )}

                  {/* Reopen Preview Button */}
                  {!showArtifact && (activeArtifactLesson || activeArtifactAssignment) && (
                    <button
                      onClick={() => setShowArtifact(true)}
                      className="flex items-center gap-2 px-3 py-1.5 border-2 border-[#000000] rounded-lg font-bold text-sm bg-[#D4F1C5] text-[#000000] transition-all shadow-[2px_2px_0px_0px_#000000] hover:shadow-[1px_1px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5"
                      title="Open Preview Pane"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                        />
                      </svg>
                      <span>Open Preview</span>
                    </button>
                  )}
                </div>

                {quickAnswerMode && (
                  <span className="text-xs text-[#000000] opacity-70">
                    Fast, short answers
                  </span>
                )}
              </div>

              {/* <p className="text-xs text-[#000000] opacity-60 mt-1 text-center">
                Chanakya can make mistakes. Check important info.
              </p> */}
            </div>
          </div>
            </>
          )}
        </main>

        {/* Artifact Workspace Overlay */}
        {showArtifact && (
          <div
            className={`${
              isCollapsibleChatMinimized ? "flex-1" : "hidden md:flex md:flex-1"
            } flex flex-col bg-white border-l-0 md:border-l-2 border-[#000000] min-h-0`}
          >
            {/* Artifact Header */}
            <div className="p-4 border-b-2 border-[#000000] bg-[#F9F9FB] flex items-center justify-between flex-shrink-0">
              <div className="flex items-center gap-3">
                <span className="text-lg font-bold text-[#000000] flex items-center gap-2">
                  ✨ Module Artifact
                </span>
                <span className="text-xs bg-[#D4F1C5] border-2 border-[#000000] px-2 py-0.5 rounded font-bold text-[#000000]">
                  Active
                </span>
              </div>
              <div className="flex items-center gap-2">
                {/* Close Artifact Button */}
                <button
                  onClick={() => setShowArtifact(false)}
                  className="p-1.5 border-2 border-[#000000] rounded bg-white hover:bg-red-200 transition-all text-[#000000] shadow-[2px_2px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5"
                  title="Close Artifact Pane"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Neo-brutalist Tabs */}
            <div className="flex border-b-2 border-[#000000] bg-[#FFFFFF] flex-shrink-0">
              <button
                onClick={() => setActiveArtifactTab("lesson")}
                className={`flex-1 py-3 px-4 text-center font-bold text-sm border-r-2 border-[#000000] transition-all ${
                  activeArtifactTab === "lesson"
                    ? "bg-[#FDE047] text-[#000000]"
                    : "bg-white text-[#000000] hover:bg-gray-100"
                }`}
              >
                🖼️ Slides Preview
              </button>
              <button
                onClick={() => setActiveArtifactTab("assignment")}
                className={`flex-1 py-3 px-4 text-center font-bold text-sm border-r-2 border-[#000000] transition-all ${
                  activeArtifactTab === "assignment"
                    ? "bg-[#E8D5FF] text-[#000000]"
                    : "bg-white text-[#000000] hover:bg-gray-100"
                }`}
              >
                📝 Assessment
              </button>
              <button
                onClick={() => setActiveArtifactTab("export")}
                className={`flex-1 py-3 px-4 text-center font-bold text-sm transition-all ${
                  activeArtifactTab === "export"
                    ? "bg-[#F99DA8] text-[#000000]"
                    : "bg-white text-[#000000] hover:bg-gray-100"
                }`}
              >
                📥 Export Controls
              </button>
            </div>

            {/* Tab Contents - Scrollable */}
            <div className="flex-1 overflow-y-auto p-6 bg-[#FAFAFA]">
              {activeArtifactTab === "lesson" && (
                <LessonPreview lesson={activeArtifactLesson} />
              )}
              {activeArtifactTab === "assignment" && (
                <AssignmentPreview assignment={activeArtifactAssignment} />
              )}
              {activeArtifactTab === "export" && (
                <ExportControls lesson={activeArtifactLesson} assignment={activeArtifactAssignment} />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatInterface;
