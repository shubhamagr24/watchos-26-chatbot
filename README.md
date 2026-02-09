# WatchOS 26 Chatbot

Welcome to the WatchOS 26 Chatbot repository! This project is an AI-powered chatbot designed to provide information about WatchOS 26, leveraging a local knowledge base and web search capabilities. The repository is structured into backend and frontend components, each serving a specific purpose.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Repository Structure](#repository-structure)
4. [Backend](#backend)
5. [Frontend](#frontend)
6. [Setup Instructions](#setup-instructions)
7. [Usage](#usage)
8. [Contributing](#contributing)
9. [License](#license)

---

## Overview

The WatchOS 26 Chatbot is an advanced conversational assistant powered by **LangGraph**, providing:
- **Intelligent Reasoning**: Decision-making agent for selecting between local knowledge and web search.
- **Insights into WatchOS 26**: Precise information about features, release notes, and user guides.
- **Refined RAG**: Multi-stage retrieval pipeline with LLM-based snippet extraction.
- **Web Search Fallback**: Tavily integration for queries not covered in the local knowledge base.

---

## Features

- **LangGraph Agent**: Orchestrates the conversation flow and tool usage (RAG vs Web Search).
- **Refined RAG Pipeline**: Uses a multi-step Retrieve -> Refine process with similarity thresholding and LLM-assisted extraction for high-precision answers.
- **Local Knowledge Base**: Preloaded JSON and Markdown data from official Apple support and developer docs.
- **Web Search Integration**: Fallback to web search when the knowledge base lacks sufficient information.
- **Streamlit Frontend**: Responsive, interactive UI with tool usage visibility.
- **FastAPI Backend**: Asynchronous API with comprehensive health and stats monitoring.

---

## Repository Structure

```
watchos-26-chatbot/
├── backend/       # Backend service built with FastAPI
├── frontend/      # Frontend application built with Streamlit
├── deployment.md  # Deployment instructions
```

### Backend

The backend is implemented using FastAPI and provides the following functionalities:
- API endpoints for chatbot communication.
- Health checks and system statistics.
- Integration with a local knowledge base and web search.

#### Key Files:
- `main.py`: Entry point for the FastAPI application.
- `app/api/routes.py`: Defines API routes.
- `app/core/config.py`: Configuration settings.
- `apple_watch_kb/`: Contains knowledge base files (JSON format).
- `chroma_db/`: Stores vectorized data for the knowledge base.

### Frontend

The frontend is implemented using Streamlit and provides an interactive user interface for the chatbot.

#### Key Files:
- `app.py`: Main Streamlit application file.
- `requirements.txt`: Lists Python dependencies.

---

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Node.js (optional, for additional tooling)

### Backend Setup

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the backend server:
   ```bash
   python -m app.main
   ```

### Frontend Setup

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the frontend application:
   ```bash
   streamlit run app.py
   ```

---

## Usage

1. Start the backend server.
2. Start the frontend application.
3. Open the frontend in your browser (Streamlit will provide a URL).
4. Interact with the chatbot by asking questions about WatchOS 26.

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes and push them to your fork.
4. Submit a pull request.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
