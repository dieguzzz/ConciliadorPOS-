import React, { useState, useEffect } from "react";
import ConciliacionYappy from "../components/ConciliacionYappy";
import BancoPreview from "../components/banco_preview";
import { getApiBase } from "../utils/api";
import { fechaATexto } from "../utils/fechas";

export default function Home() {
  const [cierreFile, setCierreFile] = useState(null);
  const [yappyFile, setYappyFile] = useState(null);
  const [bancoFile, setBancoFile] = useState(null);

  const [dataCierre, setDataCierre] = useState(null);
  const [dataYappy, setDataYappy] = useState(null);
  const [dataBanco, setDataBanco] = useState(null);

  const [cierreLoading, setCierreLoading] = useState(false);
  const [yappyLoading, setYappyLoading] = useState(false);
  const [bancoLoading, setBancoLoading] = useState(false);

  const [hojaSeleccionada, setHojaSeleccionada] = useState("1");

  // =================== FUNCIÓN PARA RECARGAR CIERRE ===================
  const recargarCierre = async (file) => {
    if (!file) return;
    
    setCierreLoading(true);
    const formData = new FormData();
    formData.append("cierre", file);
    formData.append("hoja_cierre", hojaSeleccionada);

    try {
      const apiBase = getApiBase();
      const res = await fetch(`${apiBase}/api/cierre_preview`, {
        method: "POST",
        body: formData,
      });
      const json = await res.json();
      console.log("📦 Respuesta Cierre del backend (recarga):", json);
      
      if (json.error) {
        throw new Error(json.error);
      }
      
      setDataCierre(json);
    } catch (err) {
      const errorMsg = err.message || "Error desconocido al recargar el archivo de cierre";
      console.error("❌ Error recargando Cierre:", err);
      // No mostrar alert en recarga automática para no interrumpir
      setDataCierre(null);
    } finally {
      setCierreLoading(false);
    }
  };

  // =================== FUNCIÓN PARA RECARGAR YAPPY ===================
  const recargarYappy = async (file, fechaCierre) => {
    if (!file) return;
    
    setYappyLoading(true);
    const formData = new FormData();
    formData.append("yappy", file);
    if (fechaCierre) {
      formData.append("fecha_cierre", fechaCierre);
    }

    try {
      const apiBase = getApiBase();
      const res = await fetch(`${apiBase}/api/yappy_preview`, {
        method: "POST",
        body: formData,
      });
      const json = await res.json();
      console.log("📦 Respuesta Yappy del backend (recarga):", json);
      
      if (json.error) {
        throw new Error(json.error);
      }
      
      setDataYappy(json);
    } catch (err) {
      const errorMsg = err.message || "Error desconocido al recargar el archivo Yappy";
      console.error("❌ Error recargando Yappy:", err);
      setDataYappy(null);
    } finally {
      setYappyLoading(false);
    }
  };

  // =================== FUNCIÓN PARA RECARGAR BANCO ===================
  const recargarBanco = async (file, fechaCierre, sucursalCierre) => {
    if (!file) return;
    
    setBancoLoading(true);
    const formData = new FormData();
    formData.append("file", file);
    if (fechaCierre) {
      formData.append("fecha_cierre", fechaCierre);
    }
    if (sucursalCierre) {
      formData.append("sucursal_cierre", sucursalCierre);
    }

    try {
      const apiBase = getApiBase();
      const res = await fetch(`${apiBase}/api/banco_preview`, {
        method: "POST",
        body: formData,
      });
      const json = await res.json();
      console.log("📦 Respuesta Banco del backend (recarga):", json);
      
      if (json.error) {
        throw new Error(json.error);
      }
      
      setDataBanco(json);
    } catch (err) {
      const errorMsg = err.message || "Error desconocido al recargar el archivo Banco";
      console.error("❌ Error recargando Banco:", err);
      setDataBanco(null);
    } finally {
      setBancoLoading(false);
    }
  };

  // =================== ACTUALIZAR AUTOMÁTICAMENTE AL CAMBIAR HOJA ===================
  useEffect(() => {
    // Si hay un archivo cargado y cambia la hoja, recargar automáticamente
    if (cierreFile && dataCierre && !cierreLoading) {
      console.log("🔄 Hoja cambiada a", hojaSeleccionada, ", recargando cierre...");
      recargarCierre(cierreFile);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hojaSeleccionada]); // Solo cuando cambia hojaSeleccionada

  // =================== RECARGAR YAPPY Y BANCO CUANDO CAMBIA EL CIERRE ===================
  useEffect(() => {
    // Cuando se actualiza el cierre (nueva fecha/sucursal), recargar Yappy y Banco si están cargados
    if (dataCierre?.meta?.fecha) {
      console.log("📅 Fecha del cierre actualizada:", dataCierre.meta.fecha);
      
      // Recargar Yappy si hay archivo cargado
      if (yappyFile && !yappyLoading) {
        console.log("🔄 Recargando Yappy con nueva fecha...");
        recargarYappy(yappyFile, dataCierre.meta.fecha);
      }
      
      // Recargar Banco si hay archivo cargado
      if (bancoFile && !bancoLoading) {
        console.log("🔄 Recargando Banco con nueva fecha/sucursal...");
        recargarBanco(bancoFile, dataCierre.meta.fecha, dataCierre.meta.sucursal);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataCierre?.meta?.fecha, dataCierre?.meta?.sucursal]); // Cuando cambia fecha o sucursal

  // =================== SUBIR CIERRE ===================
  const handleCierreUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setCierreFile(file);
    setCierreLoading(true);

    const formData = new FormData();
    formData.append("cierre", file);
    formData.append("hoja_cierre", hojaSeleccionada);

    try {
      const apiBase = getApiBase();
      const res = await fetch(`${apiBase}/api/cierre_preview`, {
        method: "POST",
        body: formData,
      });
      const json = await res.json();
      console.log("📦 Respuesta Cierre del backend:", json);
      
      if (json.error) {
        throw new Error(json.error);
      }
      
      setDataCierre(json);
    } catch (err) {
      const errorMsg = err.message || "Error desconocido al procesar el archivo de cierre";
      alert(`Error procesando archivo Cierre:\n${errorMsg}`);
      console.error("❌ Error cargando Cierre:", err);
      setDataCierre(null);
    } finally {
      setCierreLoading(false);
    }
  };

  // =================== SUBIR YAPPY ===================
  const handleYappyUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setYappyFile(file);
    setYappyLoading(true);

    const formData = new FormData();
    formData.append("yappy", file);

    // 🔥 ENVIAR FECHA DEL CIERRE
    if (dataCierre?.meta?.fecha) {
      formData.append("fecha_cierre", dataCierre.meta.fecha);
      console.log("📅 Enviando fecha del cierre a Yappy:", dataCierre.meta.fecha);
    }

    try {
      const apiBase = getApiBase();
      const res = await fetch(`${apiBase}/api/yappy_preview`, {
        method: "POST",
        body: formData,
      });
      const json = await res.json();
      console.log("📦 Respuesta Yappy del backend:", json);
      
      if (json.error) {
        throw new Error(json.error);
      }
      
      setDataYappy(json);
    } catch (err) {
      const errorMsg = err.message || "Error desconocido al procesar el archivo Yappy";
      alert(`Error procesando archivo Yappy:\n${errorMsg}`);
      console.error("❌ Error cargando Yappy:", err);
      setDataYappy(null);
    } finally {
      setYappyLoading(false);
    }
  };

  // =================== SUBIR BANCO ===================
  const handleBancoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setBancoFile(file);
    setBancoLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    // 🔥 AÑADIR FECHA Y SUCURSAL DEL CIERRE SI EXISTEN
    if (dataCierre?.meta?.fecha) {
      formData.append("fecha_cierre", dataCierre.meta.fecha);
      console.log("📅 Enviando fecha del cierre al banco:", dataCierre.meta.fecha);
    }
    if (dataCierre?.meta?.sucursal) {
      formData.append("sucursal_cierre", dataCierre.meta.sucursal);
      console.log("🏢 Enviando sucursal del cierre al banco:", dataCierre.meta.sucursal);
    }

    try {
      const apiBase = getApiBase();
      const res = await fetch(`${apiBase}/api/banco_preview`, {
        method: "POST",
        body: formData,
      });
      const json = await res.json();
      console.log("📦 Respuesta Banco del backend:", json);
      
      if (json.error) {
        throw new Error(json.error);
      }
      
      setDataBanco(json);
    } catch (err) {
      const errorMsg = err.message || "Error desconocido al procesar el archivo bancario";
      alert(`Error procesando archivo Banco:\n${errorMsg}`);
      console.error("❌ Error cargando Banco:", err);
      setDataBanco(null);
    } finally {
      setBancoLoading(false);
    }
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "Arial, sans-serif", background: "#f5f5f5", minHeight: "100vh" }}>
      <h1 style={{ textAlign: "center", color: "#6b5b95", marginBottom: "2rem" }}>
        Vista Previa de Cierre POS
      </h1>

      {/* Cards de carga de archivos */}
      <div style={{ 
        display: "grid", 
        gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", 
        gap: "1.5rem", 
        marginBottom: "2rem",
        maxWidth: "1200px",
        margin: "0 auto 2rem"
      }}>
        
        {/* Cierre */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>📁 Archivo Cierre</div>
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <input 
              type="number" 
              value={hojaSeleccionada}
              onChange={(e) => setHojaSeleccionada(e.target.value)}
              placeholder="N° Hoja"
              style={styles.input}
              min="1"
            />
            <label style={styles.fileLabel}>
              {cierreFile ? cierreFile.name : "Seleccionar archivo"}
              <input 
                type="file" 
                accept=".xlsx,.xls,.xlsm,.xlsb,.csv,.ods" 
                onChange={handleCierreUpload} 
                style={{ display: "none" }}
              />
            </label>
          </div>
          {cierreLoading && <div style={styles.loading}>⏳ Procesando...</div>}
          {dataCierre && !cierreLoading && (
            <div style={styles.success}>
              ✅ Cargado: {dataCierre.meta?.sucursal} - {dataCierre.meta?.fecha}
            </div>
          )}
        </div>

        {/* Yappy */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>💸 Archivo Yappy</div>
          <label style={styles.fileLabel}>
            {yappyFile ? yappyFile.name : "Seleccionar archivo"}
            <input 
              type="file" 
              accept=".xlsx,.xls,.xlsm,.xlsb,.csv,.ods" 
              onChange={handleYappyUpload} 
              style={{ display: "none" }}
            />
          </label>
          {yappyLoading && <div style={styles.loading}>⏳ Procesando...</div>}
          {dataYappy && !yappyLoading && (
            <div style={styles.success}>
              ✅ {dataYappy.total_rows || 0} transacciones cargadas
            </div>
          )}
        </div>

        {/* Banco */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>🏦 Archivo Bancario</div>
          <label style={styles.fileLabel}>
            {bancoFile ? bancoFile.name : "Seleccionar archivo"}
            <input 
              type="file" 
              accept=".xlsx,.xls,.xlsm,.xlsb,.csv,.ods" 
              onChange={handleBancoUpload} 
              style={{ display: "none" }}
            />
          </label>
          {bancoLoading && <div style={styles.loading}>⏳ Procesando...</div>}
          {dataBanco && !bancoLoading && (
            <div style={styles.success}>
              ✅ {dataBanco.total_registros || 0} movimientos cargados
            </div>
          )}
        </div>
      </div>

      {/* Vista del Cierre POS */}
      {dataCierre && !dataCierre.error && (
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>📋 Vista Cierre POS</h2>
          <div style={styles.infoBox}>
            <p><strong>Sucursal:</strong> {dataCierre.meta?.sucursal || "—"}</p>
            <p><strong>Fecha:</strong> {fechaATexto(dataCierre.meta?.fecha) || "—"}</p>
            <p><strong>Cajero:</strong> {dataCierre.meta?.cajero || "—"}</p>
          </div>
          
          <table style={styles.table}>
            <thead>
              <tr style={{ background: "#fff6d6" }}>
                <th style={styles.th}>Concepto</th>
                <th style={{ ...styles.th, textAlign: "right" }}>Monto</th>
              </tr>
            </thead>
            <tbody>
              {dataCierre.tabla?.map((row, idx) => (
                <tr key={idx} style={{ borderBottom: "1px solid #e0e0e0" }}>
                  <td style={styles.td}>{row.origen}</td>
                  <td style={{ ...styles.td, textAlign: "right", fontWeight: "600" }}>
                    B/. {row.monto?.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Conciliación Yappy */}
      {dataCierre && dataYappy && (
        <ConciliacionYappy cierre={dataCierre} yappy={dataYappy} />
      )}

      {/* Movimientos Bancarios */}
      {dataBanco && dataBanco.ok && (
        <BancoPreview data={dataBanco} />
      )}
    </div>
  );
}

const styles = {
  card: {
    background: "#fff",
    borderRadius: "12px",
    padding: "1.5rem",
    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
    border: "2px solid #e0e0e0",
  },
  cardHeader: {
    fontSize: "1.1rem",
    fontWeight: "700",
    color: "#6b5b95",
    marginBottom: "1rem",
  },
  input: {
    padding: "8px 12px",
    borderRadius: "8px",
    border: "1px solid #ccc",
    fontSize: "0.95rem",
    width: "80px",
  },
  fileLabel: {
    display: "inline-block",
    padding: "10px 20px",
    background: "#6b5b95",
    color: "#fff",
    borderRadius: "8px",
    cursor: "pointer",
    fontWeight: "600",
    fontSize: "0.9rem",
    transition: "background 0.3s",
    textAlign: "center",
    flex: 1,
  },
  loading: {
    marginTop: "10px",
    color: "#f59e0b",
    fontSize: "0.9rem",
    fontWeight: "600",
  },
  success: {
    marginTop: "10px",
    color: "#10b981",
    fontSize: "0.9rem",
    fontWeight: "600",
  },
  section: {
    background: "#fff",
    borderRadius: "12px",
    padding: "1.5rem",
    marginBottom: "2rem",
    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
  },
  sectionTitle: {
    color: "#6b5b95",
    marginBottom: "1rem",
    fontSize: "1.3rem",
  },
  infoBox: {
    background: "#f8f6ff",
    padding: "12px",
    borderRadius: "8px",
    marginBottom: "1rem",
    fontSize: "0.95rem",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
  },
  th: {
    padding: "10px",
    textAlign: "left",
    fontWeight: "700",
    borderBottom: "2px solid #6b5b95",
  },
  td: {
    padding: "10px",
    fontSize: "0.95rem",
  },
};