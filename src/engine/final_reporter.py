"""
Final Reporter - Hybrid Report Generation
하이브리드 리포터: GPT-4o-mini를 사용한 최종 리포트 생성
"""

from typing import Dict, List, Optional
from openai import OpenAI

try:
    from ..config import OPENAI_API_KEY, OPENAI_BASE_URL
except ImportError:
    from config import OPENAI_API_KEY, OPENAI_BASE_URL


class FinalReporter:
    """
    하이브리드 리포터 - 최종 리포트 생성
    
    Features:
    - GPT-4o-mini 사용
    - 익명화된 지식 경로 + Perplexity 뉴스 결합
    - 금융 분석가 톤의 4단계 구조화된 리포트
    
    Input:
    - 익명화된 그래프 경로
    - Perplexity 뉴스 결과
    
    Output Format:
    - [Executive Summary] 핵심 내용 요약
    - [Market Context] 실시간 검색 기반 시장 상황
    - [Supply Chain Analysis] 그래프 기반 멀티홉 인과관계 추론
    - [Risk & Outlook] 잠재적 리스크 및 향후 전망
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2
    ):
        """
        Initialize FinalReporter
        
        Args:
            api_key: OpenAI API key
            model: Model name
            temperature: Sampling temperature
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model
        self.temperature = temperature
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=OPENAI_BASE_URL
        )
    
    def generate_report(
        self,
        query: str,
        graph_context: str,
        web_search_results: Optional[Dict] = None,
        additional_context: Optional[str] = None
    ) -> str:
        """
        Generate comprehensive financial analysis report
        
        Args:
            query: User query
            graph_context: Anonymized graph knowledge paths
            web_search_results: Perplexity search results
            additional_context: Additional context
            
        Returns:
            Formatted report in markdown
        """
        # Build system prompt
        system_prompt = self._get_system_prompt()
        
        # Build user prompt
        user_prompt = self._build_user_prompt(
            query=query,
            graph_context=graph_context,
            web_search_results=web_search_results,
            additional_context=additional_context
        )
        
        # Call GPT-4o-mini
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=2000
            )
            
            report = response.choices[0].message.content
            return report
            
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
            return self._generate_fallback_report(query, graph_context, web_search_results)
    
    def _get_system_prompt(self) -> str:
        """
        Get system prompt for financial analyst persona
        
        Returns:
            System prompt string
        """
        return """You are a senior financial analyst specializing in the semiconductor and technology sector.

Your task is to generate comprehensive, professional analysis reports following this exact structure:

## [Executive Summary]
- Provide a concise 3-5 sentence overview of the key findings
- Highlight the most critical insights
- Use clear, executive-level language

## [Market Context]
- Analyze current market conditions based on latest news and trends
- Discuss recent developments and announcements
- Provide real-time market intelligence
- **IMPORTANT: Cite sources using [1], [2], [3] format when referencing specific information**

## [Supply Chain Analysis]
- Examine supply chain relationships and dependencies
- Identify multi-hop causal relationships (e.g., A → B → C impact chains)
- Analyze upstream and downstream effects
- Discuss strategic partnerships and vulnerabilities
- **IMPORTANT: Cite sources using [1], [2], [3] format when referencing specific information**

## [Risk & Outlook]
- Identify key risks (geopolitical, technological, financial)
- Provide forward-looking outlook
- Discuss potential scenarios and their implications
- Offer strategic recommendations
- **IMPORTANT: Cite sources using [1], [2], [3] format when referencing specific information**

Guidelines:
- Use professional, analytical tone
- Be specific and data-driven when possible
- Avoid speculation without basis
- Clearly distinguish between facts and analysis
- Use markdown formatting for readability
- Keep each section focused and concise
- **CRITICAL: When referencing information from sources, ALWAYS use citation numbers [1], [2], etc.**
- **CRITICAL: Only cite sources that are actually provided in the context**
- **CRITICAL: Each factual claim should be supported by a citation number**"""
    
    def _build_user_prompt(
        self,
        query: str,
        graph_context: str,
        web_search_results: Optional[Dict],
        additional_context: Optional[str]
    ) -> str:
        """
        Build user prompt with all available context
        
        Args:
            query: User query
            graph_context: Graph knowledge
            web_search_results: Web search results
            additional_context: Additional context
            
        Returns:
            User prompt string
        """
        prompt_parts = [
            f"**User Question:** {query}\n",
            "---\n"
        ]
        
        source_counter = 0
        
        # Add graph context
        if graph_context:
            prompt_parts.append("**Knowledge Graph Context:**")
            prompt_parts.append(graph_context)
            prompt_parts.append("\n---\n")
        
        # Add web search results
        if web_search_results and not web_search_results.get("error"):
            prompt_parts.append("**Real-time Market Intelligence (Perplexity):**")
            
            answer = web_search_results.get("answer", "")
            if answer:
                prompt_parts.append(answer)
            
            citations = web_search_results.get("citations", [])
            if citations:
                prompt_parts.append("\n**Available Sources (use these numbers for citations):**")
                for i, url in enumerate(citations[:5], 1):
                    prompt_parts.append(f"[{i}] {url}")
                    source_counter = i
            
            prompt_parts.append("\n---\n")
        
        # Add additional context
        if additional_context:
            prompt_parts.append("**Additional Context:**")
            prompt_parts.append(additional_context)
            prompt_parts.append("\n---\n")
        
        prompt_parts.append("\n**Instructions:**")
        prompt_parts.append("Generate a comprehensive analysis report following the 4-section structure.")
        if source_counter > 0:
            prompt_parts.append(f"IMPORTANT: When citing information, use the source numbers [1] through [{source_counter}] listed above.")
            prompt_parts.append("Example: 'According to recent reports [1], TSMC announced...'")
        
        return "\n".join(prompt_parts)
    
    def _generate_fallback_report(
        self,
        query: str,
        graph_context: str,
        web_search_results: Optional[Dict]
    ) -> str:
        """
        Generate fallback report when GPT-4o-mini fails
        
        Args:
            query: User query
            graph_context: Graph context
            web_search_results: Web search results
            
        Returns:
            Fallback report
        """
        report_parts = [
            "## [Executive Summary]",
            f"Analysis for: {query}",
            "",
            "## [Market Context]"
        ]
        
        if web_search_results and not web_search_results.get("error"):
            report_parts.append(web_search_results.get("answer", "No market data available."))
        else:
            report_parts.append("No real-time market data available.")
        
        report_parts.extend([
            "",
            "## [Supply Chain Analysis]",
            graph_context if graph_context else "No graph data available.",
            "",
            "## [Risk & Outlook]",
            "Further analysis required. Please consult with domain experts."
        ])
        
        return "\n".join(report_parts)
    
    def generate_quick_summary(
        self,
        query: str,
        context: str,
        max_tokens: int = 500
    ) -> str:
        """
        Generate quick summary (no structured format)
        
        Args:
            query: User query
            context: Context information
            max_tokens: Maximum tokens
            
        Returns:
            Summary text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analyst. Provide concise, accurate answers."
                    },
                    {
                        "role": "user",
                        "content": f"Question: {query}\n\nContext:\n{context}\n\nProvide a clear, concise answer."
                    }
                ],
                temperature=self.temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Quick summary failed: {e}")
            return f"Unable to generate summary. Context: {context[:200]}..."


def test_final_reporter():
    """Test FinalReporter functionality"""
    print("=" * 60)
    print("Testing FinalReporter")
    print("=" * 60)
    
    try:
        reporter = FinalReporter()
        
        # Test data
        query = "What is the impact of Taiwan geopolitical tensions on Nvidia?"
        
        graph_context = """
        Supply Chain Path:
        - ASML (Netherlands) → EUV Equipment → TSMC (Taiwan)
        - TSMC (Taiwan) → Advanced Chips → Nvidia (USA)
        - Nvidia (USA) → AI GPUs → Cloud Providers (Global)
        
        Risk Factors:
        - Taiwan Strait tensions: HIGH impact on TSMC operations
        - TSMC produces 90% of Nvidia's advanced chips
        - No immediate alternative foundries for 5nm/3nm
        """
        
        web_search_results = {
            "query": "Taiwan geopolitical tensions semiconductor",
            "answer": "Recent tensions in the Taiwan Strait have raised concerns about semiconductor supply chain stability. TSMC, the world's largest contract chipmaker, is located in Taiwan and produces chips for major tech companies including Nvidia, Apple, and AMD.",
            "citations": [
                "https://example.com/news1",
                "https://example.com/news2"
            ]
        }
        
        # Generate report
        print("\n📊 Generating comprehensive report...")
        report = reporter.generate_report(
            query=query,
            graph_context=graph_context,
            web_search_results=web_search_results
        )
        
        print("\n" + "=" * 60)
        print("GENERATED REPORT")
        print("=" * 60)
        print(report)
        
        # Test quick summary
        print("\n" + "=" * 60)
        print("Testing Quick Summary")
        print("=" * 60)
        
        summary = reporter.generate_quick_summary(
            query="What is Nvidia?",
            context="Nvidia is a leading GPU manufacturer for AI and gaming."
        )
        
        print(summary)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Make sure OPENAI_API_KEY is set in .env file")


if __name__ == "__main__":
    test_final_reporter()
