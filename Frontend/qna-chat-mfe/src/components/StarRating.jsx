import { useState } from "react";

function StarRating({
  value = 0,
  onChange,
  size = "medium",
  readonly = false,
}) {
  const [hoverValue, setHoverValue] = useState(0);

  const handleClick = (rating) => {
    if (!readonly && onChange) {
      onChange(rating);
    }
  };

  const handleMouseEnter = (rating) => {
    if (!readonly) {
      setHoverValue(rating);
    }
  };

  const handleMouseLeave = () => {
    setHoverValue(0);
  };

  const displayValue = hoverValue || value;

  const sizeClasses = {
    small: "w-3 h-3",
    medium: "w-5 h-5",
    large: "w-8 h-8",
    xlarge: "w-10 h-10",
  };

  return (
    <div
      className={`flex items-center gap-1 ${
        readonly ? "cursor-default" : "cursor-pointer"
      }`}
      onMouseLeave={handleMouseLeave}
    >
      {[1, 2, 3, 4, 5].map((rating) => {
        const isFilled = displayValue >= rating;
        return (
          <button
            key={rating}
            type="button"
            className={`${
              sizeClasses[size]
            } p-0 border-none bg-transparent transition-all ${
              readonly ? "cursor-default" : "cursor-pointer hover:scale-110"
            }`}
            onClick={() => handleClick(rating)}
            onMouseEnter={() => handleMouseEnter(rating)}
            disabled={readonly}
            aria-label={`Rate ${rating} stars`}
          >
            <svg
              viewBox="0 0 24 24"
              className="w-full h-full"
              fill={isFilled ? "#FCD34D" : "none"}
              stroke={isFilled ? "#FCD34D" : "#000000"}
              strokeWidth={isFilled ? "0" : "1.5"}
            >
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
          </button>
        );
      })}
    </div>
  );
}

export default StarRating;
