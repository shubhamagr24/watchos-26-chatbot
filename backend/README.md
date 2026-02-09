# Backend for WatchOS 26 Chatbot

This directory contains the backend implementation for the WatchOS 26 Chatbot. It provides APIs, services, and utilities to support the chatbot's functionality.

## Features
- **LangGraph Agent**: A stateful agent that uses a cyclic graph to manage conversation flow and tool execution.
- **Refined RAG Pipeline**: A sophisticated retrieval system that:
  - Filters results based on similarity thresholds.
  - Dynamically extracts relevant snippets using LLMs for borderline results.
  - Reranks and formats results for optimal context delivery.
- **FastAPI Backend**: High-performance asynchronous API endpoints.
- **Integrated Tools**: Modular tools for local knowledge search, web searching (Tavily), and webpage fetching.
- **Configuration-driven**: Easily adjustable thresholds, models, and chunking strategies.

## Folder Structure
```
backend/
├── app/
│   ├── api/                # API endpoints
│   ├── core/               # Core configurations and prompts
│   ├── services/           # Business logic and services
│   ├── utils/              # Utility functions
├── apple_watch_kb/         # Knowledge base for Apple Watch
├── chroma_db/              # Chroma database files
├── main.py                 # Entry point for the backend
├── requirements.txt        # Python dependencies
```

## Installation

### Prerequisites
- Python 3.12 or higher
- pip (Python package manager)

### Steps
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Start the FastAPI server:
   ```bash
   python main.py
   ```
2. The server will start, and you can access the API documentation at `http://localhost:8000/docs`.

## API Endpoints
- `GET /` - Health check endpoint.
- `GET /health` - Detailed health check.
- `POST /chat` - Main chat endpoint.
- `POST /reset` - Reset conversation history.
- `GET /examples` - Get example questions.
- `GET /stats` - Get knowledge base statistics.

FastAPI automatically generates interactive API documentation. Visit the `/docs` endpoint to explore and test the available APIs.

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes and push them to your fork.
4. Submit a pull request.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.