# 프로젝트명: Tech-Analyst GraphRAG (Nvidia Special Edition)

## 1. 개요
- 기술 기업(특히 반도체 섹터) 전문 금융 분석가 페르소나를 가진 AI 에이전트.
- 실시간 웹 검색(Perplexity)과 관계형 지식 그래프(Neo4j)를 결합하여 고품질 리포트 제공.

## 2. 핵심 기술 스택
- **Search API:** Perplexity API (최신 뉴스 및 거시적 리스크 확보용)
- **Database:** Neo4j (기술 기업 공급망 및 산업 공통 지식 저장)
- **LLM:** GPT-4o-mini (데이터 추출 및 리포트 작성용)
- **UI:** Streamlit (리포트 출력 및 그래프 시각화)

## 3. 데이터 아키텍처 (Data Flow)
1. **Baseline DB:** `data/baseline/` 폴더의 기술 산업 공통 리포트를 분석하여 Neo4j에 기본 공급망/리스크 그래프 형성.
2. **Dynamic Ingestion:** 사용자가 개별 기업 PDF 업로드 시, 기존 Baseline 그래프와 엔티티(Ticker 기준)를 매핑하여 결합.
3. **Hybrid Retrieval:** - 질문 수신 -> Perplexity 검색 (실시간 정보)
   - Neo4j 탐색 (2-hop 이상의 멀티홉 인과관계)
   - 두 정보를 결합하여 LLM이 추론.

## 4. 답변 스타일 가이드 (Output Format)
- 단순 단답형 금지. 아래 형식을 갖춘 리포트 출력:
  - **[Executive Summary]** 핵심 내용 요약
  - **[Market Context]** 실시간 검색 기반 시장 상황
  - **[Supply Chain Analysis]** 그래프 기반 멀티홉 인과관계 추론
  - **[Risk & Outlook]** 잠재적 리스크 및 향후 전망

  ## 5. 보안 및 LLM 역할 분담 (Security & Hybrid LLM)
- **Private Data Handling (Local - Qwen 2.5 Coder instruct):**
  - 모든 로컬 PDF 파싱 및 지식 추출은 Qwen 2.5 Coder가 담당.
  - 외부 API로 원본 텍스트를 절대 전송하지 않음.
  - Neo4j에 데이터를 저장할 때 민감 정보 태깅 수행.
- **Public Intelligence (Cloud - GPT-4o-mini & Perplexity):**
  - 실시간 웹 검색 및 공개된 시장 데이터 분석 담당.
  - 로컬에서 가공된 '비식별 지식 경로'를 바탕으로 리포트 초안 작성.
- **Data Firewall:** - 외부로 나가는 모든 프롬프트는 로컬 LLM에 의해 1차 검열 및 익명화 과정을 거침.