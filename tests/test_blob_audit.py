import requests
import time
import json
import sys

# Configuration
FUNCTION_URL = "https://rlm-engine-uksouth.azurewebsites.net/api/audit/start"
STATUS_URL = "https://rlm-engine-uksouth.azurewebsites.net/api/audit/status"
CONTAINER_NAME = "demo-invoices"

def run_test():
    print(f"Testing Blob Audit against {CONTAINER_NAME}...")
    
    payload = {
        "query": "Find all invoices with amount > $4000",
        "blob_container": CONTAINER_NAME
    }
    
    # 1. Start Job
    try:
        start_resp = requests.post(FUNCTION_URL, json=payload)
        start_resp.raise_for_status()
        data = start_resp.json()
        job_id = data.get("job_id")
        print(f"Job started. ID: {job_id}")
    except Exception as e:
        print(f"Failed to start job: {e}")
        print(start_resp.text if 'start_resp' in locals() else "")
        sys.exit(1)

    # 2. Poll Status
    while True:
        try:
            status_resp = requests.get(f"{STATUS_URL}/{job_id}")
            status_resp.raise_for_status()
            status_data = status_resp.json()
            
            state = status_data.get("status")
            pct = status_data.get("progress_percent")
            msg = status_data.get("message")
            
            print(f"[{pct}%] {state}: {msg}")
            
            if state in ["completed", "failed"]:
                if state == "completed":
                    print("\n--- Result ---")
                    result = status_data.get("result", {})
                    print(json.dumps(result, indent=2))
                    
                    # Verify we actually downloaded docs
                    logs = status_data.get("logs_text", "")
                    if "Downloaded" in logs and "documents from Blob Storage" in logs:
                        print("\nSUCCESS: Access to Blob Storage confirmed in logs.")
                    else:
                        print("\nWARNING: Did not see download confirmation in logs.")
                        
                else:
                    print(f"\nFailed. Logs:\n{status_data.get('logs_text')}")
                break
                
            time.sleep(2)
            
        except Exception as e:
            print(f"Polling failed: {e}")
            break

if __name__ == "__main__":
    run_test()
