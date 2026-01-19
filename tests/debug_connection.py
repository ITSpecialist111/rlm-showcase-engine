import os
import asyncio
from openai import AsyncAzureOpenAI

ENDPOINT = "https://rlm-showcase-uksouth-resource.openai.azure.com/"
KEY = "REDACTED_FOUNDRY_KEY"
DEPLOYMENT = "gpt-5.1-chat" # from config default

async def test_conn():
    print(f"Testing connection to: {ENDPOINT}")
    client = AsyncAzureOpenAI(
        api_key=KEY,
        api_version="2024-02-15-preview",
        azure_endpoint=ENDPOINT
    )
    
    try:
        response = await client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[{"role": "user", "content": "Hello"}],
            max_completion_tokens=10
        )
        print("Success!")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_conn())
