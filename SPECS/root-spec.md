# FinVeritas Contabolsa — Root Specification (SDD)

## Vision
FinVeritas transforma **qualquer empresa** em um padrão equivalente a companhia aberta listada na B3, para fins de análise de crédito, risco e solvência por bancos e instituições financeiras.

O sistema produz indicadores confiáveis, auditáveis e à prova de manipulação.

## Core Principles (Non-negotiable)
- **Imutabilidade total**: Todo lançamento contábil é imutável. Ajustes geram novos registros com referência ao anterior.
- **Hash Chain + Assinatura**: Cada registro carrega hash do anterior + assinatura (simulada ou real). Qualquer alteração quebra a cadeia e é detectada.
- **Anti-Fraude Ironclad**: Guardrails bloqueiam tentativas de manipulação em tempo real. Logs eternos. Termo de responsabilidade explícito.
- **Traceability**: Todo indicador (ex: Altman Z) pode ser rastreado até o lançamento original.
- **Intuitivo para humanos**: Dashboard com card gigante de solvência, semáforos (verde/amarelo/vermelho), tooltips explicativos em linguagem simples.
- **SDD First**: Specs são a fonte da verdade. Código é gerado/implementado a partir delas.

## Functional Requirements

### 1. Journal (Event Sourcing)
- Double-entry accounting
- Cada lançamento é um evento imutável
- Hash chain: entry.hash = sha256(previous_hash + entry_data)
- Suporte a reversões via novos eventos de ajuste

### 2. Indicadores Completos

**Liquidez**
- Liquidez Corrente = Ativo Circulante / Passivo Circulante
- Liquidez Seca = (Ativo Circulante - Estoques) / Passivo Circulante
- Liquidez Imediata = (Caixa + Equivalentes) / Passivo Circulante

**Solvência**
- Dívida Líquida / EBITDA
- Cobertura de Juros (Interest Coverage)
- DSCR (Debt Service Coverage Ratio)
- Altman Z-Score (versão completa para empresas)
- Grau de Endividamento

**Rentabilidade**
- ROA (Return on Assets)
- ROE (Return on Equity)
- Margem EBITDA
- Margem Líquida

**Outros**
- Fluxo de Caixa Livre / Operacional
- Score de Qualidade de Crédito (0-100) composto

### 3. Fiscal Integration (Pix + NF-e)
- Importação e reconciliação simulada de Pix + Nota Fiscal eletrônica
- Validação de consistência de valores e CNPJs
- Geração automática de lançamentos no Journal

### 4. Guardrails Anti-Fraude
- Bloqueio automático em:
  - Alteração de lançamentos passados
  - Lançamentos com valores anormais sem assinatura
  - Quebra de hash chain
  - Múltiplas entradas de alto valor em curto período
- Registro eterno de todas as tentativas
- Exigência de "termo de responsabilidade" para ações sensíveis

### 5. Export para Banco
- Botão "Exportar para Banco"
- Gera pacote assinado (PDF + JSON) com:
  - Relatório completo de indicadores
  - Hash da cadeia de eventos
  - Assinatura digital (simulada + verificável)
  - Trilhas de auditoria

## Non-Functional (ISO 25010)

- **Functional Suitability**: Cobertura total dos indicadores exigidos por bancos.
- **Performance Efficiency**: Cálculos rápidos mesmo com milhares de lançamentos.
- **Compatibility**: Docker-ready, PostgreSQL.
- **Usability**: UI extremamente clara para analistas não-contadores.
- **Reliability**: Event sourcing + hash chain garante integridade.
- **Security**: Anti-fraude como primeira classe. Imutabilidade.
- **Maintainability**: Clean Architecture + DDD.
- **Portability**: Docker.

**Quality in Use**: Confiança alta do usuário em dados para decisão de crédito.

## Architecture
- Clean Architecture + DDD
- Event Sourcing para Journal
- Domain Events para mudanças críticas
- Interface: Streamlit (MVP) + preparação para FastAPI + React

## Tech Stack (MVP completo)
- Python (domain + application + infrastructure)
- Streamlit para UI principal (rápido + bonito)
- PostgreSQL (via Docker)
- Docker Compose
- Pydantic + dataclasses
- ReportLab ou similar para PDF assinado

## Testing Strategy
- Unit tests
- Property-based (Hypothesis)
- Mutation testing
- Integration tests de fluxos completos (import → journal → ratios → export)

## Acceptance Criteria (para este build)
1. Posso importar Pix + NF-e e ver os lançamentos no Journal.
2. Posso ver o Card Gigante de Solvência com cores (verde/amarelo/vermelho).
3. Todos os indicadores listados acima são calculados corretamente e explicados.
4. Tentar manipular um lançamento passado é bloqueado + registrado no log anti-fraude.
5. Exportar para Banco gera arquivo verificável com hash.
6. Sistema roda com `make run` ou equivalente simples.
7. Testes passam.

---

**Esta é a fonte canônica.** Todo código deve traçar de volta para esta spec.
