import asyncio, os
from rlm_engine import execute_code_search

async def main():
    results = await execute_code_search('run_code_audit', repo_root=os.getcwd())
    print('Results count:', len(results))
    for r in results[:5]:
        print(r)

asyncio.run(main())
