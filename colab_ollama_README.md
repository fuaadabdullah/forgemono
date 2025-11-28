# Ollama Colab Setup - Quick Reference

## 🚀 One-Click Setup

Open this notebook in Google Colab:
[https://colab.research.google.com/github/fuaadabdullah/ForgeMonorepo/blob/main/colab_ollama_setup.ipynb](https://colab.research.google.com/github/fuaadabdullah/ForgeMonorepo/blob/main/colab_ollama_setup.ipynb)

## 📋 What It Does

1. Mounts Google Drive for persistent model storage
2. Installs Ollama in Colab VM
3. Configures Ollama to use Drive for models
4. Downloads lightweight models (qwen2.5:3b, deepseek-coder:1.3b, gemma:2b)
5. Starts Ollama server
6. Creates public tunnel with ngrok (or Pinggy as backup)
7. Provides Goblin Assistant integration config

## 🎯 Perfect For

- AI demos and prototypes
- Testing Ollama models quickly
- Development without local setup
- Learning and experimentation

## ⚠️ Important Notes

- Colab sessions timeout (~90 min idle, ~12 hr max)
- Free tier has resource limits - use small models
- Not for production use
- Models persist in Google Drive between sessions

## 🔧 Quick Start Commands

1. Run cells 1-4 (Drive mount, Ollama install, config)
2. Run cell 5 (download models - modify list as needed)
3. Run cell 6 (start Ollama server)
4. Run cell 7 (setup ngrok tunnel - add your auth token!)
5. Run cell 9 (get Goblin Assistant config)

## 🌐 Public Access

- Copy the ngrok URL from cell 7 output
- Use this URL in your Goblin Assistant config
- API endpoint: `https://your-ngrok-url.ngrok.io/v1/chat/completions`

## 💡 Pro Tips

- Use Colab Pro for longer sessions and more resources
- Start with small models (3B parameters or less)
- Keep the Colab tab active to prevent timeouts
- Models download to Drive, so they're reusable!</content>
<parameter name="filePath">/Users/fuaadabdullah/ForgeMonorepo/colab_ollama_README.md
