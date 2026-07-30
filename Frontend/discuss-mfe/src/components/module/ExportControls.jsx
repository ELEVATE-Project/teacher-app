import { useState } from "react";
import { moduleAPI } from "../../utils/moduleApi";

/**
 * ExportControls - Export buttons for lessons and assignments
 * Supports PDF, DOC, PPT for lessons and PDF, DOC for assignments
 * Requirements: 6.1, 6.2, 6.3, 6.5
 * 
 * Note: Assignment export uses lesson.id because the API endpoint
 * /api/module/assignments/{lesson_id}/export/* expects the lesson_id
 */
function ExportControls({ lesson, assignment }) {
  const [exportingLesson, setExportingLesson] = useState(null);
  const [exportingAssignment, setExportingAssignment] = useState(null);
  const [includeAnswers, setIncludeAnswers] = useState(false);
  const [error, setError] = useState(null);

  const downloadBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const getFilename = (type, format) => {
    const topic = lesson?.topic || assignment?.topic || "export";
    const sanitized = topic.replace(/[^a-zA-Z0-9]/g, "_").substring(0, 30);
    const timestamp = new Date().toISOString().split("T")[0];
    return `${sanitized}_${type}_${timestamp}.${format}`;
  };

  const handleLessonExport = async (format) => {
    if (!lesson?.id) {
      setError("No lesson available to export");
      return;
    }

    setExportingLesson(format);
    setError(null);

    try {
      let response;
      let extension;

      switch (format) {
        case "pdf":
          response = await moduleAPI.exportLessonPdf(lesson.id);
          extension = "pdf";
          break;
        case "doc":
          response = await moduleAPI.exportLessonDoc(lesson.id);
          extension = "docx";
          break;
        case "ppt":
          response = await moduleAPI.exportLessonPpt(lesson.id);
          extension = "pptx";
          break;
        default:
          throw new Error("Unsupported format");
      }

      downloadBlob(response.data, getFilename("lesson", extension));
    } catch (err) {
      console.error("Export error:", err);
      setError(`Failed to export lesson as ${format.toUpperCase()}. Please try again.`);
    } finally {
      setExportingLesson(null);
    }
  };

  const handleAssignmentExport = async (format) => {
    // Use lesson.id for export because the API expects lesson_id, not assignment_id
    const exportId = lesson?.id || assignment?.lesson_id;
    
    if (!exportId) {
      setError("No assignment available to export");
      return;
    }

    setExportingAssignment(format);
    setError(null);

    try {
      let response;
      let extension;

      switch (format) {
        case "pdf":
          response = await moduleAPI.exportAssignmentPdf(exportId, includeAnswers);
          extension = "pdf";
          break;
        case "doc":
          response = await moduleAPI.exportAssignmentDoc(exportId, includeAnswers);
          extension = "docx";
          break;
        default:
          throw new Error("Unsupported format");
      }

      const suffix = includeAnswers ? "_with_answers" : "";
      downloadBlob(response.data, getFilename(`assignment${suffix}`, extension));
    } catch (err) {
      console.error("Export error:", err);
      setError(`Failed to export assignment as ${format.toUpperCase()}. Please try again.`);
    } finally {
      setExportingAssignment(null);
    }
  };

  const hasLesson = lesson?.id;
  const hasAssignment = assignment?.id || (assignment && lesson?.id);

  if (!hasLesson && !hasAssignment) {
    return null;
  }

  return (
    <div className="bg-white border-2 border-[#000000] rounded-lg p-6 shadow-[4px_4px_0px_0px_#000000]">
      <h2 className="text-xl font-bold text-[#000000] mb-4 flex items-center gap-2">
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        Export
      </h2>

      {error && (
        <div className="mb-4 p-3 bg-[#F99DA8] border-2 border-[#000000] rounded-lg text-sm text-[#000000]">
          {error}
        </div>
      )}

      <div className="space-y-6">
        {/* Lesson Export */}
        {hasLesson && (
          <div>
            <h3 className="font-bold text-[#000000] mb-3 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              Lesson
            </h3>
            <div className="flex flex-wrap gap-3">
              <ExportButton
                format="PDF"
                icon={<PdfIcon />}
                color="#F99DA8"
                onClick={() => handleLessonExport("pdf")}
                isLoading={exportingLesson === "pdf"}
                disabled={!!exportingLesson}
              />
              <ExportButton
                format="DOC"
                icon={<DocIcon />}
                color="#E0EEEF"
                onClick={() => handleLessonExport("doc")}
                isLoading={exportingLesson === "doc"}
                disabled={!!exportingLesson}
              />
              <ExportButton
                format="PPT"
                icon={<PptIcon />}
                color="#FDE047"
                onClick={() => handleLessonExport("ppt")}
                isLoading={exportingLesson === "ppt"}
                disabled={!!exportingLesson}
              />
            </div>
          </div>
        )}

        {/* Assignment Export */}
        {hasAssignment && (
          <div>
            <h3 className="font-bold text-[#000000] mb-3 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              Assignment
            </h3>
            
            {/* Include Answers Toggle */}
            <label className="flex items-center gap-2 mb-3 cursor-pointer">
              <input
                type="checkbox"
                checked={includeAnswers}
                onChange={(e) => setIncludeAnswers(e.target.checked)}
                className="w-4 h-4 border-2 border-[#000000] rounded accent-[#D4F1C5]"
              />
              <span className="text-sm font-medium text-[#000000]">
                Include answer key
              </span>
            </label>

            <div className="flex flex-wrap gap-3">
              <ExportButton
                format="PDF"
                icon={<PdfIcon />}
                color="#F99DA8"
                onClick={() => handleAssignmentExport("pdf")}
                isLoading={exportingAssignment === "pdf"}
                disabled={!!exportingAssignment}
              />
              <ExportButton
                format="DOC"
                icon={<DocIcon />}
                color="#E0EEEF"
                onClick={() => handleAssignmentExport("doc")}
                isLoading={exportingAssignment === "doc"}
                disabled={!!exportingAssignment}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ExportButton({ format, icon, color, onClick, isLoading, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`flex items-center gap-2 px-4 py-2 border-2 border-[#000000] rounded-lg font-bold transition-all shadow-[2px_2px_0px_0px_#000000] hover:shadow-[1px_1px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-[2px_2px_0px_0px_#000000] disabled:hover:translate-x-0 disabled:hover:translate-y-0`}
      style={{ backgroundColor: color }}
    >
      {isLoading ? (
        <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      ) : (
        icon
      )}
      <span>{isLoading ? "Exporting..." : format}</span>
    </button>
  );
}

// Icon Components
function PdfIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
        d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
        d="M9 13h6m-6 4h4" />
    </svg>
  );
}

function DocIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );
}

function PptIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
        d="M8 13v-1m4 1v-3m4 3V8M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
    </svg>
  );
}

export default ExportControls;
