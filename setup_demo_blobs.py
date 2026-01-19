import os
import json
import logging
from azure.storage.blob import BlobServiceClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_blobs():
    # Load settings
    settings_path = "local.settings.json"
    if not os.path.exists(settings_path):
        logger.error("local.settings.json not found.")
        return

    with open(settings_path, "r") as f:
        settings = json.load(f)
    
    # helper to get value
    conn_str = settings.get("Values", {}).get("DEPLOYMENT_STORAGE_CONNECTION_STRING")
    if not conn_str:
        conn_str = settings.get("Values", {}).get("AzureWebJobsStorage")
    
    if not conn_str:
        logger.error("No storage connection string found in local.settings.json")
        return

    container_name = "demo-invoices"
    
    try:
        service = BlobServiceClient.from_connection_string(conn_str)
        container = service.get_container_client(container_name)
        
        if not container.exists():
            container.create_container()
            logger.info(f"Created container: {container_name}")
        else:
            logger.info(f"Container exists: {container_name}")

        # Upload files
        mock_dir = "mock_data"
        if not os.path.exists(mock_dir):
            logger.error(f"Directory {mock_dir} does not exist.")
            return

        count = 0
        for filename in os.listdir(mock_dir):
            if filename.endswith(".txt"):
                blob_client = container.get_blob_client(filename)
                file_path = os.path.join(mock_dir, filename)
                with open(file_path, "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)
                count += 1
                if count % 10 == 0:
                    logger.info(f"Uploaded {count} files...")
        
        logger.info(f"Successfully uploaded {count} files to container '{container_name}'.")

    except Exception as e:
        logger.error(f"Error setting up blobs: {e}")

if __name__ == "__main__":
    setup_blobs()
