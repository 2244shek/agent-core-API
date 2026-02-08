# Agent Core API - Agentic Insight Engine

A powerful FastAPI-based REST API that runs AI agents capable of reasoning, decision-making, and real-time web search. Built with LangGraph, Groq LLM, and integrated web search capabilities.

## 🎯 Overview

The **Agentic Insight Engine** is a production-ready API that enables intelligent conversational interactions with stateful chat sessions. The agent autonomously decides when to search the web for current information or provide direct answers using its reasoning capabilities.

### Key Features

- 🤖 **AI Agent Orchestration** - Uses LangGraph for complex multi-step agentic workflows
- 🔍 **Web Search Integration** - Real-time information gathering via Tavily Search API
- 💬 **Streaming Responses** - Server-Sent Events (SSE) for real-time chat feedback
- 💾 **Chat Persistence** - PostgreSQL-backed conversation history and session management
- ⚡ **High Performance** - Groq LLM integration for fast inference (Llama 3.3-70B model)
- 🌐 **CORS Enabled** - Ready for frontend integration
- 📊 **LangSmith Integration** - Built-in tracing and monitoring support
- 🛡️ **Error Handling** - Global exception handling with structured logging

## 📋 Prerequisites

- **Python** 3.8+
- **PostgreSQL Database** (Neon or self-hosted)
- **API Keys**:
  - Groq API Key (for LLM access)
  - Tavily API Key (for web search)
  - LangChain API Key (for tracing - optional)
  - OpenAI API Key (if using OpenAI, currently commented out)

## 🚀 Quick Start

### 1. Clone & Setup

```bash
cd agent-core-API
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
# LLM Configuration
GROQ_API_KEY=your_groq_api_key_here

# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# LangSmith Tracing (Optional)
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=agent-core-insight-engine
LANGCHAIN_TRACING_V2=true

# Web Search
TAVILY_API_KEY=your_tavily_api_key_here

# CORS Origins (adjust for your frontend URL)
CORS_ORIGINS=["http://localhost:3000"]
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 📁 Project Structure

```
agent-core-API/
├── app/
│   ├── main.py                    # FastAPI application setup
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── agent.py       # Chat endpoint routes
│   ├── core/
│   │   ├── config.py              # Settings & environment variables
│   │   └── exceptions.py          # Global exception handling
│   ├── db/
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   └── session.py             # Database connection & setup
│   └── services/
│       └── agent.py               # LangGraph agent definition
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🔌 API Endpoints

### Chat with Agent

**Endpoint:** `POST /api/v1/agent/chat/{session_id}`

**Description:** Send a message to the agent and receive a streaming response. The agent will autonomously decide whether to search the web or provide a direct answer.

**Request Body:**

```json
{
  "message": "What are the latest AI trends in 2026?"
}
```

**Parameters:**

- `session_id` (path, required): Unique identifier for the chat session
- `message` (body, required): User message

**Response:** Server-Sent Events (SSE) stream with events:

```json
{"type": "tool", "content": "Searching the web..."}
{"type": "text", "content": "The latest AI trends..."}
```

**Status Endpoint**

**Endpoint:** `GET /`

**Description:** Health check endpoint

**Response:**

```json
{
  "status": "Agent API is live",
  "version": "1.0.0"
}
```

## 🏗️ Architecture

### System Design

```
┌──────────────────────────────────────────────────────────────┐
│                      FastAPI Application                      │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              /api/v1/agent/chat Endpoint               │  │
│  └────────────┬───────────────────────────────────────────┘  │
│               │                                              │
│  ┌────────────▼───────────────────────────────────────────┐  │
│  │          Session & History Management                  │  │
│  │  • Load/Create ChatSession                             │  │
│  │  • Fetch conversation history                          │  │
│  └────────────┬───────────────────────────────────────────┘  │
│               │                                              │
│  ┌────────────▼───────────────────────────────────────────┐  │
│  │        LangGraph Agent Orchestration                   │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │        Researcher Node                          │  │  │
│  │  │  • Analyze user query                           │  │  │
│  │  │  • Invoke Groq LLM (Llama 3.3-70B)             │  │  │
│  │  │  • Decide: Search or Respond                    │  │  │
│  │  └──────────────┬──────────────────────────────────┘  │  │
│  │                 │                                      │  │
│  │       ┌─────────┴──────────┐                          │  │
│  │       │                    │                          │  │
│  │  ┌────▼────┐         ┌─────▼───────┐                 │  │
│  │  │   Tool   │         │   Response  │                 │  │
│  │  │   Node   │         │    Ready    │                 │  │
│  │  └────┬────┘         └─────────────┘                 │  │
│  │       │                                              │  │
│  │  ┌────▼────────────────────────────────────────────┐ │  │
│  │  │    Tavily Web Search Tool                       │ │  │
│  │  │  • Query the web for current info              │ │  │
│  │  │  • Return top 3 results                         │ │  │
│  │  └────┬─────────────────────────────────────────────┘ │  │
│  │       │ (loops back to researcher for synthesis)     │  │
│  │       └──────────────────────────────────────────────┘  │
│  └──────────────────────────────────────────────────────────┘  │
│               │                                              │
│  ┌────────────▼───────────────────────────────────────────┐  │
│  │        Streaming Response Generator                   │  │
│  │  • Emit events to client via SSE                      │  │
│  │  • Persist messages to database                       │  │
│  └────────────┬───────────────────────────────────────────┘  │
│               │                                              │
│  ┌────────────▼───────────────────────────────────────────┐  │
│  │            PostgreSQL Database                        │  │
│  │  • ChatSession (conversation metadata)                │  │
│  │  • ChatMessage (role + content persistence)           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Agent Workflow

The LangGraph agent implements a **reasoning loop**:

1. **Input**: User message + conversation history
2. **Researcher Node**:
   - Reads message context
   - Invokes Groq LLM with tools bound
   - LLM decides: call tool or provide answer
3. **Conditional Routing**:
   - If tool calls detected → Execute tools
   - If final answer → End workflow
4. **Tool Execution** (if needed):
   - Tavily Search Tool runs searches
   - Results returned to agent
5. **Loop Back**: Researcher node synthesizes results
6. **Output**: Final agent response

## 🔧 Configuration

All settings are managed via environment variables in `.env`:

| Variable            | Description                   | Required    |
| ------------------- | ----------------------------- | ----------- |
| `GROQ_API_KEY`      | Groq API key for LLM          | ✅ Yes      |
| `DATABASE_URL`      | PostgreSQL connection string  | ✅ Yes      |
| `TAVILY_API_KEY`    | Tavily API key for web search | ✅ Yes      |
| `LANGCHAIN_API_KEY` | LangSmith tracing API key     | ❌ Optional |
| `LANGCHAIN_PROJECT` | LangSmith project name        | ❌ Optional |
| `CORS_ORIGINS`      | Frontend URLs to allow        | ✅ Yes      |

See [app/core/config.py](app/core/config.py) for all configuration options.

## 📊 Database Schema

### ChatSession Table

| Column     | Type        | Description                                 |
| ---------- | ----------- | ------------------------------------------- |
| id         | String (PK) | Unique session identifier (UUID)            |
| user_id    | String      | User identifier (future multi-user support) |
| title      | String      | Optional session title                      |
| created_at | DateTime    | Session creation timestamp                  |
| updated_at | DateTime    | Last update timestamp                       |

### ChatMessage Table

| Column     | Type        | Description                      |
| ---------- | ----------- | -------------------------------- |
| id         | String (PK) | Unique message identifier (UUID) |
| session_id | String (FK) | Reference to ChatSession         |
| role       | String      | Message sender ("human" or "ai") |
| content    | Text        | Message content                  |
| created_at | DateTime    | Message creation timestamp       |

## 🛠️ Development

### Running Tests (Future)

```bash
pytest tests/
```

### Code Style

The project uses standard Python conventions:

- Async/await for I/O operations
- Type hints for better IDE support
- Structured logging for debugging

### Debugging with LangSmith

Enable LangSmith tracing to visualize agent behavior:

1. Set `LANGCHAIN_TRACING_V2=true` in `.env`
2. Provide valid `LANGCHAIN_API_KEY` and `LANGCHAIN_PROJECT`
3. View traces at https://smith.langchain.com

## 📦 Dependencies

- **fastapi** - Modern web framework
- **uvicorn** - ASGI server
- **sqlalchemy** - ORM for database access
- **psycopg2-binary** - PostgreSQL adapter
- **pydantic** - Data validation
- **pydantic-settings** - Environment configuration
- **langchain** - LLM framework
- **langchain-openai** - OpenAI integration
- **langchain-groq** - Groq LLM integration
- **langchain-tavily** - Web search integration
- **langgraph** - Agentic orchestration
- **python-dotenv** - Environment variable management

## 🌍 Deployment

### Production Checklist

- [ ] Set `LANGCHAIN_TRACING_V2=false` or use conditional tracing
- [ ] Use a production-grade ASGI server (e.g., Gunicorn with Uvicorn workers)
- [ ] Configure CORS for your frontend domain only
- [ ] Use a managed database (Neon, AWS RDS, etc.)
- [ ] Set up monitoring and alerting
- [ ] Implement rate limiting
- [ ] Use SSL/TLS for all communications

### Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t agent-core-api .
docker run -p 8000:8000 --env-file .env agent-core-api
```

## 🐛 Troubleshooting

### Database Connection Issues

- Verify `DATABASE_URL` format: `postgresql://user:password@host:port/dbname`
- For Neon: ensure SSL mode is configured
- Check `pool_pre_ping=True` setting in [app/db/session.py](app/db/session.py)

### API Key Errors

- Verify all required API keys are in `.env`
- Check for typos (environment variable names are case-sensitive)
- Test keys directly with provider APIs

### Streaming Response Issues

- Ensure client supports Server-Sent Events (SSE)
- Check browser console for network errors
- Verify CORS_ORIGINS configuration

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangGraph Documentation](https://langgraph.dev/)
- [LangChain Documentation](https://python.langchain.com/)
- [Groq API Docs](https://console.groq.com/docs)
- [Tavily Search API](https://tavily.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)

## 📝 License

This project is proprietary. For licensing information, contact the development team.

## 👥 Contributing

For contribution guidelines, please contact the project maintainers.

## 📧 Support

For issues, questions, or feature requests, please open an issue in the project repository.

---

**Last Updated:** February 2026  
**Version:** 1.0.0  
**Status:** Production Ready
