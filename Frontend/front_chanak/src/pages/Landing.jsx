import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useState,
} from "react";
import { motion, AnimatePresence } from "motion/react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

const RotatingText = forwardRef((props, ref) => {
  const {
    texts,
    transition = { type: "spring", damping: 25, stiffness: 300 },
    initial = { y: "100%", opacity: 0 },
    animate = { y: 0, opacity: 1 },
    exit = { y: "-120%", opacity: 0 },
    animatePresenceMode = "wait",
    animatePresenceInitial = false,
    rotationInterval = 2000,
    staggerDuration = 0,
    staggerFrom = "first",
    loop = true,
    auto = true,
    splitBy = "characters",
    onNext,
    mainClassName,
    splitLevelClassName,
    elementLevelClassName,
    ...rest
  } = props;

  const [currentTextIndex, setCurrentTextIndex] = useState(0);

  const splitIntoCharacters = (text) => {
    if (typeof Intl !== "undefined" && Intl.Segmenter) {
      const segmenter = new Intl.Segmenter("en", { granularity: "grapheme" });
      return Array.from(segmenter.segment(text), (segment) => segment.segment);
    }
    return Array.from(text);
  };

  const elements = useMemo(() => {
    const currentText = texts[currentTextIndex];
    if (splitBy === "characters") {
      const words = currentText.split(" ");
      return words.map((word, i) => ({
        characters: splitIntoCharacters(word),
        needsSpace: i !== words.length - 1,
      }));
    }
    if (splitBy === "words") {
      return currentText.split(" ").map((word, i, arr) => ({
        characters: [word],
        needsSpace: i !== arr.length - 1,
      }));
    }
    if (splitBy === "lines") {
      return currentText.split("\n").map((line, i, arr) => ({
        characters: [line],
        needsSpace: i !== arr.length - 1,
      }));
    }

    return currentText.split(splitBy).map((part, i, arr) => ({
      characters: [part],
      needsSpace: i !== arr.length - 1,
    }));
  }, [texts, currentTextIndex, splitBy]);

  const getStaggerDelay = useCallback(
    (index, totalChars) => {
      const total = totalChars;
      if (staggerFrom === "first") return index * staggerDuration;
      if (staggerFrom === "last") return (total - 1 - index) * staggerDuration;
      if (staggerFrom === "center") {
        const center = Math.floor(total / 2);
        return Math.abs(center - index) * staggerDuration;
      }
      if (staggerFrom === "random") {
        const randomIndex = Math.floor(Math.random() * total);
        return Math.abs(randomIndex - index) * staggerDuration;
      }
      return Math.abs(staggerFrom - index) * staggerDuration;
    },
    [staggerFrom, staggerDuration]
  );

  const handleIndexChange = useCallback(
    (newIndex) => {
      setCurrentTextIndex(newIndex);
      if (onNext) onNext(newIndex);
    },
    [onNext]
  );

  const next = useCallback(() => {
    const nextIndex =
      currentTextIndex === texts.length - 1
        ? loop
          ? 0
          : currentTextIndex
        : currentTextIndex + 1;
    if (nextIndex !== currentTextIndex) {
      handleIndexChange(nextIndex);
    }
  }, [currentTextIndex, texts.length, loop, handleIndexChange]);

  const previous = useCallback(() => {
    const prevIndex =
      currentTextIndex === 0
        ? loop
          ? texts.length - 1
          : currentTextIndex
        : currentTextIndex - 1;
    if (prevIndex !== currentTextIndex) {
      handleIndexChange(prevIndex);
    }
  }, [currentTextIndex, texts.length, loop, handleIndexChange]);

  const jumpTo = useCallback(
    (index) => {
      const validIndex = Math.max(0, Math.min(index, texts.length - 1));
      if (validIndex !== currentTextIndex) {
        handleIndexChange(validIndex);
      }
    },
    [texts.length, currentTextIndex, handleIndexChange]
  );

  const reset = useCallback(() => {
    if (currentTextIndex !== 0) {
      handleIndexChange(0);
    }
  }, [currentTextIndex, handleIndexChange]);

  useImperativeHandle(
    ref,
    () => ({
      next,
      previous,
      jumpTo,
      reset,
    }),
    [next, previous, jumpTo, reset]
  );

  useEffect(() => {
    if (!auto) return;
    const intervalId = setInterval(next, rotationInterval);
    return () => clearInterval(intervalId);
  }, [next, rotationInterval, auto]);

  return (
    <motion.span
      className={cn(
        "flex flex-wrap whitespace-pre-wrap relative",
        mainClassName
      )}
      {...rest}
      layout
      transition={transition}
    >
      <span className="sr-only">{texts[currentTextIndex]}</span>
      <AnimatePresence
        mode={animatePresenceMode}
        initial={animatePresenceInitial}
      >
        <motion.span
          key={currentTextIndex}
          className={cn(
            splitBy === "lines"
              ? "flex flex-col w-full"
              : "flex flex-wrap whitespace-pre-wrap relative"
          )}
          layout
          aria-hidden="true"
        >
          {elements.map((wordObj, wordIndex, array) => {
            const previousCharsCount = array
              .slice(0, wordIndex)
              .reduce((sum, word) => sum + word.characters.length, 0);
            return (
              <span
                key={wordIndex}
                className={cn("inline-flex", splitLevelClassName)}
              >
                {wordObj.characters.map((char, charIndex) => (
                  <motion.span
                    key={charIndex}
                    initial={initial}
                    animate={animate}
                    exit={exit}
                    transition={{
                      ...transition,
                      delay: getStaggerDelay(
                        previousCharsCount + charIndex,
                        array.reduce(
                          (sum, word) => sum + word.characters.length,
                          0
                        )
                      ),
                    }}
                    className={cn("inline-block", elementLevelClassName)}
                  >
                    {char}
                  </motion.span>
                ))}
                {wordObj.needsSpace && (
                  <span className="whitespace-pre"> </span>
                )}
              </span>
            );
          })}
        </motion.span>
      </AnimatePresence>
    </motion.span>
  );
});

RotatingText.displayName = "RotatingText";

function Landing() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#FFFFFF]">
      <div className="w-full max-w-6xl mx-auto space-y-12 py-12">
        <div className="text-center">
          <img src="/fav_icon_chanakya.png" alt="Chanakya" className="w-32 h-32 mx-auto mb-6 object-contain" />
          <h1 className="text-4xl md:text-6xl font-extrabold text-[#000000]" style={{ fontFamily: "TT Firs Neue, sans-serif" }}>
            Welcome to Chanakya
          </h1>
          <p className="mt-4 text-xl text-[#000000] font-medium max-w-2xl mx-auto">
            Your continuous support system for planning, handling, and reflecting on your classes.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
          <button
            onClick={() => navigate("/chat/activity")}
            className="flex flex-col items-center justify-center text-center bg-[#FEFCE8] border-4 border-[#000000] p-8 shadow-[8px_8px_0px_0px_#000000] hover:shadow-[4px_4px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all rounded-2xl h-64"
          >
            <span className="font-extrabold text-3xl mb-4 text-[#000000]">Activity</span>
            <span className="text-[#000000] font-medium text-base">Generate engaging classroom activities instantly</span>
          </button>
          
          <button
            onClick={() => navigate("/chat/qna")}
            className="flex flex-col items-center justify-center text-center bg-[#F0FDFA] border-4 border-[#000000] p-8 shadow-[8px_8px_0px_0px_#000000] hover:shadow-[4px_4px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all rounded-2xl h-64"
          >
            <span className="font-extrabold text-3xl mb-4 text-[#000000]">Q&A</span>
            <span className="text-[#000000] font-medium text-base">Ask any question and get expert teacher guidance</span>
          </button>
          
          <button
            onClick={() => navigate("/chat/module-builder")}
            className="flex flex-col items-center justify-center text-center bg-[#FAF5FF] border-4 border-[#000000] p-8 shadow-[8px_8px_0px_0px_#000000] hover:shadow-[4px_4px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all rounded-2xl h-64"
          >
            <span className="font-extrabold text-3xl mb-4 text-[#000000]">Module Builder</span>
            <span className="text-[#000000] font-medium text-base">Create complete lesson modules and slides</span>
          </button>
        </div>
      </div>

      {false && (
        <div className="old-sections">
          {/* Top Section - Two Equal Blocks */}
          <section className="flex flex-col md:flex-row w-full">
            {/* Left Block - Yellow */}
            <div className="w-full md:w-1/2 bg-[#FDE047] border-2 border-[#000000] p-4 md:p-8 flex items-center grid-texture">
              <p className="text-[#000000] text-base md:text-2xl">
                AI-powered classroom companion that supports teachers
                before class, during class, and after class — with real-time listening,
                instant crisis help, smart lesson planning, and multilingual support.
              </p>
            </div>

            {/* Right Block - Light Purple */}
            <div className="w-full md:w-1/2 bg-[#DDD6FE] border-2 border-[#000000] p-4 md:p-8 flex flex-col md:flex-row items-center gap-4 md:gap-8 grid-texture">
              <img
                src="/fav_icon_chanakya.png"
                alt="Chanakya Character"
                className="w-48 h-48 md:w-71 md:h-71 object-contain"
              />
              <p className="text-[#000000] font-extrabold uppercase text-3xl md:text-5xl lg:text-6xl tracking-wide">
                <RotatingText
                  texts={["ASSIST", "COACH", "GUIDE", "FRIEND"]}
                  mainClassName="px-3 md:px-4 bg-[#000000] text-[#DDD6FE] overflow-hidden py-1 md:py-2 rounded-lg inline-flex"
                  staggerFrom="first"
                  initial={{ y: "100%" }}
                  animate={{ y: 0 }}
                  exit={{ y: "-120%" }}
                  staggerDuration={0.04}
                  splitLevelClassName="overflow-hidden"
                  transition={{ type: "spring", damping: 30, stiffness: 400 }}
                  rotationInterval={2200}
                />
              </p>
            </div>
          </section>

          {/* Mode Selection Section - Only visible when logged in */}
          {isAuthenticated && (
            <section className="w-full bg-[#FCF4AC] border-2 border-[#000000] p-8 md:p-16 grid-texture">
              <div className="max-w-7xl mx-auto">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
                  <button
                    onClick={() => navigate("/chat/activity")}
                    className="bg-white border-2 border-[#000000] px-4 md:px-6 py-3 md:py-4 text-black font-bold text-sm md:text-base shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all"
                  >
                    Activity
                  </button>
                  <button
                    onClick={() => navigate("/chat/qna")}
                    className="bg-white border-2 border-[#000000] px-4 md:px-6 py-3 md:py-4 text-black font-bold text-sm md:text-base shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all"
                  >
                    Q&A
                  </button>
                  <button
                    onClick={() => navigate("/chat/module-builder")}
                    className="bg-white border-2 border-[#000000] px-4 md:px-6 py-3 md:py-4 text-black font-bold text-sm md:text-base shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all"
                  >
                    Module Builder
                  </button>
                </div>
              </div>
            </section>
          )}

          {/* Bottom Section - Full Width */}
          <section className="w-full bg-[#A1D7FD] border-2 border-[#000000] p-2 md:p-4 flex flex-col md:flex-row items-center gap-4 md:gap-8 grid-texture">
            <img
              src="/chan_winking.png"
              alt="Chanakya Character"
              className="w-48 h-48 md:w-72 md:h-72 object-contain"
            />
            <div>
              <h2 className="text-3xl md:text-5xl font-bold text-[#000000] mb-1">
                <span className="text-[#000000]">NOT</span> JUST AN ASSISTANT.
              </h2>
              <p className="text-[#000000] text-base md:text-2xl">
                A continuous support system for teachers -
                helping them plan better, handle live classrooms,
                and reflect on teaching without waiting for a mentor visit.
              </p>
            </div>
          </section>

          {/* Feature Buttons Section */}
          <section className="w-full bg-[#FCF4AC] border-2 border-[#000000] p-8 md:p-16 grid-texture">
            <div className="max-w-7xl mx-auto">
              <h2
                className="text-3xl md:text-5xl font-bold text-[#000000] mb-8 md:mb-12 text-center"
                style={{ fontFamily: "TT Firs Neue, sans-serif", fontWeight: 700 }}
              >
                Built to Support Teachers{" "}
                <RotatingText
                  texts={["Before Class", "During Class", "After Class", "Anytime"]}
                  mainClassName="px-3 md:px-4 bg-[#000000] text-[#FCF4AC] overflow-hidden py-1 md:py-2 rounded-lg inline-flex"
                  staggerFrom="first"
                  initial={{ y: "100%" }}
                  animate={{ y: 0 }}
                  exit={{ y: "-120%" }}
                  staggerDuration={0.04}
                  splitLevelClassName="overflow-hidden"
                  transition={{ type: "spring", damping: 30, stiffness: 400 }}
                  rotationInterval={2200}
                />
              </h2>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 mb-6 md:mb-8">
                <button className="bg-white border-2 border-[#000000] px-4 md:px-6 py-3 md:py-4 text-black font-bold text-sm md:text-base shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all">
                  Crisis-Handling Mode
                </button>
                <button className="bg-white border-2 border-[#000000] px-4 md:px-6 py-3 md:py-4 text-black font-bold text-sm md:text-base shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all">
                  Active-Listening Mode
                </button>
                <button className="bg-white border-2 border-[#000000] px-4 md:px-6 py-3 md:py-4 text-black font-bold text-sm md:text-base shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all">
                  Pre-class-Module Mode
                </button>
                <button className="bg-white border-2 border-[#000000] px-4 md:px-6 py-3 md:py-4 text-black font-bold text-sm md:text-base shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all">
                  Activity-Generator
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 max-w-4xl mx-auto">
                <button className="bg-white border-2 border-[#000000] px-4 md:px-6 py-3 md:py-4 text-black font-bold text-sm md:text-base shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all">
                  Post-class Feedback
                </button>
                <button className="bg-white border-2 border-[#000000] px-4 md:px-6 py-3 md:py-4 text-black font-bold text-sm md:text-base shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all">
                  Multilingual Support
                </button>
                <button className="bg-white border-2 border-[#000000] px-4 md:px-6 py-3 md:py-4 text-black font-bold text-sm md:text-base shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all">
                  Deep thinking Mode
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 max-w-2xl mx-auto mt-6 md:mt-8">
                <button
                  onClick={() => navigate("/personalized-support")}
                  className="bg-white border-2 border-[#000000] px-4 md:px-6 py-3 md:py-4 text-black font-bold text-sm md:text-base shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all"
                >
                  Personalized-Q/A Generator
                </button>
                <button
                  onClick={() => alert("Offline Mode Coming Soon!")}
                  className="bg-white border-2 border-[#000000] px-4 md:px-6 py-3 md:py-4 text-black font-bold text-sm md:text-base shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all"
                >
                  Offline Mode
                </button>
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

export default Landing;
