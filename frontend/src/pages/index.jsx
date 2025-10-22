import React, { useState } from "react";
import TablaConciliacionYappy from "../components/tabla_conciliacion_yappy.jsx";

export default function Home() {
  const [cierre, setCierre] = useState(null);
  const [hoja, setHoja] = useState("");
  const [loading, setLoading] = useState(false);
  const [dataCierre, setDataCierre] = useState(null);
  const [error, setError] = useState(null);

  const [yappyFile, setYappyFile] = useState(null);
  const [yappyData, setYappyData] = useState(null);
  const [yappyLoading, setYappyLoading] = useState(false);

  const [bancoData, setBancoData] = useState(null);
  const [bancoLoading, setBancoLoading] = useState(false);

  // =================== SUBIR CIERRE ===================
  const handleCierreUpload = async (e) => {
    e.preventDefault();
    if (!cierre) {
      setError("Por favor selecciona un archivo de cierre.");
      return;
    }
    setError(null);
    setLoading(true);
    setDataCierre(null);

    const formData = new FormData();
    formData.append("cierre", cierre);
    if (hoja) formData.append("hoja_cierre", hoja);

    try {
      const res = await fetch("http://localhost:8000/api/cierre_preview", {
        method: "POST",
        body: formData,
      });
      const json = await res.json();
      if (json.error) setError(json.error);
      else setDataCierre(json);
    } catch (err) {
      setError("Error procesando archivo de cierre: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  // =================== SUBIR YAPPY ===================
  const handleYappyUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setYappyFile(file);
    setYappyLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/api/yappy_preview", {
        method: "POST",
        body: formData,
      });
      const json = await res.json();
      setYappyData(json);
    } catch (err) {
      alert("Error procesando archivo Yappy: " + err.message);
    } finally {
      setYappyLoading(false);
    }
  };

  // =================== SUBIR BANCO ===================
  const handleBancoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setBancoLoading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch("http://localhost:8000/api/banco_preview", {
        method: "POST",
        body: formData,
      });
      const json = await res.json();
      setBancoData(json);
    } catch (err) {
      alert("Error procesando archivo bancario: " + err.message);
    } finally {
      setBancoLoading(false);
    }
  };

  // =================== ESTILOS ===================
  const inputStyle = {
    background: "#f7f9fc",
    color: "#333",
    border: "1px solid #d1d5db",
    borderRadius: "8px",
    padding: "6px 10px",
    width: "100%",
    marginTop: "4px",
    cursor: "pointer",
  };

  const uploadBox = {
    background: "#fff",
    borderRadius: "12px",
    boxShadow: "0 3px 8px rgba(0,0,0,0.08)",
    padding: "1rem",
    flex: "1 1 250px",
    minWidth: "250px",
  };

  const uploadTitle = {
    marginBottom: "0.5rem",
    fontWeight: "700",
    fontSize: "1rem",
  };

  const buttonStyle = {
    background: "#6b5b95",
    color: "#fff",
    border: "none",
    padding: "10px 18px",
    borderRadius: "8px",
    fontWeight: "600",
    cursor: "pointer",
  };

  // =================== CARRUSEL ===================
  const [index, setIndex] = useState(0);
  const slides = [
    { id: "cierre", title: "📂 Vista Cierre POS", content: dataCierre },
    {
      id: "yappy",
      title: "💜 Conciliación Yappy",
      content: { cierre: dataCierre, yappy: yappyData },
    },
    { id: "banco", title: "🏦 Movimientos Bancarios", content: bancoData },
  ];

  const next = () => setIndex((prev) => (prev + 1) % slides.length);
  const prev = () =>
    setIndex((prev) => (prev - 1 + slides.length) % slides.length);

  const arrowStyle = {
    position: "absolute",
    top: "50%",
    transform: "translateY(-50%)",
    width: 45,
    height: 45,
    borderRadius: "50%",
    border: "none",
    background: "#6b5b95",
    color: "#fff",
    fontSize: 22,
    cursor: "pointer",
    boxShadow: "0 3px 10px rgba(0,0,0,0.3)",
  };

  // =================== RENDER ===================
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #f7f9fc, #f1f4f8)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "2rem",
        fontFamily: "'Inter', sans-serif",
      }}
    >
      <h1
        style={{
          textAlign: "center",
          color: "#444",
          fontWeight: "700",
          marginBottom: "1.5rem",
          fontSize: "1.8rem",
        }}
      >
        Vista Previa de Cierre POS
      </h1>

      {/* === BLOQUES DE CARGA === */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: "1rem",
          marginBottom: "2rem",
        }}
      >
        {/* Cierre */}
        <div style={uploadBox}>
          <h3 style={{ ...uploadTitle, color: "#6b5b95" }}>📂 Archivo Cierre</h3>
          <form
            onSubmit={handleCierreUpload}
            style={{ display: "flex", gap: "0.5rem" }}
          >
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={(e) => setCierre(e.target.files?.[0] || null)}
              style={inputStyle}
            />
            <input
              type="number"
              placeholder="Hoja"
              value={hoja}
              onChange={(e) => setHoja(e.target.value)}
              style={{ ...inputStyle, width: "80px", textAlign: "center" }}
            />
            <button type="submit" disabled={loading} style={buttonStyle}>
              {loading ? "Cargando..." : "Cargar"}
            </button>
          </form>
        </div>

        {/* Yappy */}
        <div style={uploadBox}>
          <h3 style={{ ...uploadTitle, color: "#b85ac0" }}>💜 Archivo Yappy</h3>
          <input
            type="file"
            accept=".xlsx,.xls"
            onChange={handleYappyUpload}
            style={inputStyle}
          />
          {yappyLoading && (
            <p style={{ color: "#b85ac0", fontWeight: "600" }}>
              Procesando archivo...
            </p>
          )}
        </div>

        {/* Bancario */}
        <div style={uploadBox}>
          <h3 style={{ ...uploadTitle, color: "#6b5b95" }}>
            🏦 Archivo Bancario
          </h3>
          <input
            type="file"
            accept=".xlsx,.xls"
            onChange={handleBancoUpload}
            style={inputStyle}
          />
          {bancoLoading && (
            <p style={{ color: "#6b5b95", fontWeight: "600" }}>
              Procesando archivo...
            </p>
          )}
        </div>
      </div>

      {/* === CARRUSEL DE SECCIONES === */}
      <div
        style={{
          position: "relative",
          width: "100%",
          maxWidth: "1000px",
          background: "#fff",
          borderRadius: "1rem",
          boxShadow: "0 10px 25px rgba(0,0,0,0.1)",
          padding: "2rem",
        }}
      >
        <button onClick={prev} style={{ ...arrowStyle, left: 10 }}>
          ⬅
        </button>
        <button onClick={next} style={{ ...arrowStyle, right: 10 }}>
          ➡
        </button>

        <h2
          style={{
            textAlign: "center",
            color: "#444",
            marginBottom: "1rem",
          }}
        >
          {slides[index].title}
        </h2>

        {/* Contenido dinámico */}
        <div style={{ minHeight: "350px" }}>
        {slides[index].id === "cierre" && dataCierre && (
          <div style={{ marginTop: "1rem" }}>
            {/* Meta info */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-around",
                textAlign: "center",
                background: "#f9fafb",
                borderRadius: "10px",
                padding: "1rem",
                marginBottom: "1rem",
              }}
            >
              <div>
                <p style={{ color: "#666", fontSize: "0.9rem" }}>Sucursal</p>
                <p style={{ fontWeight: "600" }}>{dataCierre.sucursal || "—"}</p>
              </div>
              <div>
                <p style={{ color: "#666", fontSize: "0.9rem" }}>Fecha</p>
                <p style={{ fontWeight: "600" }}>{dataCierre.fecha || "—"}</p>
              </div>
              <div>
                <p style={{ color: "#666", fontSize: "0.9rem" }}>Cajero</p>
                <p style={{ fontWeight: "600" }}>{dataCierre.cajero || "—"}</p>
              </div>
            </div>

            {/* Tabla Totales */}
            <TablaTotales totales={dataCierre.totales} />
          </div>
        )}

          {slides[index].id === "yappy" && (
            <TablaConciliacionYappy
              data={{ cierre: dataCierre, yappy: yappyData }}
            />
          )}

          {slides[index].id === "banco" && (
            <pre
              style={{
                background: "#f8f9fa",
                padding: "1rem",
                borderRadius: "8px",
                overflowX: "auto",
              }}
            >
              {bancoData
                ? JSON.stringify(bancoData.preview, null, 2)
                : "Carga un archivo bancario para ver los datos"}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}

function TablaTotales({ totales }) {
  if (!totales) return null;

  return (
    <table
      style={{
        width: "100%",
        borderCollapse: "collapse",
        borderRadius: "10px",
        overflow: "hidden",
      }}
    >
      <thead>
        <tr style={{ background: "#fef9e7", textAlign: "left" }}>
          <th style={{ padding: "10px" }}>Concepto</th>
          <th style={{ padding: "10px", textAlign: "right" }}>Monto</th>
        </tr>
      </thead>
      <tbody>
        {Object.entries(totales || {}).map(([k, v], i) => (
          <tr
            key={i}
            style={{
              background: i % 2 === 0 ? "#fafafa" : "#fff",
              borderBottom: "1px solid #eee",
            }}
          >
            <td style={{ padding: "8px" }}>{k}</td>
            <td style={{ padding: "8px", textAlign: "right" }}>
              {v != null
                ? v.toLocaleString("es-PA", {
                    style: "currency",
                    currency: "PAB",
                  })
                : "—"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
