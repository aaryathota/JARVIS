import json

FILE = "memory.json"

def load():
    try:
        with open(FILE) as f:
            return json.load(f)
    except:
        return {}

def save(mem):
    with open(FILE, "w") as f:
        json.dump(mem, f)

def remember(key, value):
    mem = load()
    mem[key] = value
    save(mem)

def recall(key):
    return load().get(key)