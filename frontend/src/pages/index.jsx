import React, { useState, useEffect, useRef } from "react";
import { FaFileUpload, FaCheckCircle, FaSpinner } from "react-icons/fa";
import ConciliacionYappy from "../components/ConciliacionYappy";
import BancoPreview from "../components/banco_preview";
import { getApiBase } from "../utils/api";
import { fechaATexto } from "../utils/fechas";
import { Card, CardHeader, CardBody, Button, ProgressBar, Table } from "../components/ui";
import { notify } from "../utils/notifications";

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

  // Refs para los inputs de archivo
  const cierreInputRef = useRef(null);
  const yappyInputRef = useRef(null);
  const bancoInputRef = useRef(null);

  // Función para obtener color según concepto
  const getConceptoColor = (concepto) => {
    const colores = {
      "EFECTIVO": "#28a745",
      "YAPPY": "#17a2b8",
      "DEBITO (CLAVE)": "#6b5b95",
      "CREDITO (VISA/MASTER)": "#ffc107",
      "FONDO DE CAJA": "#dc3545",
      "ACH": "#20c997",
      "PEDIDOS YA": "#fd7e14"
    };
    return colores[concepto] || "#6c757d";
  };

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
      
      if (json.error || !json.success) {
        throw new Error(json.error || json.message || json.errors?.[0] || "Error al procesar archivo bancario");
      }
      
      // La respuesta ahora viene en formato {success, data, ...}
      if (json.success && json.data) {
        setDataBanco(json);
        notify.success(`${json.data.total_registros || 0} movimientos bancarios cargados`);
      } else {
        throw new Error(json.message || "Error al procesar archivo bancario");
      }
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
                <input 
                  ref={cierreInputRef}
                  type="file" 
                  accept=".xlsx,.xls,.xlsm,.xlsb,.csv,.ods" 
                  onChange={handleCierreUpload} 
                  style={{ display: "none" }}
                />
                <Button 
                  variant="primary" 
                  fullWidth
                  disabled={cierreLoading}
                  onClick={() => cierreInputRef.current?.click()}
                >
                  {cierreFile ? cierreFile.name : "Seleccionar archivo"}
                </Button>
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
              <input 
                ref={yappyInputRef}
                type="file" 
                accept=".xlsx,.xls,.xlsm,.xlsb,.csv,.ods" 
                onChange={handleYappyUpload} 
                style={{ display: "none" }}
              />
              <Button 
                variant="primary" 
                fullWidth
                disabled={yappyLoading}
                onClick={() => yappyInputRef.current?.click()}
              >
                {yappyFile ? yappyFile.name : "Seleccionar archivo"}
              </Button>
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
              <input 
                ref={bancoInputRef}
                type="file" 
                accept=".xlsx,.xls,.xlsm,.xlsb,.csv,.ods" 
                onChange={handleBancoUpload} 
                style={{ display: "none" }}
              />
              <Button 
                variant="primary" 
                fullWidth
                disabled={bancoLoading}
                onClick={() => bancoInputRef.current?.click()}
              >
                {bancoFile ? bancoFile.name : "Seleccionar archivo"}
              </Button>
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
                    sortable: true,
                    render: (value, row) => (
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <span style={{
                          display: "inline-block",
                          width: "8px",
                          height: "8px",
                          borderRadius: "50%",
                          backgroundColor: getConceptoColor(value),
                          flexShrink: 0
                        }} />
                        <strong style={{ color: "#333" }}>{value}</strong>
                      </div>
                    )
                  },
                  {
                    key: "monto",
                    label: "Monto",
                    sortable: true,
                    align: "right",
                    render: (value) => (
                      <span style={{ fontWeight: 600, color: "#6b5b95" }}>
                        B/. {value?.toFixed(2) || "0.00"}
                      </span>
                    )
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
      {dataBanco && dataBanco.success && dataBanco.data && (
        <BancoPreview data={dataBanco.data} />
      )}
      </div>
    </div>
  );
}
