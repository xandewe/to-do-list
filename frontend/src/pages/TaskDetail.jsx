import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";

import { getTask, updateTask, deleteTask } from "../services/tasks";
import { listCategories } from "../services/categories";
import { getApiErrorMessage } from "../lib/apiErrors";
import { toDateInput, fromDateInput } from "../lib/taskFormat";
import { useToast } from "../context/ToastContext";
import ConfirmDialog from "../components/ConfirmDialog";

function toDraft(task) {
  return {
    title: task.title,
    description: task.description || "",
    status: task.status,
    priority: task.priority,
    due: toDateInput(task.due_date),
    categoryId: task.category_id || "",
  };
}

const ACCESS = {
  owner: {
    label: "Proprietária",
    tag: "tag tag-accent",
    hint: "Você controla campos, categoria, exclusão e compartilhamentos.",
  },
  edit: {
    label: "Acesso: editar",
    tag: "tag tag-accent-2",
    hint: "Você pode editar o conteúdo, mas não a categoria nem os acessos.",
  },
  view: {
    label: "Acesso: somente leitura",
    tag: "tag tag-neutral",
    hint: "Qualquer alteração é recusada pela API.",
  },
};

export default function TaskDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { notify } = useToast();

  const [task, setTask] = useState(null);
  const [categories, setCategories] = useState([]);
  const [draft, setDraft] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setNotFound(false);
    try {
      const [t, cats] = await Promise.all([getTask(id), listCategories()]);
      setTask(t);
      setCategories(cats);
      setDraft(toDraft(t));
    } catch (err) {
      if (err?.response?.status === 404) {
        setNotFound(true);
      } else {
        notify(getApiErrorMessage(err), "err");
      }
    } finally {
      setLoading(false);
    }
  }, [id, notify]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return <p style={{ maxWidth: 640, margin: "3rem auto", padding: "0 18px" }}>Carregando...</p>;
  }

  if (notFound) {
    return (
      <main style={{ maxWidth: 640, margin: "3rem auto", padding: "0 18px" }}>
        <p style={{ fontFamily: "var(--font-heading)", fontSize: 22 }}>Tarefa não encontrada</p>
        <p style={{ color: "var(--color-neutral-700)" }}>
          Ela pode ter sido excluída ou você não tem mais acesso.
        </p>
        <Link to="/">← Voltar para tarefas</Link>
      </main>
    );
  }

  const permission = task.access.permission;
  const isOwner = permission === "owner";
  const readOnly = permission === "view";
  const catLocked = !isOwner; // só o proprietário muda a categoria
  const access = ACCESS[permission] || ACCESS.view;

  const dirty =
    draft.title !== task.title ||
    draft.description !== (task.description || "") ||
    draft.status !== task.status ||
    draft.priority !== task.priority ||
    draft.due !== toDateInput(task.due_date) ||
    draft.categoryId !== (task.category_id || "");

  const set = (key) => (e) => setDraft((d) => ({ ...d, [key]: e.target.value }));

  async function handleSave() {
    if (!draft.title.trim()) {
      notify("O título não pode ficar vazio.", "err");
      return;
    }
    // Editor compartilhado não pode enviar category_id (a API responde 403).
    const payload = {
      title: draft.title.trim(),
      description: draft.description,
      status: draft.status,
      priority: draft.priority,
      due_date: fromDateInput(draft.due),
    };
    if (isOwner) {
      payload.category_id = draft.categoryId || null;
    }
    setSaving(true);
    try {
      const updated = await updateTask(task.id, payload);
      setTask(updated);
      setDraft(toDraft(updated));
      notify("Alterações salvas.");
    } catch (err) {
      notify(getApiErrorMessage(err), "err");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    await deleteTask(task.id);
    notify("Tarefa excluída.");
    navigate("/");
  }

  return (
    <main style={{ maxWidth: 640, margin: "0 auto", padding: "26px 18px 90px" }}>
      <Link to="/" className="btn btn-ghost" style={{ marginBottom: 14, display: "inline-flex" }}>
        ← Voltar para tarefas
      </Link>

      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
        <span className={access.tag}>{access.label}</span>
        <span style={{ fontSize: 12, color: "var(--color-neutral-700)" }}>{access.hint}</span>
      </div>

      <div className="field" style={{ marginBottom: 16 }}>
        <label htmlFor="d-title">Título</label>
        <input id="d-title" className="input" value={draft.title} onChange={set("title")} disabled={readOnly} style={{ minHeight: 46, fontSize: 17 }} />
      </div>

      <div className="field" style={{ marginBottom: 16 }}>
        <label htmlFor="d-desc">Descrição</label>
        <textarea
          id="d-desc"
          className="input"
          value={draft.description}
          onChange={set("description")}
          disabled={readOnly}
          placeholder="Sem descrição"
          style={{ borderRadius: "var(--radius-md)", padding: "12px 14px" }}
        />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 14 }}>
        <div className="field">
          <label htmlFor="d-status">Status</label>
          <select id="d-status" className="input" value={draft.status} onChange={set("status")} disabled={readOnly} style={{ minHeight: 42 }}>
            <option value="pending">Pendente</option>
            <option value="completed">Concluída</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="d-prio">Prioridade</label>
          <select id="d-prio" className="input" value={draft.priority} onChange={set("priority")} disabled={readOnly} style={{ minHeight: 42 }}>
            <option value="low">Baixa</option>
            <option value="medium">Média</option>
            <option value="high">Alta</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="d-due">Prazo</label>
          <input id="d-due" type="date" className="input" value={draft.due} onChange={set("due")} disabled={readOnly} style={{ minHeight: 42 }} />
        </div>
        <div className="field">
          <label htmlFor="d-cat">Categoria</label>
          <select id="d-cat" className="input" value={draft.categoryId} onChange={set("categoryId")} disabled={catLocked} style={{ minHeight: 42 }}>
            <option value="">Sem categoria</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          {catLocked && !readOnly && (
            <p style={{ margin: "6px 0 0", fontSize: 11, color: "var(--color-neutral-700)" }}>
              Só o proprietário pode mudar a categoria.
            </p>
          )}
        </div>
      </div>

      <div style={{ display: "flex", gap: 10, marginTop: 26 }}>
        <button className="btn btn-primary" onClick={handleSave} disabled={readOnly || !dirty || saving} style={{ minHeight: 42 }}>
          {saving ? "Salvando..." : "Salvar alterações"}
        </button>
        {isOwner && (
          <button className="btn btn-secondary" onClick={() => setConfirmDelete(true)} style={{ minHeight: 42, color: "var(--color-accent-700)" }}>
            Excluir
          </button>
        )}
      </div>

      <p style={{ fontSize: 12, color: "var(--color-neutral-600)", margin: "26px 0 0" }}>
        Criada em {new Date(task.created_at).toLocaleDateString("pt-BR")} · id {task.id}
      </p>

      {confirmDelete && (
        <ConfirmDialog
          title="Excluir tarefa?"
          body={`"${task.title}" será removida permanentemente.`}
          cta="Excluir"
          onConfirm={handleDelete}
          onClose={() => setConfirmDelete(false)}
        />
      )}
    </main>
  );
}
