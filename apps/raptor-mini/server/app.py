# server/app.py
import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx

API_KEY = os.getenv("API_KEY", "")  # required for requests
MODEL_PATH = os.getenv("MODEL_PATH", "/models/raptor-mini")
PORT = int(os.getenv("PORT", "8080"))
MODEL_NAME = os.getenv("MODEL_NAME", "mistral:latest")  # Use available model

# Configure Ollama client to connect to the Ollama service
OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST", "http://172.17.0.1:11434"
)  # Docker bridge gateway
os.environ["OLLAMA_HOST"] = OLLAMA_HOST

app = FastAPI(title="Raptor-Mini Service")


# Ollama client for Raptor Mini
class InferenceRunner:
    def __init__(self, model_name: str, ollama_host: str = "http://172.17.0.1:11434"):
        self.model_name = model_name
        self.ollama_host = ollama_host
        self.client = httpx.AsyncClient(base_url=self.ollama_host, timeout=30.0)
        # Verify model is available
        try:
            response = httpx.get(f"{self.ollama_host}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                if self.model_name not in model_names:
                    print(
                        f"Warning: Model {self.model_name} not found. Available: {model_names}"
                    )
                else:
                    print(f"Model {self.model_name} is available")
            else:
                print(f"Warning: Cannot connect to Ollama API: {response.status_code}")
        except Exception as e:
            print(f"Warning: Ollama not available: {e}")

    async def infer(self, prompt: str, max_tokens: int = 128):
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7,
                },
                "stream": False,
            }
            response = await self.client.post("/api/generate", json=payload)
            if response.status_code == 200:
                result = response.json()
                return {"response": result.get("response", "")}
            else:
                return {
                    "error": f"Ollama API error: {response.status_code} - {response.text}"
                }
        except Exception as e:
            return {"error": f"Inference failed: {str(e)}"}


runner = InferenceRunner(MODEL_NAME, OLLAMA_HOST)


class InferenceRequest(BaseModel):
    prompt: str
    max_tokens: int = 128


def check_api_key(x_api_key: str | None):
    if not API_KEY:
        # dev-mode: allow if no API_KEY configured
        return
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/health")
async def health():
    return {"ok": True, "model": MODEL_NAME, "service": "raptor-mini"}


@app.post("/v1/generate")
async def generate(req: InferenceRequest, x_api_key: str | None = Header(None)):
    check_api_key(x_api_key)
    # real inference here
    out = await runner.infer(req.prompt, max_tokens=req.max_tokens)
    return JSONResponse({"ok": True, "result": out})


# simple root ping
@app.get("/")
async def root():
    return {"service": "raptor-mini", "model": MODEL_NAME, "ok": True}
