import requests
import time
import json
import sys

BASE_URL = "https://rlm-engine-uksouth.azurewebsites.net/api"
START_URL = f"{BASE_URL}/audit/start"
STATUS_URL = f"{BASE_URL}/audit/status"

def check_endpoint(name, method, url, payload=None, expected_code=200):
    print(f"\n--- Checking {name} ---")
    try:
        if method == "GET":
            resp = requests.get(url)
        else:
            resp = requests.post(url, json=payload)
        
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == expected_code:
            print("✅ Success")
            return resp
        else:
            print(f"❌ Failed. Response: {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def poll_job(job_id):
    print(f"Polling job {job_id}...")
    for _ in range(10): # Quick poll, max 20s
        resp = requests.get(f"{STATUS_URL}/{job_id}")
        if resp.status_code == 200:
            data = resp.json()
            status = data.get("status")
            msg = data.get("message")
            logs = data.get("logs_text", "")
            print(f"Status: {status} | Msg: {msg}")
            
            if "Downloading" in logs or "Connecting" in logs:
                 print("✅ Verified Blob Activity in logs")
                 return True
            
            if status in ["completed", "failed"]:
                return True
        time.sleep(2)
    return False

def run_tests():
    # 1. Basic Health (OpenAPI) - confirms app is serving
    check_endpoint("OpenAPI Spec (Health)", "GET", f"{BASE_URL}/openapi.json", expected_code=200)

    # 2. Trigger with Explicit Blob
    print("\n--- Triggering Audit (Explicit Blob) ---")
    payload_explicit = {"query": "Smoke Test Explicit", "blob_container": "demo-invoices"}
    resp = check_endpoint("Start Audit (Explicit)", "POST", START_URL, payload_explicit, expected_code=202)
    if resp:
        job_id = resp.json().get("job_id")
        poll_job(job_id)

    # 3. Trigger with Default Blob
    print("\n--- Triggering Audit (Default Blob) ---")
    payload_default = {"query": "Smoke Test Default"}
    resp = check_endpoint("Start Audit (Default)", "POST", START_URL, payload_default, expected_code=202)
    if resp:
        job_id = resp.json().get("job_id")
        poll_job(job_id)

if __name__ == "__main__":
    run_tests()
