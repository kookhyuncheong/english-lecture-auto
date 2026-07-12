import json
import os

file_path = "c:/Users/kookh/OneDrive/Desktop/english-lecture-auto/processed/01_motivation/analysis.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 1. Refactor 'aspire' (vocab_1)
for vocab in data.get("global_vocab_list", []):
    if vocab["id"] == "vocab_1":
        if "patterns" in vocab:
            # Flatten examples from patterns
            examples = []
            for p in vocab["patterns"]:
                for ex in p.get("examples", []):
                    # Add bolding to match pattern if possible, or just keep it simple
                    eng_text = ex["eng"]
                    if "aspired to a" in eng_text:
                        eng_text = eng_text.replace("aspired to", "**aspired to**")
                    elif "aspired to be" in eng_text:
                        eng_text = eng_text.replace("aspired to be", "**aspired to be**")
                    
                    examples.append({
                        "eng": eng_text,
                        "kor": ex["kor"]
                    })
            vocab["examples"] = examples
            del vocab["patterns"]

# 2. Refactor 'loom' (vocab_2)
for vocab in data.get("global_vocab_list", []):
    if vocab["id"] == "vocab_2":
        if "patterns" in vocab:
            del vocab["patterns"]
        
        # Add all 4 examples exactly as they appear in Britannica
        vocab["examples"] = [
            {
                "eng": "A workers' strike is *looming*.",
                "kor": "노동자들의 파업이 임박했다."
            },
            {
                "eng": "A battle is *looming* in Congress over the proposed budget cuts.",
                "kor": "제안된 예산 삭감을 두고 의회에서 공방전이 임박했다."
            },
            {
                "eng": "a *looming* battle/conflict/problem/storm",
                "kor": "다가오는 전투/갈등/문제/폭풍"
            },
            {
                "eng": "The deadline **looms closer** with each passing day.",
                "kor": "마감일이 하루하루 점점 다가오고 있다."
            }
        ]

# 3. Clean up sentences array if it has 'pattern' fields
for sentence in data.get("sentences", []):
    for vocab in sentence.get("vocab_list", []):
        if "pattern" in vocab:
            del vocab["pattern"]
        if "pattern_meaning" in vocab:
            del vocab["pattern_meaning"]

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("analysis.json updated with flat examples arrays and all 4 loom examples.")
