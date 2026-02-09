"""
API routes
"""
from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage, AIMessage

from app.api.models import ChatRequest, ChatResponse
from app.services.agent_service import process_message
from app.services.rag_service import rag_kb
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": f"{settings.APP_NAME} is running",
        "version": settings.APP_VERSION,
        "knowledge_base_loaded": rag_kb.chunks_loaded > 0,
        "total_chunks": rag_kb.chunks_loaded
    }


@router.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "openai": bool(settings.OPENAI_API_KEY),
            "tavily": bool(settings.TAVILY_API_KEY),
            "langsmith": settings.LANGCHAIN_TRACING_V2 == "true"
        },
        "knowledge_base": {
            "loaded": rag_kb.vectorstore is not None,
            "chunks": rag_kb.chunks_loaded,
            "persist_directory": rag_kb.persist_directory
        }
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Convert conversation history to LangChain format
        history = []
        for msg in request.conversation_history:
            if msg.role == "user":
                history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                history.append(AIMessage(content=msg.content))
        
        # Process the message
        result = process_message(request.message, history)
        
        return ChatResponse(
            response=result["response"],
            status="success",
            tools_used=result.get("tools_used", []),
            used_local_kb=result.get("used_local_kb", False),
            used_web_search=result.get("used_web_search", False)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/reset")
async def reset_conversation():
    """Reset conversation history"""
    return {
        "status": "success",
        "message": "Conversation reset. Ready for new conversation."
    }


@router.get("/examples")
async def get_examples():
    """Get example questions"""
    return {
        "examples": [
            "What's new in Watch OS 26.3?",
            "How do I set up ECG monitoring?",
            "What bugs were fixed in the latest version?",
            "Tell me about battery improvements",
            "How to customize watch faces?",
            "What devices support Watch OS 26?",
            "How do I update to Watch OS 26?",
            "Troubleshoot Watch OS 26 connectivity issues",
            "What are the new health features?",
            "How to use the Fitness app on Watch OS 26?"
        ],
        "categories": [
            {
                "name": "Features",
                "examples": [
                    "How to Track your medications on Apple Watch?",
                    "How to Log state of mind on Apple Watch?"
                ]
            },
            {
                "name": "Troubleshooting",
                "examples": [
                    "How to fix connectivity issues?",
                    "Why is my battery draining fast?"
                ]
            },
            {
                "name": "Updates",
                "examples": [
                    "What's issues were resolved in Watch OS 26.2 update?",
                    "What’s new in Apple Watch and watchOS 26 ??"
                ]
            }
        ]
    }


@router.get("/stats")
async def get_stats():
    """Get knowledge base statistics"""
    stats = rag_kb.get_stats()
    return {
        "knowledge_base": stats,
        "api_version": settings.APP_VERSION,
        "features": {
            "rag_enabled": stats['vectorstore_ready'],
            "web_search_fallback": bool(settings.TAVILY_API_KEY),
            "langsmith_tracing": settings.LANGCHAIN_TRACING_V2 == "true"
        }
    }
