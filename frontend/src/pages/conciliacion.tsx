import React, { useState } from "react";
import axios from "axios";
import { getApiBase } from "../utils/api";


export default function ConciliacionPage() {
  const [cierre, setCierre] = useState<File | null>(null);
  const [banco, setBanco] = useState<File | null>(null);
  const [yappy, setYappy] = useState<File | null>(null);
  const [data, setData] = useState<any>(null);
  const [activeTab, setActiveTab] = useState("coincidencias");
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!cierre || !banco || !yappy) return alert("Sube los tres archivos primero");
    const formData = new FormData();
    formData.append("cierre", cierre);
    formData.append("banco", banco);
    formData.append("yappy", yappy);
    setLoading(true);
    try {
      const res = await axios.post(`${getApiBase()}/conciliar_auto`, formData);
      setData(res.data);
    } catch (err) {
      alert("Error al conciliar. Revisa la consola.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const exportarExcel = async () => {
    if (!cierre || !banco || !yappy) return alert("Sube los tres archivos primero");
    const formData = new FormData();
    formData.append("cierre", cierre);
    formData.append("banco", banco);
    formData.append("yappy", yappy);
    const res = await axios.post<Blob>(
    `${getApiBase()}/conciliar_exportar`,
    formData,
    { responseType: "blob" }
    );

    const blob = new Blob([res.data], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "conciliado.xlsx";
    a.click();
  };

  const renderTable = (rows: any[]) => (
    <div className="overflow-x-auto mt-4">
      <table className="min-w-full text-sm border-collapse border border-gray-600">
        <thead className="bg-yellow-500 text-black font-semibold">
          {rows.length > 0 ? (
            <tr>
              {Object.keys(rows[0]).map((col) => (
                <th key={col} className="border border-gray-600 px-3 py-2">{col}</th>
              ))}
            </tr>
          ) : (
            <tr><th className="px-3 py-2">Sin datos</th></tr>
          )}
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="odd:bg-gray-800 even:bg-gray-700">
              {Object.values(r).map((val, j) => (
                <td key={j} className="border border-gray-600 px-3 py-1">{String(val)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <h1 className="text-2xl font-bold text-yellow-400 mb-4">Conciliación Automática</h1>

      <div className="flex flex-wrap gap-4 mb-6">
        <input type="file" onChange={(e) => setCierre(e.target.files?.[0] || null)} />
        <input type="file" onChange={(e) => setBanco(e.target.files?.[0] || null)} />
        <input type="file" onChange={(e) => setYappy(e.target.files?.[0] || null)} />
        <button
          onClick={handleUpload}
          className="bg-yellow-500 text-black px-4 py-2 rounded hover:bg-yellow-400"
        >
          {loading ? "Procesando..." : "Conciliar"}
        </button>
        {data && (
          <button
            onClick={exportarExcel}
            className="bg-green-500 text-black px-4 py-2 rounded hover:bg-green-400"
          >
            Exportar a Excel
          </button>
        )}
      </div>

      {data && (
        <>
          <div className="flex space-x-3 mb-4">
            <button
              className={`px-4 py-2 rounded-t ${activeTab === "coincidencias" ? "bg-yellow-500 text-black" : "bg-gray-700"}`}
              onClick={() => setActiveTab("coincidencias")}
            >
              ✅ Coincidencias
            </button>
            <button
              className={`px-4 py-2 rounded-t ${activeTab === "pendientes_cierre" ? "bg-yellow-500 text-black" : "bg-gray-700"}`}
              onClick={() => setActiveTab("pendientes_cierre")}
            >
              ⚠️ Pendientes en Cierre
            </button>
            <button
              className={`px-4 py-2 rounded-t ${activeTab === "pendientes_banco" ? "bg-yellow-500 text-black" : "bg-gray-700"}`}
              onClick={() => setActiveTab("pendientes_banco")}
            >
              💸 Pendientes en Banco
            </button>
          </div>

          <div className="bg-gray-800 p-4 rounded-b">
            {activeTab === "coincidencias" && renderTable(data.coincidencias)}
            {activeTab === "pendientes_cierre" && renderTable(data.pendientes_cierre)}
            {activeTab === "pendientes_banco" && renderTable(data.pendientes_banco)}
          </div>
        </>
      )}
    </div>
  );
}
