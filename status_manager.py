"""
Status Manager for RLM Audit Jobs
Handles tracking of async job progress, logging step updates, and storing final results.
"""
import uuid
import datetime
import json
import logging
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

try:
    from azure.data.tables import TableClient
    from azure.core.exceptions import ResourceExistsError, HttpResponseError
except ImportError:
    TableClient = None

# In a real Azure Function app, we might use azure.data.tables
# For this showcase portable implementation, we can use a class that *can* use Tables
# but defaults to in-memory or file-based for local simplicity if connection string is missing.

logger = logging.getLogger(__name__)

@dataclass
class JobStatus:
    job_id: str
    status: str  # "queued", "running", "completed", "failed"
    created_at: str
    updated_at: str
    progress_percent: int
    message: str
    logs: List[str]
    result: Optional[Dict[str, Any]] = None

try:
    from applicationinsights import TelemetryClient  # lightweight
except ImportError:  # pragma: no cover
    TelemetryClient = None


class StatusManager:
    def __init__(self, connection_string: Optional[str] = None, table_name: str = "rlmAuditStatus"):
        self.connection_string = connection_string
        self.table_name = table_name
        self._local_storage: Dict[str, JobStatus] = {}
        self.table_client = None

        if self.connection_string and TableClient:
            try:
                self.table_client = TableClient.from_connection_string(conn_str=self.connection_string, table_name=self.table_name)
                try:
                    self.table_client.create_table()
                except ResourceExistsError:
                    pass
                logger.info(f"StatusManager connected to Azure Table: {self.table_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Azure Table Client: {e}")
                self.table_client = None

        # Application Insights telemetry (optional)
        self._telemetry_client = self._init_telemetry_client()
        
    def create_job(self) -> str:
        """Create a new job and return its ID"""
        job_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow().isoformat()
        status = JobStatus(
            job_id=job_id,
            status="queued",
            created_at=now,
            updated_at=now,
            progress_percent=0,
            message="Job created",
            logs=["Job initialized"]
        )
        self._save_job(status)
        self._track("audit_job_created", job_id, status)
        return job_id

    def update_status(self, job_id: str, message: str, percent: Optional[int] = None, 
                      status_state: Optional[str] = None, result: Optional[Dict] = None):
        """Update the status of a job"""
        job = self._get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        now = datetime.datetime.utcnow().isoformat()
        job.updated_at = now
        job.message = message
        job.logs.append(f"[{now}] {message}")
        
        if percent is not None:
            job.progress_percent = percent
        
        if status_state:
            job.status = status_state
            
        if result:
            job.result = result

        self._save_job(job)
        self._track("audit_status_update", job_id, job)
        logger.info(f"Job {job_id} updated: {message} ({job.progress_percent}%)")

    def get_status(self, job_id: str) -> Optional[Dict]:
        """Get the full status of a job"""
        job = self._get_job(job_id)
        if job:
            return asdict(job)
        return None

    def _get_job(self, job_id: str) -> Optional[JobStatus]:
        if self.table_client:
            try:
                entity = self.table_client.get_entity(partition_key="audit_job", row_key=job_id)
                # Deserialize complex fields
                logs = json.loads(entity.get("logs", "[]"))
                result_json = entity.get("result", None)
                result = json.loads(result_json) if result_json else None
                
                return JobStatus(
                    job_id=entity["RowKey"],
                    status=entity["status"],
                    created_at=entity["created_at"],
                    updated_at=entity["updated_at"],
                    progress_percent=int(entity["progress_percent"]),
                    message=entity["message"],
                    logs=logs,
                    result=result
                )
            except Exception as e:
                # logger.debug(f"Job {job_id} not found in table: {e}")
                return None
        else:
            return self._local_storage.get(job_id)

    def _save_job(self, job: JobStatus):
        if self.table_client:
            try:
                # Serialize for Table Storage
                entity = {
                    "PartitionKey": "audit_job",
                    "RowKey": job.job_id,
                    "status": job.status,
                    "created_at": job.created_at,
                    "updated_at": job.updated_at,
                    "progress_percent": job.progress_percent,
                    "message": job.message,
                    "logs": json.dumps(job.logs),
                    "result": json.dumps(job.result) if job.result else None
                }
                self.table_client.upsert_entity(entity=entity)
            except Exception as e:
                logger.error(f"Failed to save job {job.job_id} to table: {e}")
                # Fallback to local
                self._local_storage[job.job_id] = job
        else:
            self._local_storage[job.job_id] = job

    # --- Telemetry helpers ---
    def _init_telemetry_client(self) -> Optional["TelemetryClient"]:
        if TelemetryClient is None:
            return None
        # Prefer instrumentation key if provided explicitly
        ikey = os.getenv("APPINSIGHTS_INSTRUMENTATIONKEY")
        if not ikey:
            conn_str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
            if conn_str and "InstrumentationKey=" in conn_str:
                ikey = conn_str.split("InstrumentationKey=")[-1].split(";")[0]
        if not ikey:
            return None
        try:
            return TelemetryClient(ikey)
        except Exception:
            return None

    def _track(self, event_name: str, job_id: str, job: JobStatus):
        if not self._telemetry_client:
            return
        try:
            props = {
                "job_id": job_id,
                "status": job.status,
                "progress": str(job.progress_percent),
                "message": job.message,
            }
            self._telemetry_client.track_event(event_name, props)
            # traces for easier querying
            self._telemetry_client.track_trace(f"{event_name}: {job_id} {job.status} {job.progress_percent}% {job.message}")
            self._telemetry_client.flush()
        except Exception:
            logger.debug("Telemetry tracking failed", exc_info=True)

# Global instance initialization
# Check DEPLOYMENT_STORAGE_CONNECTION_STRING first (preferred for app data), then AzureWebJobsStorage
conn_str = os.getenv("DEPLOYMENT_STORAGE_CONNECTION_STRING") or os.getenv("AzureWebJobsStorage")
status_manager = StatusManager(connection_string=conn_str)
