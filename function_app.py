import azure.functions as func
import logging
import json
import asyncio
import os
from datetime import datetime
# from azure.storage.blob import BlobServiceClient (Moved to lazy async import)

# Import local modules
from rlm_engine import create_rlm_engine, RLMConfig
from config import settings
from status_manager import status_manager

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="openapi.json", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def serve_openapi(req: func.HttpRequest) -> func.HttpResponse:
    """Serve the OpenAPI specification for custom connectors."""
    try:
        root_dir = os.path.dirname(__file__)
        candidates = [
            os.path.join(root_dir, "openapi.json"),
            os.path.join(root_dir, "copilot", "openapi.json"),
        ]
        for path in candidates:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return func.HttpResponse(f.read(), mimetype="application/json")
        return func.HttpResponse(
            json.dumps({"error": "openapi.json not found"}),
            status_code=404,
            mimetype="application/json",
        )
    except Exception as e:
        logging.error(f"Error serving openapi.json: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )

@app.route(route="audit/start", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
async def start_audit(req: func.HttpRequest) -> func.HttpResponse:
    """
    Start an audit job.
    Expected Body: {"query": "...", "documents": ["..."], "blob_url": "..."}
    """
    logging.info('Received start_audit request.')

    try:
        req_body = req.get_json()
        query = req_body.get('query')
        scenario = req_body.get('scenario', 'invoice_audit') # 'invoice_audit' or 'code_audit'
        documents = req_body.get('documents', []) # List of strings
        blob_container = req_body.get('blob_container', 'demo-invoices') # HARDCODED DEFAULT for Demo
        blob_prefix = req_body.get('blob_prefix', None) # Optional: Filter blobs by prefix
        
        if not query:
            query = "Full policy compliance audit"
            logging.info("No query provided; defaulting to 'Full policy compliance audit'")

        # Heuristic: Auto-detect scenario if not explicitly provided or if query strongly suggests code audit
        if "code audit" in query.lower() or "class " in query or "def " in query:
             logging.info(f"Auto-detecting 'code_audit' scenario from query: {query}")
             scenario = "code_audit"
        
        # Create Job ID
        job_id = status_manager.create_job()
        
        # Start processing in background
        # In Azure Functions Python V2, we can use asyncio.create_task for "fire and forget" 
        # within the limits of function timeout, OR better, use a queue-based trigger.
        # For this showcase, we will simluation 'background' by launching the task 
        # but returning immediately. Note: In Consumption plan, this is risky if function sleeps.
        # Ideally this pushes to a queue. For the demo, we'll try asyncio.create_task and hope 
        # the execution environment stays alive long enough for the demo (or use Premium plan).
        
        # BETTER APPROACH FOR DEMO: 
        # Just return the ID and let the client know it's queued. 
        # We actually need to Trigger the execution. 
        # Since we can't easily spawn a detached background thread that survives request completion reliably in serverless
        # without Durable Functions, we will execute the logic in a separate "task" but we might need
        # to wait for it if we don't have Durable. 
        # However, the requirement is "Azure returns a Job_ID immediately".
        # We will use the 'Process in background' pattern which works okay for short demos/dev.
        
        asyncio.create_task(run_audit_task(job_id, query, documents, scenario, blob_container, blob_prefix))

        return func.HttpResponse(
            json.dumps({
                "job_id": job_id,
                "status": "queued",
                "message": "Audit started. Poll /api/audit/status/{job_id} for updates."
            }),
            status_code=202,
            mimetype="application/json"
        )

    except ValueError:
        return func.HttpResponse(
             json.dumps({"error": "Invalid JSON"}),
             status_code=400,
             mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error starting audit: {str(e)}")
        return func.HttpResponse(
             json.dumps({"error": str(e)}),
             status_code=500,
             mimetype="application/json"
        )

@app.route(route="audit/status/{job_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def get_status(req: func.HttpRequest) -> func.HttpResponse:
    """Get the status of a specific job"""
    job_id = req.route_params.get('job_id')
    status = status_manager.get_status(job_id)
    
    if not status:
        return func.HttpResponse(
            json.dumps({"error": "Job not found"}),
            status_code=404,
            mimetype="application/json"
        )

    # Convenience: join logs for display in Adaptive Cards / connectors
    if isinstance(status, dict):
        # Convenience: join logs for display in Adaptive Cards / connectors
        if "logs" in status and "logs_text" not in status:
            try:
                status["logs_text"] = "\n".join(status.get("logs", []))
            except Exception:
                status["logs_text"] = ""

        # Lift common fields for easier connector bindings
        result_obj = status.get("result")
        if isinstance(result_obj, dict):
            status.setdefault("summary", result_obj.get("summary"))
            status.setdefault("details", result_obj.get("details"))

    return func.HttpResponse(
        json.dumps(status),
        status_code=200,
        mimetype="application/json"
    )

async def run_audit_task(job_id: str, query: str, documents: list, scenario: str = "invoice_audit", blob_container: str = None, blob_prefix: str = None):
    """
    Background task to run the RLM engine.
    """
    try:
        logging.info(f"Starting background task for job {job_id} (Scenario: {scenario})")
        status_manager.update_status(job_id, f"Initializing RLM Engine ({settings.FOUNDRY_ENDPOINT})...", 10, "running")
        
        logging.info(f"Initializing RLM Config with Endpoint: {settings.FOUNDRY_ENDPOINT}")
        logging.info(f"Initializing RLM Config with API Key: {'*' * 4 if settings.FOUNDRY_API_KEY else 'NONE'}")
        config = RLMConfig(
            foundry_endpoint=settings.FOUNDRY_ENDPOINT,
            api_key=settings.FOUNDRY_API_KEY,
            deployment=settings.ROOT_AGENT_DEPLOYMENT
        )
        engine = create_rlm_engine(config)
        
        # Define progress callback
        async def progress_reporter(msg: str):
            # Calculate rough percentage based on message content or just increment
            # This is a heuristic for the demo
            current_log = status_manager.get_status(job_id)
            current_pct = current_log['progress_percent'] if current_log else 10
             
            new_pct = min(95, current_pct + 5)
            if "Scanning Invoice" in msg:
                 # Parse number if possible, or just bump
                 pass
            
            status_manager.update_status(job_id, msg, new_pct)
        
        # Execute
        status_manager.update_status(job_id, f"Starting analysis ({scenario})...", 20)

        # Route by scenario
        if scenario == "code_audit":
            # Determine correct root: use setting if valid dir, else CWD (safer for local/flex hybrid)
            config_root = getattr(settings, "WORKSPACE_ROOT", ".")
            if os.path.exists(config_root):
                 repo_root = config_root
            else:
                 repo_root = os.getcwd()

            status_manager.update_status(job_id, f"Running code audit in repo: {repo_root}", 25)
            
            async def code_progress(msg, pct=None):
                status_manager.update_status(job_id, msg, pct)
                
            results = await engine.run_code_audit(query, repo_root=repo_root, progress_cb=code_progress)
            
            status_manager.update_status(job_id, "Code Audit Complete", 100, "completed", result={
                "summary": f"Found {len(results)} matches",
                "matches": results,
            })
            return
        else:
            # Blob Integration (ASYNC)
            if blob_container:
                try:
                    status_manager.update_status(job_id, f"Connecting to Blob Container: {blob_container}...", 15)
                    # Use AzureWebJobsStorage or generic connection string
                    conn_str = os.environ.get("AzureWebJobsStorage")
                    if not conn_str:
                         raise ValueError("AzureWebJobsStorage connection string not found.")
                    
                    # Async Client Context Manager
                    from azure.storage.blob.aio import BlobServiceClient
                    async with BlobServiceClient.from_connection_string(conn_str) as blob_service_client:
                        container_client = blob_service_client.get_container_client(blob_container)
                        
                        # Async list blobs
                        downloaded_count = 0
                        async for blob in container_client.list_blobs(name_starts_with=blob_prefix):
                            if downloaded_count >= 2500: # Limit for demo
                                 break
                            
                            # Simple progress sampling (don't log every single file to save I/O)
                            if downloaded_count % 50 == 0:
                                status_manager.update_status(job_id, f"Downloading {blob.name}...", 15)
                            
                            blob_client = container_client.get_blob_client(blob.name)
                            blob_data = await blob_client.download_blob()
                            content = await blob_data.readall()
                            
                            # Attempt to decode text
                            try:
                                text_content = content.decode('utf-8')
                                documents.append(f"--- {blob.name} ---\n{text_content}")
                                downloaded_count += 1
                            except UnicodeDecodeError:
                                logging.warning(f"Skipping binary file: {blob.name}")
                                
                        status_manager.update_status(job_id, f"Downloaded {downloaded_count} documents from Blob Storage.", 20)
                    
                except Exception as e:
                     logging.error(f"Blob download failed: {e}")
                     status_manager.update_status(job_id, f"Warning: Blob download failed ({str(e)}). Using available docs.", 20)

            # If documents are still empty (and no blob success), use mocks
            if not documents:
                 # Load default/mock docs for Compliance Demo
                 status_manager.update_status(job_id, "No documents provided, using mock context...", 25)
                 documents = ["Invoice 001: $500", "Invoice 002: $200", "Policy: Max travel $1000"]

            response = await engine.process_query(query, documents, progress_callback=progress_reporter)
        
        if response.status == "error":
            status_manager.update_status(job_id, f"Failed: {response.result}", 0, "failed")
        else:
            status_manager.update_status(job_id, "Audit Complete", 100, "completed", result={
                "summary": response.result,
                "reasoning": response.reasoning_steps
            })
            
    except Exception as e:
        logging.error(f"Background task failed: {str(e)}")
        status_manager.update_status(job_id, f"System Error: {str(e)}", 0, "failed")
