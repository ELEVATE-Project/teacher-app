import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { classesApi, questionsApi, sessionsApi } from "../utils/classroomApi";

function QuestionSetup() {
  const { classId } = useParams();
  const navigate = useNavigate();

  const [classInfo, setClassInfo] = useState(null);
  const [topic, setTopic] = useState("");
  const [questions, setQuestions] = useState({
    easy: [],
    medium: [],
    hard: [],
  });
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);

  // Question generation counts
  const [questionCounts, setQuestionCounts] = useState({
    easy: 3,
    medium: 3,
    hard: 3,
  });

  // Add question form
  const [newQuestionText, setNewQuestionText] = useState("");
  const [newQuestionDifficulty, setNewQuestionDifficulty] = useState("medium");

  useEffect(() => {
    loadClassInfo();
  }, [classId]);

  const loadClassInfo = async () => {
    try {
      const data = await classesApi.get(classId);
      setClassInfo(data);
    } catch (error) {
      console.error("Failed to load class:", error);
      alert("Failed to load class. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const loadQuestionsForTopic = async (topicName) => {
    try {
      const data = await questionsApi.getByTopic(topicName);
      setQuestions(data);
    } catch (error) {
      console.error("Failed to load questions:", error);
      setQuestions({ easy: [], medium: [], hard: [] });
    }
  };

  const updateQuestionCount = (difficulty, delta) => {
    setQuestionCounts((prev) => ({
      ...prev,
      [difficulty]: Math.max(0, Math.min(10, prev[difficulty] + delta)),
    }));
  };

  const handleGenerateQuestions = async () => {
    if (!topic.trim() || !classInfo) return;

    setGenerating(true);
    try {
      const data = await questionsApi.generate({
        topic: topic.trim(),
        subject: classInfo.subject,
        easy_count: questionCounts.easy,
        medium_count: questionCounts.medium,
        hard_count: questionCounts.hard,
      });
      setQuestions(data);
    } catch (error) {
      console.error("Failed to generate questions:", error);
      alert(
        "Failed to generate questions. Make sure the backend is running and AI is configured."
      );
      // Still try to load any existing questions
      await loadQuestionsForTopic(topic.trim());
    } finally {
      setGenerating(false);
    }
  };

  const handleAddQuestion = async (e) => {
    e.preventDefault();
    if (!newQuestionText.trim() || !topic.trim()) return;

    try {
      const newQuestion = await questionsApi.create({
        topic: topic.trim(),
        difficulty: newQuestionDifficulty,
        text: newQuestionText.trim(),
      });

      setQuestions((prev) => ({
        ...prev,
        [newQuestionDifficulty]: [...prev[newQuestionDifficulty], newQuestion],
      }));

      setNewQuestionText("");
      setShowAddForm(false);
    } catch (error) {
      console.error("Failed to add question:", error);
      alert("Failed to add question. Make sure the backend is running.");
    }
  };

  const handleUpdateQuestion = async (e) => {
    e.preventDefault();
    if (!editingQuestion || !newQuestionText.trim()) return;

    try {
      const updated = await questionsApi.update(editingQuestion.id, {
        topic: topic.trim(),
        difficulty: newQuestionDifficulty,
        text: newQuestionText.trim(),
      });

      // Remove from old difficulty, add to new
      setQuestions((prev) => {
        const newQuestions = { ...prev };
        Object.keys(newQuestions).forEach((diff) => {
          newQuestions[diff] = newQuestions[diff].filter(
            (q) => q.id !== editingQuestion.id
          );
        });
        newQuestions[updated.difficulty] = [
          ...newQuestions[updated.difficulty],
          updated,
        ];
        return newQuestions;
      });

      resetForm();
    } catch (error) {
      console.error("Failed to update question:", error);
      alert("Failed to update question. Make sure the backend is running.");
    }
  };

  const handleDeleteQuestion = async (questionId, difficulty) => {
    if (!window.confirm("Delete this question?")) return;

    try {
      await questionsApi.delete(questionId);
      setQuestions((prev) => ({
        ...prev,
        [difficulty]: prev[difficulty].filter((q) => q.id !== questionId),
      }));
    } catch (error) {
      console.error("Failed to delete question:", error);
      alert("Failed to delete question. Make sure the backend is running.");
    }
  };

  const startEditQuestion = (question) => {
    setEditingQuestion(question);
    setNewQuestionText(question.text);
    setNewQuestionDifficulty(question.difficulty);
    setShowAddForm(true);
  };

  const resetForm = () => {
    setNewQuestionText("");
    setNewQuestionDifficulty("medium");
    setEditingQuestion(null);
    setShowAddForm(false);
  };

  const handleStartClass = async () => {
    if (!topic.trim()) {
      alert("Please enter a topic before starting the class");
      return;
    }

    const totalQuestions =
      questions.easy.length + questions.medium.length + questions.hard.length;
    if (totalQuestions === 0) {
      alert("Please add at least one question before starting the class");
      return;
    }

    try {
      const session = await sessionsApi.start({
        class_id: parseInt(classId),
        topic: topic.trim(),
      });
      navigate(`/session/${session.id}`);
    } catch (error) {
      console.error("Failed to start session:", error);
      alert("Failed to start session. Make sure the backend is running.");
    }
  };

  const getTotalQuestions = () => {
    return (
      questions.easy.length + questions.medium.length + questions.hard.length
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#EFF0C6] grid-texture flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#000000] mx-auto mb-4"></div>
          <p className="text-[#000000] font-medium">Loading class...</p>
        </div>
      </div>
    );
  }

  if (!classInfo) {
    return (
      <div className="min-h-screen bg-[#EFF0C6] grid-texture flex items-center justify-center">
        <div className="bg-[#DDD6FE] border-2 border-[#000000] rounded-lg p-8 text-center">
          <h2 className="text-2xl font-bold text-[#000000] mb-4">
            Class not found
          </h2>
          <button
            className="px-6 py-3 bg-[#EFF0C6] border-2 border-[#000000] rounded-lg text-[#000000] font-medium hover:bg-[#E8E9B0] transition-colors"
            onClick={() => navigate("/personalized-support")}
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#EFF0C6] grid-texture">
      <div className="container mx-auto px-4 md:px-8 py-6 md:py-10">
        {/* Page Header */}
        <div className="mb-8">
          <button
            className="mb-4 px-4 py-2 bg-white border-2 border-[#000000] rounded-lg text-[#000000] font-medium hover:bg-gray-50 transition-colors flex items-center gap-2"
            onClick={() => navigate("/personalized-support")}
          >
            <svg
              className="w-4 h-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M19 12H5" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
            Back
          </button>
          <div>
            <h1
              className="text-3xl md:text-4xl font-bold text-[#000000] mb-2"
              style={{
                fontFamily: "TT Firs Neue, sans-serif",
                fontWeight: 700,
              }}
            >
              Question Setup
            </h1>
            <p className="text-lg text-[#000000] opacity-80">
              {classInfo.name} • {classInfo.subject}
            </p>
          </div>
        </div>

        {/* Topic Input */}
        <div className="bg-[#ffe99b] border-2 border-[#000000] rounded-lg p-6 md:p-8 mb-6">
          <h2
            className="text-2xl font-bold text-[#000000] mb-4"
            style={{
              fontFamily: "TT Firs Neue, sans-serif",
              fontWeight: 700,
            }}
          >
            Today's Topic
          </h2>
          <div className="flex flex-col md:flex-row gap-4 mb-6">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., Rotational Motion, Photosynthesis, Fractions..."
              className="flex-1 px-4 py-3 bg-white border-2 border-[#000000] text-[#000000] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#000000]"
            />
            <button
              className="px-6 py-3 bg-[#EFF0C6] border-2 border-[#000000] rounded-lg text-[#000000] font-bold hover:bg-[#E8E9B0] transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={handleGenerateQuestions}
              disabled={!topic.trim() || generating}
            >
              {generating ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-[#000000]"></div>
                  Generating...
                </>
              ) : (
                <>
                  <svg
                    className="w-5 h-5"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M12 2L2 7l10 5 10-5-10-5z" />
                    <path d="M2 17l10 5 10-5" />
                    <path d="M2 12l10 5 10-5" />
                  </svg>
                  Generate Questions
                </>
              )}
            </button>
          </div>

          {/* Question Count Controls */}
          <div className="bg-white border-2 border-[#000000] rounded-lg p-4">
            <div className="flex items-center gap-4 mb-4 flex-wrap">
              <span className="text-sm font-medium text-[#000000]">
                Questions to generate:
              </span>
              {["easy", "medium", "hard"].map((diff) => (
                <div key={diff} className="flex items-center gap-2">
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium border ${
                      diff === "easy"
                        ? "bg-green-100 text-green-800 border-green-300"
                        : diff === "hard"
                        ? "bg-red-100 text-red-800 border-red-300"
                        : "bg-yellow-100 text-yellow-800 border-yellow-300"
                    }`}
                  >
                    {diff}
                  </span>
                  <div className="flex items-center gap-2 border-2 border-[#000000] rounded">
                    <button
                      type="button"
                      className="px-2 py-1 text-[#000000] bg-[#ffffff] hover:bg-gray-200 transition-colors disabled:opacity-50"
                      onClick={() => updateQuestionCount(diff, -1)}
                      disabled={questionCounts[diff] <= 0}
                    >
                      −
                    </button>
                    <span className="px-3 py-1 text-[#000000] font-medium min-w-[2rem] text-center">
                      {questionCounts[diff]}
                    </span>
                    <button
                      type="button"
                      className="px-2 py-1 text-[#000000] bg-white hover:bg-gray-200 transition-colors disabled:opacity-50"
                      onClick={() => updateQuestionCount(diff, 1)}
                      disabled={questionCounts[diff] >= 10}
                    >
                      +
                    </button>
                  </div>
                </div>
              ))}
              <span className="text-sm font-bold text-[#000000] ml-auto">
                Total:{" "}
                {questionCounts.easy +
                  questionCounts.medium +
                  questionCounts.hard}
              </span>
            </div>
          </div>
        </div>

        {/* Questions Lists */}
        {topic && (
          <div className="space-y-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <h2
                className="text-2xl font-bold text-[#000000]"
                style={{
                  fontFamily: "TT Firs Neue, sans-serif",
                  fontWeight: 700,
                }}
              >
                Questions for: {topic}
              </h2>
              <div className="flex items-center gap-4">
                <span className="text-sm text-[#000000] opacity-70">
                  {getTotalQuestions()} questions
                </span>
                <button
                  className="px-4 py-2 bg-white border-2 border-[#000000] rounded-lg text-sm font-medium text-[#000000] hover:bg-gray-50 transition-colors flex items-center gap-2"
                  onClick={() => setShowAddForm(true)}
                >
                  <svg
                    className="w-4 h-4"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <line x1="12" y1="5" x2="12" y2="19" />
                    <line x1="5" y1="12" x2="19" y2="12" />
                  </svg>
                  Add Question
                </button>
              </div>
            </div>

            {showAddForm && (
              <form
                className="bg-white border-2 border-[#000000] rounded-lg p-6 mb-6"
                onSubmit={
                  editingQuestion ? handleUpdateQuestion : handleAddQuestion
                }
              >
                <h3 className="text-lg font-bold text-[#000000] mb-4">
                  {editingQuestion ? "Edit Question" : "Add New Question"}
                </h3>

                <div className="mb-4">
                  <label className="block text-sm font-bold text-[#000000] mb-2">
                    Question Text
                  </label>
                  <textarea
                    value={newQuestionText}
                    onChange={(e) => setNewQuestionText(e.target.value)}
                    placeholder="Enter your question..."
                    rows={3}
                    className="w-full px-4 py-3 bg-white border-2 border-[#000000] text-[#000000] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#000000]"
                    autoFocus
                  />
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-bold text-[#000000] mb-2">
                    Difficulty
                  </label>
                  <div className="flex gap-2">
                    {["easy", "medium", "hard"].map((diff) => (
                      <button
                        key={diff}
                        type="button"
                        className={`flex-1 px-4 py-2 rounded-lg border-2 font-medium transition-colors ${
                          newQuestionDifficulty === diff
                            ? diff === "easy"
                              ? "bg-green-500 text-white border-green-600"
                              : diff === "hard"
                              ? "bg-red-500 text-white border-red-600"
                              : "bg-yellow-500 text-white border-yellow-600"
                            : "bg-white text-[#000000] border-[#000000] hover:bg-gray-50"
                        }`}
                        onClick={() => setNewQuestionDifficulty(diff)}
                      >
                        {diff.charAt(0).toUpperCase() + diff.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2 justify-end">
                  <button
                    type="button"
                    className="px-4 py-2 bg-white border-2 border-[#000000] rounded-lg text-sm font-medium text-[#000000] hover:bg-gray-50 transition-colors"
                    onClick={resetForm}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-[#EFF0C6] border-2 border-[#000000] rounded-lg text-sm font-medium text-[#000000] hover:bg-[#E8E9B0] transition-colors"
                  >
                    {editingQuestion ? "Update" : "Add Question"}
                  </button>
                </div>
              </form>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {["easy", "medium", "hard"].map((difficulty) => (
                <div
                  key={difficulty}
                  className="bg-[#DDD6FE] border-2 border-[#000000] rounded-lg overflow-hidden"
                >
                  <div className="p-4 bg-white border-b-2 border-[#000000] flex items-center justify-between">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium border ${
                        difficulty === "easy"
                          ? "bg-green-100 text-green-800 border-green-300"
                          : difficulty === "hard"
                          ? "bg-red-100 text-red-800 border-red-300"
                          : "bg-yellow-100 text-yellow-800 border-yellow-300"
                      }`}
                    >
                      {difficulty}
                    </span>
                    <span className="text-sm font-bold text-[#000000]">
                      {questions[difficulty].length}
                    </span>
                  </div>

                  <div className="p-4 space-y-3 max-h-[500px] overflow-y-auto">
                    {questions[difficulty].length === 0 ? (
                      <div className="text-center py-8 text-[#000000] opacity-60">
                        <p>No {difficulty} questions</p>
                      </div>
                    ) : (
                      questions[difficulty].map((q) => (
                        <div
                          key={q.id}
                          className="bg-white border-2 border-[#000000] rounded-lg p-4 hover:shadow-md transition-shadow"
                        >
                          <p className="text-[#000000] mb-3">{q.text}</p>
                          <div className="flex items-center gap-2">
                            <button
                              className="p-2 bg-white border-2 border-[#000000] rounded-lg hover:bg-[#EFF0C6] transition-colors"
                              onClick={() => startEditQuestion(q)}
                              title="Edit"
                            >
                              <svg
                                className="w-4 h-4 text-[#000000]"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                              >
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                              </svg>
                            </button>
                            <button
                              className="p-2 bg-white border-2 border-[#000000] rounded-lg hover:bg-red-50 transition-colors"
                              onClick={() =>
                                handleDeleteQuestion(q.id, difficulty)
                              }
                              title="Delete"
                            >
                              <svg
                                className="w-4 h-4 text-red-600"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                              >
                                <polyline points="3 6 5 6 21 6" />
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                              </svg>
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Start Class Button */}
            <div className="flex justify-center pt-6">
              <button
                className="px-8 py-4 bg-[#EFF0C6] border-2 border-[#000000] rounded-lg text-lg font-bold text-[#000000] hover:bg-[#E8E9B0] transition-colors flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1"
                onClick={handleStartClass}
                disabled={getTotalQuestions() === 0}
              >
                <svg
                  className="w-6 h-6"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <polygon points="5 3 19 12 5 21 5 3" />
                </svg>
                Start Class Session
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default QuestionSetup;
