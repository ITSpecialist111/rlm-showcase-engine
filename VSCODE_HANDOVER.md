# VS Code Handover: RLM Showcase

**Project Goal:** "Killing Showcase" of Recursive Language Models (RLM) on Microsoft Foundry.

## 🧠 Context for AI Assistant (Copilot)

We are building a 3-scenario showcase.
1.  **Compliance Auditor:** (DONE) Checks 50 invoices for policies.
2.  **Legacy Code Archaeologist:** (READY) Agent scans repo using `grep` (Scenario 2).
3.  **Manual Master:** (TODO) Technical manual helper.

**Current State:**
-   **Backend**: `rlm_engine.py` (Core Logic), `function_app.py` (API).
-   **Infrastructure**: **DEPLOYMENT UNBLOCKED**. Resource `rlm-engine-uksouth` (Flex Consumption / FC1) created in UK South.
-   **Next Action**: Needs code publish & configuration.

---

## 🛠️ Tasks for VS Code Environment (Immediate Validation)

### 1. Fix Copilot Connector (BLOCKING)
**The Error:** `ConnectorNotSupported` and `IdentifierNotRecognized`.
**The Cause:** The file `connectionreferences.mcs.yml` points to a generic path `/providers/Microsoft.PowerApps/apis/shared_rlmfunctions`.
**The Solution:** Your environment assigns a unique **GUID** to custom connectors.
1.  **Find your Connector ID**:
    -   Open the Power Platform / Copilot Studio panel in VS Code.
    -   Or go to the Portal -> Custom Connectors -> Click "rlmfunctions" -> Look at the URL. It will look like `/apis/shared_rlmfunctions_5f3a...`.
2.  **Update File**:
    -   Edit `copilotstudio/RLMshowcase/connectionreferences.mcs.yml`.
    -   Replace `/providers/Microsoft.PowerApps/apis/shared_rlmfunctions` with your **actual Connector ID**.
3.  **Result**: This will fix the "Connector" error, which will automatically fix the "IdentifierNotRecognized" errors (because `Topic.Status` comes from the connector).

### 1b. Expose OpenAPI Spec & Import Connector (RECOMMENDED)
1. **Spec URL:** `https://rlm-engine-uksouth.azurewebsites.net/api/openapi.json` (served by `function_app.py`).
2. **Want local?** Run `func host start` and use `http://localhost:7071/api/openapi.json`.
3. **Power Platform:** Custom connectors → **+ New custom connector** → **Import an OpenAPI from URL** → name: `RLM Functions` → paste URL → **Create**.
4. **Auth:** Choose **API key**; set `x-functions-key` to your Function App key.
5. **Actions available:** `start_audit` (POST /audit/start), `get_audit_status` (GET /audit/status/{job_id}).

### 2. Publish Code (SIMPLIFIED STRATEGY)
**Issue:** Doing manual Docker builds for Python 3.13 on Flex Consumption is too complex for this demo.
**Recommended Fix:**
1.  **Recreate Function App** as **Python 3.11** (Flex Consumption).
2.  **Publish Command**:
    ```powershell
    func azure functionapp publish rlm-engine-uksouth --python
    ```
    *(This works natively with remote build. No Docker needed.)*

3.  **App Settings**:
    -   `FOUNDRY_ENDPOINT`: (Get from `HANDOVER.md`)
    -   `FOUNDRY_API_KEY`: (Get from `HANDOVER.md`)
    -   `WORKSPACE_ROOT`: `/home/site/wwwroot`
    -   `SCM_DO_BUILD_DURING_DEPLOYMENT`: `true` (Only for Python 3.11)

### 3. Copilot Studio Integration
**Action:** Connect the frontend agent.
-   **Resource:** `copilotstudio/RLMshowcase/` (Cloned Agent).
-   **Task:**
    1.  Get Function URL (e.g., `https://rlm-engine-uksouth.azurewebsites.net`).
    2.  Update Custom Connector (`shared_rlmfunctions`) in Copilot Studio with this Base URL.
    3.  Test "Start Audit" topic.

---

## 🤖 Copilot Studio & Foundry Connectivity (Recap)
-   **Architecture:** Two-Agent System.
    -   **Frontend:** Copilot Studio (Conversational UI).
    -   **Backend:** RLM Engine (Azure Function + Foundry Agents).
-   **Connectivity:**
    -   `copilot/openapi.json` -> Custom Connector -> Azure Function.
    -   `actions/rlm-root-agent.mcs.yml` -> Direct Foundry Agent Service (Hybrid mode).

## 📄 File Map
-   `rlm_engine.py`: The Brain (includes `run_code_audit`).
-   `function_app.py`: The API routing.
-   `copilotstudio/`: Use this for agent definitions.
