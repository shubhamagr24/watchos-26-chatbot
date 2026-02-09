"""
Streamlit Frontend for Watch OS 26 Chatbot
Single-file application
"""
import streamlit as st
import requests
import os
from typing import List, Dict, Optional

# ============================================================================
# Configuration
# ============================================================================

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 60

# ============================================================================
# Page Config
# ============================================================================

st.set_page_config(
    page_title="Watch OS 26 Assistant",
    page_icon="⌚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Custom CSS
# ============================================================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5rem;
        color: #1E88E5;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .tool-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        margin: 0.2rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .tool-kb {
        background-color: #E8F5E9;
        color: #2E7D32;
    }
    .tool-web {
        background-color: #E3F2FD;
        color: #1565C0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Backend API Functions
# ============================================================================

def check_backend_health() -> Dict:
    """Check backend health and get detailed status"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "error": f"Status code: {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "error": "Cannot connect to backend"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def get_backend_stats() -> Optional[Dict]:
    """Get backend statistics"""
    try:
        response = requests.get(f"{BACKEND_URL}/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def get_example_questions() -> Dict:
    """Fetch example questions from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/examples", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    # Fallback examples
    return {
        "examples": [
            "What's new in Watch OS 26.3?",
            "How do I set up ECG monitoring?",
            "What bugs were fixed recently?",
            "Tell me about battery improvements"
        ],
        "categories": []
    }


def send_message(message: str, history: List[Dict]) -> Dict:
    """Send message to backend and get response"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={
                "message": message,
                "conversation_history": history
            },
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"Error {response.status_code}: {response.text}"}
    
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out. Please try again."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to backend. Ensure backend is running."}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


# ============================================================================
# Session State Initialization
# ============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "backend_health" not in st.session_state:
    st.session_state.backend_health = check_backend_health()

# Set 'show_metadata' to True by default
if "show_metadata" not in st.session_state:
    st.session_state.show_metadata = True


# ============================================================================
# Header
# ============================================================================

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<p class="main-header">⌚ Watch OS 26 Assistant</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">AI-powered chatbot with local knowledge base + web search</p>', 
        unsafe_allow_html=True
    )


# ============================================================================
# Sidebar
# ============================================================================

with st.sidebar:
    st.header("📊 System Status")
    
    health = st.session_state.backend_health
    
    if health.get("status") == "healthy":
        st.success("✅ Backend Connected")
        
        with st.expander("View Details"):
            services = health.get("services", {})
            st.write("**API Keys:**")
            st.write(f"- OpenAI: {'✓' if services.get('openai') else '✗'}")
            st.write(f"- Tavily: {'✓' if services.get('tavily') else '✗'}")
            st.write(f"- LangSmith: {'✓' if services.get('langsmith') else '✗'}")
            
            kb = health.get("knowledge_base", {})
            st.write("**Knowledge Base:**")
            st.write(f"- Loaded: {'✓' if kb.get('loaded') else '✗'}")
            st.write(f"- Chunks: {kb.get('chunks', 0)}")
    else:
        st.error("❌ Backend Disconnected")
        st.write(f"Error: {health.get('error', 'Unknown')}")
        st.code("python -m backend.app.main", language="bash")
    
    if st.button("🔄 Refresh Status", use_container_width=True):
        st.session_state.backend_health = check_backend_health()
        st.rerun()
    
    st.divider()
    
    # Statistics
    stats = get_backend_stats()
    if stats:
        st.header("📈 Statistics")
        kb_stats = stats.get("knowledge_base", {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("KB Chunks", kb_stats.get("total_chunks", 0))
        with col2:
            st.metric("RAG", "✓" if kb_stats.get("vectorstore_ready") else "✗")
        
        features = stats.get("features", {})
        st.write("**Features:**")
        st.write(f"- Local KB: {'✓' if features.get('rag_enabled') else '✗'}")
        st.write(f"- Web Search: {'✓' if features.get('web_search_fallback') else '✗'}")
        st.write(f"- Tracing: {'✓' if features.get('langsmith_tracing') else '✗'}")
        
        st.divider()
    
    # Example Questions
    st.header("💡 Example Questions")
    examples_data = get_example_questions()
    
    if examples_data.get("categories"):
        for category in examples_data["categories"]:
            with st.expander(f"📁 {category['name']}"):
                for example in category["examples"]:
                    if st.button(example, key=f"cat_{example}", use_container_width=True):
                        st.session_state.pending_message = example
                        st.rerun()
    else:
        for i, example in enumerate(examples_data.get("examples", [])[:6]):
            if st.button(example, key=f"ex_{i}", use_container_width=True):
                st.session_state.pending_message = example
                st.rerun()
    
    st.divider()
    
    # Settings
    st.header("⚙️ Settings")
    st.session_state.show_metadata = st.checkbox(
        "Show metadata (tools used)",
        value=st.session_state.show_metadata
    )
    
    st.divider()
    
    # Actions
    st.header("🎛️ Actions")
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.caption("Powered by LangGraph + OpenAI + RAG")


# ============================================================================
# Main Chat Interface
# ============================================================================

# Display chat messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.write(msg["content"])
    
    elif msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="⌚"):
            st.write(msg["content"])
            
            # Show metadata if enabled
            if st.session_state.show_metadata and "metadata" in msg:
                metadata = msg["metadata"]
                
                if metadata.get("tools_used"):
                    st.markdown("**Tools used:**")
                    tools_html = ""
                    
                    if metadata.get("used_local_kb"):
                        tools_html += '<span class="tool-badge tool-kb">📚 Local KB</span>'
                    
                    if metadata.get("used_web_search"):
                        tools_html += '<span class="tool-badge tool-web">🌐 Web Search</span>'
                    
                    st.markdown(tools_html, unsafe_allow_html=True)


# ============================================================================
# Handle User Input
# ============================================================================

def process_message(user_input: str):
    """Process user message and get response"""
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Get conversation history (excluding the message we just added)
    history = [{"role": m["role"], "content": m["content"]} 
               for m in st.session_state.messages[:-1]]
    
    # Get response
    response = send_message(user_input, history)
    
    if response["success"]:
        data = response["data"]
        st.session_state.messages.append({
            "role": "assistant",
            "content": data["response"],
            "metadata": {
                "tools_used": data.get("tools_used", []),
                "used_local_kb": data.get("used_local_kb", False),
                "used_web_search": data.get("used_web_search", False)
            }
        })
    else:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ {response['error']}"
        })


# Handle pending message from example buttons
if "pending_message" in st.session_state:
    user_input = st.session_state.pending_message
    del st.session_state.pending_message
    
    with st.spinner("🤔 Thinking..."):
        process_message(user_input)
    st.rerun()


# Chat input
if health.get("status") != "healthy":
    st.error("⚠️ Backend is not connected. Please start the backend server:")
    st.code("cd backend && python -m app.main", language="bash")
else:
    user_input = st.chat_input("Ask me anything about Watch OS 26...")
    
    if user_input:
        with st.spinner("🤔 Searching and thinking..."):
            process_message(user_input)
        st.rerun()


# ============================================================================
# Footer
# ============================================================================

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.caption("💡 **Tip:** Ask specific questions for better answers")

with col2:
    st.caption("🔍 **Source:** Local KB → Web Search fallback")

with col3:
    if st.session_state.messages:
        st.caption(f"💬 **Messages:** {len(st.session_state.messages)}")
