import React, { useState } from "react";
import ConciliacionYappy from "../components/ConciliacionYappy";

export default function Home() {
  // =================== ESTADOS GLOBALES ===================
  const [cierre, setCierre] = useState(null);
  const [hoja, setHoja] = useState("");
  const [loading, setLoading] = useState(false);
  const [dataCierre, setDataCierre] = useState(null);
  const [error, setError] = useState(null);

  const [yappyFile, setYappyFile] = useState(null);
  const [yappyData, setYappyData] = useState(null);
  const [yappyLoading, setYappyLoading] = useState(false);

  const [bancoFile, setBancoFile] = useState(null);
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
    console.log("🟢 handleYappyUpload ejecutado");
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
      console.log("🟣 Yappy recibido en frontend:", json);
      setYappyData(json);
    } catch (err) {
      alert("Error procesando archivo Yappy: " + err.message);
    } finally {
      setYappyLoading(false);
    }
  };

  // =================== SUBIR BANCO ===================
  const handleBancoUpload = async (e) => {
    e.preventDefault();
    if (!bancoFile) {
      alert("Por favor selecciona un archivo bancario.");
      return;
    }
    setBancoLoading(true);
    const formData = new FormData();
    formData.append("file", bancoFile);

    try {
      const res = await fetch("http://localhost:8000/api/banco_preview", {
        method: "POST",
        body: formData,
      });
      const json = await res.json();
      console.log("🏦 Banco recibido en frontend:", json);

      if (!res.ok) {
        alert("Error del servidor: " + (json.detail || "Error desconocido"));
        return;
      }

      // Asegurar que preview exista siempre
      if (json && json.preview) {
        setBancoData(json);
      } else {
        alert("El archivo no devolvió datos válidos.");
      }

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
      title: "💸 Conciliación Yappy",
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
    zIndex: 10,
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
          <h3 style={{ ...uploadTitle, color: "#b85ac0" }}>💸 Archivo Yappy</h3>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              if (!yappyFile) {
                alert("Por favor selecciona un archivo Yappy.");
                return;
              }
              setYappyLoading(true);
              const formData = new FormData();
              formData.append("file", yappyFile);
              try {
                const res = await fetch(
                  "http://localhost:8000/api/yappy_preview",
                  {
                    method: "POST",
                    body: formData,
                  }
                );
                const json = await res.json();
                console.log("🟣 Yappy recibido en frontend:", json);
                setYappyData(json);
              } catch (err) {
                alert("Error procesando archivo Yappy: " + err.message);
              } finally {
                setYappyLoading(false);
              }
            }}
            style={{ display: "flex", gap: "0.5rem" }}
          >
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={(e) => setYappyFile(e.target.files?.[0] || null)}
              style={inputStyle}
            />
            <button type="submit" disabled={yappyLoading} style={buttonStyle}>
              {yappyLoading ? "Cargando..." : "Cargar"}
            </button>
          </form>
        </div>

        {/* Bancario */}
        <div style={uploadBox}>
          <h3 style={{ ...uploadTitle, color: "#6b5b95" }}>
            🏦 Archivo Bancario
          </h3>
          <form
            onSubmit={handleBancoUpload}
            style={{ display: "flex", gap: "0.5rem" }}
          >
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={(e) => setBancoFile(e.target.files?.[0] || null)}
              style={inputStyle}
            />
            <button type="submit" disabled={bancoLoading} style={buttonStyle}>
              {bancoLoading ? "Cargando..." : "Cargar"}
            </button>
          </form>
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
        <button onClick={prev} style={{ ...arrowStyle, left: -70 }}>
          ⬅
        </button>
        <button onClick={next} style={{ ...arrowStyle, right: -70 }}>
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
                  <p style={{ fontWeight: "600" }}>
                    {dataCierre.meta?.sucursal || "—"}
                  </p>
                </div>
                <div>
                  <p style={{ color: "#666", fontSize: "0.9rem" }}>Fecha</p>
                  <p style={{ fontWeight: "600" }}>
                    {dataCierre.meta?.fecha || "—"}
                  </p>
                </div>
                <div>
                  <p style={{ color: "#666", fontSize: "0.9rem" }}>Cajero</p>
                  <p style={{ fontWeight: "600" }}>
                    {dataCierre.meta?.cajero || "—"}
                  </p>
                </div>
              </div>

              {/* Tabla Totales */}
              <TablaTotales totales={dataCierre.totales} />
            </div>
          )}

          {slides[index].id === "yappy" && (
            <ConciliacionYappy cierre={dataCierre} yappy={yappyData} />
          )}

          {slides[index].id === "banco" && (
            <>
              {bancoData && bancoData.preview ? (
                <div
                  style={{
                    overflowX: "auto",
                    overflowY: "auto",
                    background: "#f9fafb",
                    borderRadius: "12px",
                    padding: "1.5rem",
                    border: "1px solid #ddd",
                    maxHeight: "75vh", // 👈 antes 450px
                    minHeight: "400px",
                    width: "100%",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
                  }}
                >
                  <table
                    style={{
                      width: "100%",
                      borderCollapse: "collapse",
                      fontSize: "0.9rem",
                    }}
                  >
                    <thead style={{ background: "#e8eaf6" }}>
                      <tr>
                        <th style={{ padding: "8px" }}>Fecha</th>
                        <th style={{ padding: "8px" }}>Descripción</th>
                        <th style={{ padding: "8px" }}>Monto</th>
                        <th style={{ padding: "8px" }}>Tipo</th>
                        <th style={{ padding: "8px" }}>Código</th>
                        <th style={{ padding: "8px" }}>Sucursal</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bancoData.preview.map((item, i) => (
                        <tr
                          key={i}
                          style={{
                            background: i % 2 === 0 ? "#fff" : "#f4f6f8",
                            borderBottom: "1px solid #eee",
                          }}
                        >
                          <td style={{ padding: "8px" }}>
                            {item.fecha || "—"}
                          </td>
                          <td style={{ padding: "8px" }}>
                            {item.descripcion || "—"}
                          </td>
                          <td
                            style={{ padding: "8px", textAlign: "right" }}
                          >
                            {item.monto != null
                              ? item.monto.toLocaleString("es-PA", {
                                  style: "currency",
                                  currency: "PAB",
                                })
                              : "—"}
                          </td>
                          <td
                            style={{
                              padding: "8px",
                              fontWeight: "600",
                              color:
                                item.tipo === "VISA"
                                  ? "#1976d2"
                                  : "#43a047",
                            }}
                          >
                            {item.tipo}
                          </td>
                          <td style={{ padding: "8px" }}>
                            {item.codigo || "—"}
                          </td>
                          <td style={{ padding: "8px" }}>
                            {item.sucursal || "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p
                    style={{
                      color: "#555",
                      fontSize: "0.85rem",
                      marginTop: "0.5rem",
                      textAlign: "right",
                    }}
                  >
                    Mostrando {bancoData.preview.length} registros
                  </p>
                </div>
              ) : (
                <p
                  style={{
                    textAlign: "center",
                    color: "#888",
                    background: "#fafafa",
                    padding: "1rem",
                    borderRadius: "10px",
                  }}
                >
                  Carga un archivo bancario para ver los datos
                </p>
              )}
            </>
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
