import React, { useState } from 'react';

const API = 'http://localhost:8000';
const btn = (bg: string): React.CSSProperties => ({
  padding: '12px 22px', fontSize: '14px', background: bg,
  color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer',
});

interface Ratio { name: string; value: number; status: string; explanation?: string; }
interface SolvencyData { credit_score: number; overall_status: string; ratios: Ratio[]; flags: string[]; }
interface Covenant { covenant_code: string; observed_value: string; threshold: string; status: string; headroom: string; }

export default function FinVeritasDashboard() {
  const [solvency, setSolvency] = useState<SolvencyData | null>(null);
  const [consol, setConsol] = useState<any>(null);
  const [covenants, setCovenants] = useState<Covenant[]>([]);
  const [exportResult, setExportResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');

  const call = async (url: string, method = 'GET', body?: object) => {
    setLoading(true);
    try {
      const res = await fetch(`${API}${url}`, {
        method,
        headers: body ? { 'Content-Type': 'application/json' } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      });
      return await res.json();
    } catch {
      setStatus('❌ API offline — inicie o FastAPI em :8000');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const fetchSolvency = async () => {
    const data = await call('/solvency');
    if (data) { setSolvency(data); setStatus('✅ Solvência atualizada'); }
  };

  const loadGroup = async () => {
    const data = await call('/consolidation/load-group', 'POST');
    if (data) setStatus(`✅ Grupo carregado: ${data.group || data.status}`);
  };

  const runConsolidation = async () => {
    const data = await call('/consolidation/run', 'POST');
    if (data) {
      setConsol(data);
      const covs = await call('/consolidation/covenants');
      if (covs) setCovenants(covs);
      setStatus(`✅ Consolidação: ${data.elims} elims • ${data.matches} matches`);
    }
  };

  const doExport = async () => {
    const data = await call('/export', 'POST');
    if (data) { setExportResult(data); setStatus('✅ Pacote bancário gerado'); }
  };

  const statusColor = solvency?.overall_status === 'GREEN' ? '#22c55e' : solvency?.overall_status === 'YELLOW' ? '#eab308' : '#ef4444';

  return (
    <div style={{ fontFamily: 'system-ui', padding: '24px', maxWidth: '1200px', margin: '0 auto', background: '#f8fafc', minHeight: '100vh' }}>
      <h1 style={{ color: '#1e40af', marginBottom: 4 }}>🏦 FinVeritas Contabolsa</h1>
      <p style={{ color: '#64748b', marginTop: 0 }}>Dashboard de crédito padrão B3 • Anti-Fraude Ironclad • Hash Chain Ativo</p>

      {/* Action bar */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24 }}>
        <button onClick={loadGroup}       disabled={loading} style={btn('#7c3aed')}>① Carregar Grupo</button>
        <button onClick={runConsolidation} disabled={loading} style={btn('#1d4ed8')}>② Consolidar + Covenants</button>
        <button onClick={fetchSolvency}   disabled={loading} style={btn('#0f766e')}>③ Score Solvência</button>
        <button onClick={doExport}        disabled={loading} style={btn('#166534')}>④ Exportar para Banco</button>
      </div>

      {status && <div style={{ marginBottom: 16, padding: '10px 16px', background: '#eff6ff', borderLeft: '4px solid #3b82f6', borderRadius: 6 }}>{loading ? '⏳ ' : ''}{status}</div>}

      {/* Solvency card */}
      {solvency && (
        <div style={{ padding: '36px', borderRadius: 20, background: statusColor, color: solvency.overall_status === 'YELLOW' ? '#1e293b' : 'white', textAlign: 'center', boxShadow: '0 10px 30px rgba(0,0,0,0.15)', marginBottom: 24 }}>
          <div style={{ fontSize: 13, opacity: 0.85 }}>SCORE DE QUALIDADE DE CRÉDITO</div>
          <div style={{ fontSize: 88, fontWeight: 'bold', lineHeight: 1 }}>{solvency.credit_score}</div>
          <div style={{ fontSize: 24, fontWeight: 600 }}>{solvency.overall_status}</div>
          {solvency.flags.map((f: string, i: number) => <div key={i} style={{ marginTop: 8, fontSize: 13, opacity: 0.9 }}>⚠️ {f}</div>)}
        </div>
      )}

      {/* Ratios grid */}
      {solvency && solvency.ratios.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ color: '#1e293b' }}>Indicadores Principais</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
            {solvency.ratios.map((r, i) => (
              <div key={i} style={{ border: '1px solid #e2e8f0', padding: 16, borderRadius: 12, background: 'white' }}>
                <div style={{ fontWeight: 600, fontSize: 13, color: '#64748b' }}>{r.name}</div>
                <div style={{ fontSize: 30, fontWeight: 700, color: r.status === 'good' ? '#16a34a' : r.status === 'warning' ? '#ca8a04' : '#dc2626' }}>{r.value}</div>
                <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>{r.explanation?.slice(0, 70)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Consolidation result */}
      {consol && (
        <div style={{ marginBottom: 24, padding: 20, background: 'white', borderRadius: 12, border: '1px solid #e2e8f0' }}>
          <h3 style={{ margin: '0 0 12px', color: '#1e293b' }}>Consolidação Pós-Eliminações</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
            {[['Eliminações', consol.elims], ['Matches', consol.matches], ['Explains', consol.explains]].map(([label, val]) => (
              <div key={label as string} style={{ textAlign: 'center', padding: 12, background: '#f1f5f9', borderRadius: 8 }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: '#1e40af' }}>{val}</div>
                <div style={{ fontSize: 12, color: '#64748b' }}>{label}</div>
              </div>
            ))}
          </div>
          {consol.consol && (
            <div style={{ marginTop: 12, fontSize: 13, color: '#475569' }}>
              Receita externa: <strong>R$ {Number(consol.consol.total_revenue_external || 0).toLocaleString('pt-BR')}</strong>
              {' · '} Loans eliminados: <strong>R$ {Number(consol.consol.ic_eliminated_loan || 0).toLocaleString('pt-BR')}</strong>
            </div>
          )}
        </div>
      )}

      {/* Covenants */}
      {covenants.length > 0 && (
        <div style={{ marginBottom: 24, padding: 20, background: 'white', borderRadius: 12, border: '1px solid #e2e8f0' }}>
          <h3 style={{ margin: '0 0 12px', color: '#1e293b' }}>Covenants (com Headroom)</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead><tr style={{ background: '#1e40af', color: 'white' }}>{['Covenant','Observado','Threshold','Headroom','Status'].map(h => <th key={h} style={{ padding: '8px 12px', textAlign: 'left' }}>{h}</th>)}</tr></thead>
            <tbody>{covenants.map((c, i) => (
              <tr key={i} style={{ borderBottom: '1px solid #f1f5f9', background: i % 2 ? '#f8fafc' : 'white' }}>
                <td style={{ padding: '8px 12px', fontWeight: 600 }}>{c.covenant_code}</td>
                <td style={{ padding: '8px 12px' }}>{c.observed_value}</td>
                <td style={{ padding: '8px 12px' }}>{c.threshold}</td>
                <td style={{ padding: '8px 12px' }}>{c.headroom}</td>
                <td style={{ padding: '8px 12px' }}><span style={{ color: c.status === 'PASS' ? '#16a34a' : '#dc2626', fontWeight: 700 }}>{c.status}</span></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}

      {/* Export result */}
      {exportResult && (
        <div style={{ padding: 16, background: '#f0fdf4', border: '1px solid #16a34a', borderRadius: 8, marginBottom: 24, fontSize: 13 }}>
          <strong>Pacote bancário gerado</strong> — ID: {exportResult.id}<br />
          Hash: <code>{exportResult.content_hash?.slice(0, 32)}…</code><br />
          Assinatura: <code>{exportResult.signature}</code>
        </div>
      )}

      <div style={{ marginTop: 40, fontSize: 11, color: '#94a3b8' }}>
        FinVeritas Contabolsa • ISO 25010 • Hash Chain + Guardrails • SDD
      </div>
    </div>
  );
}
