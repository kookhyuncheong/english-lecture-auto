import os
import json
import urllib.request
import urllib.error
import sys

def main():
    word = "loom"
    if len(sys.argv) > 1:
        word = sys.argv[1]

    env_path = ".env"
    mwld_key = None
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("MWLD_API_KEY="):
                    mwld_key = line.split("=", 1)[1].strip('"').strip("'")
                    break

    if not mwld_key:
        print("MWLD_API_KEY not found in .env")
        sys.exit(1)

    url = f"https://www.dictionaryapi.com/api/v3/references/learners/json/{word}?key={mwld_key}"
    
    os.makedirs("processed/raw_dict", exist_ok=True)
    output_path = f"processed/raw_dict/{word}_mwld.json"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = response.read().decode('utf-8')
            json_data = json.loads(data)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
                
            print(f"Successfully fetched and saved to {output_path}")
    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    main()
