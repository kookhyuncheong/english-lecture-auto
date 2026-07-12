import json
import os

filepath = os.path.join("processed", "01_motivation", "analysis.json")

# 1. 파일 로드
with open(filepath, "r", encoding="utf-8") as f:
    data = json.load(f)

# 2. vocab_2 (loom) 오브젝트 정의
vocab_2 = {
  "id": "vocab_2",
  "word": "loom",
  "base_word": "loom",
  "level": "C1",
  "meaning": "(중요하거나 위협적인 일이) 곧 닥칠 것처럼 보이다",
  "english_definition": "to appear important or threatening and likely to happen soon",
  "english_definition_translation": "중요하거나 위협적으로 보이며 곧 일어날 것 같다",
  "sentence_index": 3,
  "sentence_text": "But as the application deadline looms, you suddenly find yourself unmotivated and avoiding the canvas altogether.",
  "explanation": "이 문장에서는 '마감일이 코앞으로 다가왔을 때' 느껴지는 심리적 압박감을 생생하게 표현하기 위해 'deadline looms'라는 아주 자연스럽고 강렬한 원어민 콜로케이션 표현으로 사용되었습니다.",
  "patterns": [
    {
      "pattern": "loom",
      "pattern_translation": "(위협적인 일이) 곧 닥치다 / 코앞으로 다가오다",
      "examples": [
        {
          "eng": "The application deadline looms.",
          "kor": "지원 마감일이 코앞으로 다가왔다."
        },
        {
          "eng": "There is a crisis looming.",
          "kor": "위기가 서서히 다가오고 있다."
        }
      ]
    }
  ],
  "ab_dialogue": {
    "situation": "시험 기간을 앞두고 걱정하는 두 친구의 대화",
    "dialogue_a": "The final exams are looming, and I haven't even started studying.",
    "dialogue_b": "Don't panic. Let's make a study plan together.",
    "translation_a": "기말고사가 코앞으로 다가왔는데, 나 아직 공부 시작도 안 했어.",
    "translation_b": "당황하지 마. 같이 공부 계획을 짜보자.",
    "audio_path": "/processed/01_motivation/audio/vocab_dialogue_vocab_2.wav"
  }
}

# 3. 중복 방지하며 추가
if "global_vocab_list" not in data:
    data["global_vocab_list"] = []

# id가 'vocab_2'인 항목이 이미 있으면 업데이트하고, 없으면 추가
existing_index = -1
for i, v in enumerate(data["global_vocab_list"]):
    if v["id"] == "vocab_2":
        existing_index = i
        break

if existing_index != -1:
    data["global_vocab_list"][existing_index] = vocab_2
    print("Updated existing vocab_2 in analysis.json")
else:
    data["global_vocab_list"].append(vocab_2)
    print("Added new vocab_2 to analysis.json")

# 4. 파일 저장
with open(filepath, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Successfully synced loom (vocab_2) in analysis.json!")
