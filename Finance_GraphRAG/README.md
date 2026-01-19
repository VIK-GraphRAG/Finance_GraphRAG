# VIK AI - Privacy-First Financial GraphRAG

Enterprise-grade financial intelligence system powered by knowledge graphs.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Neo4j (Docker)
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest

# 3. Configure environment
cp .env.backup .env
# Edit .env with your settings

# 4. Start services
./start.sh
```

Visit: http://localhost:8501

## ✨ Features

- **Privacy-First**: Offline processing with local LLMs (Ollama)
- **Graph Intelligence**: Neo4j-powered knowledge graph
- **Multi-Hop Reasoning**: 2-3 hop logical inference for hidden insights
- **Data Integration**: Merge PDF + CSV + JSON into unified knowledge graph
- **Multi-Agent**: Collaborative AI agents for deep analysis
- **8GB RAM Optimized**: Efficient memory management
- **Real-time Analysis**: Fast query processing with caching
- **Path Visualization**: Interactive reasoning path display

## 📦 Architecture

```
Finance_GraphRAG/
├── src/                    # Source code
│   ├── agents/            # Multi-agent system
│   ├── engine/            # Graph processing engine
│   │   ├── extractor.py        # Entity/Relationship extraction
│   │   ├── translator.py       # JSON → Cypher
│   │   ├── integrator.py       # PDF + CSV + JSON integration
│   │   ├── reasoner.py         # Multi-hop reasoning engine
│   │   ├── query_processor.py  # Smart query processing
│   │   └── graphrag_engine.py  # Core engine
│   ├── db/                # Neo4j integration
│   ├── mcp/               # External tool integration
│   ├── app.py             # FastAPI backend
│   └── streamlit_app.py   # Streamlit UI
├── scripts/               # Utility scripts
│   ├── batch_upload.py         # Batch data upload
│   ├── manage_neo4j.py         # Database management
│   ├── reset_and_load_baseline.py  # Reset & load baseline
│   └── seed_*.py               # Data seeding scripts
├── tests/                 # Test files
├── docs/                  # Documentation
├── data/                  # Data files
│   └── baseline/          # Baseline data (CSV, PDF, JSON)
├── logs/                  # Log files
├── backups/               # Database backups
└── evaluator/             # Evaluation tools
```

## 🔧 Configuration

Key environment variables in `.env`:

```bash
# Mode
RUN_MODE=API              # API (OpenAI) or LOCAL (Ollama)
PRIVACY_MODE=true         # Enable privacy-first mode

# OpenAI
OPENAI_API_KEY=sk-...

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=password

# Ollama (for Privacy Mode)
OLLAMA_BASE_URL=http://localhost:11434
```

## 📊 Usage

### PDF Analysis
1. Go to "Data Ingestion" tab
2. Upload PDF document
3. System extracts entities and builds knowledge graph

### Query Interface
1. Go to "Query Interface" tab
2. Ask questions about your data
3. Get citation-backed answers with confidence scores

### Advanced Settings
- **Temperature**: Control creativity (0.0-2.0)
- **Retrieval Chunks**: Number of context chunks (5-50)
- **Web Search**: Enable real-time web data
- **Multi-Agent**: Use collaborative AI pipeline

## 📦 Database Management

### Batch Upload (일괄 업로드)
폴더의 모든 CSV, JSON, PDF 파일을 한번에 Neo4j에 업로드:

```bash
# 기본 사용
python scripts/batch_upload.py <폴더경로>

# 예시
python scripts/batch_upload.py ./data/baseline
python scripts/batch_upload.py /path/to/your/data
```

**자동 처리 기능:**
- CSV: 첫 번째 컬럼을 엔티티로, 나머지를 속성으로 자동 설정
- JSON: 루트 키 자동 감지
- PDF: 로컬 모델로 엔티티 추출
- 파일명 기반 엔티티 타입 자동 분류

### Database Management (데이터베이스 관리)

```bash
# 통계 조회
python scripts/manage_neo4j.py stats

# 백업 생성
python scripts/manage_neo4j.py export
python scripts/manage_neo4j.py export my_backup.json

# 백업 목록
python scripts/manage_neo4j.py backups

# 백업 복원
python scripts/manage_neo4j.py import backups/neo4j_backup_20260119_120000.json

# 데이터베이스 초기화 (주의!)
python scripts/manage_neo4j.py clear
```

**사용 시나리오:**

1. **초기 설정 (1회만)**
```bash
python scripts/reset_and_load_baseline.py
```

2. **새 데이터 추가**
```bash
python scripts/batch_upload.py data/my_data
python scripts/manage_neo4j.py stats
```

3. **정기 백업**
```bash
python scripts/manage_neo4j.py export
python scripts/manage_neo4j.py backups
```


## 🛠️ Development

```bash
# Run tests
python -m pytest tests/

# Check lints
python -m flake8 src/

# Format code
python -m black src/
```

## 📝 License

MIT License - See LICENSE file for details

## 🕸️ Graph Visualization

### 실시간 그래프 시각화
메인 Streamlit UI의 **"🕸️ Graph Visualizer"** 탭에서 바로 사용 가능합니다!

```bash
./start.sh
# 또는
streamlit run src/streamlit_app.py --server.port 8501
```

Visit: http://localhost:8501 → **Graph Visualizer 탭**

### 기능
- **All Nodes**: 전체 그래프 보기
- **Company Focus**: 특정 기업 중심 네트워크
- **Risk Analysis**: 리스크 관계 시각화
- **Custom Query**: Cypher 쿼리 직접 입력

### 색상 구분
- 🔴 Company (기업)
- 🔵 Country (국가)
- 🟢 Industry (산업)
- 🟠 MacroIndicator (거시경제)
- 🟣 FinancialMetric (재무지표)

### 인터랙티브 기능
- 노드 드래그로 위치 조정
- 클릭으로 연결된 노드 확인
- 줌/팬으로 그래프 탐색
- 물리 시뮬레이션으로 자동 배치
- 실시간 노드 검색 및 필터링

---

## 🧠 Multi-Hop Reasoning System

### 통합된 인터페이스
모든 기능이 **하나의 Streamlit 앱 (Port 8501)** 에 통합되었습니다!

```bash
./start.sh
```

Visit: http://localhost:8501

**탭 구조:**
- 📊 **Query Interface**: 질문 & 답변
- 📥 **Data Ingestion**: PDF 업로드 & 인덱싱
- 📁 **Data Sources**: 데이터 소스 관리
- 🕸️ **Graph Visualizer**: 지식 그래프 시각화

### 핵심 기능

#### 1. 데이터 통합 (Data Integration)
- **PDF + CSV + JSON** 통합 인덱싱
- 엔티티 자동 병합 (예: 'NVDA' → 'Nvidia')
- 지표 데이터 연결

#### 2. 멀티홉 추론 (Multi-Hop Reasoning)
- **2-3 hop** 논리적 추론 체인
- A → B → C → D 인과관계 분석
- 숨겨진 리스크 발견

#### 3. 추론 경로 시각화
- 인터랙티브 경로 그래프
- 노드 및 관계 상세 정보
- 신뢰도 기반 색상 코딩

### 사용 예시

```python
# 질문: "How does Taiwan tension affect Nvidia?"

# 추론 결과:
💡 Because Nvidia depends on TSMC (high criticality), 
   and TSMC is located in Taiwan, and Taiwan faces 
   geopolitical tension, therefore Nvidia is exposed 
   to significant supply chain disruption risk.

📊 Confidence: 85%

🔗 Reasoning Path:
   Taiwan Strait Tension → Taiwan → TSMC → Nvidia
```

### 고급 사용법

자세한 내용은 [Multi-Hop Reasoning Guide](MULTIHOP_REASONING_GUIDE.md) 참조

### API 사용
```python
import asyncio
from engine.reasoner import MultiHopReasoner

async def analyze():
    reasoner = MultiHopReasoner()
    result = await reasoner.reason(
        question="Nvidia의 공급망 리스크는?",
        max_hops=3
    )
    print(result['inference'])
    reasoner.close()

asyncio.run(analyze())
```

---

## 🧪 Testing

### 멀티홉 시스템 테스트
```bash
python test_multihop_system.py
```

테스트 항목:
1. ✅ Entity Resolver - 엔티티 이름 정규화
2. ✅ Data Integrator - CSV/JSON 통합
3. ✅ Multi-Hop Reasoner - 추론 엔진
4. ✅ End-to-End - 전체 워크플로우
