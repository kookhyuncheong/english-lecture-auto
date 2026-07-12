import json
import os

filepath = os.path.join("processed", "01_motivation", "analysis.json")

# 1. 파일 로드
with open(filepath, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Original sentences: {len(data['sentences'])}")
print(f"Original global_vocab_list size: {len(data.get('global_vocab_list', []))}")

# 2. 정제 대상인 vocab_1 (aspire)만 남기고 global_vocab_list 필터링
# (개발자가 OALD 스펙으로 완성한 유일한 단어)
refined_vocab_ids = ["vocab_1"]
data["global_vocab_list"] = [v for v in data.get("global_vocab_list", []) if v["id"] in refined_vocab_ids]

# 3. 각 문장의 vocab_list 필터링 (sentence 1의 aspire만 남기고 나머지는 비움)
for s in data["sentences"]:
    if s["index"] == 1:
        # sentence 1의 vocab_list에서 C1 레벨의 aspire만 필터링 (professional 등 미가공 단어 제외)
        s["vocab_list"] = [v for v in s.get("vocab_list", []) if v["word"] == "aspire"]
    else:
        s["vocab_list"] = []

print(f"Cleaned global_vocab_list size: {len(data['global_vocab_list'])}")

# 4. 파일 저장
with open(filepath, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Successfully cleaned analysis.json!")
