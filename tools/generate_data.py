import os
import random
from datetime import datetime, timedelta
import asyncio
from azure.storage.blob.aio import BlobServiceClient
from dotenv import load_dotenv

# Config
COUNT = 2000
CONTAINER_NAME = "demo-invoices"
policy_limit = 1000

# Mock Data
categories = ["Travel", "Meals", "Lodging", "Software", "Office Supplies"]
vendors = ["Uber", "Delta", "Hilton", "AWS", "Staples", "WeWork", "Starbucks"]
locations = ["London", "New York", "Seattle", "Remote", "Tokyo"]

def generate_invoice(i):
    """Generate a single invoice content."""
    date = datetime.now() - timedelta(days=random.randint(0, 365))
    category = random.choice(categories)
    vendor = random.choice(vendors)
    
    # 5% chance of violation
    if random.random() < 0.05:
        amount = random.randint(1001, 5000)
        status = "VIOLATION"
    else:
        amount = random.randint(10, 999)
        status = "COMPLIANT"
        
    filename = f"Invoice_{i:04d}_{vendor}_{status}.txt"
    content = f"""INVOICE #{i:04d}
Date: {date.strftime('%Y-%m-%d')}
Vendor: {vendor}
Category: {category}
Location: {random.choice(locations)}
Amount: ${amount}.00
Description: Standard business expense for {category}.
"""
    return filename, content

async def upload_blobs(conn_str):
    service_client = BlobServiceClient.from_connection_string(conn_str)
    
    try:
        container_client = service_client.get_container_client(CONTAINER_NAME)
        # Create if not exists
        if not await container_client.exists():
            await container_client.create_container()
            print(f"Created container: {CONTAINER_NAME}")
        
        print(f"Generating and uploading {COUNT} invoices to '{CONTAINER_NAME}'...")
        
        # Determine upload batch size
        tasks = []
        for i in range(COUNT):
            filename, content = generate_invoice(i)
            blob_client = container_client.get_blob_client(filename)
            tasks.append(blob_client.upload_blob(content, overwrite=True))
            
            if len(tasks) >= 50:
                await asyncio.gather(*tasks)
                print(f"Uploaded batch ending {i}")
                tasks = []
        
        if tasks:
            await asyncio.gather(*tasks)
            
        print("Upload complete!")
        
    finally:
        await service_client.close()

if __name__ == "__main__":
    # Load connection string from env or hardcoded (for this script execution)
    conn_str = os.environ.get("AzureWebJobsStorage")
    if not conn_str:
        # Fallback to loading from local.settings.json manually if running isolated
        import json
        try:
            # Try current directory first (if running from root)
            path = 'local.settings.json'
            if not os.path.exists(path):
                # Try parent (if running from tools/)
                path = '../local.settings.json'
                
            with open(path) as f:
                settings = json.load(f)
                conn_str = settings['Values']['AzureWebJobsStorage']
        except Exception as e:
            print(f"Error loading settings: {e}")
            exit(1)
            
    asyncio.run(upload_blobs(conn_str))
