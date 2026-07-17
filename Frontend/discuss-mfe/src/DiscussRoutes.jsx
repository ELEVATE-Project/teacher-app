import { Routes, Route } from "react-router-dom";
import Discuss from "./pages/Discuss";
import DiscussNew from "./pages/DiscussNew";
import DiscussPost from "./pages/DiscussPost";

export default function DiscussRoutes() {
  return (
    <Routes>
      <Route index element={<Discuss />} />
      <Route path="new" element={<DiscussNew />} />
      <Route path=":id" element={<DiscussPost />} />
    </Routes>
  );
}
