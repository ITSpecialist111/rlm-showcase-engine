import asyncio, os
from rlm_engine import RLMEngine, RLMConfig
from config import settings

async def main():
    cfg = RLMConfig(
        foundry_endpoint=settings.FOUNDRY_ENDPOINT,
        api_key=settings.FOUNDRY_API_KEY,
        root_agent_deployment=settings.ROOT_AGENT_DEPLOYMENT,
        sub_agent_deployment=settings.SUB_AGENT_DEPLOYMENT
    )
    eng = RLMEngine(cfg)
    results = await eng.run_code_audit('run_code_audit', repo_root=os.getcwd())
    print('Results count:', len(results))
    for r in results[:5]:
        print(r)

asyncio.run(main())
