import json
import os

analysis_path = os.path.join("processed", "01_motivation", "analysis.json")

with open(analysis_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for sentence in data.get("sentences", []):
    idx = sentence.get("index")
    # 3-digit video id, 3-digit sentence index: S-001-XXX
    sentence["id"] = f"S-001-{str(idx).zfill(3)}"
    sentence["video_id"] = "01_motivation"

with open(analysis_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Updated analysis.json to use 3-digit formatting (S-001-XXX) successfully!")
