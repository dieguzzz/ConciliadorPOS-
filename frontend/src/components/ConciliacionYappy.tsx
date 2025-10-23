// frontend/src/components/ConciliacionYappy.tsx
import React from "react";

interface Props {
  cierre: any;
  yappy: any;
}

const ConciliacionYappy: React.FC<Props> = ({ cierre, yappy }) => {
  if (!cierre || !yappy) {
    return (
      <div style={styles.infoMuted}>
        Carga ambos archivos para mostrar la conciliación.
      </div>
    );
  }

  const detalleCierre = cierre.detalle_yappy || [];
  const fechaCierreStr: string = cierre.meta?.fecha || "";
  console.log("🟣 Yappy recibido en frontend:", yappy);
  const allTx = Array.isArray(yappy?.preview) ? yappy.preview : [];

  // === Formato de texto ===
  const fmtMonto = (n: number | string) => {
    const num =
      typeof n === "number"
        ? n
        : parseFloat(String(n).replace(/[^\d.]/g, "")) || 0;
    return `B/. ${num.toFixed(2)}`;
  };

  const fmtPhone = (raw: any) => {
  if (!raw) return "";
  // Convertir siempre a string antes de usar .replace()
  const s = String(raw).trim();
  if (!s) return "";
  const d = s.replace(/\D/g, ""); // elimina todo lo que no sea número
  const last8 = d.slice(-8);
  if (last8.length === 8) {
    return `(+507) ${last8.slice(0, 4)}-${last8.slice(4)}`;
  }
  return s; // devuelve el original si no cumple formato
};


  // === UI ===
  return (
    <div style={styles.wrapper}>
      <h2 style={styles.h2}>💜 Conciliación Yappy</h2>
      <h4 style={styles.h4}>Transacciones Yappy (sin filtrar)</h4>

      {/* Encabezado con sucursal + fecha */}
      <div style={{ display: "flex", justifyContent: "center", marginBottom: 10 }}>
        <div style={styles.headerBox}>
          💜 {cierre.meta?.sucursal || "Sucursal no detectada"} — Fecha:{" "}
          {fechaCierreStr || "No detectada"}
        </div>
      </div>

      <div style={styles.columns}>
        {/* === Cierre POS === */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>📋 Cierre POS (detalle_yappy)</div>
          <table style={styles.table}>
            <thead>
              <tr style={styles.theadRow}>
                <th style={{ ...styles.th, textAlign: "left" }}>Cliente</th>
                <th style={{ ...styles.th, textAlign: "right" }}>Monto</th>
              </tr>
            </thead>
            <tbody>
              {detalleCierre.length > 0 ? (
                detalleCierre.map((item: any, idx: number) => (
                  <tr
                    key={idx}
                    style={{ background: "#fff", borderBottom: "1px solid #eee" }}
                  >
                    <td style={{ ...styles.td, textAlign: "left" }}>
                      {item.nombre}
                    </td>
                    <td style={{ ...styles.td, textAlign: "right" }}>
                      {item.monto}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={2} style={styles.empty}>
                    Sin Yappy en el cierre POS
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* === Archivo Yappy completo === */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>💜 Archivo Yappy (todas las transacciones)</div>
          <table style={styles.table}>
            <thead>
              <tr style={styles.theadRow}>
                <th style={{ ...styles.th, textAlign: "left" }}>Fecha</th>
                <th style={{ ...styles.th, textAlign: "left" }}>Cliente</th>
                <th style={{ ...styles.th, textAlign: "left" }}>Celular</th>
                <th style={{ ...styles.th, textAlign: "right" }}>Monto</th>
              </tr>
            </thead>
            <tbody>
              {allTx.length > 0 ? (
                allTx.map((t: any, i: number) => (
                  <tr
                    key={i}
                    style={{ background: "#fff", borderBottom: "1px solid #eee" }}
                  >
                    <td style={{ ...styles.td, textAlign: "left" }}>
                      {t.fecha || t["Fecha"] || t["Fecha y hora"] || t["FECHA"] || ""}
                    </td>
                    <td style={{ ...styles.td, textAlign: "left" }}>
                      {t.cliente || t["Cliente"] || ""}
                    </td>
                    <td style={{ ...styles.td, textAlign: "left" }}>
                      {fmtPhone(t.celular || t["Celular"] || "")}
                    </td>
                    <td style={{ ...styles.td, textAlign: "right" }}>
                      {fmtMonto(t.monto || t["Monto"] || "0")}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} style={styles.empty}>
                    No se encontraron transacciones Yappy
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// === estilos ===
const styles: Record<string, React.CSSProperties> = {
  wrapper: { background: "transparent", padding: "0.5rem 0 1.25rem" },
  h2: { textAlign: "center", color: "#6b5b95", fontWeight: 700, marginBottom: 4 },
  h4: { textAlign: "center", color: "#6b5b95", marginBottom: 8, fontWeight: 700 },
  headerBox: {
    textAlign: "center",
    color: "#6b5b95",
    fontWeight: 600,
    background: "#f8f6ff",
    padding: "8px 16px",
    borderRadius: 10,
    boxShadow: "0 2px 6px rgba(0,0,0,0.05)",
    minWidth: "fit-content",
  },
  columns: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "18px",
  },
  card: {
    background: "#fff",
    borderRadius: "14px",
    boxShadow: "0 6px 18px rgba(0,0,0,.08)",
    padding: "12px",
  },
  cardHeader: {
    color: "#6b5b95",
    fontWeight: 700,
    marginBottom: "8px",
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  table: { width: "100%", borderCollapse: "collapse", fontSize: ".95rem" },
  theadRow: { background: "#fff6d6", color: "#4b5563" },
  th: { padding: "8px 10px", fontWeight: 700 },
  td: { padding: "8px 10px" },
  empty: {
    textAlign: "center",
    color: "#9aa3af",
    fontStyle: "italic",
    padding: "14px",
  },
  infoMuted: {
    textAlign: "center",
    color: "#6b7280",
    background: "#f3f4f6",
    padding: "10px 12px",
    borderRadius: 10,
  },
};

export default ConciliacionYappy;
