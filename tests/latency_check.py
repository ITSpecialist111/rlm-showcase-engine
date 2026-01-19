import requests
import time

URL = "https://rlm-engine-uksouth.azurewebsites.net/api/audit/start"
PAYLOAD = {"query": "Latency Check"}

def check_latency():
    print("Checking /audit/start latency...")
    
    # 1. First Call (may be cold)
    start = time.time()
    try:
        resp = requests.post(URL, json=PAYLOAD, timeout=60)
        duration = time.time() - start
        print(f"Call 1 (Potential Cold): {duration:.2f}s | Status: {resp.status_code}")
    except Exception as e:
        print(f"Call 1 Failed: {e}")

    # 2. Second Call (Warm)
    time.sleep(1)
    start = time.time()
    try:
        resp = requests.post(URL, json=PAYLOAD, timeout=60)
        duration = time.time() - start
        print(f"Call 2 (Warm):          {duration:.2f}s | Status: {resp.status_code}")
    except Exception as e:
        print(f"Call 2 Failed: {e}")
        
    # 3. Health Check (Get)
    try:
        start = time.time()
        resp = requests.get("https://rlm-engine-uksouth.azurewebsites.net/api/openapi.json", timeout=10)
        duration = time.time() - start
        print(f"Health Check (Warm):     {duration:.2f}s | Status: {resp.status_code}")
    except Exception as e:
        print(f"Health Check Failed: {e}")

if __name__ == "__main__":
    check_latency()
