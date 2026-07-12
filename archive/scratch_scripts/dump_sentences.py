import json
import os

filepath = os.path.join("processed", "01_motivation", "analysis.json")
with open(filepath, "r", encoding="utf-8") as f:
    data = json.load(f)

outpath = os.path.join("scratch", "source_sentences.txt")
with open(outpath, "w", encoding="utf-8") as f:
    for s in data["sentences"]:
        f.write(f"Index {s['index']}: {s['english_text']}\n")
        f.write(f"       Old Translation: {s['korean_text']}\n\n")

print("Successfully written source_sentences.txt!")
