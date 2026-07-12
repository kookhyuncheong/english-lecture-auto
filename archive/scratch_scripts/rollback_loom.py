import json
import os

filepath = os.path.join("processed", "01_motivation", "analysis.json")

# 1. 로컬 파일 로드
with open(filepath, "r", encoding="utf-8") as f:
    data = json.load(f)

# 2. vocab_2 삭제
original_count = len(data.get("global_vocab_list", []))
data["global_vocab_list"] = [v for v in data.get("global_vocab_list", []) if v["id"] != "vocab_2"]
new_count = len(data["global_vocab_list"])

# 3. 로컬 파일 저장
with open(filepath, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Rollback local analysis.json complete. Vocab count: {original_count} -> {new_count}")
