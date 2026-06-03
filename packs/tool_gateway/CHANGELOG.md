# Tool Gateway Pack Changelog

## v0.1.0 — Initial release (2026-06-03)

### Added
- 3 object types: `capability_provider`, `capability_call`, `capability_result`
- 3 relation types: `calls`, `produces_result`, `sourced_as`
- 3 behaviors:
  - `call_recorder` — creates calls relation on capability_call.created
  - `policy_enforcer` — checks risk_class against auto_approve_risk_classes
  - `result_sourcer` — maps capability_result to Core source object
- `execute_capability` tool with local function registry
- `register_local_capability` for registering Python functions as capabilities
- `ToolGatewaySettings` with configurable risk policy
- Fixture: tool_call_flow (provider → call → result → source)
- Full README with behavior map

### Design decisions
- credential_ref_name stores names only — actual secrets resolved by Secrets Pack
- output_data is truncated to max_output_chars to avoid giant graph objects
- result_sourcer is the cross-pack bridge: Tool Gateway → Core → observations
