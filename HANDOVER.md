# RLM Showcase Engine - Project Handover Document

**Date Created:** 2026-01-18
**Project Status:** Phase 2 - Verified Live (Async IO Enabled) ✅
**Last Updated:** 2026-01-19 17:55:00

---

## 📋 Executive Summary

The RLM (Recursive Language Model) Showcase Engine is a production-ready implementation of a hierarchical language model architecture. This project integrates **Microsoft Foundry**, **Azure Functions (Flex)**, and **Copilot Studio**.

**Jan 20 Update (Fixes):**
- **Smart Routing**: "Ask Anything" vs "Data Analysis" logic refined.
- **Dynamic Response**: Copilot now displays the actual backend result text.
- **Deployment Hardening**: `.funcignore` updated to exclude local environments (reducing upload from 128MB to <1MB) and `rlm_engine.py` syntax errors resolved.

**Jan 19 Update (Async Refactor):**
To support massive datasets (2,000+ files), we refactored the ingestion layer to use **Asynchronous IO (`aio`)**. This ensures the RLM Engine remains responsive to Copilot health checks even while downloading gigabytes of data.

**Key Achievements:**
- **Zero Blocking**: Switched to `azure.storage.blob.aio`.
- **High Concurrency**: Verified 2,000 document ingestion within Copilot timeout limits.
- **Auto-Routing**: Validated both "Compliance" and "Code Archeologist" scenarios.
- **Demo Data Prepared**: ☁️ **Blob Connectivity** established. Container `demo-invoices` created and seeded with 2,000 mock documents.

---

## 🔬 Theoretical Grounding (The "Why")

### Based on: *Recursive Language Models* (arXiv:2512.24601v1)
**Core Concept:** Treating long context as an *environment* (symbolic interaction) rather than a prompt.
**Our Implementation:**
1.  **Context-as-Environment**: Documents are loaded into a Python REPL (`context` variable).
2.  **Symbolic Interaction**: The LLM writes Python code to inspect, slice, and loop over documents.
3.  **Recursive Decomposition**: The generated code can call `llm_query()` to recurse on sub-problems.

**Refactor Note (Jan 19):** Switched from Map-Reduce to REPL architecture to align strictly with the paper.

---

## 🎬 Showcase Scenarios

### 1. The Compliance Auditor (LIVE ✅)
**Goal:** Process 2,000+ invoices against policy documents.
**User Experiene:**
-   User: *"Run audit"* (No complex prompt needed).
-   System: Defaults to "Full policy compliance audit", starts background job, and polls for status.
-   **Auto-Ingestion:** Backend automatically connects to `demo-invoices` blob container (Hardcoded default).
-   Visuals: Real-time streaming logs in Copilot Studio (e.g., *"Downloading Invoice_0042..."*).
-   Result: Accurate identification of policy violations across the massive dataset.


### 2. The Legacy Code Archaeologist (Ready 🏗️)
**Goal:** Trace logic across a repo.
**Status:** `execute_code_search` implemented. Invoke via `scenario="code_audit"` and pass a regex query.

### 3. The Wildcard (Agentic Freedom) 🔓
**Goal:** Demonstrate that the system is not "on rails".
**Mechanism:** The user types a custom question into the chat instead of clicking a button.
**Smart Routing:**
-   **General Chat ("Ask Anything"):** Questions like "Who are you?" or "Is the world flat?" are answered instantly using the LLM's general knowledge (No data load).
-   **Data Analysis:** Questions about "cost", "invoices", "compliance" trigger the **Invoice Audit** scenario, loading the document set for analysis.

**Example Prompts:**
- *"Who are the top 3 vendors by total spend? Show the calculation."* (Data Analysis)
- *"Calculate the average invoice amount and find outliers."* (Data Analysis)
- *"What is a recursive language model?"* (General Chat)

---

## 🏗️ Technical Architecture

```
User (Copilot Studio)
       ↓ (HTTP POST /audit/start)
[Azure Function: rlm-engine-uksouth] <───> [Status Manager]
       ↓ (Async Background Task)            ^
       │ (Smart Routing: Invoice vs Code vs General)
[RLM Engine (Python)] ──────────────────────┘
       ↓ (Foundry SDK)
[Root Agent] ──> [Sub-Agents] (Parallel Execution via Foundry)
```

**Architecture Note:** To simulate a high-scale distributed cluster within a single Function App demo instance, the backend acts as a "Virtual Cluster". It spawns "Simulated Workers" (Log threads) that process batches of files concurrently using `asyncio`, creating the appearance of multi-server activity in the logs. Physically, this maps to **2 Foundry Agents** (Root + Analysis), not 5+ servers.

### Components
1.  **Backend (Azure Functions - Flex Consumption)**
    -   **Runtime:** Python 3.11 (Simplifies deployment, no Docker needed).
    -   **Endpoints:**
        -   `POST /audit/start`: Starts job. Optional `blob_container` (defaults to `demo-invoices`).
        -   `GET /audit/status/{job_id}`: Returns status + logs.
        -   `GET /openapi.json`: Auto-serves spec for Connector import.
    -   **Telemetry:** Custom Events (`audit_job_created`, `audit_status_update`) pushed to App Insights.

2.  **Frontend (Copilot Studio)**
    -   **Pattern:** Agent-to-Agent Delegation.
    -   **Topics:**
        -   `AuditStart`: Calls backend, initializes `Global.JobId`.
        -   `AuditPoll`: Recursive loop checking status every 2s.
    -   **Connector:** Custom `RLMFunctions` connector (Imported via `openapi.json`).

---

## 🚀 Deployment Guide (Final)

### 1. Deploy Backend
```powershell
# Navigate to root
func azure functionapp publish rlm-engine-uksouth --python
```
*Note: We use Python 3.11 to allow native remote build on Flex Consumption.*

### 2. Configure Environment
App Settings in Azure Portal:
-   `FOUNDRY_ENDPOINT`: Your Foundry Project API URL.
-   `FOUNDRY_API_KEY`: Your Key.
-   `WORKSPACE_ROOT`: `/home/site/wwwroot` (Crucial for code audits).
-   `SCM_DO_BUILD_DURING_DEPLOYMENT`: `true`.

### 3. Copilot Studio Setup (Manual Rebuild)
If you need to recreate the agent:
1.  **Import Connector:** URL -> `https://rlm-engine-uksouth.azurewebsites.net/api/openapi.json`.
2.  **Auth:** API Key (Function Key/`x-functions-key`).
3.  **Topic "StartAudit"**:
    -   Trigger: "Run audit".
    -   Action: `StartAuditJob` (Query defaults to "Full audit" if empty).
    -   Set Variable: `Global.JobId`.
    -   Redirect: `AuditPoll` (or loop logic).
4.  **Displaying Results**:
    -   Unlike standard topics, **use `{Topic.summary}`** to display the final text response from the RLM engine.
    -   Do **not** use hardcoded success messages.

---

## ☁️ Demo Data Setup (Blob Storage)

To demonstrate processing thousands of files, we use Azure Blob Storage as the document source.

### 1. Prerequisites
Ensure `local.settings.json` (or Azure App Settings) has `AzureWebJobsStorage` set to a valid Storage Account connection string.

### 2. Setup Script
We include a utility script to create the container and upload mock data.
```powershell
# Create 'demo-invoices' container and upload 2,000 mock documents
python tools/generate_data.py
```

### 3. Running the Blob Demo
The system is configured to use the `demo-invoices` container by default if no documents are provided.
**Limit:** The backend is configured to process up to 2,500 documents per run.

**JSON Payload (Explicit):**
```json
{
  "query": "Audit these invoices against the travel policy",
  "blob_container": "demo-invoices"
}
```
**JSON Payload (Implicit/Default):**
```json
{
  "query": "Audit these invoices"
}
```

---
## 🔧 Troubleshooting & Maintenance
-   **Static/Hardcoded Messages:** If Copilot always says "468 invoices...", check the `StartAudit` topic. It likely has hardcoded text instead of the `{Topic.summary}` variable.
-   **Agent keeps asking for query:** **Resolution:** Backend now defaults to "Full audit" if query is missing.
-   **"Plan" output instead of "Result":** If the agent describes code ("Running this will...") instead of showing the number, the System Prompt needs tightening to force `print()` execution. (Fixed in Jan 20 update).
-   **Deployment fails:** Ensure you are on Python 3.11 and using `func azure functionapp publish ... --python`.

## 🧪 Quick Test
1.  **Open Copilot Test Pane.**
2.  **Say:** "Start Audit".
3.  **Expect:** "Audit Started! Job ID: ..." -> "Status: running (10%)" -> ... -> "Audit Complete!".
