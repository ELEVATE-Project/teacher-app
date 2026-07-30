function SuggestionCard({ suggestion, onAsk, onSkip, loading = false }) {
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

  const getInitials = (name) => {
    return name
      .split(" ")
      .map((part) => part[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const getAvatarColor = (name) => {
    const colors = [
      "#E57373",
      "#81C784",
      "#64B5F6",
      "#FFD54F",
      "#BA68C8",
      "#4DB6AC",
      "#FF8A65",
      "#A1887F",
    ];
    const index = name
      .split("")
      .reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return colors[index % colors.length];
  };

  if (loading) {
    return (
      <div className="bg-[#DDD6FE] border-2 border-[#000000] rounded-lg p-12 flex flex-col items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#000000] mb-4"></div>
        <p className="text-[#000000] font-medium">Finding next student...</p>
      </div>
    );
  }

  if (!suggestion) {
    return (
      <div className="bg-[#DDD6FE] border-2 border-[#000000] rounded-lg p-12 flex flex-col items-center justify-center text-center">
        <svg
          className="w-16 h-16 text-[#000000] opacity-50 mb-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <circle cx="12" cy="12" r="10" />
          <path d="M8 15h8" />
          <circle cx="9" cy="9" r="1" fill="currentColor" />
          <circle cx="15" cy="9" r="1" fill="currentColor" />
        </svg>
        <p className="text-xl font-bold text-[#000000] mb-2">
          All students have been called!
        </p>
        <span className="text-[#000000] opacity-70">
          Great participation in this session.
        </span>
      </div>
    );
  }

  return (
    <div className="bg-[#FFF6E5] border-2 border-[#000000] rounded-lg p-6 md:p-8 animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <span className="text-sm font-bold text-[#000000] uppercase tracking-wide">
          Ask Next
        </span>
        <span
          className={`px-3 py-1 rounded-lg text-sm font-bold border ${getDifficultyBadgeClass(
            suggestion.difficulty
          )}`}
        >
          {suggestion.difficulty}
        </span>
      </div>

      <div className="flex flex-col items-center mb-6">
        <div
          className="w-20 h-20 rounded-full flex items-center justify-center text-white font-bold text-2xl mb-4"
          style={{ backgroundColor: getAvatarColor(suggestion.student_name) }}
        >
          {getInitials(suggestion.student_name)}
        </div>
        <div className="text-2xl font-bold text-[#000000]">
          {suggestion.student_name}
        </div>
      </div>

      {suggestion.question_text && (
        <div className="bg-white border-2 border-[#000000] rounded-lg p-4 mb-6">
          <div className="text-xs font-bold text-[#000000] opacity-70 uppercase tracking-wide mb-2">
            Suggested Question
          </div>
          <div className="text-lg text-[#000000] italic">
            "{suggestion.question_text}"
          </div>
        </div>
      )}

      <div className="flex items-start gap-3 mb-6 p-4 bg-white border-2 border-[#000000] rounded-lg">
        <svg
          className="w-5 h-5 text-[#000000] flex-shrink-0 mt-0.5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <circle cx="12" cy="12" r="10" />
          <path d="M12 16v-4" />
          <path d="M12 8h.01" />
        </svg>
        <span className="text-[#000000] text-sm">{suggestion.reason}</span>
      </div>

      <div className="flex gap-4">
        <button
          className="flex-1 px-6 py-4 bg-white border-2 border-[#000000] rounded-lg text-[#000000] font-bold hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
          onClick={onSkip}
        >
          <svg
            className="w-5 h-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M5 4l10 8-10 8V4z" />
            <line x1="19" y1="5" x2="19" y2="19" />
          </svg>
          Skip
        </button>
        <button
          className="flex-1 px-6 py-4 bg-[#ffd9e4] border-2 border-[#000000] rounded-lg text-[#000000] font-bold hover:bg-[#E8E9B0] transition-colors flex items-center justify-center gap-2 shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1"
          onClick={onAsk}
        >
          <svg
            className="w-5 h-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          Ask Question
        </button>
      </div>
    </div>
  );
}

export default SuggestionCard;
