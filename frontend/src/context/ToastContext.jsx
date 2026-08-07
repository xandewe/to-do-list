import { createContext, useContext, useState, useCallback, useRef, useEffect } from "react";

const ToastContext = createContext(null);

// Toast global no estilo do design: pílula fixa no rodapé, some sozinho.
// `notify(msg, kind)` — kind "ok" (padrão) ou "err".
export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null);
  const timer = useRef(null);

  const notify = useCallback((msg, kind = "ok") => {
    clearTimeout(timer.current);
    setToast({ msg, kind });
    timer.current = setTimeout(() => setToast(null), 2600);
  }, []);

  useEffect(() => () => clearTimeout(timer.current), []);

  const isError = toast?.kind === "err";

  return (
    <ToastContext.Provider value={{ notify }}>
      {children}
      {toast && (
        <div
          role="status"
          aria-live="polite"
          style={{
            position: "fixed",
            left: "50%",
            bottom: 26,
            transform: "translateX(-50%)",
            zIndex: 50,
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "12px 20px",
            borderRadius: 999,
            boxShadow: "var(--shadow-lg)",
            fontSize: 14,
            background: isError ? "var(--color-accent-100)" : "var(--color-neutral-900)",
            color: isError ? "var(--color-accent-800)" : "var(--color-neutral-100)",
          }}
        >
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: 999,
              display: "inline-block",
              background: isError ? "var(--color-accent)" : "var(--color-accent-2-400)",
            }}
          />
          {toast.msg}
        </div>
      )}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (context === null) {
    throw new Error("useToast deve ser usado dentro de um ToastProvider");
  }
  return context;
}
