This project is a small AI assistant that can:
- store documents,
- answer questions using those documents,
- use simple tools such as search, summarize, and calculate,
- and show progress while it works.

It is built with Python, FastAPI, and a simple agent workflow.

## What this project does

The app provides three main API actions:

- POST /documents: add documents to the in-memory store
- POST /chat: ask a question and get a reply
- POST /chat/stream: get live progress updates while the agent works

The agent can use these tools:
- search_documents: find relevant information in stored documents
- summarize: make a short summary of the content
- calculate: solve simple math expressions safely

## Step-by-step setup

1. Open the project folder in VS Code.
2. Create a local environment file:
   - Copy .env.example to .env
3. Install the required Python packages:
   - Run: python -m pip install -r requirements.txt
4. Start the server:
   - Run: uvicorn app.main:app --reload
5. Open the API docs in your browser:
   - http://127.0.0.1:8000/docs

## Simple environment setup

The project uses a .env file for configuration.

Example values:
- AGENT_LLM_PROVIDER=none
- AGENT_OPENAI_API_KEY=
- AGENT_OPENAI_MODEL=gpt-4o-mini

If no OpenAI key is configured, the app will fall back to simple local behavior.

## How to use the app

### 1. Add documents

Send a POST request to /documents with text content.

Example:

```bash
curl -X POST "http://127.0.0.1:8000/documents" \
  -H "Content-Type: application/json" \
  -d '{"documents": ["Python is easy to learn.", "FastAPI helps build APIs quickly."]}'
```

### 2. Ask a question

Send a POST request to /chat.

Example:

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What does the document say about Python?"}'
```

### 3. Watch progress live

Use /chat/stream if you want to see updates while the agent is working.

### How to run this project -
clone the project
save the files
run -
uv add -r requirements.txt - for adding all the dependencies
uvicorn app.main:app --reload - for running the project 
Now, open path http://127.0.0.1:800/docs and call the respective endpoints



## Project structure

- app/main.py: starts the FastAPI app
- app/api.py: defines the API routes
- app/agent.py: contains the agent logic
- app/vector_store.py: stores and searches documents
- app/tools/: contains the available tools
- tests/: contains basic test cases

## How the agent works

In simple words:
1. The app receives a user message.
2. It looks for relevant documents.
3. It may use tools such as search, summarize, or calculate.
4. It builds a final response.

## How to run tests

Run:

```bash
pytest
```

## Notes and limitations

- Documents are stored in memory, so they are lost when the server restarts.
- The summarizer uses a simple local fallback when no external AI provider is configured.
- This is a small demo project, not a full production system.

## Why this design was chosen

- It is easy to understand.
- It is good for learning and testing.
- It keeps the project small and clear.
