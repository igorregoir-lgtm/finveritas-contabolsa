# Micro-Spec: Ironclad Anti-Fraud Guardrails

## Core Invariants
1. **Imutability**: Eventos passados nunca são alterados.
2. **Hash Chain Integrity**: Verificação obrigatória antes de qualquer cálculo ou export.
3. **No Direct Manipulation**: Toda mudança passa por UseCase + Policy.

## Automatic Blocks (Hard)
- Modificação de evento histórico
- Hash chain quebrada
- Lançamento de alto valor (> R$ 100k ou configurável) sem "assinatura digital"
- Tentativa de deletar ou editar entrada

## Soft Blocks / Review
- Velocity: > 3 lançamentos de alto valor em 1 hora
- Inconsistência fiscal (Pix vs NF-e)
- Score de crédito caindo drasticamente sem justificativa

## Logging
- Todo evento de decisão antifraude é registrado eternamente (mesmo que permitido).
- Campos: timestamp, user, action, decision (ALLOW/BLOCK/REVIEW), reason, context_hash

## User Experience
- Quando bloqueado: mensagem clara + "Registrar Termo de Responsabilidade" (simulado).
- Logs visíveis em aba "Auditoria & Fraude".

## Implementation
AntiFraudPolicy (domain) decide.
Qualquer UseCase sensível chama policy.evaluate(...) antes de persistir.
