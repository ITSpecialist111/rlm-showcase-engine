import requests
import json
import time

FUNCTION_URL = "https://rlm-engine-uksouth.azurewebsites.net/api/audit/start"
STATUS_URL = "https://rlm-engine-uksouth.azurewebsites.net/api/audit/status"

def verify_default():
    print("Testing Default Blob Container (no parameter)...")
    
    # NO blob_container specified
    payload = {
        "query": "Find high value invoices"
    }
    
    start_resp = requests.post(FUNCTION_URL, json=payload)
    if start_resp.status_code != 202:
        print(f"Failed start: {start_resp.text}")
        return

    job_id = start_resp.json()["job_id"]
    print(f"Job IDs: {job_id}")

    # Poll
    for _ in range(30):
        resp = requests.get(f"{STATUS_URL}/{job_id}").json()
        print(f"Status: {resp['status']} - {resp.get('message', '')}")
        
        if resp['status'] == 'completed':
            logs = resp.get('logs_text', '')
            if "demo-invoices" in logs or "Downloaded" in logs:
                print("SUCCESS: Used default blob container!")
            else:
                 print("WARNING: Did not see blob download in logs.")
                 print(logs)
            return
        elif resp['status'] == 'failed':
            print("FAILED")
            return
            
        time.sleep(2)

if __name__ == "__main__":
    verify_default()
