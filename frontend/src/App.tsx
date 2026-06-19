import React, { useState } from 'react';

interface Ratio {
  name: string;
  value: number;
  status: string;
}

interface SolvencyData {
  credit_score: number;
  status: string;
  ratios: Ratio[];
  flags: string[];
}

export default function FinVeritasDashboard() {
  const [solvency, setSolvency] = useState<SolvencyData | null>(null);
  const [exportResult, setExportResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchSolvency = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/solvency');
      const data = await res.json();
      setSolvency(data);
    } catch (e) {
      alert("API not running? Start FastAPI on port 8000");
    }
    setLoading(false);
  };

  const doExport = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/export', { method: 'POST' });
      const data = await res.json();
      setExportResult(data);
      alert(`Export successful! Check ${data.pdf_path || 'server logs'}`);
    } catch (e) {
      alert("Export failed. Make sure backend is running.");
    }
    setLoading(false);
  };

  const statusColor = solvency?.status === 'GREEN' ? '#22c55e' : solvency?.status === 'YELLOW' ? '#eab308' : '#ef4444';

  return (
    <div style={{ fontFamily: 'system-ui', padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ color: '#1e40af' }}>🏦 FinVeritas Contabolsa</h1>
      <p>Dashboard para análise de crédito padrão B3</p>

      <button onClick={fetchSolvency} disabled={loading} style={{ padding: '12px 24px', fontSize: '16px', background: '#1e40af', color: 'white', border: 'none', borderRadius: '8px' }}>
        {loading ? 'Carregando...' : 'Atualizar Score de Solvência'}
      </button>

      {solvency && (
        <div style={{
          marginTop: '30px',
          padding: '40px',
          borderRadius: '20px',
          background: statusColor,
          color: solvency.status === 'YELLOW' ? 'black' : 'white',
          textAlign: 'center',
          boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
        }}>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>SCORE DE QUALIDADE DE CRÉDITO</div>
          <div style={{ fontSize: '96px', fontWeight: 'bold', lineHeight: 1 }}>{solvency.credit_score}</div>
          <div style={{ fontSize: '28px', fontWeight: '600' }}>{solvency.status}</div>
        </div>
      )}

      {solvency && solvency.ratios.length > 0 && (
        <div style={{ marginTop: '30px' }}>
          <h3>Indicadores Detalhados</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
            {solvency.ratios.map((r, i) => (
              <div key={i} style={{ border: '1px solid #ddd', padding: '16px', borderRadius: '12px', background: 'white' }}>
                <div style={{ fontWeight: 600 }}>{r.name}</div>
                <div style={{ fontSize: '32px', fontWeight: 700, color: r.status === 'good' ? '#16a34a' : r.status === 'warning' ? '#ca8a04' : '#dc2626' }}>
                  {r.value}
                </div>
                <div style={{ fontSize: '13px', color: '#666' }}>{r.status.toUpperCase()}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ marginTop: '40px', display: 'flex', gap: '16px' }}>
        <button onClick={doExport} disabled={loading} style={{ padding: '14px 28px', background: '#166534', color: 'white', border: 'none', borderRadius: '8px', fontSize: '15px' }}>
          📤 Exportar para Banco (PDF + Assinatura)
        </button>
      </div>

      {exportResult && (
        <div style={{ marginTop: '20px', padding: '16px', background: '#f0fdf4', border: '1px solid #16a34a', borderRadius: '8px' }}>
          <strong>Export gerado:</strong> {exportResult.id}<br />
          Hash: {exportResult.content_hash?.slice(0, 24)}...<br />
          Assinatura: {exportResult.signature}
        </div>
      )}

      <div style={{ marginTop: '60px', fontSize: '12px', color: '#888' }}>
        Conectado ao FastAPI em :8000 • Anti-Fraude Ironclad • Hash Chain Ativo • ISO 25010
      </div>
    </div>
  );
}
