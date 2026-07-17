import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import StarRating from "./StarRating";

function RatingPopup({ studentName, difficulty, onSubmit, onCancel }) {
  const [rating, setRating] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  const handleSubmit = async () => {
    if (rating === 0) return;

    setSubmitting(true);
    await onSubmit(rating);
    setSubmitting(false);
  };

  const getRatingLabel = (rating) => {
    switch (rating) {
      case 5:
        return "Excellent! Perfect answer";
      case 4:
        return "Good answer";
      case 3:
        return "Acceptable";
      case 2:
        return "Needs improvement";
      case 1:
        return "Struggled/No answer";
      default:
        return "Tap stars to rate";
    }
  };

  const getDifficultyBadgeClass = (difficulty) => {
    switch (difficulty) {
      case "easy":
        return "bg-green-100 text-green-800 border-green-300";
      case "hard":
        return "bg-red-100 text-red-800 border-red-300";
      default:
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
    }
  };

  if (!mounted) return null;

  const popupContent = (
    <div
      className="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center z-[9999] p-4"
      onClick={onCancel}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 9999,
      }}
    >
      <div
        className="bg-[#DDD6FE] border-2 border-[#000000] rounded-lg p-6 md:p-8 max-w-md w-full shadow-2xl animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-[#000000]">
            Rate {studentName}'s Answer
          </h3>
          <span
            className={`px-2 py-1 rounded text-xs font-medium border ${getDifficultyBadgeClass(
              difficulty
            )}`}
          >
            {difficulty} question
          </span>
        </div>

        <div className="mb-6">
          <div className="flex justify-center mb-4">
            <StarRating value={rating} onChange={setRating} size="xlarge" />
          </div>

          <p
            className={`text-center text-sm font-medium transition-opacity ${
              rating > 0
                ? "text-[#000000] opacity-100"
                : "text-[#000000] opacity-50"
            }`}
          >
            {getRatingLabel(rating)}
          </p>
        </div>

        <div className="flex gap-3">
          <button
            className="flex-1 px-4 py-3 bg-white border-2 border-[#000000] rounded-lg text-[#000000] font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
            onClick={onCancel}
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            className="flex-1 px-4 py-3 bg-[#EFF0C6] border-2 border-[#000000] rounded-lg text-[#000000] font-medium hover:bg-[#E8E9B0] transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleSubmit}
            disabled={rating === 0 || submitting}
          >
            {submitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-[#000000]"></div>
                Submitting...
              </>
            ) : (
              <>
                Submit Rating
                <svg
                  className="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );

  return createPortal(popupContent, document.body);
}

export default RatingPopup;
