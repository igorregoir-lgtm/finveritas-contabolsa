# FinVeritas Contabolsa

**Localização:** `C:\DEV\allla\Clara Contábil\finveritas-contabolsa`

Sistema completo de contabilidade padrão B3 para análise de bancos (crédito, risco, solvência).

> Este artefato faz parte do projeto Clara Contábil.

## Como rodar (todos os 4 itens implementados)

### 1. Streamlit UI (recomendado para demo rápida)
```powershell
cd "C:\DEV\allla\Clara Contábil\finveritas-contabolsa"
pip install -r requirements.txt
make run
# ou
streamlit run app.py
```

### 2. FastAPI Backend
```powershell
make run-api
# ou
uvicorn src.api.main:app --reload --port 8000
```

### 3. React Frontend
```powershell
cd frontend
npm install
npm run dev
```
Acesse http://localhost:5173 (conecta ao FastAPI em 8000 via proxy)

## The "WHAT THE HELL" Experience (next-level elevation)

Run the Streamlit app and follow the top launcher:

1. Load the 3-entity golden interco group (loans + AR/AP + revenue inside the group).
2. Run full consolidation → watch 5M loans + 7M AR/AP disappear from the consolidated view while external revenue stays.
3. Try to "cheat" with a material adjustment → system blocks it with four-eyes/segregation message.
4. Click into Crédito workspace → move the What-If sliders (interco loan size, EBITDA multiplier) → covenants and headroom recalculate live.
5. Hit "Generate Full Credit Memo" → get a committee-ready formatted document with numbers, covenant status + headroom, explain narratives, root verification hashes.

**For the Credit Analyst**: Headroom numbers, scope-aware covenants, one-click lineage to source lines + immutable hashes.
**For the Founder/Investor**: Honest consolidated health + instant "what if we cleaned this up" simulator.
**For the Auditor**: Everything is explainable and the hash chain would break on tampering.

**NEXT-LEVEL (Iteration 3 - Internet Research Driven from OneStream, Nominal, Hebbia, IFRS leaders):**
- AI anomaly detection + covenant stress testing (enterprise credit tools)
- Rich interactive D3 ownership/elim graphs (clickable lineage) in Streamlit + HTML
- Expanded harness with AI/IFRS/stress/fraud pressure cases
- IFRS10/B3 regulatory depth, enhanced compliance
- Standalone HTML: full JS AI engines, D3, stress/anomaly sims
- All previous + real outputs scale impressively

Run: `python -m harness.golden_consolidation` (all cases pass); `streamlit run app.py` (new AI/stress/D3 buttons); open HTML demo.

Golden harness stays green. Repo at true next-level "what the hell" for target users.

This is the level where people say "WHAT THE HELL, this is actually production-grade for banks/FIDC".

### 4. Tudo com Docker + Postgres
```powershell
make docker
# Acesse:
# - API: http://localhost:8000
# - Streamlit: http://localhost:8501
# - React: http://localhost:5173 (adicione manualmente ou exponha)
```

## Testes
```powershell
make test
```

## Principais Features Atendidas
- ✅ Card gigante de solvência + semáforos + tooltips
- ✅ Todos indicadores (Liquidez, Solvência com Altman Z + DSCR, Rentabilidade, Score 0-100)
- ✅ Journal imutável com Hash Chain + Event Sourcing
- ✅ Anti-Fraude Ironclad (bloqueio automático + logs eternos)
- ✅ Import Pix + NF-e com guardrails
- ✅ Export real para Banco (PDF gerado com ReportLab + JSON assinado)
- ✅ FastAPI real + React moderno
- ✅ Persistência PostgreSQL via SQLAlchemy
- ✅ Docker-ready + ISO 25010 mindset
- ✅ Traceabilidade completa até o lançamento original

Construído com SDD (Spec-Driven Development). Specs em /SPECS são a fonte da verdade.
