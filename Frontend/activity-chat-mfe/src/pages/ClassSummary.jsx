import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { analyticsApi } from "../utils/classroomApi";
import StarRating from "../components/StarRating";
import {
  Users,
  HelpCircle,
  Star,
  TrendingUp,
  ArrowLeft,
  AlertCircle,
} from "lucide-react";

function ClassSummary() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSummary();
  }, [sessionId]);

  const loadSummary = async () => {
    try {
      const data = await analyticsApi.getSessionSummary(sessionId);
      setSummary(data);
    } catch (error) {
      console.error("Failed to load summary:", error);
      setError("Failed to load session summary");
      alert("Failed to load summary. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (minutes) => {
    if (minutes < 1) return "Less than a minute";
    if (minutes < 60) return `${Math.round(minutes)} minutes`;
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#EFF0C6] grid-texture flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#000000] mx-auto mb-4"></div>
          <p className="text-[#000000] font-medium">Loading summary...</p>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="min-h-screen bg-[#EFF0C6] grid-texture flex items-center justify-center">
        <div className="bg-[#DDD6FE] border-2 border-[#000000] rounded-lg p-8 text-center">
          <h2 className="text-2xl font-bold text-[#000000] mb-4">
            {error || "Summary not found"}
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
            <ArrowLeft className="w-4 h-4" />
            Back to Classes
          </button>
          <div>
            <h1
              className="text-3xl md:text-4xl font-bold text-[#000000] mb-2"
              style={{
                fontFamily: "TT Firs Neue, sans-serif",
                fontWeight: 700,
              }}
            >
              Session Summary
            </h1>
            <p className="text-lg text-[#000000] opacity-80">{summary.topic}</p>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-8">
          <div className="bg-[#FFDAD6] border-2 border-[#000000] rounded-lg p-6 text-center">
            <div className="w-14 h-14 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Users className="w-7 h-7 text-blue-600" />
            </div>
            <div className="mb-2">
              <span className="text-4xl font-bold text-[#000000]">
                {summary.participation_percentage.toFixed(0)}%
              </span>
              <span className="block text-sm text-[#000000] opacity-70 mt-1">
                Participation
              </span>
            </div>
            <div className="text-xs text-[#000000] opacity-60">
              {summary.students_called} of{" "}
              {summary.students_called + summary.students_not_called} students
            </div>
          </div>

          <div className="bg-[#DDD6FE] border-2 border-[#000000] rounded-lg p-6 text-center">
            <div className="w-14 h-14 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <HelpCircle className="w-7 h-7 text-purple-600" />
            </div>
            <div className="mb-2">
              <span className="text-4xl font-bold text-[#000000]">
                {summary.total_questions_asked}
              </span>
              <span className="block text-sm text-[#000000] opacity-70 mt-1">
                Questions Asked
              </span>
            </div>
            <div className="text-xs text-[#000000] opacity-60">
              {formatDuration(summary.duration_minutes)}
            </div>
          </div>

          <div className="bg-[#DDD6FE] border-2 border-[#000000] rounded-lg p-6 text-center">
            <div className="w-14 h-14 bg-orange-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Star className="w-7 h-7 text-orange-600" />
            </div>
            <div className="mb-2">
              <span className="text-4xl font-bold text-[#000000]">
                {summary.average_rating.toFixed(1)}
              </span>
              <span className="block text-sm text-[#000000] opacity-70 mt-1">
                Avg Rating
              </span>
            </div>
            <div className="flex justify-center">
              <StarRating
                value={Math.round(summary.average_rating)}
                readonly
                size="small"
              />
            </div>
          </div>

          <div className="bg-[#ffffff] border-2 border-[#000000] rounded-lg p-6 text-center">
            <div className="w-14 h-14 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <TrendingUp className="w-7 h-7 text-green-600" />
            </div>
            <div className="mb-2">
              <span className="text-4xl font-bold text-[#000000]">
                {summary.students_improved.length}
              </span>
              <span className="block text-sm text-[#000000] opacity-70 mt-1">
                Students Improved
              </span>
            </div>
            <div className="text-xs text-[#000000] opacity-60">
              This session
            </div>
          </div>
        </div>

        {/* Difficulty Distribution */}
        <div className="bg-[#DDD6FE] border-2 border-[#000000] rounded-lg p-6 md:p-8 mb-6">
          <h2
            className="text-2xl font-bold text-[#000000] mb-6"
            style={{
              fontFamily: "TT Firs Neue, sans-serif",
              fontWeight: 700,
            }}
          >
            Difficulty Distribution
          </h2>
          <div className="space-y-4">
            {["easy", "medium", "hard"].map((diff) => {
              const count = summary.difficulty_distribution[diff] || 0;
              const total = summary.total_questions_asked || 1;
              const percentage = (count / total) * 100;

              return (
                <div key={diff} className="flex items-center gap-4">
                  <span
                    className={`px-3 py-1 rounded-lg text-sm font-bold border w-20 text-center ${
                      diff === "easy"
                        ? "bg-green-100 text-green-800 border-green-300"
                        : diff === "hard"
                        ? "bg-red-100 text-red-800 border-red-300"
                        : "bg-yellow-100 text-yellow-800 border-yellow-300"
                    }`}
                  >
                    {diff}
                  </span>
                  <div className="flex-1 h-6 bg-white border-2 border-[#000000] rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        diff === "easy"
                          ? "bg-green-500"
                          : diff === "hard"
                          ? "bg-red-500"
                          : "bg-yellow-500"
                      }`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold text-[#000000] w-12 text-right">
                    {count}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Student Lists */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Students Who Improved */}
          <div className="bg-[#ECF1FF] border-2 border-[#000000] rounded-lg p-6">
            <h2
              className="text-xl font-bold text-[#000000] mb-4 flex items-center gap-2"
              style={{
                fontFamily: "TT Firs Neue, sans-serif",
                fontWeight: 700,
              }}
            >
              <TrendingUp className="w-5 h-5" />
              Improved
            </h2>
            {summary.students_improved.length === 0 ? (
              <p className="text-sm text-[#000000] opacity-60 text-center py-8">
                No students improved this session
              </p>
            ) : (
              <div className="space-y-2">
                {summary.students_improved.map((s) => (
                  <div
                    key={s.student_id}
                    className="bg-white border-2 border-[#000000] rounded-lg p-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                  >
                    <span className="font-medium text-[#000000]">
                      {s.student_name}
                    </span>
                    <span className="text-sm font-bold text-green-600">
                      +{s.confidence_change.toFixed(1)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Students Needing Attention */}
          <div className="bg-[#eafff6] border-2 border-[#000000] rounded-lg p-6">
            <h2
              className="text-xl font-bold text-[#000000] mb-4 flex items-center gap-2"
              style={{
                fontFamily: "TT Firs Neue, sans-serif",
                fontWeight: 700,
              }}
            >
              <AlertCircle className="w-5 h-5" />
              Needs Attention
            </h2>
            {summary.students_need_attention.length === 0 ? (
              <p className="text-sm text-[#000000] opacity-60 text-center py-8">
                All students are doing well!
              </p>
            ) : (
              <div className="space-y-2">
                {summary.students_need_attention.map((s) => (
                  <div
                    key={s.student_id}
                    className="bg-white border-2 border-[#000000] rounded-lg p-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                  >
                    <span className="font-medium text-[#000000]">
                      {s.student_name}
                    </span>
                    {s.times_called === 0 ? (
                      <span className="text-xs text-[#000000] opacity-60 bg-gray-100 px-2 py-1 rounded border border-[#000000]">
                        Not called
                      </span>
                    ) : (
                      <span className="text-sm font-bold text-red-600">
                        {s.confidence_change.toFixed(1)}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* All Students */}
        <div className="bg-[#FCF4AC] border-2 border-[#000000] rounded-lg p-6 md:p-8">
          <h2
            className="text-2xl font-bold text-[#000000] mb-6"
            style={{
              fontFamily: "TT Firs Neue, sans-serif",
              fontWeight: 700,
            }}
          >
            All Student Performance
          </h2>
          <div className="overflow-x-auto">
            <div className="min-w-full">
              {/* Table Header */}
              <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr] gap-4 pb-3 mb-3 border-b-2 border-[#000000] text-xs font-bold text-[#000000] opacity-70 uppercase tracking-wide">
                <span>Student</span>
                <span>Times Called</span>
                <span>Avg Rating</span>
                <span>Change</span>
                <span>Homework</span>
              </div>

              {/* Table Rows */}
              <div className="space-y-2">
                {summary.all_student_summaries.map((s) => {
                  const getHomeworkLevel = () => {
                    if (s.times_called === 0) return null;
                    if (s.average_rating < 2.5) return "easy";
                    if (s.average_rating < 4) return "medium";
                    return "hard";
                  };
                  const homeworkLevel = getHomeworkLevel();

                  return (
                    <div
                      key={s.student_id}
                      className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr] gap-4 items-center py-3 px-2 bg-white border-2 border-[#000000] rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <span className="font-medium text-[#000000]">
                        {s.student_name}
                      </span>
                      <span className="text-[#000000]">{s.times_called}</span>
                      <span className="flex items-center">
                        {s.times_called > 0 ? (
                          <StarRating
                            value={Math.round(s.average_rating)}
                            readonly
                            size="small"
                          />
                        ) : (
                          <span className="text-[#000000] opacity-50">-</span>
                        )}
                      </span>
                      <span
                        className={`text-sm font-bold ${
                          s.confidence_change > 0
                            ? "text-green-600"
                            : s.confidence_change < 0
                            ? "text-red-600"
                            : "text-[#000000]"
                        }`}
                      >
                        {s.confidence_change > 0 ? "+" : ""}
                        {s.confidence_change.toFixed(1)}
                      </span>
                      <span>
                        {homeworkLevel ? (
                          <span
                            className={`px-2 py-1 rounded text-xs font-medium border ${
                              homeworkLevel === "easy"
                                ? "bg-green-100 text-green-800 border-green-300"
                                : homeworkLevel === "hard"
                                ? "bg-red-100 text-red-800 border-red-300"
                                : "bg-yellow-100 text-yellow-800 border-yellow-300"
                            }`}
                          >
                            {homeworkLevel === "easy"
                              ? "Easy"
                              : homeworkLevel === "medium"
                              ? "Medium"
                              : "Hard"}
                          </span>
                        ) : (
                          <span className="text-[#000000] opacity-50">-</span>
                        )}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ClassSummary;
