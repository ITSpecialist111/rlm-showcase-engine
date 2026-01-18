# RLM Showcase Engine — Gemini Handover
**Date:** 2026-01-18

## 🧠 Context
- **Goal:** Demonstrate Recursive Language Models (RLM) with a Compliance Auditor (50+ invoices, policy checks).
- **Stack:** Python, Functions, Microsoft Foundry (GPT-5.1 agents), Copilot Studio, async orchestration.
- **Key idea:** Treat long context as environment; agents request scans instead of stuffing prompts.

## 🗂️ Key Files
- `rlm_engine.py` — Hierarchical agents + `execute_code_search` helper (regex repo scan).
- `function_app.py` — HTTP triggers: `audit/start`, `audit/status/{job_id}`; async background job.
- `status_manager.py` — In-memory job tracking (logs, progress, result).
- `config.py` — Settings with defaults for local/tests (`FOUNDRY_ENDPOINT=https://example.com`, `FOUNDRY_API_KEY=dummy`).
- `mock_data/` — 50 invoices (Invoice #42 has violation), policy doc.
- `tests/` — `test_code_archeologist.py`.
- `host.json`, `local.settings.json` — Added for Functions runtime.

## 🧪 Tests
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest tests/test_code_archeologist.py -q
python -m pytest -q
```
**Results (2026-01-18):** All green (one pydantic v2 deprecation warning).

## 🔄 Updates (Additions)
- `rlm_engine.py`: `run_code_audit`, `tool_execution` wiring for `code_search`.
- `function_app.py`: `scenario="code_audit"` routes to repo scan using `settings.WORKSPACE_ROOT`.
- `adaptive_cards/polling_status.json`: Copilot Studio UI (expects `title`, `status`, `progress`, `logs_text`).
- `copilotstudio/RLMshowcase/`: Copilot agent clone with actions (`start_audit`, `get_audit_status`, optional `rlm-root-agent`), topics (`AuditStart`, `AuditPoll`, `AuditStatus`), connector placeholder `shared_rlmfunctions`, README with setup steps.

### Copilot Studio Agent Configuration Syntax (VS Code / .mcs)
- `agent.mcs.yml`
  - `kind: GptComponentMetadata`
  - `instructions: |` **use plain text**. Avoid `{}` or `{{}}` (Power Platform expression parser). Use `/audit/status/:job_id` style in examples (not `{job_id}`). Provide examples as plain text, not JSON blocks.
  - Example snippet:
    ```yaml
    kind: GptComponentMetadata
    displayName: RLMshowcase
    instructions: |
      You are **Compliance Auditor & Code Archaeologist**...
      - Poll status via GET /audit/status/:job_id
      - Sample: query "(?i)run_code_audit", scenario "code_audit"
    ```
- `connectionreferences.mcs.yml`
  - Replace placeholder logical name `copilots_header_54b8d.shared_rlmfunctions` with actual custom connector logical name.
- `actions/start_audit.mcs.yml`, `actions/get_audit_status.mcs.yml`
  - Use `InvokeConnectorAction`:
    ```yaml
    action:
      kind: InvokeConnectorAction
      connectionReference: <your_logical_name>
      connectionProperties:
        mode: Fixed
      operationId: start_audit
      parameters:
        query: =Topic.query ?? "Audit invoices"
        scenario: =Topic.scenario ?? "invoice_audit"
    ```
  - For status:
    ```yaml
    action:
      kind: InvokeConnectorAction
      connectionReference: <your_logical_name>
      connectionProperties:
        mode: Fixed
      operationId: get_audit_status
      parameters:
        job_id: =Topic.job_id
    ```
- Topics (`AuditStart`, `AuditPoll`, `AuditStatus`)
  - Call the above actions; store `Topic.job_id` on start; reuse in polls.
  - Optional: bind `adaptive_cards/polling_status.json` to show `title`, `status`, `progress`, `logs_text`.

### Flex Consumption Deployment (Python 3.13)
- Remote build **unsupported**; bundle Linux deps via Docker.
- Build inside Functions container:
  ```powershell
  docker run --rm -v C:\Users\graham\Documents\GitHub\rlm-showcase-engine:/app -w /app \
    mcr.microsoft.com/azure-functions/python:4-python3.13 bash -c "
      apt-get update && apt-get install -y build-essential rustc cargo && \
      /opt/python/3.13.11/bin/pip install maturin==1.3.3 && \
      PIP_NO_BUILD_ISOLATION=1 /opt/python/3.13.11/bin/pip install pydantic-core==2.14.1 --no-binary pydantic-core -v && \
      PIP_NO_BUILD_ISOLATION=1 /opt/python/3.13.11/bin/pip install -r requirements.txt -t .python_packages/lib/site-packages
    "
  ```
- Publish: `func azure functionapp publish rlm-engine-uksouth --python --no-build --no-app-settings`
- App settings: `FOUNDRY_ENDPOINT`, `FOUNDRY_API_KEY`, `WORKSPACE_ROOT=/home/site/wwwroot` (no SCM_DO_BUILD_*).
- Troubleshoot: `/admin/functions` 500 ⇒ deps missing. SCM logstream not available on Flex.

## 🚧 Deployment Status
- **Deployed:** `rlm-engine-uksouth` (Flex Consumption **Python 3.11**) with bundled deps.
- **Storage:** `rgrlmshowcaseuksoutaebe` / `app-package-rlm-engine-uksouth-c0520e5`
- **Functions:** `POST /api/audit/start`, `GET /api/audit/status/{job_id}`
- **Notes:** `/admin/host/status` may 404 during warmup; SCM logstream not exposed on Flex.

## 🧩 Foundry Project
- **Project:** `rlm-showcase-uksouth`
- **Account:** `rlm-showcase-uksouth-resource` (Cognitive Services)
- **Project Endpoint (AI Projects):** `https://rlm-showcase-uksouth-resource.services.ai.azure.com/api/projects/rlm-showcase-uksouth`
- **OpenAI Endpoint (if needed):** `https://rlm-showcase-uksouth-resource.openai.azure.com/`
- **Agent list via SDK/REST:** Currently returns **API version not supported** (service rewrites to `agents.uksouth.hyena.infra.ai.azure.com`). Agents confirmed in portal; CLI/SDK listing blocked pending correct extension/API.

### 👉 Verify Agents
- Use Microsoft Foundry portal to view the two agents in the project.
- When CLI extension is available, run:
```bash
az login
az <foundry-extension> agent list \
  --resource-group rg-rlm-showcase-uksouth \
  --resource-name rlm-showcase-uksouth-resource \
  --project-name rlm-showcase-uksouth
```

## 🧩 Foundry Project
- **Project:** `rlm-showcase-uksouth`
- **Account:** `rlm-showcase-uksouth-resource` (Cognitive Services)
- **Project Endpoint (AI Projects):** `https://rlm-showcase-uksouth-resource.services.ai.azure.com/api/projects/rlm-showcase-uksouth`
- **OpenAI Endpoint (if needed):** `https://rlm-showcase-uksouth-resource.openai.azure.com/`
- **Agent list via SDK:** `azure.ai.projects` returned empty; direct REST calls showed API-version mismatch. Use CLI below.

### 👉 List Agents via CLI (recommended)
```bash
az extension add -n openai
az login
az openai agent list \
  --resource-group rg-rlm-showcase-uksouth \
  --resource-name rlm-showcase-uksouth-resource \
  --project-name rlm-showcase-uksouth
```

### 👉 Flex Consumption Deploy Steps (Python 3.11)
```powershell
docker run --rm -v C:\Users\graham\Documents\GitHub\rlm-showcase-engine:/app -w /app \
  mcr.microsoft.com/azure-functions/python:4-python3.11 \
  bash -c "python -m pip install -r requirements.txt -t .python_packages/lib/site-packages"

func azure functionapp publish rlm-engine-uksouth --python --no-build --no-app-settings
```

**App Settings**
- `FOUNDRY_ENDPOINT=https://rlm-showcase-uksouth-resource.services.ai.azure.com/api/projects/rlm-showcase-uksouth`
- `FOUNDRY_API_KEY=<set>`
- `WORKSPACE_ROOT=/home/site/wwwroot`
> Do **NOT** set `SCM_DO_BUILD_DURING_DEPLOYMENT` on Flex.

### 👉 List agents via local scripts
```bash
python list_agents.py          # AI Projects endpoint using token_ai.txt
python list_agents_openai.py   # OpenAI endpoint using token.txt
```

### After Quota/Plan Exists
```powershell
New-AzFunctionAppPlan -Name plan-rlm-showcase-uksouth -ResourceGroupName rg-rlm-showcase-uksouth -Location uksouth -Sku EP1 -WorkerType Linux
New-AzFunctionApp -Name rlm-engine-uksouth `
  -ResourceGroupName rg-rlm-showcase-uksouth `
  -Location uksouth `
  -StorageAccountName rlmdocumentsstorage `
  -PlanName plan-rlm-showcase-uksouth `
  -Runtime python -RuntimeVersion 3.12 -FunctionsVersion 4
func azure functionapp publish rlm-engine-uksouth --python
```

## 🔜 Next Steps
- Request quota / use existing plan; create Function App; publish.
- Wire `code_search` tool into agent tool loop; add `codeaudit` endpoints.
- Import `copilot/openapi.json`, update connector placeholders, publish Copilot agent, wire Adaptive Card.
- Build & publish Flex app with bundled deps; verify `/api/audit/start` responds 202.

## 💬 Prompts for Gemini
- "Summarize role of `execute_code_search` and how to integrate as a tool call in RLM agent loop."
- "Generate Azure Functions Python v4 durable pattern to offload long-running audit jobs."
- "Design Adaptive Card schema for streaming job logs (status_manager logs)."
- "Outline Copilot Studio connector setup using `copilot/openapi.json` and topic wiring (AuditStart/AuditPoll/AuditStatus)."
 - "Explain Copilot Studio `.mcs` instructions syntax constraints (no `{}` / `{{}}`; use plain text examples; `:job_id` path)."
