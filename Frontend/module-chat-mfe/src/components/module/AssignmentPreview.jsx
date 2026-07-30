import { useState } from "react";

/**
 * AssignmentPreview - Displays questions grouped by difficulty
 * Shows question types with appropriate formatting, toggle answer visibility
 * Requirements: 5.2, 5.3
 */
function AssignmentPreview({ assignment }) {
  const [showAnswers, setShowAnswers] = useState(false);
  const [groupBy, setGroupBy] = useState("difficulty"); // "difficulty" or "type"
  const [expandedQuestions, setExpandedQuestions] = useState(new Set());

  if (!assignment || !assignment.questions || assignment.questions.length === 0) {
    return (
      <div className="bg-white border-2 border-[#000000] rounded-lg p-6 shadow-[4px_4px_0px_0px_#000000]">
        <p className="text-center text-gray-500">No assignment to display</p>
      </div>
    );
  }

  const toggleQuestion = (questionId) => {
    setExpandedQuestions((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(questionId)) {
        newSet.delete(questionId);
      } else {
        newSet.add(questionId);
      }
      return newSet;
    });
  };

  const getDifficultyColor = (difficulty) => {
    const colors = {
      easy: "#D4F1C5",
      medium: "#FDE047",
      hard: "#F99DA8",
    };
    return colors[difficulty] || "#FFFFFF";
  };

  const getDifficultyLabel = (difficulty) => {
    const labels = {
      easy: "Easy",
      medium: "Medium",
      hard: "Hard",
    };
    return labels[difficulty] || difficulty;
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case "mcq":
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case "short_answer":
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
              d="M4 6h16M4 12h8m-8 6h16" />
          </svg>
        );
      case "long_answer":
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        );
      default:
        return null;
    }
  };

  const getTypeLabel = (type) => {
    const labels = {
      mcq: "Multiple Choice",
      short_answer: "Short Answer",
      long_answer: "Long Answer",
    };
    return labels[type] || type;
  };

  // Group questions
  const groupedQuestions = groupBy === "difficulty" 
    ? groupByDifficulty(assignment.questions)
    : groupByType(assignment.questions);

  return (
    <div className="bg-white border-2 border-[#000000] rounded-lg shadow-[4px_4px_0px_0px_#000000] overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b-2 border-[#000000] bg-[#E8D5FF]">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-xl font-bold text-[#000000] flex items-center gap-2">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              Assignment
            </h2>
            <p className="text-sm text-[#000000] opacity-70">
              {assignment.questions.length} questions • {assignment.total_marks} marks
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* Group By Toggle */}
            <div className="flex items-center border-2 border-[#000000] rounded-lg overflow-hidden">
              <button
                onClick={() => setGroupBy("difficulty")}
                className={`px-3 py-1.5 text-sm font-bold transition-all ${
                  groupBy === "difficulty" 
                    ? "bg-[#000000] text-white" 
                    : "bg-white text-[#000000] hover:bg-gray-100"
                }`}
              >
                By Difficulty
              </button>
              <button
                onClick={() => setGroupBy("type")}
                className={`px-3 py-1.5 text-sm font-bold transition-all ${
                  groupBy === "type" 
                    ? "bg-[#000000] text-white" 
                    : "bg-white text-[#000000] hover:bg-gray-100"
                }`}
              >
                By Type
              </button>
            </div>

            {/* Show Answers Toggle */}
            <button
              onClick={() => setShowAnswers(!showAnswers)}
              className={`flex items-center gap-2 px-4 py-2 border-2 border-[#000000] rounded-lg font-bold transition-all shadow-[2px_2px_0px_0px_#000000] hover:shadow-[1px_1px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5 ${
                showAnswers ? "bg-[#D4F1C5]" : "bg-white"
              }`}
            >
              {showAnswers ? (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                  Hide Answers
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  Show Answers
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Questions */}
      <div className="p-6 space-y-6">
        {Object.entries(groupedQuestions).map(([group, questions]) => (
          <div key={group}>
            {/* Group Header */}
            <div 
              className="flex items-center gap-2 mb-4 pb-2 border-b-2 border-[#000000]"
              style={{ 
                borderColor: groupBy === "difficulty" 
                  ? getDifficultyColor(group) 
                  : "#000000" 
              }}
            >
              {groupBy === "difficulty" ? (
                <span 
                  className="px-3 py-1 text-sm font-bold border-2 border-[#000000] rounded-full"
                  style={{ backgroundColor: getDifficultyColor(group) }}
                >
                  {getDifficultyLabel(group)}
                </span>
              ) : (
                <span className="flex items-center gap-2 px-3 py-1 text-sm font-bold border-2 border-[#000000] rounded-full bg-white">
                  {getTypeIcon(group)}
                  {getTypeLabel(group)}
                </span>
              )}
              <span className="text-sm text-[#000000] opacity-70">
                ({questions.length} questions)
              </span>
            </div>

            {/* Questions List */}
            <div className="space-y-4">
              {questions.map((question, idx) => (
                <QuestionCard
                  key={`${group}-${idx}`}
                  question={question}
                  index={idx + 1}
                  showAnswers={showAnswers}
                  isExpanded={expandedQuestions.has(`${group}-${idx}`)}
                  onToggle={() => toggleQuestion(`${group}-${idx}`)}
                  getDifficultyColor={getDifficultyColor}
                  getDifficultyLabel={getDifficultyLabel}
                  getTypeIcon={getTypeIcon}
                  getTypeLabel={getTypeLabel}
                  groupBy={groupBy}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function QuestionCard({ 
  question, index, showAnswers, isExpanded, onToggle,
  getDifficultyColor, getDifficultyLabel, getTypeIcon, getTypeLabel, groupBy
}) {
  return (
    <div className="border-2 border-[#000000] rounded-lg overflow-hidden">
      {/* Question Header */}
      <button
        onClick={onToggle}
        className="w-full p-4 bg-white hover:bg-gray-50 transition-all text-left"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className="font-bold text-[#000000]">Q{index}.</span>
              {groupBy === "difficulty" && (
                <span className="flex items-center gap-1 px-2 py-0.5 text-xs font-medium border border-[#000000] rounded bg-white">
                  {getTypeIcon(question.question_type)}
                  {getTypeLabel(question.question_type)}
                </span>
              )}
              {groupBy === "type" && (
                <span 
                  className="px-2 py-0.5 text-xs font-medium border border-[#000000] rounded"
                  style={{ backgroundColor: getDifficultyColor(question.difficulty) }}
                >
                  {getDifficultyLabel(question.difficulty)}
                </span>
              )}
              <span className="px-2 py-0.5 text-xs font-medium border border-[#000000] rounded bg-[#E0EEEF]">
                {question.marks} {question.marks === 1 ? "mark" : "marks"}
              </span>
            </div>
            <p className="text-[#000000] font-medium">{question.question_text}</p>
          </div>
          <svg 
            className={`w-5 h-5 text-[#000000] transition-transform ${isExpanded ? "rotate-180" : ""}`} 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t-2 border-[#000000] p-4 bg-gray-50">
          {/* MCQ Options */}
          {question.question_type === "mcq" && question.options && (
            <div className="space-y-2 mb-4">
              {question.options.map((option, idx) => (
                <div 
                  key={idx}
                  className={`flex items-center gap-3 p-3 border-2 border-[#000000] rounded-lg transition-all ${
                    showAnswers && option.is_correct 
                      ? "bg-[#D4F1C5]" 
                      : "bg-white"
                  }`}
                >
                  <span className="w-6 h-6 flex items-center justify-center border-2 border-[#000000] rounded-full text-sm font-bold bg-white">
                    {String.fromCharCode(65 + idx)}
                  </span>
                  <span className="flex-1 text-[#000000]">{option.option_text}</span>
                  {showAnswers && option.is_correct && (
                    <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Answer Section */}
          {showAnswers && (
            <div className="space-y-3">
              {/* Expected Answer */}
              {question.expected_answer && (
                <div className="p-3 bg-[#D4F1C5] border-2 border-[#000000] rounded-lg">
                  <h5 className="font-bold text-[#000000] mb-1 flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Expected Answer
                  </h5>
                  <p className="text-[#000000]">{question.expected_answer}</p>
                </div>
              )}

              {/* Marking Scheme */}
              {question.marking_scheme && question.marking_scheme.length > 0 && (
                <div className="p-3 bg-[#E0EEEF] border-2 border-[#000000] rounded-lg">
                  <h5 className="font-bold text-[#000000] mb-2 flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                    </svg>
                    Marking Scheme
                  </h5>
                  <ul className="space-y-1">
                    {question.marking_scheme.map((point, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-[#000000]">
                        <span className="w-1.5 h-1.5 mt-1.5 bg-[#000000] rounded-full flex-shrink-0" />
                        <span>{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Source Reference */}
              {question.source_reference && (
                <p className="text-xs text-gray-500 italic">
                  Source: {question.source_reference}
                </p>
              )}
            </div>
          )}

          {!showAnswers && (
            <p className="text-sm text-gray-500 italic">
              Click "Show Answers" to reveal the answer
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// Helper functions
function groupByDifficulty(questions) {
  const groups = { easy: [], medium: [], hard: [] };
  questions.forEach((q) => {
    if (groups[q.difficulty]) {
      groups[q.difficulty].push(q);
    }
  });
  // Remove empty groups
  return Object.fromEntries(
    Object.entries(groups).filter(([_, qs]) => qs.length > 0)
  );
}

function groupByType(questions) {
  const groups = { mcq: [], short_answer: [], long_answer: [] };
  questions.forEach((q) => {
    if (groups[q.question_type]) {
      groups[q.question_type].push(q);
    }
  });
  // Remove empty groups
  return Object.fromEntries(
    Object.entries(groups).filter(([_, qs]) => qs.length > 0)
  );
}

export default AssignmentPreview;
