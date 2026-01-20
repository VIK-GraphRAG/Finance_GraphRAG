"""
유틸리티 함수 모음
공통으로 사용되는 함수들을 모아놓은 파일이에요!
"""

import os
import re
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from ollama import AsyncClient

# config에서 설정 가져오기
from config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    API_MODELS,
    LOCAL_MODELS,
)


# --- [1] OpenAI API 함수들 ---

async def openai_model_if(
    prompt: str,
    system_prompt: Optional[str] = None,
    history_messages: List[Dict[str, str]] = [],
    **kwargs
) -> str:
    """
    OpenAI API를 사용해서 LLM에 질문하는 함수예요!
    
    Args:
        prompt: 질문 내용
        system_prompt: 시스템 메시지 (선택사항)
        history_messages: 이전 대화 내용
        **kwargs: 추가 인자
        
    Returns:
        LLM 응답 텍스트
    """
    
    client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})
    
    response = await client.chat.completions.create(
        model=API_MODELS["llm"],
        messages=messages,
        temperature=0.0,  # 0.1 -> 0.0 (더 빠른 응답)
        max_tokens=2000,  # 500 -> 2000 (JSON 파싱 에러 방지)
    )
    
    result = response.choices[0].message.content
    
    
    return result


async def openai_embedding_if(texts: List[str]) -> List[List[float]]:
    """
    OpenAI API를 사용해서 텍스트를 벡터로 변환하는 함수예요!
    
    Args:
        texts: 변환할 텍스트 리스트
        
    Returns:
        벡터 리스트 (각 텍스트마다 하나의 벡터)
    """
    client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    
    response = await client.embeddings.create(
        model=API_MODELS["embedding"],
        input=texts
    )
    
    return [item.embedding for item in response.data]

# nano-graphrag가 요구하는 embedding_dim 속성 추가
openai_embedding_if.embedding_dim = 1536


# --- [2] Ollama 함수들 ---

async def ollama_model_if(
    prompt: str,
    system_prompt: Optional[str] = None,
    history_messages: List[Dict[str, str]] = [],
    **kwargs
) -> str:
    """
    Ollama를 사용해서 LLM에 질문하는 함수예요!
    
    Args:
        prompt: 질문 내용
        system_prompt: 시스템 메시지 (선택사항)
        history_messages: 이전 대화 내용
        **kwargs: 추가 인자
        
    Returns:
        LLM 응답 텍스트
    """
    
    client = AsyncClient()
    
    # Detect if this is a JSON-expecting call (GraphRAG internal operations)
    is_json_request = (
        "json" in prompt.lower() or 
        "```json" in prompt.lower() or
        (system_prompt and "json" in system_prompt.lower())
    )
    
    messages = []
    if system_prompt:
        # Enhance system prompt for JSON requests
        if is_json_request:
            enhanced_system = system_prompt + "\n\nIMPORTANT: You MUST respond with valid JSON only. Do not include any explanatory text, markdown formatting, or conversational responses. Output only the raw JSON object."
            messages.append({"role": "system", "content": enhanced_system})
        else:
            messages.append({"role": "system", "content": system_prompt})
    elif is_json_request:
        # Add JSON enforcement if no system prompt exists
        messages.append({"role": "system", "content": "You are a precise JSON generator. Respond only with valid JSON. No explanations, no markdown, no conversational text."})
    
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})
    
    response = await client.chat(
        model=LOCAL_MODELS["llm"],
        messages=messages,
        format="json" if is_json_request else None  # Force JSON mode for Ollama
    )
    
    result = response['message']['content']
    
    
    # If JSON was expected, try to extract it from conversational responses
    if is_json_request and result:
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result, re.DOTALL)
        if json_match:
            result = json_match.group(1)
        # Try to find JSON object in the response
        elif not result.strip().startswith('{'):
            json_obj_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_obj_match:
                result = json_obj_match.group(0)
    
    
    return result


async def ollama_embedding_if(texts: List[str]) -> List[List[float]]:
    """
    Ollama를 사용해서 텍스트를 벡터로 변환하는 함수예요!
    
    Args:
        texts: 변환할 텍스트 리스트
        
    Returns:
        벡터 리스트 (각 텍스트마다 하나의 벡터)
    """
    client = AsyncClient()
    
    embeds = []
    for text in texts:
        response = await client.embeddings(
            model=LOCAL_MODELS["embedding"],
            prompt=text
        )
        embeds.append(response['embedding'])
    
    return embeds


# Ollama embedding 차원 설정
ollama_embedding_if.embedding_dim = LOCAL_MODELS["embedding_dim"]


# --- [3] 텍스트 전처리 함수들 ---

def preprocess_text(text: str) -> str:
    """
    텍스트를 전처리하는 함수예요!
    - 불용어 제거
    - 한 글자 단어 제거
    - 금융 숫자 보존
    
    Args:
        text: 원본 텍스트
        
    Returns:
        전처리된 텍스트
    """
    # 한국어 불용어 리스트
    stopwords = {
        "이", "가", "을", "를", "에", "의", "와", "과", "도", "로", "으로",
        "은", "는", "에서", "에게", "께", "한테", "에게서", "한테서",
        "처럼", "같이", "만큼", "만", "부터", "까지", "조차", "마저",
        "밖에", "뿐", "따라", "따름", "마다", "대로", "커녕",
        "그", "그것", "저", "저것", "이것", "그런", "저런", "이런",
        "그래서", "그러나", "그런데", "그러므로", "그리고", "그리하여",
        "또", "또한", "또는", "또한", "또한", "또한",
        "하지만", "그러나", "그런데", "그렇지만", "그러면", "그래서",
        "그리고", "그리하여", "그러므로", "그런즉", "그런즉",
        "그러므로", "그러니까", "그러니", "그러면", "그래서",
    }
    
    # 영어 불용어 리스트
    english_stopwords = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
        "been", "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "should", "could", "may", "might", "must", "can", "this",
        "that", "these", "those", "it", "its", "itself", "they", "them",
        "their", "theirs", "themselves", "what", "which", "who", "whom",
        "whose", "where", "when", "why", "how", "all", "each", "every",
        "both", "few", "more", "most", "other", "some", "such", "no",
        "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    }
    
    # 모든 불용어 합치기
    all_stopwords = stopwords | english_stopwords
    
    # 텍스트를 단어로 분리
    words = text.split()
    
    # 불용어 제거 및 한 글자 단어 제거
    filtered_words = []
    for word in words:
        # 단어 정리 (구두점 제거)
        cleaned_word = re.sub(r'[^\w\s$%]', '', word)
        
        # 한 글자 단어 제거 (단, 숫자나 특수문자는 보존)
        if len(cleaned_word) <= 1 and not cleaned_word.isdigit():
            continue
        
        # 불용어 제거
        if cleaned_word.lower() in all_stopwords:
            continue
        
        # 금융 숫자 패턴 보존 ($57.0B, 23.5% 등)
        if re.match(r'^[\$€£¥]?\d+[.,]?\d*[BMKkmb%]?$', cleaned_word):
            filtered_words.append(word)
            continue
        
        # 나머지 단어 추가
        if cleaned_word:
            filtered_words.append(word)
    
    # 단어들을 다시 문장으로 합치기
    processed_text = " ".join(filtered_words)
    
    return processed_text


def chunk_text(text: str, max_tokens: int = 1200) -> List[str]:
    """
    텍스트를 토큰 단위로 청크로 나누는 함수예요!
    
    Args:
        text: 원본 텍스트
        max_tokens: 최대 토큰 수 (기본값: 1200)
        
    Returns:
        청크 리스트
    """
    chunks: List[str] = []
    
    # tiktoken 사용 가능 여부 확인
    try:
        import tiktoken
        encoding = tiktoken.encoding_for_model(API_MODELS["llm"])
        tokens = encoding.encode(text)
        
        for i in range(0, len(tokens), max_tokens):
            token_chunk = tokens[i : i + max_tokens]
            chunks.append(encoding.decode(token_chunk))
    except Exception:
        # tiktoken이 없으면 문자 기준으로 청크 분할 (대략 4글자 = 1토큰 가정)
        approx_chars = max_tokens * 4
        for i in range(0, len(text), approx_chars):
            chunks.append(text[i : i + approx_chars])
    
    return chunks


# --- [4] PDF 파싱 함수들 ---

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    PDF 파일에서 텍스트를 추출하는 함수예요!
    
    Args:
        pdf_path: PDF 파일 경로
        
    Returns:
        추출된 텍스트
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없어요: '{pdf_path}'")
    
    # PyMuPDF 사용 시도
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except ImportError:
        raise ImportError("PyMuPDF가 설치되지 않았어요! 'pip install pymupdf'로 설치해주세요.")


def split_into_sentences(text: str) -> List[str]:
    """
    텍스트를 문장 단위로 분리하는 함수
    
    Args:
        text: 분리할 텍스트
        
    Returns:
        문장 리스트
    """
    import re
    # 간단한 문장 분리 (마침표, 느낌표, 물음표 기준)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def extract_text_from_pdf_with_metadata(pdf_path: str) -> List[Dict[str, Any]]:
    """
    PDF 파일에서 텍스트와 메타데이터를 함께 추출하는 함수
    
    Args:
        pdf_path: PDF 파일 경로
        
    Returns:
        메타데이터가 포함된 청크 리스트
        [
            {
                "text": "...",
                "page_number": 1,
                "source_file": "report.pdf",
                "sentence_id": "p1_s1",
                "original_sentence": "..."
            },
            ...
        ]
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없어요: '{pdf_path}'")
    
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        chunks_with_metadata = []
        source_file = os.path.basename(pdf_path)
        
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text()
            
            if not page_text.strip():
                continue
            
            # 문장 단위로 분리
            sentences = split_into_sentences(page_text)
            
            for sent_id, sentence in enumerate(sentences):
                if len(sentence.strip()) < 10:  # 너무 짧은 문장 제외
                    continue
                    
                chunks_with_metadata.append({
                    "text": sentence,
                    "page_number": page_num,
                    "source_file": source_file,
                    "sentence_id": f"p{page_num}_s{sent_id}",
                    "original_sentence": sentence
                })
        
        doc.close()
        return chunks_with_metadata
        
    except ImportError:
        raise ImportError("PyMuPDF가 설치되지 않았어요! 'pip install pymupdf'로 설치해주세요.")


# --- [5] 금융 엔티티 프롬프트 ---

def get_financial_entity_prompt() -> str:
    """
    금융 엔티티 추출을 위한 프롬프트를 반환하는 함수예요!
    
    Returns:
        프롬프트 텍스트
    """
    return """You are a financial analyst extracting entities from financial documents.

Focus on extracting the following financial entities with HIGH PRIORITY:
- REVENUE (매출, Revenue, Sales, Total Revenue)
- OPERATING_INCOME (영업이익, Operating Income, Operating Profit)
- NET_INCOME (순이익, Net Income, Profit)
- GROWTH_RATE (성장률, Growth Rate, YoY Growth, QoQ Growth)
- MARGIN (마진, Gross Margin, Operating Margin, Net Margin)
- ASSET (자산, Total Assets, Current Assets)
- LIABILITY (부채, Total Liabilities, Current Liabilities)
- EQUITY (자본, Shareholders' Equity, Equity)
- CASH_FLOW (현금흐름, Operating Cash Flow, Free Cash Flow)
- EPS (주당순이익, Earnings Per Share, EPS)
- PE_RATIO (주가수익비율, P/E Ratio, Price-to-Earnings)
- MARKET_CAP (시가총액, Market Capitalization, Market Cap)

Also extract standard entities:
- ORGANIZATION (회사명, 기관명)
- PERSON (인물명, 임원명)
- GEO (지역, 국가, 도시)
- DATE (날짜, 분기, 연도)
- TECHNOLOGY (기술명, 제품명)

For each entity, extract:
1. The exact name/value
2. The entity type
3. The context (where it appears in the document)
4. Relationships to other entities (e.g., "NVIDIA's revenue is $57.0B")

Be precise with financial numbers. Extract exact values with units (e.g., "$57.0 billion", "23.5%", "Q3 2026").
"""


def get_strict_grounding_prompt(question: str, sources: List[dict]) -> str:
    """
    외부 지식 사용을 금지하고 문서 기반 답변만 강제하는 프롬프트
    
    Args:
        question: 사용자 질문
        sources: 출처 리스트 [{"id": 1, "file": "...", "page_number": 1, "excerpt": "..."}, ...]
    
    Returns:
        Strict grounding system prompt
    """
    if not sources:
        return f"""You are a STRICT document-based analyst.

CRITICAL RULE: The provided documents contain NO information relevant to this question.

QUESTION: {question}

REQUIRED RESPONSE: "해당 문서들에서는 관련 정보를 찾을 수 없습니다."

You MUST respond with exactly this message in Korean."""
    
    sources_text = "\n\n".join([
        f"[{s['id']}] File: {s['file']}, Page: {s.get('page_number', 'N/A')}\n"
        f"Content: {s['excerpt']}\n"
        f"Original: {s.get('original_sentence', s['excerpt'])}"
        for s in sources
    ])
    
    max_citation_num = len(sources)
    
    return f"""You are a professional financial analyst. Create a structured report using **Professional Markdown** format.

📋 CRITICAL RULES:
1. ONLY use information from the provided sources below
2. DO NOT use external knowledge or background information
3. If information is NOT in sources, respond: "해당 문서들에서는 관련 정보를 찾을 수 없습니다"

📚 AVAILABLE SOURCES:
{sources_text}

❓ QUESTION: {question}

📝 REQUIRED FORMAT (Professional Markdown):

## 핵심 인사이트
[2-3 문장으로 핵심 답변 요약, 모든 수치는 **굵게**, 용어는 `inline code`로]

## 인과관계 다이어그램
```
A → B → C → 결과
```
[화살표로 관계를 명확히 표현]

## 상세 분석

### 1️⃣ [첫 번째 주요 포인트]
- **수치 데이터**는 반드시 **굵게** 표시
- `핵심 용어`는 inline code로 감싸기
- 구체적인 사실과 데이터 중심

### 2️⃣ [두 번째 주요 포인트]
- 관련 세부사항과 맥락
- 비교 데이터가 있으면 테이블 사용

### 3️⃣ [세 번째 주요 포인트] (필요시)
- 추가 분석 내용

## 데이터 요약 
| 항목 | 수치 |
|------|------|
| 예시 | **$100M** |

## 에이전트의 한 줄 평
**[분석 결과를 한 문장으로 명확하게 요약]**

FORMATTING RULES:
✅ 모든 수치는 **굵게** (예: **$57B**, **22%**)
✅ 핵심 용어는 `inline code` (예: `TSMC`, `HBM`, `AI GPU`)
✅ 인과관계는 A → B → C 다이어그램으로
✅ 테이블은 Markdown Table 형식
✅ 마지막에 **에이전트의 한 줄 평** 필수
❌ 인용 번호 [1], [2] 사용 금지
❌ HTML 태그 사용 금지
❌ 별도 출처 섹션 작성 금지

Begin your Professional Markdown response:"""


def get_executive_report_prompt(question: str, sources: List[dict]) -> str:
    """
    임원급 보고서 형식의 System Prompt 생성
    Perplexity 스타일로 Citation이 포함된 전문적인 보고서를 작성하도록 유도
    
    Args:
        question: 사용자 질문
        sources: 출처 리스트 [{"id": 1, "file": "...", "excerpt": "..."}, ...]
    
    Returns:
        System prompt string
    """
    # 출처 리스트를 포맷팅
    sources_text = "\n".join([
        f"[{s['id']}] {s['file']} (Chunk {s.get('chunk_id', 'N/A')}): \"{s['excerpt'][:150]}...\""
        for s in sources
    ])
    
    max_citation_num = len(sources) if sources else 0
    
    prompt = f"""You are an elite executive analyst preparing a professional report for C-level executives.

QUESTION: {question}

AVAILABLE SOURCES (Citation numbers: [1] to [{max_citation_num}]):
{sources_text if sources else "[No specific sources available - use general knowledge]"}

REPORT STRUCTURE (MANDATORY):

## EXECUTIVE SUMMARY
Provide a concise 2-3 sentence overview of the key findings. This should be immediately actionable for decision-makers.

## KEY FINDINGS
Present 3-5 bullet points highlighting the most critical insights. **EVERY finding MUST include citation [1], [2], etc.**
- Finding 1 with supporting data [1]
- Finding 2 with evidence [2]
- Continue with [3], [4] as needed

## DETAILED ANALYSIS  
Provide in-depth analysis with clear sections:
- Break down complex information into digestible parts
- **Support EVERY factual claim with citations [1], [2], [3]**
- Example: "TSMC announced 690억 달러 revenue [1]."
- Use quantitative data where available
- Explain implications and context

## CONCLUSION & RECOMMENDATIONS
Summarize the analysis and provide actionable recommendations:
- Key takeaways
- Strategic implications  
- Recommended next steps

CITATION RULES (CRITICAL):
1. After EVERY factual statement, immediately add [1], [2], [3] etc. corresponding to the source
2. Available citation range: [1] through [{max_citation_num}] ONLY
3. Citation placement: "Statement here [1]." NOT "Statement here. [1]"
4. Multiple citations allowed: [1][2] or [1, 2]
5. ONLY use source numbers provided above - do NOT invent citations
6. If no sources available, do NOT use citations - state it's based on general knowledge
7. **Be generous with citations - better to over-cite than under-cite**
8. Cite specific data points, quotes, and factual claims

FORMATTING:
- Use clear markdown headers (##)
- Use bold (**text**) for emphasis
- Use bullet points for lists
- Keep paragraphs concise (3-4 sentences max)
- Professional, data-driven tone
- PLAIN TEXT ONLY - absolutely NO HTML tags or markup

IMPORTANT: 
- Do NOT add a separate References section at the end (it will be added automatically)
- Do NOT generate HTML code (<a>, <div>, etc.) - text only
- Focus on insights, not just data regurgitation
- Be precise with numbers and dates
- If data is insufficient, acknowledge limitations
- Every paragraph should have at least one citation if it contains factual information

Begin your report now (PLAIN TEXT, NO HTML, CITE FREQUENTLY):"""
    
    return prompt


def get_web_search_report_prompt(question: str, search_results: List[dict]) -> str:
    """
    웹 검색 결과를 바탕으로 보고서를 작성하는 System Prompt
    
    Args:
        question: 사용자 질문
        search_results: 웹 검색 결과 [{"title": "...", "snippet": "...", "url": "..."}, ...]
    
    Returns:
        System prompt string
    """
    # 검색 결과를 소스 형식으로 변환
    sources_text = "\n".join([
        f"[{idx}] {result['title']}\n   Source: {result['url']}\n   Content: \"{result['snippet'][:200]}...\""
        for idx, result in enumerate(search_results, 1)
    ])
    
    prompt = f"""You are an elite research analyst synthesizing web search results into an executive report.

QUESTION: {question}

WEB SEARCH RESULTS:
{sources_text}

REPORT STRUCTURE (MANDATORY):

## EXECUTIVE SUMMARY
Synthesize the web findings into 2-3 actionable sentences.

## KEY FINDINGS
Present 3-5 bullet points from the search results. Cite sources [1], [2], etc.

## DETAILED ANALYSIS
Synthesize information from multiple sources:
- Compare and contrast different perspectives
- Identify trends and patterns
- Cite sources for every claim [1][2][3]

## CONCLUSION & RECOMMENDATIONS
Based on the web research, provide strategic insights.

CITATION RULES:
- Cite web sources as [1], [2], [3] matching the search results above
- Every factual claim needs a citation
- Synthesize multiple sources when appropriate [1][2]

Begin your report now:"""
    
    return prompt

