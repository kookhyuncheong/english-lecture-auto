import json
import os

file_path = "c:/Users/kookh/OneDrive/Desktop/english-lecture-auto/processed/01_motivation/analysis.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Update global_vocab_list for vocab_2
for vocab in data.get("global_vocab_list", []):
    if vocab.get("id") == "vocab_2":
        vocab["word"] = "looms"

# Update sentences array
for sentence in data.get("sentences", []):
    for vocab in sentence.get("vocab_list", []):
        if vocab.get("word") == "loom": # The previous logic might have inserted 'loom'
            vocab["word"] = "looms"

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("word field updated to 'looms' successfully.")
