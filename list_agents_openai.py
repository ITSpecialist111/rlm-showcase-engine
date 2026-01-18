from azure.ai.agents import AgentsClient
from azure.core.credentials import AccessToken, TokenCredential
from datetime import datetime, timedelta
from pathlib import Path
import json

plain = Path('token.txt').read_text().strip()
class StaticToken(TokenCredential):
    def get_token(self, *scopes, **kwargs):
        return AccessToken(plain, int((datetime.utcnow()+timedelta(hours=1)).timestamp()))

endpoint = 'https://rlm-showcase-uksouth-resource.openai.azure.com/'
client = AgentsClient(endpoint, StaticToken())
agents = list(client.list_agents())
print(json.dumps([{'id': a.id, 'name': getattr(a, 'name', None), 'model': getattr(a, 'model', None)} for a in agents], indent=2))
