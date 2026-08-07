import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

// Shell das telas autenticadas: top nav (marca + navegação + avatar/Sair) e o
// conteúdo da rota via <Outlet/>. A tela de Perfil chega numa task futura.
export default function AppLayout() {
  const { user, logout } = useAuth();
  const [loggingOut, setLoggingOut] = useState(false);

  const first = user?.first_name || "";
  const last = user?.last_name || "";
  const initials =
    `${first[0] || ""}${last[0] || ""}`.toUpperCase() || (user?.email?.[0] || "").toUpperCase();

  async function handleLogout() {
    setLoggingOut(true);
    try {
      await logout();
    } finally {
      setLoggingOut(false);
    }
  }

  const linkStyle = ({ isActive }) => ({
    cursor: "pointer",
    color: isActive ? "var(--color-accent)" : "inherit",
  });

  return (
    <>
      <header className="nav" style={{ maxWidth: 940, margin: "0 auto", paddingTop: 22, gap: 20 }}>
        <span className="nav-brand" style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span
            style={{ width: 26, height: 26, borderRadius: 999, background: "var(--color-accent)", display: "inline-block" }}
          />
          To-do AH
        </span>
        <nav style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <NavLink to="/" end style={linkStyle}>
            Tarefas
          </NavLink>
          <NavLink to="/categories" style={linkStyle}>
            Categorias
          </NavLink>
          <span
            title={user?.email}
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
          >
            {initials}
          </span>
          <button className="btn btn-secondary" onClick={handleLogout} disabled={loggingOut} style={{ height: 36 }}>
            {loggingOut ? "Saindo..." : "Sair"}
          </button>
        </nav>
      </header>
      <Outlet />
    </>
  );
}
