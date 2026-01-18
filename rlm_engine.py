"""
Recursive Language Model (RLM) Engine
Core implementation of the RLM architecture with hierarchical agent support
"""

import os
import json
import asyncio
from typing import Optional, List, Dict, Any
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


class RLMEngine:
      """Main RLM Engine with hierarchical agent architecture"""

    def __init__(self, config: RLMConfig):
              self.config = config
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
              self.reasoning_history = []

    async def process_query(self, query: str, documents: Optional[List[str]] = None) -> RLMResponse:
              """
                      Process a query using RLM architecture with root and sub-agents

                                      Args:
                                                  query: User query
                                                              documents: Optional list of documents to analyze

                                                                              Returns:
                                                                                          RLMResponse with results and reasoning steps
                                                                                                  """
              response = RLMResponse(status="processing", reasoning_steps=[])

        try:
                      # Step 1: Root agent decomposes the query
                      decomposition = await self._root_agent_decompose(query)
                      response.reasoning_steps.append(f"Query decomposed into {len(decomposition)} sub-tasks")

            # Step 2: Sub-agents execute analysis tasks
                      sub_results = await self._execute_sub_tasks(decomposition, documents)
                      response.sub_agent_results = sub_results
                      response.reasoning_steps.append(f"Executed {len(sub_results)} sub-agent tasks")

            # Step 3: Root agent synthesizes results
                      final_result = await self._root_agent_synthesize(query, sub_results, decomposition)
                      response.result = final_result
                      response.status = "completed"

except Exception as e:
              logger.error(f"Error processing query: {str(e)}")
              response.status = "error"
              response.result = f"Error: {str(e)}"

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

    async def _execute_sub_tasks(self, tasks: List[str], documents: Optional[List[str]] = None) -> List[Dict]:
              """Sub-agents execute specific tasks in parallel"""
              results = []
              tasks_to_run = [
                  self._execute_single_task(task, documents, idx)
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

                                                    Provide concise, actionable results."""
                              }]
            )

            return {
                              "task_id": idx,
                              "task": task,
                              "result": message.content[0].text,
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
          foundry_endpoint=os.getenv("FOUNDRY_ENDPOINT"),
          api_key=os.getenv("FOUNDRY_API_KEY")
      )

    engine = create_rlm_engine(config)
    response = await engine.process_query(
              "Analyze the key insights from the provided documents"
    )
    print(f"Response: {response}")


if __name__ == "__main__":
      asyncio.run(main())
