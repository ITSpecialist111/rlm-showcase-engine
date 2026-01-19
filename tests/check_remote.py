import requests
import time
import json
import sys

# BASE_URL = "http://127.0.0.1:7072"
BASE_URL = "https://rlm-engine-uksouth.azurewebsites.net"

def test_remote_deployment():
    print(f"Testing Remote Deployment at: {BASE_URL}")

    # 1. Check OpenAPI (Public endpoint)
    try:
        r = requests.get(f"{BASE_URL}/api/openapi.json")
        if r.status_code == 200:
            print("SUCCESS: /api/openapi.json is accessible.")
        else:
            print(f"FAILED: /api/openapi.json returned {r.status_code}")
            return
    except Exception as e:
        print(f"FAILED: Could not connect to {BASE_URL}: {e}")
        return

    # 2. Run Audit (Compliance Scenario)
    start_url = f"{BASE_URL}/api/audit/start"
    print(f"POST {start_url} (Compliance Scenario)")
    
    payload = {
        "query": "Check for travel policy violations", 
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
    
    for i in range(30): 
        try:
            resp = requests.get(status_url)
            data = resp.json()
            status = data.get("status")
            pct = data.get("progress_percent")
            msg = data.get("message")
            
            print(f"[{i}] Status: {status} ({pct}%) - {msg}")
            
            if status == "completed":
                print("Remote Audit Complete")
                # print(json.dumps(data, indent=2))
                break
            elif status == "failed":
                print("Remote Audit Failed")
                print(json.dumps(data, indent=2))
                break
                
            time.sleep(2)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    test_remote_deployment()
