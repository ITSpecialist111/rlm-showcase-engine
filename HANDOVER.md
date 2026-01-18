# RLM Showcase Engine - Project Handover Document

**Date Created:** 2026-01-18
**Project Status:** Phase 2 - 100% Complete (Backend Deployed & Integrated)
**Last Updated:** 2026-01-18 19:30:00

---

## 📋 Executive Summary

The RLM (Recursive Language Model) Showcase Engine is a production-ready implementation of a hierarchical language model architecture, grounded in the MIT paper *Recursive Language Models*. This project integrates **Microsoft Foundry**, **Azure Functions (Flex)**, and **Copilot Studio** to demonstrate how to solve the "Context Rot" problem for massive datasets.

**Key Achievement:** The system is fully operational. The backend successfully processes audit requests via a background job queue, and the Copilot Studio frontend provides a seamless, "Agent-to-Agent" conversational interface.

---

## 🔬 Theoretical Grounding (The "Why")

### Based on: *Recursive Language Models* (arXiv:2512.24601v1)
**Core Concept:** Treating long context as an *environment* (symbolic interaction) rather than a prompt.
**Our Implementation:**
1.  **Context-as-Environment**: Documents are stored externally; the Agent requests scans.
2.  **Symbolic Interaction**: `RLMEngine` acts as the REPL, executing scanned tasks.
3.  **Recursive Decomposition**: Map-Reduce pattern used for parallel compliance checks.

---

## 🎬 Showcase Scenarios

### 1. The Compliance Auditor (LIVE ✅)
**Goal:** Process 50+ invoices against policy documents.
**User Experiene:**
-   User: *"Run audit"* (No complex prompt needed).
-   System: Defaults to "Full policy compliance audit", starts background job, and polls for status.
-   Visuals: Real-time streaming logs in Copilot Studio (e.g., *"Scanning Invoice #42... VIOLATION"*).
-   Result: 100% accurate identification of the "Business Class" violation.

### 2. The Legacy Code Archaeologist (Ready 🏗️)
**Goal:** Trace logic across a repo.
**Status:** `execute_code_search` implemented. Invoke via `scenario="code_audit"` and pass a regex query.

---

## 🏗️ Technical Architecture

```
User (Copilot Studio)
       ↓ (HTTP POST /audit/start)
[Azure Function: rlm-engine-uksouth] <───> [Status Manager]
       ↓ (Async Background Task)            ^
[RLM Engine (Python)] ──────────────────────┘
       ↓ (Foundry SDK)
[Root Agent] ──> [Sub-Agents] (Parallel Execution)
```

### Components
1.  **Backend (Azure Functions - Flex Consumption)**
    -   **Runtime:** Python 3.11 (Simplifies deployment, no Docker needed).
    -   **Endpoints:**
        -   `POST /audit/start`: Starts job (Query optional, defaults to full audit).
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
3.  **Topic "Audit Start"**:
    -   Trigger: "Run audit".
    -   Action: `StartAuditJob` (Query defaults to "Full audit" if empty).
    -   Set Variable: `Global.JobId`.
    -   Redirect: `AuditPoll`.
4.  **Topic "Audit Poll"**:
    -   Action: `GetAuditStatus` (Input: `Global.JobId`).
    -   Message: Status + Logs.
    -   Condition: If not complete, Loop (Redirect to Self).

---

## � Troubleshooting & Maintenance
-   **"Unknown Element" in Copilot:** Caused by file naming conflicts. **Resolution:** We renamed actions to simple names (`StartAuditJob`, `GetAuditStatus`) and deleted old/duplicate files.
-   **Agent keeps asking for query:** **Resolution:** Backend now defaults to "Full audit" if query is missing.
-   **Deployment fails:** Ensure you are on Python 3.11 and using `func azure functionapp publish ... --python`.

## 🧪 Quick Test
1.  **Open Copilot Test Pane.**
2.  **Say:** "Start Audit".
3.  **Expect:** "Audit Started! Job ID: ..." -> "Status: running (10%)" -> ... -> "Audit Complete!".
