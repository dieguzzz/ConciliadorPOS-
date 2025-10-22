import React from "react";

export default function TablaConciliacionYappy({ data }) {
  if (!data || !data.cierre || !data.yappy) {
    return (
      <p style={{ color: "#777", textAlign: "center" }}>
        Carga el archivo de Cierre y el de Yappy para ver la conciliación.
      </p>
    );
  }

  const cierre = data.cierre.detalle_yappy || [];
  const fechaCierre = data.cierre.fecha;
  const yappy = data.yappy.preview?.filter(
    (t) => t.fecha === fechaCierre
  ) || [];

  // comparar y colorear
  const comparar = cierre.map((c) => {
    const montoNum = parseFloat(c.monto.replace(/[^\d.]/g, ""));
    const match = yappy.find(
      (y) =>
        Math.abs(y.monto - montoNum) < 0.01 &&
        y.cliente.trim().toLowerCase() === c.nombre.trim().toLowerCase()
    );
    const similares = yappy.filter((y) => Math.abs(y.monto - montoNum) < 0.01);
    return {
      ...c,
      match,
      similares,
      color: match ? "#b9f6ca" : similares.length > 0 ? "#ffe0b2" : "#fff",
    };
  });

  // formatear celular
  const formatCelular = (num) => {
    if (!num) return "";
    return num.replace(
      /^\+507(\d{4})(\d{4})$/,
      "(+507) $1-$2"
    );
  };

  return (
    <div style={{ textAlign: "center" }}>
      <h2 style={{ color: "#6b5b95" }}>💜 Conciliación Yappy</h2>
      <h4 style={{ color: "#6b5b95" }}>Fecha: {fechaCierre || "No detectada"}</h4>

      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "1rem",
          flexWrap: "wrap",
          marginTop: "1rem",
        }}
      >
        {/* Cierre POS */}
        <div
          style={{
            flex: "1 1 400px",
            background: "#fff",
            borderRadius: "10px",
            boxShadow: "0 3px 10px rgba(0,0,0,0.1)",
            overflow: "hidden",
          }}
        >
          <h4
            style={{
              background: "#f4f1ff",
              padding: "0.7rem",
              margin: 0,
              color: "#6b5b95",
            }}
          >
            📄 Cierre POS
          </h4>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
            }}
          >
            <thead>
              <tr style={{ background: "#fef9e7", textAlign: "left" }}>
                <th style={{ padding: "10px" }}>Cliente</th>
                <th style={{ padding: "10px", textAlign: "right" }}>Monto</th>
              </tr>
            </thead>
            <tbody>
              {comparar.map((c, i) => (
                <tr
                  key={i}
                  style={{
                    background: c.color,
                    borderBottom: "1px solid #eee",
                  }}
                >
                  <td style={{ padding: "8px" }}>{c.nombre}</td>
                  <td style={{ padding: "8px", textAlign: "right" }}>
                    {c.monto}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Yappy */}
        <div
          style={{
            flex: "1 1 400px",
            background: "#fff",
            borderRadius: "10px",
            boxShadow: "0 3px 10px rgba(0,0,0,0.1)",
            overflow: "hidden",
          }}
        >
          <h4
            style={{
              background: "#f4f1ff",
              padding: "0.7rem",
              margin: 0,
              color: "#6b5b95",
            }}
          >
            💜 Archivo Yappy (filtrado)
          </h4>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
            }}
          >
            <thead>
              <tr style={{ background: "#fef9e7", textAlign: "left" }}>
                <th style={{ padding: "10px" }}>Cliente</th>
                <th style={{ padding: "10px" }}>Celular</th>
                <th style={{ padding: "10px", textAlign: "right" }}>Monto</th>
              </tr>
            </thead>
            <tbody>
              {yappy.length > 0 ? (
                yappy.map((y, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #eee" }}>
                    <td style={{ padding: "8px" }}>{y.cliente}</td>
                    <td style={{ padding: "8px" }}>{formatCelular(y.celular)}</td>
                    <td style={{ padding: "8px", textAlign: "right" }}>
                      B/. {y.monto.toFixed(2)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} style={{ padding: "10px", color: "#888" }}>
                    Sin transacciones para esta fecha
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* leyenda */}
      <div style={{ marginTop: "1rem", color: "#555", fontSize: "0.9rem" }}>
        <p>✅ Verde = Coincide nombre y monto</p>
        <p>🟧 Naranja = Mismo monto, diferente nombre</p>
        <p>⚪ Blanco = Sin coincidencia</p>
      </div>
    </div>
  );
}
