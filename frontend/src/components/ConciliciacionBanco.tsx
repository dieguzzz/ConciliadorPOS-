"use client";
import React, { useState } from "react";
import axios from "axios";
import { getApiBase } from "../utils/api";

interface Movimiento {
  fecha: string;
  descripcion: string;
  monto: number;
  tipo: string;
  codigo: string;
  sucursal: string;
}

interface ConciliacionBancoProps {
  apiUrl?: string; // Puedes pasarle la URL desde fuera si quieres
}

const ConciliacionBanco: React.FC<ConciliacionBancoProps> = ({ apiUrl }) => {
  const [file, setFile] = useState<File | null>(null);
  const [data, setData] = useState<Movimiento[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Selecciona un archivo Excel (.xlsx)");
      return;
    }
    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setError(null);
    setData([]);

    try {
      const response = await axios.post(
        `${apiUrl || getApiBase()}/api/banco_preview`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setData((response.data as any).preview || []);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Error procesando el archivo.");
    } finally {
      setLoading(false);
    }
  };

  const formatMoney = (value: number) => {
    if (!value && value !== 0) return "";
    return `B/. ${value.toFixed(2)}`;
  };

  return (
    <div className="bg-gray-900 text-white p-8 rounded-xl shadow-lg">
      <h2 className="text-xl font-bold mb-4 text-yellow-400">
        Movimientos Bancarios
      </h2>

      <div className="bg-gray-800 p-4 rounded-lg shadow-md mb-6">
        <input
          type="file"
          accept=".xlsx,.xls,.xlsm,.xlsb,.csv,.ods"
          onChange={handleFileChange}
          className="mb-3 text-sm"
        />
        <button
          onClick={handleUpload}
          disabled={loading}
          className="bg-yellow-500 text-black px-4 py-2 rounded hover:bg-yellow-400 transition"
        >
          {loading ? "Procesando..." : "Subir archivo"}
        </button>
        {error && <p className="text-red-400 mt-3">{error}</p>}
      </div>

      {data.length > 0 && (
        <div className="overflow-x-auto max-h-[70vh] border border-gray-700 rounded-lg">
          <table className="min-w-full bg-gray-800 text-sm">
            <thead>
              <tr className="bg-gray-700 text-yellow-400">
                <th className="p-2 border border-gray-700">Fecha</th>
                <th className="p-2 border border-gray-700">Descripción</th>
                <th className="p-2 border border-gray-700">Monto</th>
                <th className="p-2 border border-gray-700">Tipo</th>
                <th className="p-2 border border-gray-700">Código</th>
                <th className="p-2 border border-gray-700">Sucursal</th>
              </tr>
            </thead>
            <tbody>
              {data.map((item, index) => (
                <tr
                  key={index}
                  className="hover:bg-gray-700 border-b border-gray-700 transition"
                >
                  <td className="p-2">{item.fecha}</td>
                  <td className="p-2">{item.descripcion}</td>
                  <td className="p-2">{formatMoney(item.monto)}</td>
                  <td
                    className={`p-2 ${
                      item.tipo === "VISA"
                        ? "text-blue-400"
                        : "text-green-400"
                    }`}
                  >
                    {item.tipo}
                  </td>
                  <td className="p-2">{item.codigo || "-"}</td>
                  <td className="p-2">{item.sucursal}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-gray-400 text-sm p-3">
            Mostrando {data.length} movimientos
          </p>
        </div>
      )}
    </div>
  );
};

export default ConciliacionBanco;
