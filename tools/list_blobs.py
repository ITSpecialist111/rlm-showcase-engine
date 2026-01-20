import os
import sys
from azure.storage.blob import BlobServiceClient

# Connection string from local.settings.json (hardcoded for this script for ease, but normally would load from env)
CONN_STR = "DefaultEndpointsProtocol=https;AccountName=rgrlmshowcaseuksout80ac;AccountKey=REDACTED_STORAGE_KEY;EndpointSuffix=core.windows.net"
CONTAINER = "demo-invoices"

def list_blobs():
    print(f"Connecting to container '{CONTAINER}'...")
    try:
        blob_service_client = BlobServiceClient.from_connection_string(CONN_STR)
        container_client = blob_service_client.get_container_client(CONTAINER)
        
        blobs = list(container_client.list_blobs())
        print(f"Total Blobs Found: {len(blobs)}")
        
        print("\n--- First 20 Invoices ---")
        for blob in blobs[:20]:
            print(f"- {blob.name} ({blob.size} bytes)")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_blobs()
