# Micro-Spec: Journal + Event Sourcing + Hash Chain

## Purpose
Registro contábil imutável com rastreabilidade total e proteção contra fraude.

## Model
- `AccountingEvent` (imutável)
  - id
  - previous_hash
  - timestamp
  - event_type (JournalEntryPosted, AdjustmentPosted, etc.)
  - payload (double entry lines)
  - hash (current)
  - signature (optional)

## Rules
1. Novo evento sempre referencia `previous_hash` do último.
2. `current_hash = sha256( previous_hash + canonical_payload )`
3. Qualquer tentativa de modificar um evento antigo quebra a cadeia → bloqueio imediato.
4. Ajustes são novos eventos do tipo `Adjustment`.
5. Nunca delete ou update em eventos passados.

## Implementation Notes
- Domain: `Journal` como agreggate que aplica eventos.
- Infrastructure: pode persistir como lista ordenada de eventos + projeção atual (current balances).
- Anti-fraud deve verificar a cadeia antes de qualquer operação.

## Verification
- Ao carregar o journal, reconstituir a cadeia e validar todos os hashes.
- Expor método `verify_chain()` → bool + detalhes da quebra se houver.
