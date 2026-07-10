import json
import os
import urllib.request
import urllib.error

# 1. Load env variables
env_path = ".env"
supabase_url = None
supabase_service_key = None

if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key == "SUPABASE_URL":
                    supabase_url = val
                elif key == "SUPABASE_SERVICE_ROLE_KEY":
                    supabase_service_key = val

if not supabase_url or not supabase_service_key:
    print("Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in .env")
    exit(1)

print("Supabase config loaded successfully.")

# 2. Load analysis.json
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from schema import AnalysisData

analysis_path = os.path.join("processed", "01_motivation", "analysis.json")
with open(analysis_path, "r", encoding="utf-8") as f:
    raw_data = json.load(f)
    
# 🚀 Pydantic 설계도 통과 (이 과정에서 형태가 다르면 에러 뿜음)
data = AnalysisData.model_validate(raw_data)

def slugify(text):
    return text.lower().replace(" ", "_").replace("-", "_")

def build_id(prefix, lemma, pos="verb", sense=0, extra=""):
    slug = slugify(lemma)
    if extra:
        return f"{prefix}-{slug}-{pos}-{sense}-{extra}"
    return f"{prefix}-{slug}-{pos}-{sense}"

lexicon_to_upload = []
examples_to_upload = []
dialogues_to_upload = []

vocab_lookup = {} # Maps word/base_word to (lexicon_id, target_phrase)

# Process global_vocab_list
for i, v in enumerate(data.global_vocab_list):
    lemma = v.base_word if v.base_word else v.word
    pos = "verb"
    sense = i # using index as sense for now
    
    l_id = build_id("L", lemma, pos, sense)
    d_id = build_id("D", lemma, pos, sense)
    
    # Lookup map
    vocab_lookup[lemma.lower()] = (l_id, v.target_phrase if v.target_phrase else v.word)
    vocab_lookup[v.word.lower()] = (l_id, v.target_phrase if v.target_phrase else v.word)
    
    # 1. Lexicon payload
    lexicon_to_upload.append({
        "id": l_id,
        "lemma": lemma,
        "pos": pos,
        "level": v.level or "",
        "meaning": v.meaning or "",
        "english_definition": v.english_definition or "",
        "english_definition_translation": v.english_definition_translation or ""
    })
    
    # 2. Examples payload
    eg_index = 1
    if v.example_groups:
        for p in v.example_groups:
            ghint = p.grammar_hint
            for ex in p.examples:
                e_id = build_id("E", lemma, pos, sense, str(eg_index))
                examples_to_upload.append({
                    "id": e_id,
                    "lexicon_id": l_id,
                    "english_text": ex.eng,
                    "korean_text": ex.kor,
                    "grammar_hint": ghint,
                    "tts_url": None
                })
                eg_index += 1
                
    # 3. Dialogues payload
    if v.ab_dialogue:
        ab = v.ab_dialogue
        dialogues_to_upload.append({
            "id": d_id,
            "lexicon_id": l_id,
            "speaker_a_eng": ab.dialogue_a,
            "speaker_a_kor": ab.translation_a,
            "speaker_b_eng": ab.dialogue_b,
            "speaker_b_kor": ab.translation_b
        })

# Process sentences
sentences_to_upload = []
for s in data.sentences:
    lexicon_instances = []
    
    # Process lexicon_instances properly
    if s.lexicon_instances:
        for inst in s.lexicon_instances:
            lexicon_instances.append({
                "lexicon_id": inst.lexicon_id,
                "target_phrase": inst.target_phrase
            })

    sentences_to_upload.append({
        "index": s.index,
        "start_time": s.start_time,
        "end_time": s.end_time,
        "english_text": s.english_text,
        "korean_text": s.korean_text,
        "visual_description": s.visual_description,
        "lecture_script": s.lecture_script,
        "lexicon_instances": lexicon_instances
    })

def upload_to_supabase(table_name, payload):
    if not payload:
        return True
    url = f"{supabase_url}/rest/v1/{table_name}"
    headers = {
        "apikey": supabase_service_key,
        "Authorization": f"Bearer {supabase_service_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            status = response.status
            print(f"[{table_name}] Successfully uploaded! (HTTP Status: {status})")
            return True
    except urllib.error.HTTPError as e:
        print(f"[{table_name}] HTTP Error: {e.code}")
        print(e.read().decode("utf-8"))
        return False
    except Exception as e:
        print(f"[{table_name}] Exception Error: {e}")
        return False

# Run
print("Starting migration...")
l_success = upload_to_supabase("lexicon", lexicon_to_upload)
e_success = upload_to_supabase("examples", examples_to_upload)
d_success = upload_to_supabase("dialogues", dialogues_to_upload)
s_success = upload_to_supabase("sentence", sentences_to_upload)

if all([l_success, e_success, d_success, s_success]):
    print("Migration completed successfully!")
else:
    print("Migration failed. Please check the logs above.")
