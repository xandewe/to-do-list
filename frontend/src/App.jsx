import { Routes, Route, Navigate } from "react-router-dom";

import HealthCheck from "./pages/HealthCheck.jsx";

// Roteamento base da Task 18. As telas reais (login, tarefas, etc.) entram nas
// próximas tasks. Por ora, "/" mostra o smoke test de conectividade com a API.
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HealthCheck />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
