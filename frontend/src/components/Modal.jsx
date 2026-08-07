import { useEffect } from "react";

// Modal genérico: backdrop escurecido, fecha com Esc ou clique fora.
// O conteúdo (form/ações) vem via children.
export default function Modal({ onClose, ariaLabel, role = "dialog", children }) {
  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="dialog-backdrop" onClick={onClose}>
      <div
        className="dialog"
        role={role}
        aria-modal="true"
        aria-label={ariaLabel}
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
}
