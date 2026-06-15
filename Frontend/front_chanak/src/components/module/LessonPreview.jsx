import { useState } from "react";

/**
 * LessonPreview - Displays 8-slide lesson in carousel/grid view
 * Shows slide content: explanation, bullets, key terms, diagrams
 * Requirements: 3.2
 */
function LessonPreview({ lesson }) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [viewMode, setViewMode] = useState("carousel"); // "carousel" or "grid"

  if (!lesson || !lesson.slides || lesson.slides.length === 0) {
    return (
      <div className="bg-white border-2 border-[#000000] rounded-lg p-6 shadow-[4px_4px_0px_0px_#000000]">
        <p className="text-center text-gray-500">No lesson to display</p>
      </div>
    );
  }

  const slides = lesson.slides;
  const slide = slides[currentSlide];

  const goToSlide = (index) => {
    setCurrentSlide(Math.max(0, Math.min(index, slides.length - 1)));
  };

  const nextSlide = () => goToSlide(currentSlide + 1);
  const prevSlide = () => goToSlide(currentSlide - 1);

  const getSlideTypeColor = (slideType) => {
    const colors = {
      introduction: "#FDE047",
      concept: "#E8D5FF",
      examples: "#D4F1C5",
      practice: "#E0EEEF",
      real_world: "#F99DA8",
      summary: "#FDE047",
    };
    return colors[slideType] || "#FFFFFF";
  };

  const getSlideTypeLabel = (slideType) => {
    const labels = {
      introduction: "Introduction",
      concept: "Concept",
      examples: "Examples",
      practice: "Practice",
      real_world: "Real World",
      summary: "Summary",
    };
    return labels[slideType] || slideType;
  };

  return (
    <div className="bg-white border-2 border-[#000000] rounded-lg shadow-[4px_4px_0px_0px_#000000] overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b-2 border-[#000000] bg-[#FDE047]">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-[#000000]">{lesson.topic}</h2>
            <p className="text-sm text-[#000000] opacity-70">
              {lesson.class_name?.replace("_", " ")} • {lesson.subject?.replace(/_/g, " ")}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode("carousel")}
              className={`p-2 border-2 border-[#000000] rounded transition-all ${
                viewMode === "carousel" 
                  ? "bg-[#000000] text-white" 
                  : "bg-white text-[#000000] hover:bg-gray-100"
              }`}
              title="Carousel View"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode("grid")}
              className={`p-2 border-2 border-[#000000] rounded transition-all ${
                viewMode === "grid" 
                  ? "bg-[#000000] text-white" 
                  : "bg-white text-[#000000] hover:bg-gray-100"
              }`}
              title="Grid View"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {viewMode === "carousel" ? (
        <CarouselView
          slide={slide}
          slides={slides}
          currentSlide={currentSlide}
          goToSlide={goToSlide}
          nextSlide={nextSlide}
          prevSlide={prevSlide}
          getSlideTypeColor={getSlideTypeColor}
          getSlideTypeLabel={getSlideTypeLabel}
        />
      ) : (
        <GridView
          slides={slides}
          goToSlide={goToSlide}
          setViewMode={setViewMode}
          getSlideTypeColor={getSlideTypeColor}
          getSlideTypeLabel={getSlideTypeLabel}
        />
      )}
    </div>
  );
}

function CarouselView({ 
  slide, slides, currentSlide, goToSlide, nextSlide, prevSlide, 
  getSlideTypeColor, getSlideTypeLabel 
}) {
  return (
    <>
      {/* Slide Content */}
      <div className="p-6" style={{ backgroundColor: getSlideTypeColor(slide.slide_type) + "40" }}>
        {/* Slide Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 text-sm font-bold border-2 border-[#000000] rounded-full bg-white">
              Slide {slide.slide_number}/8
            </span>
            <span 
              className="px-3 py-1 text-sm font-bold border-2 border-[#000000] rounded-full"
              style={{ backgroundColor: getSlideTypeColor(slide.slide_type) }}
            >
              {getSlideTypeLabel(slide.slide_type)}
            </span>
          </div>
        </div>

        {/* Slide Title */}
        <h3 className="text-2xl font-bold text-[#000000] mb-4">{slide.title}</h3>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Text Content */}
          <div className="space-y-4">
            {/* Explanation */}
            <div className="bg-white border-2 border-[#000000] rounded-lg p-4">
              <h4 className="font-bold text-[#000000] mb-2 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Explanation
              </h4>
              <p className="text-[#000000] leading-relaxed">{slide.explanation}</p>
            </div>

            {/* Key Terms */}
            {slide.key_terms && slide.key_terms.length > 0 && (
              <div className="bg-white border-2 border-[#000000] rounded-lg p-4">
                <h4 className="font-bold text-[#000000] mb-2 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                  Key Terms
                </h4>
                <div className="flex flex-wrap gap-2">
                  {slide.key_terms.map((term, idx) => (
                    <span 
                      key={idx} 
                      className="px-3 py-1 text-sm font-medium border-2 border-[#000000] rounded-full bg-[#E8D5FF]"
                    >
                      {term}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Examples & Key Points */}
          <div className="space-y-4">
            {/* Examples */}
            {slide.examples && slide.examples.length > 0 && (
              <div className="bg-white border-2 border-[#000000] rounded-lg p-4">
                <h4 className="font-bold text-[#000000] mb-2 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  Examples
                </h4>
                <div className="space-y-2">
                  {slide.examples.map((example, idx) => (
                    <div 
                      key={idx} 
                      className="p-3 bg-[#D4F1C5] border-2 border-[#000000] rounded-lg text-[#000000]"
                    >
                      {example}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Key Points */}
            {slide.bullet_points && slide.bullet_points.length > 0 && (
              <div className="bg-white border-2 border-[#000000] rounded-lg p-4">
                <h4 className="font-bold text-[#000000] mb-2 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                  </svg>
                  Key Points
                </h4>
                <ul className="space-y-2">
                  {slide.bullet_points.map((point, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-[#000000]">
                      <span className="w-2 h-2 mt-2 bg-[#000000] rounded-full flex-shrink-0" />
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="p-4 border-t-2 border-[#000000] bg-white">
        <div className="flex items-center justify-between">
          <button
            onClick={prevSlide}
            disabled={currentSlide === 0}
            className="flex items-center gap-2 px-4 py-2 border-2 border-[#000000] rounded-lg font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#FDE047] shadow-[2px_2px_0px_0px_#000000] hover:shadow-[1px_1px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5 text-white"
          >
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Previous
          </button>

          {/* Slide Indicators */}
          <div className="flex items-center gap-2">
            {slides.map((_, idx) => (
              <button
                key={idx}
                onClick={() => goToSlide(idx)}
                className={`w-3 h-3 rounded-full border-2 border-[#000000] transition-all ${
                  idx === currentSlide ? "bg-[#FDE047]" : "bg-white hover:bg-gray-200"
                }`}
                title={`Go to slide ${idx + 1}`}
              />
            ))}
          </div>

          <button
            onClick={nextSlide}
            disabled={currentSlide === slides.length - 1}
            className="flex items-center gap-2 px-4 py-2 border-2 border-[#000000] rounded-lg font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#FDE047] shadow-[2px_2px_0px_0px_#000000] hover:shadow-[1px_1px_0px_0px_#000000] hover:translate-x-0.5 hover:translate-y-0.5 text-white"
          >
            Next
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </>
  );
}

function GridView({ slides, goToSlide, setViewMode, getSlideTypeColor, getSlideTypeLabel }) {
  return (
    <div className="p-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {slides.map((slide, idx) => (
          <button
            key={idx}
            onClick={() => {
              goToSlide(idx);
              setViewMode("carousel");
            }}
            className="p-4 border-2 border-[#000000] rounded-lg text-left transition-all hover:shadow-[2px_2px_0px_0px_#000000] hover:-translate-x-0.5 hover:-translate-y-0.5"
            style={{ backgroundColor: getSlideTypeColor(slide.slide_type) + "60" }}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold px-2 py-1 bg-white border border-[#000000] rounded">
                {slide.slide_number}
              </span>
              <span className="text-xs font-medium">
                {getSlideTypeLabel(slide.slide_type)}
              </span>
            </div>
            <h4 className="font-bold text-sm text-[#000000] line-clamp-2 mb-2">
              {slide.title}
            </h4>
            <p className="text-xs text-[#000000] opacity-70 line-clamp-3">
              {slide.explanation}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}

export default LessonPreview;
