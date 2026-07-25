import React, { Suspense, lazy } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Header from "./components/Header";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import SignUp from "./pages/SignUp";
import NotFound from "./pages/NotFound";

// Lazy load Microfrontends using Module Federation
const DashboardRoutes = lazy(() => import("dashboard_mfe/DashboardRoutes"));
const QnaChatRoutes = lazy(() => import("qna_chat_mfe/QnaChatRoutes"));
const ActivityChatRoutes = lazy(() => import("activity_chat_mfe/ActivityChatRoutes"));
const ModuleChatRoutes = lazy(() => import("module_chat_mfe/ModuleChatRoutes"));
const DiscussRoutes = lazy(() => import("discuss_mfe/DiscussRoutes"));

// Premium animated loading fallback for MFEs
const LoadingFallback = () => (
  <div className="flex-1 flex items-center justify-center bg-slate-50/50 backdrop-blur-sm min-h-[400px]">
    <div className="text-center">
      <div className="inline-block animate-spin rounded-full h-10 w-10 border-4 border-blue-600 border-t-transparent shadow-md"></div>
      <p className="mt-4 text-slate-600 font-medium tracking-wide">Loading application module...</p>
    </div>
  </div>
);

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
            <Suspense fallback={<LoadingFallback />}>
              <Routes>
                {/* Native Shell Routes */}
                <Route path="/" element={<Landing />} />
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<SignUp />} />

                {/* Microfrontend: Dashboard Module */}
                <Route
                  path="/dashboard/*"
                  element={
                    <ProtectedRoute>
                      <DashboardRoutes />
                    </ProtectedRoute>
                  }
                />

                {/* Microfrontend: QnA Chat Module */}
                <Route
                  path="/chat/qna/*"
                  element={
                    <ProtectedRoute>
                      <QnaChatRoutes />
                    </ProtectedRoute>
                  }
                />

                {/* Consolidated single Chat interface */}
                <Route path="/chat/dynamic/*" element={<Navigate to="/chat/qna/dynamic" replace />} />
                <Route path="/chat/dynamic" element={<Navigate to="/chat/qna/dynamic" replace />} />
                <Route path="/chat/activity/*" element={<Navigate to="/chat/qna/dynamic" replace />} />
                <Route path="/chat/module-builder" element={<Navigate to="/chat/qna/dynamic" replace />} />
                <Route
                  path="/chat/module-builder/view"
                  element={
                    <ProtectedRoute>
                      <ModuleChatRoutes />
                    </ProtectedRoute>
                  }
                />

                {/* Root paths /chat redirects to default Dynamic selection */}
                <Route path="/chat" element={<Navigate to="/chat/dynamic" replace />} />

                {/* Redirect legacy direct links to MFE routes */}
                <Route path="/alm" element={<Navigate to="/chat/qna/alm" replace />} />
                <Route path="/module" element={<Navigate to="/chat/module-builder/view" replace />} />

                {/* Microfrontend: Discussion Board Module */}
                <Route
                  path="/discuss/*"
                  element={
                    <ProtectedRoute>
                      <DiscussRoutes />
                    </ProtectedRoute>
                  }
                />

                {/* Fallback */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Suspense>
          </main>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
