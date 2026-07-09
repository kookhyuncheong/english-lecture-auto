import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("오류: GEMINI_API_KEY가 .env 파일에 없습니다.")
        return

    client = genai.Client(api_key=api_key)

    analysis_path = os.path.join("processed", "01_motivation", "analysis.json")
    if not os.path.exists(analysis_path):
        print(f"오류: '{analysis_path}' 분석 결과 파일이 없습니다. 비디오 분석을 먼저 진행해야 합니다.")
        return

    # 대본 파일 불러오기
    with open(analysis_path, "r", encoding="utf-8") as f:
        analysis_data = json.load(f)

    sentences = analysis_data.get("sentences", [])
    total_sentences = len(sentences)
    print(f"총 {total_sentences}개의 문장 대본을 읽어왔어. 제미나이 순정 목소리 녹음을 시작할게!")

    audio_dir = os.path.join("processed", "01_motivation", "audio")
    os.makedirs(audio_dir, exist_ok=True)

    for i, s in enumerate(sentences):
        idx = s["index"]
        lecture_text = s["lecture_script"]
        audio_filename = f"sentence_{idx}.wav"
        audio_path = os.path.join(audio_dir, audio_filename)

        # 이미 녹음 파일이 존재하면 건너뛰어서 리소스를 절약해 (중간에 에러나서 재시작했을 때 매우 안전해!)
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
            print(f"[{i+1}/{total_sentences}] 문장 {idx}번: 이미 오디오 파일이 존재하여 건너뜁니다.")
            continue

        print(f"[{i+1}/{total_sentences}] 문장 {idx}번 녹음 중... 대본: '{lecture_text[:30]}...'")
        
        try:
            # tts-preview 모델 호출
            tts_prompt = f"아래 한국어 문장을 영어 강사처럼 다정하고 자연스럽게 한국어로 읽어줘. 절대 다른 설명은 하지 말고 이 문장만 자연스럽게 낭독한 오디오 데이터만 돌려줘:\n{lecture_text}"
            
            response = client.models.generate_content(
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

            # 오디오 이진 데이터를 파일로 저장
            audio_saved = False
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    with open(audio_path, "wb") as f_audio:
                        f_audio.write(part.inline_data.data)
                    audio_saved = True
                    break
            
            if audio_saved:
                print(f" -> 성공: {audio_filename} 저장 완료!")
            else:
                print(f" -> 에러: 응답에 오디오 데이터가 포함되어 있지 않습니다.")

        except Exception as e:
            print(f" -> 에러 발생 (문장 {idx}번): {e}")

        # 구글 API 속도 제한(RPM)을 초과하지 않도록 4초 대기
        if i < total_sentences - 1:
            print("안전 대기 중 (4초)...")
            time.sleep(4)

    print("\n축하해! 모든 대본의 제미나이 AI 목소리 녹음이 끝났어! 🎈")

if __name__ == "__main__":
    main()
