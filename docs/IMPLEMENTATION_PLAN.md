# Implementation Plan: Local LLM CLI Multi-Agent Chat App

## 1. Architecture Overview
A full-stack application integrating local CLI LLMs (e.g., `gemini-cli`) with a web-based multi-agent chat interface.
- **Backend:** Python (FastAPI) handling business logic, process management, and data persistence.
- **Frontend:** React (TypeScript) with TailwindCSS for a modern, responsive, and streaming-capable UI.
- **Database:** SQLite for storing chat history, sessions, and personas.
- **Communication:** 
  - REST API for CRUD operations (Personas, Sessions, Messages).
  - WebSockets (or SSE) for real-time streaming of LLM responses.

## 2. Backend Design (FastAPI)

### 2.1. Core Domain Models (SQLAlchemy)
- **Persona:** `id`, `name`, `instruction`, `engine_type`, `is_favorite`, `created_at`, `updated_at`
- **Session:** `id`, `title`, `created_at`, `updated_at`
- **Message:** `id`, `session_id`, `sender_type` (user, agent), `persona_id` (nullable), `content`, `metadata` (JSON), `created_at`

### 2.2. LLM Engine Interface (`ILLMConnector`)
- Abstract base class defining `send_message(prompt: str, context: list[dict], system_prompt: str) -> AsyncGenerator[str, None]`.
- **GeminiCLIConnector:** Implementation using `asyncio.create_subprocess_exec` to interact with `gemini-cli`.
  - Uses `stdin` to send prompts and `stdout` to stream responses asynchronously.

### 2.3. API Endpoints
- `GET /api/personas`, `POST /api/personas`, `PUT /api/personas/{id}`, `DELETE /api/personas/{id}`
- `GET /api/sessions`, `POST /api/sessions`, `GET /api/sessions/{id}/messages`
- `WebSocket /api/chat/ws/{session_id}`: Handles bidirectional communication. Client sends messages/prompts, server invokes the CLI and streams markdown chunks back.

## 3. Frontend Design (React + TypeScript + Tailwind)

### 3.1. UI Layout
- **Sidebar (Left):** Session history (like ChatGPT), Settings button.
- **Main Chat Area (Center):** Message list supporting rich text (Markdown, Code highlighting).
- **Input Area (Bottom):** Textarea for prompts, controls for Moderation (selecting which agent responds).
- **Agent/Persona Panel (Right - Optional/Collapsible):** Manage and select active personas for the current session.

### 3.2. State Management
- React Context or Zustand for global state (active session, active personas, streaming status).
- `react-markdown` for rendering Markdown.

### 3.3. Streaming Chat Implementation
- The user (Moderator) types a message and optionally selects one or more agents to respond.
- The message is sent to the backend.
- The backend stores the user message, invokes the selected agent(s) sequentially or parallelly (if supported), and streams the response(s) via WebSocket.
- The UI dynamically updates the current agent's message block as chunks arrive.

## 4. Execution Phases

### Phase 1: Backend Scaffolding & CLI Integration
- Set up FastAPI project and SQLite database with SQLAlchemy.
- Implement the `ILLMConnector` and specifically the `GeminiCLIConnector` using asynchronous subprocesses.
- Create basic CRUD routes for Personas and Sessions.

### Phase 2: Frontend Scaffolding & Basic UI
- Initialize React (Vite) project with TailwindCSS.
- Build the static layout (Sidebar, Chat window, Input area).
- Implement basic state to handle text input and display static messages.

### Phase 3: Streaming & WebSockets Integration
- Implement the WebSocket endpoint in FastAPI to handle chat logic.
- Connect the React frontend to the WebSocket.
- Implement streaming message rendering with Markdown support.

### Phase 4: Multi-Agent Moderation & Polish
- Add UI controls for the user to act as a moderator (e.g., "Ask Agent A", "Ask Agent B").
- Implement context window management strategies (truncating older messages before sending to CLI).
- Add error handling for CLI process crashes (Fail-Fast recovery).
- Final UI polish and consistent aesthetics.