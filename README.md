# FinVeritas Contabolsa

Sistema completo de contabilidade padrão B3 para análise de bancos (crédito, risco, solvência).

## Como rodar (todos os 4 itens implementados)

### 1. Streamlit UI (recomendado para demo rápida)
```powershell
cd C:\DEV\allla\finveritas-contabolsa
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
