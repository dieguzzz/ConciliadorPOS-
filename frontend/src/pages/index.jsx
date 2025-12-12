import React, { useState, useEffect } from "react";
import { FaFileUpload, FaCheckCircle, FaSpinner } from "react-icons/fa";
import ConciliacionYappy from "../components/ConciliacionYappy";
import BancoPreview from "../components/banco_preview";
import { getApiBase } from "../utils/api";
import { fechaATexto } from "../utils/fechas";
import { Card, CardHeader, CardBody, Button, ProgressBar, Table } from "../components/ui";
import { notify } from "../utils/notifications";
import "../styles/theme.css";

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
      notify.success(`Archivo de cierre cargado correctamente`);
    } catch (err) {
      const errorMsg = err.message || "Error desconocido al procesar el archivo de cierre";
      notify.error(`Error procesando archivo Cierre: ${errorMsg}`);
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
      notify.success(`${json.total_rows || 0} transacciones Yappy cargadas`);
    } catch (err) {
      const errorMsg = err.message || "Error desconocido al procesar el archivo Yappy";
      notify.error(`Error procesando archivo Yappy: ${errorMsg}`);
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
      notify.success(`${json.total_registros || 0} movimientos bancarios cargados`);
    } catch (err) {
      const errorMsg = err.message || "Error desconocido al procesar el archivo bancario";
      notify.error(`Error procesando archivo Banco: ${errorMsg}`);
      console.error("❌ Error cargando Banco:", err);
      setDataBanco(null);
    } finally {
      setBancoLoading(false);
    }
  };

  return (
    <div style={{ 
      padding: "2rem", 
      fontFamily: "system-ui, -apple-system, sans-serif", 
      background: "var(--color-background)", 
      minHeight: "100vh" 
    }}>
      <div className="container">
        <h1 style={{ 
          textAlign: "center", 
          color: "var(--color-primary)", 
          marginBottom: "2rem",
          fontSize: "2rem",
          fontWeight: 700
        }}>
          Vista Previa de Cierre POS
        </h1>

        {/* Cards de carga de archivos */}
        <div className="grid grid-cols-3" style={{ marginBottom: "2rem" }}>
          {/* Cierre */}
          <Card>
            <CardHeader>
              <FaFileUpload style={{ marginRight: "0.5rem", display: "inline" }} />
              Archivo Cierre
            </CardHeader>
            <CardBody>
              <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "1rem" }}>
                <input 
                  type="number" 
                  value={hojaSeleccionada}
                  onChange={(e) => setHojaSeleccionada(e.target.value)}
                  placeholder="N° Hoja"
                  style={{
                    padding: "8px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--color-border)",
                    fontSize: "0.95rem",
                    width: "80px"
                  }}
                  min="1"
                />
                <label style={{ flex: 1 }}>
                  <input 
                    type="file" 
                    accept=".xlsx,.xls,.xlsm,.xlsb,.csv,.ods" 
                    onChange={handleCierreUpload} 
                    style={{ display: "none" }}
                  />
                  <Button 
                    variant="primary" 
                    fullWidth
                    disabled={cierreLoading}
                  >
                    {cierreFile ? cierreFile.name : "Seleccionar archivo"}
                  </Button>
                </label>
              </div>
              {cierreLoading && (
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--color-warning)" }}>
                  <FaSpinner style={{ animation: "spin 1s linear infinite" }} />
                  <span>Procesando...</span>
                </div>
              )}
              {dataCierre && !cierreLoading && (
                <div style={{ 
                  display: "flex", 
                  alignItems: "center", 
                  gap: "0.5rem", 
                  color: "var(--color-success)",
                  fontSize: "0.9rem",
                  marginTop: "0.5rem"
                }}>
                  <FaCheckCircle />
                  <span>{dataCierre.meta?.sucursal} - {dataCierre.meta?.fecha}</span>
                </div>
              )}
            </CardBody>
          </Card>

          {/* Yappy */}
          <Card>
            <CardHeader>
              <FaFileUpload style={{ marginRight: "0.5rem", display: "inline" }} />
              Archivo Yappy
            </CardHeader>
            <CardBody>
              <label style={{ display: "block", marginBottom: "1rem" }}>
                <input 
                  type="file" 
                  accept=".xlsx,.xls,.xlsm,.xlsb,.csv,.ods" 
                  onChange={handleYappyUpload} 
                  style={{ display: "none" }}
                />
                <Button 
                  variant="primary" 
                  fullWidth
                  disabled={yappyLoading}
                >
                  {yappyFile ? yappyFile.name : "Seleccionar archivo"}
                </Button>
              </label>
              {yappyLoading && (
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--color-warning)" }}>
                  <FaSpinner style={{ animation: "spin 1s linear infinite" }} />
                  <span>Procesando...</span>
                </div>
              )}
              {dataYappy && !yappyLoading && (
                <div style={{ 
                  display: "flex", 
                  alignItems: "center", 
                  gap: "0.5rem", 
                  color: "var(--color-success)",
                  fontSize: "0.9rem"
                }}>
                  <FaCheckCircle />
                  <span>{dataYappy.total_rows || 0} transacciones</span>
                </div>
              )}
            </CardBody>
          </Card>

          {/* Banco */}
          <Card>
            <CardHeader>
              <FaFileUpload style={{ marginRight: "0.5rem", display: "inline" }} />
              Archivo Bancario
            </CardHeader>
            <CardBody>
              <label style={{ display: "block", marginBottom: "1rem" }}>
                <input 
                  type="file" 
                  accept=".xlsx,.xls,.xlsm,.xlsb,.csv,.ods" 
                  onChange={handleBancoUpload} 
                  style={{ display: "none" }}
                />
                <Button 
                  variant="primary" 
                  fullWidth
                  disabled={bancoLoading}
                >
                  {bancoFile ? bancoFile.name : "Seleccionar archivo"}
                </Button>
              </label>
              {bancoLoading && (
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--color-warning)" }}>
                  <FaSpinner style={{ animation: "spin 1s linear infinite" }} />
                  <span>Procesando...</span>
                </div>
              )}
              {dataBanco && !bancoLoading && (
                <div style={{ 
                  display: "flex", 
                  alignItems: "center", 
                  gap: "0.5rem", 
                  color: "var(--color-success)",
                  fontSize: "0.9rem"
                }}>
                  <FaCheckCircle />
                  <span>{dataBanco.total_registros || 0} movimientos</span>
                </div>
              )}
            </CardBody>
          </Card>
        </div>

      {/* Vista del Cierre POS */}
      {dataCierre && !dataCierre.error && (
        <Card style={{ marginBottom: "2rem" }}>
          <CardHeader>📋 Vista Cierre POS</CardHeader>
          <CardBody>
            <div style={{
              background: "#f8f6ff",
              padding: "1rem",
              borderRadius: "6px",
              marginBottom: "1rem",
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "1rem"
            }}>
              <div>
                <strong style={{ color: "var(--color-text-muted)", display: "block", marginBottom: "0.25rem" }}>
                  Sucursal:
                </strong>
                <span>{dataCierre.meta?.sucursal || "—"}</span>
              </div>
              <div>
                <strong style={{ color: "var(--color-text-muted)", display: "block", marginBottom: "0.25rem" }}>
                  Fecha:
                </strong>
                <span>{fechaATexto(dataCierre.meta?.fecha) || "—"}</span>
              </div>
              <div>
                <strong style={{ color: "var(--color-text-muted)", display: "block", marginBottom: "0.25rem" }}>
                  Cajero:
                </strong>
                <span>{dataCierre.meta?.cajero || "—"}</span>
              </div>
            </div>
            
            {dataCierre.tabla && dataCierre.tabla.length > 0 ? (
              <Table
                data={dataCierre.tabla}
                columns={[
                  {
                    key: "origen",
                    label: "Concepto",
                    sortable: true
                  },
                  {
                    key: "monto",
                    label: "Monto",
                    sortable: true,
                    align: "right",
                    render: (value) => `B/. ${value?.toFixed(2) || "0.00"}`
                  }
                ]}
                pagination={{ pageSize: 10, showPagination: dataCierre.tabla.length > 10 }}
              />
            ) : (
              <div style={{ padding: "2rem", textAlign: "center", color: "var(--color-text-muted)" }}>
                No hay datos de totales disponibles
              </div>
            )}
          </CardBody>
        </Card>
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