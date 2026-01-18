"""
Configuration management for RLM Engine
"""
import os
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Azure Foundry Configuration
    FOUNDRY_ENDPOINT: str = "https://example.com"
    FOUNDRY_API_KEY: str = "dummy"
    AZURE_SUBSCRIPTION_ID: Optional[str] = None
    
    # Model Deployments
    ROOT_AGENT_DEPLOYMENT: str = "rlm-root-agent"
    SUB_AGENT_DEPLOYMENT: str = "rlm-analysis-agent"
    
    # RLM Engine Parameters
    MAX_TOKENS: int = 10000000
    CHUNK_SIZE: int = 100000
    MAX_ITERATIONS: int = 10
    TIMEOUT_SECONDS: int = 300
    
    # Infrastructure
    STORAGE_CONNECTION_STRING: Optional[str] = None
    TABLE_NAME: str = "rlm_audit_status"

    # Workspace
    WORKSPACE_ROOT: str = str(Path(__file__).resolve().parent)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra fields in .env

# Global settings instance
try:
    settings = Settings()
except Exception as e:
    # Fallback for when .env is missing or invalid in some environments
    print(f"Warning: Could not load settings from environment: {e}")
    # Create empty settings with some dummy values if needed, or let it fail later
    # For now, we rely on Pydantic validation to ensure required fields are present
    raise
