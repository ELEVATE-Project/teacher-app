import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Header from "./components/Header";
import Footer from "./components/Footer";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import SignUp from "./pages/SignUp";
import ActiveListeningMode from "./pages/ActiveListeningMode";
import ChatInterface from "./pages/ChatInterface";
import ModulePage from "./pages/ModulePage";
import Personalized_student_support from "./pages/Personalized_student_support";
import QuestionSetup from "./pages/QuestionSetup";
import LiveSession from "./pages/LiveSession";
import ClassSummary from "./pages/ClassSummary";
import Discuss from "./pages/Discuss";
import DiscussNew from "./pages/DiscussNew";
import DiscussPost from "./pages/DiscussPost";
import NotFound from "./pages/NotFound";

// Dashboard imports
import DashboardLayout from "./components/dashboard/DashboardLayout";
import ColdStartSetup from "./pages/dashboard/ColdStartSetup";
import DashboardQuestionSetup from "./pages/dashboard/QuestionSetup";
import DashboardLiveSession from "./pages/dashboard/LiveSession";
import DashboardClassSummary from "./pages/dashboard/ClassSummary";
import StudentProfile from "./pages/dashboard/StudentProfile";

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen flex flex-col">
          <Header />
          <Toaster
            position="top-center"
            containerStyle={{ top: "50%", transform: "translateY(-50%)" }}
          />
          <main className="flex-1 min-h-0 flex flex-col">
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<SignUp />} />
              <Route path="/alm" element={<ActiveListeningMode />} />

              {/* Dashboard Routes */}
              <Route
                path="/dashboard"
                element={<DashboardLayout />}>
                <Route index element={<ColdStartSetup />} />
                <Route path="setup" element={<ColdStartSetup />} />
                <Route path="questions/:classId" element={<DashboardQuestionSetup />} />
                <Route path="session/:sessionId" element={<DashboardLiveSession />} />
                <Route path="summary/:sessionId" element={<DashboardClassSummary />} />
                <Route path="student/:studentId" element={<StudentProfile />} />
              </Route>

              <Route
                path="/chat"
                element={
                  <ProtectedRoute>
                    <ChatInterface />
                  </ProtectedRoute>
                }
              />
              <Route path="/module" element={<ModulePage />} />
              <Route path="/discuss" element={<Discuss />} />
              <Route path="/discuss/new" element={<DiscussNew />} />
              <Route path="/discuss/:id" element={<DiscussPost />} />
              <Route path="/personalized-support/*" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </main>
          {/* <Footer /> */}
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
