import React, { useState } from "react";
import { fechaATexto } from "../utils/fechas";

interface Props {
  cierre: any;
  yappy: any;
}

const ConciliacionYappy: React.FC<Props> = ({ cierre, yappy }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

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
    const k = Object.keys(row).find(
      (x) => x.toLowerCase() === key.toLowerCase()
    );
    return k ? row[k] : undefined;
  };

  const toYMD = (v: any): string | null => {
    if (!v) return null;

    if (v instanceof Date && !isNaN(v.getTime())) {
      return v.toISOString().slice(0, 10);
    }

    if (typeof v === "number") {
      const excelEpoch = new Date(Date.UTC(1899, 11, 30));
      const d = new Date(excelEpoch.getTime() + v * 86400000);
      return !isNaN(d.getTime()) ? d.toISOString().slice(0, 10) : null;
    }

    let s = String(v).trim();
    s = s.replace(/^(lun|mar|mi[eé]|jue|vie|s[aá]b|dom)\.?\s+/i, "").trim();

    const ddmmyyyyMatch = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (ddmmyyyyMatch) {
      const [, day, month, year] = ddmmyyyyMatch;
      const d = new Date(Date.UTC(parseInt(year), parseInt(month) - 1, parseInt(day)));
      if (!isNaN(d.getTime())) {
        return d.toISOString().slice(0, 10);
      }
    }

    if (/^\d{4}-\d{2}-\d{2}/.test(s)) {
      return s.slice(0, 10);
    }

    const parsed = new Date(s);
    if (!isNaN(parsed.getTime())) {
      return parsed.toISOString().slice(0, 10);
    }

    return null;
  };

  // ==========================
  // Procesamiento principal
  // ==========================

  const detalleCierre = cierre.detalle_yappy || [];
  const fechaCierreRaw: any = cierre.meta?.fecha || "";
  const cierreYMD = toYMD(fechaCierreRaw);

  const allRows = Array.isArray(yappy?.preview) ? yappy.preview : [];
  const yappyRows = allRows.map((t: any) => {
    const f =
      getField(t, "fecha") ||
      getField(t, "Fecha") ||
      getField(t, "FECHA") ||
      getField(t, "date");
    const normal = toYMD(f);
    return { ...t, _fechaOriginal: f, _fechaYMD: normal };
  });

  // Filtrar por fecha
  let filtered = [];
  if (cierreYMD) {
    const cierreClean = cierreYMD.trim();
    filtered = yappyRows.filter((r: any) => {
      const yappyClean = (r._fechaYMD || "").trim();
      return yappyClean === cierreClean;
    });
  } else {
    filtered = yappyRows;
  }

  // ==========================
  // Utils numéricos y texto
  // ==========================
  const parseNum = (v: any) => {
    if (v == null) return 0;
    if (typeof v === "number") return v;
    const s = String(v).trim()
      .replace(/B\/\.\s*/g, "")
      .replace(/\$/g, "")
      .replace(/,/g, "")
      .trim();
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
    if (last8.length === 8)
      return `(+507) ${last8.slice(0, 4)}-${last8.slice(4)}`;
    return s;
  };

  const normalizeName = (name: string): string => {
    if (!name) return "";
    return name
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9\s]/g, "")
      .trim();
  };

  const similarity = (s1: string, s2: string): number => {
    const longer = s1.length > s2.length ? s1 : s2;
    const shorter = s1.length > s2.length ? s2 : s1;
    if (longer.length === 0) return 1.0;
    const editDistance = levenshtein(longer, shorter);
    return (longer.length - editDistance) / longer.length;
  };

  const levenshtein = (s1: string, s2: string): number => {
    const costs = [];
    for (let i = 0; i <= s1.length; i++) {
      let lastValue = i;
      for (let j = 0; j <= s2.length; j++) {
        if (i === 0) costs[j] = j;
        else if (j > 0) {
          let newValue = costs[j - 1];
          if (s1.charAt(i - 1) !== s2.charAt(j - 1))
            newValue = Math.min(Math.min(newValue, lastValue), costs[j]) + 1;
          costs[j - 1] = lastValue;
          lastValue = newValue;
        }
      }
      if (i > 0) costs[s2.length] = lastValue;
    }
    return costs[s2.length];
  };

  // 🔥 Buscar coincidencias
  interface Match {
    yappyRow: any;
    cierreItem: any;
    matchType: "exact" | "similar" | "amount_duplicate" | "none";
    color: string;
    similarity?: number;
  }

  const matches: Match[] = filtered.map((yappyRow: any) => {
    const yappyTotal = computeTotal(yappyRow);
    const yappyName = normalizeName(getField(yappyRow, "cliente") || "");

    let bestMatch: Match = {
      yappyRow,
      cierreItem: null,
      matchType: "none",
      color: "#fff",
    };

    let matchesFound = 0;

    for (const cierreItem of detalleCierre) {
      const cierreTotal = parseNum(cierreItem.monto);
      const cierreName = normalizeName(cierreItem.nombre || "");

      const amountMatch = Math.abs(yappyTotal - cierreTotal) <= 0.02;

      if (amountMatch) {
        matchesFound++;
        const sim = similarity(yappyName, cierreName);

        if (sim >= 0.7) {
          return {
            yappyRow,
            cierreItem,
            matchType: "exact" as const,
            color: "#d4edda",
            similarity: sim,
          };
        }

        if (bestMatch.matchType !== "exact") {
          bestMatch = {
            yappyRow,
            cierreItem,
            matchType: "similar" as const,
            color: "#fff3cd",
            similarity: sim,
          };
        }
      }
    }

    if (bestMatch.matchType === "similar" && matchesFound > 1) {
      bestMatch.matchType = "amount_duplicate";
      bestMatch.color = "#cfe2ff";
    }

    return bestMatch;
  });

  const validMatches = matches.filter((m) => m.matchType !== "none");

  // 🔥 ORDENAR: Verde primero, luego amarillo, luego azul
  const sortOrder = { exact: 1, similar: 2, amount_duplicate: 3 };
  validMatches.sort((a, b) => sortOrder[a.matchType] - sortOrder[b.matchType]);

  // Resumen por tipo
  const exactCount = validMatches.filter((m) => m.matchType === "exact").length;
  const similarCount = validMatches.filter((m) => m.matchType === "similar").length;
  const duplicateCount = validMatches.filter((m) => m.matchType === "amount_duplicate").length;

  // ==========================
  // Paginación
  // ==========================
  const totalPages = Math.ceil(validMatches.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentItems = validMatches.slice(startIndex, endIndex);

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  // ==========================
  // Render
  // ==========================
  return (
    <div style={styles.wrapper}>
      <h2 style={styles.title}>💸 Conciliación Yappy</h2>

      {/* Info de fecha y sucursal */}
      <div style={styles.infoBox}>
        <p style={styles.infoText}>
          📍 <strong>Sucursal:</strong> {cierre.meta?.sucursal || "—"}
        </p>
        <p style={styles.infoText}>
          📅 <strong>Fecha:</strong> {fechaATexto(fechaCierreRaw) || "No detectada"}
        </p>
      </div>

      {/* Resumen de coincidencias */}
      <div style={styles.summaryGrid}>
        <div style={{ ...styles.summaryCard, borderColor: "#28a745" }}>
          <div style={styles.summaryLabel}>✅ Coincidencias Exactas</div>
          <div style={{ ...styles.summaryAmount, color: "#28a745" }}>
            {exactCount}
          </div>
          <div style={styles.summaryCount}>Nombre + Monto</div>
        </div>

        <div style={{ ...styles.summaryCard, borderColor: "#ffc107" }}>
          <div style={styles.summaryLabel}>⚠️ Coincidencias Parciales</div>
          <div style={{ ...styles.summaryAmount, color: "#ffc107" }}>
            {similarCount}
          </div>
          <div style={styles.summaryCount}>Solo Monto</div>
        </div>

        <div style={{ ...styles.summaryCard, borderColor: "#17a2b8" }}>
          <div style={styles.summaryLabel}>🔄 Montos Duplicados</div>
          <div style={{ ...styles.summaryAmount, color: "#17a2b8" }}>
            {duplicateCount}
          </div>
          <div style={styles.summaryCount}>Múltiples con mismo monto</div>
        </div>
      </div>

      {/* Tabla de conciliación */}
      <div style={styles.columns}>
        {/* Cierre POS */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>📋 Cierre POS (Detalles Yappy)</div>
          <table style={styles.table}>
            <thead>
              <tr style={styles.theadRow}>
                <th style={{ ...styles.th, textAlign: "left" }}>Cliente</th>
                <th style={{ ...styles.th, textAlign: "right" }}>Monto</th>
                <th style={{ ...styles.th, textAlign: "right" }}>Total</th>
              </tr>
            </thead>
            <tbody>
              {detalleCierre.length > 0 ? (
                <>
                  {detalleCierre.map((item: any, idx: number) => {
                    // Buscar si este item tiene match
                    const match = validMatches.find(
                      (m) => m.cierreItem?.nombre === item.nombre
                    );
                    const bgColor = match?.color || "#fff";

                    // Calcular total acumulado hasta esta fila
                    const totalAcumulado = detalleCierre
                      .slice(0, idx + 1)
                      .reduce((sum: number, it: any) => {
                        const montoStr = it.monto || "0";
                        const montoNum = parseFloat(montoStr.replace(/[^\d.-]/g, "")) || 0;
                        return sum + montoNum;
                      }, 0);

                    return (
                      <tr
                        key={idx}
                        style={{ borderBottom: "1px solid #eee", backgroundColor: bgColor }}
                      >
                        <td style={{ ...styles.td, textAlign: "left" }}>
                          {item.nombre}
                        </td>
                        <td style={{ ...styles.td, textAlign: "right" }}>
                          {item.monto}
                        </td>
                        <td style={{ ...styles.td, textAlign: "right", fontWeight: 600, color: "#6b5b95" }}>
                          B/. {totalAcumulado.toFixed(2)}
                        </td>
                      </tr>
                    );
                  })}
                  {/* Fila de total */}
                  <tr style={{ 
                    borderTop: "2px solid #333", 
                    backgroundColor: "#f8f9fa",
                    fontWeight: "bold"
                  }}>
                    <td style={{ ...styles.td, textAlign: "left", fontWeight: "bold" }}>
                      TOTAL
                    </td>
                    <td style={{ ...styles.td, textAlign: "right", fontWeight: "bold" }}>
                      {(() => {
                        const total = detalleCierre.reduce((sum: number, it: any) => {
                          const montoStr = it.monto || "0";
                          const montoNum = parseFloat(montoStr.replace(/[^\d.-]/g, "")) || 0;
                          return sum + montoNum;
                        }, 0);
                        return `B/. ${total.toFixed(2)}`;
                      })()}
                    </td>
                    <td style={{ ...styles.td, textAlign: "right", fontWeight: "bold", color: "#6b5b95" }}>
                      {(() => {
                        const total = detalleCierre.reduce((sum: number, it: any) => {
                          const montoStr = it.monto || "0";
                          const montoNum = parseFloat(montoStr.replace(/[^\d.-]/g, "")) || 0;
                          return sum + montoNum;
                        }, 0);
                        return `B/. ${total.toFixed(2)}`;
                      })()}
                    </td>
                  </tr>
                </>
              ) : (
                <tr>
                  <td colSpan={3} style={styles.empty}>
                    Sin Yappy en el cierre POS
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Yappy filtrado */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            💸 Archivo Yappy (coincidencias del {cierreYMD || "—"})
          </div>

          <div style={styles.tableContainer}>
            <table style={styles.table}>
              <thead>
                <tr style={styles.theadRow}>
                  <th style={styles.th}>Fecha</th>
                  <th style={styles.th}>Referencia</th>
                  <th style={styles.th}>Cliente</th>
                  <th style={styles.th}>Celular</th>
                  <th style={styles.th}>Estado</th>
                  <th style={{ ...styles.th, textAlign: "right" }}>Total</th>
                  <th style={styles.th}>Match POS</th>
                </tr>
              </thead>
              <tbody>
                {currentItems.length > 0 ? (
                  currentItems.map((match: Match, i: number) => {
                    const t = match.yappyRow;
                    return (
                      <tr
                        key={i}
                        style={{
                          borderBottom: "1px solid #eee",
                          backgroundColor: match.color,
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
                        <td style={{ ...styles.td, fontSize: "0.8rem" }}>
                          {match.cierreItem?.nombre || "—"}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={7} style={styles.empty}>
                      No hay coincidencias para esta fecha
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Paginación */}
          {totalPages > 1 && (
            <div style={styles.pagination}>
              <button
                onClick={handlePrevPage}
                disabled={currentPage === 1}
                style={{
                  ...styles.pageButton,
                  opacity: currentPage === 1 ? 0.5 : 1,
                  cursor: currentPage === 1 ? "not-allowed" : "pointer",
                }}
              >
                ← Anterior
              </button>
              <span style={styles.pageInfo}>
                Página {currentPage} de {totalPages} ({validMatches.length} coincidencias)
              </span>
              <button
                onClick={handleNextPage}
                disabled={currentPage === totalPages}
                style={{
                  ...styles.pageButton,
                  opacity: currentPage === totalPages ? 0.5 : 1,
                  cursor: currentPage === totalPages ? "not-allowed" : "pointer",
                }}
              >
                Siguiente →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    background: "#fff",
    borderRadius: "12px",
    padding: "1.5rem",
    marginBottom: "2rem",
    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
  },
  title: {
    color: "#6b5b95",
    marginBottom: "1rem",
    fontSize: "1.3rem",
    fontWeight: "700",
  },
  infoBox: {
    background: "#f8f6ff",
    padding: "12px",
    borderRadius: "8px",
    marginBottom: "1rem",
  },
  infoText: {
    margin: "4px 0",
    fontSize: "0.95rem",
    color: "#4b5563",
  },
  summaryGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: "1rem",
    marginBottom: "1.5rem",
  },
  summaryCard: {
    background: "#fff",
    border: "2px solid",
    borderRadius: "10px",
    padding: "1rem",
    textAlign: "center" as const,
  },
  summaryLabel: {
    fontSize: "0.85rem",
    color: "#6b7280",
    fontWeight: "600",
    marginBottom: "0.5rem",
  },
  summaryAmount: {
    fontSize: "1.5rem",
    fontWeight: "700",
    marginBottom: "0.25rem",
  },
  summaryCount: {
    fontSize: "0.8rem",
    color: "#9ca3af",
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
    borderRadius: "10px",
    border: "1px solid #e5e7eb",
    padding: "12px",
    maxHeight: "78vh",
    overflowY: "auto" as const,
  },
  cardHeader: {
    color: "#6b5b95",
    fontWeight: 700,
    marginBottom: "8px",
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  tableContainer: {
    overflowX: "auto" as const,
    borderRadius: "8px",
  },
  table: { width: "100%", borderCollapse: "collapse" as const, fontSize: ".9rem" },
  theadRow: { background: "#fff6d6", color: "#4b5563" },
  th: { padding: "10px 8px", fontWeight: 700, textAlign: "left" as const, borderBottom: "2px solid #6b5b95" },
  td: { padding: "8px", verticalAlign: "middle" as const },
  empty: {
    textAlign: "center" as const,
    color: "#9aa3af",
    fontStyle: "italic",
    padding: "14px",
  },
  infoMuted: {
    textAlign: "center" as const,
    color: "#6b7280",
    background: "#f3f4f6",
    padding: "10px 12px",
    borderRadius: 10,
  },
  pagination: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: "1rem",
    paddingTop: "1rem",
    borderTop: "1px solid #e5e7eb",
  },
  pageButton: {
    background: "#6b5b95",
    color: "#fff",
    border: "none",
    padding: "10px 20px",
    borderRadius: "8px",
    fontWeight: 600,
    fontSize: "0.9rem",
    cursor: "pointer",
  },
  pageInfo: {
    color: "#6b7280",
    fontSize: "0.9rem",
    fontWeight: 600,
  },
};

export default ConciliacionYappy;