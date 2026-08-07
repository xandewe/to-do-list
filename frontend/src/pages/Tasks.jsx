import { useState, useEffect, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";

import { listTasks, countTasks, createTask, updateTask, PAGE_SIZE } from "../services/tasks";
import { listCategories } from "../services/categories";
import { getApiErrorMessage } from "../lib/apiErrors";
import { PRIORITY, dueInfo } from "../lib/taskFormat";
import { useToast } from "../context/ToastContext";

const STATUS_TABS = [
  { key: "all", label: "Todas" },
  { key: "pending", label: "Pendentes" },
  { key: "completed", label: "Concluídas" },
];

export default function Tasks() {
  const navigate = useNavigate();
  const { notify } = useToast();

  const [categories, setCategories] = useState([]);
  const [data, setData] = useState({ count: 0, next: null, previous: null, results: [] });
  const [counts, setCounts] = useState({ all: 0, pending: 0, completed: 0 });
  const [status, setStatus] = useState("all");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const [quickTitle, setQuickTitle] = useState("");
  const [quickCat, setQuickCat] = useState("");
  const [adding, setAdding] = useState(false);

  const catById = useMemo(
    () => Object.fromEntries(categories.map((c) => [c.id, c])),
    [categories]
  );

  useEffect(() => {
    listCategories()
      .then(setCategories)
      .catch(() => {});
  }, []);

  const reloadCounts = useCallback(async () => {
    try {
      const [all, pending, completed] = await Promise.all([
        countTasks("all"),
        countTasks("pending"),
        countTasks("completed"),
      ]);
      setCounts({ all, pending, completed });
    } catch {
      // Contagens são acessórias; um erro aqui não deve quebrar a tela.
    }
  }, []);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listTasks({ page, status, category });
      setData(res);
    } catch (err) {
      notify(getApiErrorMessage(err), "err");
    } finally {
      setLoading(false);
    }
  }, [page, status, category, notify]);

  useEffect(() => {
    reload();
  }, [reload]);

  useEffect(() => {
    reloadCounts();
  }, [reloadCounts]);

  function changeStatus(next) {
    setStatus(next);
    setPage(1);
  }

  function onCategoryFilter(e) {
    setCategory(e.target.value);
    setPage(1);
  }

  async function handleQuickAdd(e) {
    e.preventDefault();
    const title = quickTitle.trim();
    if (!title) {
      notify("O título é obrigatório.", "err");
      return;
    }
    setAdding(true);
    try {
      await createTask({ title, category_id: quickCat || null });
      setQuickTitle("");
      setQuickCat("");
      setPage(1);
      notify("Tarefa criada.");
      reload();
      reloadCounts();
    } catch (err) {
      notify(getApiErrorMessage(err), "err");
    } finally {
      setAdding(false);
    }
  }

  async function toggleDone(task) {
    if (task.access.permission === "view") {
      notify("Você só tem permissão de leitura nesta tarefa.", "err");
      return;
    }
    const done = task.status === "completed";
    try {
      await updateTask(task.id, { status: done ? "pending" : "completed" });
      notify(done ? "Tarefa reaberta." : "Tarefa concluída.");
      reload();
      reloadCounts();
    } catch (err) {
      notify(getApiErrorMessage(err), "err");
    }
  }

  const totalPages = Math.max(1, Math.ceil(data.count / PAGE_SIZE));
  const results = data.results;
  const showEmpty = !loading && results.length === 0;

  return (
    <main style={{ maxWidth: 940, margin: "0 auto", padding: "26px 18px 90px" }}>
      <h1 style={{ fontSize: 40, lineHeight: 1.1, margin: "8px 0 4px" }}>Tarefas</h1>
      <p style={{ margin: "0 0 26px", fontSize: 15, color: "var(--color-neutral-700)" }}>
        {counts.pending} pendente{counts.pending === 1 ? "" : "s"} · {counts.completed} concluída
        {counts.completed === 1 ? "" : "s"}
      </p>

      {/* Quick-add */}
      <form onSubmit={handleQuickAdd} style={{ display: "flex", gap: 10, marginBottom: 22, flexWrap: "wrap" }}>
        <input
          className="input"
          placeholder="Adicionar uma tarefa..."
          value={quickTitle}
          onChange={(e) => setQuickTitle(e.target.value)}
          aria-label="Nova tarefa"
          style={{ flex: 1, minWidth: 220, minHeight: 46, background: "var(--color-neutral-100)", borderColor: "transparent", boxShadow: "var(--shadow-sm)" }}
        />
        <select
          className="input"
          value={quickCat}
          onChange={(e) => setQuickCat(e.target.value)}
          aria-label="Categoria da nova tarefa"
          style={{ width: 170, minHeight: 46, background: "var(--color-neutral-100)", borderColor: "transparent" }}
        >
          <option value="">Sem categoria</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <button type="submit" className="btn btn-primary" disabled={adding} style={{ minHeight: 46, paddingInline: 22 }}>
          {adding ? "Adicionando..." : "Adicionar"}
        </button>
      </form>

      {/* Filtros */}
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 12, marginBottom: 6 }}>
        <div className="seg" role="group" aria-label="Filtrar por status">
          {STATUS_TABS.map((tab) => (
            <label key={tab.key} className="seg-opt">
              <input
                type="radio"
                name="ah-status"
                checked={status === tab.key}
                onChange={() => changeStatus(tab.key)}
              />
              {tab.label} <span style={{ opacity: 0.6 }}>{counts[tab.key]}</span>
            </label>
          ))}
        </div>
        <select
          className="input"
          value={category}
          onChange={onCategoryFilter}
          aria-label="Filtrar por categoria"
          style={{ width: "auto", minWidth: 180, background: "transparent" }}
        >
          <option value="">Todas as categorias</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {/* Lista */}
      {loading && (
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {[1, 2, 3, 4].map((n) => (
            <li
              key={n}
              style={{ height: 62, marginTop: 10, borderRadius: 999, background: "var(--color-neutral-200)", animation: "ah-pulse 1.2s ease-in-out infinite" }}
            />
          ))}
        </ul>
      )}

      {showEmpty && (
        <div style={{ textAlign: "center", padding: "64px 20px", color: "var(--color-neutral-700)" }}>
          <p style={{ fontFamily: "var(--font-heading)", fontSize: 22, margin: "0 0 6px", color: "var(--color-text)" }}>
            {status === "completed" ? "Nada concluído ainda" : counts.all > 0 ? "Nenhuma tarefa neste filtro" : "Sua lista está vazia"}
          </p>
          <p style={{ margin: 0, fontSize: 14 }}>Ajuste os filtros ou crie uma tarefa no campo acima.</p>
        </div>
      )}

      {!loading && results.length > 0 && (
        <>
          <ul style={{ listStyle: "none", margin: "14px 0 0", padding: 0 }}>
            {results.map((t) => {
              const done = t.status === "completed";
              const noEdit = t.access.permission === "view";
              const cat = t.category_id ? catById[t.category_id] : null;
              const due = dueInfo(t.due_date, done);
              const prio = PRIORITY[t.priority] || PRIORITY.medium;
              const shared = t.access.type === "shared";
              return (
                <li
                  key={t.id}
                  style={{ display: "flex", gap: 14, alignItems: "flex-start", padding: "15px 14px", borderBottom: "1px solid var(--color-divider)" }}
                >
                  <input
                    type="checkbox"
                    checked={done}
                    disabled={noEdit}
                    onChange={() => toggleDone(t)}
                    aria-label={`${done ? "Reabrir" : "Concluir"}: ${t.title}`}
                    style={{ width: 19, height: 19, marginTop: 3, cursor: noEdit ? "not-allowed" : "pointer", flex: "none" }}
                  />
                  <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: 6 }}>
                    <button
                      onClick={() => navigate(`/tasks/${t.id}`)}
                      style={{
                        background: "none",
                        border: 0,
                        padding: 0,
                        textAlign: "left",
                        font: "inherit",
                        fontSize: 16,
                        cursor: "pointer",
                        color: done ? "var(--color-neutral-600)" : "var(--color-text)",
                        textDecoration: done ? "line-through" : "none",
                      }}
                    >
                      {t.title}
                    </button>
                    <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10, fontSize: 12, color: "var(--color-neutral-700)" }}>
                      <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                        <span style={{ width: 7, height: 7, borderRadius: 999, background: prio.color, display: "inline-block" }} />
                        {prio.label}
                      </span>
                      {cat && (
                        <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                          <span style={{ width: 8, height: 8, borderRadius: 3, background: cat.color || "var(--color-neutral-400)", display: "inline-block" }} />
                          {cat.name}
                        </span>
                      )}
                      {due.has && (
                        <span style={{ color: due.late ? "var(--color-accent-700)" : "var(--color-neutral-700)", fontWeight: due.late ? 600 : 400 }}>
                          {due.label}
                        </span>
                      )}
                    </div>
                  </div>
                  {shared && (
                    <span
                      className={t.access.permission === "edit" ? "tag tag-accent-2" : "tag tag-neutral"}
                      style={{ flex: "none", marginTop: 2 }}
                    >
                      {t.access.permission === "edit" ? "Compartilhada · editar" : "Compartilhada · ver"}
                    </span>
                  )}
                </li>
              );
            })}
          </ul>

          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, marginTop: 22, fontSize: 13, color: "var(--color-neutral-700)" }}>
            <span>
              {data.count} tarefa{data.count === 1 ? "" : "s"} · página {page} de {totalPages}
            </span>
            <span style={{ display: "flex", gap: 8 }}>
              <button className="btn btn-secondary" disabled={!data.previous} onClick={() => setPage((p) => Math.max(1, p - 1))} style={{ height: 36 }}>
                Anterior
              </button>
              <button className="btn btn-secondary" disabled={!data.next} onClick={() => setPage((p) => p + 1)} style={{ height: 36 }}>
                Próxima
              </button>
            </span>
          </div>
        </>
      )}
    </main>
  );
}
