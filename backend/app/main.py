import os
import traceback
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our new agent creator and the old tool initializer
from .tools import get_knowledge_base
from .agent import create_security_agent
# from .security import is_injection_attempt, log_audit_event, AUDIT_LOG_STORE, AuditLogEntry
from typing import List

import logging
logger = logging.getLogger('app.main')
logging.basicConfig(level=logging.INFO)

load_dotenv()

if os.getenv("OPENAI_API_KEY") is None:
    logger.warning("Warning: OPENAI_API_KEY environment variable not set.")

# future work: add user auth, rate limiting, logging, etc.
# chat history management can be added later.
class ChatRequest(BaseModel):
    query: str
    user_id: str | None = None


class ChatResponse(BaseModel):
    response: str


# --- FastAPI App Initialization ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # start
    logger.info("Server starting...")
    logger.info("Initializing RAG knowledge base...")
    get_knowledge_base()
    logger.info("Knowledge base initialized.")

    logger.info("Creating AI agent...")
    agent_executor = create_security_agent()

    app.state.agent_executor = agent_executor
    logger.info("AI agent created and ready.")

    yield

    # down
    logger.info("Server shutting down...")

app = FastAPI(
    title="EOS Security Incident Knowledge Assistant",
    description="An AI assistant for security policies and incident response.",
    version="0.0.1",
    lifespan=lifespan
)

# FIXME: port 5173 is for dev. must be removed for production
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",

    # production: docker maps 3000
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---
@app.get("/")
def get_root():
    return {"status": "Server is running..."}

@app.post("/api/chat", response_model=ChatResponse)
async def handle_chat(request: Request, chat_request: ChatRequest):
    """
    chat endpoint.
    this endpoint now uses the LangChain agent to process the query.
    """
    logger.debug(f"Received query from user '{chat_request.user_id}': {chat_request.query}")
    user_id = chat_request.user_id or "anonymous"
    query = chat_request.query
    print('>>> ', user_id, query)
    # any user try to inject forbiden proompts, reject and log it
    # if is_injection_attempt(chat_request.query):
    #     # log_audit_event(user_id, query, "InjectionBlocked", {"System": "Rejected due to PI keywords."}, "Rejected")
    #     return ChatResponse(response="Sorry... I am not able to process your request.")

    # log_id = log_audit_event(user_id, "QueryReceived", query, {"System": "Processing started."}, 'Received')
    agent_executor = request.app.state.agent_executor
    try:
        # CORE AGENTIC CALL
        # invoke the agent with the user's input.
        # The agent will decide which tools to call, run them,
        # and generate a final response.
        response = await agent_executor.ainvoke({
            "input": chat_request.query,
            "user_id": user_id
            # "chat_history": [] # We can add chat history here later
        })

        ai_response = response.get("output", "Sorry, I encountered an error.")
        # log_audit_event(user_id, query, "QueryCompleted", {"Agent": ai_response}, log_id)
        return ChatResponse(response=ai_response)

    except Exception as e:
        # log the full, detailed error on the server side for debugging
        logger.error(f"!!! Error during agent invocation: {e}")

        ### enable this for dev. print the error on the console.
        # traceback.print_exc()
        #######################

        # log_audit_event(user_id, "QueryFailed", query, "Agent", f"Execution failed: {e}", log_id)

        # a generic, user-friendly message for the frontend
        user_friendly_error = "Sorry, I encountered an issue processing your request. Please try rephrasing or asking something else."
        return ChatResponse(response=user_friendly_error)

# @app.get("/api/audit-logs", response_model=List[AuditLogEntry])
# def get_audit_logs():
#     """Returns the list of in-memory audit logs for review."""
#     return AUDIT_LOG_STORE

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
