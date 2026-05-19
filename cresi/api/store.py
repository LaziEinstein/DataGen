"""
In-process job store. Replace with Redis-backed store for multi-worker deployments.
"""
from typing import Any, Dict

job_store: Dict[str, Any] = {}
