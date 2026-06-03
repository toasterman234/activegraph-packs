# Secrets Pack Changelog

## v0.1.0 — Initial release (2026-06-03)

### Added
- 2 object types: `credential_ref`, `secret_usage_event`
- 1 relation type: `credential_used_in`
- 1 behavior: `secret_usage_recorder` — creates audit events on credential registration
- `resolve_credential` tool — reads actual secret from env var at execution time
- `SecretsSettings` with env_prefix, record_usage_events, fail_on_missing
- Fixture: credential_registration (registers ref → SecretUsageEvent created)
- Full README with security design diagram

### Design decisions
- CredentialRef contains name ONLY — never the actual secret value
- v0.1 supports environment variables only; v0.2 will add vault backend
- Usage events record registration (not resolution) — resolution events added in v0.2
