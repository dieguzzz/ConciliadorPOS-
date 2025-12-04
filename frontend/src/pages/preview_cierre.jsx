import React, { useState } from "react";
import { getApiBase } from "../utils/api";

export default function PreviewCierre() {
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState("totales");
  const [file, setFile] = useState(null);
  const [hoja, setHoja] = useState("1");
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return alert("Selecciona un archivo de cierre");
    setLoading(true);

    const formData = new FormData();
    formData.append("cierre", file);
    formData.append("hoja_cierre", hoja);

    const apiBase = getApiBase();
    const res = await fetch(`${apiBase}/api/cierre_preview`, {
      method: "POST",
      body: formData,
    });

    const json = await res.json();
    setData(json);
    setLoading(false);
  };

  const tabs = [
    { id: "totales", name: "Totales" },
    { id: "yappy", name: "Detalle Yappy" },
    { id: "ach", name: "Detalle ACH" },
    { id: "pedidosya", name: "Detalle Pedidos Ya" },
  ];

  return (
    <div className="min-h-screen bg-[#f8f9fa] flex flex-col items-center p-6">
      <h1 className="text-3xl font-semibold text-gray-700 mb-4">📊 Vista previa del Cierre</h1>

      {/* Upload */}
      <div className="bg-white shadow-md rounded-2xl p-5 w-full max-w-2xl mb-6">
        <label className="block text-gray-600 font-medium mb-2">Archivo de Cierre</label>
        <input
          type="file"
          accept=".xlsx,.xls,.xlsm,.xlsb,.csv,.ods"
          className="block w-full mb-3"
          onChange={(e) => setFile(e.target.files[0])}
        />

        <label className="block text-gray-600 font-medium mb-2">Número de Hoja</label>
        <input
          type="number"
          min="1"
          className="border border-gray-300 rounded-md px-3 py-1 w-24"
          value={hoja}
          onChange={(e) => setHoja(e.target.value)}
        />

        <button
          onClick={handleUpload}
          disabled={loading}
          className="bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-semibold px-5 py-2 rounded-lg ml-3 transition-all shadow-md"
        >
          {loading ? "Procesando..." : "Cargar"}
        </button>
      </div>

      {/* Data view */}
      {data && !data.error && (
        <div className="w-full max-w-5xl bg-white shadow-lg rounded-2xl p-6">
          {/* Meta */}
          <div className="flex flex-wrap justify-between mb-6">
            <div>
              <p className="text-gray-500 text-sm">Sucursal</p>
              <p className="text-lg font-semibold text-gray-800">{data.meta?.sucursal || "—"}</p>
            </div>
            <div>
              <p className="text-gray-500 text-sm">Fecha</p>
              <p className="text-lg font-semibold text-gray-800">{data.meta?.fecha || "—"}</p>
            </div>
            <div>
              <p className="text-gray-500 text-sm">Cajero</p>
              <p className="text-lg font-semibold text-gray-800">{data.meta?.cajero || "—"}</p>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b mb-4">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                className={`px-4 py-2 font-semibold transition-all ${
                  activeTab === tab.id
                    ? "border-b-4 border-yellow-400 text-yellow-600"
                    : "text-gray-500 hover:text-gray-700"
                }`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.name}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div>
            {activeTab === "totales" && (
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-yellow-100">
                    <th className="p-2 text-left">Concepto</th>
                    <th className="p-2 text-right">Monto</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(data.totales || {}).map(([key, val], idx) => (
                    <tr
                      key={idx}
                      className={idx % 2 === 0 ? "bg-gray-50" : "bg-white"}
                    >
                      <td className="p-2">{key}</td>
                      <td className="p-2 text-right">
                        {val != null ? val.toLocaleString("es-PA", { style: "currency", currency: "PAB" }) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {activeTab === "yappy" && (
              <TableDetalle data={data.detalle_yappy} titulo="Yappy" />
            )}
            {activeTab === "ach" && (
              <TableDetalle data={data.detalle_ach} titulo="ACH" />
            )}
            {activeTab === "pedidosya" && (
              <TableDetalle data={data.detalle_pedidosya} titulo="Pedidos Ya" />
            )}
          </div>
        </div>
      )}

      {data && data.error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-4 w-full max-w-3xl">
          <strong>Error:</strong> {data.error}
        </div>
      )}
    </div>
  );
}

function TableDetalle({ data, titulo }) {
  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-700 mb-3">{titulo}</h2>
      {data && data.length > 0 ? (
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-yellow-100">
              <th className="p-2 text-left">Nombre</th>
              <th className="p-2 text-right">Monto</th>
            </tr>
          </thead>
          <tbody>
            {data.map((r, i) => (
              <tr
                key={i}
                className={i % 2 === 0 ? "bg-gray-50" : "bg-white"}
              >
                <td className="p-2">{r.nombre}</td>
                <td className="p-2 text-right">
                  {r.monto != null
                    ? r.monto.toLocaleString("es-PA", { style: "currency", currency: "PAB" })
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="text-gray-500 italic">Sin registros</p>
      )}
    </div>
  );
}
