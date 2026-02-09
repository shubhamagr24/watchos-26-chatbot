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

The WatchOS 26 Chatbot is a conversational assistant that provides:
- Insights into WatchOS 26 features.
- Answers to frequently asked questions.
- Information from release notes and user guides.
- Web search fallback for additional queries.

---

## Features

- **Local Knowledge Base**: Uses preloaded data from release notes and user guides.
- **Web Search Integration**: Fallback to web search for queries not covered in the knowledge base.
- **Streamlit Frontend**: Interactive and user-friendly interface.
- **FastAPI Backend**: Robust and scalable backend API.
- **CORS Configuration**: Secure communication between frontend and backend.

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
