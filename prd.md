3. 바이브 코딩을 위한 PRD (Product Requirements Document)
이 내용을 커서(Cursor) 에이전트에게 복사해서 주시면 개발을 시작할 수 있습니다.

[PRD] Tech-Analyst GraphRAG Agent (NVIDIA Special Edition)
1. 제품 목표

기술 기업 전문 분석가 페르소나를 가진 에이전트 구축.

사용자 업로드 PDF와 기존 산업 지식 그래프를 결합한 고차원 멀티홉 추론.

실시간 웹 검색(Perplexity)을 통한 최신성 확보 및 리포트 형식의 고품질 답변.

2. 핵심 기능 (Functional Requirements)

Hybrid Search Engine: 질문 수신 시 Perplexity API를 호출하여 실시간 뉴스 확보 + Neo4j에서 관련 지식 그래프 경로(Path) 추출.

Multi-hop Reasoning: 미리 구축된 '기술 산업 베이스라인 그래프'와 사용자가 새로 업로드한 '특정 기업 PDF'의 엔티티(Entity)를 연결하여 병합된 인사이트 도출.

Professional Reporting: 모든 답변은 [Executive Summary], [Key Findings], [Risk Analysis], [Strategic Recommendation]의 형식을 갖춤.

Context Management: 사용자가 질문을 이어갈 때 이전 대화 맥락과 그래프 탐색 결과를 유지.

3. 기술 스택 (Technical Stack)

LLM: GPT-4o 또는 Claude 3.5 Sonnet (추론 및 구조화용)

Search API: Perplexity API (온라인 컨텍스트 확보용)

Database: Neo4j (GraphRAG 구현 및 멀티홉 추론용)

Orchestration: LangChain 또는 LlamaIndex (비동기 병렬 처리)