import { useState } from "react";

import { getHealth } from "../services/health";

// Smoke test da Task 18: prova conectividade e CORS ponta a ponta contra o
// backend. É temporário — some quando a tela de login (Task 19) virar a home.
const STATUS = {
  idle: "idle",
  loading: "loading",
  ok: "ok",
  error: "error",
};

export default function HealthCheck() {
  const [status, setStatus] = useState(STATUS.idle);
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  async function handleCheck() {
    setStatus(STATUS.loading);
    setResult(null);
    setErrorMessage("");
    try {
      const data = await getHealth();
      setResult(data);
      setStatus(STATUS.ok);
    } catch (error) {
      setErrorMessage(error.message || "Falha ao consultar a API");
      setStatus(STATUS.error);
    }
  }

  return (
    <main style={{ maxWidth: 480, margin: "4rem auto", padding: "0 1rem" }}>
      <h1>To-do List AH</h1>
      <p>Setup do frontend (Task 18). Teste a conexão com a API:</p>

      <button onClick={handleCheck} disabled={status === STATUS.loading}>
        {status === STATUS.loading ? "Consultando..." : "Verificar API"}
      </button>

      {status === STATUS.ok && result && (
        <pre
          style={{
            marginTop: "1rem",
            padding: "1rem",
            background: "#e6f4ea",
            borderRadius: 6,
          }}
        >
          {JSON.stringify(result, null, 2)}
        </pre>
      )}

      {status === STATUS.error && (
        <p style={{ marginTop: "1rem", color: "#b3261e" }}>{errorMessage}</p>
      )}
    </main>
  );
}
