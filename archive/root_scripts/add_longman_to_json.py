import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from longman_crawler import crawl_longman_patterns

# ==========================================
# 1. 제미나이 응답 매칭 스키마 정의
# ==========================================
class MatchResult(BaseModel):
    pattern: str = Field(description="문맥과 짝 맞추기가 되는 롱맨 사전 공식 패턴 (예: aspire to be/do something)")
    pattern_meaning: str = Field(description="선택한 패턴의 사전 등록 한글 뜻 (예: ⋯이 되기를 열망하다, 간절히 원하다)")

# ==========================================
# 2. 메인 매칭 처리 로직
# ==========================================
def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("오류: GEMINI_API_KEY가 없습니다.")
        return
        
    client = genai.Client(api_key=api_key)
    
    json_path = os.path.join("processed", "01_motivation", "analysis.json")
    if not os.path.exists(json_path):
        print(f"오류: '{json_path}' 분석 결과 파일이 없습니다.")
        return
        
    # 기존 analysis.json 로드
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    sentences = data.get("sentences", [])
    total_sentences = len(sentences)
    print(f"총 {total_sentences}개 문장의 단어장 패치 작업을 시작합니다.")
    
    # 동일한 단어 중복 크롤링 방지를 위한 캐시 딕셔너리
    crawl_cache = {}
    
    for s_idx, s in enumerate(sentences):
        eng_text = s["english_text"]
        vocab_list = s.get("vocab_list", [])
        if not vocab_list:
            continue
            
        print(f"\n[{s_idx+1}/{total_sentences}] 문장 {s['index']}번 단어장 패치 중...")
        
        for v in vocab_list:
            original_word = v["word"]  # 예: "aspired"
            
            # [수정된 1단계]: 먼저 제미나이를 이용해 단어의 사전식 원형(Lemma)을 획득합니다.
            # 딕셔너리에 원형이 없는 단어(예: 'aspired', 'looms')를 긁으면 404 에러가 나기 때문입니다.
            lemma_prompt = f"""
영어 문장에서 사용된 단어의 사전식 기본 원형(Lemma)을 알려주세요.
예:
- 문장: "You've always aspired to be an artist." / 단어: "aspired" -> aspire
- 문장: "The application deadline looms." / 단어: "looms" -> loom
- 문장: "avoiding the canvas altogether" / 단어: "avoiding" -> avoid

문장: "{eng_text}"
단어: "{original_word}"

결과는 단어 원형 글자 하나만 영문 소문자로 적어주세요. 설명이나 공백, 마침표는 절대 붙이지 마세요.
"""
            lemma = original_word.strip().lower() # 기본 폴백
            try:
                lemma_res = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=lemma_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0
                    )
                )
                detected_lemma = lemma_res.text.strip().lower()
                if detected_lemma and len(detected_lemma) < 30:  # 비정상적인 긴 텍스트 응답 방어
                    lemma = detected_lemma
                print(f"  - '{original_word}' ➡️ 원형 감지: '{lemma}'")
            except Exception as e:
                print(f"  - '{original_word}' 원형 감지 에러: {e}")

            # [2단계]: 원형 단어를 바탕으로 롱맨 사전 크롤링 혹은 캐시 로드
            word_key = lemma
            if word_key not in crawl_cache:
                patterns = crawl_longman_patterns(lemma)
                crawl_cache[word_key] = patterns
            else:
                patterns = crawl_cache[word_key]
                
            if not patterns:
                # 크롤링 실패 또는 사전 미등록 단어일 경우 대체 기본값 설정
                v["word"] = lemma
                v["pattern"] = lemma
                v["pattern_meaning"] = v["meaning"]
                print(f"  - '{original_word}': 사전 데이터가 없어 기본값 유지")
                continue
                
            # [3단계]: 제미나이에게 고스톱 짝 맞추기 요청
            prompt = f"""
영어 문장에서 사용된 단어가 제공된 롱맨 영한사전 패턴 목록 중 어떤 것과 짝을 이루는지 골라주세요.

영어 문장: "{eng_text}"
단어 원형: "{lemma}"
롱맨 사전 패턴 목록:
{json.dumps(patterns, ensure_ascii=False, indent=2)}

규칙:
1. 문장 속에서 단어가 사용된 실제 구조와 가장 잘 매치되는 롱맨 패턴을 골라주세요.
   예: 문장에 "aspired to be"가 있다면, 사전 패턴 목록 중 "aspire to be/do something"을 골라야 합니다.
2. 만약 특별한 문형 패턴이 매칭되지 않거나 목록에 단어 기본형만 존재한다면, 단어 기본형을 선택해주세요.
3. 반드시 다음 JSON 포맷으로만 응답해주세요. 설명이나 추가 텍스트는 절대 붙이지 마세요:
{{
  "pattern": "선택한 패턴",
  "pattern_meaning": "선택한 패턴의 뜻"
}}
"""
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=MatchResult,
                        temperature=0.1
                    )
                )
                
                res = json.loads(response.text)
                
                # 기존 데이터 덮어쓰기 업데이트
                v["word"] = lemma                           # 단어 표기 원형으로 교체 (Lemma 완료!)
                v["pattern"] = res["pattern"]               # 매치되는 사전 공식 패턴
                v["pattern_meaning"] = res["pattern_meaning"] # 사전 패턴 뜻
                
                print(f"    ➡️ 최종 짝 맞춤: '{v['pattern']}' ({v['pattern_meaning']})")
                
            except Exception as e:
                print(f"    ➡️ 짝 맞춤 에러 발생: {e}")
                # 에러 발생 시 안전 폴백
                v["word"] = lemma
                v["pattern"] = lemma
                v["pattern_meaning"] = v["meaning"]
                
            # API 제한(RPM) 우회를 위해 대기 (1.5초)
            time.sleep(1.5)
            
    # 최종 수정 완료된 JSON 파일 저장
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("\n성공: 롱맨 영한사전 매칭 및 원형 변환 작업이 모두 끝났습니다! 🎈")

if __name__ == "__main__":
    main()
