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
src/
├── agents/          # Multi-agent system (Analyst, Planner, Writer)
├── engine/          # Graph processing engine
│   ├── extractor.py       # Entity/Relationship extraction
│   ├── translator.py      # JSON → Cypher
│   ├── integrator.py      # PDF + CSV + JSON integration
│   ├── reasoner.py        # Multi-hop reasoning engine
│   ├── graphrag_engine.py # Core engine
│   └── privacy_graph_builder.py # Privacy-optimized builder
├── db/              # Neo4j integration
├── mcp/             # External tool integration
├── streamlit_app.py # Web UI
└── reasoning_ui.py  # Multi-hop reasoning UI
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
```bash
streamlit run src/graph_visualizer.py --server.port 8502
```

Visit: http://localhost:8502

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

---

## 🧠 Multi-Hop Reasoning System

### 멀티홉 추론 UI 실행
```bash
streamlit run src/reasoning_ui.py --server.port 8503
```

Visit: http://localhost:8503

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
