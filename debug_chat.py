import logging
import sys
from app.services.chat_service import chat_service
from app.core.config import settings
from llama_index.core import Settings

# Setup Debug Logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()

def debug_rag_pipeline():
    print("🔧 STARTING DEBUG SESSION...")
    
    # 1. Test Graph Retrieval
    print("\n[1] Testing Graph Retrieval...")
    try:
        # Initialize engine to set up retriever
        chat_service._initialize_engine()
        
        query = "Explain RAG simply"
        # Access retriever from the chat engine context
        # Note: condense_plus_context puts the retriever in a tool or internal component
        # We will try to access the index directly from the service if possible, 
        # but since we can't easily, we will skip direct retrieval check 
        # and rely on the chat test which implicitly checks it.
        print("   ✅ Engine initialized. Skipping manual retrieval check (complex internal structure).")

    except Exception as e:
        print(f"   ❌ Engine Init Error: {e}")

    # 2. Test Full Chat Service
    print("\n[2] Testing Full Chat Service...")
    try:
        gen = chat_service.stream_chat("Explain RAG simply.")
        print("   > Stream started...")
        full_msg = ""
        for token in gen:
            # FIX: 'token' is a string, not an object
            print(token, end="", flush=True)
            full_msg += token
        print("\n")
        
        if not full_msg:
             print("   ❌ CHAT SERVICE FAILURE: Returned empty response.")
        else:
             print("   ✅ Chat Service Working.")

    except Exception as e:
        print(f"   ❌ Chat Service Error: {e}")

if __name__ == "__main__":
    debug_rag_pipeline()