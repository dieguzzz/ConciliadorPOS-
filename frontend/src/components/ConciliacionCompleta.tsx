import React, { useState } from "react";
import { getApiBase } from "../utils/api";

export default function ConciliacionCompleta() {
  const [files, setFiles] = useState({
    cierre: null,
    yappy: null,
    banco: null,
  });
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (key: string, file: File | null) => {
    setFiles((prev) => ({ ...prev, [key]: file }));
  };

  const handleConciliar = async () => {
    if (!files.cierre || !files.yappy || !files.banco) {
      alert("Por favor selecciona los tres archivos (Cierre, Yappy y Banco).");
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("cierre", files.cierre);
    formData.append("yappy", files.yappy);
    formData.append("banco", files.banco);

    try {
      const apiBase = getApiBase();
      const res = await fetch(`${apiBase}/api/conciliar_auto`, {
        method: "POST",
        body: formData,
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Error desconocido");
      setData(json);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const colorMap = {
    COINCIDE: "#c8f7c5", // verde
    MONTO_OK_NOMBRE_DIF: "#ffeaa7", // amarillo
    SIN_MATCH: "#f1f2f6", // gris
  };

  return (
    <div
      style={{
        padding: "1.5rem 2rem",
        width: "100%",
        maxWidth: "1100px",
        margin: "0 auto",
      }}
    >
      <h2
        style={{
          textAlign: "center",
          color: "#6b5b95",
          marginBottom: "1rem",
        }}
      >
        🧮 Conciliación Completa
      </h2>

      {/* === SUBIDA DE ARCHIVOS === */}
      <div
        style={{
          display: "flex",
          gap: "1rem",
          justifyContent: "center",
          flexWrap: "wrap",
          marginBottom: "1rem",
        }}
      >
        {["cierre", "yappy", "banco"].map((key) => (
          <div
            key={key}
            style={{
              background: "#fff",
              padding: "1rem",
              borderRadius: "10px",
              boxShadow: "0 4px 8px rgba(0,0,0,0.08)",
              minWidth: "250px",
            }}
          >
            <h4 style={{ marginBottom: "0.5rem", color: "#6b5b95" }}>
              {key === "cierre"
                ? "📂 Archivo Cierre"
                : key === "yappy"
                ? "💜 Archivo Yappy"
                : "🏦 Archivo Banco"}
            </h4>
            <input
              type="file"
              accept=".xlsx,.xls,.xlsm,.xlsb,.csv,.ods"
              onChange={(e) => handleChange(key, e.target.files?.[0] || null)}
              style={{
                display: "block",
                width: "100%",
                padding: "8px",
                borderRadius: "8px",
                border: "1px solid #ddd",
              }}
            />
          </div>
        ))}
      </div>

      <div style={{ textAlign: "center" }}>
        <button
          onClick={handleConciliar}
          disabled={loading}
          style={{
            background: "#6b5b95",
            color: "#fff",
            border: "none",
            padding: "10px 20px",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: "1rem",
          }}
        >
          {loading ? "Procesando..." : "Conciliar"}
        </button>
      </div>

      {/* === RESULTADOS === */}
      <div style={{ marginTop: "2rem" }}>
        {error && (
          <div
            style={{
              background: "#fee",
              color: "#900",
              padding: "10px",
              borderRadius: "8px",
              textAlign: "center",
            }}
          >
            ⚠️ Error: {error}
          </div>
        )}

        {loading && (
          <div style={{ textAlign: "center", marginTop: "1rem" }}>
            <p>🔄 Conciliando transacciones...</p>
            <div
              style={{
                width: "200px",
                height: "10px",
                background: "#eee",
                margin: "0.5rem auto",
                borderRadius: "8px",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: "100%",
                  height: "100%",
                  background: "#6b5b95",
                  animation: "progress 2s infinite",
                }}
              ></div>
            </div>
          </div>
        )}

        {data && !loading && (
          <>
            <h4 style={{ marginBottom: "0.5rem", color: "#444" }}>
              Resultado: {data.total_registros} registros
            </h4>
            <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
              {Object.entries(data.resumen || {}).map(([estado, count]) => (
                <div
                  key={estado}
                  style={{
                    background: colorMap[estado],
                    padding: "0.5rem 1rem",
                    borderRadius: "8px",
                    fontWeight: 600,
                  }}
                >
                  {estado}: {String(count)}
                </div>
              ))}
            </div>

            <div
              style={{
                background: "#fff",
                borderRadius: "10px",
                padding: "1rem",
                boxShadow: "0 4px 10px rgba(0,0,0,0.08)",
                overflowX: "auto",
                maxHeight: "65vh",
                overflowY: "auto",
              }}
            >
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  fontSize: "0.9rem",
                }}
              >
                <thead>
                  <tr style={{ background: "#f0f0f0" }}>
                    <th style={{ padding: "8px" }}>Fecha</th>
                    <th style={{ padding: "8px" }}>Cliente</th>
                    <th style={{ padding: "8px" }}>Monto</th>
                    <th style={{ padding: "8px" }}>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {data.preview.map((row: any, i: number) => (
                    <tr
                      key={i}
                      style={{
                        background: colorMap[row.estado] || "#fff",
                        borderBottom: "1px solid #eee",
                      }}
                    >
                      <td style={{ padding: "8px" }}>{row.fecha}</td>
                      <td style={{ padding: "8px" }}>{row.cliente}</td>
                      <td style={{ padding: "8px" }}>B/. {row.monto?.toFixed(2)}</td>
                      <td style={{ padding: "8px", fontWeight: 600 }}>
                        {row.estado}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
