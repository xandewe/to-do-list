import { useState } from "react";

import { useAuth } from "../context/AuthContext";

// Home autenticada — placeholder da Task 19 já no tema Organic. A nav completa
// (Tarefas/Categorias/Perfil) e o conteúdo real chegam nas Tasks 20/21.
export default function Dashboard() {
  const { user, logout } = useAuth();
  const [loggingOut, setLoggingOut] = useState(false);

  const first = user?.first_name || "";
  const last = user?.last_name || "";
  const initials = `${first[0] || ""}${last[0] || ""}`.toUpperCase() || (user?.email?.[0] || "").toUpperCase();

  async function handleLogout() {
    setLoggingOut(true);
    try {
      await logout();
      // Sem navigate: ao zerar a sessão, a ProtectedRoute redireciona sozinha.
    } finally {
      setLoggingOut(false);
    }
  }

  return (
    <>
      <header className="nav" style={{ maxWidth: 940, margin: "0 auto", paddingTop: 22, gap: 20 }}>
        <span className="nav-brand" style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span
            style={{ width: 26, height: 26, borderRadius: 999, background: "var(--color-accent)", display: "inline-block" }}
          />
          To-do AH
        </span>
        <nav style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <span
            style={{
              width: 28,
              height: 28,
              borderRadius: 999,
              background: "var(--color-accent-2-300)",
              color: "var(--color-accent-2-800)",
              display: "grid",
              placeItems: "center",
              fontSize: 12,
              fontWeight: 700,
            }}
            title={user?.email}
          >
            {initials}
          </span>
          <button className="btn btn-secondary" onClick={handleLogout} disabled={loggingOut} style={{ height: 36 }}>
            {loggingOut ? "Saindo..." : "Sair"}
          </button>
        </nav>
      </header>

      <main style={{ maxWidth: 940, margin: "0 auto", padding: "26px 18px 90px" }}>
        <h1 style={{ fontSize: 40, lineHeight: 1.1, margin: "8px 0 4px" }}>
          Olá, {first || user?.email}
        </h1>
        <p style={{ margin: 0, fontSize: 15, color: "var(--color-neutral-700)" }}>
          Você está autenticado. As telas de categorias e tarefas chegam nas próximas etapas.
        </p>
      </main>
    </>
  );
}
