// Helpers de apresentação das tarefas (rótulos e cores), compartilhados entre a
// lista e o detalhe.

export const PRIORITY = {
  low: { label: "Baixa", color: "var(--color-neutral-400)" },
  medium: { label: "Média", color: "var(--color-accent-2-500)" },
  high: { label: "Alta", color: "var(--color-accent)" },
};

export const STATUS_LABEL = {
  pending: "Pendente",
  completed: "Concluída",
};

// ISO -> "YYYY-MM-DD" no fuso local, para <input type="date">.
export function toDateInput(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

// "YYYY-MM-DD" -> ISO (meio-dia local, evita virada de dia por fuso). Vazio => null.
export function fromDateInput(value) {
  return value ? new Date(`${value}T12:00:00`).toISOString() : null;
}

// Rótulo amigável do prazo + se está atrasado (passado e ainda pendente).
export function dueInfo(iso, done) {
  if (!iso) return { has: false };
  const d = new Date(iso);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const dDay = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const days = Math.round((dDay - today) / 86400000);

  let label;
  if (days === 0) label = "Hoje";
  else if (days === 1) label = "Amanhã";
  else if (days === -1) label = "Ontem";
  else label = d.toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });

  const late = days < 0 && !done;
  return { has: true, label: late ? `${label} · atrasada` : label, late };
}
