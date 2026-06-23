# ADR 0003: Anti-Fraud Four-Eyes Policy

## Status

Accepted

## Context

Financial systems are high-value targets for internal fraud. Single-person
approval of high-value journal entries is a common attack vector. The system
must enforce a policy that sensitive operations require additional scrutiny or
multiple authorizers.

## Decision

We implement a `AntiFraudPolicy` that evaluates every sensitive operation
(`post_entry`, fiscal import) against risk factors: amount, chain validity,
actor velocity, and signature presence. If the policy blocks an action, a
`FraudAttempt` is recorded in the `FraudLog`. The default implementation
blocks high-value entries without a second signature, and logs all attempts
for audit.

## Consequences

- **Positive**: Fraud attempts are explicitly denied and recorded.
- **Positive**: Policy rules are centralized in the domain layer and can be extended without touching infrastructure.
- **Positive**: The four-eyes principle is enforced by default for high-value operations.
- **Negative**: High-value workflows require a second signature, adding operational friction.
- **Negative**: Policy tuning must be validated against real business scenarios to avoid false positives.

## Related

- `src/domain/anti_fraud_policy.py`
- `tests/test_anti_fraud.py`
