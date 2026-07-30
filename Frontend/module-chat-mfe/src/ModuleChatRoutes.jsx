import { Routes, Route, Navigate } from "react-router-dom";
import ChatInterface from "./pages/ChatInterface";
import ModulePage from "./pages/ModulePage";

export default function ModuleChatRoutes() {
  return (
    <Routes>
      <Route index element={<ChatInterface mode="module_builder" />} />
      <Route path="view" element={<ModulePage />} />
      <Route path="*" element={<Navigate to="" replace />} />
    </Routes>
  );
}
