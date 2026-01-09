#!/bin/bash
# Docker Compose 실행 스크립트

echo "🚀 Finance GraphRAG Docker 시작 중..."

# Docker 실행 확인
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker가 실행되지 않았습니다!"
    echo "   Docker Desktop을 실행해주세요."
    exit 1
fi

# .env 파일 확인
if [ ! -f .env ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사합니다..."
    cp .env.example .env
    echo "✅ .env 파일이 생성되었습니다."
    echo "   ⚠️  .env 파일을 편집하여 API 키와 비밀번호를 설정해주세요!"
    echo "   nano .env"
    exit 1
fi

# Docker Compose 실행
echo "📦 Docker 이미지 빌드 및 컨테이너 시작..."
docker-compose up --build -d

# 서비스 상태 확인
echo ""
echo "📊 서비스 상태:"
docker-compose ps

echo ""
echo "✅ 서비스가 시작되었습니다!"
echo ""
echo "🌐 접속 주소:"
echo "   - Streamlit: http://localhost:8501"
echo "   - FastAPI:   http://localhost:8000"
echo "   - Neo4j:    http://localhost:7474"
echo ""
echo "📋 유용한 명령어:"
echo "   로그 확인:    docker-compose logs -f"
echo "   서비스 중지:  docker-compose down"
echo "   재시작:       docker-compose restart"
