#!/bin/bash
# Docker 서비스 상태 확인 스크립트

echo "🔍 Docker 서비스 상태 확인 중..."
echo ""

# Docker 실행 확인
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker가 실행되지 않았습니다!"
    echo "   Docker Desktop을 실행해주세요."
    exit 1
fi

echo "✅ Docker 실행 중"
echo ""

# 컨테이너 상태 확인
echo "📊 컨테이너 상태:"
docker-compose ps
echo ""

# 서비스별 헬스 체크
echo "🏥 서비스 헬스 체크:"
echo ""

# Backend (FastAPI)
if docker ps | grep -q finance-graphrag-backend; then
    echo -n "  Backend (FastAPI): "
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 정상 (http://localhost:8000)"
    else
        echo "⚠️  응답 없음"
    fi
else
    echo "  Backend: ❌ 실행 중이 아님"
fi

# Frontend (Streamlit)
if docker ps | grep -q finance-graphrag-frontend; then
    echo -n "  Frontend (Streamlit): "
    if curl -s http://localhost:8501 > /dev/null 2>&1; then
        echo "✅ 정상 (http://localhost:8501)"
    else
        echo "⚠️  응답 없음"
    fi
else
    echo "  Frontend: ❌ 실행 중이 아님"
fi

# Neo4j
if docker ps | grep -q finance-graphrag-neo4j; then
    echo -n "  Neo4j: "
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        echo "✅ 정상 (http://localhost:7474)"
    else
        echo "⚠️  응답 없음"
    fi
else
    echo "  Neo4j: ❌ 실행 중이 아님"
fi

echo ""
echo "📋 최근 로그 (마지막 10줄):"
echo "--- Backend ---"
docker-compose logs --tail=10 backend 2>/dev/null || echo "  로그 없음"
echo ""
echo "--- Frontend ---"
docker-compose logs --tail=10 frontend 2>/dev/null || echo "  로그 없음"
echo ""

echo "✅ 확인 완료!"
echo ""
echo "🌐 접속 주소:"
echo "   - Streamlit: http://localhost:8501"
echo "   - FastAPI:   http://localhost:8000"
echo "   - Neo4j:    http://localhost:7474"
