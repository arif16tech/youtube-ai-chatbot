# 🎥 YouTube AI Chatbot

An AI-powered YouTube chatbot that lets you ask questions about **Hindi and English YouTube videos**. Answers are grounded in the video's transcript using **RAG**, with timestamped sources.

### ✨ Features

- 🎥 YouTube video URL processing
- 🇮🇳 Hindi + 🇬🇧 English transcript support
- 🤖 RAG-based question answering
- 🔎 FAISS vector search
- 🌐 Multilingual Hugging Face embeddings
- ⚡ Groq LLM responses
- 💬 Interactive chat interface
- 📝 Video summary
- 💡 Suggested questions
- ⏱️ Timestamped sources
- ⚡ Streaming responses
- 🛡️ Input validation, error handling & rate limiting

### 🛠️ Tech Stack

**Frontend**
- React 19
- Vite 8
- Tailwind CSS v4

**Backend**
- Python
- FastAPI
- LangChain
- FAISS
- YouTube Transcript API

**AI**
- Groq — `openai/gpt-oss-120b`
- Hugging Face multilingual embeddings

### 🏗️ Architecture

```text
YouTube URL
     ↓
Transcript
     ↓
Documents → Chunking
     ↓
Hugging Face Embeddings
     ↓
FAISS
     ↓
Retriever
     ↓
Groq LLM
     ↓
Answer + Sources
```

### 📁 Project Structure

```text
youtube-ai-chatbot/
├── backend/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── models/
│       ├── routers/
│       ├── services/
│       └── utils/
│
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       └── components/
│
├── docker-compose.yml
└── README.md
```

### 🚀 Setup

#### 1. Clone the repository

```bash
git clone <your-repository-url>
cd youtube-ai-chatbot
```

#### 2. Backend

```bash
cd backend

python -m venv .venv
```

**Windows:**

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env`:

```env
GROQ_API_KEY=your_groq_api_key
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token
```

Start the server:

```bash
uvicorn app.main:app --reload --port 8000
```

#### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

### 🔑 Environment Variables

| Variable | Required |
|---|---|
| `GROQ_API_KEY` | Yes |
| `HUGGINGFACEHUB_API_TOKEN` | Yes |
| `GROQ_MODEL` | No |
| `EMBEDDING_MODEL` | No |
| `ALLOWED_ORIGINS` | No |

### 📡 API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/video/process` | Process YouTube video |
| POST | `/api/chat/ask` | Ask a question |
| POST | `/api/chat/stream` | Stream answer |
| GET | `/api/chat/history/{session_id}` | Get chat history |
| GET | `/api/health` | Health check |
