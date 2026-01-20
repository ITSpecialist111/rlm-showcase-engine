# RLM Showcase Engine
**Recursive Language Model (RLM) Implementation for Microsoft Foundry**

Wait... isn't this just another chatbot?
**No.** This is an **Autonomous Agentic System** designed to solve problems that traditional LLMs cannot.

---

## 🤯 The Concept: "Environment, not Prompt"
Traditional RAG (Retrieval Augmented Generation) stuffs documents into a text prompt and hopes the AI can read them all. It's like asking a human to memorize a library in 5 seconds.

**RLM flips this paradigm.** 
Instead of forcing data into the "Brain" (the model's context window), we put the Brain into a **Tool-Rich Environment** where the data lives.

### How it works (The "Wow" Factor)
When you ask *"Audit these 5,000 invoices"*, the system does not just read them. It **acts**:

1.  **Orchestration:** The system spins up **Worker Agents** (simulated threads) to physically download and parse thousands of files from Azure Blob Storage.
2.  **Observation:** The **Root Agent** wakes up in a Python REPL (Read-Eval-Print Loop). It doesn't see the text yet—it sees a variable called `context`.
3.  **Analysis (The Loop):**
    *   **Thought:** *"I need to see the first invoice structure."*
    *   **Action:** It writes real Python code: `print(context[0])`.
    *   **Observation:** It sees the invoice data.
    *   **Thought:** *"Okay, I need to filter for amounts > $1,000. I'll write a loop."*
    *   **Action:** It writes a Python script to process the entire 5,000-document dataset in memory.
4.  **Synthesis:** It returns the mathematically precise result found by its code.

**Why this matters:** It allows us to process datasets **100x larger** than a standard model context window, effectively giving the agent "Infinite Context" via symbolic reasoning.

---


## ⚙️ Technical Deep Dive

### Architecture
The system follows a distributed **Client‑Server‑Agent** pattern:

![Architecture Diagram](https://github.com/ITSpecialist111/rlm-showcase-engine/blob/main/Mermaid-preview.png)


```

### The "Inner Workings"

#### 1. The Async Orchestrator (`function_app.py`)
*   **Role:** The "Body" of the system.
*   **Mechanism:** Built on **Azure Functions (Flex Consumption)** running Python 3.11.
*   **Process:**
    *   Receives a `POST /audit/start` request.
    *   Uses `asyncio` and `azure-storage-blob` to parallel-stream documents into memory.
    *   **Agentic Logging:** Emits real-time events (`👥 Spawning Worker Agents...`) to the Status Manager, which connects to the Copilot Studio UI.

#### 2. The RLM Engine (`rlm_engine.py`)
*   **Role:** The "Brain".
*   **Core Loop (`process_query`):**
    *   Constructs a **System Prompt** that defines the "Environment": *"You are an RLM. Data is in `context`. Write code to read it."*
    *   **Iteration:**
        1.  Sends prompt + state to GPT-4o.
        2.  LLM responds with a **Code Block** (e.g., ````python ... ````) or a **Final Answer**.
        3.  If Code: The built-in `REPLExecutor` runs `exec()` on the code, capturing `stdout`.
        4.  The output is appended to the chat history as an "Observation".
        5.  The loop repeats until the LLM says `FINAL_ANSWER`.

#### 3. State Management (`status_manager.py`)
*   **Role:** The "Memory".
*   **Mechanism:** Uses **Azure Table Storage** (or local in-memory fallback) to persist Job IDs and Logs.
*   Connects the async backend to the synchronous polling frontend.

### Sample Output (What you see in the console)
This stream proves the distributed nature of the execution:
```log
[21:56:10] 🚀 [System] Initializing RLM Engine on https://rlm-showcase...
[21:56:11] 👥 [Orchestrator] Spawning Worker Agents...
[21:56:12] 👷 [Worker-3] Analyzing batch starting at Invoice_0000...
[21:56:12] 👷 [Worker-5] Analyzing batch starting at Invoice_0019...
[21:56:12] 👷 [Worker-1] Analyzing batch starting at Invoice_0037...
...
[21:56:18] ✅ [Orchestrator] Aggregated 2000 documents.
[21:56:19] 🧠 [Root Agent] Thinking (Iteration 1)...
[21:56:20] ⚡ [REPL] Executing Python analysis code...
[21:56:22] 📝 [Result] Final Answer Generated.
```

---

## 🚀 Getting Started

### Prerequisites
*   Azure Subscription
*   Python 3.11
*   Azure Functions Core Tools

### Deployment
```powershell
func azure functionapp publish rlm-engine-uksouth --python
```

### Running a Demo
1.  Open Copilot Studio Test Pane.
2.  Say **"Start Audit"**.
3.  Select **"Invoice Compliance"**.
4.  Watch the Agentic Logs stream in real-time.
