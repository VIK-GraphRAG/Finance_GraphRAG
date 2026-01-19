# Scripts Directory

이 디렉토리는 프로젝트 관리 및 유틸리티 스크립트를 포함합니다.

## 📁 구조

```
scripts/
├── upload/           # PDF 업로드 스크립트
│   ├── quick_upload_pdfs.py       # 작은 PDF 빠른 업로드
│   ├── upload_baseline_pdfs.py    # 모든 baseline PDF 업로드
│   └── upload_all_data.py         # JSON + PDF 통합 업로드
│
├── seed/             # 데이터 시딩 스크립트
│   ├── seed_baseline_graph.py     # 기본 그래프 데이터
│   ├── seed_semiconductor.py      # 반도체 온톨로지
│   └── seed_financial_data.py     # 금융 데이터
│
├── test/             # 테스트 스크립트
│   ├── test_backend.py            # 백엔드 테스트
│   ├── test_full_system.py        # 전체 시스템 테스트
│   ├── test_multihop.py           # 멀티홉 테스트
│   └── test_neo4j_direct.py       # Neo4j 직접 연결 테스트
│
└── utils/            # 유틸리티 스크립트
    ├── check_neo4j_data.py        # Neo4j 데이터 확인
    ├── view_database.py           # 데이터베이스 뷰어
    └── generate_baseline_pdfs.py  # Baseline PDF 생성기

## 🚀 주요 스크립트 사용법

### PDF 업로드
```bash
# 작은 PDF 빠르게 업로드
python scripts/upload/quick_upload_pdfs.py

# 모든 baseline PDF 업로드
python scripts/upload/upload_baseline_pdfs.py
```

### 데이터 시딩
```bash
# 반도체 온톨로지 시딩
python scripts/seed/seed_semiconductor.py

# 기본 그래프 데이터 시딩
python scripts/seed/seed_baseline_graph.py
```

### 테스트 실행
```bash
# Neo4j 연결 테스트
python scripts/test/test_neo4j_direct.py

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
