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

  // ✅ Obtener datos del archivo Yappy
  const allTx = Array.isArray(yappy?.preview)
    ? yappy.preview.slice(0, 20) // 👈 solo muestra las primeras 20 filas
    : [];

  console.log("🟣 Yappy recibido en frontend:", yappy);

  const parseNum = (v: any) => {
    if (v == null) return 0;
    if (typeof v === "number") return v;
    const s = String(v).trim().replace(/[^\d,-.]/g, "").replace(",", ".");
    const n = parseFloat(s);
    return isNaN(n) ? 0 : n;
  };

  const computeTotal = (t: any) => {
    const tot = parseNum(t.total);
    if (Math.abs(tot) > 0.0001) return tot;
    const subtotal = parseNum(t.subtotal);
    const propina = parseNum(t.propina);
    const descuento = parseNum(t.descuento);
    const impuesto = parseNum(t.impuesto);
    return subtotal + propina - descuento + impuesto;
  };

  const fmtMonto = (n: number | string) => {
    const num =
      typeof n === "number"
        ? n
        : parseFloat(String(n).replace(/[^\d.-]/g, "")) || 0;
    return `B/. ${num.toFixed(2)}`;
  };

  const fmtPhone = (raw: any) => {
    if (!raw) return "";
    const s = String(raw).trim();
    if (!s) return "";
    const d = s.replace(/\D/g, "");
    const last8 = d.slice(-8);
    if (last8.length === 8) {
      return `(+507) ${last8.slice(0, 4)}-${last8.slice(4)}`;
    }
    return s;
  };

  return (
    <div style={styles.wrapper}>
      {/* === Encabezado === */}
      <div
        style={{ display: "flex", justifyContent: "center", marginBottom: 10 }}
      >
        <div style={styles.headerBox}>
          📍 {cierre.meta?.sucursal || "Sucursal no detectada"} — Fecha:{" "}
          {fechaCierreStr || "No detectada"}
        </div>
      </div>

      {/* === Columnas === */}
      <div style={styles.columns}>
        {/* === Cierre POS === */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>📋 Cierre POS (Detalles Yappy)</div>
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
                  <tr key={idx} style={{ borderBottom: "1px solid #eee" }}>
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

        {/* === Archivo Yappy === */}
        <div
          style={{
            background: "#f9fafb",
            borderRadius: "14px",
            padding: "2rem 2rem 1.5rem 2rem",
            border: "1px solid #ddd",
            boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
            maxHeight: "78vh",
            minHeight: "450px",
            overflowY: "auto",
            overflowX: "auto",
            width: "100%",
          }}
        >
          <div style={{ ...styles.cardHeader, marginBottom: "1rem" }}>
            💸 Archivo Yappy (todas las transacciones)
          </div>

          <table style={{ ...styles.table, width: "100%" }}>
            <thead>
              <tr style={styles.theadRow}>
                <th style={styles.th}>Fecha</th>
                <th style={styles.th}>Referencia</th>
                <th style={styles.th}>Cliente</th>
                <th style={styles.th}>Celular</th>
                <th style={styles.th}>Estado</th>
                <th style={{ ...styles.th, textAlign: "right" }}>Total</th>
              </tr>
            </thead>
            <tbody>
              {allTx.length > 0 ? (
                allTx.map((t: any, i: number) => (
                  <tr
                    key={i}
                    style={{
                      borderBottom: "1px solid #eee",
                      background: i % 2 === 0 ? "#fff" : "#f4f6f8",
                    }}
                  >
                    <td style={styles.td}>{t.fecha || ""}</td>
                    <td style={styles.td}>{t.referencia || ""}</td>
                    <td style={styles.td}>{t.cliente || ""}</td>
                    <td style={styles.td}>{fmtPhone(t.celular)}</td>
                    <td style={styles.td}>{t.estado || ""}</td>
                    <td style={{ ...styles.td, textAlign: "right" }}>
                      {fmtMonto(computeTotal(t))}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} style={styles.empty}>
                    Sin transacciones en el archivo Yappy
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          <p
            style={{
              color: "#555",
              fontSize: "0.85rem",
              marginTop: "0.75rem",
              textAlign: "right",
            }}
          >
            Mostrando {allTx.length} transacciones
          </p>
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    background: "transparent",
    padding: "1.5rem 2rem",
    width: "100%",
    maxWidth: "1150px",
    margin: "0 auto",
     boxSizing: "border-box",
  },
  h2: {
    textAlign: "center",
    color: "#6b5b95",
    fontWeight: 700,
    marginBottom: 4,
  },
  h4: {
    textAlign: "center",
    color: "#6b5b95",
    marginBottom: 8,
    fontWeight: 700,
  },
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
    gridTemplateColumns: "30% 70%", // 30% cierre, 70% archivo yappy
    gap: "25px",
    alignItems: "start",
    width: "100%",
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
  table: { width: "100%", borderCollapse: "collapse", fontSize: ".9rem" },
  theadRow: { background: "#fff6d6", color: "#4b5563" },
  th: { padding: "6px 8px", fontWeight: 700, textAlign: "left" },
  td: { padding: "6px 8px", verticalAlign: "middle" },
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
