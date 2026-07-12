import re
import os

filepath = r"C:\Users\kookh\OneDrive\Desktop\english-lecture-auto\.system_generated\steps\1477\content.md"
if not os.path.exists(filepath):
    # Try the absolute path from appdata
    filepath = r"C:\Users\kookh\.gemini\antigravity-ide\brain\2b6ac948-085f-46b1-9524-86c2a6f24c89\.system_generated\steps\1477\content.md"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Let's extract paragraphs containing words like 'unauthorized', 'login', 'env', 'token', 'key'
clean_text = re.sub(r'<[^>]+>', ' ', content)
clean_text = re.sub(r'\s+', ' ', clean_text)

# Let's split by sentence boundaries (e.g. dot followed by space)
sentences = re.split(r'\. ', clean_text)
keywords = ["unauthorized", "login", "env", "token", "key", "work", "fix", "supabase", "antigravity", "error"]

matching_sentences = []
for s in sentences:
    lower_s = s.lower()
    # Check if sentence contains at least two keywords to get relevant context
    hits = [kw for kw in keywords if kw in lower_s]
    if len(hits) >= 2:
        matching_sentences.append(s.strip())

print(f"Total matching sentences: {len(matching_sentences)}")
for i, s in enumerate(matching_sentences[:20]):
    print(f"{i+1}: {s}\n")
