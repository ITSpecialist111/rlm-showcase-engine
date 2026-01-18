import requests
from pathlib import Path

token = Path('token_ai.txt').read_text().strip()
headers = { 'Authorization': f'Bearer {token}' }
for apiver in ['2024-10-21','2024-10-01','2024-10-01-preview','2024-09-01-preview','2024-07-01-preview','2024-06-01-preview']:
    url = f'https://rlm-showcase-uksouth-resource.services.ai.azure.com/agents?api-version={apiver}'
    resp = requests.get(url, headers=headers)
    print(apiver, resp.status_code)
    try:
        print(resp.json())
    except Exception:
        print(resp.text[:400])
