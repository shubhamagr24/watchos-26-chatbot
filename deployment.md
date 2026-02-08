# Deployment Guide for Render

## Single Deployment for Backend and Frontend
1. Ensure all dependencies are installed for both backend and frontend by running:
   ```bash
   uv install
   ```
2. Push the code to a GitHub repository.
3. On Render, create a new Web Service:
   - Select the repository.
   - Render will automatically detect the `render.yaml` file at the root of the repository.
4. Deploy the services as defined in the `render.yaml` file.