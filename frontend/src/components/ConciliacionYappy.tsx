// frontend/src/components/ConciliacionYappy.tsx
import React from "react";

interface Props {
  cierre: any;
  yappy: any;
}

const ConciliacionYappy: React.FC<Props> = ({ cierre, yappy }) => {
  // ====== Guardas ======
  if (!cierre)
    return (
      <div style={styles.infoMuted}>Carga primero el archivo de cierre POS.</div>
    );
  if (!yappy)
    return (
      <div style={styles.infoMuted}>Carga el archivo de Yappy para comparar.</div>
    );

  const detalleCierre: any[] = cierre?.detalle_yappy || [];
  const fechaCierreStr: string | undefined = cierre?.meta?.fecha;
  const fechaCierre = fechaCierreStr ? new Date(fechaCierreStr) : null;

  // ====== Filtrado por fecha ======
  const allTx: any[] = Array.isArray(yappy?.preview) ? yappy.preview : [];

  // 1) mismo día
  let filtradas = allTx.filter((t) => {
    if (!fechaCierre) return false;
    const ft = new Date(t.fecha);
    return (
      ft.getFullYear() === fechaCierre.getFullYear() &&
      ft.getMonth() === fechaCierre.getMonth() &&
      ft.getDate() === fechaCierre.getDate()
    );
  });

  let notaFiltro = "";
  // 2) si no hay, mismo mes y año (fallback amable)
  if (filtradas.length === 0 && fechaCierre) {
    filtradas = allTx.filter((t) => {
      const ft = new Date(t.fecha);
      return (
        ft.getFullYear() === fechaCierre.getFullYear() &&
        ft.getMonth() === fechaCierre.getMonth()
      );
    });
    if (filtradas.length > 0) {
      notaFiltro =
        "Mostrando transacciones del mismo mes porque no se encontraron del día exacto.";
    }
  }

  // ====== Utilidades ======
  const fmtMonto = (n: number | string) => {
    const num =
      typeof n === "number"
        ? n
        : parseFloat(String(n).toString().replace(/[^\d.]/g, "")) || 0;
    return `B/. ${num.toFixed(2)}`;
  };

  const fmtPhone = (raw: string) => {
    if (!raw) return "";
    const d = raw.replace(/\D/g, "");
    const last8 = d.slice(-8);
    if (last8.length === 8) return `(+507) ${last8.slice(0, 4)}-${last8.slice(4)}`;
    return raw;
  };

  // tipo de match para colorear filas del CIERRE (izquierda)
  const matchType = (nombre: string, montoTexto: string) => {
    const montoCierre = parseFloat(montoTexto.replace(/[^\d.]/g, "") || "0");
    const m2 = filtradas.find(
      (t) => Number(t.monto).toFixed(2) === montoCierre.toFixed(2)
    );
    if (!m2) return "none";
    if (m2.cliente?.trim().toLowerCase() === nombre?.trim().toLowerCase())
      return "full";
    return "amount";
  };

  const rowBg = (t: "none" | "amount" | "full") =>
    t === "full"
      ? "#d1fadf" // verde claro
      : t === "amount"
      ? "#ffe8cc" // naranja claro
      : "#ffffff"; // blanco

  // ====== UI ======
  return (
    <div style={styles.wrapper}>
      <h2 style={styles.h2}>💜 Conciliación Yappy</h2>
      <h4 style={styles.h4}>Transacciones Yappy</h4>
      <div style={{ textAlign: "center", color: "#6b5b95", fontWeight: 600, marginBottom: 10 }}>
        💜 Conciliación Yappy — Fecha: {fechaCierreStr || "No detectada"}
      </div>

      {notaFiltro && (
        <div style={styles.note}>
          {notaFiltro}
        </div>
      )}

      <div style={styles.columns}>
        {/* Izquierda: CIERRE POS */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            <span style={styles.cardHeaderIcon}>📑</span> Cierre POS
          </div>
          <table style={styles.table}>
            <thead>
              <tr style={styles.theadRow}>
                <th style={{ ...styles.th, textAlign: "left" }}>Cliente</th>
                <th style={{ ...styles.th, textAlign: "right" }}>Monto</th>
              </tr>
            </thead>
            <tbody>
              {detalleCierre.map((item, idx) => {
                const t = matchType(item.nombre, item.monto);
                return (
                  <tr key={idx} style={{ background: rowBg(t), borderBottom: "1px solid #eee" }}>
                    <td style={{ ...styles.td, textAlign: "left" }}>{item.nombre}</td>
                    <td style={{ ...styles.td, textAlign: "right" }}>{item.monto}</td>
                  </tr>
                );
              })}
              {detalleCierre.length === 0 && (
                <tr>
                  <td colSpan={2} style={styles.empty}>Sin Yappy en el cierre POS</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Derecha: YAPPY (filtrado) */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            <span style={styles.cardHeaderIcon}>💜</span> Archivo Yappy (filtrado)
          </div>
          <table style={styles.table}>
            <thead>
              <tr style={styles.theadRow}>
                <th style={{ ...styles.th, textAlign: "left" }}>Cliente</th>
                <th style={{ ...styles.th, textAlign: "left" }}>Celular</th>
                <th style={{ ...styles.th, textAlign: "right" }}>Monto</th>
              </tr>
            </thead>
            <tbody>
              {filtradas.length > 0 ? (
                filtradas.map((t, i) => (
                  <tr key={i} style={{ background: "#fff", borderBottom: "1px solid #eee" }}>
                    <td style={{ ...styles.td, textAlign: "left" }}>{t.cliente}</td>
                    <td style={{ ...styles.td, textAlign: "left" }}>{fmtPhone(t.celular)}</td>
                    <td style={{ ...styles.td, textAlign: "right" }}>{fmtMonto(t.monto)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} style={styles.empty}>
                    Sin transacciones para esta fecha
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Leyenda */}
      <div style={styles.legend}>
        <div style={styles.legendItem}>
          <span style={{ ...styles.dot, background: "#d1fadf" }} />
          <span>Coincide nombre y monto — <b>Verde</b></span>
        </div>
        <div style={styles.legendItem}>
          <span style={{ ...styles.dot, background: "#ffe8cc" }} />
          <span>Mismo monto, diferente nombre — <b>Naranja</b></span>
        </div>
        <div style={styles.legendItem}>
          <span style={{ ...styles.dot, background: "#ffffff", border: "1px solid #ddd" }} />
          <span>Sin coincidencia — <b>Blanco</b></span>
        </div>
      </div>
    </div>
  );
};

// ====== estilos inline para mantener tu estética actual ======
const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    background: "transparent",
    padding: "0.5rem 0.5rem 1.25rem",
  },
  h2: {
    textAlign: "center",
    color: "#6b5b95",
    fontWeight: 700,
    margin: "0 0 .25rem",
  },
  h4: {
    textAlign: "center",
    color: "#6b5b95",
    margin: "0 0 .5rem",
    fontWeight: 700,
  },
  note: {
    textAlign: "center",
    background: "#f6f0ff",
    color: "#6b5b95",
    border: "1px dashed #d9c9ff",
    padding: "6px 10px",
    borderRadius: 10,
    margin: "0 auto 10px",
    maxWidth: 680,
    fontSize: ".9rem",
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
  cardHeaderIcon: { fontSize: "1rem" },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: ".95rem",
  },
  theadRow: {
    background: "#fff6d6",
    color: "#4b5563",
  },
  th: {
    padding: "8px 10px",
    fontWeight: 700,
  },
  td: {
    padding: "8px 10px",
  },
  empty: {
    textAlign: "center",
    color: "#9aa3af",
    fontStyle: "italic",
    padding: "14px",
  },
  legend: {
    display: "flex",
    justifyContent: "center",
    gap: "18px",
    marginTop: "18px",
    flexWrap: "wrap",
    color: "#334155",
    fontSize: ".95rem",
  },
  legendItem: { display: "flex", alignItems: "center", gap: 8 },
  dot: {
    width: 16,
    height: 16,
    borderRadius: 4,
    display: "inline-block",
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
