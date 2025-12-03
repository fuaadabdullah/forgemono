# Colab llama.cpp Deployment Guide

## 🚀 Quick Deploy to Google Colab

### Option 1: Direct Upload (Recommended)

1. **Open Google Colab**: Go to [https://colab.research.google.com/](https://colab.research.google.com/)

2. **Upload the notebook**:
   - Click `File` → `Upload notebook`
   - Select: `notebooks/colab_llamacpp_setup.ipynb` from your local machine
   - Or drag and drop the file into Colab

3. **Run the setup**:
   - Run cells 1-7 in order to set up llama.cpp and download the model
   - Run cell 8 to start the server with ngrok tunnel
   - Copy the public ngrok URL that appears in the output

### Option 2: GitHub Integration

If you have the notebook in a GitHub repository:

1. **Open Colab**: [https://colab.research.google.com/](https://colab.research.google.com/)

2. **Load from GitHub**:
   - Click `File` → `Open notebook`
   - Select `GitHub` tab
   - Enter your repository URL
   - Select the `colab_llamacpp_setup.ipynb` file

### Option 3: Direct Colab Link (if uploaded to Drive)

Once uploaded to Google Colab, your notebook will have a URL like:

```text
https://colab.research.google.com/drive/YOUR_NOTEBOOK_ID_HERE
```

Share this link with others for instant access.

## 🔧 Configuration

### ngrok Setup (for public access)

1. **Get ngrok token**: Sign up at [ngrok.com](https://ngrok.com) and get your auth token

2. **Add to Colab**: In cell 3 of the notebook, uncomment and add your token:

```bash
!ngrok config add-authtoken YOUR_NGROK_TOKEN_HERE
```

### Model Selection

Edit cell 5 to choose your model:

```python
MODEL_REPO = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"  # Change this
MODEL_FILENAME = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"  # And this
```

## 🧪 Testing Your Deployment

Once the server is running, test it with:

```bash
# Test connectivity
python3 scripts/test_llamacpp_server.py --server-url https://your-ngrok-url.ngrok.io

# Run benchmarks
python3 scripts/benchmark_llamacpp.py --server-url https://your-ngrok-url.ngrok.io --threads 1,2,4
```

## 📊 Performance Optimization

- **Use Colab Pro** for better GPU/CPU resources
- **Choose smaller models** (Q2_K, Q3_K_S) for faster inference
- **Adjust thread count** based on Colab's CPU cores (usually 2-8)
- **Monitor memory usage** in Colab's resource monitor

## 🔗 Integration with Goblin Assistant

This Colab deployment integrates with your multi-LLM routing setup:

- **Ollama**: Remote model via API
- **llama.cpp (Colab)**: Public tunnel access
- **LMStudio**: Local GUI deployment

Use the routing logic in `goblin-assistant/` to switch between deployments.

## 🆘 Troubleshooting

### Common Issues

1. **"Model not found"**: Check the HuggingFace model repo and filename
2. **"ngrok tunnel failed"**: Verify your ngrok token and account limits
3. **"Out of memory"**: Use smaller quantization or Colab Pro
4. **"Build failed"**: Check Colab's system resources and try again

### Getting Help

- Check the server logs in Colab output
- Use `!top` or `!htop` in Colab to monitor resources
- Test with smaller models first (TinyLlama, Phi-2)

## 🔗 API Integration with Goblin Assistant

After deploying to Colab, integrate with your Goblin Assistant backend:

### 1. Configure Provider

```bash
# Update the backend configuration
python3 scripts/configure_colab_llamacpp.py \
  --ngrok-url "https://your-ngrok-url.ngrok.io" \
  --model "tinyllama-1.1b-chat-v1.0.Q4_K_M"

You can also configure KPI reporting for the provider. For example, to add Datadog KPIs:

```bash
python3 scripts/configure_colab_llamacpp.py \
   --ngrok-url "https://your-ngrok-url.ngrok.io" \
   --model "tinyllama-1.1b-chat-v1.0.Q4_K_M" \
   --kpi-provider datadog \
   --kpi-api-env LLAMACPP_COLAB_DATADOG_API_KEY \
   --kpi-endpoint https://api.datadoghq.com/api/v1/series \
   --kpi-metric-prefix goblin.llamacpp_colab \
   --kpi-tags env:colab,region:colab
```
```

### 2. Restart Backend

```bash
cd goblin-assistant/api
python start_server.py
```

### 3. Test Integration

```bash
# Test the full integration
python3 scripts/test_goblin_colab_integration.py --backend-url http://localhost:8000
```

### 4. Use in Applications

The routing system will automatically use the Colab deployment for supported tasks:

```python
import requests

# Route through Goblin Assistant
response = requests.post("http://localhost:8000/routing/route", json={
    "task_type": "chat",
    "payload": {
        "messages": [{"role": "user", "content": "Hello from Colab!"}]
    }
})
```

