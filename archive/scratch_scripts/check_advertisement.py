import json
import os

filepath = os.path.join("processed", "01_motivation", "analysis.json")
with open(filepath, "r", encoding="utf-8") as f:
    data = json.load(f)

outpath = os.path.join("scratch", "check_advertisement.txt")
with open(outpath, "w", encoding="utf-8") as f:
    f.write("=== Last 15 Sentences in analysis.json ===\n\n")
    for s in data["sentences"][-15:]:
        f.write(f"Index {s['index']}: {s['english_text']}\n")
        f.write(f"       Translation: {s['korean_text']}\n\n")

print("Successfully written check_advertisement.txt!")
