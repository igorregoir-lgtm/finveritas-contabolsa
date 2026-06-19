# FinVeritas Contabolsa

**Sistema completo de contabilidade padrão B3 para análise de crédito, risco e solvência por bancos.**

Transforme qualquer empresa em um padrão equivalente a companhia aberta listada na B3, com indicadores confiáveis, auditáveis e à prova de manipulação.

[![CI](https://github.com/igorregoir-lgtm/finveritas-contabolsa/actions/workflows/ci.yml/badge.svg)](https://github.com/igorregoir-lgtm/finveritas-contabolsa/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Visão Geral

FinVeritas Contabolsa entrega:
- **Indicadores completos**: Liquidez (Corrente, Seca, Imediata), Solvência (Dívida Líquida/EBITDA, Cobertura de Juros, **Altman Z-Score**, **DSCR**), Rentabilidade (ROA, ROE, Margem EBITDA), Fluxo de Caixa e Score de Qualidade de Crédito (0-100).
- **Card Gigante de Solvência** com semáforos (verde/amarelo/vermelho), tooltips explicativos e total rastreabilidade até os lançamentos originais.
- **Anti-Fraude Ironclad**: Hash chain imutável, detecção automática de manipulação, bloqueio imediato, logs eternos e termo de responsabilidade.
- **Conformidade ISO 25010** (todas as 8 características + Quality in Use).
- Arquitetura Clean + DDD + Event Sourcing.

## Tecnologias

- **Backend**: Python FastAPI + SQLAlchemy
- **Frontend**: React (Vite) + Streamlit (demo)
- **Banco de Dados**: PostgreSQL
- **Infra**: Docker Compose
- **Testes**: pytest + Hypothesis (property-based)
- **CI/CD**: GitHub Actions

## Como Executar

### Opção 1: Streamlit (mais simples para demo)

```powershell
cd C:\DEV\allla\finveritas-contabolsa
pip install -r requirements.txt
make run
# ou
streamlit run app.py
```

### Opção 2: FastAPI + React

```powershell
# Terminal 1 - Backend
make run-api

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

Acesse:
- FastAPI Docs: http://localhost:8000/docs
- React Dashboard: http://localhost:5173

### Opção 3: Tudo com Docker + PostgreSQL

```powershell
make docker
```

Acesse:
- API: http://localhost:8000/docs
- Streamlit: http://localhost:8501

## Comandos Principais

| Comando          | Descrição                     |
|------------------|-------------------------------|
| `make run`       | Inicia Streamlit UI           |
| `make run-api`   | Inicia FastAPI backend        |
| `make test`      | Executa testes unitários      |
| `make docker`    | Sobe tudo com Docker Compose  |

## Estrutura do Projeto

```
finveritas-contabolsa/
├── SPECS/                  # Spec-Driven Development (fonte da verdade)
├── src/
│   ├── domain/             # Journal (Event Sourcing + Hash Chain), RatioEngine, AntiFraudPolicy
│   ├── application/        # FinVeritasService
│   ├── infrastructure/     # Fiscal, Export (PDF), DB, Repos
│   └── api/                # FastAPI endpoints
├── frontend/               # React Vite app
├── tests/
├── .github/workflows/ci.yml
├── docker-compose.yml
└── app.py                  # Streamlit demo
```

## Principais Features

- ✅ Card gigante de solvência + semáforos + explicações em linguagem simples
- ✅ Todos os indicadores exigidos (incluindo Altman Z e DSCR)
- ✅ Journal imutável com Hash Chain verificável
- ✅ Anti-Fraude Ironclad com bloqueios automáticos
- ✅ Integração Fiscal simulada (Pix + NF-e)
- ✅ Export assinado real (PDF gerado com ReportLab + JSON)
- ✅ FastAPI + React modernos
- ✅ Persistência em PostgreSQL
- ✅ Docker-ready
- ✅ Rastreabilidade completa até o lançamento original

## Testes e Qualidade

```bash
make test
```

Inclui testes unitários e property-based (Hypothesis). CI roda testes + lint + build do frontend em cada push.

## Licença

MIT License - veja [LICENSE](LICENSE)

---

**Construído com Spec-Driven Development (SDD)**. As especificações em `/SPECS` são a fonte canônica do sistema.

Para mais detalhes, acesse a [documentação das SPECS](SPECS/root-spec.md).