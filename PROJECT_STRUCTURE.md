# Finance GraphRAG - 프로젝트 구조

## 📁 디렉토리 구조

```
Finance_GraphRAG/
│
├── 📄 설정 파일
│   ├── .env                    # 환경 변수 (API 키, DB 설정)
│   ├── .gitignore              # Git 무시 파일
│   ├── requirements.txt        # Python 의존성
│   ├── docker-compose.yml      # Docker 컴포즈 설정
│   ├── Dockerfile              # Docker 이미지 빌드
│   └── prd.md                  # 제품 요구사항 문서
│
├── 📚 문서
│   ├── README.md               # 프로젝트 메인 문서
│   ├── README_UPLOAD.md        # PDF 업로드 가이드
│   └── PROJECT_STRUCTURE.md    # 이 파일
│
├── 🚀 실행 스크립트
│   ├── start.sh                # 서버 시작
│   ├── restart.sh              # 서버 재시작
│   ├── deploy.sh               # 배포
│   └── run_upload.sh           # PDF 업로드 실행
│
├── 📊 data/                    # 데이터 저장소
│   └── baseline/               # Baseline PDF 데이터
│       ├── README.md
│       ├── *.pdf               # 반도체/금융 PDF 문서
│       └── *.json              # 구조화된 데이터
│
├── 💻 src/                     # 메인 소스 코드
│   │
│   ├── 🌐 app.py              # FastAPI 메인 서버
│   ├── 🎨 streamlit_app.py    # Streamlit UI
│   ├── ⚙️  config.py           # 전역 설정
│   │
│   ├── 🤖 agents/             # Multi-Agent 시스템
│   │   ├── __init__.py
│   │   ├── base_agent.py           # 베이스 에이전트 클래스
│   │   ├── planner_agent.py        # 질문 분해
│   │   ├── kb_collector_agent.py   # 정보 수집
│   │   ├── analyst_agent.py        # 데이터 분석
│   │   ├── writer_agent.py         # 리포트 작성
│   │   ├── agent_context.py        # 공유 컨텍스트
│   │   ├── memory_manager.py       # 메모리 관리
│   │   └── langgraph_workflow.py   # LangGraph 워크플로우
│   │
│   ├── 🔍 engine/             # GraphRAG 엔진
│   │   ├── __init__.py
│   │   ├── graphrag_engine.py      # 메인 GraphRAG 엔진
│   │   ├── extractor.py            # 엔티티 추출
│   │   ├── integrator.py           # 데이터 통합
│   │   ├── neo4j_retriever.py      # Neo4j 검색
│   │   ├── query_analyzer.py       # 쿼리 분석
│   │   ├── reasoner.py             # 추론 엔진
│   │   ├── reporter.py             # 리포트 생성
│   │   ├── final_reporter.py       # 최종 리포트
│   │   ├── search_handler.py       # 검색 핸들러 (Perplexity)
│   │   ├── local_worker.py         # 로컬 모델 워커
│   │   └── ...                     # 기타 엔진 컴포넌트
│   │
│   ├── 💾 db/                 # 데이터베이스
│   │   ├── __init__.py
│   │   └── neo4j_db.py             # Neo4j 데이터베이스 클래스
│   │
│   ├── 🔧 utils/              # 유틸리티
│   │   ├── __init__.py
│   │   ├── logger.py               # 로깅
│   │   └── error_logger.py         # 에러 로깅
│   │
│   ├── 🔌 mcp/                # MCP (Model Context Protocol)
│   │   ├── __init__.py
│   │   ├── manager.py              # MCP 매니저
│   │   └── tools.py                # MCP 도구
│   │
│   ├── 📦 models/             # 데이터 모델
│   │   ├── __init__.py
│   │   └── neo4j_models.py         # Neo4j 모델
│   │
│   ├── utils.py                    # 공통 유틸리티 함수
│   ├── citation_validator.py       # Citation 검증
│   ├── entity_resolver.py          # 엔티티 해석
│   └── health_check.py             # 헬스 체크
│
├── 🧪 scripts/                # 관리 스크립트
│   │
│   ├── 📤 upload/             # PDF 업로드
│   │   ├── quick_upload_pdfs.py        # 작은 PDF 빠른 업로드
│   │   ├── upload_baseline_pdfs.py     # Baseline PDF 업로드
│   │   ├── upload_all_data.py          # 전체 데이터 업로드
│   │   └── test_upload_one_pdf.py      # 단일 PDF 테스트
│   │
│   ├── 🌱 seed/               # 데이터 시딩
│   │   ├── seed_baseline_graph.py      # 기본 그래프
│   │   ├── seed_semiconductor.py       # 반도체 온톨로지
│   │   └── seed_financial_data.py      # 금융 데이터
│   │
│   ├── 🧪 test/               # 테스트
│   │   ├── test_backend.py             # 백엔드 테스트
│   │   ├── test_full_system.py         # 전체 시스템 테스트
│   │   ├── test_multihop.py            # 멀티홉 테스트
│   │   └── test_neo4j_direct.py        # Neo4j 연결 테스트
│   │
│   ├── 🛠️  utils/             # 유틸리티
│   │   ├── check_neo4j_data.py         # Neo4j 데이터 확인
│   │   ├── view_database.py            # DB 뷰어
│   │   └── generate_baseline_pdfs.py   # PDF 생성기
│   │
│   └── README.md               # Scripts 사용 가이드
│
├── 🧪 evaluator/              # 평가 시스템
│   ├── __init__.py
│   ├── test_bench.py           # 테스트 벤치
│   ├── test_cases.json         # 테스트 케이스
│   └── evaluation_report.json  # 평가 결과
│
├── 📚 lib/                    # 프론트엔드 라이브러리
│   ├── vis-9.1.2/             # Vis.js (그래프 시각화)
│   ├── tom-select/            # Tom Select (선택 UI)
│   └── bindings/              # 바인딩
│
└── 📝 logs/                   # 로그 파일
    └── *.log

```

## 🎯 주요 컴포넌트

### 1. FastAPI 서버 (`src/app.py`)
- RESTful API 엔드포인트 제공
- PDF 업로드 및 처리
- GraphRAG 쿼리 처리
- Multi-Agent 워크플로우 실행

### 2. Streamlit UI (`src/streamlit_app.py`)
- 사용자 인터페이스
- PDF 업로드 인터페이스
- 그래프 시각화
- 질의응답 인터페이스

### 3. Multi-Agent 시스템 (`src/agents/`)
- **Planner**: 질문을 서브태스크로 분해
- **Collector**: 정보 수집 (GraphRAG + MCP)
- **Analyst**: 데이터 검증 및 분석
- **Writer**: 최종 리포트 작성

### 4. GraphRAG 엔진 (`src/engine/`)
- **Extractor**: PDF에서 엔티티/관계 추출
- **Integrator**: Neo4j에 데이터 통합
- **Retriever**: 그래프 검색
- **Reasoner**: 멀티홉 추론
- **Reporter**: 리포트 생성

### 5. 데이터베이스 (`src/db/`)
- **Neo4j**: 그래프 데이터베이스
- 엔티티, 관계, 지식 그래프 저장
- 영구 저장 (세션 종료 후에도 유지)

## 🚀 빠른 시작

### 1. 서버 시작
```bash
./restart.sh
```

### 2. UI 접속
- Streamlit: http://localhost:8501
- FastAPI: http://localhost:8000
- Neo4j Browser: http://localhost:7474

### 3. PDF 업로드
```bash
# 작은 PDF 빠르게 업로드
python scripts/upload/quick_upload_pdfs.py

# 모든 PDF 업로드
python scripts/upload/upload_baseline_pdfs.py
```

### 4. 데이터 확인
```bash
# Neo4j 데이터 확인
python scripts/utils/check_neo4j_data.py

# 테스트 실행
python scripts/test/test_neo4j_direct.py
```

## 📝 설정 파일

### `.env`
```bash
# API Keys
OPENAI_API_KEY=sk-...
PERPLEXITY_API_KEY=pplx-...

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Models
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

## 🔧 개발 가이드

### 새로운 Agent 추가
1. `src/agents/` 에 새 에이전트 클래스 생성
2. `BaseAgent` 상속
3. `execute()` 메서드 구현
4. `langgraph_workflow.py`에 통합

### 새로운 엔드포인트 추가
1. `src/app.py`에 FastAPI 라우터 추가
2. `src/streamlit_app.py`에 UI 컴포넌트 추가

### 테스트 추가
1. `scripts/test/`에 테스트 스크립트 추가
2. `evaluator/test_cases.json`에 테스트 케이스 추가

## 📊 데이터 흐름

```
PDF 업로드 → Extractor (엔티티 추출) → Integrator (Neo4j 저장)
                                              ↓
사용자 질문 → Query Analyzer → Neo4j Retriever → Reasoner → Reporter
                                              ↓
                                          Multi-Agent
                                          (Planner → Collector → Analyst → Writer)
```

## 🔍 트러블슈팅

### Neo4j 연결 실패
```bash
# Docker 컨테이너 확인
docker-compose ps

# Neo4j 로그 확인
docker-compose logs neo4j
```

### API 서버 오류
```bash
# 로그 확인
tail -f logs/*.log

# 서버 재시작
./restart.sh
```

## 📚 추가 문서

- [README.md](README.md) - 프로젝트 개요
- [README_UPLOAD.md](README_UPLOAD.md) - PDF 업로드 가이드
- [scripts/README.md](scripts/README.md) - Scripts 사용법
- [prd.md](prd.md) - 제품 요구사항

---

**Last Updated**: 2026-01-19  
**Version**: 2.0 (Refactored)
