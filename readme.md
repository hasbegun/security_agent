# Security-agent Security Incident Knowledge Assistant

## I. Project Overview

This full-stack application combines a conversational AI assistant (Agentic AI) with Retrieval-Augmented Generation (RAG) to provide quick, accurate responses regarding enterprise security policies and incident logs.

**Technology Stack:**

* Backend: Python, FastAPI, LangChain (Agent Executor)

* Frontend: React, Vite (served via Nginx in deployment)

* AI Backend: Ollama (Qwen2.5-Coder for reasoning, Nomic-Embed-Text for RAG)

* Orchestration: Docker, Docker Compose, Makefile

## II. System Requirements

Successful operation requires the following software to be installed on the host machine, as the LLM utilizes local GPU resources.

### 1. Large Language Model Service (Ollama)

The system relies on an Ollama instance accessible via `http://host.docker.internal:11434`.

| Component | Version | Purpose |
| ----- | ----- | ----- |
| **Ollama** | v0.12.3+ | Required to run local models. [Ollama Download](https://ollama.com/download) |
| **Qwen2.5-Coder** | 32B | Conversational AI and agentic reasoning (Tool Calling). |
| **Nomic-Embed-Text** | Latest | Embedding model for RAG and vector search (Policy Knowledge Base). |

**Installation Commands (Host Machine):**
Install Ollama if not already done (Download from link above)
  ```
  ollama serve
  ollama pull qwen2.5-coder:32b
  ollama pull nomic-embed-text
  ```
### 2. Containerization (Docker)

Docker and Docker Compose are essential for building and orchestrating the backend and frontend services. [Docker Installation Guide](https://docs.docker.com/engine/install/)

## III. Deployment and Controls (Recommended Method)

The project utilizes Docker Compose and a `Makefile` to manage the full environment, including network configuration necessary to connect the containers to the host-based Ollama service.

### A. Setup and Execution

1. **Start Ollama Server:**
   Before starting Docker, initiate the Ollama service on the host machine:
   ```
   ollama serve
   ```

2. **Start the Application:**
  Navigate to the project root directory and execute the primary build and start command:
    ```
    make up
    ```

### B. Command Reference (Makefile)

| Command | Function | Description |
| ----- | ----- | ----- |
| `make help` | Displays all available commands. | Self-explanatory reference. |
| `make up` | `docker compose up --build -d` | **Builds images** (if required) and starts all services (backend:8000, frontend:3000) in detached mode. |
| `make build` | `docker compose build` | Forces the rebuild of all service images. |
| `make down` | `docker compose down` | Stops and removes containers and networks. |
| `make logs` | `docker compose logs -f` | Streams consolidated logs from all services. |
| `make logs-backend` | `docker compose logs -f backend` | Streams logs specifically for the FastAPI backend. |
| `make logs-frontend` | `docker compose logs -f frontend` | Streams logs specifically for the Nginx/React frontend. |

### C. Access

The live application is accessible at: `http://localhost:3000`

## IV. Local Development Environment (Alternative Method)

For making quick code changes without rebuilding Docker containers, developers may run the backend and frontend services directly on the host machine.

### A. Backend Setup (Python)

1. **Python Environment:** Use Python 3.13+
    ```
    # Create and activate environment
    python3 -m venv venv
    source venv/bin/activate
    # OR conda environment setup:
    # conda create security-agent-dev python=3.13
    # conda activate security-agent-dev
    ```

2. **Dependencies:**
    ```
    pip install -r requirements.txt
    ```
3. **Execution:**
    ```
    python app/main.py
    ```

4. **Test**
    ```
    cd backend/test
    pytest
   ```
### B. Frontend Setup (React/Vite)

1. **Node/NPM:** [NPM Installation Instructions](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)
2. **Project Initialization:**
(Only required if the `frontend` directory does not exist)
    ```
    npm create vite@latest frontend -- --template react
    ```
3. **Dependencies and Execution:**
Navigate into the `frontend` directory and install dependencies:
    ```
    cd frontend
    npm install
    npm run dev
    ```
4. **Access:** The frontend is typically available at `http://localhost:5173`.


# Conncerns and future works.

## Single Points of Failure (SPOFs) and Performance Analysis

### 1. Single Points of Failure (SPOFs)
| Component | Failure Point | Impact | Mitigation Strategy |
| ----- | ----- | ----- | ----- |
| Ollama Host Service | Ollama is running on the host machine. If the host service crashes, stops, or is unreachable from the Docker network. | Total System Failure. The backend cannot initialize the RAG vector store or process any queries, leading to httpx.ConnectError and inability to start the agent. | Monitoring & Resilience: Implement an external health check or monitoring service that alerts if Ollama is down. In the future, redeploy Ollama into a dedicated container with guaranteed CPU/GPU resources and robust restart policies. |
| RAG Initialization	| Failure during get_knowledge_base() startup (e.g., policy files missing, embedding model not found/downloaded).	| Backend Startup Failure. The lifespan handler crashes, and the FastAPI service never becomes ready, preventing the entire application from starting.	| Pre-flight Checks & Graceful Degradation: Use a dedicated pre-flight check in the Docker entrypoint. Modify get_knowledge_base to not crash the server on failure, but instead return a dummy or error state, allowing the API to respond with "Service degraded: KB unavailable."|
|Hardcoded Tool Prompt (hwchase17/react)	| If the structure of the prompt pulled from the LangChain Hub changes, or if the Hub itself is down during initial setup or a redeploy.	| Agent Instantiation Failure. The hub.pull call fails, or the subsequent prompt.partial fails due to missing variables, preventing the agent from being created.	|Caching & Redundancy: Store a local copy of the hwchase17/react template within the backend/app directory (as a .txt file) and modify the agent code to use the local file as a fallback if the hub.pull fails.|


### 2. Performance Bottlenecks
| Area | Bottleneck Point | Impact on Latency | Mitigation Strategy |
| ----- | ----- | ----- | ----- |
| LLM Inference | Qwen2.5-Coder:32B is a large model running on the host, consuming significant GPU/CPU time for every single query. | High Latency (P99). Queries requiring the agent (most queries) will wait for the model's full thought/action loop. | Model Optimization: Use a smaller, tool-call-fine-tuned model (e.g., Llama 3.1 8B Instruct if available, or a highly quantized Qwen). Implement streaming responses in the backend to provide immediate feedback to the user.|
| RAG Embedding Speed | Ollama Embeddings (nomic-embed-text) are used during KB initialization. While the search is fast, if the documents were much larger, the initial embedding process would be very slow. | Startup Latency. Initial startup time increases linearly with the size of the policy documents. | Persistent Vector Store: Instead of rebuilding the vector store in memory (FAISS) every time the service starts, save the index to disk (e.g., a file-based FAISS index) after the first build. Load the saved index directly on subsequent startups. |
| Single-Threaded Agent | All agent actions (ainvoke) run on FastAPI's single event loop thread, blocking other requests while the LLM or RAG calls execute. | Low Throughput. The application cannot handle concurrent users efficiently, leading to request queuing. | Use Async I/O: Ensure all I/O operations (which is true for httpx-based Ollama calls) use await. More importantly, if synchronous tools were used, they would need to be wrapped in run_in_executor to offload them to a thread pool. (The current setup is mostly non-blocking, but concurrent LLM calls still consume CPU time). |


### 3. Security Concerns and Mitigation
| Concern | Status in Prototype | Risk & Attack Vector | Recommended Future Mitigation |
| ----- | ----- | ----- | ----- |
| Prompt Injection (PI)	| Heuristic Filtered. (Weak Defense)	| High. User attempts to trick the LLM into disclosing policies or executing unauthorized tool calls.	| Input/Output Guardrails: Use a small, fast model (e.g., Llama 3 8B) as an input classifier to reject malicious prompts before they reach the main agent. Use red-teaming to find prompt vulnerabilities. |
|RBAC / Data Leakage | Simulated. (Tool Gated)	| Medium. Unauthorized users could access raw log data via the tool. Current defense is simple string matching on user_id.	| Token-Based Auth: Use Firebase or JWTs for real authentication. Tie the user's role/permissions to their authenticated ID (request.auth.uid), which is then passed to the tool wrapper for database query construction (Policy-as-Code). |
| Audit Logging	| Implemented (In-Memory).	| Low Traceability. Logs are lost on container restart.	| Persistence: Integrate an enterprise logging tool (e.g., Splunk, ELK stack) or a cloud database (Firestore/Postgres) for immutable, off-host log storage. |
| Tool Abuse (DoS)	| Partially Mitigated. (max_iterations=5)	| Medium. Agent could execute the RAG/Log tool in an infinite loop, causing a denial of service (DoS) on Ollama/CPU resources.	| Rate Limiting: Implement rate limiting on the /api/chat endpoint (e.g., 5 requests per minute per user_id or IP). Implement token usage limits per query. |
| Output Hallucination	| Unmitigated.	| High. The LLM may invent non-existent policies or fabricate log events, leading to incorrect incident response actions.	| Grounding: Explicitly instruct the agent to prefix all retrieved knowledge with a source citation ([Source: phishing_policy.md]). Use RAG scores to enforce high-confidence responses and refuse to answer if grounding is poor. |


# License
Free to use without warrantees.

### Story
I was asked (in the interview) to implement the AI chat bot that handles tool selections: security incident tool and log look up tool. Otherwise just do chat like ChatGPT. This is the answer (source) and is considered a good answer. Hope this helps others looking for a SW Engineering job.

backend: free to choose (by candidate.)

frontend: React (but you can choose others for your interview.) Front end is pretty simple. Only one page. No auth handling. Just interact with the backend.
