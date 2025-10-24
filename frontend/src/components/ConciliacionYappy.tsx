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

  // ==========================
  // Helpers de normalización
  // ==========================
  const getField = (row: any, key: string) => {
    if (!row || typeof row !== "object") return undefined;
    if (key in row) return row[key];
    const k = Object.keys(row).find((x) => x.toLowerCase() === key.toLowerCase());
    return k ? row[k] : undefined;
  };

  // Convierte fechas variadas a 'YYYY-MM-DD' (o null si imposible)
  const toYMD = (v: any): string | null => {
    if (v == null || v === "") return null;

    // 1) Date
    if (v instanceof Date && !isNaN(v.getTime())) {
      return v.toISOString().slice(0, 10);
    }

    // 2) Números de Excel (serial)
    if (typeof v === "number" && isFinite(v)) {
      // Excel base 1899-12-30 (maneja correctamente el bug de 1900)
      const excelEpoch = new Date(Date.UTC(1899, 11, 30));
      const ms = v * 24 * 60 * 60 * 1000;
      const d = new Date(excelEpoch.getTime() + ms);
      if (!isNaN(d.getTime())) return d.toISOString().slice(0, 10);
    }

    // 3) String
    const s = String(v).trim();
    if (!s) return null;

    // a) ISO-like
    // '2025-11-09' o '2025/11/09' o '2025-11-09T...'
    if (/\d{4}[-/]\d{2}[-/]\d{2}/.test(s)) {
      const clean = s.replace(/\//g, "-").slice(0, 10);
      const [Y, M, D] = clean.split("-").map((x) => parseInt(x, 10));
      if (Y && M >= 1 && M <= 12 && D >= 1 && D <= 31) {
        const d = new Date(Date.UTC(Y, M - 1, D));
        if (!isNaN(d.getTime())) return d.toISOString().slice(0, 10);
      }
    }

    // b) 'DD/MM/YYYY' o 'MM/DD/YYYY'
    if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(s)) {
      const [a, b, c] = s.split("/").map((x) => parseInt(x, 10));
      // Heurística: si a > 12 -> es DD/MM/YYYY
      // si a <= 12 y b > 12 -> es MM/DD/YYYY
      // si ambos <= 12, preferimos DD/MM/YYYY (por PA/ES)
      let D = a, M = b, Y = c;
      if (a <= 12 && b > 12) {
        // MM/DD/YYYY
        M = a; D = b;
      }
      const d = new Date(Date.UTC(Y, M - 1, D));
      if (!isNaN(d.getTime())) return d.toISOString().slice(0, 10);
    }

    // c) 'DD-MM-YYYY'
    if (/^\d{1,2}-\d{1,2}-\d{4}$/.test(s)) {
      const [d1, m1, y1] = s.split("-").map((x) => parseInt(x, 10));
      const d = new Date(Date.UTC(y1, m1 - 1, d1));
      if (!isNaN(d.getTime())) return d.toISOString().slice(0, 10);
    }

    // d) Último intento: Date.parse
    const parsed = new Date(s);
    if (!isNaN(parsed.getTime())) return parsed.toISOString().slice(0, 10);

    return null;
  };

  // ==========================
  // Datos del cierre / yappy
  // ==========================
  const detalleCierre = cierre.detalle_yappy || [];
  const fechaCierreRaw: any = cierre.meta?.fecha || "";
  const cierreYMD = toYMD(fechaCierreRaw); // <-- fecha del cierre normalizada

  const allRows = Array.isArray(yappy?.preview) ? yappy.preview : [];

  // Normalizamos la fecha de cada transacción Yappy
  const yappyRows = allRows.map((t: any) => {
    const f =
      getField(t, "fecha") ??
      getField(t, "Fecha") ??
      getField(t, "FECHA") ??
      getField(t, "date");

    return {
      ...t,
      _fechaOriginal: f,
      _fechaYMD: toYMD(f),
    };
  });

  // Filtrado por la fecha del cierre
  let filtered = yappyRows;
  if (cierreYMD) {
    filtered = yappyRows.filter((r: any) => r._fechaYMD === cierreYMD);
  }

  // Limitar a 20 (solo visual)
  const limited = filtered.slice(0, 20);

  // Utilidades de monto / formatos
  const parseNum = (v: any) => {
    if (v == null) return 0;
    if (typeof v === "number") return v;
    const s = String(v).trim().replace(/[^\d,-.]/g, "").replace(",", ".");
    const n = parseFloat(s);
    return isNaN(n) ? 0 : n;
  };

  const computeTotal = (t: any) => {
    const tot = parseNum(getField(t, "total"));
    if (Math.abs(tot) > 0.0001) return tot;
    const subtotal = parseNum(getField(t, "subtotal"));
    const propina = parseNum(getField(t, "propina"));
    const descuento = parseNum(getField(t, "descuento"));
    const impuesto = parseNum(getField(t, "impuesto"));
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
    const d = s.replace(/\D/g, "");
    const last8 = d.slice(-8);
    if (last8.length === 8) return `(+507) ${last8.slice(0, 4)}-${last8.slice(4)}`;
    return s;
  };

  return (
    <div style={styles.wrapper}>
      {/* Header info */}
      <div style={{ display: "flex", justifyContent: "center", marginBottom: 10 }}>
        <div style={styles.headerBox}>
          📍 {cierre.meta?.sucursal || "Sucursal no detectada"} — Fecha:{" "}
          {cierreYMD || "No detectada"}
        </div>
      </div>

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
                    <td style={{ ...styles.td, textAlign: "left" }}>{item.nombre}</td>
                    <td style={{ ...styles.td, textAlign: "right" }}>{item.monto}</td>
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

        {/* === Archivo Yappy (filtrado por la fecha del cierre) === */}
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
            💸 Archivo Yappy (transacciones del {cierreYMD || "—"})
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
              {limited.length > 0 ? (
                limited.map((t: any, i: number) => (
                  <tr
                    key={i}
                    style={{
                      borderBottom: "1px solid #eee",
                      background: i % 2 === 0 ? "#fff" : "#f4f6f8",
                    }}
                  >
                    <td style={styles.td}>
                      {t._fechaOriginal ?? t._fechaYMD ?? ""}
                    </td>
                    <td style={styles.td}>{getField(t, "referencia") || ""}</td>
                    <td style={styles.td}>{getField(t, "cliente") || ""}</td>
                    <td style={styles.td}>{fmtPhone(getField(t, "celular"))}</td>
                    <td style={styles.td}>{getField(t, "estado") || ""}</td>
                    <td style={{ ...styles.td, textAlign: "right" }}>
                      {fmtMonto(computeTotal(t))}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} style={styles.empty}>
                    No hay transacciones Yappy para esta fecha
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
            Mostrando {limited.length} transacciones del {cierreYMD || "—"}
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
    gridTemplateColumns: "30% 70%",
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
