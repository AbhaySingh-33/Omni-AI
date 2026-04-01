# OmniAI

OmniAI is a full stack multi-agent AI platform with:
- FastAPI backend orchestrated by LangGraph
- Next.js frontend
- RAG over Pinecone
- Knowledge graph over Neo4j
- PostgreSQL auth and memory
- MCP tool execution (web search, calculator, file system, terminal)
- Interview preparation module
- Emotion and risk analytics module

This README is a complete project reference for setup, architecture, APIs, and operations.

## Table of Contents

1. Project Summary
2. Current Features
3. Architecture
4. Repository Structure
5. Prerequisites
6. Environment Variables
7. Local Setup
8. Running the System
9. API Reference
10. Data and Storage
11. Agent Orchestration
12. Performance and Latency Notes
13. Development Workflow
14. Testing
15. Troubleshooting
16. Security Notes

## Project Summary

OmniAI processes user input through a router-driven multi-agent workflow and returns context-aware responses.

Primary backend entry point:
- ai-engine/main.py

Primary frontend app:
- client/app/page.tsx

Optional Node service:
- server/src/server.js

## Current Features

- JWT auth (register/login)
- Multi-agent chat endpoint
- Emotion detection and risk scoring
- Optional TTS audio in chat response
- PDF upload and semantic retrieval
- Knowledge graph ingestion and inspection
- Interview resume generation, analysis, mock interview, scoring
- Emotion analytics dashboard APIs
- Client chat UI, sidebar, docs panel, KG and mood pages

## Architecture

High level backend flow:

1. User sends message to POST /chat
2. Input guard validates message
3. Emotion detector classifies message
4. Risk engine computes risk and trend from recent emotion history
5. LangGraph workflow executes:
   - router agent selects route
   - one of reasoning, research, tools, memory, interview agents responds
6. Output formatter and output guard process final response
7. Background tasks persist chat, KG message extraction, and emotion log
8. Optional TTS audio synthesis if voice=true

Core modules:
- Routing and graph: ai-engine/graph/workflow.py, ai-engine/agents/router_agent.py
- LLM and DSPy: ai-engine/app/gemini.py, ai-engine/app/dspy_module.py
- RAG: ai-engine/services/ingest.py, ai-engine/services/retriever.py
- KG: ai-engine/services/kg.py, ai-engine/database/neo4j_loader.py
- Memory: ai-engine/services/memory.py
- Emotion: ai-engine/emotion/classifier.py, ai-engine/emotion/risk_engine.py, ai-engine/emotion/emotion_store.py
- Tools: ai-engine/agents/tool_agent.py, ai-engine/app/mcp_client.py, mcp-servers/*.py

## Repository Structure

Top level folders:

- ai-engine: Python backend
- client: Next.js frontend
- server: optional Node service
- mcp-servers: MCP tool servers
- docs: run notes

Important backend files:

- ai-engine/main.py
- ai-engine/routes/auth.py
- ai-engine/routes/chat.py
- ai-engine/routes/documents.py
- ai-engine/routes/kg.py
- ai-engine/routes/interview.py
- ai-engine/routes/emotion.py
- ai-engine/routes/tts.py
- ai-engine/routes/system.py
- ai-engine/app/auth.py
- ai-engine/app/db.py
- ai-engine/core/app_state.py

Important frontend files:

- client/app/layout.tsx
- client/app/page.tsx
- client/app/interview/*
- client/app/kg/*
- client/app/mood/page.tsx
- client/hooks/useChat.ts
- client/hooks/useEmotion.ts
- client/components/ChatWindow.tsx

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- PostgreSQL
- Pinecone index
- Neo4j (optional but required for KG features)
- Mistral API key

## Environment Variables

Create .env in ai-engine directory (recommended) with:

```env
# LLM
MISTRAL_API_KEY=your_key
MISTRAL_MODEL=mistral-small-latest

# Vector DB
PINECONE_API_KEY=your_key
PINECONE_INDEX=your_index_name

# Relational DB
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Auth
JWT_SECRET=change-this-secret

# Neo4j (for KG)
NEO4J_URI=neo4j+s://<host>
NEO4J_USER=neo4j
# or NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

Create .env.local in client directory:

```env
NEXT_PUBLIC_AI_ENGINE_URL=http://localhost:8000
```

Notes:
- MISTRAL_MODEL is optional. Current default in code is mistral-small-latest.
- KG routes will fail if Neo4j variables are missing.

## Local Setup

### Backend setup

```bash
cd ai-engine
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt
```

### Database migration

```bash
cd ai-engine
.venv\Scripts\activate
python migrate.py
```

### Frontend setup

```bash
cd client
npm install
```

### Optional Node service

```bash
cd server
npm install
```

## Running the System

Run backend:

```bash
cd ai-engine
.venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Run frontend:

```bash
cd client
npm run dev
```

Optional Node service:

```bash
cd server
npm run dev
```

Open:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Backend docs: http://localhost:8000/docs

## API Reference

All protected endpoints require:

Authorization: Bearer <token>

### System

- GET /
  - Health message from backend

### Auth

- POST /auth/register
  - body: { "email": string, "password": string }
  - returns token and email

- POST /auth/login
  - body: { "email": string, "password": string }
  - returns token and email

### Chat

- POST /chat
  - body: { "message": string, "voice": boolean, "voice_lang": string|null }
  - returns:
    - response
    - agent
    - optional emotion metadata
    - optional audio_b64 and audio_mime

- GET /history
  - returns last persisted user/assistant turns

### Documents and RAG

- POST /upload
  - multipart PDF upload
  - ingests chunks to Pinecone and KG

- GET /documents
  - list uploaded docs and chunk counts

- DELETE /documents/{doc_id}
  - delete vectors and related KG document edges

### KG

- GET /kg/health
  - shows Neo4j env variable presence

- GET /kg/inspect
  - query params:
    - q
    - limit
    - doc_id
    - source_type

### TTS

- POST /tts
  - body: { "text": string, "lang": string }
  - returns audio/mpeg binary

### Emotion

- GET /emotion/history?days=30
- GET /emotion/trend?days=7
- GET /emotion/alerts
- GET /emotion/analytics
- POST /emotion/alerts/{alert_id}/acknowledge

### Interview

Resume:
- POST /interview/resume
- POST /interview/resume/generate
- POST /interview/resume/analyze
- GET /interview/resume
- GET /interview/resume/all
- DELETE /interview/resume/{resume_id}

Questions and simulation:
- POST /interview/questions
- POST /interview/mock/start
- POST /interview/mock/respond
- GET /interview/mock/session/{session_id}
- GET /interview/mock/sessions

Feedback and progress:
- POST /interview/feedback/{session_id}
- GET /interview/feedback/{session_id}
- POST /interview/evaluate-answer
- GET /interview/progress
- POST /interview/init-db

## Data and Storage

PostgreSQL tables (created by migrate.py and startup initializers):

- users
- chat_history
- summarized_memory
- emotion_log
- emotion_alerts
- interview-related tables from services/interview.py initializer

Pinecone:
- stores embedded document chunks with metadata user_id/doc_id/chunk/filename

Neo4j:
- nodes: Entity, Document, Message
- relationships for mentions and extracted relations
- constraints/indexes auto-created by Neo4jLoader

## Agent Orchestration

Graph nodes:
- router
- reasoning
- research
- tools
- memory
- interview

State includes:
- messages
- next
- user_id
- iterations
- agent_used
- emotion_context

Router behavior:
- deterministic keyword fast paths for low latency
- routes to specific agent
- worker response usually finishes in one pass

## Performance and Latency Notes

Latency optimizations already in code:

- blocking work moved to threadpool in chat route
- background tasks for persistence operations
- deterministic router paths to reduce unnecessary model calls
- configurable fast default model via MISTRAL_MODEL
- parallel retrieval/KG calls in research and memory paths
- timeout protection on optional context fetches
- thread-local PostgreSQL connection handling

If response is still slow, verify:

1. Backend restarted after code changes
2. MISTRAL_MODEL is set to a fast model
3. Pinecone index is reachable and healthy
4. Neo4j is reachable (if KG enabled)
5. DATABASE_URL network latency is reasonable

## Development Workflow

Typical workflow:

1. Start backend and frontend
2. Create account and login
3. Test chat, upload, and interview routes from UI
4. Validate backend with /docs
5. Run focused tests from ai-engine/tests

Formatting and linting:
- Frontend: npm run lint
- Backend: use your preferred formatter/linter (not enforced in this repo root)

## Testing

Backend tests/scripts currently present in ai-engine/tests:

- check_rag.py
- test_rag.py
- test_a2a_loop.py
- test_a2a_mocked.py
- test_a2a_scenario_aapl.py

Run example:

```bash
cd ai-engine
.venv\Scripts\activate
python tests\test_rag.py
```

## Troubleshooting

### 1) Auth fails
- Confirm DATABASE_URL is correct
- Run migrate.py
- Ensure users table exists

### 2) /chat returns slowly
- Check MISTRAL_MODEL
- Check external DB/network latency
- Check Pinecone and Neo4j connectivity

### 3) KG endpoints fail
- Ensure NEO4J_URI, NEO4J_USER (or NEO4J_USERNAME), NEO4J_PASSWORD are set

### 4) Upload works but answers have no context
- Verify PINECONE_INDEX and API key
- Confirm vectors were inserted (logs during upload)

### 5) TTS fails
- Check outbound internet access for gTTS
- Validate language code sent to /tts

### 6) Frontend cannot reach backend
- Confirm NEXT_PUBLIC_AI_ENGINE_URL in client/.env.local
- Confirm backend is running on that URL

## Security Notes

- Do not use default JWT secret in production
- Restrict CORS in production
- Enforce strong DB credentials and TLS
- Review tool guard rules before enabling broad command execution
- Keep API keys only in server-side env files

## License

No license file is currently defined in this repository. Add a LICENSE file before open-source distribution.
  "password": "securepassword"
}
```

### Chat

#### Send Message
```http
POST /chat
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
  "message": "What is the capital of France?"
}
```

**Response:**
```json
{
  "response": "The capital of France is Paris...",
  "agent": "reasoning",
  "timestamp": "2026-03-24T10:30:00Z"
}
```

#### Get Chat History
```http
GET /history
Authorization: Bearer <your_jwt_token>
```

### Document Management

#### Upload PDF
```http
POST /upload
Authorization: Bearer <your_jwt_token>
Content-Type: multipart/form-data

file: <pdf_file>
```

#### List Documents
```http
GET /documents
Authorization: Bearer <your_jwt_token>
```

#### Delete Document
```http
DELETE /documents/{document_id}
Authorization: Bearer <your_jwt_token>
```

---

## Agent System

### Agent Specifications

| Agent | Role | Data Source | Tools | LLM |
|-------|------|-------------|-------|-----|
| **Router** | Classifies intent and delegates | None | Fast-path keywords | Gemini |
| **Reasoning** | General knowledge, coding, explanations | LLM knowledge | DSPy modules | Mistral |
| **Research** | Document Q&A, RAG | Pinecone (user PDFs) | Semantic search | Mistral |
| **Tool** | Web search, files, terminal | Live web, filesystem | 6 MCP tools | Mistral |
| **Memory** | Conversation context | PostgreSQL | History retrieval | Mistral |

### Available Tools (MCP)

1. **web_search** - Search the web via DuckDuckGo
2. **calculator** - Perform mathematical calculations
3. **list_files** - List files in a directory
4. **read_file** - Read file contents
5. **write_file** - Write content to a file
6. **run_command** - Execute terminal commands (with safety confirmation)

### Workflow Example

```python
# User asks: "Search for recent AI news"

1. Router Agent
   - Receives: "Search for recent AI news"
   - LLM Classification: "tools" (web search needed)
   - Delegates to: Tool Agent

2. Tool Agent
   - Selects tool: web_search
   - Validates: Safe operation
   - Executes: DuckDuckGo search
   - Returns: Top 5 results with summaries

3. Output Guard
   - Validates response safety
   - Formats for user display

4. User Receives
   - Formatted search results
   - Agent badge: "🛠️ Tool Agent"
```

---

## Usage Examples

### Example 1: Document Q&A (RAG)

**Upload a PDF:**
```bash
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@research_paper.pdf"
```

**Ask Questions:**
```
User: "What is the main conclusion of the paper?"

Response: [Research Agent]
According to the uploaded document, the main conclusion is...
(Retrieved from page 15, relevance: 0.89)
```

### Example 2: Web Search

```
User: "What's the latest news about SpaceX?"

Response: [Tool Agent]
Here are the latest SpaceX news articles I found:
1. SpaceX launches 60 Starlink satellites...
2. Elon Musk announces new Mars mission timeline...
```

### Example 3: Coding Help

```
User: "Explain how async/await works in Python"

Response: [Reasoning Agent]
async/await is Python's syntax for asynchronous programming:

1. **async def**: Defines a coroutine function
2. **await**: Pauses execution until awaitable completes
3. **asyncio.run()**: Runs the async event loop

Example:
```python
async def fetch_data():
    await asyncio.sleep(1)
    return "Data"
```

### Example 4: Memory Recall

```
User: "What did we discuss yesterday?"

Response: [Memory Agent]
Based on your chat history, yesterday we discussed:
- Python async programming patterns
- FastAPI best practices
- LangGraph workflow design
```

---

## Development

### Running Tests

```bash
cd ai-engine
pytest tests/
```

### Code Style

**Python:**
```bash
black ai-engine/
flake8 ai-engine/
```

**TypeScript:**
```bash
cd client
npm run lint
```

### Adding a New Agent

1. Create agent file in `ai-engine/agents/`
2. Define agent logic with LangGraph node function
3. Add node to workflow in `graph/workflow.py`
4. Update router classification logic
5. Add tests

### Database Migrations

```bash
# Connect to PostgreSQL
psql $DATABASE_URL

# Run schema
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    agent VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE summaries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    summary TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Contribution Guidelines

- Follow existing code style
- Add tests for new features
- Update documentation
- Keep commits atomic and descriptive

---

## Troubleshooting

### Common Issues

**1. API_KEY_INVALID Error**

**Problem:** Environment variables not loading before LLM initialization

**Solution:**
```bash
# Ensure .env file exists in root directory
# Restart all services after updating .env
```

**2. Pinecone Index Not Found**

**Problem:** Pinecone index doesn't exist

**Solution:**
```python
# Create index in Pinecone console or via API
import pinecone
pinecone.create_index(
    name="omni-ai-docs",
    dimension=1024,  # Mistral embedding dimension
    metric="cosine"
)
```

**3. PostgreSQL Connection Failed**

**Problem:** Database not running or wrong credentials

**Solution:**
```bash
# Check PostgreSQL is running
systemctl status postgresql

# Test connection
psql $DATABASE_URL

# Update DATABASE_URL in .env
```

**4. CORS Errors**

**Problem:** Frontend can't reach backend

**Solution:**
```python
# In ai-engine/main.py, verify CORS middleware:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update for production
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**5. Module Import Errors**

**Problem:** Python packages not installed

**Solution:**
```bash
cd ai-engine
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### Debug Mode

**Enable FastAPI Debug:**
```bash
uvicorn main:app --reload --log-level debug
```

**Enable Next.js Debug:**
```bash
NODE_OPTIONS='--inspect' npm run dev
```

---

## License

This project is open source and available under the MIT License.

---

## Acknowledgments

- **LangChain** for LangGraph orchestration framework
- **Mistral AI** for powerful language models
- **Pinecone** for vector database infrastructure
- **FastAPI** for modern Python API framework
- **Next.js** for React framework

---

## Contact

**Project Maintainer**: [AbhaySingh-33](https://github.com/AbhaySingh-33)

**Repository**: [Omni-AI](https://github.com/AbhaySingh-33/Omni-AI)

**Issues**: [Report a bug](https://github.com/AbhaySingh-33/Omni-AI/issues)

---

Made with ❤️ by the OmniAI Team
