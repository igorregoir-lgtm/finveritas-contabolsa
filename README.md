# FinVeritas Contabolsa

[![CI](https://github.com/igorregoir-lgtm/finveritas-contabolsa/actions/workflows/ci.yml/badge.svg)](https://github.com/igorregoir-lgtm/finveritas-contabolsa/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/typescript-strict-blue)](frontend/)

Sistema completo de contabilidade padrão B3 para análise de bancos (crédito, risco, solvência), com arquitetura em camadas, event sourcing imutável com hash chain, anti-fraude four-eyes, e consolidação intercompany com explicabilidade e covenants escopados.

> Este artefato faz parte do projeto **Clara Contábil**.

## 🚀 Quick start

```powershell
# Windows / PowerShell (sem make instalado)
python -m pip install -r requirements.txt
streamlit run app.py

# Linux / macOS / WSL (com make)
make run
```

## 🛠️ Como rodar os serviços

| Serviço | Comando rápido | URL |
|---|---|---|
| Streamlit UI | `streamlit run app.py` | http://localhost:8501 |
| FastAPI backend | `uvicorn src.api.main:app --reload --port 8000` | http://localhost:8000 |
| React frontend | `cd frontend && npm install && npm run dev` | http://localhost:5173 |
| Docker + Postgres | `docker compose up --build -d` | API 8000, Streamlit 8501 |

## ✅ Tesla-level local gate

Rode o mesmo pipeline que o CI em qualquer sistema operacional:

```powershell
# Com nox (recomendado, cross-platform)
python -m nox

# Com make (Linux / macOS / WSL)
make check
```

A `check` executa: **lint** (`ruff`), **typecheck** (`mypy`), **security** (`bandit`, `pip-audit`), **tests** (`pytest` com 90% de cobertura mínima), **frontend build** (`tsc` + `vite build`) e **docker build** (via CI).

## 📊 Quality metrics atuais

| Métrica | Valor |
|---|---|
| Testes | 31 |
| Cobertura | 92% |
| Lint | ✅ pass |
| Typecheck | ✅ pass |
| Bandit | ✅ 0 issues |
| pip-audit | ✅ 0 vulnerabilities |
| npm audit | ✅ 0 vulnerabilities |

## 🏦 Domínio de aplicação

- **Analista de crédito (banco/FIDC)**: prove alavancagem e covenants depois de eliminar ruído intercompany.
- **Founder/Investor**: simule "e se" em intercompany/EBITDA e veja o impacto nos covenants em tempo real.
- **Auditor**: rastreie cada número até o lançamento original e ao hash imutável que prova que nada foi adulterado.

## 📁 Arquitetura

```
src/
├── domain/          # Regras de negócio puras (journal, ratio engine, consolidação, anti-fraude)
├── application/     # Serviços de aplicação (orquestração)
├── api/             # FastAPI endpoints
└── infrastructure/  # Banco, eventos, exportação assinada, simulador fiscal
```

## 🧪 Testes

```powershell
python -m pytest tests/ -q
python -m pytest tests/ --cov=src --cov-report=term
```

A suíte inclui testes de contrato de API, testes de repositório (in-memory e SQLAlchemy), testes de exportação PDF, testes de hash chain e testes property-based com Hypothesis.

## 🐳 Docker

```powershell
docker compose up --build -d
```

- API: http://localhost:8000
- Streamlit: http://localhost:8501

## 📝 Principais features

- ✅ Solvency card gigante com score 0-100, semáforos e tooltips
- ✅ Indicadores de liquidez, solvência (Altman Z + DSCR), rentabilidade
- ✅ Journal imutável com hash chain e event sourcing
- ✅ Anti-fraude four-eyes com logs eternos
- ✅ Importação Pix + NF-e com guardrails
- ✅ Exportação real para banco (PDF + JSON assinado)
- ✅ FastAPI + React + Vite + TypeScript strict
- ✅ PostgreSQL via SQLAlchemy
- ✅ Docker-ready
- ✅ Rastreabilidade completa até o lançamento original

Construído com **SDD** (Spec-Driven Development). Specs em `/SPECS` são a fonte da verdade.
