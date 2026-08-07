import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

// Envolve rotas que exigem autenticação. Enquanto a sessão inicial é validada,
// mostra um estado de carregamento; sem sessão, redireciona para /login
// preservando de onde o usuário veio (para voltar após o login).
export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <p style={{ padding: "2rem" }}>Carregando...</p>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}
