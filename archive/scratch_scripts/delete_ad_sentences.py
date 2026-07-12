import json
import os

filepath = os.path.join("processed", "01_motivation", "analysis.json")

# 1. 로컬 파일 로드
with open(filepath, "r", encoding="utf-8") as f:
    data = json.load(f)

# 2. 40번 이상의 광고 문장들 제외하기 (index 1 ~ 39까지만 유지)
original_count = len(data["sentences"])
data["sentences"] = [s for s in data["sentences"] if s["index"] <= 39]
new_count = len(data["sentences"])

# 3. 로컬 파일 저장
with open(filepath, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Successfully deleted advertisement sentences from analysis.json!")
print(f"Sentence count changed from {original_count} to {new_count}")
