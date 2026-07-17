import { useState, useEffect } from "react";
import { moduleAPI } from "../../utils/moduleApi";

/**
 * TopicSelector - Hierarchical topic selection component
 * Allows teachers to select class, subject, and topic for lesson generation
 * Requirements: 1.1, 1.2, 1.3, 1.5
 */
function TopicSelector({ onSelectionComplete, disabled = false }) {
  // Selection state
  const [selectedClass, setSelectedClass] = useState("");
  const [selectedSubject, setSelectedSubject] = useState("");
  const [selectedTopic, setSelectedTopic] = useState("");

  // Data state
  const [classes, setClasses] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [topics, setTopics] = useState([]);

  // Loading states
  const [loadingClasses, setLoadingClasses] = useState(false);
  const [loadingSubjects, setLoadingSubjects] = useState(false);
  const [loadingTopics, setLoadingTopics] = useState(false);

  // Error states
  const [error, setError] = useState(null);

  // Fetch available classes on mount
  useEffect(() => {
    fetchClasses();
  }, []);

  // Fetch subjects when class changes
  useEffect(() => {
    if (selectedClass) {
      fetchSubjects(selectedClass);
      setSelectedSubject("");
      setSelectedTopic("");
      setTopics([]);
    } else {
      setSubjects([]);
      setTopics([]);
    }
  }, [selectedClass]);

  // Fetch topics when subject changes
  useEffect(() => {
    if (selectedClass && selectedSubject) {
      fetchTopics(selectedClass, selectedSubject);
      setSelectedTopic("");
    } else {
      setTopics([]);
    }
  }, [selectedSubject]);

  // Notify parent when selection is complete
  useEffect(() => {
    if (selectedClass && selectedSubject && selectedTopic) {
      onSelectionComplete?.({
        className: selectedClass,
        subject: selectedSubject,
        topic: selectedTopic,
      });
    }
  }, [selectedClass, selectedSubject, selectedTopic, onSelectionComplete]);

  const fetchClasses = async () => {
    setLoadingClasses(true);
    setError(null);
    try {
      const response = await moduleAPI.getClasses();
      setClasses(response.data.classes || []);
    } catch (err) {
      setError("Failed to load classes. Please try again.");
      console.error("Error fetching classes:", err);
    } finally {
      setLoadingClasses(false);
    }
  };

  const fetchSubjects = async (className) => {
    setLoadingSubjects(true);
    setError(null);
    try {
      const response = await moduleAPI.getSubjects(className);
      setSubjects(response.data.subjects || []);
    } catch (err) {
      setError("Failed to load subjects. Please try again.");
      console.error("Error fetching subjects:", err);
    } finally {
      setLoadingSubjects(false);
    }
  };

  const fetchTopics = async (className, subject) => {
    setLoadingTopics(true);
    setError(null);
    try {
      const response = await moduleAPI.getTopics(className, subject);
      setTopics(response.data.topics || []);
    } catch (err) {
      if (err.response?.status === 404) {
        setError("No content available for this combination.");
      } else {
        setError("Failed to load topics. Please try again.");
      }
      console.error("Error fetching topics:", err);
    } finally {
      setLoadingTopics(false);
    }
  };

  const handleClassChange = (e) => {
    setSelectedClass(e.target.value);
  };

  const handleSubjectChange = (e) => {
    setSelectedSubject(e.target.value);
  };

  const handleTopicChange = (e) => {
    setSelectedTopic(e.target.value);
  };

  const isSelectionComplete = selectedClass && selectedSubject && selectedTopic;

  return (
    <div className="bg-white border-2 border-[#000000] rounded-lg p-6 shadow-[4px_4px_0px_0px_#000000]">
      <h2 className="text-xl font-bold text-[#000000] mb-4 flex items-center gap-2">
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
            d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
        Select Topic
      </h2>

      {error && (
        <div className="mb-4 p-3 bg-[#F99DA8] border-2 border-[#000000] rounded-lg text-sm text-[#000000]">
          {error}
        </div>
      )}

      <div className="space-y-4">
        {/* Class Dropdown */}
        <div>
          <label className="block text-sm font-bold text-[#000000] mb-2">
            Class
          </label>
          <div className="relative">
            <select
              value={selectedClass}
              onChange={handleClassChange}
              disabled={disabled || loadingClasses}
              className="w-full p-3 border-2 border-[#000000] rounded-lg bg-white text-[#000000] font-medium appearance-none cursor-pointer disabled:bg-gray-100 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-[#FDE047]"
            >
              <option value="">
                {loadingClasses ? "Loading classes..." : "Select a class"}
              </option>
              {classes.map((cls) => (
                <option key={cls} value={cls}>
                  {cls.replace("_", " ")}
                </option>
              ))}
            </select>
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
              {loadingClasses ? (
                <LoadingSpinner />
              ) : (
                <ChevronDownIcon />
              )}
            </div>
          </div>
        </div>

        {/* Subject Dropdown */}
        <div>
          <label className="block text-sm font-bold text-[#000000] mb-2">
            Subject
          </label>
          <div className="relative">
            <select
              value={selectedSubject}
              onChange={handleSubjectChange}
              disabled={disabled || !selectedClass || loadingSubjects}
              className="w-full p-3 border-2 border-[#000000] rounded-lg bg-white text-[#000000] font-medium appearance-none cursor-pointer disabled:bg-gray-100 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-[#FDE047]"
            >
              <option value="">
                {loadingSubjects 
                  ? "Loading subjects..." 
                  : !selectedClass 
                    ? "Select a class first" 
                    : "Select a subject"}
              </option>
              {subjects.map((subject) => (
                <option key={subject} value={subject}>
                  {subject.replace(/_/g, " ")}
                </option>
              ))}
            </select>
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
              {loadingSubjects ? (
                <LoadingSpinner />
              ) : (
                <ChevronDownIcon />
              )}
            </div>
          </div>
        </div>

        {/* Topic Dropdown */}
        <div>
          <label className="block text-sm font-bold text-[#000000] mb-2">
            Topic
          </label>
          <div className="relative">
            <select
              value={selectedTopic}
              onChange={handleTopicChange}
              disabled={disabled || !selectedSubject || loadingTopics}
              className="w-full p-3 border-2 border-[#000000] rounded-lg bg-white text-[#000000] font-medium appearance-none cursor-pointer disabled:bg-gray-100 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-[#FDE047]"
            >
              <option value="">
                {loadingTopics 
                  ? "Loading topics..." 
                  : !selectedSubject 
                    ? "Select a subject first" 
                    : topics.length === 0 
                      ? "No topics available"
                      : "Select a topic"}
              </option>
              {topics.map((topic) => (
                <option key={topic.topic_name} value={topic.topic_name}>
                  {topic.chapter_number ? `Ch ${topic.chapter_number}: ` : ""}
                  {topic.topic_name}
                  {topic.content_count ? ` (${topic.content_count} sections)` : ""}
                </option>
              ))}
            </select>
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
              {loadingTopics ? (
                <LoadingSpinner />
              ) : (
                <ChevronDownIcon />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Selection Summary */}
      {isSelectionComplete && (
        <div className="mt-4 p-3 bg-[#D4F1C5] border-2 border-[#000000] rounded-lg">
          <p className="text-sm font-medium text-[#000000]">
            Ready to generate lesson for:
          </p>
          <p className="text-sm text-[#000000] mt-1">
            <span className="font-bold">{selectedClass.replace("_", " ")}</span>
            {" → "}
            <span className="font-bold">{selectedSubject.replace(/_/g, " ")}</span>
            {" → "}
            <span className="font-bold">{selectedTopic}</span>
          </p>
        </div>
      )}
    </div>
  );
}

// Helper Components
function LoadingSpinner() {
  return (
    <svg className="w-5 h-5 animate-spin text-[#000000]" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
  );
}

function ChevronDownIcon() {
  return (
    <svg className="w-5 h-5 text-[#000000]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  );
}

export default TopicSelector;
