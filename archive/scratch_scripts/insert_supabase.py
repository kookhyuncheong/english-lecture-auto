import json
import os
import requests

env_path = "c:/Users/kookh/OneDrive/Desktop/english-lecture-auto/.env"
SUPABASE_URL = ""
SUPABASE_KEY = ""

with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("SUPABASE_URL="):
            SUPABASE_URL = line.strip().split("=", 1)[1].strip('"')
        elif line.startswith("SUPABASE_SERVICE_ROLE_KEY="):
            SUPABASE_KEY = line.strip().split("=", 1)[1].strip('"')

analysis_file = "c:/Users/kookh/OneDrive/Desktop/english-lecture-auto/processed/01_motivation/analysis.json"
with open(analysis_file, "r", encoding="utf-8") as f:
    data = json.load(f)

vocab_list = data.get("global_vocab_list", [])

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

records = []
for vocab in vocab_list:
    record = {
        "word": vocab.get("word", ""),
        "base_word": vocab.get("base_word", ""),
        "level": vocab.get("level", "C1"), # Default to C1 if missing
        "meaning": vocab.get("meaning", ""),
        "english_definition": vocab.get("english_definition"),
        "english_definition_translation": vocab.get("english_definition_translation"),
        "example_groups": vocab.get("example_groups"),
        "sentence_text": vocab.get("sentence_text"),
        "sentence_contextual_translation": vocab.get("sentence_contextual_translation"),
        "ab_dialogue": vocab.get("ab_dialogue"),
        "video_id": "01_motivation",
        "sentence_index": vocab.get("sentence_index")
    }
    records.append(record)

url = f"{SUPABASE_URL}/rest/v1/vocabularies"
res = requests.post(url, headers=headers, json=records)

print(f"Status Code: {res.status_code}")
if res.status_code in (200, 201):
    print("Successfully inserted records into Supabase!")
else:
    print(res.text)
