# 🧠 Multi-Hop Reasoning System Guide

## 개요

PDF 문서와 CSV/JSON 지표 데이터를 통합하여 **2-3단계 멀티홉 추론**이 가능한 시스템입니다.

### 핵심 기능

1. **통합 인덱서 (Integrator)**: PDF + CSV + JSON → Neo4j 통합
2. **멀티홉 추론 (Reasoner)**: 2-3 hop 논리적 추론 체인
3. **인사이트 도출**: A→B→C→D 인과관계 분석
4. **경로 시각화**: 추론 경로를 그래프로 표시

---

## 1. 데이터 통합 (engine/integrator.py)

### 주요 클래스

#### `EntityResolver`
- **역할**: 엔티티 이름 정규화
- **예시**: 'NVDA', 'Nvidia', 'NVIDIA Corp' → 'Nvidia'

```python
from engine.integrator import EntityResolver

# 엔티티 해석
canonical = EntityResolver.resolve('NVDA')  # → 'Nvidia'

# 새 별칭 추가
EntityResolver.add_alias('Tesla', ['TSLA', 'Tesla Inc', 'Tesla Motors'])
```

#### `DataIntegrator`
- **역할**: 다양한 데이터 소스를 Neo4j에 통합

### 사용 예시

#### 1) CSV 인덱싱

```python
from engine.integrator import DataIntegrator

integrator = DataIntegrator()

# CSV 파일 (예: company_financials.csv)
# Company,Revenue,MarketCap,Growth
# Nvidia,60.9,1200,126
# Intel,54.2,180,2

integrator.ingest_csv(
    csv_path='data/company_financials.csv',
    mapping={
        'Company': 'entity_name',  # 엔티티 식별 컬럼
        'Revenue': 'property',      # 속성으로 저장
        'MarketCap': 'property',
        'Growth': 'property'
    }
)
```

#### 2) JSON 인덱싱

```python
# JSON 파일 (예: indicators.json)
# {
#   "indicators": [
#     {
#       "name": "US-China Trade War",
#       "type": "geopolitical",
#       "severity": 0.85,
#       "affected_sectors": ["Semiconductor", "Technology"]
#     }
#   ]
# }

integrator.ingest_json(
    json_path='data/indicators.json',
    schema={
        'root': 'indicators',           # JSON 루트 키
        'entity_key': 'name',           # 엔티티 이름 필드
        'entity_type': 'MacroIndicator',
        'relationships': [
            {
                'type': 'AFFECTS',
                'target_key': 'affected_sectors',  # 배열 필드
                'target_type': 'Industry'
            }
        ]
    }
)
```

#### 3) PDF 엔티티 통합

```python
# PDF에서 추출한 엔티티
pdf_entities = [
    {
        'name': 'Nvidia',
        'type': 'Company',
        'context': 'Leading GPU manufacturer with 80% AI chip market share'
    },
    {
        'name': 'Jensen Huang',
        'type': 'Person',
        'context': 'CEO of Nvidia since 1993'
    }
]

integrator.ingest_pdf_entities(pdf_entities)
```

#### 4) 지표-엔티티 연결

```python
# 재무 지표를 회사에 연결
metrics = [
    {'company': 'Nvidia', 'metric': 'Revenue', 'value': 60.9, 'period': 'FY2024'},
    {'company': 'Nvidia', 'metric': 'Growth Rate', 'value': 126, 'period': 'YoY 2024'}
]

integrator.link_metrics_to_entities(metrics)
```

#### 5) 통계 확인

```python
stats = integrator.get_stats()
print(stats)
# {
#   'entities_merged': 25,
#   'relationships_created': 48,
#   'csv_records': 10,
#   'json_records': 5,
#   'pdf_chunks': 10
# }

integrator.close()
```

---

## 2. 멀티홉 추론 (engine/reasoner.py)

### 주요 클래스

#### `MultiHopReasoner`
- **역할**: 2-3 hop 논리적 추론 수행
- **기능**:
  1. LLM 기반 Cypher 쿼리 생성
  2. Neo4j에서 경로 탐색
  3. 논리적 인과관계 도출

### 사용 예시

```python
import asyncio
from engine.reasoner import MultiHopReasoner

async def analyze_question():
    reasoner = MultiHopReasoner()
    
    # 질문
    question = "How does Taiwan tension affect Nvidia?"
    
    # 멀티홉 추론 (최대 3 hop)
    result = await reasoner.reason(question, max_hops=3)
    
    print(f"💡 Inference: {result['inference']}")
    print(f"📊 Confidence: {result['confidence']:.1%}")
    
    # 추론 경로
    for i, path in enumerate(result['reasoning_paths'], 1):
        nodes = [n['name'] for n in path['nodes']]
        print(f"Path {i}: {' → '.join(nodes)}")
    
    reasoner.close()

# 실행
asyncio.run(analyze_question())
```

### 출력 예시

```
💡 Inference: Because Nvidia depends on TSMC (high criticality), 
and TSMC is located in Taiwan, and Taiwan faces geopolitical 
tension with China, therefore Nvidia is exposed to significant 
supply chain disruption risk from Taiwan Strait conflict.

📊 Confidence: 85.0%

Path 1: Taiwan Strait Tension → Taiwan → TSMC → Nvidia
Path 2: US-China Trade War → Semiconductor Sector → Nvidia
```

### 추론 타입

1. **risk_chain**: 리스크 전파 경로
2. **influence_propagation**: 영향력 확산
3. **causal_inference**: 인과관계 추론
4. **impact_analysis**: 영향도 분석

---

## 3. Streamlit UI (reasoning_ui.py)

### 실행 방법

```bash
cd Finance_GraphRAG
streamlit run src/reasoning_ui.py --server.port 8503
```

### 주요 기능

#### 1) 데이터 통합
- 사이드바에서 CSV/JSON 파일 업로드
- 자동으로 Neo4j에 통합

#### 2) 질문 입력
- 자연어 질문 입력 (한글/영어)
- 예시:
  - "Nvidia의 공급망 리스크는?"
  - "미중 갈등이 반도체 업계에 미치는 영향은?"
  - "How does Taiwan tension affect Apple?"

#### 3) 추론 결과
- **논리적 추론**: A→B→C→D 인과관계
- **신뢰도**: 0-100% (경로 수, 관계 강도 기반)
- **추론 체인**: 단계별 논리 전개
- **경로 그래프**: 시각적 표현

#### 4) 설정
- **Maximum Hops**: 추론 깊이 (1-4)

---

## 4. 활용 예시

### 예시 1: 공급망 리스크 분석

**질문**: "Nvidia의 공급망 리스크는?"

**추론 과정**:
1. Nvidia → DEPENDS_ON → TSMC (high criticality)
2. TSMC → LOCATED_IN → Taiwan
3. Taiwan Strait Tension → AFFECTS → Taiwan (severity: 0.95)

**결론**: TSMC 의존도가 높고, TSMC가 대만에 위치하며, 대만이 지정학적 긴장 상태에 있으므로, Nvidia는 공급망 중단 리스크에 심각하게 노출되어 있음.

---

### 예시 2: 거시경제 영향 분석

**질문**: "미중 무역전쟁이 애플에 미치는 영향은?"

**추론 과정**:
1. US-China Trade War → AFFECTS → China
2. China → MAJOR_MARKET_FOR → Apple
3. China → MANUFACTURING_HUB → Apple

**결론**: 미중 무역전쟁이 중국 시장에 영향을 주고, 중국이 애플의 주요 시장이자 제조 거점이므로, 애플은 매출 감소 및 제조 비용 증가 리스크에 직면함.

---

### 예시 3: 인재 유출 영향

**질문**: "Tesla의 인재 유출이 경쟁사에 미치는 영향은?"

**추론 과程**:
1. Key Engineer → WORKS_AT → Tesla
2. Key Engineer → MOVED_TO → Lucid Motors
3. Lucid Motors → COMPETES_WITH → Tesla

**결론**: 핵심 엔지니어가 Tesla에서 경쟁사 Lucid Motors로 이직하면서, Tesla의 기술 우위가 약화되고 Lucid의 경쟁력이 강화될 가능성.

---

## 5. 고급 활용

### 커스텀 엔티티 별칭 추가

```python
from engine.integrator import EntityResolver

# 한글-영문 매핑
EntityResolver.add_alias('삼성전자', ['Samsung', 'Samsung Electronics', '005930'])
EntityResolver.add_alias('SK하이닉스', ['SK Hynix', 'Hynix', '000660'])
```

### 커스텀 추론 프롬프트

```python
from engine.reasoner import MultiHopReasoner

reasoner = MultiHopReasoner()

# 특정 관계 타입만 탐색
query_spec = await reasoner.generate_multihop_query(
    question="Find all geopolitical risks for Nvidia",
    max_hops=3
)

# Cypher 수정
custom_cypher = query_spec['cypher'].replace(
    "WHERE type(target)",
    "WHERE type(target) = 'MacroIndicator' AND target.type = 'geopolitical'"
)

# 실행
paths = reasoner.execute_multihop_query(custom_cypher)
```

---

## 6. 성능 최적화

### 8GB RAM 환경

1. **배치 처리**: 엔티티 100개씩 처리
2. **인덱스 생성**: Neo4j에서 `name` 필드 인덱싱
   ```cypher
   CREATE INDEX entity_name IF NOT EXISTS FOR (n:Company) ON (n.name)
   ```
3. **경로 제한**: `max_hops=2` 로 설정하여 쿼리 부하 감소

### 대용량 데이터 처리

```python
# Generator 패턴 사용
def process_large_csv(csv_path):
    integrator = DataIntegrator()
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        batch = []
        
        for row in reader:
            batch.append(row)
            
            if len(batch) >= 100:
                # 100개씩 처리
                for item in batch:
                    integrator.merge_entity(
                        name=item['name'],
                        entity_type='Company',
                        properties=item
                    )
                batch = []
        
        # 남은 데이터 처리
        for item in batch:
            integrator.merge_entity(
                name=item['name'],
                entity_type='Company',
                properties=item
            )
    
    integrator.close()
```

---

## 7. 문제 해결

### 1) 추론 경로가 없음

**원인**: 그래프에 데이터가 부족하거나 관계가 연결되지 않음

**해결**:
```python
# 1. 데이터 확인
with GraphDatabase.driver(NEO4J_URI, auth=(user, pw)) as driver:
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) as count")
        print(f"Total nodes: {result.single()['count']}")

# 2. 관계 확인
result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
print(f"Total relationships: {result.single()['count']}")

# 3. 누락된 관계 추가
integrator = DataIntegrator()
integrator.create_relationship('Nvidia', 'TSMC', 'DEPENDS_ON', {'criticality': 0.9})
```

### 2) 신뢰도가 낮음

**원인**: 경로가 간접적이거나 관계 강도가 약함

**해결**:
```python
# 관계에 weight/severity 속성 추가
integrator.create_relationship(
    'Taiwan Strait Tension',
    'Taiwan',
    'THREATENS',
    {'severity': 0.95, 'probability': 0.7}
)
```

### 3) 속도가 느림

**원인**: 대규모 그래프 탐색

**해결**:
```python
# max_hops 감소
result = await reasoner.reason(question, max_hops=2)

# Neo4j 인덱스 확인
# SHOW INDEXES
```

---

## 8. 다음 단계

1. **실시간 데이터 통합**: API에서 최신 지표 자동 수집
2. **시계열 분석**: 시간에 따른 리스크 변화 추적
3. **알림 시스템**: 임계값 초과 시 자동 알림
4. **시나리오 시뮬레이션**: "만약 X가 발생하면?" 가상 시나리오

---

## 참고 자료

- Neo4j Cypher: https://neo4j.com/docs/cypher-manual/
- LangChain: https://python.langchain.com/
- Streamlit: https://docs.streamlit.io/

---

**문의**: 시스템 관련 질문은 GitHub Issues에 등록해주세요.
