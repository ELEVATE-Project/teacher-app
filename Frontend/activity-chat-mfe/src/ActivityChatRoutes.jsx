import { Routes, Route, Navigate } from "react-router-dom";
import ChatInterface from "./pages/ChatInterface";

export default function ActivityChatRoutes() {
  return (
    <Routes>
      <Route index element={<ChatInterface mode="activity_generator" />} />
      <Route path="*" element={<Navigate to="" replace />} />
    </Routes>
  );
}
