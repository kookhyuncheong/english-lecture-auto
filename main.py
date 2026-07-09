import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# FastAPI 애플리케이션 생성
app = FastAPI(title="AI English Lecture Assistant")

# 1. static 폴더의 프론트엔드 파일(HTML, CSS, JS)을 서비스하도록 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. processed 폴더의 분석 자막(JSON) 및 음성(WAV) 파일을 서비스하도록 설정
app.mount("/processed", StaticFiles(directory="processed"), name="processed")

# 3. 브라우저에서 처음 접속하면 index.html 화면을 띄워줌
@app.get("/")
async def get_index():
    index_path = os.path.join("static", "index.html")
    if not os.path.exists(index_path):
        return {"error": "static/index.html 파일을 찾을 수 없습니다. 프론트엔드가 생성되었는지 확인해주세요."}
    return FileResponse(index_path)

# 4. 동영상을 스트리밍 전송해주는 엔드포인트
# FastAPI의 FileResponse는 기본적으로 HTML5 비디오의 범위 요청(Range Requests)을 지원하여,
# 동영상 내 시각 탐색(Seek) 및 순간이동 기능이 끊김 없이 매끄럽게 작동합니다.
@app.get("/video")
async def get_video():
    video_path = os.path.join("static", "video.mp4")
    if not os.path.exists(video_path):
        return {"error": f"비디오 파일 '{video_path}'을 찾을 수 없습니다."}
    return FileResponse(video_path)

# 직접 실행 시 uvicorn을 통해 8000포트로 로컬 웹 서버 시작
if __name__ == "__main__":
    import uvicorn
    print("\n========================================================")
    print(" AI 영어 강의 튜터 로컬 웹 서버를 시작합니다!")
    print(" 크롬 브라우저를 열고 다음 주소에 접속해보세요:")
    print(" http://localhost:8000")
    print("========================================================\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
