import { useState, useEffect, useCallback } from "react";

import {
  listCategories,
  createCategory,
  updateCategory,
  deleteCategory,
} from "../services/categories";
import { getApiErrorMessage } from "../lib/apiErrors";
import { useToast } from "../context/ToastContext";
import CategoryDialog from "../components/CategoryDialog";
import ConfirmDialog from "../components/ConfirmDialog";

export default function Categories() {
  const { notify } = useToast();

  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  // dialog: null | { category: <cat|null> }  · confirm: null | <cat>
  const [dialog, setDialog] = useState(null);
  const [confirm, setConfirm] = useState(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setLoadError("");
    try {
      const data = await listCategories();
      setCategories(data);
    } catch (err) {
      setLoadError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  async function handleSave(payload) {
    const editing = dialog?.category;
    if (editing) {
      await updateCategory(editing.id, payload);
    } else {
      await createCategory(payload);
    }
    // Fecha só após sucesso; erros são tratados dentro do dialog.
    setDialog(null);
    notify(editing ? "Categoria atualizada." : "Categoria criada.");
    reload();
  }

  async function handleDelete() {
    try {
      await deleteCategory(confirm.id);
      setConfirm(null);
      notify("Categoria excluída.");
      reload();
    } catch (err) {
      setConfirm(null);
      notify(getApiErrorMessage(err), "err");
    }
  }

  return (
    <main style={{ maxWidth: 940, margin: "0 auto", padding: "26px 18px 90px" }}>
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 16, marginBottom: 26 }}>
        <div>
          <h1 style={{ fontSize: 40, lineHeight: 1.1, margin: "8px 0 4px" }}>Categorias</h1>
          <p style={{ margin: 0, fontSize: 15, color: "var(--color-neutral-700)" }}>
            Excluir uma categoria não apaga as tarefas — elas ficam sem categoria.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setDialog({ category: null })} style={{ minHeight: 42, flex: "none" }}>
          Nova categoria
        </button>
      </div>

      {loading && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))", gap: 16 }}>
          {[1, 2, 3, 4].map((n) => (
            <div
              key={n}
              style={{ height: 120, borderRadius: 32, background: "var(--color-neutral-200)", animation: "ah-pulse 1.2s ease-in-out infinite" }}
            />
          ))}
        </div>
      )}

      {!loading && loadError && (
        <p role="alert" className="alert alert-error">
          {loadError}
        </p>
      )}

      {!loading && !loadError && categories.length === 0 && (
        <div style={{ textAlign: "center", padding: "64px 20px", color: "var(--color-neutral-700)" }}>
          <p style={{ fontFamily: "var(--font-heading)", fontSize: 22, margin: "0 0 6px", color: "var(--color-text)" }}>
            Nenhuma categoria ainda
          </p>
          <p style={{ margin: 0, fontSize: 14 }}>Crie a primeira para organizar suas tarefas.</p>
        </div>
      )}

      {!loading && !loadError && categories.length > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))", gap: 16 }}>
          {categories.map((c) => (
            <div key={c.id} className="card" style={{ background: "var(--color-neutral-100)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span
                  style={{
                    width: 22,
                    height: 22,
                    borderRadius: 999,
                    flex: "none",
                    background: c.color || "var(--color-neutral-300)",
                    border: "1px solid var(--color-divider)",
                  }}
                />
                <span className="card-title" style={{ flex: 1, minWidth: 0 }}>
                  {c.name}
                </span>
              </div>
              <p className="card-body">{c.description || "Sem descrição"}</p>
              <div className="card-meta" style={{ justifyContent: "flex-end" }}>
                <span style={{ display: "flex", gap: 4 }}>
                  <button className="btn btn-ghost" onClick={() => setDialog({ category: c })} style={{ fontSize: 12 }}>
                    Editar
                  </button>
                  <button className="btn btn-ghost" onClick={() => setConfirm(c)} style={{ fontSize: 12 }}>
                    Excluir
                  </button>
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {dialog && (
        <CategoryDialog category={dialog.category} onSave={handleSave} onClose={() => setDialog(null)} />
      )}

      {confirm && (
        <ConfirmDialog
          title="Excluir categoria?"
          body={`"${confirm.name}" será removida. As tarefas associadas continuam existindo, apenas ficam sem categoria.`}
          cta="Excluir"
          onConfirm={handleDelete}
          onClose={() => setConfirm(null)}
        />
      )}
    </main>
  );
}
