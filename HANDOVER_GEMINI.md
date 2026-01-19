# RLM Showcase Engine — Gemini Handover
**Date:** 2026-01-19

## 🧠 Context
- **Goal:** Demonstrate Recursive Language Models (RLM) with a Compliance Auditor (50+ invoices, policy checks).
- **Stack:** Python 3.11+, Azure Functions V2, Microsoft Foundry (GPT-5.1 agents), Copilot Studio.
- **Architecture:** **REPL-based** (Paper specific). Context is an environment; agents write Python code.
- **Model:** `gpt-5.1-chat` (Requires `openai>=1.57.0`, `max_completion_tokens`, NO `temperature` param).

## 🗂️ Key Files
- `rlm_engine.py` — **Refactored**: Uses `REPLExecutor`. `temperature` param removed to fix O-series compatibility.
- `function_app.py` — HTTP triggers: `audit/start`, `audit/status/{job_id}`.
- `local.settings.json` — `ROOT_AGENT_DEPLOYMENT="gpt-5.1-chat"`. `AzureWebJobsStorage` must be empty for local testing without storage emulator.
- `tests/check_repl.py` — **Primary Test**: End-to-end verification script against local host (port 7072).

## 🧪 Tests (Validated Jan 19)
1. **Start Host:**
```powershell
# Port 7072 to avoid conflicts
func host start -p 7072
```
2. **Run Check:**
```powershell
python tests/check_repl.py
```
**Results:** Scenario 1 (Compliance) and Scenario 2 (Code Audit) verified locally.

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
  - **New:** `StartAudit` shows card buttons:
    - 📄 Invoice Compliance → `scenario=invoice_audit`, `blob_container=demo-invoices`
    - 🧠 Code Audit → `scenario=code_audit`
    - ✏️ Custom → prompts for query

### Flex Consumption Deployment (Python 3.11)
- **Runtime:** Python 3.11 (Recommended for stability).
- **Remote build:** Supported natively.
- **Publish:**
  ```powershell
  func azure functionapp publish rlm-engine-uksouth --python --build-remote
  ```
- **App settings:** `FOUNDRY_ENDPOINT`, `FOUNDRY_API_KEY`, `WORKSPACE_ROOT=/home/site/wwwroot`, `SCM_DO_BUILD_DURING_DEPLOYMENT=true`.
- **Note:** Ensure `DEPLOYMENT_STORAGE_CONNECTION_STRING` is correct in Azure Portal (use `fetch-app-settings` to verify).

## 🚧 Deployment Status
- **Deployed:** `rlm-engine-uksouth` (Flex Consumption **Python 3.11**).
- **Storage:** Account `rgrlmshowcaseuksout80ac`.
- **Functions:** `POST /api/audit/start`, `GET /api/audit/status/{job_id}`
- **Known Issue:** Job status is currently stored in-memory. On Flex Consumption, subsequent requests may hit different instances yielding 404s. Production requires Azure Table Storage.
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


## ✅ Status: COMPLETE (Ready for Showcase)
All active development tasks for the RLM Showcase are finished.
-   **Backend:** Stable, Async, Logging Enabled.
-   **Frontend:** Polished, Options UI, Live Polling.
-   **Documentation:** Handover, README, Implementation Plan updated.

## 🔜 Next Steps (Future Phase)
-   **Productionize:** Move from Flex Consumption to Durable Functions for long-running state.
-   **Scale:** Implement Azure Table Storage for persistent job history (currently in-memory fallback).
-   **Extend:** Add PDF parsing support to the blob ingestion pipeline.

## 💬 Prompts for Gemini (Maintenance)
-   "Help me debug a 500 error in the Azure Function logs."
-   "How do I add a new tool to the REPL executor?"
-   "Explain the Open-Ended Query architecture to a business user."

## 🏗️ Appendix: Valid Topic Configurations
**`copilotstudio/RLMshowcase/topics/AuditStart.mcs.yml` (Final Rich Version)**
```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: Start Audit
    triggerQueries:
      - start audit
      - begin audit
      - initiate audit process
      - launch an audit
      - kick off audit
      - run an audit now

  actions:
    - kind: Question
      id: question_oaXyT8
      interruptionPolicy:
        allowInterruption: true

      variable: init:Topic.Query
      prompt: What should I audit for?
      entity:
        kind: EmbeddedEntity
        definition:
          kind: ClosedListEntity
          items:
            - id: Audit these invoices against the travel policy
              displayName: Audit these invoices against the travel policy

            - id: Run code audit through the repository
              displayName: Run code audit through the repository

    - kind: ConditionGroup
      id: conditionGroup_te3bUS
      conditions:
        - id: conditionItem_0KvBoU
          condition: =Topic.Query = 'copilots_header_54b8d.topic.StartAudit.main.question_oaXyT8'.'Audit these invoices against the travel policy'

        - id: conditionItem_2O5y3N
          condition: =Topic.Query = 'copilots_header_54b8d.topic.StartAudit.main.question_oaXyT8'.'Run code audit through the repository'

    - kind: BeginDialog
      id: Action_StartJob
      input:
        binding:
          query: =Text(Topic.Query)

      dialog: copilots_header_54b8d.action.StartAuditJob
      output:
        binding:
          job_id: Topic.job_id
          message: Topic.message
          status: Topic.status

    - kind: SendActivity
      id: SendActivity_StartMsg
      activity: "Audit Started! Job ID: {Topic.job_id}"

    - kind: BeginDialog
      id: Action_GetStatus
      input:
        binding:
          job_id: =Topic.job_id

      dialog: copilots_header_54b8d.action.GetAuditStatus
      output:
        binding:
          created_at: Topic.created_at
          job_id: Topic.job_id
          logs: Topic.logs
          logs_text: Topic.logs_text
          message: Topic.message
          progress_percent: Topic.progress_percent
          result: Topic.result
          status: Topic.status
          updated_at: Topic.updated_at

    - kind: ConditionGroup
      id: Condition_CheckStatus
      conditions:
        - id: Condition_Success
          condition: =Topic.status = "completed"
          actions:
            - kind: SendActivity
              id: SendActivity_Success
              activity: |-
                ✅ Audit Complete!

                **Summary:**
                Job ID: {Topic.job_id}
                Status: {Topic.status}
                Completed: {Topic.updated_at}

                **Results:**
                {Topic.result}

                **Processing Log:**
                {Topic.logs_text}

        - id: Condition_Failed
          condition: =Topic.status = "failed"
          actions:
            - kind: SendActivity
              id: SendActivity_Fail
              activity: |-
                ❌ Audit Failed!

                **Error Details:**
                {Topic.message}

                **Job ID:** {Topic.job_id}

                **Logs:**
                {Topic.logs_text}

      elseActions:
        - kind: SendActivity
          id: SendActivity_StatusUpdate
          activity: "Status: {Topic.status} | Progress: {Topic.progress_percent}% | Logs: {Topic.logs_text}"

        - kind: AdaptiveCardPrompt
          id: Prompt_StatusCard
          card: "=\"{\"\"type\"\":\"\"AdaptiveCard\"\",\"\"version\"\":\"\"1.5\"\",\"\"body\"\":[{\"\"type\"\":\"\"TextBlock\"\",\"\"text\"\":\"\"Status: \" & Topic.status & \"\"\",\"\"weight\"\":\"\"Bolder\"\",\"\"size\"\":\"\"Medium\"\"},{\"\"type\"\":\"\"TextBlock\"\",\"\"text\"\":\"\"Logs: \" & Topic.logs_text & \"\"\",\"\"wrap\"\":true,\"\"size\"\":\"\"Small\"\",\"\"maxLines\"\":5}],\"\"actions\"\":[{\"\"type\"\":\"\"Action.Submit\"\",\"\"title\"\":\"\"🔄 Refresh Status\"\",\"\"data\"\":{\"\"submitActionId\"\":\"\"refresh\"\"}}]}\""
          output:
            binding:
              submitActionId: Topic.CardAction

          outputType:
            properties:
              submitActionId: String

        - kind: GotoAction
          id: Loop_Back
          actionId: Action_GetStatus

inputType: {}
outputType: {}
```
