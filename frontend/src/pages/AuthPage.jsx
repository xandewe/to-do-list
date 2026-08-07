import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { getApiErrorMessage } from "../lib/apiErrors";

// Tela combinada de login/cadastro, no tema Organic do design.
// O modo é derivado da rota (/login ou /register); o toggle troca de rota
// para preservar deep-linking. Diferente do mock do design, o cadastro NÃO
// autentica (a API não emite token no POST /users/): após criar a conta,
// volta para o login com um aviso de sucesso.
export default function AuthPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const isRegister = location.pathname === "/register";
  const redirectTo = location.state?.from?.pathname || "/";
  const notice = location.state?.notice;

  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (isRegister) {
        await register(form);
        navigate("/login", {
          replace: true,
          state: { notice: "Conta criada com sucesso. Faça login para continuar." },
        });
      } else {
        await login({ email: form.email, password: form.password });
        navigate(redirectTo, { replace: true });
      }
    } catch (err) {
      const message =
        !isRegister && err?.response?.status === 401
          ? "E-mail ou senha inválidos."
          : getApiErrorMessage(err);
      setError(message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: "40px 18px" }}>
      <div style={{ width: "min(420px, 100%)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 26 }}>
          <span
            style={{
              width: 34,
              height: 34,
              borderRadius: 999,
              background: "var(--color-accent)",
              display: "inline-block",
            }}
          />
          <span style={{ fontFamily: "var(--font-heading)", fontSize: 24 }}>To-do AH</span>
        </div>

        <h1 style={{ fontSize: 34, lineHeight: 1.15, margin: "0 0 6px" }}>
          {isRegister ? "Criar uma conta" : "Entrar na sua conta"}
        </h1>
        <p style={{ margin: "0 0 26px", fontSize: 15, color: "var(--color-neutral-700)" }}>
          {isRegister ? "Leva menos de um minuto." : "Suas tarefas e as compartilhadas com você."}
        </p>

        {notice && !isRegister && (
          <p role="status" className="alert alert-success" style={{ marginBottom: 14 }}>
            {notice}
          </p>
        )}

        <form onSubmit={handleSubmit} noValidate style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {isRegister && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
              <div className="field">
                <label htmlFor="firstName">Nome</label>
                <input
                  id="firstName"
                  name="firstName"
                  className="input"
                  autoComplete="given-name"
                  value={form.firstName}
                  onChange={handleChange}
                  style={{ minHeight: 44 }}
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="lastName">Sobrenome</label>
                <input
                  id="lastName"
                  name="lastName"
                  className="input"
                  autoComplete="family-name"
                  value={form.lastName}
                  onChange={handleChange}
                  style={{ minHeight: 44 }}
                  required
                />
              </div>
            </div>
          )}

          <div className="field">
            <label htmlFor="email">E-mail</label>
            <input
              id="email"
              name="email"
              type="email"
              className="input"
              autoComplete="email"
              value={form.email}
              onChange={handleChange}
              style={{ minHeight: 44 }}
              required
            />
          </div>

          <div className="field">
            <label htmlFor="password">Senha</label>
            <input
              id="password"
              name="password"
              type="password"
              className="input"
              autoComplete={isRegister ? "new-password" : "current-password"}
              value={form.password}
              onChange={handleChange}
              style={{ minHeight: 44 }}
              required
            />
          </div>

          {error && (
            <p role="alert" className="alert alert-error">
              {error}
            </p>
          )}

          <button type="submit" className="btn btn-primary btn-block" disabled={busy} style={{ minHeight: 46 }}>
            {busy ? "Aguarde..." : isRegister ? "Criar conta" : "Entrar"}
          </button>
        </form>

        <p style={{ margin: "20px 0 0", fontSize: 14, color: "var(--color-neutral-700)" }}>
          {isRegister ? "Já tem conta? " : "Ainda não tem conta? "}
          <Link to={isRegister ? "/login" : "/register"}>
            {isRegister ? "Entrar" : "Cadastre-se"}
          </Link>
        </p>
      </div>
    </main>
  );
}
