# OmniAI

A full-stack, multi-agent AI platform that turns user intent into action with guardrails, retrieval, and analytics.

OmniAI solves a practical problem: how to build a reliable AI assistant that can route between reasoning, research, tools, memory, and interview workflows, while still tracking user wellbeing signals (emotion + risk) and maintaining retrieval context from documents and a knowledge graph.

This repository contains a production-style FastAPI backend orchestrated by LangGraph and a polished Next.js client. The platform supports multi-agent chat, RAG over Pinecone, knowledge graph over Neo4j, MCP tool execution, and an interview preparation suite.

---

## What This Project Does

OmniAI receives a user message, detects emotion, computes risk context, routes the request to a specialized agent, and returns a formatted response. It also stores chat history, extracts knowledge graph signals, and optionally generates TTS audio.

Primary use cases:

- Multi-agent conversational assistant
- Document Q&A with vector retrieval
- Knowledge graph exploration
- Interview prep workflows and scoring
- Emotion analytics with trend tracking

---

## Architecture Overview

At a high level, the backend is a LangGraph state machine wrapped by FastAPI, and the frontend is a Next.js SPA that consumes the API and renders the agent + emotion metadata.

```mermaid
flowchart LR
  U[User] --> UI[Next.js Client]
  UI -->|JWT Auth| API[FastAPI /chat]
  API --> IG[Input Guard]
  IG --> ED[Emotion Detection]
  ED --> RA[Risk Assessment]
  RA --> LG[LangGraph Router]
  LG --> R1[Reasoning Agent]
  LG --> R2[Research Agent]
  LG --> R3[Tools Agent]
  LG --> R4[Memory Agent]
  LG --> R5[Interview Agent]
  R1 --> OUT[Output Guard + Formatter]
  R2 --> OUT
  R3 --> OUT
  R4 --> OUT
  R5 --> OUT
  OUT --> UI
  OUT -->|Async| DB[(PostgreSQL)]
  OUT -->|Async| PC[(Pinecone)]
  OUT -->|Async| KG[(Neo4j)]
  OUT -->|Optional| TTS[Text-to-Speech]
```

---

## Key Features

- Multi-agent routing with LangGraph
- Input + output guardrails
- Emotion detection and risk scoring
- RAG with Pinecone + chunked PDF ingestion
- Knowledge graph ingestion and inspection via Neo4j
- MCP tool execution (web search, calculator, filesystem, terminal)
- Interview prep: resume analysis, mock sessions, feedback
- Optional TTS audio responses
- Polished chat UI with sessions and emotion tags

---

## Repository Map

- ai-engine: FastAPI backend, agents, graph, services
- client: Next.js UI (chat, mood, interview, KG)
- server: optional Node service
- mcp-servers: MCP tool servers
- docs: run notes

---

## How It Works (Backend Flow)

1) POST /chat receives the message
2) Input guard validates
3) Emotion classifier detects tone + intensity
4) Risk engine evaluates trends from history
5) LangGraph routes to the right agent
6) Output guard + formatter finalize response
7) Background tasks persist memory + KG extraction
8) Optional TTS returns audio

---

## Tech Stack

Backend: FastAPI, LangGraph, Mistral API, PostgreSQL
Retrieval: Pinecone, BM25 fallback
Graph: Neo4j
Frontend: Next.js, React, Tailwind
Tools: MCP servers (filesystem, search, terminal)

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL
- Pinecone index
- Neo4j (required for KG features)
- Mistral API key

### Backend

```bash
cd ai-engine
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd client
npm install
```

### Optional Node Service

```bash
cd server
npm install
```

---

## Environment Variables

Create ai-engine/.env:

```env
MISTRAL_API_KEY=your_key
MISTRAL_MODEL=mistral-small-latest
PINECONE_API_KEY=your_key
PINECONE_INDEX=your_index_name
DATABASE_URL=postgresql://user:password@host:5432/dbname
JWT_SECRET=change-this-secret
NEO4J_URI=neo4j+s://<host>
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

Create client/.env.local:

```env
NEXT_PUBLIC_AI_ENGINE_URL=http://localhost:8000
```

---

## Run

Backend:

```bash
cd ai-engine
.venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd client
npm run dev
```

Open:
- http://localhost:3000
- http://localhost:8000/docs

---

## API Highlights

Auth: /auth/register, /auth/login
Chat: /chat, /history/sessions, /history/{session_id}
Documents: /upload, /documents
KG: /kg/inspect, /kg/health
Emotion: /emotion/analytics, /emotion/trend
Interview: /interview/mock/start, /interview/feedback/{session_id}
TTS: /tts

---

## Data & Storage

- PostgreSQL stores users, chat history, emotion logs, interview sessions
- Pinecone stores embedded document chunks
- Neo4j stores extracted entities, relations, and messages

---

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

---

## Troubleshooting

Auth fails:

- Confirm DATABASE_URL is correct
- Run migrate.py
- Ensure users table exists

---

## Notes

- KG routes require Neo4j env vars
- If responses feel slow, use a faster Mistral model
- MCP servers can be swapped or extended for new tools

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
