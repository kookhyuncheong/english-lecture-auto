import json
import os

analysis_path = os.path.join("processed", "01_motivation", "analysis.json")

with open(analysis_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for sentence in data.get("sentences", []):
    if "index" in sentence:
        del sentence["index"]

with open(analysis_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Removed index from analysis.json successfully!")
