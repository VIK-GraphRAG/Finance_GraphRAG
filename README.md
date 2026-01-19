# Finance GraphRAG 🚀

**Knowledge Graph-Based Financial Analysis System**  
반도체 및 금융 산업 분석을 위한 GraphRAG 시스템

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.15-red.svg)](https://neo4j.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31-orange.svg)](https://streamlit.io/)

---

## 📊 프로젝트 개요

이 프로젝트는 **Neo4j 그래프 데이터베이스**와 **Large Language Models (LLMs)**를 결합하여 복잡한 금융/반도체 산업 분석을 수행하는 시스템입니다.

### ✨ 주요 기능

- 🔍 **GraphRAG**: 지식 그래프 기반 검색 및 추론
- 🤖 **Multi-Agent System**: 질문 분해 → 정보 수집 → 분석 → 리포트 작성
- 📄 **PDF Processing**: OpenAI GPT-4o-mini를 사용한 고품질 엔티티 추출
- 💾 **Persistent Storage**: Neo4j에 영구 저장 (세션 종료 후에도 유지)
- 🎨 **Interactive UI**: Streamlit 기반 사용자 인터페이스
- 📈 **Graph Visualization**: 실시간 그래프 시각화
- 📝 **Citation System**: 모든 답변에 출처 번호 참조

---

## 🗂️ 프로젝트 구조

```
Finance_GraphRAG/
├── 📄 설정 파일
│   ├── .env, requirements.txt
│   ├── docker-compose.yml
│   └── Dockerfile
│
├── 💻 src/                 # 메인 소스 코드
│   ├── app.py             # FastAPI 서버
│   ├── streamlit_app.py   # Streamlit UI
│   ├── agents/            # Multi-Agent 시스템
│   ├── engine/            # GraphRAG 엔진
│   ├── db/                # Neo4j 데이터베이스
│   └── utils/             # 유틸리티
│
├── 🧪 scripts/            # 관리 스크립트
│   ├── upload/            # PDF 업로드
│   ├── seed/              # 데이터 시딩
│   ├── test/              # 테스트
│   └── utils/             # 유틸리티
│
├── 📊 data/baseline/      # Baseline 데이터
│   └── *.pdf              # 반도체/금융 PDF
│
└── 📚 문서
    ├── README.md          # 이 파일
    ├── PROJECT_STRUCTURE.md
    └── README_UPLOAD.md
```

📖 **상세 구조**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) 참조

---

## 🚀 빠른 시작

### 1️⃣ 환경 설정

```bash
# 저장소 클론
cd /Users/gyuteoi/Desktop/Finance_GraphRAG

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어서 API 키 입력
```

### 2️⃣ Docker로 실행 (권장)

```bash
# Docker Compose로 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 3️⃣ 직접 실행

```bash
# Python 의존성 설치
pip install -r requirements.txt

# Neo4j 시작 (별도 설치 필요)
# 또는 docker-compose up -d neo4j

# 서버 시작
./restart.sh
```

### 4️⃣ 접속

- **Streamlit UI**: http://localhost:8501
- **FastAPI Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474

---

## 📊 데이터 업로드

### PDF 파일 업로드

```bash
# 작은 PDF 빠르게 업로드 (4개)
python scripts/upload/quick_upload_pdfs.py

# 모든 baseline PDF 업로드
python scripts/upload/upload_baseline_pdfs.py
```

### 기본 데이터 시딩

```bash
# 반도체 온톨로지 시딩
python scripts/seed/seed_semiconductor.py

# 금융 데이터 시딩
python scripts/seed/seed_financial_data.py
```

📖 **상세 가이드**: [README_UPLOAD.md](README_UPLOAD.md) 참조

---

## 💡 사용 예시

### 1. Streamlit UI에서 질문하기

1. http://localhost:8501 접속
2. **Query 탭** 선택
3. 질문 입력: "Nvidia의 supply chain risk는 무엇인가?"
4. 결과 확인 (citation 번호 포함)

### 2. FastAPI로 질문하기

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the risks in TSMC supply chain?",
    "mode": "local",
    "search_type": "local"
  }'
```

### 3. Multi-Agent 모드 사용

```bash
curl -X POST "http://localhost:8000/agentic-query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Analyze Nvidia H100 GPU supply chain dependencies"
  }'
```

---

## 🏗️ 시스템 아키텍처

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Streamlit  │────▶│   FastAPI    │────▶│   Neo4j     │
│     UI      │     │   Backend    │     │   Database  │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Multi-Agent  │
                    │   System     │
                    └──────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ┌─────────┐      ┌──────────┐      ┌──────────┐
   │ Planner │      │Collector │      │ Analyst  │
   └─────────┘      └──────────┘      └──────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Writer     │
                    │  (Reporter)  │
                    └──────────────┘
```

### 데이터 흐름

```
PDF Upload → Entity Extraction → Neo4j Storage
                                      ↓
User Query → Query Analysis → Neo4j Retrieval → Reasoning → Report
                                                              ↓
                                                      Citation [1][2][3]
```

---

## 🧪 테스트

### 시스템 테스트

```bash
# Neo4j 연결 테스트
python scripts/test/test_neo4j_direct.py

# 백엔드 테스트
python scripts/test/test_backend.py

# 전체 시스템 테스트
python scripts/test/test_full_system.py
```

### 데이터 확인

```bash
# Neo4j 데이터 확인
python scripts/utils/check_neo4j_data.py

# 데이터베이스 뷰어
python scripts/utils/view_database.py
```

---

## 📝 환경 변수

`.env` 파일에 다음 변수를 설정하세요:

```bash
# OpenAI API
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1

# Perplexity API (옵션)
PERPLEXITY_API_KEY=pplx-...

# Neo4j Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# LLM Models
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Privacy Mode (옵션)
PRIVACY_MODE=false
```

---

## 📚 문서

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 프로젝트 구조 상세 설명
- [README_UPLOAD.md](README_UPLOAD.md) - PDF 업로드 가이드
- [scripts/README.md](scripts/README.md) - Scripts 사용법
- [prd.md](prd.md) - 제품 요구사항 문서

---

## 🔧 개발

### 새로운 Agent 추가

1. `src/agents/`에 새 에이전트 클래스 생성
2. `BaseAgent` 상속
3. `execute()` 메서드 구현
4. `langgraph_workflow.py`에 통합

### 새로운 엔드포인트 추가

1. `src/app.py`에 FastAPI 라우터 추가
2. `src/streamlit_app.py`에 UI 컴포넌트 추가

---

## 🐛 트러블슈팅

### Neo4j 연결 실패

```bash
# Docker 컨테이너 확인
docker-compose ps

# Neo4j 로그 확인
docker-compose logs neo4j

# Neo4j 재시작
docker-compose restart neo4j
```

### API 서버 오류

```bash
# 로그 확인
tail -f logs/*.log

# 서버 재시작
./restart.sh
```

### PDF 업로드 실패

```bash
# 단일 PDF 테스트
python scripts/upload/test_upload_one_pdf.py

# API 서버 상태 확인
curl http://localhost:8000/health
```

---

## 🤝 기여

이 프로젝트는 개인 프로젝트입니다. 

---

## 📄 라이선스

이 프로젝트는 개인 사용을 위한 것입니다.

---

## 📞 문의

문제가 발생하면 Issue를 생성하거나 로그를 확인하세요.

---

**Last Updated**: 2026-01-19  
**Version**: 2.0 (Refactored Structure)
