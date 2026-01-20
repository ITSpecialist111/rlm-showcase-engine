import asyncio
import azure.functions as func
import json
import logging
from unittest.mock import Mock

# Import the function app code
import sys
import os
sys.path.append("c:/Users/graham/Documents/GitHub/rlm-showcase-engine")
import function_app

async def run_test():
    print("--- Starting Integration Test for General Chat ---")
    
    # Mock Request
    req = func.HttpRequest(
        method="POST",
        body=json.dumps({"query": "What is the capital of France?"}).encode("utf-8"),
        url="/api/audit/start",
        params={}
    )
    
    # 1. Start Audit
    print("Calling start_audit...")
    resp = await function_app.start_audit(req)
    if resp.status_code != 202:
        print(f"FAILED: Expected 202, got {resp.status_code}")
        print(resp.get_body().decode())
        return

    data = json.loads(resp.get_body().decode())
    job_id = data["job_id"]
    print(f"Job ID: {job_id}")

    # 2. Poll Status (Simulating the background execution which is triggered via asyncio.create_task in start_audit)
    # Since start_audit uses asyncio.create_task, the background task *should* be running in the event loop.
    # We will wait a bit.
    
    print("Polling for status...")
    for _ in range(15):
        await asyncio.sleep(2)
        
        # Manually invoke get_status route logic (simplification)
        # We can just check the status_manager directly since we are in the same process
        from status_manager import status_manager
        status = status_manager.get_status(job_id)
        
        if not status:
            print("Status not found yet...")
            continue
            
        logs = status.get("logs", [])
        log_text = " ".join(logs).lower()
        pct = status.get("progress_percent")
        s_state = status.get("status")
        
        print(f"State: {s_state} ({pct}%) -> Last Log: {logs[-1] if logs else ''}")

        if s_state in ["completed", "failed"]:
            print(f"Finished. Result: {status.get('result')}")
            if "general chat" in log_text:
                print("✅ PASSED: 'General Chat' detected in logs.")
            else:
                print("❌ FAILED: 'General Chat' NOT detected in logs.")
            return

    print("Timeout.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_test())
