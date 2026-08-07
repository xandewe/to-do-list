import { useState } from "react";

import Modal from "./Modal";

// Diálogo de confirmação reutilizável. `onConfirm` pode ser assíncrono; enquanto
// roda, o botão fica em estado ocupado para evitar duplo clique.
export default function ConfirmDialog({ title, body, cta = "Confirmar", onConfirm, onClose }) {
  const [busy, setBusy] = useState(false);

  async function handleConfirm() {
    setBusy(true);
    try {
      await onConfirm();
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal role="alertdialog" ariaLabel={title} onClose={onClose}>
      <p className="dialog-title" style={{ margin: 0 }}>
        {title}
      </p>
      <p className="dialog-body" style={{ margin: 0 }}>
        {body}
      </p>
      <div className="dialog-actions">
        <button className="btn btn-secondary" onClick={onClose} disabled={busy}>
          Cancelar
        </button>
        <button className="btn btn-primary" onClick={handleConfirm} disabled={busy}>
          {busy ? "Aguarde..." : cta}
        </button>
      </div>
    </Modal>
  );
}
