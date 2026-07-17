import { Routes, Route } from "react-router-dom";
import DashboardLayout from "./components/dashboard/DashboardLayout";
import ColdStartSetup from "./pages/dashboard/ColdStartSetup";
import DashboardQuestionSetup from "./pages/dashboard/QuestionSetup";
import DashboardLiveSession from "./pages/dashboard/LiveSession";
import DashboardClassSummary from "./pages/dashboard/ClassSummary";
import StudentProfile from "./pages/dashboard/StudentProfile";

export default function DashboardRoutes() {
  return (
    <Routes>
      <Route element={<DashboardLayout />}>
        <Route index element={<ColdStartSetup />} />
        <Route path="setup" element={<ColdStartSetup />} />
        <Route path="questions/:classId" element={<DashboardQuestionSetup />} />
        <Route path="session/:sessionId" element={<DashboardLiveSession />} />
        <Route path="summary/:sessionId" element={<DashboardClassSummary />} />
        <Route path="student/:studentId" element={<StudentProfile />} />
      </Route>
    </Routes>
  );
}
