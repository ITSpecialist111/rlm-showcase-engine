import requests
from pathlib import Path

token = Path('token_ai.txt').read_text().strip()
headers = { 'Authorization': f'Bearer {token}' }
for apiver in ['2024-02-15-preview','2024-03-01-preview','2024-05-01-preview']:
    url = f'https://rlm-showcase-uksouth-resource.services.ai.azure.com/api/projects/rlm-showcase-uksouth/agents?api-version={apiver}'
    resp = requests.get(url, headers=headers)
    print(apiver, resp.status_code)
    try:
        print(resp.json())
    except Exception:
        print(resp.text[:500])
