import csv
import os

from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools import tool, InjectedToolArg
from typing_extensions import Annotated


from .config import POLICY_DOCS_PATH, LOG_FILE_PATH
# from .security import is_authorized

import logging
logger = logging.getLogger('app.tools')


# in-memory vector store
# FIXME: this could be a bottle neck in the furuture if is grows.
_vector_store = None

def get_knowledge_base():
    """
    Initializes and returns the RAG knowledge base (vector store).
    Loads policy documents, splits them, embeds them, and stores them in FAISS.
    """
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434') # fallback for local dev
    embedding_model = "nomic-embed-text"

    logger.debug(f"Init KB: {POLICY_DOCS_PATH}")
    try:
        loader = DirectoryLoader(
            POLICY_DOCS_PATH,
            glob="**/*.md",
            loader_cls=UnstructuredMarkdownLoader
        )
        docs = loader.load()

        if not docs:
            logger.warning("warn: No documents found in policy directory.")
            return None

        # split md file into smaller chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)

        embeddings =OllamaEmbeddings(model=embedding_model,
                                     base_url=ollama_base_url)
        _vector_store = FAISS.from_documents(splits, embeddings)
        logger.info("KB init complete.")
        return _vector_store

    except Exception as e:
        logger.error("Error KB init failed: %s", e)
        return None

@tool
def security_policy_search(query: str) -> str:
    """
    searches the security policy and playbooks.
    """

    logger.debug("Tool: security_policy_search query: %s", query)
    db = get_knowledge_base()
    if db is None:
        return "Error: Knowledge base is not initialized."

    # similarity search
    try:
        docs = db.similarity_search(query, k=2) # top 2 relevant chunks
        if not docs:
            return "No relevant policy information found."

        # combine them use "\n---\n"
        return "\n---\n".join([doc.page_content for doc in docs])
    except Exception as e:
        logger.error(f"Error during policy search: {e}")
        return f"Error performing search: {e}"


@tool
# def query_security_logs(log_query: str, user_id: Annotated[str, InjectedToolArg()]) -> str:
def query_security_logs(log_query: str, user_id="anonymous") -> str:
    """
    Use this tool to find log entries.
    Security logs (security_logs.csv) for specific events.
    """

    logger.debug(f"Tool: Running query_security_logs with query: '{log_query}'")
    print('>>> query log userid', user_id)
    # if not is_authorized(user_id, "log_access"):
    #     logger.info(f"RBAC DENY: User {user_id} attempted unauthorized log access.")
    #     return "Access Denied: You do not have the required role to query security logs. Please contact the security team."

    # simulate "today" for the mock data
    # change this datetime today
    today_str = "2024-10-28"
    query_lower = log_query.lower()

    results = []
    try:
        with open(LOG_FILE_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                row_str = " ".join(row.values()).lower() # combine all fields for easy search
                match = False
                # treat today as an important keyword. make sure it handled.
                if "today" in query_lower and today_str not in row['timestamp']:
                    continue

                if any(keyword in row_str for keyword in query_lower.split() if keyword not in ["today", "show", "me"]):
                    match = True

                if match:
                    results.append(row)

        if not results:
            return f"No log entries found matching '{log_query}'."

        summary = f"Found {len(results)} log entries matching '{log_query}':\n"

        # max 10 results
        # format them in a specific mananer.
        for res in results[:10]:
            summary += f"- {res['timestamp']} | User: {res['user_id']} | Action: {res['action']} | Status: {res['status']} | IP: {res['ip_address']} | Details: {res['details']}\n"

        if len(results) > 10:
            summary += f"...and {len(results) - 10} more entries."

        return summary

    except FileNotFoundError:
        logger.error(f"Error: Log file not found at {LOG_FILE_PATH}")
        return "Error: The security log file could not be found."
    except Exception as e:
        logger.error(f"Error querying logs: {e}")
        return f"Error querying logs: {e}"

def get_all_tools():
    """Returns a list of all defined tools for the agent."""

    get_knowledge_base()
    return [security_policy_search, query_security_logs]

