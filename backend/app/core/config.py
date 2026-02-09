"""
Configuration management
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings"""
    
    # API Settings
    APP_NAME = "Watch OS 26 Chatbot API"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "AI-powered chatbot for Watch OS 26 information with RAG"
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    
    # LangSmith Settings
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false")
    LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "watchos-26-chatbot")
    
    # Model Settings
    LLM_MODEL = "gpt-4o-mini"
    LLM_TEMPERATURE = 0.8
    
    # RAG Settings
    USER_GUIDE_PATH = "./apple_watch_kb/user_guide.json"
    RELEASE_NOTES_PATH = "./apple_watch_kb/release_notes.json"
    CHROMA_PERSIST_DIR = "./chroma_db"
    FORCE_REBUILD = False
    
    # Chunking Settings
    USER_GUIDE_CHUNK_SIZE = 1200
    USER_GUIDE_CHUNK_OVERLAP = 200
    RELEASE_NOTES_CHUNK_SIZE = 800
    RELEASE_NOTES_CHUNK_OVERLAP = 150
    
    # Search Settings
    DEFAULT_SEARCH_RESULTS = 4
    MAX_SEARCH_RESULTS = 10
    WEB_SEARCH_DEPTH = "advanced"
    WEB_SEARCH_MAX_RESULTS = 3
    RAG_SIMILARITY_THRESHOLD = 0.6  # Filter for high-relevance docs
    REFINEMENT_SIMILARITY_MIN = 0.6
    REFINEMENT_SIMILARITY_MAX = 0.8
    REFINEMENT_MAX_DOCS = 3
    REFINEMENT_MODEL = "gpt-4o-mini"
    
    # Server Settings
    HOST = "0.0.0.0"
    PORT = 8000
    LOG_LEVEL = "info"
    
    @classmethod
    def validate(cls):
        """Validate required settings"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        if not cls.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY is required")
        
        # Check file paths
        if not Path(cls.USER_GUIDE_PATH).exists():
            print(f"⚠️ Warning: User guide not found at {cls.USER_GUIDE_PATH}")
        if not Path(cls.RELEASE_NOTES_PATH).exists():
            print(f"⚠️ Warning: Release notes not found at {cls.RELEASE_NOTES_PATH}")


# Initialize settings
settings = Settings()

# Configure LangSmith if enabled
if settings.LANGCHAIN_TRACING_V2 == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
    print("✓ LangSmith tracing enabled")
