import React, { useState, useEffect } from 'react';
import { FaChartLine, FaCheckCircle, FaExclamationTriangle, FaTimesCircle } from 'react-icons/fa';
import { Card, CardHeader, CardBody } from './ui';
import { getApiBase } from '../utils/api';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface StatsData {
  periodo: {
    inicio: string;
    fin: string;
    dias: number;
  };
  resumen: {
    total_conciliaciones: number;
    coincidencias_exactas: number;
    coincidencias_parciales: number;
    sin_coincidencia: number;
    tasa_coincidencia: number;
  };
  por_tipo: {
    yappy: {
      total: number;
      coincidencias: number;
      discrepancias: number;
    };
    banco: {
      total: number;
      coincidencias: number;
      discrepancias: number;
    };
  };
  por_sucursal: Record<string, number>;
  tendencias: {
    fechas: string[];
    conciliaciones: number[];
    coincidencias: number[];
  };
}

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    loadStats();
  }, [days]);

  const loadStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiBase = getApiBase();
      const response = await fetch(`${apiBase}/api/stats?days=${days}`);
      const json = await response.json();
      
      if (json.success && json.data) {
        setStats(json.data);
      } else {
        setError(json.message || 'Error al cargar estadísticas');
      }
    } catch (err: any) {
      setError(err.message || 'Error al cargar estadísticas');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardBody>
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            Cargando estadísticas...
          </div>
        </CardBody>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardBody>
          <div style={{ textAlign: 'center', padding: '2rem', color: '#dc3545' }}>
            {error}
          </div>
        </CardBody>
      </Card>
    );
  }

  if (!stats) {
    return null;
  }

  // Preparar datos para gráficos
  const tendenciasData = stats.tendencias.fechas.map((fecha, idx) => ({
    fecha: new Date(fecha).toLocaleDateString('es-PA', { month: 'short', day: 'numeric' }),
    conciliaciones: stats.tendencias.conciliaciones[idx] || 0,
    coincidencias: stats.tendencias.coincidencias[idx] || 0
  }));

  const sucursalesData = Object.entries(stats.por_sucursal).map(([name, value]) => ({
    name,
    value
  }));

  const tipoData = [
    { name: 'Yappy', coincidencias: stats.por_tipo.yappy.coincidencias, discrepancias: stats.por_tipo.yappy.discrepancias },
    { name: 'Banco', coincidencias: stats.por_tipo.banco.coincidencias, discrepancias: stats.por_tipo.banco.discrepancias }
  ];

  const COLORS = ['#28a745', '#ffc107', '#dc3545', '#17a2b8'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header con selector de días */}
      <Card>
        <CardHeader>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FaChartLine />
              <span>Dashboard de Conciliaciones</span>
            </div>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              style={{
                padding: '0.5rem',
                borderRadius: '6px',
                border: '1px solid #dee2e6',
                fontSize: '0.875rem'
              }}
            >
              <option value={7}>Últimos 7 días</option>
              <option value={30}>Últimos 30 días</option>
              <option value={60}>Últimos 60 días</option>
              <option value={90}>Últimos 90 días</option>
            </select>
          </div>
        </CardHeader>
      </Card>

      {/* Métricas principales */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <Card>
          <CardBody>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: '#6b5b95' }}>
              {stats.resumen.total_conciliaciones}
            </div>
            <div style={{ fontSize: '0.875rem', color: '#6c757d', marginTop: '0.5rem' }}>
              Total Conciliaciones
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <FaCheckCircle style={{ color: '#28a745' }} />
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#28a745' }}>
                {stats.resumen.coincidencias_exactas}
              </div>
            </div>
            <div style={{ fontSize: '0.875rem', color: '#6c757d' }}>
              Coincidencias Exactas
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <FaExclamationTriangle style={{ color: '#ffc107' }} />
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#ffc107' }}>
                {stats.resumen.coincidencias_parciales}
              </div>
            </div>
            <div style={{ fontSize: '0.875rem', color: '#6c757d' }}>
              Coincidencias Parciales
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <FaTimesCircle style={{ color: '#dc3545' }} />
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#dc3545' }}>
                {stats.resumen.sin_coincidencia}
              </div>
            </div>
            <div style={{ fontSize: '0.875rem', color: '#6c757d' }}>
              Sin Coincidencia
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: '#6b5b95' }}>
              {stats.resumen.tasa_coincidencia.toFixed(1)}%
            </div>
            <div style={{ fontSize: '0.875rem', color: '#6c757d', marginTop: '0.5rem' }}>
              Tasa de Coincidencia
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Gráficos */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
        {/* Tendencias */}
        {tendenciasData.length > 0 && (
          <Card>
            <CardHeader>Tendencias</CardHeader>
            <CardBody>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={tendenciasData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="fecha" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="conciliaciones" stroke="#6b5b95" name="Conciliaciones" />
                  <Line type="monotone" dataKey="coincidencias" stroke="#28a745" name="Coincidencias" />
                </LineChart>
              </ResponsiveContainer>
            </CardBody>
          </Card>
        )}

        {/* Por tipo */}
        <Card>
          <CardHeader>Por Tipo</CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={tipoData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="coincidencias" fill="#28a745" name="Coincidencias" />
                <Bar dataKey="discrepancias" fill="#dc3545" name="Discrepancias" />
              </BarChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        {/* Por sucursal */}
        {sucursalesData.length > 0 && (
          <Card>
            <CardHeader>Por Sucursal</CardHeader>
            <CardBody>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={sucursalesData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {sucursalesData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardBody>
          </Card>
        )}
      </div>
    </div>
  );
};

