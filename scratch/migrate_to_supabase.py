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
print(f"URL: {supabase_url}")

# 2. Load analysis.json
analysis_path = os.path.join("processed", "01_motivation", "analysis.json")
with open(analysis_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 3. Format sentences
sentences_to_upload = []
for s in data["sentences"]:
    sentences_to_upload.append({
        "index": s["index"],
        "start_time": s["start_time"],
        "end_time": s["end_time"],
        "english_text": s["english_text"],
        "korean_text": s["korean_text"],
        "visual_description": s.get("visual_description", ""),
        "lecture_script": s.get("lecture_script", "")
    })

# 4. Format vocab
vocabs_to_upload = []
for v in data.get("global_vocab_list", []):
    vocabs_to_upload.append({
        "id": v["id"],
        "sentence_index": v["sentence_index"],
        "word": v["word"],
        "meaning": v["meaning"],
        "level": v.get("level", ""),
        "english_definition": v.get("english_definition", ""),
        "english_definition_translation": v.get("english_definition_translation", ""),
        "explanation": v.get("explanation", ""),
        "patterns": v.get("patterns", []),
        "ab_dialogue": v.get("ab_dialogue", {})
    })

def upload_to_supabase(table_name, payload):
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
s_success = upload_to_supabase("sentence", sentences_to_upload)
v_success = upload_to_supabase("vocab", vocabs_to_upload)

if s_success and v_success:
    print("Migration completed successfully!")
else:
    print("Migration failed. Please check the logs above.")
