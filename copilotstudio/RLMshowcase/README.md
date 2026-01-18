# RLMshowcase Copilot Agent

## Configure Custom Connector
1. In Copilot Studio (VS Code extension or portal), import `copilot/openapi.json` (already set to `https://rlm-engine-uksouth.azurewebsites.net/api`).
2. Create a custom connector (e.g., `rlmfunctions`), and configure **Authentication** header `x-functions-key` with your default function key.
3. Copy the **connection reference logical name**; update:
   - `connectionreferences.mcs.yml` (`copilots_header_54b8d.shared_rlmfunctions` placeholder)
   - `actions/start_audit.mcs.yml` and `actions/get_audit_status.mcs.yml` `connectionReference` value.

## Actions
- `start_audit` → **Stub** (replace with connector action once imported)
- `get_audit_status` → **Stub** (replace with connector action once imported)

## Topics
- `AuditStart` → calls `start_audit`, stores `Topic.job_id`, performs a first poll via `AuditPoll`.
- `AuditPoll` → calls `get_audit_status`, prints status/logs; user can say **audit poll** again to repeat.
- `AuditStatus` → manual status check; echoes status/logs.

## Notes
- Polling loop can be added later; current flow is single status check.
- Ensure Function App has `x-functions-key` configured in connector.
> Actions/topics are stubbed to satisfy linting. After importing connector, update actions to `InvokeConnectorAction` and topics to call them.

### Function Key
- Default key (as of 2026-01-18): `l75VFecjUpmUKsdPUE_4oWI_XbKN2deW-eYveeQta2YTAzFudx869g==`
- Rotate via: `az functionapp keys set/list -g rg-rlm-showcase-uksouth -n rlm-engine-uksouth`
## Direct Foundry Agent (optional)
- `actions/rlm-root-agent.mcs.yml` uses Azure Agent Service connector to talk directly to Foundry root agent (`rlm-root-agent:1`).
