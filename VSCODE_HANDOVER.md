# VS Code Handover: RLM Showcase

**Project Goal:** "Killing Showcase" of Recursive Language Models (RLM) on Microsoft Foundry.

## 🧠 Context for AI Assistant (Copilot)

We are building a 3-scenario showcase.
1.  **Compliance Auditor:** (DONE) Checks 50 invoices for policies.
2.  **Legacy Code Archaeologist:** (READY FOR WIRING) Agent traces code using `grep` tools.
3.  **Manual Master:** (TODO) Technical manual helper.

**Current State:**
-   **Backend**: `rlm_engine.py` (Core Logic, includes `run_code_audit` and `tool_execution`), `function_app.py` (API, scenario routing), `status_manager.py`.
-   **Infrastructure**: `host.json`, `local.settings.json` ready. **Deployment Blocked** by UK South Quota.
-   **Scenarios**: Scenario 1 (Invoices) complete. Scenario 2 (Code) **wired**: `POST /api/audit/start` with `{"scenario":"code_audit", "query":"<regex>"}` scans repo via `run_code_audit`.
-   **Copilot Studio agent**: `copilotstudio/RLMshowcase/` with actions (`start_audit`, `get_audit_status`, optional `rlm-root-agent`) and topics (`AuditStart`, `AuditPoll`, `AuditStatus`); connector placeholder `shared_rlmfunctions`.

---

## 🤖 Copilot Studio & Foundry Connectivity (New!)

**Goal**: Create the "Frontend Agent" in Copilot Studio that delegates complex tasks to our "RLM Backend Agent" (Foundry).

### 1. The "Agent-to-Agent" Architecture
We are not just calling an API; we are connecting two agents.
-   **Frontend Agent (Copilot Studio)**: Handles user intent, conversational flow, and display (Adaptive Cards).
-   **Backend Agent (RLM Engine/Foundry)**: Performs the "Deep Reporting" and "Recursive Analysis".

### 2. Connection Strategy: "Custom Engine" / AI Plugin
Instead of a raw HTTP Node, we should expose the RLM Engine as a **Skill** or **AI Plugin**.

**Steps for VS Code User:**
1.  **Deploy Function App**: Must be live (get the URL).
2.  **Create Custom Connector (or AI Plugin)**:
    -   Import the API definition from `function_app.py` (we can generate an OpenAPI spec).
    -   Host URL: `<your-function-app>.azurewebsites.net`.
    -   Auth: API Key (Function Key).
3.  **Copilot Studio Setup**:
    -   Create New Agent: "Compliance Auditor".
    -   Add **Action**: "Start Audit" (maps to `POST /api/audit/start`).
    -   Add **Action**: "Check Status" (maps to `GET /api/audit/status/{job_id}`).
    -   **Orchestration**:
        -   User: "Audit these invoices."
        -   Copilot: Calls "Start Audit", gets `job_id`.
        -   Copilot: Loops "Check Status" every 2s until `status == 'completed'`.
        -   Copilot: Displays result card.

### 3. Direct Foundry Connection (Alternative)
*Note: The user mentioned "Agent to Agent" connectivity.*
If using the **Foundry Agent Service** (preview):
-   You can "Deploy to Copilot Studio" directly from Microsoft Foundry Studio.
-   **WARNING**: This bypasses our `rlm_engine.py` logic (the Python REPL).
-   **Recommendation**: Stick to the **Azure Function Connector** approach to preserve the RLM "Code-as-Environment" capability. The Function *is* the Agent Interface.

---

## 🧩 Foundry Project & Agents
- **Project:** `rlm-showcase-uksouth`
- **Account:** `rlm-showcase-uksouth-resource` (Cognitive Services)
- **Project Endpoint:** `https://rlm-showcase-uksouth-resource.services.ai.azure.com/api/projects/rlm-showcase-uksouth`
- **OpenAI Endpoint:** `https://rlm-showcase-uksouth-resource.openai.azure.com/`
- **Agent listing via SDK/REST:** Currently fails with **API version not supported** (service rewrites to `agents.uksouth.hyena.infra.ai.azure.com`). Agents exist in portal (two agents), CLI/SDK listing pending correct extension.

**Verify agents:** Use Microsoft Foundry portal to confirm agents. When CLI extension is released, run:
```bash
az login
az <foundry-extension> agent list \
    --resource-group rg-rlm-showcase-uksouth \
    --resource-name rlm-showcase-uksouth-resource \
    --project-name rlm-showcase-uksouth
```

---

## 🛠️ Tasks for VS Code Environment

### 1. Fix/Verify Code Structure
**Status:** ✅ Completed
- `execute_code_search` at module level; `RLMEngine.tool_execution` routes `code_search`; `run_code_audit` added.
- `function_app.py`: scenario `code_audit` routes to `run_code_audit` using `settings.WORKSPACE_ROOT`.

### 2. Deploy to Azure
**Action:** Use the Azure extensions in VS Code.
-   **Task:** Deploy `function_app.py` to the `rlm-showcase-uksouth` resource group.
    -   *Prompt:* "Help me deploy this function app to my Azure subscription. Use the existing resource group if possible."
-   **Config:** You must upload the Local Settings or configure App Settings in the portal for:
    -   `FOUNDRY_ENDPOINT`
    -   `FOUNDRY_API_KEY`

### 3. Frontend Integration (Adaptive Cards)
**Action:** Copilot Studio needs a UI.
-   **Status:** ✅ `adaptive_cards/polling_status.json` added (expects `title`, `status`, `progress`, `logs_text`).

**Copilot Studio Actions & Topics**
- Import `copilot/openapi.json` to create a custom connector (set host to Function App, set `x-functions-key`).
- Update `copilotstudio/RLMshowcase/connectionreferences.mcs.yml` (`shared_rlmfunctions` placeholder) and `actions/*` connectionReference values.
- Actions: `start_audit`, `get_audit_status`, optional `rlm-root-agent` (direct Foundry via Azure Agent Service).
- Topics: `AuditStart` (start + initial poll), `AuditPoll` (single poll), `AuditStatus` (manual check).

### 4. Run Tests
**Status:** ⚠️ `tests/test_audit_flow.py` contains a runnable script (no pytest tests). Full suite passes:
- `pytest tests/test_code_archeologist.py`
- `pytest -q` → 1 passed (pydantic v2 warning)

### 5. Copilot Studio Setup (Extension)
- **Assets:**
    - `copilot/openapi.json` (import as Custom Connector / API Action)
    - `copilot/agent_prompt.md` (system prompt)
    - `adaptive_cards/polling_status.json` (UI)
- **Steps:**
    1. Open Copilot Studio extension in VS Code.
    2. Create new **Plugin/Action** from `copilot/openapi.json` (Function Key auth: `x-functions-key`).
    3. Paste system prompt from `copilot/agent_prompt.md` into agent instructions.
    4. Use Adaptive Card for polling updates; bind `progress`, `status`, `logs_text`.
    5. Publish the agent.

### ✅ Local Verification
- `python quick_check_exec.py` → runs `execute_code_search` directly (no model needed).
- `python quick_check.py` → runs `run_code_audit` (engine logs warning if model not configured; still scans repo).
- `pytest -q` → ensures all tests pass.

> Note: Model clients are optional for code audit; engine will proceed without Foundry credentials (logs a warning).

**Copilot Agent Assets**
- `copilotstudio/RLMshowcase/README.md` for quick setup steps.

---

## ⚠️ Key Constraints
-   **Region:** UK South (Strict).
-   **Subscription:** Subscription No.2.
-   **Model:** `gpt-5.1-chat` (Foundry).

## 📄 File Map
-   `rlm_engine.py`: The Brain.
-   `function_app.py`: The API.
-   `config.py`: The Config.
-   `mock_data/`: The Test Logic.
-   `copilotstudio/RLMshowcase/`: Copilot agent (actions/topics/README; connector placeholder `shared_rlmfunctions`).
