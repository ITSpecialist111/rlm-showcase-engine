import requests
from pathlib import Path

token = Path('token_ai.txt').read_text().strip()
headers = { 'Authorization': f'Bearer {token}' }
base = 'https://agents.uksouth.hyena.infra.ai.azure.com/agents/v2.0/subscriptions/bfec7165-22d1-4917-89e7-efda8a9e85b4/resourceGroups/rg-rlm-showcase-uksouth/providers/Microsoft.MachineLearningServices/workspaces/rlm-showcase-uksouth-resource@rlm-showcase-uksouth@AML/agents'
for apiver in ['2024-10-01-preview','2024-08-01-preview','2024-06-01-preview','2024-04-01-preview']:
    url = f'{base}?api-version={apiver}'
    resp = requests.get(url, headers=headers)
    print(apiver, resp.status_code)
    try:
        print(resp.json())
    except Exception:
        print(resp.text[:400])
