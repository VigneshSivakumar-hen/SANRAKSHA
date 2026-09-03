import Dashboard from "./pages/Dashboard";

export default function App() {
  return (
    <div>
      <header
        style={{
          borderBottom: "1px solid var(--line)",
          padding: "16px 24px",
          display: "flex",
          alignItems: "baseline",
          gap: 12,
        }}
      >
        <span style={{ fontFamily: "var(--font-display)", fontSize: 22, letterSpacing: 0.3 }}>
          Sanraksha
        </span>
        <span style={{ color: "var(--text-muted)", fontSize: 13 }}>
          Landslide early-warning monitoring — Phase 1 prototype
        </span>
      </header>
      <Dashboard />
    </div>
  );
}
