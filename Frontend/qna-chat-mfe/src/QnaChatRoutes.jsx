import { Routes, Route, Navigate } from "react-router-dom";
import ChatInterface from "./pages/ChatInterface";
import ActiveListeningMode from "./pages/ActiveListeningMode";

export default function QnaChatRoutes() {
  return (
    <Routes>
      <Route index element={<ChatInterface mode="expert_teacher" />} />
      <Route path="alm" element={<ActiveListeningMode />} />
      <Route path="*" element={<Navigate to="" replace />} />
    </Routes>
  );
}
