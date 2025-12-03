import requests
import time

# Quick test script to verify server response
url = "http://127.0.0.1:8080/completions"
payload = {"prompt": "Hello from test", "max_tokens": 32}

try:
    t0 = time.time()
    r = requests.post(url, json=payload, timeout=20)
    print("Status:", r.status_code)
    print(r.json() if r.status_code == 200 else r.text)
    print("Elapsed:", time.time() - t0)
except Exception as e:
    print("Request failed:", e)
