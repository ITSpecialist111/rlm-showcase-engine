import requests
import time
import json

BASE_URL = "http://127.0.0.1:7072"

def test_repl():
    print(f"Testing REPL Logic at: {BASE_URL}")

    # Start Audit with simple math query
    start_url = f"{BASE_URL}/api/audit/start"
    print(f"POST {start_url} (REPL Test)")
    
    # We rely on function_app default mock docs if documents list is empty
    payload = {
        "query": "How many documents are there in the context? Use python code to find out.", 
        "scenario": "invoice_audit"
    }
    
    try:
        resp = requests.post(start_url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        job_id = data.get("job_id")
        print(f"Job Started: {job_id}")
    except Exception as e:
        print(f"Failed to start audit: {e}")
        try:
             print(resp.text)
        except:
             pass
        return

    # Poll Status
    status_url = f"{BASE_URL}/api/audit/status/{job_id}"
    print(f"Polling {status_url}...")
    
    for i in range(20): # increased timeout for LLM thinking
        try:
            resp = requests.get(status_url)
            data = resp.json()
            status = data.get("status")
            pct = data.get("progress_percent")
            msg = data.get("message")
            
            # Print new logs only (simplified)
            # Actually just print status/msg
            print(f"[{i}] Status: {status} ({pct}%) - {msg}")
            
            if status in ["completed", "failed"]:
                print("Final Result:")
                print(json.dumps(data, indent=2))
                break
        except Exception as e:
            print(f"Error polling: {e}")
        
        time.sleep(2)

if __name__ == "__main__":
    test_repl()
