import json
import os

filepath = os.path.join("processed", "01_motivation", "analysis.json")

# 1. 파일 로드
with open(filepath, "r", encoding="utf-8") as f:
    data = json.load(f)

# 2. 모든 문장의 lecture_script를 빈 문자열로 초기화 (1번 문장 포함 모두 제거)
for s in data["sentences"]:
    s["lecture_script"] = ""

# 3. 파일 저장
with open(filepath, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Successfully cleared all lecture_scripts in analysis.json!")
