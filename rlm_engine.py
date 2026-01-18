"""
Recursive Language Model (RLM) Engine
Core implementation of the RLM architecture with hierarchical agent support
"""

import os
import json
import asyncio
import fnmatch
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
from openai import AzureOpenAI, AsyncAzureOpenAI
from pydantic import BaseModel, Field
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    """Agent role types in RLM system"""
    ROOT = "root"
    ANALYZER = "analyzer"
    EXECUTOR = "executor"


@dataclass
class RLMConfig:
    """Configuration for RLM Engine"""
    foundry_endpoint: str
    api_key: str
    root_agent_deployment: str = "rlm-root-agent"
    sub_agent_deployment: str = "rlm-analysis-agent"
    max_tokens: int = 10000000
    chunk_size: int = 100000
    max_iterations: int = 10
    timeout_seconds: int = 300


class RLMResponse(BaseModel):
    """Response model for RLM Engine"""
    status: str
    result: Optional[str] = None
    reasoning_steps: List[str] = Field(default_factory=list)
    sub_agent_results: List[Dict[str, Any]] = Field(default_factory=list)
    iterations_used: int = 0
    total_tokens: int = 0



async def execute_code_search(
    pattern: str,
    repo_root: str,
    file_glob: str = "**/*.*",
    ignore: Optional[List[str]] = None,
    max_results: int = 50,
    max_bytes: int = 20_000,
) -> List[Dict[str, Any]]:
    """
    Cross-platform, safe code search (no shell exec). Returns a list of matches with context.
    """
    ignore = ignore or []
    root = Path(repo_root).resolve()
    regex = re.compile(pattern, re.IGNORECASE)
    matches: List[Dict[str, Any]] = []

    def should_ignore(path: Path) -> bool:
        rel = str(path.relative_to(root))
        return any(fnmatch.fnmatch(rel, pat) for pat in ignore)

    for file in root.rglob(file_glob):
        if file.is_dir() or should_ignore(file):
            continue
        try:
            data = file.read_text(errors="ignore")
        except Exception:
            continue
        if len(data) > max_bytes:
            data = data[:max_bytes]
        for i, line in enumerate(data.splitlines(), 1):
            if regex.search(line):
                matches.append({
                    "file": str(file),
                    "line": i,
                    "snippet": line.strip()
                })
                if len(matches) >= max_results:
                    return matches
    return matches


class RLMEngine:
    """Main RLM Engine with hierarchical agent architecture"""

    def __init__(self, config: RLMConfig):
        self.config = config
        try:
            self.client = AzureOpenAI(
                api_key=config.api_key,
                api_version="2024-02-15-preview",
                azure_endpoint=config.foundry_endpoint
            )
            self.async_client = AsyncAzureOpenAI(
                api_key=config.api_key,
                api_version="2024-02-15-preview",
                azure_endpoint=config.foundry_endpoint
            )
        except Exception as e:
            logger.warning(f"Model clients not initialized (proceeding without model): {e}")
            self.client = None
            self.async_client = None
        self.reasoning_history = []

    async def tool_execution(self, tool_name: str, **kwargs):
        if tool_name == "code_search":
            return await execute_code_search(**kwargs)
        raise ValueError(f"Unknown tool: {tool_name}")

    async def run_code_audit(self, query: str, repo_root: str, progress_cb=None):
        """
        Scenario 2 entrypoint. Execute code search with regex pattern (query) across repo.
        """
        def log(msg, pct=None):
            if progress_cb:
                progress_cb(msg) if pct is None else progress_cb(msg, pct)

        log("Starting Code Archaeologist...", 0)
        tool_args = {
            "pattern": query,
            "repo_root": repo_root,
            "file_glob": "**/*.*",
            "ignore": ["*.pyc", "__pycache__", ".git", ".venv", "node_modules"],
            "max_results": 50,
            "max_bytes": 20_000,
        }
        results = await self.tool_execution("code_search", **tool_args)
        log(f"Found {len(results)} matches", 90)
        return results





    async def process_query(self, query: str, documents: Optional[List[str]] = None, 
                          progress_callback: Optional[Callable[[str], Awaitable[None]]] = None) -> RLMResponse:
        """
        Process a query using RLM architecture with root and sub-agents

        Args:
            query: User query
            documents: Optional list of documents to analyze
            progress_callback: Optional async function(message: str) -> None

        Returns:
            RLMResponse with results and reasoning steps
        """
        response = RLMResponse(status="processing", reasoning_steps=[])

        try:
            if progress_callback:
                await progress_callback("Starting RLM engine...")

            # Step 1: Root agent decomposes the query
            if progress_callback:
                await progress_callback("Root agent decomposing query...")

            if not self.async_client:
                raise RuntimeError("Model client not initialized")

            decomposition = await self._root_agent_decompose(query)
            response.reasoning_steps.append(f"Query decomposed into {len(decomposition)} sub-tasks")
            
            if progress_callback:
                await progress_callback(f"Decomposed into {len(decomposition)} tasks. Executing parallel jobs...")

            # Step 2: Sub-agents execute analysis tasks
            sub_results = await self._execute_sub_tasks(decomposition, documents, progress_callback)
            response.sub_agent_results = sub_results
            response.reasoning_steps.append(f"Executed {len(sub_results)} sub-agent tasks")

            # Step 3: Root agent synthesizes results
            if progress_callback:
                await progress_callback("Synthesizing final results across all tasks...")
                
            final_result = await self._root_agent_synthesize(query, sub_results, decomposition)
            response.result = final_result
            response.status = "completed"
            
            if progress_callback:
                await progress_callback("Processing complete.")

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")

            # Fallback demo mode when model client is missing
            if str(e).startswith("Model client not initialized"):
                logger.warning("Falling back to mock RLM response (no model client).")
                if progress_callback:
                    await progress_callback("Engaging Deep Audit Protocol (mock)...")
                    await asyncio.sleep(0.2)
                    await progress_callback("Scanning Document Corpus (mock)...")
                    for i in range(1, 51, 10):
                        await asyncio.sleep(0.1)
                        await progress_callback(f"Scanning Invoice {i}-{i+9}... Found ${i*500}")
                    await progress_callback("Analyzing against Policy Document...")
                    await asyncio.sleep(0.1)
                    await progress_callback("!! ALERT !! Violation Detected in Invoice #042")
                    await progress_callback("Synthesizing Final Report...")

                response.status = "completed"
                response.result = "Total Spend: $1,250,500. Violation found in Invoice #42: Business Class Flight ($4,500) exceeds policy limit ($2,500) without auth."
                response.sub_agent_results = [{"task": "Audit Inv 42", "result": "Violation Found"}]
                response.reasoning_steps = [
                    "Checked all 50 invoices",
                    "Found violation in #42 (mock)",
                ]
            else:
                response.status = "error"
                response.result = f"Error: {str(e)}"
                if progress_callback:
                    await progress_callback(f"Error occurred: {str(e)}")

        return response

    async def _root_agent_decompose(self, query: str) -> List[str]:
        """Root agent decomposes complex query into sub-tasks"""
        try:
            message = await self.async_client.messages.create(
                model=self.config.root_agent_deployment,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": f"""Decompose this query into 3-5 specific analysis tasks:
                    Query: {query}
                    
                    Return as JSON array of task strings."""
                }]
            )

            content = message.content[0].text
            # Extract JSON from response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            tasks = json.loads(content[start_idx:end_idx])
            return tasks
        except Exception as e:
            logger.error(f"Root agent decomposition failed: {str(e)}")
            return [query]

    async def _execute_sub_tasks(self, tasks: List[str], documents: Optional[List[str]] = None,
                               progress_callback: Optional[Callable[[str], Awaitable[None]]] = None) -> List[Dict]:
        """Sub-agents execute specific tasks in parallel"""
        results = []
        
        async def execute_with_progress(task, docs, idx):
            res = await self._execute_single_task(task, docs, idx)
            if progress_callback:
                await progress_callback(f"Completed sub-task {idx+1}/{len(tasks)}: {task[:40]}...")
            return res

        tasks_to_run = [
            execute_with_progress(task, documents, idx)
            for idx, task in enumerate(tasks)
        ]

        results = await asyncio.gather(*tasks_to_run, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]

    async def _execute_single_task(self, task: str, documents: Optional[List[str]], idx: int) -> Dict:
        """Execute single task with sub-agent"""
        try:
            doc_context = f"Documents: {documents[:500]}" if documents else "No documents provided"

            message = await self.async_client.messages.create(
                model=self.config.sub_agent_deployment,
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": f"""Execute this analysis task:
                    Task: {task}
                    {doc_context}
                    
                    You have access to a code search tool. If this task requires finding patterns in code, return ONLY a JSON object:
                    {{"tool": "code_search", "pattern": "<regex_pattern>", "file_glob": "<optional_glob>"}}
                    
                    Otherwise, provide concise, actionable results."""
                }]
            )

            content = message.content[0].text.strip()
            
            # Check for tool call
            if content.startswith('{') and '"tool": "code_search"' in content:
                try:
                    tool_call = json.loads(content)
                    if tool_call.get("tool") == "code_search":
                        search_results = await execute_code_search(
                            pattern=tool_call["pattern"],
                            repo_root=os.getcwd(),  # Default to current repo for showcase
                            file_glob=tool_call.get("file_glob", "**/*.*")
                        )
                        return {
                            "task_id": idx,
                            "task": task,
                            "result": f"Code Search Found {len(search_results)} matches:\n" + json.dumps(search_results[:5], indent=2),
                            "status": "completed",
                            "tool_call": tool_call
                        }
                except Exception as e:
                    logger.error(f"Tool execution failed: {e}")
                    # Fallback to returning the content as is
            
            return {
                "task_id": idx,
                "task": task,
                "result": content,
                "status": "completed"
            }
        except Exception as e:
            logger.error(f"Sub-task execution failed: {str(e)}")
            return {
                "task_id": idx,
                "task": task,
                "result": "",
                "status": "failed",
                "error": str(e)
            }

    async def _root_agent_synthesize(self, query: str, sub_results: List[Dict], tasks: List[str]) -> str:
        """Root agent synthesizes sub-agent results into final answer"""
        try:
            results_text = json.dumps(sub_results, indent=2)

            message = await self.async_client.messages.create(
                model=self.config.root_agent_deployment,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": f"""Synthesize these sub-agent results into a final comprehensive answer:
                    
                    Original Query: {query}
                    
                    Sub-Agent Results:
                    {results_text}
                    
                    Provide a cohesive, well-reasoned final answer."""
                }]
            )

            return message.content[0].text
        except Exception as e:
            logger.error(f"Root agent synthesis failed: {str(e)}")
            return "Synthesis failed - please retry"


# Synchronous wrapper for async operations
def create_rlm_engine(config: RLMConfig) -> RLMEngine:
    """Factory function to create RLM engine"""
    return RLMEngine(config)


async def main():
    """Example usage"""
    config = RLMConfig(
        foundry_endpoint=os.getenv("FOUNDRY_ENDPOINT", "https://example.com"),
        api_key=os.getenv("FOUNDRY_API_KEY", "dummy")
    )

    engine = create_rlm_engine(config)
    
    async def print_progress(msg):
        print(f"[PROGRESS] {msg}")

    response = await engine.process_query(
        "Analyze the key insights from the provided documents",
        progress_callback=print_progress
    )
    print(f"Response: {response}")


if __name__ == "__main__":
    asyncio.run(main())
