import requests
import time
import json
import sys

BASE_URL = "http://localhost:7071"

def test_local():
    print(f"Testing Local Function at: {BASE_URL}")

    # 1. Start Code Audit
    start_url = f"{BASE_URL}/api/audit/start"
    print(f"POST {start_url} (Code Audit)")
    
    payload = {
        "query": "run_code_audit", 
        "scenario": "code_audit"
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

    # 2. Poll Status
    status_url = f"{BASE_URL}/api/audit/status/{job_id}"
    print(f"Polling {status_url}...")
    
    for i in range(10):
        try:
            resp = requests.get(status_url)
            data = resp.json()
            status = data.get("status")
            pct = data.get("progress_percent")
            print(f"[{i}] Status: {status} ({pct}%)")
            if status is None:
                print("Full Response:", json.dumps(data, indent=2))
            
            if status in ["completed", "failed"]:
                print("Final Result:")
                print(json.dumps(data, indent=2))
                break
        except Exception as e:
            print(f"Error polling: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    test_local()
