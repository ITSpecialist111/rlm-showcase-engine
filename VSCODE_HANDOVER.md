# VS Code Handover: RLM Showcase

**Project Goal:** "Killing Showcase" of Recursive Language Models (RLM) on Microsoft Foundry.

## 🧠 Context for AI Assistant (Copilot)

We are building a 3-scenario showcase.
1.  **Compliance Auditor:** (DONE & DEPLOYED) Checks 50 invoices for policies.
2.  **Legacy Code Archaeologist:** (READY) Agent scans repo using `grep` (Scenario 2).
3.  **Manual Master:** (TODO) Technical manual helper.

**Current State (Jan 19 Update):**
-   **Architecture**: Refactored to Local REPL Loop (Python execution inside LLM context).
-   **Model**: Upgraded to `gpt-5.1-chat` (Azure OpenAI).
-   **Backend**: Deployed to `rlm-engine-uksouth` (UK South, Flex Consumption).
-   **Frontend**: Copilot Studio Agent fully wired with "Wow" logging.
-   **Status**: **LIVE & VERIFIED**. Ready for Showcase.

---

## 🚀 Active Scenarios
1.  **Compliance Auditor:** Checks 2,000+ invoices for policies.
2.  **Legacy Code Archaeologist:** Agent scans repo using `grep` (Scenario 2).
3.  **Agentic Freedom:** User enters wildcard queries (e.g. "Find top vendors") to prove code-on-demand.

---

## 🛠️ Tasks for VS Code Environment (Maintenance)

### 1. Redeploy Code
If you make changes to python files:
```powershell
func azure functionapp publish rlm-engine-uksouth --python
```

### 2. Copilot Studio File Map
-   **Valid Topics:** `topics/AuditStart.mcs.yml`, `topics/AuditPoll.mcs.yml`.
-   **Valid Actions:** `actions/StartAuditJob.mcs.yml`, `actions/GetAuditStatus.mcs.yml`.
-   **Connection:** `connectionreferences.mcs.yml` (Must match your environment's GUID).

### 3. Debugging
-   **Backend Logs:** Use App Insights in Azure Portal (Flex Consumption doesn't stream logs well continuously).
-   **Frontend:** Use the "Test Copilot" pane in VS Code or the Web UI.

---

## 🤖 Architecture Recap
-   **REPL Pattern:** The Agent writes code to see the data. It doesn't just "Read" it.
-   **RLM Paradigm:** We don't read documents; we *scan* them recursively using Python loops.

## ⚠️ Common Pitfalls fixed
-   **Duplicate Actions:** We deleted `start_audit.mcs.yml` (etc) in favor of the imported `StartAuditJob`.
-   **Query Prompting:** Backend now handles empty queries gracefully.
-   **Validation Errors:** Fixed by matching naming conventions in `.mcs.yml` files.
-   **Audit Options Card:** StartAudit topic now offers buttons for invoice audit, code audit, or custom query.

