# 🔍 GraphRAG 시스템 분석 리포트

**생성 시간**: 2026-01-19  
**테스트 대상**: Finance_GraphRAG 프로젝트

---

## 📊 핵심 발견

### ❌ **현재 문제: Neo4j 그래프 데이터를 사용하지 않고 Perplexity 웹 검색만 사용**

```
현재 상황:
- Neo4j에 573개 노드, 1457개 관계 저장됨 ✅
- 하지만 답변은 100% Perplexity Web Search 사용 ❌
- 그래프 데이터가 전혀 활용되지 않음 ❌
```

---

## 상세 분석

### 1. Neo4j 데이터베이스 상태

**✅ 데이터 존재 확인** (`test_neo4j_direct.py` 결과):
```
📊 전체 노드 수: 573
🔗 전체 관계 수: 1457

📋 Labels:
- Company: 89개
- Person: 30개
- FinancialMetric: 95개
- Risk: 29개
- Regulation: 35개
- Product: 101개
- Location: 36개
등 총 13개 타입
```

**샘플 데이터**:
- Companies: Nvidia, TSMC, AMD, Samsung 등
- Risks: Geopolitical Tensions, Supply Chain Disruption 등
- Relationships: SUPPLIES, COMPETES_WITH, IMPACTS 등

### 2. 실제 쿼리 테스트 결과

**테스트 쿼리**: "TSMC supply chain risks"

**결과**:
```json
{
  "answer_length": 3080,
  "sources_count": 4,
  "sources": [
    "Perplexity Web Search",  // ❌ 모두 웹 검색
    "Perplexity Web Search",
    "Perplexity Web Search",
    "Perplexity Web Search"
  ]
}
```

**❌ Neo4j 그래프 데이터가 전혀 사용되지 않음!**

### 3. 원인 분석

#### 📍 **위치**: `src/app.py` (Line 767-803, 688-738)

#### 🔄 **문제 흐름**:

```
1. 사용자 질문 입력
   ↓
2. GraphRAG Engine 실행 시도
   ↓
3. Neo4j에서 검색 → 결과 없음 또는 신뢰도 낮음
   ↓
4. ❌ 자동으로 Perplexity로 폴백
   ↓
5. Perplexity 답변 반환
```

#### 💻 **코드 분석**:

```python
# src/app.py Line 767-768
# 출처가 없으면 Perplexity로 폴백
print(f"📚 No sources found in database, falling back to Perplexity search")
```

```python
# src/app.py Line 691-696
# 신뢰도가 낮으면 Perplexity로 폴백
if not override_applied and (validation_result["confidence_score"] < 0.7 or ...):
    print(f"[WARNING] Low confidence or invalid response, falling back to Perplexity search")
```

#### 🎯 **핵심 문제**:

1. **Neo4j Retriever가 제대로 작동하지 않음**
   - 573개 노드가 있는데도 검색 결과 없음
   - `Neo4jRetriever.retrieve()` 함수에 문제 가능성

2. **너무 공격적인 Perplexity 폴백**
   - 신뢰도 < 0.7이면 즉시 폴백
   - 출처가 없으면 즉시 폴백
   - 그래프 데이터를 활용할 기회가 없음

3. **GraphRAG vs Perplexity 우선순위 문제**
   - 설계는 "GraphRAG 우선, Perplexity 보조"
   - 실제는 "Perplexity 주력, GraphRAG 비활성화"

---

## 🔧 해결 방법

### 방법 1: Neo4j Retriever 수정 (권장)

**문제**: `Neo4jRetriever`가 데이터를 찾지 못함

**해결**:
1. `src/engine/neo4j_retriever.py` 검색 로직 개선
2. 임베딩 기반 검색 추가
3. 키워드 매칭 개선

```python
# 예시: 개선된 검색
async def retrieve(self, query: str, limit: int = 10):
    # 1. 키워드 추출
    keywords = self._extract_keywords(query)
    
    # 2. 다중 전략 검색
    results = []
    results.extend(await self._search_by_keywords(keywords))
    results.extend(await self._search_by_embeddings(query))
    results.extend(await self._search_by_relationships(keywords))
    
    # 3. 랭킹 및 필터링
    return self._rank_and_filter(results, limit)
```

### 방법 2: Perplexity 폴백 조건 강화

**문제**: 너무 쉽게 Perplexity로 폴백

**해결**:
```python
# src/app.py 수정
# 신뢰도 임계값 낮추기 (0.7 → 0.3)
if validation_result["confidence_score"] < 0.3:  # 더 관대하게
    # Perplexity 폴백
```

**또는**:
```python
# 출처가 없어도 그래프 데이터 활용 시도
if not sources_list:
    # 1차: Neo4j 직접 쿼리 시도
    graph_results = await self._query_neo4j_directly(question)
    
    if graph_results:
        # 그래프 기반 답변 생성
        response = self._generate_from_graph(graph_results)
    else:
        # 2차: Perplexity 폴백
        response = self._perplexity_fallback(question)
```

### 방법 3: 하이브리드 접근 활성화

**목표**: GraphRAG + Perplexity 결합

**구현**:
```python
# 1. GraphRAG에서 내부 데이터 수집
graph_results = await self._retrieve_from_neo4j(question)

# 2. Perplexity에서 최신 뉴스 수집
web_results = await self._retrieve_from_perplexity(question)

# 3. 결합하여 답변 생성
combined_sources = graph_results + web_results
response = self._generate_hybrid_answer(question, combined_sources)
```

---

## 🧪 테스트 시나리오

### 시나리오 1: 그래프 데이터만 사용

**질문**: "Neo4j에 저장된 회사들은?"

**기대 결과**:
```
답변: "데이터베이스에는 Nvidia, TSMC, AMD, Samsung 등 89개 회사가 저장되어 있습니다."
출처: Neo4j Graph Database
```

**현재 결과**:
```
답변: "저는 Neo4j 데이터베이스에 접근할 수 없습니다..." (Perplexity 답변)
출처: Perplexity Web Search ❌
```

### 시나리오 2: 그래프 + 웹 검색 결합

**질문**: "TSMC의 최근 뉴스와 공급망 리스크는?"

**기대 결과**:
```
답변:
[Neo4j 데이터]
- TSMC는 Nvidia에 GPU를 공급합니다 [1]
- 주요 리스크: Geopolitical Tensions, Supply Chain Disruption [2]

[최신 뉴스]
- 2026년 1월, TSMC 2nm 공정 양산 시작 [3]
- 미국 애리조나 공장 가동 개시 [4]

출처:
[1] Neo4j - Company Relationships
[2] Neo4j - Risk Factors
[3] Perplexity - Reuters
[4] Perplexity - Bloomberg
```

**현재 결과**:
```
답변: [Perplexity 뉴스만 표시]
출처: 전부 Perplexity Web Search ❌
```

---

## 📈 개선 로드맵

### Phase 1: Neo4j Retriever 수정 (우선)
- [ ] `Neo4jRetriever.retrieve()` 검색 로직 개선
- [ ] 키워드 매칭 강화
- [ ] 관계 탐색 추가 (2-hop, 3-hop)
- [ ] 테스트: "TSMC"로 검색하면 관련 노드 반환

### Phase 2: Perplexity 폴백 조정
- [ ] 신뢰도 임계값 낮추기 (0.7 → 0.3)
- [ ] 출처 없음 시 그래프 직접 쿼리 시도
- [ ] Perplexity는 최후의 수단으로만 사용

### Phase 3: 하이브리드 모드 구현
- [ ] GraphRAG + Perplexity 병렬 실행
- [ ] 출처별로 구분하여 표시
- [ ] UI에서 "그래프 데이터" vs "웹 검색" 토글

### Phase 4: UI 개선
- [ ] Visualization 탭에서 "이 쿼리에 사용된 노드" 하이라이트
- [ ] 그래프 기반 답변 강조
- [ ] 출처 필터링 (Neo4j only / Web only / All)

---

## 💡 결론

### 현재 상태
- ❌ **Neo4j 그래프 데이터 활용: 0%**
- ✅ **Perplexity 웹 검색 활용: 100%**
- 📊 **데이터**: 573 노드, 1457 관계 (미활용)

### Perplexity vs 현재 시스템

| 기능 | Perplexity | 현재 시스템 |
|------|-----------|------------|
| 웹 검색 | ✅ | ✅ (Perplexity API 사용) |
| 그래프 기반 검색 | ❌ | ❌ (구현됐지만 작동 안 함) |
| 최신 뉴스 | ✅ | ✅ |
| 내부 문서 검색 | ❌ | ❌ (Neo4j 있지만 미활용) |

**결론**: **현재는 Perplexity와 동일하게 작동하고 있습니다.**

### 개선 후 기대 효과

**GraphRAG 제대로 작동 시**:
```
질문: "TSMC supply chain risks"

답변:
## 내부 데이터 분석 (Neo4j)
TSMC는 다음 회사들과 공급망 관계를 맺고 있습니다:
- Nvidia (고객) - H100 GPU 제조
- ASML (공급사) - EUV 장비 제공
- AMD (고객) - 서버 CPU 제조

주요 리스크:
1. Geopolitical Tensions (Impact: High)
   - Taiwan Strait 긴장
2. Supply Chain Disruption (Impact: High)
   - 장비 공급 의존도

## 최신 뉴스 (Perplexity)
- 2026년 1월 19일: TSMC 2nm 공정 양산...
- 미국 정부, CHIPS Act 보조금...

출처:
[1-4] Neo4j - 내부 그래프 데이터
[5-8] Perplexity - 실시간 웹 검색
```

---

## 🚀 즉시 실행 가능한 해결책

### Quick Fix (5분)

**Perplexity 폴백 비활성화** (테스트용):

```bash
# src/app.py 수정
# Line 767-803, Line 688-738을 주석 처리

# 테스트 쿼리 실행
python test_query_with_graph.py
```

이렇게 하면:
- ✅ Perplexity 폴백 없음
- ✅ Neo4j Retriever 문제가 명확히 보임
- ✅ 다음 단계 디버깅 가능

### 근본 해결 (30분)

1. **Neo4j Retriever 수정**
2. **Perplexity 폴백 조건 조정**
3. **테스트 및 검증**

---

## 📞 추가 질문

1. **Perplexity 폴백을 완전히 비활성화하고 싶으신가요?**
   - → Neo4j 그래프만 사용

2. **하이브리드 모드를 원하시나요?**
   - → Neo4j (내부 데이터) + Perplexity (최신 뉴스)

3. **UI에서 선택 가능하게 하시겠습니까?**
   - → 체크박스: "웹 검색 사용" ON/OFF

어떤 방식을 원하시는지 알려주시면 바로 구현하겠습니다!
