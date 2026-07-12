import json
import os

file_path = "c:/Users/kookh/OneDrive/Desktop/english-lecture-auto/processed/01_motivation/analysis.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Update existing vocab_8
for vocab in data.get("global_vocab_list", []):
    if "explanation" in vocab:
        del vocab["explanation"]
    
    # Add source and equivalent_term to existing vocab
    if vocab.get("id") == "vocab_8":
        vocab["equivalent_term"] = "그 자체로 목적이 되는 것"
        vocab["source_video"] = "01강"
        vocab["source_sentence_index"] = 7
        vocab["level"] = "C2" # Assuming it's C2

for sentence in data.get("sentences", []):
    for vocab in sentence.get("vocab_list", []):
        if "explanation" in vocab:
            del vocab["explanation"]

# Create vocab_2 (loom)
vocab_2 = {
  "id": "vocab_2",
  "word": "loom",
  "target_phrase": "deadline looms",
  "base_word": "loom",
  "level": "C1",
  "equivalent_term": "다가오다, 임박하다",
  "meaning": "(불쾌하거나 두려운 일이) 다가오다, 임박하다",
  "english_definition": "to be close to happening : to be about to happen — used especially of unpleasant or frightening things",
  "english_definition_translation": "무언가가 일어날 때가 가까워지다, 곧 일어날 것 같다 — 특히 불쾌하거나 두려운 일에 대해 쓰임",
  "source_video": "01강",
  "source_sentence_index": 3,
  "sentence_text": "But as the application deadline looms, you suddenly find yourself unmotivated and avoiding the canvas altogether.",
  "patterns": [
    {
      "pattern": "loom (large/closer)",
      "pattern_translation": "(거대하게/점점 더) 다가오다",
      "examples": [
        {
          "eng": "The deadline looms closer with each passing day.",
          "kor": "마감일이 하루하루 점점 다가오고 있다."
        },
        {
          "eng": "A workers' strike is looming.",
          "kor": "노동자들의 파업이 임박했다."
        }
      ]
    }
  ],
  "ab_dialogue": {
    "situation": "회사에서 프로젝트 마감일을 앞두고",
    "dialogue_a": "The project deadline is looming, and we still have so much to do.",
    "dialogue_b": "I know, we need to work overtime this weekend.",
    "translation_a": "프로젝트 마감일이 코앞으로 다가오고 있는데, 우린 아직 할 일이 너무 많아.",
    "translation_b": "알아, 우리 이번 주말엔 야근해야 할 것 같아."
  }
}

# Remove old vocab_2 if exists, then append
data["global_vocab_list"] = [v for v in data["global_vocab_list"] if v.get("id") != "vocab_2"]
data["global_vocab_list"].append(vocab_2)

# Ensure sentences[2] has vocab_list info
if len(data["sentences"]) > 2:
    vocab_list_item = {
      "word": "loom",
      "level": "C1",
      "equivalent_term": "다가오다, 임박하다",
      "meaning": "다가오다, 임박하다",
      "pattern": "loom (large/closer)",
      "pattern_meaning": "(거대하게/점점 더) 다가오다"
    }
    # Check if already added
    exists = any(v.get("word") == "loom" for v in data["sentences"][2].get("vocab_list", []))
    if not exists:
        if "vocab_list" not in data["sentences"][2]:
            data["sentences"][2]["vocab_list"] = []
        data["sentences"][2]["vocab_list"].append(vocab_list_item)

# Write back
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("analysis.json updated successfully.")
