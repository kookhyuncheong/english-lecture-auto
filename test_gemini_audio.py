import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. .env 파일 로드 및 API 클라이언트 초기화
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("gemini-2.0-flash 모델을 사용하여 오디오(음성) 생성을 시도합니다...")

try:
    # 2. 제미나이 3.1 TTS 모델에게 오디오 포맷 대답을 요청
    response = client.models.generate_content(
        model='gemini-3.1-flash-tts-preview',
        contents="안녕하세요, 국현님! 저는 국현님의 인공지능 영어 튜터예요. 목소리가 잘 들리시나요? 앞으로 재밌게 공부해봐요!",
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Aoede"  # 다정하고 세련된 목소리
                    )
                )
            )
        )
    )

    # 3. 돌려받은 이진 데이터(Binary)를 파일로 저장
    audio_saved = False
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            # 보통 wav 형식으로 반환됩니다.
            with open("test_voice.wav", "wb") as f:
                f.write(part.inline_data.data)
            print("성공: 'test_voice.wav' 파일이 성공적으로 생성되었습니다!")
            audio_saved = True
            break
            
    if not audio_saved:
        print("실패: 응답은 받았으나 오디오 데이터를 찾을 수 없습니다.")

except Exception as e:
    print(f"에러 발생: {e}")
