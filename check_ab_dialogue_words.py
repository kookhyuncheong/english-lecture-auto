import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 평가 결과 스키마
class WordEvaluation(BaseModel):
    word: str
    is_suitable_for_ab: bool = Field(description="일상생활이나 직장/학업 상황에서 A/B 대화문으로 자연스럽게 연습할 수 있는 단어인가?")
    ab_situation: str = Field(description="대화가 이루어질 수 있는 상황 설명 (예: 직장 업무, 친구와의 날씨 대화 등)")
    dialogue_a: str = Field(description="대화문 A의 대사 (해당 단어/패턴이 포함되어야 함)")
    dialogue_b: str = Field(description="대화문 B의 대사 (자연스러운 맞받아치기)")

class EvaluationList(BaseModel):
    evaluations: list[WordEvaluation]

def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # 중복을 제거한 실제 C1/C2 고급 어휘 목록
    c1_c2_words = [
        "actionable", "aspire", "daunt", "extrinsic", "fickle", 
        "impetus", "intrinsic", "loom", "persistence", "phenomenon", 
        "short-lived", "tedious"
    ]
    
    prompt = f"""
다음은 영어 비디오 분석에서 추출된 C1, C2 레벨의 고급 단어 목록입니다:
{json.dumps(c1_c2_words)}

이 단어들 각각에 대해, 원어민들이 일상 대화나 회사 업무(직장), 학교 생활 등의 실생활 'A/B 핑퐁 대화'에서 자연스럽게 사용할 수 있는지 판단하고 분류해주세요.
사용이 가능하다면, 해당 단어를 사용한 짧고 실용적인 A/B 대화문(영어)과 어떤 상황인지도 적어주세요.

반드시 지정된 JSON 포맷으로 응답해야 합니다.
"""
    
    print("제미나이에게 C1/C2 단어의 실생활 A/B 대화 가능성 평가를 요청하는 중...")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EvaluationList,
                temperature=0.1
            )
        )
        
        res = json.loads(response.text)
        evals = res.get("evaluations", [])
        
        suitable_words = [e for e in evals if e["is_suitable_for_ab"]]
        unsuitable_words = [e for e in evals if not e["is_suitable_for_ab"]]
        
        print("\n=== 평가 결과 요약 ===")
        print(f"전체 평가 단어: {len(evals)}개")
        print(f" 실생활 A/B 대화문 제작 가능 단어: {len(suitable_words)}개")
        print(f"❌ 대화문으로 쓰기 다소 딱딱한 단어: {len(unsuitable_words)}개")
        
        print("\n[ 대화문 제작 가능 단어 리스트 및 예시 ]")
        for i, e in enumerate(suitable_words, 1):
            print(f"\n{i}. {e['word'].upper()} (상황: {e['ab_situation']})")
            print(f"  A: {e['dialogue_a']}")
            print(f"  B: {e['dialogue_b']}")
            
        if unsuitable_words:
            print("\n[ ❌ 대화문으로 부적합한 단어 리스트 ]")
            for e in unsuitable_words:
                print(f"  - {e['word']}")
                
    except Exception as e:
        print("에러 발생:", e)

if __name__ == "__main__":
    main()
