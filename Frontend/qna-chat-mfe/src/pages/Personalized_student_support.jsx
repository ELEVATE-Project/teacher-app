import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { classesApi, studentsApi } from "../api/dashboardApi";
import StudentCard from "../components/StudentCard";
import StarRating from "../components/StarRating";
import ClassDashboard from "../components/ClassDashboard";

function Personalized_student_support() {
  const navigate = useNavigate();
  const [classes, setClasses] = useState([]);
  const [selectedClass, setSelectedClass] = useState(null);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showClassForm, setShowClassForm] = useState(false);
  const [showStudentForm, setShowStudentForm] = useState(false);
  const [editingStudent, setEditingStudent] = useState(null);
  const [activeTab, setActiveTab] = useState("dashboard"); // 'dashboard' or 'students'

  // Form states
  const [className, setClassName] = useState("");
  const [classSubject, setClassSubject] = useState("");
  const [studentName, setStudentName] = useState("");
  const [studentLevel, setStudentLevel] = useState("medium");
  const [studentConfidence, setStudentConfidence] = useState(2.5);

  useEffect(() => {
    loadClasses();
  }, []);

  useEffect(() => {
    if (selectedClass) {
      loadStudents(selectedClass.id);
    }
  }, [selectedClass]);

  const loadClasses = async () => {
    try {
      const data = await classesApi.getAll();
      // Backend returns { classes: [...] }
      setClasses(data.classes || []);
    } catch (error) {
      console.error("Failed to load classes:", error);
      // Show user-friendly error
      alert(
        "Failed to load classes. Make sure the backend is running on http://localhost:3000"
      );
    } finally {
      setLoading(false);
    }
  };

  const loadStudents = async (classId) => {
    try {
      const data = await studentsApi.getByClass(classId);
      // Backend returns List[StudentResponse] directly
      setStudents(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Failed to load students:", error);
      setStudents([]);
    }
  };

  const handleCreateClass = async (e) => {
    e.preventDefault();
    if (!className.trim() || !classSubject.trim()) return;

    try {
      const newClass = await classesApi.create({
        name: className.trim(),
        subject: classSubject.trim(),
      });
      // Backend returns ClassResponse directly
      // Reload classes to get updated student counts
      await loadClasses();
      // Find and select the newly created class
      const createdClass =
        (await classesApi.getAll()).classes.find((c) => c.id === newClass.id) ||
        newClass;
      setSelectedClass(createdClass);
      setClassName("");
      setClassSubject("");
      setShowClassForm(false);
    } catch (error) {
      console.error("Failed to create class:", error);
      alert("Failed to create class. Make sure the backend is running.");
    }
  };

  const handleDeleteClass = async (classId) => {
    if (!window.confirm("Delete this class and all its students?")) return;

    try {
      await classesApi.delete(classId);
      // Reload classes to get updated list
      await loadClasses();
      if (selectedClass?.id === classId) {
        setSelectedClass(null);
        setStudents([]);
      }
    } catch (error) {
      console.error("Failed to delete class:", error);
      alert("Failed to delete class. Make sure the backend is running.");
    }
  };

  const handleAddStudent = async (e) => {
    e.preventDefault();
    if (!studentName.trim() || !selectedClass) return;

    try {
      const newStudent = await studentsApi.create(selectedClass.id, {
        name: studentName.trim(),
        level: studentLevel,
        confidence: studentConfidence,
      });
      setStudents([...students, newStudent]);
      // Reload classes to update student count
      await loadClasses();
      // Update selected class with new student count
      const updatedClasses = await classesApi.getAll();
      const updatedClass = updatedClasses.classes.find(
        (c) => c.id === selectedClass.id
      );
      if (updatedClass) {
        setSelectedClass(updatedClass);
      }
      resetStudentForm();
    } catch (error) {
      console.error("Failed to add student:", error);
      alert("Failed to add student. Make sure the backend is running.");
    }
  };

  const handleUpdateStudent = async (e) => {
    e.preventDefault();
    if (!editingStudent) return;

    try {
      const updated = await studentsApi.update(editingStudent.id, {
        name: studentName.trim(),
        level: studentLevel,
        confidence: studentConfidence,
      });
      setStudents(students.map((s) => (s.id === updated.id ? updated : s)));
      resetStudentForm();
    } catch (error) {
      console.error("Failed to update student:", error);
    }
  };

  const handleDeleteStudent = async (studentId) => {
    if (!window.confirm("Delete this student?")) return;

    try {
      await studentsApi.delete(studentId);
      setStudents(students.filter((s) => s.id !== studentId));
      // Reload classes to update student count
      await loadClasses();
      // Update selected class with new student count
      if (selectedClass) {
        const updatedClasses = await classesApi.getAll();
        const updatedClass = updatedClasses.classes.find(
          (c) => c.id === selectedClass.id
        );
        if (updatedClass) {
          setSelectedClass(updatedClass);
        }
      }
    } catch (error) {
      console.error("Failed to delete student:", error);
      alert("Failed to delete student. Make sure the backend is running.");
    }
  };

  const startEditStudent = (student) => {
    setEditingStudent(student);
    setStudentName(student.name);
    setStudentLevel(student.level);
    setStudentConfidence(student.confidence);
    setShowStudentForm(true);
  };

  const resetStudentForm = () => {
    setStudentName("");
    setStudentLevel("medium");
    setStudentConfidence(2.5);
    setEditingStudent(null);
    setShowStudentForm(false);
  };

  const handleStartSession = () => {
    if (selectedClass && students.length > 0) {
      navigate(`/questions/${selectedClass.id}`);
    } else {
      alert(
        "Please add at least one student to the class before starting a session."
      );
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#EFF0C6] grid-texture flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#000000] mx-auto mb-4"></div>
          <p className="text-[#000000] font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#EFF0C6] grid-texture">
      <div className="container mx-auto px-4 md:px-8 py-6 md:py-10">
        {/* Page Header */}
        <div className="mb-8">
          <h1
            className="text-3xl md:text-4xl font-bold text-[#000000] mb-2"
            style={{
              fontFamily: "TT Firs Neue, sans-serif",
              fontWeight: 700,
            }}
          >
            Classroom Setup
          </h1>
          <p className="text-lg text-[#000000] opacity-80">
            Create your class and add students to get started
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[350px_1fr] gap-6 md:gap-8">
          {/* Classes Panel */}
          <div className="bg-[#DDD6FE] border-2 border-[#000000] rounded-lg flex flex-col overflow-hidden">
            <div className="p-4 md:p-6 border-b-2 border-[#000000] flex items-center justify-between gap-4 flex-wrap">
              <h2
                className="text-xl md:text-2xl font-bold text-[#000000]"
                style={{
                  fontFamily: "TT Firs Neue, sans-serif",
                  fontWeight: 700,
                }}
              >
                Your Classes
              </h2>
              <button
                className="px-4 py-2 bg-[#EFF0C6] border-2 border-[#000000] rounded-lg text-sm font-medium text-[#000000] hover:bg-[#E8E9B0] transition-colors flex items-center gap-2"
                onClick={() => setShowClassForm(true)}
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
                Add Class
              </button>
            </div>

            {showClassForm && (
              <form
                className="m-4 bg-white border-2 border-[#000000] rounded-lg p-4 md:p-6 animate-fade-in"
                onSubmit={handleCreateClass}
              >
                <h3 className="text-lg font-bold text-[#000000] mb-4">
                  New Class
                </h3>
                <div className="mb-4">
                  <label className="block text-sm font-bold text-[#000000] mb-2">
                    Class Name
                  </label>
                  <input
                    type="text"
                    value={className}
                    onChange={(e) => setClassName(e.target.value)}
                    placeholder="e.g., Class 8-A"
                    className="w-full px-4 py-3 bg-white border-2 border-[#000000] text-[#000000] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#000000]"
                    autoFocus
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-bold text-[#000000] mb-2">
                    Subject
                  </label>
                  <input
                    type="text"
                    value={classSubject}
                    onChange={(e) => setClassSubject(e.target.value)}
                    placeholder="e.g., Science"
                    className="w-full px-4 py-3 bg-white border-2 border-[#000000] text-[#000000] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#000000]"
                  />
                </div>
                <div className="flex gap-2 justify-end">
                  <button
                    type="button"
                    className="px-4 py-2 bg-white border-2 border-[#000000] rounded-lg text-sm font-medium text-[#000000] hover:bg-gray-50 transition-colors"
                    onClick={() => setShowClassForm(false)}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-[#EFF0C6] border-2 border-[#000000] rounded-lg text-sm font-medium text-[#000000] hover:bg-[#E8E9B0] transition-colors"
                  >
                    Create Class
                  </button>
                </div>
              </form>
            )}

            <div className="flex-1 overflow-y-auto p-4">
              {classes.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <svg
                    className="w-16 h-16 text-[#000000] opacity-30 mb-4"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                  </svg>
                  <p className="text-lg font-medium text-[#000000] mb-1">
                    No classes yet
                  </p>
                  <span className="text-sm text-[#000000] opacity-70">
                    Create your first class to begin
                  </span>
                </div>
              ) : (
                <div className="space-y-2">
                  {classes.map((cls) => (
                    <div
                      key={cls.id}
                      className={`group p-4 rounded-lg cursor-pointer transition-all border-2 ${selectedClass?.id === cls.id
                          ? "bg-[#EFF0C6] border-[#000000]"
                          : "bg-white border-[#000000] hover:bg-gray-50"
                        }`}
                      onClick={() => setSelectedClass(cls)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h3 className="font-bold text-[#000000] text-base mb-1">
                            {cls.name}
                          </h3>
                          <span className="text-sm text-[#000000] opacity-70 block">
                            {cls.subject}
                          </span>
                          <span className="text-xs text-[#000000] opacity-60 mt-1 block">
                            {cls.student_count || 0} students
                          </span>
                        </div>
                        <button
                          className="p-2 hover:bg-red-50 rounded transition-all opacity-0 group-hover:opacity-100"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteClass(cls.id);
                          }}
                        >
                          <svg
                            className="w-5 h-5 text-red-600"
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
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Students Panel */}
          <div className="bg-[#DDD6FE] border-2 border-[#000000] rounded-lg flex flex-col overflow-hidden">
            {selectedClass ? (
              <>
                <div className="p-4 md:p-6 border-b-2 border-[#000000]">
                  <div className="flex items-center justify-between gap-4 flex-wrap mb-4">
                    <div>
                      <h2
                        className="text-xl md:text-2xl font-bold text-[#000000] mb-2"
                        style={{
                          fontFamily: "TT Firs Neue, sans-serif",
                          fontWeight: 700,
                        }}
                      >
                        {selectedClass.name}
                      </h2>
                      <span className="inline-block px-2 py-1 bg-white border border-[#000000] rounded text-xs text-[#000000] opacity-70">
                        {selectedClass.subject}
                      </span>
                    </div>
                    <div className="flex gap-2">
                      {students.length > 0 && (
                        <button
                          className="px-4 py-2 bg-[#EFF0C6] border-2 border-[#000000] rounded-lg text-sm font-medium text-[#000000] hover:bg-[#E8E9B0] transition-colors flex items-center gap-2"
                          onClick={handleStartSession}
                        >
                          Start Class
                          <svg
                            className="w-4 h-4"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                          >
                            <polygon points="5 3 19 12 5 21 5 3" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Tabs */}
                  <div className="flex border-gray-200 gap-2">
                    <button
                      className={`px-4 py-2 text-sm font-medium transition-colors flex items-center gap-2 border-b-2 -mb-[2px] ${activeTab === "dashboard"
                          ? "border-blue-500 text-blue-600 bg-blue-50"
                          : "border-transparent text-gray-600 hover:text-gray-900 hover:bg-white bg-white"
                        }`}
                      onClick={() => setActiveTab("dashboard")}
                    >
                      <svg
                        className="w-4 h-4"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M3 3v18h18" />
                        <path d="M18 17V9" />
                        <path d="M13 17V5" />
                        <path d="M8 17v-3" />
                      </svg>
                      Dashboard
                    </button>
                    <button
                      className={`px-4 py-2 text-sm font-medium transition-colors flex items-center gap-2 border-b-2 -mb-[2px] ${activeTab === "students"
                          ? "border-black text-blue-600 bg-blue-50"
                          : "border-transparent text-gray-600 hover:text-gray-900 hover:bg-white bg-white"
                        }`}
                      onClick={() => setActiveTab("students")}
                    >
                      <svg
                        className="w-4 h-4"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                        <circle cx="9" cy="7" r="4" />
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                      </svg>
                      Students ({students.length})
                    </button>
                  </div>
                </div>

                {/* Dashboard Tab */}
                {activeTab === "dashboard" && (
                  <div className="flex-1 overflow-y-auto p-4 md:p-6">
                    <ClassDashboard classId={selectedClass.id} />
                  </div>
                )}

                {/* Students Tab */}
                {activeTab === "students" && (
                  <div className="flex-1 overflow-y-auto p-4 md:p-6">
                    <div className="flex justify-end mb-4">
                      <button
                        className="px-4 py-2 bg-white border-2 border-[#000000] rounded-lg text-sm font-medium text-[#000000] hover:bg-gray-50 transition-colors flex items-center gap-2"
                        onClick={() => setShowStudentForm(true)}
                      >
                        <svg
                          className="w-4 h-4"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                          <circle cx="8.5" cy="7" r="4" />
                          <line x1="20" y1="8" x2="20" y2="14" />
                          <line x1="23" y1="11" x2="17" y2="11" />
                        </svg>
                        Add Student
                      </button>
                    </div>

                    {showStudentForm && (
                      <form
                        className="mb-6 bg-white border-2 border-[#000000] rounded-lg p-4 md:p-6 animate-fade-in"
                        onSubmit={
                          editingStudent
                            ? handleUpdateStudent
                            : handleAddStudent
                        }
                      >
                        <h3 className="text-lg font-bold text-[#000000] mb-4">
                          {editingStudent ? "Edit Student" : "Add New Student"}
                        </h3>

                        <div className="mb-4">
                          <label className="block text-sm font-bold text-[#000000] mb-2">
                            Student Name
                          </label>
                          <input
                            type="text"
                            value={studentName}
                            onChange={(e) => setStudentName(e.target.value)}
                            placeholder="Enter student name"
                            className="w-full px-4 py-3 bg-white border-2 border-[#000000] text-[#000000] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#000000]"
                            autoFocus
                          />
                        </div>

                        <div className="mb-4">
                          <label className="block text-sm font-bold text-[#000000] mb-2">
                            Initial Level
                          </label>
                          <div className="flex gap-2">
                            {["weak", "medium", "strong"].map((level) => (
                              <button
                                key={level}
                                type="button"
                                className={`flex-1 px-4 py-2 rounded-lg border-2 font-medium transition-colors ${studentLevel === level
                                    ? level === "weak"
                                      ? "bg-red-500 text-white border-red-600"
                                      : level === "strong"
                                        ? "bg-green-500 text-white border-green-600"
                                        : "bg-yellow-500 text-white border-yellow-600"
                                    : "bg-white text-[#000000] border-[#000000] hover:bg-gray-50"
                                  }`}
                                onClick={() => setStudentLevel(level)}
                              >
                                {level.charAt(0).toUpperCase() + level.slice(1)}
                              </button>
                            ))}
                          </div>
                        </div>

                        <div className="mb-4">
                          <label className="block text-sm font-bold text-[#000000] mb-2">
                            Initial Confidence
                          </label>
                          <div className="flex items-center gap-4">
                            <StarRating
                              value={Math.round(studentConfidence)}
                              onChange={setStudentConfidence}
                              size="medium"
                            />
                            <span className="text-xl font-bold text-[#000000] min-w-[40px]">
                              {studentConfidence.toFixed(1)}
                            </span>
                          </div>
                        </div>

                        <div className="flex gap-2 justify-end">
                          <button
                            type="button"
                            className="px-4 py-2 bg-white border-2 border-[#000000] rounded-lg text-sm font-medium text-[#000000] hover:bg-gray-50 transition-colors"
                            onClick={resetStudentForm}
                          >
                            Cancel
                          </button>
                          <button
                            type="submit"
                            className="px-4 py-2 bg-[#EFF0C6] border-2 border-[#000000] rounded-lg text-sm font-medium text-[#000000] hover:bg-[#E8E9B0] transition-colors"
                          >
                            {editingStudent ? "Update" : "Add Student"}
                          </button>
                        </div>
                      </form>
                    )}

                    <div className="space-y-3">
                      {students.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-12 text-center">
                          <svg
                            className="w-16 h-16 text-[#000000] opacity-30 mb-4"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                          >
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                            <circle cx="12" cy="7" r="4" />
                          </svg>
                          <p className="text-lg font-medium text-[#000000] mb-1">
                            No students yet
                          </p>
                          <span className="text-sm text-[#000000] opacity-70">
                            Add students to this class
                          </span>
                        </div>
                      ) : (
                        students.map((student) => (
                          <StudentCard
                            key={student.id}
                            student={student}
                            onUpdate={startEditStudent}
                            onDelete={handleDeleteStudent}
                          />
                        ))
                      )}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center py-12 text-center">
                <svg
                  className="w-16 h-16 text-[#000000] opacity-30 mb-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M15 18l-6-6 6-6" />
                </svg>
                <p className="text-lg font-medium text-[#000000]">
                  Select a class to view students
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Personalized_student_support;
