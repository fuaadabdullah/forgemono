from pathlib import Path
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "providers.toml"
print('CONFIG_PATH:', CONFIG_PATH)
print('Exists:', CONFIG_PATH.exists())
print('__file__:', __file__)
print('resolve():', Path(__file__).resolve())
print('parents[0]:', Path(__file__).resolve().parents[0])
print('parents[1]:', Path(__file__).resolve().parents[1])
print('parents[2]:', Path(__file__).resolve().parents[2])
