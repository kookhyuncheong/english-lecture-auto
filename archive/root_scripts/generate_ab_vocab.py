import os
import json
import time
import wave
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# ==========================================
# 1. 제미나이 스키마 정의
# ==========================================
class DialogueDetail(BaseModel):
    situation: str = Field(description="A/B 대화가 일어나는 상황 (예: 친구와의 일상 대화, 회사 회의 등)")
    dialogue_a: str = Field(description="A의 짧고 자연스러운 영어 대사 (해당 단어/패턴 포함)")
    dialogue_b: str = Field(description="B의 화답하는 영어 대사")
    translation_a: str = Field(description="A 대사의 한글 번역")
    translation_b: str = Field(description="B 대사의 한글 번역")

class VocabReprocessResult(BaseModel):
    word: str = Field(description="본문 문맥을 반영한 롱맨 스타일의 사전식 콜로케이션 패턴/문형 (예: aspire to be/do something)")
    meaning: str = Field(description="패턴의 한글 사전식 번역 뜻")
    explanation: str = Field(description="본문 속에서의 쓰임새를 설명하는 친근한 한글 설명 (1-2문장)")
    ab_dialogue: DialogueDetail

# ==========================================
# 2. WAV 헤더 추가 함수 (RAW PCM -> WAV 변환)
# ==========================================
def save_pcm_as_wav(pcm_bytes, wav_path):
    """
    제미나이 TTS가 리턴한 RAW PCM 바이트 데이터(24000Hz, 16-bit, Mono, Little-Endian)에
    WAV RIFF 헤더를 결합하여 브라우저에서 바로 재생 가능한 .wav 파일로 저장합니다.
    """
    with wave.open(wav_path, 'wb') as wav_file:
        wav_file.setnchannels(1)      # 단일 채널 (모노)
        wav_file.setsampwidth(2)      # 16-bit (2바이트)
        wav_file.setframerate(24000)  # 24kHz 주파수
        wav_file.writeframes(pcm_bytes)
    print(f"  [오디오 저장] {wav_path} 생성 완료")

# ==========================================
# 3. 메인 작업 처리 로직
# ==========================================
def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("오류: GEMINI_API_KEY를 찾을 수 없습니다.")
        return
        
    client = genai.Client(api_key=api_key)
    
    json_path = os.path.join("processed", "01_motivation", "analysis.json")
    if not os.path.exists(json_path):
        print(f"오류: {json_path} 분석 결과가 없습니다.")
        return
        
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    sentences = data.get("sentences", [])
    
    # 1. C1, C2 단어만 골라내어 중복 제거 (Lemma 기준 그룹화)
    unique_lemmas = {}
    
    # 임시 단어 보정 매핑
    lemma_corrections = {
        "tedioustedious": "tedious",
        "science-base": "science-based"
    }
    
    for s in sentences:
        for v in s.get("vocab_list", []):
            level = v.get("level", "")
            if level in ["C1", "C2"]:
                raw_lemma = v.get("word", "").strip().lower()
                
                # 이상 단어 보정
                if raw_lemma in lemma_corrections:
                    raw_lemma = lemma_corrections[raw_lemma]
                    
                # 비정상 한 자짜리 단어 거르기
                if len(raw_lemma) <= 1:
                    continue
                    
                if raw_lemma not in unique_lemmas:
                    unique_lemmas[raw_lemma] = {
                        "lemma": raw_lemma,
                        "level": level,
                        "sentence_index": s["index"],
                        "sentence_text": s["english_text"]
                    }
                    
    print(f"추출 완료: C1/C2 등급 단어 {len(unique_lemmas)}개 식별 (B2 제외 및 중복 제거 완료)")
    
    # 2. 각 고유 단어에 대해 대화문 생성 및 오디오 합성 진행
    global_vocab_list = []
    
    audio_dir = os.path.join("processed", "01_motivation", "audio")
    os.makedirs(audio_dir, exist_ok=True)
    
    for idx, (lemma, item) in enumerate(unique_lemmas.items(), 1):
        vocab_id = f"vocab_{idx}"
        print(f"\n[{idx}/{len(unique_lemmas)}] 단어 '{lemma}' (레벨: {item['level']}) 처리 중...")
        
        # 제미나이에게 단어 정보 및 A/B 대화문 생성 요청
        prompt = f"""
영어 비디오 강의에서 사용된 고급 어휘에 대해 사전식 표제어(콜로케이션 패턴), 사전 정의, 그리고 이를 활용한 스피킹 학습용 실생활/비즈니스 A/B 대화문을 영어 및 한국어 번역으로 작성해주세요.

대상 단어 (기본형): "{lemma}"
이 단어가 사용된 비디오 본문 문장: "{item['sentence_text']}"

규칙:
1. "word": 본문 문맥을 반영한 롱맨 스타일의 공식 사전식 콜로케이션 패턴/문형을 적어주세요. 만약 패턴 없이 단어만 있는 경우 단어만 적으세요. (예: aspire -> aspire to be/do something, loom -> loom, avoid -> avoid doing something)
2. "meaning": 해당 패턴의 정확한 한국어 사전식 번역 뜻을 적어주세요.
3. "explanation": 본문 문장에서 이 단어가 어떻게 사용되었는지 쉽고 다정한 한국어로 1~2문장 설명해주세요.
4. "ab_dialogue":
   - "situation": 이 단어로 A/B 대화를 나눌 수 있는 자연스러운 상황 설명 (한글, 예: 친구와의 대화, 회사 회의)
   - "dialogue_a": 화자 A의 영어 대사. 이 단어(또는 패턴)를 핵심으로 포함해야 하며, 15단어 미만의 실용적이고 자연스러운 영어여야 합니다. (이름 표기 생략하고 대사만)
   - "dialogue_b": 화자 B의 자연스러운 영어 대사 (화답). 15단어 미만.
   - "translation_a": 화자 A 대사의 정확한 한국어 번역.
   - "translation_b": 화자 B 대사의 정확한 한국어 번역.

반드시 다음 JSON 구조로 응답해주세요. 설명이나 다른 텍스트는 절대 붙이지 마세요:
{{
  "word": "콜로케이션 패턴 표제어",
  "meaning": "사전식 뜻",
  "explanation": "본문 쓰임새 설명",
  "ab_dialogue": {{
    "situation": "상황 설명",
    "dialogue_a": "대사 A...",
    "dialogue_b": "대사 B...",
    "translation_a": "A 한글 번역",
    "translation_b": "B 한글 번역"
  }}
}}
"""
        try:
            # 2.5-flash 모델로 JSON 생성
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=VocabReprocessResult,
                    temperature=0.1
                )
            )
            
            vocab_info = json.loads(response.text)
            
            # 대화문 오디오용 합성 텍스트 준비 (A와 B 사이에 긴 쉼표/대시를 추가해 자연스러운 텀을 줌)
            dial_a = vocab_info["ab_dialogue"]["dialogue_a"].replace("A:", "").strip()
            dial_b = vocab_info["ab_dialogue"]["dialogue_b"].replace("B:", "").strip()
            
            # 합성 텍스트: "A의 대사 ... (대시) B의 대사"
            tts_text = f"{dial_a} --- {dial_b}"
            print(f"  [TTS 합성 텍스트]: {tts_text}")
            
            # 제미나이 3.1 TTS 모델을 사용하여 오디오 생성 (speech_config 및 프롬프트 보완)
            audio_path = os.path.join(audio_dir, f"vocab_dialogue_{vocab_id}.wav")
            
            tts_prompt = f"Please read this English dialogue naturally as a native speaker. Speak both parts A and B with a brief pause between them. Do not explain or say anything else, only read the dialogue:\n{tts_text}"
            
            audio_response = client.models.generate_content(
                model='gemini-3.1-flash-tts-preview',
                contents=tts_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Aoede"  # 다정하고 지적인 목소리
                            )
                        )
                    )
                )
            )
            
            # 오디오 바이트 추출 및 WAV 저장
            audio_bytes = None
            for part in audio_response.candidates[0].content.parts:
                if part.inline_data:
                    audio_bytes = part.inline_data.data
                    break
                    
            if audio_bytes:
                save_pcm_as_wav(audio_bytes, audio_path)
                audio_web_path = f"/processed/01_motivation/audio/vocab_dialogue_{vocab_id}.wav"
            else:
                print("  [경고] 제미나이가 오디오 바이트 데이터를 반환하지 않았습니다.")
                audio_web_path = ""
                
            # 최종 단어 리스트에 추가
            global_vocab_list.append({
                "id": vocab_id,
                "word": vocab_info["word"],
                "base_word": lemma,
                "level": item["level"],
                "meaning": vocab_info["meaning"],
                "sentence_index": item["sentence_index"],
                "sentence_text": item["sentence_text"],
                "explanation": vocab_info["explanation"],
                "ab_dialogue": {
                    "situation": vocab_info["ab_dialogue"]["situation"],
                    "dialogue_a": dial_a,
                    "dialogue_b": dial_b,
                    "translation_a": vocab_info["ab_dialogue"]["translation_a"],
                    "translation_b": vocab_info["ab_dialogue"]["translation_b"],
                    "audio_path": audio_web_path
                }
            })
            
        except Exception as e:
            print(f"  - '{lemma}' 처리 에러 발생: {e}")
            
        # API 부하 방지를 위해 1.5초 정지
        time.sleep(1.5)
        
    # 3. 데이터 통합 저장
    # 기존 sentences 내부의 복잡하고 지저분했던 vocab_list는 비우거나 유지
    # (프론트엔드에서는 global_vocab_list를 직접 참고하므로, sentences를 깔끔히 나둬도 무방)
    data["global_vocab_list"] = global_vocab_list
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"\n축하합니다! 총 {len(global_vocab_list)}개의 C1/C2 명품 A/B 대화 단어장 정보와 TTS 음성 생성 완료! 🎈")

if __name__ == "__main__":
    main()
