import json
import os

file_path = "c:/Users/kookh/OneDrive/Desktop/english-lecture-auto/processed/01_motivation/analysis.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for vocab in data.get("global_vocab_list", []):
    if vocab["id"] == "vocab_1": # aspire
        vocab["word"] = "aspired"
        vocab["base_word"] = "aspire"
        vocab["meaning"] = "열망하다, 간절히 바라다"
        vocab["english_definition"] = "to want to have or achieve something (such as a particular career or level of success)"
        vocab["english_definition_translation"] = "무언가를 성취하거나 무언가가 되고자 강하게 원하다 (특히 특정 직업이나 성공의 수준)"
        
        # Build example_groups
        vocab["example_groups"] = [
            {
                "grammar_hint": "often + *to*",
                "examples": [
                    {
                        "eng": "Both young men *aspire to* careers in medicine.",
                        "kor": "두 청년 모두 의학 분야의 커리어를 열망한다."
                    },
                    {
                        "eng": "She *aspires to* a more active role in her government.",
                        "kor": "그녀는 정부에서 더 적극적인 역할을 맡기를 간절히 바란다."
                    },
                    {
                        "eng": "people who *aspire to* home ownership",
                        "kor": "내 집 마련을 열망하는 사람들"
                    }
                ]
            },
            {
                "grammar_hint": "often followed by *to* + verb",
                "examples": [
                    {
                        "eng": "He says he never *aspired to become* famous.",
                        "kor": "그는 한 번도 유명해지기를 바란 적이 없다고 말한다."
                    },
                    {
                        "eng": "little girls who *aspire to play* professional basketball",
                        "kor": "프로 농구 선수가 되기를 꿈꾸는 어린 소녀들"
                    }
                ]
            }
        ]
        
        # Remove old fields
        if "examples" in vocab: del vocab["examples"]
        if "patterns" in vocab: del vocab["patterns"]
        
        vocab["sentence_index"] = 1
        vocab["sentence_text"] = "You've always aspired to be a professional artist."
        vocab["sentence_contextual_translation"] = "항상 전문 화가가 되기를 꿈꿔왔죠."
        
        vocab["ab_dialogue"] = {
            "situation": "동료와 커리어 목표에 대해 이야기할 때",
            "dialogue_a": "I've always aspired to a leadership position in this company.",
            "dialogue_b": "That's great! You definitely have the skills for it.",
            "translation_a": "나는 항상 이 회사에서 리더십 있는 자리에 오르기를 열망해왔어.",
            "translation_b": "멋지다! 넌 확실히 그럴 만한 능력이 있어."
        }

    elif vocab["id"] == "vocab_2": # loom
        # Convert flat examples to a single example_group
        if "examples" in vocab:
            vocab["example_groups"] = [
                {
                    "grammar_hint": None,
                    "examples": vocab["examples"]
                }
            ]
            del vocab["examples"]
            
        if "patterns" in vocab: del vocab["patterns"]

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("analysis.json updated with example_groups successfully.")
