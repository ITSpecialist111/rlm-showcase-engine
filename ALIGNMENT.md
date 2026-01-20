# RLM Showcase Engine: Architecture Alignment with MIT Paper (arXiv:2512.24601v1)

This document details how the **RLM Showcase Engine** implements the theoretical framework proposed in **"Recursive Language Models" (arXiv:2512.24601v1)**.

## 📋 Core Concept Alignment

| Paper Concept | Description | Showcase Implementation (`rlm-showcase-engine`) |
| :--- | :--- | :--- |
| **Context-as-Environment** | Treating large context not as input tokens, but as an interactive environment (variable) the model can inspect. | **`rlm_engine.py`**: The `context` variable in `REPLExecutor` holds the 2,000 document list. The LLM never sees the raw data; it sees the *variable name* `context`. |
| **Symbolic Interaction** | The model interacts with the environment using formal tools (code) rather than natural language reading. | **`rlm_engine.py`**: The `process_query` loop forces the LLM to write Python code (`print(context[0])`) to "observe" the data. |
| **Recursive Decomposition** | Breaking complex queries into sub-problems solved by sub-agents. | **`rlm_engine.py`**: The `llm_query()` function is exposed to the REPL, allowing the agent to *intent* to call a sub-agent. (Note: In this showcase, actual recursion is simulated for stability). |
| **Distributed Scaling** | Using a cluster of workers to manage the environment's scale. | **`function_app.py`**: We use an `asyncio` loop with randomized "Worker IDs" to simulate a distributed set of workers downloading blobs in parallel. |

---

## 🔬 Code-Level Mapping

### 1. The Environment (`rlm_engine.py`)
In the paper, the RLM is "born" into an environment containing the data.
*   **Code:** [`rlm_engine.py:186`](file:///c:/Users/graham/Documents/GitHub/rlm-showcase-engine/rlm_engine.py)
    ```python
    repl_globals = {
        "context": documents if documents else [], ...
    }
    ```
*   **Alignment:** ✅ **Direct.** We inject the data directly into the Python REPL's global scope.

### 2. The Systematic Prompt
The paper suggests a prompt that defines the "rules of engagement" for the environment.
*   **Code:** [`rlm_engine.py:228`](file:///c:/Users/graham/Documents/GitHub/rlm-showcase-engine/rlm_engine.py)
    ```python
    system_prompt = """...
    The data you need IS in the `context` variable.
    You must write Python code to read it."""
    ```
*   **Alignment:** ✅ **Direct.** The prompt explicitly forbids guessing and forces interaction.

### 3. The Recursion Interface
The paper describes an interface where the model can call `llm_query(prompt, context_subset)`.
*   **Code:** [`rlm_engine.py:178`](file:///c:/Users/graham/Documents/GitHub/rlm-showcase-engine/rlm_engine.py)
    ```python
    def sync_llm_query(prompt, context_subset):
        # Placeholder for full async recursion
        return f"[System: Recursive call...]"
    ```
*   **Alignment:** ⚠️ **Simulated.** The interface exists and is exposed to the LLM, but the execution is mocked for the single-process demo. Production would require `nest_asyncio` or IPC.

### 4. Distributed Data Loading
The paper implies a massive backing store.
*   **Code:** [`function_app.py`](file:///c:/Users/graham/Documents/GitHub/rlm-showcase-engine/function_app.py)
    ```python
    # Async download of 2,000 blobs
    async for blob in container_client.list_blobs...
    ```
*   **Alignment:** ✅ **Aligned.** We use Azure Blob Storage as the "Massive Context" store and stream it into the environment on demand.

---

## 📊 Feature Comparison Matrix

| Feature | Paper Ideal | Showcase Status | Production Gap |
| :--- | :--- | :--- | :--- |
| **Infinite Context** | Yes (via Pagination/Search) | **Yes** (via Python iterators) | None |
| **Determinism** | High (Code Execution) | **High** (Python REPL) | None |
| **Recursion Depth** | Unlimited | **1 Level** (Simulated) | Needs `nest_asyncio` |
| **Parallelism** | Multi-Node Cluster | **Single-Node Async** | Needs Azure Durable Functions |

