# Deployment Guide for Render

## Single Deployment for Backend and Frontend
1. Ensure all dependencies are installed for both backend and frontend by running:
   ```bash
   pip install -r backend/requirements.txt
   pip install -r frontend/requirements.txt
   ```
2. Push the code to a GitHub repository.
3. On Render, create a new Web Service:
   - Select the repository.
   - Render will automatically detect the `render.yaml` file at the root of the repository.
   - This file defines two services:
     - **Backend Service**:
       - Build Command: `pip install -r backend/requirements.txt`
       - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
     - **Frontend Service**:
       - Build Command: `pip install -r frontend/requirements.txt`
       - Start Command: `gunicorn frontend.app:app`
4. Deploy the services as defined in the `render.yaml` file.