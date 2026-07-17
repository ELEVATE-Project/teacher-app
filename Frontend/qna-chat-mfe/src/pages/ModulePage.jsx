import { useState, useCallback, useEffect } from "react";
import { moduleAPI } from "../utils/moduleApi";
import TopicSelector from "../components/module/TopicSelector";
import LessonPreview from "../components/module/LessonPreview";
import AssignmentPreview from "../components/module/AssignmentPreview";
import ExportControls from "../components/module/ExportControls";

/**
 * ModulePage - Main container for the MODULE lesson builder feature
 * Wires together all components and manages state for generation flow
 * Requirements: All
 */
function ModulePage() {
  
  // View mode state: "create" for new lesson, "saved" for viewing saved lessons
  const [viewMode, setViewMode] = useState("create");
  
  // Selection state
  const [selection, setSelection] = useState(null);
  
  // Generation state
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState("");
  const [error, setError] = useState(null);
  
  // Result state
  const [lesson, setLesson] = useState(null);
  const [assignment, setAssignment] = useState(null);
  const [validationReport, setValidationReport] = useState(null);
  
  // View state
  const [activeTab, setActiveTab] = useState("lesson"); // "lesson" or "assignment"
  
  // Saved lessons state
  const [savedLessons, setSavedLessons] = useState([]);
  const [loadingSavedLessons, setLoadingSavedLessons] = useState(false);
  const [loadingLesson, setLoadingLesson] = useState(false);

  // Fetch saved lessons when switching to saved view
  useEffect(() => {
    if (viewMode === "saved") {
      fetchSavedLessons();
    }
  }, [viewMode]);

  const fetchSavedLessons = async () => {
    setLoadingSavedLessons(true);
    setError(null);
    try {
      const response = await moduleAPI.getLessons();
      setSavedLessons(response.data.lessons || []);
    } catch (err) {
      console.error("Error fetching saved lessons:", err);
      setError("Failed to load saved lessons. Please try again.");
    } finally {
      setLoadingSavedLessons(false);
    }
  };

  const handleLoadLesson = async (lessonId) => {
    setLoadingLesson(true);
    setError(null);
    try {
      const response = await moduleAPI.getLesson(lessonId);
      setLesson(response.data.lesson);
      setAssignment(response.data.assignment);
      setValidationReport(null);
      setViewMode("create");
      setActiveTab("lesson");
    } catch (err) {
      console.error("Error loading lesson:", err);
      setError("Failed to load lesson. Please try again.");
    } finally {
      setLoadingLesson(false);
    }
  };

  const handleDeleteLesson = async (lessonId) => {
    if (!window.confirm("Are you sure you want to delete this lesson?")) {
      return;
    }
    try {
      await moduleAPI.deleteLesson(lessonId);
      setSavedLessons((prev) => prev.filter((l) => l.id !== lessonId));
    } catch (err) {
      console.error("Error deleting lesson:", err);
      setError("Failed to delete lesson. Please try again.");
    }
  };

  const handleSelectionComplete = useCallback((newSelection) => {
    setSelection(newSelection);
    // Clear previous results when selection changes
    setLesson(null);
    setAssignment(null);
    setValidationReport(null);
    setError(null);
  }, []);

  const handleGenerate = async () => {
    if (!selection) {
      setError("Please select a class, subject, and topic first.");
      return;
    }

    setIsGenerating(true);
    setError(null);
    setGenerationProgress("Retrieving textbook content...");

    try {
      setGenerationProgress("Generating lesson slides...");
      
      const response = await moduleAPI.generateLesson({
        class_name: selection.className,
        subject: selection.subject,
        topic: selection.topic,
      });

      const data = response.data;
      
      setLesson(data.lesson);
      setAssignment(data.assignment);
      setValidationReport(data.validation_report);
      setActiveTab("lesson");
      setGenerationProgress("");
    } catch (err) {
      console.error("Generation error:", err);
      if (err.response?.status === 404) {
        setError("No content found for the selected topic. Please try a different topic.");
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Failed to generate lesson. Please try again.");
      }
    } finally {
      setIsGenerating(false);
      setGenerationProgress("");
    }
  };

  const handleReset = () => {
    setSelection(null);
    setLesson(null);
    setAssignment(null);
    setValidationReport(null);
    setError(null);
    setActiveTab("lesson");
  };

  const hasResults = lesson || assignment;

  return (
    <div className="min-h-screen bg-[#FFFFFF] relative">
      {/* Background */}
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

      <div className="relative z-10 max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-[#000000] mb-2">
                MODULE - Lesson Builder
              </h1>
              <p className="text-[#000000] opacity-70">
                Generate structured 8-slide lessons and assignments from textbook content
              </p>
            </div>
            
            {/* View Mode Toggle */}
            <div className="flex items-center border-2 border-[#000000] rounded-lg overflow-hidden shadow-[2px_2px_0px_0px_#000000]">
              <button
                onClick={() => setViewMode("create")}
                className={`px-4 py-2 font-bold transition-all flex items-center gap-2 ${
                  viewMode === "create"
                    ? "bg-[#FDE047] text-[#000000]"
                    : "bg-white text-[#000000] hover:bg-gray-100"
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M12 4v16m8-8H4" />
                </svg>
                Create New
              </button>
              <button
                onClick={() => setViewMode("saved")}
                className={`px-4 py-2 font-bold transition-all flex items-center gap-2 border-l-2 border-[#000000] ${
                  viewMode === "saved"
                    ? "bg-[#E8D5FF] text-[#000000]"
                    : "bg-white text-[#000000] hover:bg-gray-100"
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                </svg>
                Saved Lessons
              </button>
            </div>
          </div>
        </div>

        {/* Main Content - Conditional based on view mode */}
        {viewMode === "saved" ? (
          <SavedLessonsView
            lessons={savedLessons}
            loading={loadingSavedLessons}
            loadingLesson={loadingLesson}
            error={error}
            onLoadLesson={handleLoadLesson}
            onDeleteLesson={handleDeleteLesson}
            onCreateNew={() => setViewMode("create")}
          />
        ) : (
          <CreateLessonView
            selection={selection}
            isGenerating={isGenerating}
            generationProgress={generationProgress}
            error={error}
            lesson={lesson}
            assignment={assignment}
            validationReport={validationReport}
            activeTab={activeTab}
            hasResults={hasResults}
            onSelectionComplete={handleSelectionComplete}
            onGenerate={handleGenerate}
            onReset={handleReset}
            setActiveTab={setActiveTab}
          />
        )}
      </div>
    </div>
  );
}

function ValidationReportCard({ report }) {
  if (!report) return null;

  const scoreColor = report.overall_score >= 0.8 
    ? "#D4F1C5" 
    : report.overall_score >= 0.6 
      ? "#FDE047" 
      : "#F99DA8";

  return (
    <div className="bg-white border-2 border-[#000000] rounded-lg p-4 shadow-[2px_2px_0px_0px_#000000]">
      <h3 className="font-bold text-[#000000] mb-3 flex items-center gap-2">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Validation Report
      </h3>
      
      {/* Score */}
      <div className="flex items-center gap-3 mb-3">
        <div 
          className="px-3 py-1 border-2 border-[#000000] rounded-full font-bold"
          style={{ backgroundColor: scoreColor }}
        >
          {Math.round(report.overall_score * 100)}% Grounded
        </div>
        <span className={`text-sm font-medium ${report.is_valid ? "text-green-600" : "text-red-600"}`}>
          {report.is_valid ? "✓ Valid" : "⚠ Needs Review"}
        </span>
      </div>

      {/* Issues */}
      {report.issues && report.issues.length > 0 && (
        <div className="mb-3">
          <p className="text-sm font-medium text-[#000000] mb-1">Issues:</p>
          <ul className="text-sm text-[#000000] opacity-70 space-y-1">
            {report.issues.map((issue, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-red-500">•</span>
                <span>{issue}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {report.recommendations && report.recommendations.length > 0 && (
        <div>
          <p className="text-sm font-medium text-[#000000] mb-1">Recommendations:</p>
          <ul className="text-sm text-[#000000] opacity-70 space-y-1">
            {report.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-blue-500">→</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function CreateLessonView({
  selection,
  isGenerating,
  generationProgress,
  error,
  lesson,
  assignment,
  validationReport,
  activeTab,
  hasResults,
  onSelectionComplete,
  onGenerate,
  onReset,
  setActiveTab,
}) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left Column - Controls */}
      <div className="lg:col-span-1 space-y-6">
        {/* Topic Selector */}
        <TopicSelector 
          onSelectionComplete={onSelectionComplete}
          disabled={isGenerating}
        />

        {/* Generate Button */}
        <button
          onClick={onGenerate}
          disabled={!selection || isGenerating}
          className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-[#D4F1C5] border-2 border-[#000000] rounded-lg font-bold text-lg transition-all shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-[4px_4px_0px_0px_#000000] disabled:hover:translate-x-0 disabled:hover:translate-y-0"
        >
          {isGenerating ? (
            <>
              <svg className="w-6 h-6 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span>{generationProgress || "Generating..."}</span>
            </>
          ) : (
            <>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>Generate Lesson</span>
            </>
          )}
        </button>

        {/* Error Display */}
        {error && (
          <div className="p-4 bg-[#F99DA8] border-2 border-[#000000] rounded-lg">
            <p className="text-[#000000] font-medium">{error}</p>
          </div>
        )}

        {/* Export Controls */}
        {hasResults && (
          <ExportControls lesson={lesson} assignment={assignment} />
        )}

        {/* Validation Report */}
        {validationReport && (
          <ValidationReportCard report={validationReport} />
        )}

        {/* Reset Button */}
        {hasResults && (
          <button
            onClick={onReset}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-white border-2 border-[#000000] rounded-lg font-bold transition-all shadow-[2px_2px_0px_0px_#000000] hover:shadow-[1px_1px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Start New Lesson
          </button>
        )}
      </div>

      {/* Right Column - Preview */}
      <div className="lg:col-span-2">
        {hasResults ? (
          <div className="space-y-6">
            {/* Tab Navigation */}
            <div className="flex border-2 border-[#000000] rounded-lg overflow-hidden">
              <button
                onClick={() => setActiveTab("lesson")}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 font-bold transition-all ${
                  activeTab === "lesson"
                    ? "bg-[#FDE047] text-[#000000]"
                    : "bg-white text-[#000000] hover:bg-gray-100"
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                Lesson ({lesson?.slides?.length || 0} slides)
              </button>
              <button
                onClick={() => setActiveTab("assignment")}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 font-bold transition-all border-l-2 border-[#000000] ${
                  activeTab === "assignment"
                    ? "bg-[#E8D5FF] text-[#000000]"
                    : "bg-white text-[#000000] hover:bg-gray-100"
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                Assignment ({assignment?.questions?.length || 0} questions)
              </button>
            </div>

            {/* Content */}
            {activeTab === "lesson" ? (
              <LessonPreview lesson={lesson} />
            ) : (
              <AssignmentPreview assignment={assignment} />
            )}
          </div>
        ) : (
          <EmptyState isGenerating={isGenerating} />
        )}
      </div>
    </div>
  );
}

function SavedLessonsView({ lessons, loading, loadingLesson, error, onLoadLesson, onDeleteLesson, onCreateNew }) {
  if (loading) {
    return (
      <div className="bg-white border-2 border-[#000000] rounded-lg p-12 shadow-[4px_4px_0px_0px_#000000]">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-[#E8D5FF] border-2 border-[#000000] rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 animate-spin text-[#000000]" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </div>
          <p className="text-[#000000] font-medium">Loading saved lessons...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border-2 border-[#000000] rounded-lg p-12 shadow-[4px_4px_0px_0px_#000000]">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-[#F99DA8] border-2 border-[#000000] rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-[#000000]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-[#000000] font-medium mb-4">{error}</p>
          <button
            onClick={onCreateNew}
            className="px-4 py-2 bg-[#FDE047] border-2 border-[#000000] rounded-lg font-bold shadow-[2px_2px_0px_0px_#000000] hover:shadow-[1px_1px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5 transition-all"
          >
            Create New Lesson
          </button>
        </div>
      </div>
    );
  }

  if (lessons.length === 0) {
    return (
      <div className="bg-white border-2 border-[#000000] rounded-lg p-12 shadow-[4px_4px_0px_0px_#000000]">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-[#E0EEEF] border-2 border-[#000000] rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-[#000000]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-[#000000] mb-2">No Saved Lessons</h3>
          <p className="text-[#000000] opacity-70 mb-6">
            You haven't created any lessons yet. Start by creating your first lesson!
          </p>
          <button
            onClick={onCreateNew}
            className="px-6 py-3 bg-[#D4F1C5] border-2 border-[#000000] rounded-lg font-bold shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5 transition-all"
          >
            Create Your First Lesson
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {lessons.map((lesson) => (
        <SavedLessonCard
          key={lesson.id}
          lesson={lesson}
          loading={loadingLesson}
          onLoad={() => onLoadLesson(lesson.id)}
          onDelete={() => onDeleteLesson(lesson.id)}
        />
      ))}
    </div>
  );
}

function SavedLessonCard({ lesson, loading, onLoad, onDelete }) {
  const scoreColor = lesson.validation_score >= 0.8 
    ? "#D4F1C5" 
    : lesson.validation_score >= 0.6 
      ? "#FDE047" 
      : "#F99DA8";

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="bg-white border-2 border-[#000000] rounded-lg overflow-hidden shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5 transition-all">
      {/* Header */}
      <div className="p-4 bg-[#FDE047] border-b-2 border-[#000000]">
        <h3 className="font-bold text-[#000000] text-lg line-clamp-1">{lesson.topic}</h3>
        <p className="text-sm text-[#000000] opacity-70">
          {lesson.class_name?.replace("_", " ")} • {lesson.subject?.replace(/_/g, " ")}
        </p>
      </div>

      {/* Body */}
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm text-[#000000] opacity-70">
            {formatDate(lesson.created_at)}
          </span>
          <span 
            className="px-2 py-1 text-xs font-bold border border-[#000000] rounded-full"
            style={{ backgroundColor: scoreColor }}
          >
            {Math.round(lesson.validation_score * 100)}%
          </span>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={onLoad}
            disabled={loading}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-[#E8D5FF] border-2 border-[#000000] rounded-lg font-bold text-sm transition-all hover:bg-[#d4c0f0] disabled:opacity-50"
          >
            {loading ? (
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            )}
            View
          </button>
          <button
            onClick={onDelete}
            className="px-3 py-2 bg-[#F99DA8] border-2 border-[#000000] rounded-lg font-bold text-sm transition-all hover:bg-[#f08090]"
            title="Delete lesson"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

function EmptyState({ isGenerating }) {
  return (
    <div className="bg-white border-2 border-[#000000] rounded-lg p-12 shadow-[4px_4px_0px_0px_#000000]">
      <div className="text-center">
        {isGenerating ? (
          <>
            <div className="w-24 h-24 mx-auto mb-6 bg-[#FDE047] border-2 border-[#000000] rounded-full flex items-center justify-center">
              <svg className="w-12 h-12 animate-spin text-[#000000]" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-[#000000] mb-2">
              Generating Your Lesson...
            </h3>
            <p className="text-[#000000] opacity-70">
              This may take a minute. We're creating slides, diagrams, and questions.
            </p>
          </>
        ) : (
          <>
            <div className="w-24 h-24 mx-auto mb-6 bg-[#E0EEEF] border-2 border-[#000000] rounded-full flex items-center justify-center">
              <svg className="w-12 h-12 text-[#000000]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-[#000000] mb-2">
              Ready to Create Your Lesson
            </h3>
            <p className="text-[#000000] opacity-70 mb-6">
              Select a class, subject, and topic from the left panel, then click "Generate Lesson" to create your teaching materials.
            </p>
            <div className="flex flex-wrap justify-center gap-4 text-sm">
              <div className="flex items-center gap-2 px-3 py-2 bg-[#FDE047] border-2 border-[#000000] rounded-lg">
                <span className="font-bold">8</span>
                <span>Slides</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-2 bg-[#E8D5FF] border-2 border-[#000000] rounded-lg">
                <span className="font-bold">9+</span>
                <span>Questions</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-2 bg-[#D4F1C5] border-2 border-[#000000] rounded-lg">
                <span className="font-bold">3</span>
                <span>Export Formats</span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default ModulePage;
