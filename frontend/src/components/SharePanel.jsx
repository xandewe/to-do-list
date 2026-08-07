import { useState, useEffect, useCallback } from "react";

import { listShares, addShare, updateShare, deleteShare } from "../services/shares";
import { getApiErrorMessage } from "../lib/apiErrors";
import { useToast } from "../context/ToastContext";
import ConfirmDialog from "./ConfirmDialog";

// Painel de compartilhamento, exibido no detalhe da tarefa apenas para o
// proprietário. Lista acessos, adiciona por e-mail, troca a permissão e revoga.
export default function SharePanel({ taskId }) {
  const { notify } = useToast();

  const [shares, setShares] = useState([]);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState("");
  const [permission, setPermission] = useState("view");
  const [adding, setAdding] = useState(false);
  const [revokeTarget, setRevokeTarget] = useState(null);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      setShares(await listShares(taskId));
    } catch (err) {
      notify(getApiErrorMessage(err), "err");
    } finally {
      setLoading(false);
    }
  }, [taskId, notify]);

  useEffect(() => {
    reload();
  }, [reload]);

  async function handleAdd(e) {
    e.preventDefault();
    const value = email.trim().toLowerCase();
    if (!value) return;
    setAdding(true);
    try {
      await addShare(taskId, { email: value, permission });
      setEmail("");
      setPermission("view");
      notify(`Compartilhada com ${value}.`);
      reload();
    } catch (err) {
      // 404 = e-mail sem conta; 400 = consigo mesmo / já compartilhada.
      notify(getApiErrorMessage(err), "err");
    } finally {
      setAdding(false);
    }
  }

  async function handleChangePermission(share, value) {
    try {
      await updateShare(taskId, share.id, { permission: value });
      setShares((prev) => prev.map((s) => (s.id === share.id ? { ...s, permission: value } : s)));
      notify(`Permissão de ${share.user_email} atualizada.`);
    } catch (err) {
      notify(getApiErrorMessage(err), "err");
    }
  }

  async function handleRevoke() {
    const share = revokeTarget;
    try {
      await deleteShare(taskId, share.id);
      setRevokeTarget(null);
      setShares((prev) => prev.filter((s) => s.id !== share.id));
      notify("Acesso revogado.");
    } catch (err) {
      setRevokeTarget(null);
      notify(getApiErrorMessage(err), "err");
    }
  }

  return (
    <div className="card" style={{ background: "var(--color-neutral-100)", gap: "var(--space-3)", marginTop: 26 }}>
      <p className="card-title" style={{ margin: 0 }}>
        Compartilhamento
      </p>

      {loading && <p style={{ margin: 0, fontSize: 13, color: "var(--color-neutral-700)" }}>Carregando...</p>}

      {!loading && shares.length === 0 && (
        <p style={{ margin: 0, fontSize: 13, color: "var(--color-neutral-700)" }}>
          Ainda não compartilhada com ninguém.
        </p>
      )}

      {!loading && shares.length > 0 && (
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 10 }}>
          {shares.map((s) => (
            <li key={s.id} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ flex: 1, minWidth: 0, fontSize: 13, overflow: "hidden", textOverflow: "ellipsis" }}>
                {s.user_email}
              </span>
              <select
                className="input"
                aria-label={`Permissão de ${s.user_email}`}
                value={s.permission}
                onChange={(e) => handleChangePermission(s, e.target.value)}
                style={{ width: 104, minHeight: 32, fontSize: 12 }}
              >
                <option value="view">Ver</option>
                <option value="edit">Editar</option>
              </select>
              <button
                className="btn btn-ghost"
                onClick={() => setRevokeTarget(s)}
                aria-label={`Revogar acesso de ${s.user_email}`}
                style={{ fontSize: 12 }}
              >
                Revogar
              </button>
            </li>
          ))}
        </ul>
      )}

      <form
        onSubmit={handleAdd}
        style={{ display: "flex", flexDirection: "column", gap: 10, borderTop: "1px solid var(--color-divider)", paddingTop: "var(--space-3)" }}
      >
        <div className="field">
          <label htmlFor="share-email">Compartilhar por e-mail</label>
          <input
            id="share-email"
            type="email"
            className="input"
            placeholder="pessoa@empresa.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <select
            className="input"
            aria-label="Permissão"
            value={permission}
            onChange={(e) => setPermission(e.target.value)}
            style={{ width: 110 }}
          >
            <option value="view">Ver</option>
            <option value="edit">Editar</option>
          </select>
          <button type="submit" className="btn btn-primary" disabled={adding} style={{ flex: 1 }}>
            {adding ? "Convidando..." : "Convidar"}
          </button>
        </div>
      </form>

      {revokeTarget && (
        <ConfirmDialog
          title="Revogar acesso?"
          body={`${revokeTarget.user_email} perde o acesso imediatamente.`}
          cta="Revogar"
          onConfirm={handleRevoke}
          onClose={() => setRevokeTarget(null)}
        />
      )}
    </div>
  );
}
