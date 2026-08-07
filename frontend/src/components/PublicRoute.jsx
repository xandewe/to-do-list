import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

// Para rotas exclusivas de quem NÃO está autenticado (login, registro): um
// usuário já logado é mandado para a home. Espera a validação inicial da sessão.
export default function PublicRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <p style={{ padding: "2rem" }}>Carregando...</p>;
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
}
