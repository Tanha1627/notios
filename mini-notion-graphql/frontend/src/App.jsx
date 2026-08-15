import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import WorkspacePage from "./pages/WorkspacePage.jsx";

function RequireAuth({ children }) {
  const { token, loading } = useAuth();
  if (loading) return <FullScreenLoader />;
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

function FullScreenLoader() {
  return (
    <div className="h-screen w-screen flex items-center justify-center bg-paper">
      <div className="flex items-center gap-3 text-subink font-mono text-sm">
        <span className="w-2 h-2 rounded-full bg-pine-500 animate-pulse" />
        loading notio
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <RequireAuth>
            <WorkspacePage />
          </RequireAuth>
        }
      />
    </Routes>
  );
}
