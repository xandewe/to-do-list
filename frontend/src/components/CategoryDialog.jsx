import { useState } from "react";

import Modal from "./Modal";
import { getApiErrorMessage } from "../lib/apiErrors";

// Paleta do design (último valor = sem cor). A API aceita vazio ou #RRGGBB.
const COLOR_CHOICES = ["#c67139", "#7a8a5e", "#b2622d", "#56633f", "#82796a", ""];

// Dialog de criar/editar categoria. `category` null => criação.
// `onSave(payload)` deve persistir e pode lançar erro (ex.: nome duplicado 400),
// que é exibido inline.
export default function CategoryDialog({ category, onSave, onClose }) {
  const [name, setName] = useState(category?.name || "");
  const [description, setDescription] = useState(category?.description || "");
  const [color, setColor] = useState(category?.color ?? "#c67139");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const isEdit = Boolean(category);

  async function handleSave() {
    const trimmed = name.trim();
    if (!trimmed) {
      setError("O nome é obrigatório.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      await onSave({ name: trimmed, description, color });
    } catch (err) {
      setError(getApiErrorMessage(err));
      setBusy(false);
    }
  }

  return (
    <Modal ariaLabel={isEdit ? "Editar categoria" : "Nova categoria"} onClose={onClose}>
      <p className="dialog-title" style={{ margin: 0 }}>
        {isEdit ? "Editar categoria" : "Nova categoria"}
      </p>

      <div className="field">
        <label htmlFor="c-name">Nome</label>
        <input
          id="c-name"
          className="input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ minHeight: 42 }}
          autoFocus
        />
      </div>

      <div className="field">
        <label htmlFor="c-desc">Descrição</label>
        <input
          id="c-desc"
          className="input"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          style={{ minHeight: 42 }}
        />
      </div>

      <div className="field">
        <label id="c-color-label">Cor</label>
        <div role="group" aria-labelledby="c-color-label" style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {COLOR_CHOICES.map((hex) => {
            const selected = color === hex;
            return (
              <button
                key={hex || "none"}
                type="button"
                onClick={() => setColor(hex)}
                aria-label={hex ? `Cor ${hex}` : "Sem cor"}
                aria-pressed={selected}
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: 999,
                  cursor: "pointer",
                  background: hex || "var(--color-neutral-200)",
                  border: selected ? "3px solid var(--color-text)" : "1px solid var(--color-divider)",
                }}
              />
            );
          })}
        </div>
      </div>

      {error && (
        <p role="alert" className="alert alert-error">
          {error}
        </p>
      )}

      <div className="dialog-actions">
        <button className="btn btn-secondary" onClick={onClose} disabled={busy}>
          Cancelar
        </button>
        <button className="btn btn-primary" onClick={handleSave} disabled={busy}>
          {busy ? "Salvando..." : "Salvar"}
        </button>
      </div>
    </Modal>
  );
}
