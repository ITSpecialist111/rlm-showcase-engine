from azure.ai.projects import AIProjectClient
from azure.core.credentials import AccessToken, TokenCredential
from datetime import datetime, timedelta
from pathlib import Path
import json

token_path = Path('token_ai.txt')
if not token_path.exists():
    raise SystemExit('token_ai.txt not found')
plain = token_path.read_text().strip()

class StaticToken(TokenCredential):
    def get_token(self, *scopes, **kwargs):
        return AccessToken(plain, int((datetime.utcnow()+timedelta(hours=1)).timestamp()))

endpoint = 'https://rlm-showcase-uksouth-resource.services.ai.azure.com/api/projects/rlm-showcase-uksouth'
client = AIProjectClient(endpoint, StaticToken())

agents = list(client.agents.list_agents())
print(json.dumps([{'id': a.id, 'name': getattr(a, 'name', None), 'model': getattr(a, 'model', None)} for a in agents], indent=2))
