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

## 🚧 Deployment Status
- **Not deployed**. Function App `rlm-engine-uksouth` missing.
- **Blocker:** UK South Shared VMs quota = 0 (ExtendedCode `70007`). Plan creation fails (`Y1`, `B1`, `EP1`).
- **Ready:** Storage account `rlmdocumentsstorage`, `host.json`, `local.settings.json`.
- **Need:** Quota increase or existing App Service plan, then create Function App.

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

## 💬 Prompts for Gemini
- "Summarize role of `execute_code_search` and how to integrate as a tool call in RLM agent loop."
- "Generate Azure Functions Python v4 durable pattern to offload long-running audit jobs."
- "Design Adaptive Card schema for streaming job logs (status_manager logs)."
- "Outline Copilot Studio connector setup using `copilot/openapi.json` and topic wiring (AuditStart/AuditPoll/AuditStatus)."
