import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def print_pass(msg):
    print(f"✅ PASS: {msg}")

def print_fail(msg):
    print(f"❌ FAIL: {msg}")
    sys.exit(1)

def verify_full_pipeline():
    print("🚀 Starting Full System Verification...\n")

    # 1. Health Check
    try:
        r = requests.get("http://localhost:8000/health")
        if r.status_code == 200:
            print_pass("API is reachable")
        else:
            print_fail(f"API Health Check failed: {r.text}")
    except Exception as e:
        print_fail(f"API is down. Is uvicorn running? Error: {e}")

    # 2. Trigger Ingestion (Phase 1, 2, 3)
    # We use a unique topic to ensure we are testing fresh ingestion
    query_topic = "What is Retrieval Augmented Generation?"
    print(f"\n📡 Triggering Ingestion for: '{query_topic}'...")
    
    payload = {"query": query_topic, "num_results": 1}
    r = requests.post(f"{BASE_URL}/ingest", json=payload)
    
    if r.status_code != 200:
        print_fail(f"Ingest request failed: {r.text}")
    
    task_id = r.json().get("task_id")
    print_pass(f"Ingestion Task started with ID: {task_id}")

    # 3. Poll for Task Completion
    print("⏳ Waiting for Celery Worker (this may take 30-60s)...")
    status = "PENDING"
    while status in ["PENDING", "STARTED", "PROGRESS"]:
        time.sleep(5)
        r_status = requests.get(f"{BASE_URL}/ingest/status/{task_id}")
        data = r_status.json()
        status = data.get("status")
        
        meta = data.get("result", {})
        if isinstance(meta, dict) and "status" in meta:
            print(f"   ... Worker Status: {meta['status']}")
        else:
            print(f"   ... Task State: {status}")

    if status == "SUCCESS" or (isinstance(data.get("result"), dict) and data["result"].get("status") == "completed"):
        print_pass("Ingestion Pipeline Completed Successfully!")
    else:
        print_fail(f"Ingestion Failed. Final State: {status}. Response: {data}")

    # 4. Test Chat (Phase 4)
    # Now we ask the chatbot about the data we just ingested
    print(f"\n💬 Testing Chatbot with RAG...")
    chat_payload = {"message": "Explain RAG simply."}
    
    # We use stream=True to handle the streaming endpoint
    with requests.post(f"{BASE_URL}/chat/stream", json=chat_payload, stream=True) as r:
        if r.status_code == 200:
            print("   Chat Response: ", end="")
            full_response = ""
            for chunk in r.iter_content(chunk_size=None):
                if chunk:
                    text = chunk.decode("utf-8")
                    print(text, end="", flush=True)
                    full_response += text
            print("\n")
            
            if len(full_response) > 10:
                print_pass("Chatbot returned a valid response.")
            else:
                print_fail("Chatbot response was too empty.")
        else:
            print_fail(f"Chat request failed: {r.status_code} {r.text}")

    print("\n🎉🎉🎉 SYSTEM VERIFICATION COMPLETE! READY FOR FRONTEND. 🎉🎉🎉")

if __name__ == "__main__":
    verify_full_pipeline()