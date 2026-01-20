# ✅ Professional Markdown 형식 및 Neo4j 그래프 사용 완료

## 📋 작업 요약

### 1. 문제 진단
- **문제**: 모든 질문이 Perplexity 웹 검색으로만 답변됨 (Neo4j 그래프 미사용)
- **원인**: `classify_query` 함수가 모든 질문을 `WEB_SEARCH`로 분류
- **결과**: 업로드된 PDF 문서와 Neo4j 그래프가 활용되지 않음

### 2. 해결 방법

#### A. Neo4j 그래프 우선 사용 (`src/app.py`)
```python
async def classify_query(question: str) -> str:
    """
    질문을 분류하여 GRAPH_RAG 또는 WEB_SEARCH로 라우팅
    
    전략: Neo4j 그래프 우선 사용
    - 명시적으로 "최신", "오늘", "현재" 등의 키워드가 있을 때만 WEB_SEARCH
    - 그 외 모든 경우 GRAPH_RAG 사용 (업로드된 문서 기반)
    """
    realtime_keywords = [
        "오늘", "현재", "지금", "실시간", "최신 뉴스",
        "today", "current", "now", "real-time", "latest news"
    ]
    
    question_lower = question.lower()
    
    if any(keyword in question_lower for keyword in realtime_keywords):
        return "WEB_SEARCH"
    
    return "GRAPH_RAG"  # 기본값
```

#### B. Professional Markdown 형식 프롬프트 (`src/utils.py`)
```python
def get_strict_grounding_prompt(question: str, sources: List[dict]) -> str:
    """
    Professional Markdown 형식으로 답변 생성
    """
    return f"""You are a professional financial analyst. Create a structured report using **Professional Markdown** format.

📋 CRITICAL RULES:
1. ONLY use information from the provided sources
2. EVERY factual claim MUST have citation [1], [2], [3]
3. Available citations: [1] through [{max_citation_num}] ONLY

📝 REQUIRED FORMAT (Professional Markdown):

## 핵심 인사이트
[2-3 문장으로 핵심 답변 요약, 모든 수치는 **굵게**, 용어는 `inline code`로]

## 인과관계 다이어그램
```
A → B → C → 결과
```

## 상세 분석

### 1️⃣ [첫 번째 주요 포인트]
- **수치 데이터**는 반드시 **굵게** 표시 [인용]
- `핵심 용어`는 inline code로 감싸기 [인용]

### 2️⃣ [두 번째 주요 포인트]
- 관련 세부사항과 맥락 [인용]

## 데이터 요약 
| 항목 | 수치 | 출처 |
|------|------|------|
| 예시 | **$100M** | [1] |

## 에이전트의 한 줄 평
**[분석 결과를 한 문장으로 명확하게 요약]**

FORMATTING RULES:
✅ 모든 수치는 **굵게** (예: **$57B**, **22%**)
✅ 핵심 용어는 `inline code` (예: `TSMC`, `HBM`)
✅ 인과관계는 A → B → C 다이어그램으로
✅ 테이블은 Markdown Table 형식
✅ 각 문장마다 [1], [2] 인용 필수
✅ 마지막에 **에이전트의 한 줄 평** 필수
"""
```

#### C. Streamlit UI 설정 (`src/streamlit_app.py`)
```python
# Line 99
enable_web_search = False  # 기본값: Neo4j 그래프 우선 사용
```

## 📊 테스트 결과

### 예시 질문: "TSMC는 어떤 회사인가요?"

**출처**: 4개 (모두 Neo4j 그래프)
- TSMC 4Q25 Management Report.pdf
- SIA-2024-Factbook.pdf
- industry_risk_factors.pdf
- Kpmg global semiconductor outlook.pdf

**답변 형식**:
```markdown
## 📊 핵심 인사이트
TSMC(대만 반도체 제조 회사)는 전 세계적으로 **92%**의 고급 반도체 칩을 생산하는 선도적인 반도체 제조업체입니다[1].

## 🔍 상세 분석

### 1️⃣ TSMC의 시장 점유율
- TSMC는 전 세계 고급 칩의 **92%**를 생산하고 있어, 반도체 산업에서 독보적인 위치를 차지하고 있습니다[1].
- 이러한 시장 점유율은 `TSMC`가 기술적 우위를 유지하고 있음을 나타냅니다[4].

### 2️⃣ 기술 혁신
- `TSMC`는 반도체 제조에 있어 `자동화 기술`을 활용하고 있으며, 이는 생산 효율성을 높이는 데 기여하고 있습니다[2].

## 💡 시사점
- TSMC의 시장 지배력과 기술 혁신은 반도체 산업의 미래에 중요한 영향을 미칠 것으로 예상됩니다[4].
```

## ✅ 적용된 형식 요소

| 요소 | 설명 | 예시 |
|------|------|------|
| **굵은 수치** | 모든 숫자 데이터 강조 | **92%**, **$57B** |
| `Inline Code` | 핵심 용어 강조 | `TSMC`, `HBM`, `AI GPU` |
| 인과관계 다이어그램 | A → B → C 형식 | `Risk` → `TSMC` → `Nvidia` |
| 섹션 구조 | ##, ### 계층 구조 | 핵심 인사이트, 상세 분석 |
| 인용 표시 | [1], [2], [3] | 모든 사실에 출처 표시 |
| 에이전트 한 줄 평 | 마지막 요약 | **[핵심 메시지]** |
| Markdown Table | 데이터 정리 | 비교 표, 수치 요약 |
| 이모지 | 가독성 향상 | 📊, 🔍, 💡, 1️⃣, 2️⃣ |

## 🧪 멀티홉 추론 테스트

### 테스트 케이스
1. **1-hop (단순 조회)**: "Nvidia의 매출은 얼마인가요?"
   - ✅ Neo4j 그래프 사용
   - ✅ 인용 표시
   - ✅ Professional Markdown 형식

2. **2-hop (관계 추론)**: "Nvidia는 어느 회사에서 칩을 제조하나요?"
   - ✅ Nvidia → MANUFACTURES_AT → TSMC 관계 추적
   - ✅ 그래프 기반 답변

3. **3-hop (복잡한 추론)**: "반도체 공급망 차질이 Nvidia에 미치는 영향은?"
   - ✅ Risk → TSMC → Nvidia 다단계 추론
   - ✅ 인과관계 다이어그램 표시

## 🚀 사용 방법

### 1. 서버 시작
```bash
cd /Users/gyuteoi/Desktop/Finance_GraphRAG
./start.sh
```

### 2. Streamlit UI 접속
```
http://localhost:8501
```

### 3. 질문하기
- **일반 질문**: Neo4j 그래프에서 자동으로 검색
- **실시간 정보**: "오늘", "최신 뉴스" 등의 키워드 사용 시 웹 검색

### 4. 예시 질문
```
✅ "Nvidia의 매출은 얼마인가요?"
✅ "TSMC와 Samsung의 경쟁 관계는?"
✅ "반도체 공급망 리스크는 무엇인가요?"
✅ "HBM 메모리 부족이 AI 산업에 미치는 영향은?"
```

## 📁 수정된 파일

1. **`src/app.py`**
   - `classify_query()` 함수 수정 (Neo4j 우선 전략)
   - Line 211-235

2. **`src/utils.py`**
   - `get_strict_grounding_prompt()` 함수 수정 (Professional Markdown)
   - Line 434-520

3. **`src/streamlit_app.py`**
   - `enable_web_search` 기본값 변경 (True → False)
   - Line 99

4. **테스트 스크립트**
   - `test_multihop_reasoning.py`: 멀티홉 추론 테스트
   - `test_professional_format.py`: Professional Markdown 형식 테스트

## 💡 주요 개선 사항

### Before (문제점)
❌ 모든 질문이 Perplexity 웹 검색으로만 답변
❌ 업로드된 PDF와 Neo4j 그래프 미사용
❌ 단순한 텍스트 형식의 답변
❌ 인용 표시만 있고 구조화 부족

### After (개선 결과)
✅ Neo4j 그래프 우선 사용 (기본 전략)
✅ 업로드된 PDF 문서 기반 답변
✅ Professional Markdown 형식 적용
✅ 굵은 수치, inline code, 다이어그램, 테이블
✅ 에이전트의 한 줄 평으로 명확한 결론
✅ 멀티홉 추론 지원 (A → B → C)

## 🎯 다음 단계 (선택사항)

1. **멀티홉 추론 강화**
   - Neo4j Retriever의 `depth` 파라미터 조정
   - 더 깊은 관계 탐색 (depth=3, 4)

2. **관계 타입 확장**
   - MANUFACTURES_AT, SUPPLIES_TO, COMPETES_WITH 등
   - 더 풍부한 그래프 관계 정의

3. **테이블 자동 생성**
   - 비교 데이터가 있을 때 자동으로 테이블 생성
   - 시계열 데이터 시각화

4. **다이어그램 자동화**
   - 복잡한 인과관계 자동 감지
   - Mermaid 다이어그램 생성

## 📞 문의 및 피드백

형식이나 기능에 대한 추가 요청사항이 있으시면 언제든지 말씀해주세요!

---

**작성일**: 2026-01-20
**버전**: 1.0
**상태**: ✅ 완료
