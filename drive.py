import json, os

DATA_FILE = "flashcards.json"

def load_flashcards() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_flashcards(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)