import { useAuth } from "../context/AuthContext";

// Home autenticada — placeholder até a Task 21 trazer a lista de tarefas.
// A top nav e o logout ficam no AppLayout.
export default function Dashboard() {
  const { user } = useAuth();
  const first = user?.first_name || user?.email;

  return (
    <main style={{ maxWidth: 940, margin: "0 auto", padding: "26px 18px 90px" }}>
      <h1 style={{ fontSize: 40, lineHeight: 1.1, margin: "8px 0 4px" }}>Olá, {first}</h1>
      <p style={{ margin: 0, fontSize: 15, color: "var(--color-neutral-700)" }}>
        A lista de tarefas chega na próxima etapa. Enquanto isso, organize suas{" "}
        <strong>categorias</strong> pelo menu acima.
      </p>
    </main>
  );
}
