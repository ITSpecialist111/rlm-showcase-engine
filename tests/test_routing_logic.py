import asyncio
import azure.functions as func
import json
import logging
from unittest.mock import Mock

# Import the function app code
import sys
sys.path.append("c:/Users/graham/Documents/GitHub/rlm-showcase-engine")
import function_app

# Set up basic logging to capture the logic output
logging.basicConfig(level=logging.INFO)

async def test_scenario_routing(query, expected_scenario_hint):
    print(f"\n--- Testing Query: '{query}' ---")
    
    # Mock Request
    req = func.HttpRequest(
        method="POST",
        body=json.dumps({"query": query}).encode("utf-8"),
        url="/api/audit/start",
        params={}
    )
    
    # We only need to start the audit and check the *logs* or the *initial status* to see where it *would* have gone.
    # Actually, start_audit launches a background task. 
    # The background task updates the status with a specific message:
    # "Starting analysis (scenario)..."
    
    resp = await function_app.start_audit(req)
    if resp.status_code != 202:
        print(f"Start failed: {resp.status_code}")
        return False
        
    data = json.loads(resp.get_body().decode())
    job_id = data["job_id"]
    
    # Poll briefly to catch the "Starting analysis" message
    from status_manager import status_manager
    
    for _ in range(5):
        await asyncio.sleep(1) # Wait for async task to fire
        status = status_manager.get_status(job_id)
        if not status: continue
        
        logs = status.get("logs", [])
        log_text = " ".join(logs).lower()
        
        # Check for the hint
        if expected_scenario_hint.lower() in log_text:
            print(f"✅ PASSED: Found hint '{expected_scenario_hint}'")
            return True
            
        # Fail fast if we see the WRONG hint
        # If we expect Invoice Audit but see General Chat
        if "general chat" in log_text and expected_scenario_hint != "general chat":
             print(f"❌ FAILED: Routed to General Chat instead of {expected_scenario_hint}")
             return False
        if "invoice_audit" in log_text and expected_scenario_hint == "general chat":
             print(f"❌ FAILED: Routed to Invoice Audit instead of General Chat")
             return False

    print("Timeout or inconclusive logs.")
    print("Logs:", logs)
    return False

async def run_tests():
    tests = [
        ("What is the total cost?", "invoice_audit"),
        ("How many files are available?", "invoice_audit"),
        ("List all documents", "invoice_audit"),
        ("What is the sum of expenses?", "invoice_audit"),
        ("Hello, who are you?", "general chat"),
        ("Full policy compliance audit", "invoice_audit"),
        ("Check code for class definitions", "code_audit")
    ]
    
    passed = 0
    for query, expected in tests:
        if await test_scenario_routing(query, expected):
            passed += 1
            
    print(f"\nTotal: {passed}/{len(tests)} PASSED")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_tests())
