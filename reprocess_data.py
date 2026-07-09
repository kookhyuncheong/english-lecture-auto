import os
import json
import re
import time
import wave
import shutil
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ==========================================
# 1. 시간 변환 헬퍼 함수들
# ==========================================
def parse_time(ts):
    """HH:MM:SS,mmm 포맷의 문자열을 초(float) 단위로 변환"""
    ts = ts.replace('.', ',')
    parts = ts.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    sec_parts = parts[2].split(',')
    seconds = int(sec_parts[0])
    ms = int(sec_parts[1]) if len(sec_parts) > 1 else 0
    return hours * 3600 + minutes * 60 + seconds + ms / 1000.0

def format_time(seconds):
    """초(float) 단위를 HH:MM:SS,mmm 포맷의 문자열로 변환"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    
    # 밀리초 올림 처리
    if ms >= 1000:
        ms -= 1000
        secs += 1
    if secs >= 60:
        secs -= 60
        minutes += 1
    if minutes >= 60:
        minutes -= 60
        hours += 1
        
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"

# ==========================================
# 2. 리스트 길이 맞추기 함수 (대사 개수가 맞지 않을 때 대비)
# ==========================================
def align_lists(sub_eng, sub_other):
    if len(sub_eng) == len(sub_other):
        return sub_other
    elif len(sub_eng) > len(sub_other):
        result = list(sub_other)
        while len(result) < len(sub_eng):
            result.append(sub_other[-1] if sub_other else "이어서 설명합니다.")
        return result
    else:
        result = list(sub_other[:len(sub_eng)-1])
        combined = " ".join(sub_other[len(sub_eng)-1:])
        result.append(combined)
        return result

# ==========================================
# 3. WAV 파일 작성기 (머리표 정보 입히기)
# ==========================================
def save_wav_with_header(file_path, raw_pcm_data):
    """Raw PCM 데이터에 WAV 헤더(24kHz, 16-bit, Mono)를 입혀 저장"""
    with wave.open(file_path, 'wb') as wav_file:
        wav_file.setnchannels(1)     # 1채널 (모노)
        wav_file.setsampwidth(2)     # 16비트 (2바이트)
        wav_file.setframerate(24000) # 제미나이 3.1 tts 출력 표준인 24kHz
        wav_file.writeframes(raw_pcm_data)

# ==========================================
# 4. 메인 분석 및 재생성 로직
# ==========================================
def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("오류: GEMINI_API_KEY가 없습니다.")
        return

    client = genai.Client(api_key=api_key)
    output_dir = os.path.join("processed", "01_motivation")
    analysis_path = os.path.join(output_dir, "analysis.json")

    if not os.path.exists(analysis_path):
        print("오류: 기존 analysis.json 파일을 찾을 수 없습니다.")
        return

    # 기존 데이터 로드
    with open(analysis_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    original_sentences = data.get("sentences", [])
    new_sentences = []
    
    print("1. 한 문장 단위로 자막 분할 시작...")
    
    for s in original_sentences:
        # 문장 경계 분할 규칙 (마침표, 물음표, 느낌표 뒤에 공백이 있을 때)
        sub_eng = re.split(r'(?<=[.!?])\s+', s["english_text"].strip())
        sub_eng = [x for x in sub_eng if x]
        
        # 1문장만 있으면 그대로 유지
        if len(sub_eng) <= 1:
            new_sentences.append(s)
            continue
            
        # 여러 문장이 들어있을 경우 분할 작업 수행
        print(f" -> 분할 대상 발견 (인덱스 {s['index']}): 총 {len(sub_eng)}문장")
        
        sub_kor = re.split(r'(?<=[.!?])\s+', s["korean_text"].strip())
        sub_kor = [x for x in sub_kor if x]
        sub_kor = align_lists(sub_eng, sub_kor)
        
        sub_lecture = re.split(r'(?<=[.!?])\s+', s["lecture_script"].strip())
        sub_lecture = [x for x in sub_lecture if x]
        sub_lecture = align_lists(sub_eng, sub_lecture)
        
        # 글자 길이 비율대로 시간 분할
        start_sec = parse_time(s["start_time"])
        end_sec = parse_time(s["end_time"])
        duration = end_sec - start_sec
        total_chars = sum(len(x) for x in sub_eng)
        
        current_start = start_sec
        for i, eng_text in enumerate(sub_eng):
            frac = len(eng_text) / total_chars if total_chars > 0 else 1.0
            sub_dur = duration * frac
            sub_end = current_start + sub_dur
            
            # 단어장 매핑 (해당 분할 문장에 포함된 단어만 상속)
            vocab_for_sub = []
            for v in s["vocab_list"]:
                if v["word"].lower() in eng_text.lower():
                    vocab_for_sub.append(v)
            
            new_sentences.append({
                "index": 0, # 임시 설정, 추후 재정렬
                "start_time": format_time(current_start),
                "end_time": format_time(sub_end),
                "english_text": eng_text,
                "korean_text": sub_kor[i],
                "vocab_list": vocab_for_sub,
                "visual_description": s["visual_description"],
                "lecture_script": sub_lecture[i]
            })
            current_start = sub_end

    # 인덱스 재부여 (1부터 다시 정렬)
    for idx, s in enumerate(new_sentences, start=1):
        s["index"] = idx

    # 업데이트된 전체 JSON 구조 저장
    data["sentences"] = new_sentences
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"자막 분할 완료! 총 문장 수: {len(original_sentences)}개 -> {len(new_sentences)}개")

    # 2. 새로운 SRT 자막 파일 재생성
    print("2. 새로운 subtitle.srt 파일 작성 중...")
    srt_path = os.path.join(output_dir, "subtitle.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        for s in new_sentences:
            f.write(f"{s['index']}\n")
            f.write(f"{s['start_time']} --> {s['end_time']}\n")
            f.write(f"{s['english_text']}\n\n")
    print("새로운 SRT 자막 생성 완료!")

    # 3. 기존 오디오 폴더 리셋 (깨끗이 비우기)
    audio_dir = os.path.join(output_dir, "audio")
    print("3. 기존 오디오 폴더 비우기...")
    if os.path.exists(audio_dir):
        shutil.rmtree(audio_dir)
    os.makedirs(audio_dir, exist_ok=True)

    # 4. 제미나이 3.1 tts로 고품질 WAV 생성 (WAV 헤더 탑재)
    total_sentences = len(new_sentences)
    print(f"4. 총 {total_sentences}개 문장의 오디오 재생성 시작...")
    
    for i, s in enumerate(new_sentences):
        idx = s["index"]
        lecture_text = s["lecture_script"]
        audio_path = os.path.join(audio_dir, f"sentence_{idx}.wav")

        print(f"[{i+1}/{total_sentences}] 문장 {idx}번 오디오 생성 중... ('{lecture_text[:30]}...')")
        
        try:
            tts_prompt = f"아래 한국어 문장을 영어 강사처럼 다정하고 자연스럽게 한국어로 읽어줘. 절대 다른 설명은 하지 말고 이 문장만 자연스럽게 낭독한 오디오 데이터만 돌려줘:\n{lecture_text}"
            
            response = client.models.generate_content(
                model='gemini-3.1-flash-tts-preview',
                contents=tts_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Aoede"
                            )
                        )
                    )
                )
            )

            # 오디오 데이터 추출 및 WAV 헤더 파일 저장
            audio_saved = False
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    # 헤더를 입혀서 확실하게 저장!
                    save_wav_with_header(audio_path, part.inline_data.data)
                    audio_saved = True
                    break
            
            if audio_saved:
                print(f" -> 성공: sentence_{idx}.wav (WAV 헤더 포함) 저장 완료!")
            else:
                print(f" -> 에러: 응답에 오디오 데이터가 포함되어 있지 않습니다.")

        except Exception as e:
            print(f" -> 에러 발생 (문장 {idx}번): {e}")

        # API 호출 속도 제한(RPM) 우회를 위해 4초 대기
        if i < total_sentences - 1:
            print("안전 대기 중 (4초)...")
            time.sleep(4)

    print("\n자막 분할 및 오디오 헤더 작업이 모두 완료되었습니다! 🎈")

if __name__ == "__main__":
    main()
