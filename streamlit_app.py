import streamlit as st
import requests
import json
import time

# --- Configuration ---
API_URL = "http://127.0.0.1:8000/api/v1"
HEALTH_URL = "http://127.0.0.1:8000/health"

st.set_page_config(
    page_title="GraphRAG Agent", 
    page_icon="🕸️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Production Polish ---
st.markdown("""
<style>
    /* 1. FORCE DARK THEME BACKGROUNDS */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    
    /* 2. SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #2D3748;
    }
    
    /* 3. FIX INVISIBLE LABELS & TEXT */
    /* Target all labels in sidebar and main area */
    .stTextInput label, .stSlider label, .stNumberInput label {
        color: #E6E6E6 !important;
        font-weight: 600;
        font-size: 14px;
    }
    
    /* Fix Input Box Text Color (The "e.g. What is Agentic AI?" text) */
    .stTextInput input {
        color: #FFFFFF !important;
        background-color: #0D1117 !important;
        border: 1px solid #4F8BF9 !important; 
    }
    
    /* Fix Placeholder Text opacity */
    ::placeholder {
        color: #A0AEC0 !important;
        opacity: 1 !important; 
    }

    /* 4. FIX TOOLTIP ICON & HELP TEXT */
    /* The small question mark circle */
    [data-testid="stTooltipIcon"] {
        color: #4F8BF9 !important; /* Bright Blue Icon */
    }
    /* The actual tooltip popup text - Forces Black Text on White Background */
    div[data-baseweb="tooltip"] {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #4F8BF9;
    }
    div[data-baseweb="tooltip"] p {
        color: #000000 !important;
    }

    /* 5. BUTTON STYLING */
    /* "Start Ingestion" Button */
    div.stButton > button:first-child {
        background-color: #4F8BF9 !important; /* Bright Blue Background */
        color: #FFFFFF !important;             /* White Text */
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease-in-out;
    }
    
    div.stButton > button:first-child:hover {
        background-color: #357ABD !important;
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        color: #FFFFFF !important;
    }
    
    /* "Clear Chat" Button */
    div.stButton > button:active {
        color: #FFFFFF !important;
    }

    /* 6. CHAT INTERFACE */
    .stChatMessage {
        background-color: #262730;
        border-radius: 12px;
        padding: 12px;
        border: 1px solid #363B47;
    }
    
    /* User Message distinct style */
    div[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #1A202C;
        border: 1px solid #2D3748;
    }
    
    /* 7. BOTTOM CHAT INPUT (Fixing the "Ask a question" bar) */
    .stChatInput textarea {
        background-color: #1A202C !important; /* Dark Blue-Grey Background */
        color: #FFFFFF !important;             /* White Text */
        border: 1px solid #4F8BF9 !important;  /* Blue Border */
    }
    
    /* 8. HEADERS & TEXT */
    h1, h2, h3, h4, h5, h6, p, li, span {
        color: #E6E6E6 !important;
        font-family: 'Inter', sans-serif;
    }
    h1 { color: #4F8BF9 !important; } /* Keep Title Blue */
    
</style>
""", unsafe_allow_html=True)

# --- 1. Sidebar: Knowledge & Controls ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
    st.title("Control Panel")
    
    st.markdown("### 📚 Knowledge Ingestion")
    
    # Using a container for the form elements
    with st.container():
        query_input = st.text_input(
            "Topic to Research:", 
            placeholder="e.g. What is Agentic AI?",
            help="Enter a topic. The system will search Google, scrape top results, and build a Knowledge Graph."
        )
        
        # Slider with visible labels
        num_results = st.slider(
            "Websites to Scrape:", 
            min_value=1, 
            max_value=5, 
            value=2,
            help="More websites = deeper knowledge but slower ingestion."
        )
        
        # Proper Vertical Spacing (Fixes the "br" text issue)
        st.markdown("<br>", unsafe_allow_html=True) 
        
        # THE BUTTON (Blue with White Text)
        if st.button("🚀 Start Ingestion Pipeline", use_container_width=True):
            if not query_input:
                st.warning("⚠️ Please enter a topic first.")
            else:
                with st.spinner(f"🔍 Searching & Scraping {num_results} sources..."):
                    try:
                        payload = {"query": query_input, "num_results": num_results}
                        res = requests.post(f"{API_URL}/ingest", json=payload, timeout=20)
                        
                        if res.status_code == 200:
                            data = res.json()
                            task_id = data.get("task_id", "Unknown")
                            st.success(f"✅ Pipeline Active! Task: `{task_id}`")
                            st.info("Building graph... Check backend logs.")
                        else:
                            st.error(f"❌ Error: {res.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Backend Offline. Is `main.py` running?")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    st.markdown("---")
    
    # System Health Check
    st.markdown("### 🖥️ System Status")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄", key="refresh_btn"): 
            st.rerun()
            
    with col2:
        try:
            # Short timeout for health check
            health = requests.get(HEALTH_URL, timeout=1)
            if health.status_code == 200:
                st.markdown("🟢 **API Online**")
            else:
                st.markdown("🔴 **API Error**")
        except:
            st.markdown("🔴 **API Offline**")

    # Clear Chat History Button
    st.markdown("### ⚙️ Settings")
    if st.button("🗑️ Clear Chat History", use_container_width=True, key="clear_btn"):
        st.session_state.messages = []
        st.rerun()

# --- 2. Main Chat Interface ---
st.title("🕸️ Graph RAG Agent")
st.markdown("""
    *Ask complex questions based on the knowledge graph you built.  
    The agent retrieves concepts, relationships, and context to answer.*
""")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am connected to your Neo4j Knowledge Graph. What would you like to know?"}
    ]

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input Handling
if prompt := st.chat_input("Ask a question about your data..."):
    # 1. Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate Assistant Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Stream from Backend
            with requests.post(f"{API_URL}/chat/stream", json={"message": prompt}, stream=True, timeout=60) as r:
                if r.status_code == 200:
                    for chunk in r.iter_content(chunk_size=None):
                        if chunk:
                            try:
                                text = chunk.decode("utf-8")
                                full_response += text
                                message_placeholder.markdown(full_response + "▌")
                            except:
                                pass 
                    
                    message_placeholder.markdown(full_response)
                else:
                    error_msg = f"❌ API Error {r.status_code}: {r.text}"
                    message_placeholder.error(error_msg)
                    full_response = error_msg
                    
        except requests.exceptions.ConnectionError:
            error_msg = "❌ Connection Refused. Is the backend running on port 8000?"
            message_placeholder.error(error_msg)
            full_response = error_msg
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            message_placeholder.error(error_msg)
            full_response = error_msg

    # 3. Save Assistant Message
    st.session_state.messages.append({"role": "assistant", "content": full_response})