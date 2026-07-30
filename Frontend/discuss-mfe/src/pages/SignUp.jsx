import { useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../context/AuthContext";
import { authAPI } from "../utils/apiClient";

function SignUp() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    // Step 1
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    // Step 2
    classesHandled: [],
    subjects: [],
    schoolLocation: "",
    preferredLanguage: [],
  });

  const [subjectInput, setSubjectInput] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [classInput, setClassInput] = useState("");
  const [showClassSuggestions, setShowClassSuggestions] = useState(false);

  const knownSubjects = [
    "Mathematics",
    "Science",
    "English",
    "Hindi",
    "Social Studies",
    "Physics",
    "Chemistry",
    "Biology",
    "History",
    "Geography",
    "Computer Science",
    "Physical Education",
    "Art",
    "Music",
    "Telugu",
    "Tamil",
    "Kannada",
    "Malayalam",
    "Sanskrit",
    "Economics",
    "Political Science",
    "Commerce",
    "Accountancy",
  ];

  const knownClasses = [
    "Class 1",
    "Class 2",
    "Class 3",
    "Class 4",
    "Class 5",
    "Class 6",
    "Class 7",
    "Class 8",
    "Class 9",
    "Class 10",
    "Class 11",
    "Class 12",
  ];

  const knownLanguages = [
    "English",
    "Hindi",
    "Telugu",
    "Tamil",
    "Kannada",
    "Malayalam",
    "Sanskrit",
    "Urdu",
    "Bengali",
    "Marathi",
    "Gujarati",
    "Odia",
    "Punjabi",
  ];

  const [languageInput, setLanguageInput] = useState("");
  const [showLanguageSuggestions, setShowLanguageSuggestions] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubjectInputChange = (e) => {
    const value = e.target.value;
    setSubjectInput(value);
    setShowSuggestions(value.length > 0);
  };

  const handleClassInputChange = (e) => {
    const value = e.target.value;
    setClassInput(value);
    setShowClassSuggestions(value.length > 0);
  };

  const addClass = (className) => {
    if (!formData.classesHandled.includes(className)) {
      setFormData({
        ...formData,
        classesHandled: [...formData.classesHandled, className],
      });
    }
    setClassInput("");
    setShowClassSuggestions(false);
  };

  const removeClass = (classToRemove) => {
    setFormData({
      ...formData,
      classesHandled: formData.classesHandled.filter(
        (c) => c !== classToRemove
      ),
    });
  };

  const handleClassKeyDown = (e) => {
    if (e.key === "Enter" && classInput.trim()) {
      e.preventDefault();
      const trimmedInput = classInput.trim();
      // Only add if it matches a known class or if it's a valid class format
      if (
        knownClasses.includes(trimmedInput) ||
        /^Class \d+$/.test(trimmedInput)
      ) {
        addClass(trimmedInput);
      }
    }
  };

  const addSubject = (subject) => {
    if (!formData.subjects.includes(subject)) {
      setFormData({
        ...formData,
        subjects: [...formData.subjects, subject],
      });
    }
    setSubjectInput("");
    setShowSuggestions(false);
  };

  const addLanguage = (language) => {
    if (!formData.preferredLanguage.includes(language)) {
      setFormData({
        ...formData,
        preferredLanguage: [...formData.preferredLanguage, language],
      });
    }
    setLanguageInput("");
    setShowLanguageSuggestions(false);
  };

  const removeLanguage = (languageToRemove) => {
    setFormData({
      ...formData,
      preferredLanguage: formData.preferredLanguage.filter(
        (l) => l !== languageToRemove
      ),
    });
  };

  const handleLanguageInputChange = (e) => {
    const value = e.target.value;
    setLanguageInput(value);
    setShowLanguageSuggestions(value.length > 0);
  };

  const handleLanguageKeyDown = (e) => {
    if (e.key === "Enter" && languageInput.trim()) {
      e.preventDefault();
      const trimmedInput = languageInput.trim();
      addLanguage(trimmedInput);
    }
  };

  const removeSubject = (subjectToRemove) => {
    setFormData({
      ...formData,
      subjects: formData.subjects.filter((s) => s !== subjectToRemove),
    });
  };

  const handleSubjectKeyDown = (e) => {
    if (e.key === "Enter" && subjectInput.trim()) {
      e.preventDefault();
      const trimmedInput = subjectInput.trim();
      // Only add if it matches a known subject (allow custom subjects too)
      if (trimmedInput.length > 0) {
        addSubject(trimmedInput);
      }
    }
  };

  const filteredSuggestions = knownSubjects.filter(
    (subject) =>
      subject.toLowerCase().includes(subjectInput.toLowerCase()) &&
      !formData.subjects.includes(subject)
  );

  const filteredClassSuggestions = knownClasses.filter(
    (className) =>
      className.toLowerCase().includes(classInput.toLowerCase()) &&
      !formData.classesHandled.includes(className)
  );
  const filteredLanguageSuggestions = knownLanguages.filter(
    (lang) =>
      lang.toLowerCase().includes(languageInput.toLowerCase()) &&
      !formData.preferredLanguage.includes(lang)
  );

  const handleStep1Submit = (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      toast.error("Passwords do not match!");
      return;
    }
    setStep(2);
  };

  const handleStep2Submit = async (e) => {
    e.preventDefault();
    if (formData.classesHandled.length === 0) {
      toast.error("Please add at least one class!");
      return;
    }
    if (formData.subjects.length === 0) {
      toast.error("Please add at least one subject!");
      return;
    }
    if (formData.preferredLanguage.length === 0) {
      toast.error("Please select at least one preferred teaching language!");
      return;
    }

    // Submit to backend using axios
    setIsLoading(true);
    try {
      const response = await authAPI.signup({
        name: formData.name,
        email: formData.email,
        password: formData.password,
        confirmPassword: formData.confirmPassword,
        classesHandled: formData.classesHandled,
        subjects: formData.subjects,
        schoolLocation: formData.schoolLocation,
        preferredLanguage: formData.preferredLanguage,
      });

      const { data } = response;

      // Store token in localStorage and context
      if (data.token && data.user) {
        login(data.user, data.token);
      }

      toast.success("Signed up successfully!");

      // Redirect to dashboard after brief delay
      setTimeout(() => {
        navigate("/");
      }, 1000);
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "An error occurred. Please check your connection and try again.";
      toast.error(errorMessage);
      console.error("Signup error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#EFF0C6] grid-texture flex items-center justify-center p-4 md:p-8">
      <div className="w-full max-w-6xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-8">
          {/* Step 1: Personal Details */}
          <div
            className={`bg-[#FCF4AC] border-2 border-[#000000] p-6 md:p-8 ${
              step === 1 ? "" : "opacity-60"
            }`}
          >
            <h2
              className="text-3xl md:text-4xl font-bold text-[#000000] mb-6"
              style={{
                fontFamily: "TT Firs Neue, sans-serif",
                fontWeight: 700,
              }}
            >
              Let's get you started
            </h2>
            <h3 className="text-xl md:text-2xl font-bold text-[#000000] mb-4">
              Personal Details
            </h3>

            <form onSubmit={handleStep1Submit}>
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-bold text-[#000000] mb-2">
                    Name
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    className="w-full px-4 py-3 bg-white border-2 border-[#000000] text-[#000000] focus:outline-none focus:ring-2 focus:ring-[#000000]"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-[#000000] mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="w-full px-4 py-3 bg-white border-2 border-[#000000] text-[#000000] focus:outline-none focus:ring-2 focus:ring-[#000000]"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-[#000000] mb-2">
                    Password
                  </label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    className="w-full px-4 py-3 bg-white border-2 border-[#000000] text-[#000000] focus:outline-none focus:ring-2 focus:ring-[#000000]"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-[#000000] mb-2">
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className="w-full px-4 py-3 bg-white border-2 border-[#000000] text-[#000000] focus:outline-none focus:ring-2 focus:ring-[#000000]"
                    required
                  />
                </div>
              </div>
              <button
                type="submit"
                className="w-full bg-[#FDE047] border-2 border-[#000000] font-bold text-[#000000] px-6 py-3 shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all"
              >
                Next
              </button>
            </form>
          </div>

          {/* Step 2: Generic Details */}
          <div
            className={`bg-[#F99DA8] border-2 border-[#000000] p-6 md:p-8 ${
              step === 2 ? "" : "opacity-60"
            }`}
          >
            <h2
              className="text-3xl md:text-4xl font-bold text-[#000000] mb-6"
              style={{
                fontFamily: "TT Firs Neue, sans-serif",
                fontWeight: 700,
              }}
            >
              Step-2 :
            </h2>
            <h3 className="text-xl md:text-2xl font-bold text-[#000000] mb-4">
              Generic Details
            </h3>

            <form onSubmit={handleStep2Submit}>
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-bold text-[#000000] mb-2">
                    Classes Handled
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={classInput}
                      onChange={handleClassInputChange}
                      onKeyDown={handleClassKeyDown}
                      placeholder="Type to search classes..."
                      className="w-full px-4 py-3 bg-white border-2 border-[#000000] text-[#000000] focus:outline-none focus:ring-2 focus:ring-[#000000]"
                      disabled={step !== 2}
                      onFocus={() =>
                        classInput && setShowClassSuggestions(true)
                      }
                      onBlur={() =>
                        setTimeout(() => setShowClassSuggestions(false), 200)
                      }
                    />
                    {showClassSuggestions &&
                      filteredClassSuggestions.length > 0 &&
                      step === 2 && (
                        <div className="absolute z-10 w-full mt-1 bg-white border-2 border-[#000000] max-h-48 overflow-y-auto">
                          {filteredClassSuggestions.map((className) => (
                            <div
                              key={className}
                              onMouseDown={(e) => {
                                e.preventDefault();
                                addClass(className);
                              }}
                              className="px-4 py-2 hover:bg-[#E8D5FF] cursor-pointer text-[#000000] border-b border-[#000000] last:border-b-0"
                            >
                              {className}
                            </div>
                          ))}
                        </div>
                      )}
                  </div>
                  {formData.classesHandled.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {formData.classesHandled.map((className, index) => (
                        <div
                          key={`${className}-${index}`}
                          className="bg-[#E8D5FF] border-2 border-[#000000] px-3 py-1.5 flex items-center gap-2 shadow-[2px_2px_0px_0px_#000000]"
                        >
                          <span className="text-sm font-bold text-[#000000] whitespace-nowrap">
                            {className}
                          </span>
                          <button
                            type="button"
                            onClick={() => removeClass(className)}
                            className="bg-white border-2 border-[#000000] text-[#000000] font-bold text-lg leading-none w-5 h-5 flex items-center justify-center rounded-full hover:text-red-600 disabled:opacity-50"
                            disabled={step !== 2}
                            aria-label={`Remove ${className}`}
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-bold text-[#000000] mb-2">
                    Subjects
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={subjectInput}
                      onChange={handleSubjectInputChange}
                      onKeyDown={handleSubjectKeyDown}
                      placeholder="Type to search subjects..."
                      className="w-full px-4 py-3 bg-white border-2 border-[#000000] text-[#000000] focus:outline-none focus:ring-2 focus:ring-[#000000]"
                      disabled={step !== 2}
                      onFocus={() => subjectInput && setShowSuggestions(true)}
                      onBlur={() =>
                        setTimeout(() => setShowSuggestions(false), 200)
                      }
                    />
                    {showSuggestions &&
                      filteredSuggestions.length > 0 &&
                      step === 2 && (
                        <div className="absolute z-10 w-full mt-1 bg-white border-2 border-[#000000] max-h-48 overflow-y-auto">
                          {filteredSuggestions.map((subject) => (
                            <div
                              key={subject}
                              onMouseDown={(e) => {
                                e.preventDefault();
                                addSubject(subject);
                              }}
                              className="px-4 py-2 hover:bg-[#D4F1C5] cursor-pointer text-[#000000] border-b border-[#000000] last:border-b-0"
                            >
                              {subject}
                            </div>
                          ))}
                        </div>
                      )}
                  </div>
                  {formData.subjects.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {formData.subjects.map((subject, index) => (
                        <div
                          key={`${subject}-${index}`}
                          className="bg-[#D4F1C5] border-2 border-[#000000] px-3 py-1.5 flex items-center gap-2 shadow-[2px_2px_0px_0px_#000000]"
                        >
                          <span className="text-sm font-bold text-[#000000] whitespace-nowrap">
                            {subject}
                          </span>
                          <button
                            type="button"
                            onClick={() => removeSubject(subject)}
                            className="bg-white border-2 border-[#000000] text-[#000000] font-bold text-lg leading-none w-5 h-5 flex items-center justify-center rounded-full hover:text-red-600 disabled:opacity-50"
                            disabled={step !== 2}
                            aria-label={`Remove ${subject}`}
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-bold text-[#000000] mb-2">
                    School Location
                  </label>
                  <input
                    type="text"
                    name="schoolLocation"
                    value={formData.schoolLocation}
                    onChange={handleChange}
                    placeholder="Enter school location"
                    className="w-full px-4 py-3 bg-white border-2 border-[#000000] text-[#000000] focus:outline-none focus:ring-2 focus:ring-[#000000]"
                    required
                    disabled={step !== 2}
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-[#000000] mb-2">
                    Language you prefer for teaching
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={languageInput}
                      onChange={handleLanguageInputChange}
                      onKeyDown={handleLanguageKeyDown}
                      placeholder="Type to search languages..."
                      className="w-full px-4 py-3 bg-white border-2 border-[#000000] text-[#000000] focus:outline-none focus:ring-2 focus:ring-[#000000]"
                      disabled={step !== 2}
                      onFocus={() =>
                        languageInput && setShowLanguageSuggestions(true)
                      }
                      onBlur={() =>
                        setTimeout(() => setShowLanguageSuggestions(false), 200)
                      }
                    />
                    {showLanguageSuggestions &&
                      filteredLanguageSuggestions.length > 0 &&
                      step === 2 && (
                        <div className="absolute z-10 w-full mt-1 bg-white border-2 border-[#000000] max-h-48 overflow-y-auto">
                          {filteredLanguageSuggestions.map((lang) => (
                            <div
                              key={lang}
                              onMouseDown={(e) => {
                                e.preventDefault();
                                addLanguage(lang);
                              }}
                              className="px-4 py-2 hover:bg-[#D4F1C5] cursor-pointer text-[#000000] border-b border-[#000000] last:border-b-0"
                            >
                              {lang}
                            </div>
                          ))}
                        </div>
                      )}
                  </div>
                  {formData.preferredLanguage.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {formData.preferredLanguage.map((lang, index) => (
                        <div
                          key={`${lang}-${index}`}
                          className="bg-[#E8D5FF] border-2 border-[#000000] px-3 py-1.5 flex items-center gap-2 shadow-[2px_2px_0px_0px_#000000]"
                        >
                          <span className="text-sm font-bold text-[#000000] whitespace-nowrap">
                            {lang}
                          </span>
                          <button
                            type="button"
                            onClick={() => removeLanguage(lang)}
                            className="bg-white border-2 border-[#000000] text-[#000000] font-bold text-lg leading-none w-5 h-5 flex items-center justify-center rounded-full hover:text-red-600 disabled:opacity-50"
                            disabled={step !== 2}
                            aria-label={`Remove ${lang}`}
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="flex-1 bg-white border-2 border-[#000000] font-bold text-[#000000] px-6 py-3 shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all"
                  disabled={step !== 2}
                >
                  Back
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-[#FDE047] border-2 border-[#000000] font-bold text-[#000000] px-6 py-3 shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={step !== 2 || isLoading}
                >
                  {isLoading ? "Signing up..." : "Sign Up"}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Happy Chanakya Character
        <div className="flex justify-center mt-8">
          <img
            src="/happy_chanakya.png"
            alt="Happy Chanakya Character"
            className="w-32 h-32 md:w-48 md:h-48 object-contain"
          />
        </div> */}
      </div>
    </div>
  );
}

export default SignUp;
