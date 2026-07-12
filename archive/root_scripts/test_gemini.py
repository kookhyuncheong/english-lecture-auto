import os
import time
from dotenv import load_dotenv
from google import genai

# 1. .env 파일의 환경 변수 로드
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("오류: GEMINI_API_KEY가 .env 파일에 설정되지 않았어! 확인해줘.")
    exit(1)

print(f"성공: API 키를 찾았어! (앞 글자 일부: {api_key[:10]}...)")

# 2. Gemini 클라이언트 초기화
print("Gemini API 클라이언트를 연결하는 중...")
client = genai.Client(api_key=api_key)

# 3. 비디오 파일 업로드
video_path = "01. How to get motivated even when you don't feel like it.mp4"
if not os.path.exists(video_path):
    print(f"오류: 폴더에 '{video_path}' 동영상이 없어! 파일명을 다시 확인해줘.")
    exit(1)

print(f"'{video_path}' 파일을 Gemini 서버로 업로드하는 중... 잠시만 기다려줘 (파일 크기에 따라 수십 초 정도 걸릴 수 있어)")
video_file = client.files.upload(file=video_path)
print(f"업로드 완료! AI 서버 내 파일 이름: {video_file.name}")

# 4. 비디오 처리 대기 (구글 서버가 비디오의 화면과 소리를 분석하는 단계야)
print("Gemini AI가 비디오를 분석(인덱싱)하는 중이야...")
start_time = time.time()
while video_file.state.name == "PROCESSING":
    print("비디오 분석 대기 중... (5초마다 확인하는 중)")
    time.sleep(5)
    video_file = client.files.get(name=video_file.name)

print(f"분석 완료 소요 시간: {time.time() - start_time:.1f}초")
print("비디오 처리 상태:", video_file.state.name)

if video_file.state.name == "ACTIVE":
    print("축하해! 비디오 분석이 완벽히 끝났어. 이제 AI에게 이 영상을 보고 공부용 자료를 만들어달라고 시킬 수 있어!")
    print(f"비디오 URI: {video_file.uri}")
else:
    print(f"오류: 비디오 처리가 실패했어. 상태: {video_file.state.name}")
