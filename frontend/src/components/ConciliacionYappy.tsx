// frontend/src/components/ConciliacionYappy.tsx
import React from "react";

interface Props {
  cierre: any;
  yappy: any;
}

const ConciliacionYappy: React.FC<Props> = ({ cierre, yappy }) => {
  if (!cierre || !yappy) {
    return (
      <div className="text-center text-gray-500 italic">
        Carga ambos archivos para mostrar la conciliación.
      </div>
    );
  }

  const detalleCierre = cierre.detalle_yappy || [];
  const detalleArchivo = (yappy.preview || []).filter(
    (t: any) => t.fecha === cierre.meta?.fecha
  );

  const formatPhone = (num: string) => {
    if (!num) return "";
    const digits = num.replace(/\D/g, "");
    if (digits.startsWith("507")) {
      const last8 = digits.slice(-8);
      return `(+507) ${last8.slice(0, 4)}-${last8.slice(4)}`;
    }
    if (digits.length === 8) {
      return `(+507) ${digits.slice(0, 4)}-${digits.slice(4)}`;
    }
    return num;
  };

  const getMatchColor = (nombre: string, monto: string) => {
    const montoCierre = parseFloat(monto.replace(/[^\d.]/g, ""));
    const match = detalleArchivo.find(
      (t: any) => parseFloat(t.monto) === montoCierre
    );
    if (!match) return "bg-white";
    if (match.cliente.trim().toLowerCase() === nombre.trim().toLowerCase())
      return "bg-green-100";
    return "bg-orange-100";
  };

  return (
    <div className="bg-white shadow-lg rounded-2xl p-6 mt-4">
      <h2 className="text-center text-2xl font-semibold text-purple-700 mb-2">
        💜 Conciliación Yappy
      </h2>
      <p className="text-center text-gray-500 mb-4">
        Fecha: {cierre.meta?.fecha || "No detectada"}
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Cierre POS */}
        <div className="bg-purple-50 rounded-xl shadow p-4">
          <h3 className="text-purple-600 font-semibold mb-2">📋 Cierre POS</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-yellow-50 text-gray-700">
                <th className="text-left px-2 py-1">Cliente</th>
                <th className="text-right px-2 py-1">Monto</th>
              </tr>
            </thead>
            <tbody>
              {detalleCierre.map((item: any, idx: number) => (
                <tr
                  key={idx}
                  className={`${getMatchColor(item.nombre, item.monto)} border-b`}
                >
                  <td className="px-2 py-1">{item.nombre}</td>
                  <td className="text-right px-2 py-1">{item.monto}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Archivo Yappy */}
        <div className="bg-purple-50 rounded-xl shadow p-4">
          <h3 className="text-purple-600 font-semibold mb-2">💜 Archivo Yappy (filtrado)</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-yellow-50 text-gray-700">
                <th className="text-left px-2 py-1">Cliente</th>
                <th className="text-left px-2 py-1">Celular</th>
                <th className="text-right px-2 py-1">Monto</th>
              </tr>
            </thead>
            <tbody>
              {detalleArchivo.length > 0 ? (
                detalleArchivo.map((t: any, i: number) => (
                  <tr key={i} className="border-b bg-white hover:bg-purple-100">
                    <td className="px-2 py-1">{t.cliente}</td>
                    <td className="px-2 py-1">{formatPhone(t.celular)}</td>
                    <td className="text-right px-2 py-1">
                      B/. {t.monto.toFixed(2)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} className="text-center text-gray-400 italic py-4">
                    Sin transacciones para esta fecha
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Leyenda */}
      <div className="flex flex-wrap justify-center gap-4 text-sm mt-6 text-gray-600">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-200 rounded"></div>
          <span>Verde = Coincide nombre y monto</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-orange-200 rounded"></div>
          <span>Naranja = Mismo monto, diferente nombre</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-white border rounded"></div>
          <span>Blanco = Sin coincidencia</span>
        </div>
      </div>
    </div>
  );
};

export default ConciliacionYappy;
