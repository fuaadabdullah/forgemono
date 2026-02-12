import os
import time


class LocalModelAdapter:
    name = "local_phi3"

    def __init__(
        self,
        model_path: str = "/models",
        model_name: str = "Phi-3-mini-4k.gguf",
        n_threads: int = 4,
        quantization: str = "auto",
        n_gpu_layers: int = 0,  # GPU layers for llama-cpp
    ):
        self.model_path = model_path
        self.model_name = model_name
        self.n_threads = n_threads
        self.quantization = quantization
        self.n_gpu_layers = n_gpu_layers
        self.client = None

    def init(self):
        try:
            import torch
            import llama_cpp

            model_file = os.path.join(self.model_path, self.model_name)

            # Configure GPU layers based on availability and quantization
            if self.quantization in ["int4", "int8"] and self.n_gpu_layers == 0:
                # For quantized models, enable GPU layers if available
                try:
                    if torch.cuda.is_available():
                        self.n_gpu_layers = -1  # Use all available layers on GPU
                except Exception:
                    pass

            self.client = llama_cpp.Llama(
                model_path=model_file,
                n_threads=self.n_threads,
                n_gpu_layers=self.n_gpu_layers,
                # Additional optimization for quantized models
                use_mmap=True,  # Memory mapping for faster loading
                use_mlock=False,  # Don't lock memory for quantized models
            )
        except Exception:
            self.client = None
            raise

    def health_check(self, timeout: float = 3.0) -> bool:
        if not self.client:
            return False
        try:
            start = time.time()
            response = self.client.create_completion(prompt="ping", max_tokens=1)
            return (time.time() - start) < timeout and bool(response.get("choices"))
        except Exception:
            return False

    def generate(self, prompt: str, max_tokens: int = 512, **kwargs):
        if not self.client:
            raise RuntimeError("client not initialized")
        return self.client.create_completion(
            prompt=prompt, max_tokens=max_tokens, **kwargs
        )

    def metadata(self):
        return {"name": self.name, "type": "local", "model": self.model_name}

    def shutdown(self):
        self.client = None
