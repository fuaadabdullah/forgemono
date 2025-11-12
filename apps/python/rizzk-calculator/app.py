"""
Deployment entrypoint for Streamlit.

This shim imports and executes the real app located in
`risk_reward_calculator/app.py` so platforms that expect a top-level
`app.py` (Azure App Service, Render, etc.) can run `streamlit run app.py`.
"""

# Importing the module executes the Streamlit script at import time.
# Do not add any extra logic here.
from risk_reward_calculator import app as _rizzk_app  # noqa: F401

