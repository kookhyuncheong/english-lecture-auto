# 1. Base Image 선택
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 환경 변수 설정
ENV PYTHONUNBUFFERED=1

# 4. 필수 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드 및 정적 자산, 비디오 파일 복사
COPY . .

# 6. Cloud Run 환경 포트 설정 및 서버 실행
# Cloud Run은 환경 변수 $PORT를 통해 포트 번호를 제공합니다. (기본값 8080)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
