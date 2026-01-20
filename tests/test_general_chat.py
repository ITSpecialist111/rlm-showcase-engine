import requests
import time
import sys

# Configuration
ENDPOINT = "http://localhost:7071/api/audit/start"
STATUS_ENDPOINT = "http://localhost:7071/api/audit/status/"

def test_query(test_name, query, expected_scenario_hint):
    print(f"\n--- Test: {test_name} ---")
    print(f"Query: '{query}'")
    
    payload = {"query": query}
    try:
        response = requests.post(ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()
        job_id = data.get("job_id")
        print(f"Job started: {job_id}")
    except Exception as e:
        print(f"Start failed: {e}")
        return

    # Poll
    for _ in range(30):
        time.sleep(1)
        res = requests.get(STATUS_ENDPOINT + job_id)
        status_data = res.json()
        status = status_data.get("status")
        pct = status_data.get("progress_percent")
        logs = status_data.get("logs", [])
        
        # Check logs for clues about scenario
        log_text = " ".join(logs).lower()
        
        if status in ["completed", "failed"]:
            print(f"Finished with status: {status}")
            print(f"Result: {status_data.get('result')}")
            
            # Verification
            if expected_scenario_hint.lower() in log_text:
                print(f"✅ PASSED: Found expected hint '{expected_scenario_hint}' in logs.")
            else:
                 print(f"❌ FAILED: Did not find '{expected_scenario_hint}' in logs.")
                 print("Logs:", logs)
            return
        
        if _ % 2 == 0:
            print(f"Polling... {pct}% ({status})")

    print("Timeout waiting for completion.")

if __name__ == "__main__":
    # Test 1: General Chat
    test_query("General Chat", "What is the capital of France?", "General Chat")
    
    # Test 2: Invoice Audit (Force via keyword)
    # We expect 'Spawning Worker' or 'Blob' related logs if it goes to invoice path, 
    # but we want to avoid actually waiting for big downloads if possible or just verify the log intent.
    # Since we don't want to actually stress test the blob download here, we rely on the log message "Accessing Blob Container"
    # test_query("Invoice Audit", "Check these invoices for compliance", "Connector") 
