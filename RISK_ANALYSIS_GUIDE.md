# 포괄적 리스크 분석 가이드

## 🎯 개요

이 시스템은 "Nvidia's risk"와 같은 포괄적인 질문에 대해 지식 그래프를 활용한 심층 분석을 제공합니다.

## 🏗️ 지식 그래프 구조

### 노드 타입
- **Company**: 기업 (Nvidia, TSMC, AMD, Intel 등)
- **Country**: 국가 (미국, 중국, 대만 등)
- **Industry**: 산업 (반도체, AI 등)
- **MacroIndicator**: 거시경제 지표 (미중 무역분쟁, 대만 해협 긴장 등)
- **FinancialMetric**: 재무 지표 (매출, 시장 점유율 등)

### 관계 타입
- **DEPENDS_ON**: 공급망 의존도 (예: Nvidia → TSMC)
- **COMPETES_WITH**: 시장 경쟁 (예: Nvidia ↔ AMD)
- **IMPACTS**: 거시경제 영향 (예: 대만 긴장 → 반도체 산업)
- **OPERATES_IN**: 산업 분류 (예: Nvidia → 반도체)
- **LOCATED_IN**: 지리적 위치 (예: TSMC → 대만)
- **AFFECTS**: 지정학적 영향 (예: 대만 긴장 → 대만)

## 🚀 시작하기

### 1. Seed Data 생성

```bash
cd /Users/gyuteoi/new/Finance_GraphRAG
python3 seed_financial_data.py
```

이 명령은 다음을 생성합니다:
- 5개 국가
- 5개 산업
- 3개 거시경제 지표
- 4개 주요 기업
- 24개 관계

### 2. 시스템 실행

```bash
./start.sh
```

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:8501

## 📊 예시 쿼리

### 1. 포괄적 리스크 분석
```
질문: "Nvidia's risk"

답변 경로:
├─ 지정학적 리스크
│  ├─ Nvidia → TSMC → Taiwan → Taiwan Strait Tension
│  └─ Nvidia → Semiconductor → US-China Trade War
├─ 공급망 리스크
│  └─ Nvidia → TSMC (high criticality)
└─ 경쟁 리스크
   ├─ Nvidia ↔ AMD (GPU segment)
   └─ Nvidia ↔ Intel (AI segment)
```

### 2. 재무 성과 조회
```
질문: "Nvidia revenue"

답변: Nvidia의 FY2024 매출은 $60.9B입니다.
```

### 3. 시장 포지션 분석
```
질문: "Nvidia market position"

답변 경로:
├─ GPU Market Share: 80%
├─ Competitors: AMD (19%), Intel
└─ Industry: Semiconductor (Technology sector)
```

## 🧠 Query Analyzer 작동 방식

### 1. 질문 분석 (LLM)
```python
query_analyzer = QueryAnalyzer()
analysis = await query_analyzer.analyze_query("Nvidia's risk")

# 출력:
{
  "entities": ["Nvidia"],
  "intent": "risk_analysis",
  "risk_categories": ["geopolitical", "supply_chain", "competition"],
  "exploration_strategy": {
    "max_hops": 2,
    "priority_relationships": ["IMPACTS", "DEPENDS_ON", "COMPETES_WITH"],
    "focus_nodes": ["Country", "MacroIndicator", "Company"]
  }
}
```

### 2. Cypher 쿼리 생성
```cypher
MATCH path = (start {name: ~'(?i).*Nvidia.*'})-[*1..2]->(end)
WHERE ALL(r IN relationships(path) 
          WHERE type(r) IN ['IMPACTS', 'DEPENDS_ON', 'COMPETES_WITH'])
RETURN path
LIMIT 100
```

### 3. 리스크 분류
```python
classified_risks = {
  "geopolitical": [
    "Nvidia → TSMC → Taiwan → Taiwan Strait Tension",
    "Nvidia → Semiconductor → US-China Trade War"
  ],
  "supply_chain": [
    "Nvidia → TSMC (high criticality dependency)"
  ],
  "competition": [
    "Nvidia ↔ AMD (GPU market)",
    "Nvidia ↔ Intel (AI accelerators)"
  ]
}
```

### 4. 컨텍스트 재구성
```
# Risk Analysis Context for: Nvidia

## Geopolitical Risks
1. Nvidia → TSMC → Taiwan → Taiwan Strait Tension
2. Nvidia → Semiconductor → US-China Trade War

## Supply Chain Risks
1. Nvidia → TSMC (high criticality dependency)

## Competition Risks
1. Nvidia → AMD (GPU segment)
2. Nvidia → Intel (AI segment)
```

## 🔧 확장 방법

### 새로운 기업 추가
```python
# seed_financial_data.py에 추가
queries.append(
    "MERGE (c:Company {name: 'Apple'}) SET c.market_cap = 3000, c.revenue = 394.3"
)
queries.append(
    "MATCH (c:Company {name: 'Apple'}), (i:Industry {name: 'Consumer Electronics'}) "
    "MERGE (c)-[:OPERATES_IN]->(i)"
)
```

### 새로운 리스크 추가
```python
queries.append(
    "MERGE (m:MacroIndicator {name: 'Climate Change'}) "
    "SET m.type = 'environmental', m.impact_level = 'high'"
)
queries.append(
    "MATCH (m:MacroIndicator {name: 'Climate Change'}), (i:Industry {name: 'Semiconductor'}) "
    "MERGE (m)-[:IMPACTS {impact: 'negative', severity: 0.6}]->(i)"
)
```

## 📈 성능 최적화

### Neo4j 인덱스
```cypher
CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.name);
CREATE INDEX country_name IF NOT EXISTS FOR (c:Country) ON (c.name);
CREATE INDEX industry_name IF NOT EXISTS FOR (i:Industry) ON (i.name);
```

### 쿼리 최적화
- 2-hop 탐색으로 제한 (성능 vs 깊이 균형)
- 관계 타입 필터링으로 불필요한 경로 제외
- LIMIT로 결과 수 제한

## 🎓 베스트 프랙티스

1. **구체적 질문**: "Nvidia risk"보다 "Nvidia geopolitical risk"가 더 정확
2. **지식 그래프 업데이트**: 정기적으로 seed data 갱신
3. **관계 가중치**: criticality, severity 등으로 중요도 표현
4. **시간성 데이터**: updated_at 필드로 데이터 신선도 관리

## 🐛 문제 해결

### "No data found" 에러
```bash
# Neo4j 연결 확인
curl http://localhost:7474

# Seed data 재생성
python3 seed_financial_data.py
```

### 느린 쿼리
```cypher
# 현재 실행 중인 쿼리 확인
CALL dbms.listQueries();

# 인덱스 확인
CALL db.indexes();
```

## 📚 참고 자료

- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [Graph Data Science](https://neo4j.com/docs/graph-data-science/)
- [Knowledge Graph Best Practices](https://neo4j.com/graph-databases-book/)
