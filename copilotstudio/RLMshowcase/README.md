# RLMshowcase Copilot Agent

## Configure Custom Connector
1. In Copilot Studio (VS Code extension or portal), import `copilot/openapi.json`.
2. Create a custom connector (e.g., `rlmfunctions`), set host to your Function App URL.
3. Copy the **connection reference logical name**; update:
   - `connectionreferences.mcs.yml` (`copilots_header_54b8d.shared_rlmfunctions` placeholder)
   - `actions/start_audit.mcs.yml` and `actions/get_audit_status.mcs.yml` `connectionReference` value.

## Actions
- `start_audit` → POST /api/audit/start
- `get_audit_status` → GET /api/audit/status/{job_id}

## Topics
- `AuditStart` → calls `start_audit`, stores `Topic.job_id`, performs a first poll via `AuditPoll`.
- `AuditPoll` → calls `get_audit_status`, prints status/logs; user can say **audit poll** again to repeat.
- `AuditStatus` → manual status check; echoes status/logs.

## Notes
- Polling loop can be added later; current flow is single status check.
- Ensure Function App has `x-functions-key` configured in connector.
## Direct Foundry Agent (optional)
- `actions/rlm-root-agent.mcs.yml` uses Azure Agent Service connector to talk directly to Foundry root agent (`rlm-root-agent:1`).
