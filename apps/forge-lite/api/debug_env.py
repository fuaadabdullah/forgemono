import os
from pathlib import Path
from dotenv import load_dotenv

script_file = os.path.abspath(__file__)
script_dir = Path(script_file).parent
env_path = script_dir.parent / '.env.local'

print('Script file:', script_file)
print('Script dir:', script_dir)
print('Env path:', env_path)
print('Env exists:', env_path.exists())

# Clear existing env vars
if 'FINNHUB_API_KEY' in os.environ:
    del os.environ['FINNHUB_API_KEY']
if 'ALPHA_VANTAGE_API_KEY' in os.environ:
    del os.environ['ALPHA_VANTAGE_API_KEY']

print('Before load_dotenv:')
print('FINNHUB_API_KEY:', repr(os.getenv('FINNHUB_API_KEY')))

# Try loading
result = load_dotenv(dotenv_path=env_path, override=True)
print('Load result:', result)

print('After load_dotenv:')
print('FINNHUB_API_KEY:', repr(os.getenv('FINNHUB_API_KEY')))
