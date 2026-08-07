import { Routes, Route, Navigate } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute.jsx";
import PublicRoute from "./components/PublicRoute.jsx";
import AuthPage from "./pages/AuthPage.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import HealthCheck from "./pages/HealthCheck.jsx";

export default function App() {
  return (
    <Routes>
      {/* Rotas públicas: a mesma tela combinada em dois modos (login/cadastro).
          Quem já está logado é redirecionado para a home. */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <AuthPage />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <AuthPage />
          </PublicRoute>
        }
      />

      {/* Home autenticada (placeholder até a Task 21). */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      {/* Smoke test de infraestrutura da Task 18. */}
      <Route path="/health" element={<HealthCheck />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
