#!/bin/bash
set -e

# 필수: Docker, docker-compose 설치 확인
if ! command -v docker &> /dev/null; then
    echo "Docker가 설치되어 있지 않습니다. https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose가 설치되어 있지 않습니다."
    exit 1
fi

# 필수: .env 파일 확인/생성
if [ ! -f ".env" ]; then
    echo ".env 파일이 없습니다. env.docker.example을 .env로 복사합니다."
    cp env.docker.example .env
fi

# 이미지 빌드 및 컨테이너 실행
docker-compose build --no-cache
docker-compose up -d

# 서비스 상태 출력
docker-compose ps

echo ""
echo "접속 URL:"
echo "  - Streamlit: http://localhost:8501"
echo "  - FastAPI:   http://localhost:8000/docs"
echo "  - Neo4j:     http://localhost:7474"
