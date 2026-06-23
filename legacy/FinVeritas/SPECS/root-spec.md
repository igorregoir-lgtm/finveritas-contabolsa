# FinVeritas - Spec Completa (real modules)

**Pasta:** C:\DEV\allla\Clara Contábil\FinVeritas (legado inicial)
**Status:** Versão inicial. O artefato completo e avançado está em: C:\DEV\allla\Clara Contábil\finveritas-contabolsa (FinStatement Pro com 3 planos, consolidação de grupos, AI, D3 etc.)

## Módulos
- **Journal** — Partida dobrada, imutável, validação de equilíbrio.
- **RatioEngine** — Cálculo de ratios + SolvencyReport com score 0-100.
- **AntiFraudPolicy** (Guardrails) — Regras ironclad + log imutável de decisões.
- **FiscalIntegrator** — Import Pix + NF-e com validação, assinatura e reconciliação.
- **BankExporter** — Pacote com manifest, SHA-256 e assinatura simulada + verificação.

## Características
- anti_fraud: ironclad (bloqueio + registro eterno)
- ui: card-solvencia-gigante + dashboard Streamlit funcional
- iso25010: full (auditabilidade, segurança, confiabilidade)
- Arquitetura limpa: domain / application / infrastructure
- Todo caminho sensível passa pelo guardrail

## Como rodar (versão legada)
streamlit run FinVeritas/app.py

## Versão atual (recomendada)
cd "C:\DEV\allla\Clara Contábil\finveritas-contabolsa"
streamlit run app.py

## Testes (versão legada)
pytest FinVeritas/tests/
