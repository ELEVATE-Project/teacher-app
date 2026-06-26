import os
import requests
from dotenv import load_dotenv, find_dotenv

# Load .env
load_dotenv(find_dotenv())

# Get settings
base_url = os.getenv("RAGFLOW_BASE_URL", os.getenv("RAGFLOW_API_URL", "http://localhost:5001")).rstrip("/")
api_key = os.getenv("RAGFLOW_API_KEY", os.getenv("RAGFLOW_CLIENT_ID", ""))
dataset_id = os.getenv("RAGFLOW_DATASET_ID", "")

print("Testing RAGFlow connection...")
print("URL:", base_url)
print("API Key:", api_key[:15] + "..." if api_key else "None")
print("Dataset ID:", dataset_id)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 1. Health check
print("\n[1] Checking system health...")
try:
    resp = requests.get(f"{base_url}/api/v1/system/healthz", timeout=10)
    print("Health Status Code:", resp.status_code)
    print("Response Body:", resp.text)
except Exception as e:
    print("Health check failed:", e)

# 2. List datasets
print("\n[2] Checking dataset retrieval...")
try:
    resp = requests.get(f"{base_url}/api/v1/datasets", headers=headers, timeout=10)
    print("Datasets Status Code:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        datasets = data.get("data", [])
        if isinstance(datasets, dict):
            datasets = datasets.get("datasets", [])
        print("Connected successfully! Number of datasets found:", len(datasets))
        for d in datasets:
            print(f" - Dataset Name: {d.get('name')} | ID: {d.get('id')}")
    else:
        print("Datasets failed response:", resp.text)
except Exception as e:
    print("Datasets check failed:", e)

# 3. Test retrieval with query variations
d_id = "0badb70a688e11f1a49727756bfeeac2"
queries = [
    "Class_7 Geography Air in English (NCERT board)",
    "Class 7 Geography Air",
    "Class 7 Air",
    "Air"
]

for query in queries:
    print(f"\nTesting query variation: '{query}'...")
    try:
        payload = {
            "question": query,
            "dataset_ids": [d_id],
            "top_k": 3,
            "similarity_threshold": 0.1
        }
        resp = requests.post(f"{base_url}/api/v1/retrieval", headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            chunks = resp.json().get("data", [])
            if isinstance(chunks, dict):
                chunks = chunks.get("chunks", [])
            print(f" -> Retrieved {len(chunks)} chunks!")
            if chunks:
                print(f"    First chunk: '{chunks[0].get('content')[:120].strip()}...'")
        else:
            print(" -> Retrieval failed:", resp.text)
    except Exception as e:
        print(" -> Query failed:", e)
