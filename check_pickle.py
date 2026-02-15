import pickle
from pathlib import Path

p = Path("models/gita_embeddings.pkl")
if not p.exists():
    print("File not found.")
else:
    with open(p, "rb") as f:
        data = pickle.load(f)
        print(f"Model Name in Pickle: {data.get('model_name')}")
