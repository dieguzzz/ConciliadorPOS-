"use client";

import { useState } from "react";

interface BancoPreviewProps {
  data: any;
}

export default function BancoPreview({ data }: BancoPreviewProps) {
  if (!data) return null;

  const { hoja, fecha_inicio, fecha_fin, total_registros, preview } = data;

  return (
    <div className="bg-zinc-900 text-white rounded-xl p-5 shadow-lg border border-yellow-500 mt-4">
      <h2 className="text-xl font-bold mb-2 text-yellow-400">
        📊 {hoja} ({total_registros} registros)
      </h2>
      <p className="text-sm text-gray-400 mb-4">
        Rango: {fecha_inicio} → {fecha_fin}
      </p>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-zinc-800 text-yellow-300 text-sm">
              <th className="p-2 text-left border-b border-zinc-700">Fecha</th>
              <th className="p-2 text-left border-b border-zinc-700">Descripción</th>
              <th className="p-2 text-left border-b border-zinc-700">Sucursal</th>
              <th className="p-2 text-left border-b border-zinc-700">Tipo</th>
              <th className="p-2 text-left border-b border-zinc-700">Tipo/Sucursal</th>
              <th className="p-2 text-right border-b border-zinc-700">Monto</th>
            </tr>
          </thead>
          <tbody>
            {preview.map((row: any, index: number) => (
              <tr key={index} className="hover:bg-zinc-800 transition-colors">
                <td className="p-2 border-b border-zinc-700">{row.fecha}</td>
                <td className="p-2 border-b border-zinc-700">{row.descripcion}</td>
                <td className="p-2 border-b border-zinc-700">{row.sucursal}</td>
                <td className="p-2 border-b border-zinc-700">{row.tipo}</td>
                <td className="p-2 border-b border-zinc-700">{row.tipo_sucursal}</td>
                <td className="p-2 text-right border-b border-zinc-700">
                  ${row.monto.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
