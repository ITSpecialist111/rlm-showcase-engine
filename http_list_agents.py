import requests
from pathlib import Path

token = Path('token_ai.txt').read_text().strip()
endpoint = 'https://rlm-showcase-uksouth-resource.services.ai.azure.com/api/projects/rlm-showcase-uksouth/agents?api-version=v1'
headers = { 'Authorization': f'Bearer {token}' }
resp = requests.get(endpoint, headers=headers)
print(resp.status_code)
print(resp.text[:1000])
