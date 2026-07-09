import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

# ==========================================
# 1. Pydantic 데이터 구조 정의 (AI 대답 틀)
# ==========================================
class VocabularyItem(BaseModel):
    word: str = Field(description="영어 단어 또는 숙어 표현")
    level: str = Field(description="CEFR 난이도 레벨 (B2, C1, C2 중 하나)")
    meaning: str = Field(description="한국어 뜻")
    explanation: str = Field(description="이 문장에서 단어가 어떻게 쓰였는지 친절한 설명")

class SentenceLecture(BaseModel):
    index: int = Field(description="문장 번호 (1부터 시작)")
    start_time: str = Field(description="문장 시작 시간 (포맷: HH:MM:SS,mmm - 예: 00:00:02,150)")
    end_time: str = Field(description="문장 종료 시간 (포맷: HH:MM:SS,mmm - 예: 00:00:05,400)")
    english_text: str = Field(description="영어 원문 대사 (마침표나 물음표로 끝나는 완전한 한 문장)")
    korean_text: str = Field(description="자연스러운 한국어 번역")
    vocab_list: List[VocabularyItem] = Field(description="이 문장에 사용된 CEFR B2 레벨 이상의 고급 어휘 리스트")
    visual_description: str = Field(description="해당 문장이 말해질 때 화면에 나오는 시각적 장면 묘사 (한글)")
    lecture_script: str = Field(description="선생님이 화면 속 모습과 대사를 같이 보면서 다정하게 설명해주는 한국어 강의 대본 (1~3문장)")

class LectureData(BaseModel):
    title: str = Field(description="강의 영상의 대주제 제목 (한글)")
    sentences: List[SentenceLecture] = Field(description="비디오 속 모든 문장들의 분석 리스트")

# ==========================================
# 2. 메인 처리 함수
# ==========================================
def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("오류: GEMINI_API_KEY가 .env 파일에 없습니다.")
        return

    client = genai.Client(api_key=api_key)

    video_path = "01. How to get motivated even when you don't feel like it.mp4"
    if not os.path.exists(video_path):
        print(f"오류: '{video_path}' 파일이 존재하지 않습니다.")
        return

    # 결과를 저장할 폴더 생성
    output_dir = os.path.join("processed", "01_motivation")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "audio"), exist_ok=True)

    # 1. 비디오 업로드 및 대기
    print("1. 비디오 파일을 Gemini AI 서버로 업로드하는 중...")
    video_file = client.files.upload(file=video_path)
    print(f"업로드 완료! 서버 파일 이름: {video_file.name}")

    print("Gemini AI가 비디오의 소리와 화면을 통합 분석 중입니다...")
    while video_file.state.name == "PROCESSING":
        time.sleep(5)
        video_file = client.files.get(name=video_file.name)

    if video_file.state.name != "ACTIVE":
        print(f"오류: 비디오 분석 실패. 상태: {video_file.state.name}")
        return

    print("비디오 분석 완료! 이제 자막 및 강의 정보 분석을 시작합니다.")

    # 2. 제미나이에게 멀티모달 분석 및 자막 생성 주문
    prompt = """
    당신은 친절하고 전문적인 영어 강사입니다. 업로드된 영어 강의 동영상을 시각적 화면과 음성 소리를 모두 참고하여 분석해주세요.
    다음 규칙에 따라 데이터를 작성해주세요:
    1. 동영상의 전체 대사를 마침표(.), 물음표(?) 등으로 끝나는 완전한 하나의 영어 문장 단위로 분할하여 받아쓰기하세요.
    2. 각 문장의 시작 시간과 끝나는 시간을 'HH:MM:SS,mmm' 형식(예: 00:01:23,450)으로 정확하게 채워주세요. 자막 싱크에 매우 중요합니다.
    3. 각 문장에서 수준이 다소 높은 영어 단어 또는 숙어(CEFR B2, C1, C2 레벨)를 골라내어 정리해주세요.
    4. 각 문장이 말해지는 타이밍의 비디오 화면을 눈으로 보고 화면에 무엇이 등장하는지(예: 칠판 글씨, 강사의 손동작, 화면 전환, 물건 등) 한글로 묘사해주세요.
    5. '강의 대본(lecture_script)'은 AI 선생님이 국현이와 함께 영상을 모니터링하면서 가르쳐주는 상황입니다. 한국어로 친근하게 작성하되, 화면에 나타난 내용(예: '지금 화면에 나온 양탄자를 보세요', '강사가 손으로 가리킨 부분을 주목하세요')을 언급하며 영상 내용과 영어 표현을 조화롭게 설명하도록 해주세요.
    """

    print("2. Gemini AI에게 비디오 텍스트 분석 요청 중...")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[video_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LectureData,
                temperature=0.2, # 결과의 정확성을 높이기 위해 낮은 온도로 설정
            ),
        )
        
        # 분석 결과를 JSON 객체로 파싱 및 저장
        analysis_data = json.loads(response.text)
        analysis_path = os.path.join(output_dir, "analysis.json")
        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2)
        print(f"분석 결과 저장 완료: {analysis_path}")

    except Exception as e:
        print(f"분석 에러 발생: {e}")
        return

    # 3. SRT 자막 파일 생성
    print("3. SRT 자막 파일 작성 중...")
    srt_path = os.path.join(output_dir, "subtitle.srt")
    try:
        with open(srt_path, "w", encoding="utf-8") as f:
            for s in analysis_data["sentences"]:
                idx = s["index"]
                start = s["start_time"]
                end = s["end_time"]
                # 일부 타임스탬프 형식 보정 (예: 00:00:02.150 -> 00:00:02,150)
                start = start.replace(".", ",")
                end = end.replace(".", ",")
                text = s["english_text"]
                
                f.write(f"{idx}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")
        print(f"자막 파일 생성 완료: {srt_path}")
    except Exception as e:
        print(f"자막 파일 작성 오류: {e}")

    # 4. 각 문장별 AI 목소리(TTS) 오디오 파일 생성
    print("4. 문장별 AI 선생님 목소리(TTS) 생성 중...")
    sentences = analysis_data.get("sentences", [])
    total_sentences = len(sentences)

    for i, s in enumerate(sentences):
        idx = s["index"]
        lecture_text = s["lecture_script"]
        audio_filename = f"sentence_{idx}.mp3"
        audio_path = os.path.join(output_dir, "audio", audio_filename)

        print(f"[{i+1}/{total_sentences}] 문장 {idx}번 오디오 생성 중... ('{lecture_text[:20]}...')")
        
        try:
            # Gemini의 오디오 모달리티(Audio Out) 활용 호출
            tts_prompt = f"아래 한국어 문장을 영어 강사처럼 다정하고 자연스럽게 한국어로 읽어줘. 절대 다른 말은 덧붙이지 말고 낭독한 오디오만 생성해줘:\n{lecture_text}"
            
            tts_response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=tts_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Aoede"  # 다정하고 세련된 여성 목소리 계열
                            )
                        )
                    )
                )
            )

            # 오디오 데이터 추출 및 파일 저장
            audio_saved = False
            for part in tts_response.candidates[0].content.parts:
                if part.inline_data:
                    with open(audio_path, "wb") as f_audio:
                        f_audio.write(part.inline_data.data)
                    audio_saved = True
                    break
            
            if audio_saved:
                print(f" -> 오디오 저장 성공: {audio_path}")
            else:
                print(f" -> 오디오 데이터를 응답에서 찾을 수 없습니다 (문장 {idx})")

        except Exception as e:
            print(f" -> 오디오 생성 에러 (문장 {idx}): {e}")

        # API 호출 속도 제한(RPM)을 지키기 위해 잠시 대기 (4초)
        if i < total_sentences - 1:
            print("대기 중 (4초)...")
            time.sleep(4)

    print("\n모든 백엔드 분석 및 오디오 생성 작업이 완료되었습니다! 🎈")

if __name__ == "__main__":
    main()
