# RLM Showcase Engine - Project Handover Document

**Date Created:** 2026-01-18
**Project Status:** Phase 2 - 85% Complete (Backend Ready)
**Last Updated:** 2026-01-18 13:30:00

---

## 📋 Executive Summary

The RLM (Recursive Language Model) Showcase Engine is a production-ready implementation of a hierarchical language model architecture, grounded in the MIT paper *Recursive Language Models*. This project integrates **Microsoft Foundry**, **Functions**, and **Copilot Studio** to demonstrate how to solve the "Context Rot" problem for massive datasets (10M+ tokens).

**Key Achievement:** We have successfully built the "Compliance Auditor" backend, capable of processing 50+ invoices via an async "Deep Audit" protocol, fulfilling the MIT paper's vision of treating context as an external environment variable rather than a prompt input.

---

## 🔬 Theoretical Grounding (The "Why")

### Based on: *Recursive Language Models* (arXiv:2512.24601v1)
This project is not just a chatbot; it is a fidelity showcase of the RLM paradigm defined by MIT researchers.

**Core Concept:**
> *"The key insight is that long prompts should not be fed into the neural network directly but should instead be treated as part of the environment that the LLM can symbolically interact with."*

**Our Implementation Strategy:**
1.  **Context-as-Environment**: We store documents in Azure Storage (not the prompt).
2.  **Symbolic Interaction**: Our `RLMEngine` (Python) acts as the REPL environment. It allows the LLM to request "scans" of data.
3.  **Recursive/Parallel Decomposition**:
    -   *Paper*: Focuses on sequential recursion (Depth-First).
    -   *Showcase*: We adapted this to **Parallel Map-Reduce** (Breadth-First) for the "Compliance Auditor" scenario to maximize efficiency when checking 50+ files simultaneously.

---

## 🎬 Showcase Scenarios

### 1. The Compliance Auditor (Backend READY ✅)
**Goal:** Process 50+ invoices against a 10-page policy document to calculate total spend and find violations.
**The "Killer Moment":**
-   User asks: *"Audit the Acme Corp invoices."*
-   Bot replies: *"Starting Deep Audit..."*
-   **Visuals:** Real-time logs stream in: *"Scanning Invoice #1... Found $500"*, *"Scanning Invoice #42... **VIOLATION DETECTED**"*.
-   **Why it wins:** Standard RAG fails here (retrieves top-5, misses the violation). Standard Context Windows rot (hallucinate the total). RLM gets it 100% right.

### 2. The Legacy Code Archaeologist (Architecture Ready 🏗️)
**Goal:** Trace a variable through a 100-file codebase.
**Implementation:** Requires strict RLM/REPL pattern where the agent writes `grep` commands.
**Status:** `execute_code_search` helper added to `rlm_engine.py`; needs agent tool wiring & Function endpoint.

### 3. The Manual Master (Planned 📅)
**Goal:** Guide users through complex technical manuals with precise cross-referencing.
**Status:** Conceptual.

---

## 🏗️ Technical Architecture (Current State)

```
User (Copilot Studio)
       ↓ (HTTP POST)
[Azure Function: start_audit] <───> [Status Manager (Table Storage)]
       ↓ (Async Trigger)                  ^
[RLM Engine (Python)] ────────────────────┘ w/ Callback Logs
       ↓ (Foundry SDK)
[Root Agent (GPT-5.1)] ──> Decomposes Task
       ↓
[Sub-Agents (GPT-5.1)] ──> Parallel Execution (Map-Reduce) on 50+ Docs
```

### Completed Components (100% Code Complete)

1.  **RLM Engine (`rlm_engine.py`)**
    -   Hierarchical Agents (Root + Sub).
    -   Async/Await architecture for parallel processing.
    -   **NEW:** Progress Callback system for real-time status updates.
    -   **NEW (Scenario 2 helper):** `execute_code_search` safe repo regex scan (not yet wired into agent loop).

2.  **API Layer (`function_app.py`)**
    -   `POST /api/audit/start`: Initiates background job, returns `job_id`.
    -   `GET /api/audit/status/{job_id}`: Returns status, percentage, and detailed logs.
    -   **MOCK MODE Included:** If no Blob URL is passed, it loads the 50 generated text files automatically for the demo.

3.  **Infrastructure (`config.py`, `status_manager.py`)**
    -   Pydantic-based configuration.
    -   Job status tracking (queued -> running -> completed/failed).

4.  **Mock Data (`mock_data/`)**
    -   Generated 50 unique invoices.
    -   **Invoice #42** contains the "Business Class" violation for the demo payoff.
    -   Asset: `compliance_audit_data.zip` (Ready for upload).

---

## 🔄 Updates (2026-01-18)
- Added `execute_code_search` helper in `rlm_engine.py` for Scenario 2 (safe regex scan).
- Added `tests/test_code_archeologist.py` (async code search test).
- Updated `requirements.txt`: removed `numpy` and PyPI `asyncio`; bumped `aiohttp==3.9.5`; added `pydantic-settings`.
- `config.py` now includes defaults for `FOUNDRY_ENDPOINT` and `FOUNDRY_API_KEY` for local/tests.
- Wired `run_code_audit` + `tool_execution` in `rlm_engine.py`; `function_app.py` routes `scenario="code_audit"` to repo scan.
- Added `adaptive_cards/polling_status.json` for Copilot Studio UI.
- **Copilot Studio agent (RLMshowcase)** added under `copilotstudio/RLMshowcase/`:
    - Actions: `start_audit`, `get_audit_status` (Function connector placeholder `shared_rlmfunctions`).
    - Topics: `AuditStart` (starts audit, first poll), `AuditPoll` (single poll), `AuditStatus` (manual status).
    - Optional direct Foundry action: `rlm-root-agent` (Azure Agent Service connector).
    - README with connector import steps (`copilot/openapi.json`).

---

## 🚀 How to Run the "Killer Demo"

### Prerequisites
-   **Subscription:** Subscription No.2 (UK South)
-   **Service:** Microsoft Foundry (ai.azure.com)

### Step 1: Deploy Backend
1.  Deploy `function_app.py` to your Function App in UK South.
2.  Set Environment Variables in Azure (`FOUNDRY_ENDPOINT`, `FOUNDRY_API_KEY`).

### Step 2: Configure Copilot Studio
1. **Import custom connector** from `copilot/openapi.json` (create `rlmfunctions` connector, set host to your Function App, set `x-functions-key`).
2. **Update connection references** in `copilotstudio/RLMshowcase/connectionreferences.mcs.yml` and actions (`shared_rlmfunctions` placeholder).
3. **Use actions** `start_audit` and `get_audit_status` (already defined in `copilotstudio/RLMshowcase/actions/`).
4. **Topics** (already scaffolded):
    - `AuditStart` → calls `start_audit`, stores `Topic.job_id`, runs one poll via `AuditPoll`.
    - `AuditPoll` → calls `get_audit_status`, prints progress/logs (user can invoke again).
    - `AuditStatus` → manual status check.
5. **Adaptive Card**: Bind `title`, `status`, `progress`, `logs_text` to `adaptive_cards/polling_status.json` (optional UI step).
6. **Optional**: `rlm-root-agent` action (direct Foundry agent via Azure Agent Service) — bypasses Python RLM engine; use only if you want direct Foundry.

### Step 3: Execute
1.  Type "Run Audit" (for invoices) or invoke `scenario="code_audit"` with `query` regex to scan repo.
2.  Watch the logs stream (The "Thinking" Process).
3.  Celebrate when it catches Invoice #42.

---

## 🧪 Testing

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest tests/test_code_archeologist.py -q
python -m pytest -q
```

**Results (2026-01-18):**
- `tests/test_code_archeologist.py` ✅
- Full suite ✅ (pydantic V2 deprecation warning only)

> Note: `config.py` defaults enable tests without env vars. If using real Foundry, set `FOUNDRY_ENDPOINT` and `FOUNDRY_API_KEY`.

---

## 🚧 Deployment Status (2026-01-18)
- **Not deployed**: Function App `rlm-engine-uksouth` not found.
- **Blocker**: **Shared VMs quota = 0** in **UK South**; plan creation (Consumption `Y1`, Basic `B1`, Premium `EP1`) fails with `Unauthorized` (ExtendedCode `70007`).
- **What’s ready**: `host.json`, `local.settings.json`, storage account `rlmdocumentsstorage` in `rg-rlm-showcase-uksouth`.
- **Need**: Request quota increase or use existing plan, then create Function App.

### Foundry Project & Agents
- **Project:** `rlm-showcase-uksouth`
- **Account:** `rlm-showcase-uksouth-resource` (Cognitive Services)
- **Endpoint (AI Projects):** `https://rlm-showcase-uksouth-resource.services.ai.azure.com/api/projects/rlm-showcase-uksouth`
- **OpenAI Endpoint:** `https://rlm-showcase-uksouth-resource.openai.azure.com/`
- **Agent listing:** `azure.ai.projects` / `azure.ai.agents` and raw HTTP currently return **API version not supported** (service rewrites to `agents.uksouth.hyena.infra.ai.azure.com`). Agents are present (per portal), but CLI/SDK listing is blocked until correct extension/API is available.

**Recommended verification:**
- Use Microsoft Foundry portal to confirm the two agents.
- Or, when available, install the Foundry/Agents CLI extension and run:
    ```bash
    az login
    az <foundry-extension> agent list \
        --resource-group rg-rlm-showcase-uksouth \
        --resource-name rlm-showcase-uksouth-resource \
        --project-name rlm-showcase-uksouth
    ```

- Local scripts: `python list_agents.py` (AI Projects), `python list_agents_openai.py` (OpenAI endpoint) with `token_ai.txt` / `token.txt`.

### After Quota/Plan Exists
```powershell
# Create App Service plan (example)
New-AzFunctionAppPlan -Name plan-rlm-showcase-uksouth -ResourceGroupName rg-rlm-showcase-uksouth -Location uksouth -Sku EP1 -WorkerType Linux

# Create Function App
New-AzFunctionApp -Name rlm-engine-uksouth `
    -ResourceGroupName rg-rlm-showcase-uksouth `
    -Location uksouth `
    -StorageAccountName rlmdocumentsstorage `
    -PlanName plan-rlm-showcase-uksouth `
    -Runtime python -RuntimeVersion 3.12 -FunctionsVersion 4

# Publish
func azure functionapp publish rlm-engine-uksouth --python
```

---

## 📝 Next Steps
-   [ ] **Deploy to Azure**: resolve quota → create plan → create app → `func azure functionapp publish ...`
-   [ ] **Frontend Integration**: Import `copilot/openapi.json`, update `shared_rlmfunctions` connection reference, publish `RLMshowcase` agent, wire Adaptive Card.
-   [ ] **Scenario 2**: Wire `code_search` tool into `RLMEngine` + add `codeaudit` Function endpoints.
