import { Routes, Route, Navigate } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute.jsx";
import PublicRoute from "./components/PublicRoute.jsx";
import AppLayout from "./components/AppLayout.jsx";
import AuthPage from "./pages/AuthPage.jsx";
import Tasks from "./pages/Tasks.jsx";
import TaskDetail from "./pages/TaskDetail.jsx";
import Categories from "./pages/Categories.jsx";
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

      {/* Área autenticada: shell com top nav + conteúdo via Outlet. */}
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Tasks />} />
        <Route path="/tasks/:id" element={<TaskDetail />} />
        <Route path="/categories" element={<Categories />} />
      </Route>

      {/* Smoke test de infraestrutura da Task 18. */}
      <Route path="/health" element={<HealthCheck />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
