"use client";

import { useState } from "react";

interface BancoPreviewProps {
  data: any;
}

export default function BancoPreview({ data }: BancoPreviewProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 15;

  if (!data || !data.preview) return null;

  const { total_registros, preview, filtros } = data;

  // Paginación
  const totalPages = Math.ceil(preview.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentItems = preview.slice(startIndex, endIndex);

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  // Agrupar por tipo y calcular totales
  const claveTotal = preview
    .filter((r: any) => r.tipo === "CLAVE")
    .reduce((sum: number, r: any) => sum + (r.monto || 0), 0);

  const visaTotal = preview
    .filter((r: any) => r.tipo === "VISA")
    .reduce((sum: number, r: any) => sum + (r.monto || 0), 0);

  const totalGeneral = preview.reduce(
    (sum: number, r: any) => sum + (r.monto || 0),
    0
  );

  const claveCount = preview.filter((r: any) => r.tipo === "CLAVE").length;
  const visaCount = preview.filter((r: any) => r.tipo === "VISA").length;

  return (
    <div style={styles.wrapper}>
      <h2 style={styles.title}>🏦 Movimientos Bancarios</h2>
      
      {/* Filtros aplicados */}
      {filtros && (filtros.fecha || filtros.sucursal) && (
        <div style={styles.infoBox}>
          {filtros.fecha && (
            <p style={styles.infoText}>
              📅 <strong>Fecha:</strong> {filtros.fecha}
            </p>
          )}
          {filtros.sucursal && (
            <p style={styles.infoText}>
              🏢 <strong>Sucursal:</strong> {filtros.sucursal}
            </p>
          )}
        </div>
      )}

      {/* Resumen de totales */}
      <div style={styles.summaryGrid}>
        <div style={{ ...styles.summaryCard, borderColor: "#3b82f6" }}>
          <div style={styles.summaryLabel}>💳 CLAVE</div>
          <div style={{ ...styles.summaryAmount, color: "#3b82f6" }}>
            B/. {claveTotal.toFixed(2)}
          </div>
          <div style={styles.summaryCount}>{claveCount} transacciones</div>
        </div>

        <div style={{ ...styles.summaryCard, borderColor: "#a855f7" }}>
          <div style={styles.summaryLabel}>💎 VISA/MasterCard</div>
          <div style={{ ...styles.summaryAmount, color: "#a855f7" }}>
            B/. {visaTotal.toFixed(2)}
          </div>
          <div style={styles.summaryCount}>{visaCount} transacciones</div>
        </div>

        <div style={{ ...styles.summaryCard, borderColor: "#6b5b95" }}>
          <div style={styles.summaryLabel}>📊 Total General</div>
          <div style={{ ...styles.summaryAmount, color: "#6b5b95" }}>
            B/. {totalGeneral.toFixed(2)}
          </div>
          <div style={styles.summaryCount}>{total_registros} movimientos</div>
        </div>
      </div>

      {/* Tabla */}
      <div style={styles.tableContainer}>
        <table style={styles.table}>
          <thead>
            <tr style={styles.theadRow}>
              <th style={styles.th}>Fecha</th>
              <th style={styles.th}>Descripción</th>
              <th style={styles.th}>Sucursal</th>
              <th style={{ ...styles.th, textAlign: "center" }}>Tipo</th>
              <th style={styles.th}>Código</th>
              <th style={{ ...styles.th, textAlign: "right" }}>Monto</th>
            </tr>
          </thead>
          <tbody>
            {currentItems.map((row: any, index: number) => (
              <tr
                key={index}
                style={{
                  ...styles.tr,
                  backgroundColor:
                    row.tipo === "CLAVE"
                      ? "rgba(59, 130, 246, 0.05)"
                      : "rgba(168, 85, 247, 0.05)",
                }}
              >
                <td style={styles.td}>{row.fecha}</td>
                <td style={{ ...styles.td, fontSize: "0.85rem", maxWidth: "300px" }}>
                  {row.descripcion}
                </td>
                <td style={{ ...styles.td, fontWeight: "600" }}>
                  {row.sucursal}
                </td>
                <td style={{ ...styles.td, textAlign: "center" }}>
                  <span
                    style={{
                      ...styles.badge,
                      backgroundColor:
                        row.tipo === "CLAVE" ? "#3b82f6" : "#a855f7",
                    }}
                  >
                    {row.tipo}
                  </span>
                </td>
                <td style={{ ...styles.td, fontFamily: "monospace", fontSize: "0.85rem" }}>
                  {row.codigo}
                </td>
                <td style={{ ...styles.td, textAlign: "right", fontWeight: "600" }}>
                  B/. {row.monto.toFixed(2)}
                </td>
              </tr>
            ))}
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
            Página {currentPage} de {totalPages}
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
  );
}

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
  tableContainer: {
    overflowX: "auto" as const,
    borderRadius: "8px",
    border: "1px solid #e5e7eb",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse" as const,
    fontSize: "0.9rem",
  },
  theadRow: {
    background: "#fff6d6",
    color: "#4b5563",
  },
  th: {
    padding: "12px",
    fontWeight: "700" as const,
    textAlign: "left" as const,
    borderBottom: "2px solid #6b5b95",
  },
  tr: {
    borderBottom: "1px solid #e5e7eb",
    transition: "background-color 0.2s",
  },
  td: {
    padding: "12px",
    verticalAlign: "middle" as const,
  },
  badge: {
    padding: "4px 12px",
    borderRadius: "6px",
    color: "#fff",
    fontSize: "0.8rem",
    fontWeight: "600" as const,
    display: "inline-block",
  },
  pagination: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: "1.5rem",
    paddingTop: "1rem",
    borderTop: "1px solid #e5e7eb",
  },
  pageButton: {
    background: "#6b5b95",
    color: "#fff",
    border: "none",
    padding: "10px 20px",
    borderRadius: "8px",
    fontWeight: "600" as const,
    fontSize: "0.9rem",
    cursor: "pointer",
    transition: "background 0.3s",
  },
  pageInfo: {
    color: "#6b7280",
    fontSize: "0.9rem",
    fontWeight: "600" as const,
  },
};