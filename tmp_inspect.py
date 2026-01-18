from azure.ai.projects import AIProjectClient
from azure.core.credentials import AccessToken, TokenCredential
from datetime import datetime, timedelta

class SC(TokenCredential):
    def __init__(self, t): self.t = t
    def get_token(self, *scopes, **kwargs):
        return AccessToken(self.t, int((datetime.utcnow()+timedelta(hours=1)).timestamp()))

client = AIProjectClient('http://example.com', SC('x'))
print(client.agents)
print(dir(client.agents))
