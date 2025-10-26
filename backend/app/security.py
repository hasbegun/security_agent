import os
import uuid
import datetime
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

import logging
logger = logging.getLogger('app.securyt')

# pydantic model defining the structure of every log entry
class AuditLogEntry(BaseModel):
    timestamp: str
    audit_id: str
    user_id: str
    query: str
    action: str
    details: Dict[str, Any]
    status: str

### can improve... no time...
# class AuditLogEntry(BaseModel):
#     """Schema for a single audit log entry."""
#     log_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
#     timestamp: float = Field(default_factory=time.time)
#     user_id: str
#     event_type: str # e.g., QueryReceived, ToolCalled, InjectionBlocked, QueryCompleted
#     input_query: str
#     source: str # e.g., System, Agent, query_security_logs
#     details: str
#     session_id: Optional[str] = None # Optional: Use for correlating multi-turn chats
##############################


# In-memory store for audit logs (SPOF)
AUDIT_LOG_STORE: List[AuditLogEntry] = []

def log_audit_event(user_id: str, query: str, action: str, details: Dict[str, Any], status: str) -> str:
    """Creates a structured audit log entry and stores it."""
    log_id = str(uuid.uuid4())
    entry = AuditLogEntry(
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        audit_id=log_id,
        user_id=user_id,
        query=query,
        action=action,
        details=details,
        status=status
    )
    AUDIT_LOG_STORE.append(entry)
    # Print to console for immediate visibility in prototype
    logger.info(f"[AUDIT LOG {status}] ID: {log_id[:8]} | User: {user_id} | Action: {action}")
    return log_id

def get_audit_log_store():
    """Retrieves the full log store."""
    return AUDIT_LOG_STORE


# IPROMPT INJECTION DEFENSE (HEURISTICS)
# FIMXME: we can do better here
INJECTION_KEYWORDS = [
    "ignore all previous",
    "forget everything",
    "act as a hacker",
    "system prompt",
    "print the source code",
    "developer mode",
]

# Commands/targets that should never be revealed or executed
INJECTION_BLOCKLIST = [
    "delete file",
    "modify data",
    "reveal key",
    "sql injection",
    "shell access",
    "bypass security",
]

def is_injection_attempt(query: str) -> bool:
    """
    Checks the user query against a heuristic blocklist for common
    prompt injection patterns.
    """
    query_lower = query.lower()
    if any(keyword in query_lower for keyword in INJECTION_KEYWORDS):
        return True

    if any(forbidden in query_lower for forbidden in INJECTION_BLOCKLIST):
        return True

    return False

# ROLE-BASED ACCESS CONTROL (RBAC SIMULATION)
# FIXME: We can do better here...

def is_authorized(user_id: str, required_role: str) -> bool:
    """
    Simulates checking user roles against required permissions.
    In a production system, this would query an identity provider.
    """
    if required_role == "log_access":
        return user_id == "security_admin"

    return True
