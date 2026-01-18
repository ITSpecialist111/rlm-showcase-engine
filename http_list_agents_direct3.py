import requests
from pathlib import Path

token = Path('token_ai.txt').read_text().strip()
headers = { 'Authorization': f'Bearer {token}' }
url = 'https://agents.uksouth.hyena.infra.ai.azure.com/agents/v2.0/subscriptions/bfec7165-22d1-4917-89e7-efda8a9e85b4/resourceGroups/rg-rlm-showcase-uksouth/providers/Microsoft.MachineLearningServices/workspaces/rlm-showcase-uksouth-resource@rlm-showcase-uksouth@AML/agents?api-version=v2.0'
resp = requests.get(url, headers=headers)
print(resp.status_code)
print(resp.text[:1000])
