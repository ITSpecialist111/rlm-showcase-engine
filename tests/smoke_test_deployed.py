import requests
import time
import json
import sys

BASE_URL = "https://rlm-engine-uksouth.azurewebsites.net"

def run_smoke_test():
    print(f"Smoke Testing Deployment at: {BASE_URL}")

    # 0. Health Check
    health_url = f"{BASE_URL}/api/openapi.json"
    try:
        print(f"Checking Health: {health_url}")
        resp = requests.get(health_url)
        print(f"Health Status: {resp.status_code}")
        if resp.status_code != 200:
            print("WARNING: Health check failed. Function might not be loaded.")
            print(resp.text[:200])
    except Exception as e:
        print(f"Health Check exception: {e}")

    # 1. Start Audit
    start_url = f"{BASE_URL}/api/audit/start"
    print(f"POST {start_url}")
    
    try:
        resp = requests.post(start_url, json={"query": "Smoke Test Audit"})
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
        sys.exit(1)

    # 2. Poll Status
    status_url = f"{BASE_URL}/api/audit/status/{job_id}"
    print(f"Polling {status_url}...")
    
    start_time = time.time()
    last_log_count = 0
    
    while True:
        try:
            resp = requests.get(status_url)
            resp.raise_for_status()
            data = resp.json()
            
            status = data.get("status")
            logs = data.get("logs", [])
            
            # Print new logs
            if len(logs) > last_log_count:
                for log in logs[last_log_count:]:
                    print(f"[REMOTE LOG] {log}")
                last_log_count = len(logs)
            
            if status == "completed":
                print("\nSUCCESS: Job Completed.")
                print(json.dumps(data.get("result"), indent=2))
                break
            
            if status == "failed":
                print("\nFAILURE: Job Failed.")
                print(data.get("message"))
                break
                
            if time.time() - start_time > 120: # 2 minute timeout
                print("\nTIMEOUT: Job took too long.")
                break
                
            time.sleep(2)
            
        except Exception as e:
            print(f"Polling Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    run_smoke_test()
