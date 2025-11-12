---
description: "README"
---

# RIZZK Calculator

RIZZK Calculator (pronounced "Rizz-k") — sharp, refined position-sizing for traders who think in probabilities and move with style.

Author: Fuaad Abdullah

## Live Demo

🚀 [Try the live demo here](https://rr-calculator-2tywogeksqdgr4hf4jzssm.streamlit.app/)

## What this is

- Edgy, polished Streamlit app to compute position size, stop-loss impact, and profit targets. Built for traders who want clean numbers without the fluff.

## Key Features

- Position sizing from account size and risk %
- Long and short support
- 1:1 and 2:1 profit targets
- Downloadable CSV of results
- Calculation history stored in session
- Input validation and clear feedback
- Clean UI with charts and metrics

## Local Development

If you want to run locally:

```bash
pip install -r requirements.txt
# Entrypoint at repo root delegates to the package app
streamlit run app.py
```

## Usage

Fill the inputs: account size, risk %, entry, stop. Hit Calculate. Export CSV if you want to log the trade.

## Testing

Run unit tests:

```bash
pytest
```

Tests live under `risk_reward_calculator/`.

## Deployment

Two easy paths:

- Azure App Service (no container):
  - Set runtime to Python 3.11
  - Deploy this folder with `requirements.txt` present
  - Startup command: `python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0`

- Container (Azure Web App for Containers, ACI, ECS):
  - Build using the Dockerfile in the package directory as build context:

    ```bash
    docker build -t rizzk:latest -f risk_reward_calculator/Dockerfile risk_reward_calculator
    docker run -p 8501:8501 rizzk:latest
    ```

  - Push to a registry (e.g., ACR) and point your service at the image

Note: The app expects no secrets; `EDGY_MODE_DEFAULT` env can optionally be set to `true`/`false` to toggle the default UI mode.

## Tech

- Python 3.11
- Streamlit
- Pandas

## Tone

RIZZK is designed to be direct and pragmatic — modern, confident, and professional with an edge.

## License

MIT
