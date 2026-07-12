import json
import os

analysis_path = os.path.join("processed", "01_motivation", "analysis.json")

with open(analysis_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Manually insert the lexicon_instances for sentence 1 and 3 based on what we know is in Supabase.
for sentence in data.get("sentences", []):
    idx = sentence.get("index")
    
    if idx == 1:
        sentence["lexicon_instances"] = [
            {
                "lexicon_id": "L-aspire-verb-0",
                "target_phrase": "aspired to be"
            }
        ]
    elif idx == 3:
        sentence["lexicon_instances"] = [
            {
                "lexicon_id": "L-loom-verb-1",
                "target_phrase": "deadline looms"
            }
        ]
    else:
        # initialize empty array for others
        if "lexicon_instances" not in sentence:
            sentence["lexicon_instances"] = []

with open(analysis_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Linked lexicon_instances into analysis.json successfully!")
