from azure.ai.agents import AgentsClient
from azure.core.credentials import AccessToken, TokenCredential
from datetime import datetime, timedelta
from pathlib import Path

plain = Path('token_ai.txt').read_text().strip()
class StaticToken(TokenCredential):
    def get_token(self, *scopes, **kwargs):
        return AccessToken(plain, int((datetime.utcnow()+timedelta(hours=1)).timestamp()))

endpoint = 'https://rlm-showcase-uksouth-resource.services.ai.azure.com/api/projects/rlm-showcase-uksouth'
client = AgentsClient(endpoint, StaticToken(), api_version='2024-12-01-preview')
try:
    agents = list(client.list_agents())
    print('Agents count:', len(agents))
    for a in agents:
        print(a)
except Exception as e:
    import traceback; traceback.print_exc()
