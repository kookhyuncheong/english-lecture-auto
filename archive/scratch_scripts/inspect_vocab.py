import json
import os

filepath = os.path.join("processed", "01_motivation", "analysis.json")
with open(filepath, "r", encoding="utf-8") as f:
    data = json.load(f)

outpath = os.path.join("scratch", "vocab_inspect.json")
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(data.get("global_vocab_list", []), f, ensure_ascii=False, indent=2)

print("Successfully written vocab_inspect.json!")
