# Micro-Spec: Full Ratio Engine + Credit Quality Score

## Liquidity
- Liquidez Corrente = AC / PC
- Liquidez Seca = (AC - Estoques) / PC
- Liquidez Imediata = (Caixa + Aplicações) / PC

## Solvency
- Dívida Líquida / EBITDA = (Dívida - Caixa) / EBITDA
- Cobertura de Juros = EBIT / Juros
- DSCR = (EBITDA - CAPEX - Impostos) / (Juros + Amortizações)
- Altman Z-Score (private company version):
  Z = 0.717*(WC/TA) + 0.847*(RE/TA) + 3.107*(EBIT/TA) + 0.420*(Equity/Debt) + 0.998*(Sales/TA)
  Zones: >2.9 safe, 1.23-2.9 grey, <1.23 distress

## Profitability
- ROA, ROE, Margem EBITDA, Margem Líquida

## Credit Quality Score (0-100)
Composição sugerida (ajustável):
- 30% Solvency ratios (inverted scales)
- 25% Liquidity
- 20% Profitability & Cash Flow
- 15% Altman Z + DSCR
- 10% Qualitative / guardrail history (penalidade por tentativas de fraude)

Semáforos:
- >= 80: Verde "Investment Grade"
- 60-79: Amarelo "Monitor"
- < 60: Vermelho "High Risk"

Cada indicador deve ter:
- Valor
- Benchmark (comparação)
- Explicação em linguagem simples
- Link/trilha até os lançamentos que o compõem
