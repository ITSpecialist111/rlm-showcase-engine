import azure.functions as func
import logging
import json
import asyncio
import os
from datetime import datetime

# Import local modules
from rlm_engine import create_rlm_engine, RLMConfig
from config import settings
from status_manager import status_manager

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="audit/start", methods=["POST"])
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
        documents = req_body.get('documents', []) # For now, simple list. Later, blob support.
        
        if not query:
            return func.HttpResponse(
                json.dumps({"error": "Please pass a query in the request body"}),
                status_code=400,
                mimetype="application/json"
            )

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
        
        asyncio.create_task(run_audit_task(job_id, query, documents, scenario))

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

@app.route(route="audit/status/{job_id}", methods=["GET"])
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

    return func.HttpResponse(
        json.dumps(status),
        status_code=200,
        mimetype="application/json"
    )

async def run_audit_task(job_id: str, query: str, documents: list, scenario: str = "invoice_audit"):
    """
    Background task to run the RLM engine.
    """
    try:
        logging.info(f"Starting background task for job {job_id} (Scenario: {scenario})")
        status_manager.update_status(job_id, "Initializing RLM Engine...", 10, "running")
        
        # Initialize Engine
        config = RLMConfig(
            foundry_endpoint=settings.FOUNDRY_ENDPOINT,
            api_key=settings.FOUNDRY_API_KEY,
            root_agent_deployment=settings.ROOT_AGENT_DEPLOYMENT,
            sub_agent_deployment=settings.SUB_AGENT_DEPLOYMENT
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
            repo_root = getattr(settings, "WORKSPACE_ROOT", os.getcwd())
            status_manager.update_status(job_id, f"Running code audit in repo: {repo_root}", 25)
            results = await engine.run_code_audit(query, repo_root=repo_root, progress_cb=lambda msg, pct=None: status_manager.update_status(job_id, msg, pct or None))
            status_manager.update_status(job_id, "Code Audit Complete", 100, "completed", result={
                "summary": f"Found {len(results)} matches",
                "matches": results,
            })
            return
        else:
            # If documents are empty, we might want to throw error or load from blob
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
                "details": response.sub_agent_results,
                "reasoning": response.reasoning_steps
            })
            
    except Exception as e:
        logging.error(f"Background task failed: {str(e)}")
        status_manager.update_status(job_id, f"System Error: {str(e)}", 0, "failed")
