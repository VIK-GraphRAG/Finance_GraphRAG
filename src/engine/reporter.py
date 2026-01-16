"""
Financial Report Generator
Implements PRD 4-stage report format:
1. Executive Summary
2. Market Context (from Perplexity)
3. Supply Chain Analysis (from Neo4j multi-hop)
4. Risk & Outlook
"""

import json
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI

from ..config import OPENAI_API_KEY, OPENAI_BASE_URL


class FinancialReporter:
    """
    Generate professional financial analyst reports
    Combines web search results + graph reasoning paths
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini"
    ):
        self.openai_client = AsyncOpenAI(
            api_key=api_key or OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )
        self.model = model
    
    async def generate_report(
        self,
        question: str,
        web_search_results: Dict[str, Any],
        graph_reasoning: Dict[str, Any],
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete financial analysis report
        
        Args:
            question: User's question
            web_search_results: Results from Perplexity search
            graph_reasoning: Results from Neo4j multi-hop reasoning
            additional_context: Optional PDF context
        
        Returns:
            {
                'question': str,
                'executive_summary': str,
                'market_context': str,
                'supply_chain_analysis': str,
                'risk_and_outlook': str,
                'full_report': str (markdown),
                'sources': List[Dict],
                'confidence': float
            }
        """
        
        print(f"📊 Generating financial report for: {question[:50]}...")
        
        # Build comprehensive prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            question,
            web_search_results,
            graph_reasoning,
            additional_context
        )
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Format as complete markdown report
            full_report = self._format_markdown_report(result)
            
            # Collect all sources
            sources = []
            
            # Add web search sources
            if web_search_results and 'sources' in web_search_results:
                sources.extend(web_search_results['sources'])
            
            # Add graph reasoning paths as "internal sources"
            if graph_reasoning and 'reasoning_paths' in graph_reasoning:
                sources.append({
                    'title': 'Internal Knowledge Graph',
                    'url': 'neo4j://local',
                    'snippet': f"{len(graph_reasoning['reasoning_paths'])} reasoning paths analyzed"
                })
            
            return {
                'question': question,
                'executive_summary': result.get('executive_summary', ''),
                'market_context': result.get('market_context', ''),
                'supply_chain_analysis': result.get('supply_chain_analysis', ''),
                'risk_and_outlook': result.get('risk_and_outlook', ''),
                'full_report': full_report,
                'sources': sources,
                'confidence': result.get('confidence', 0.7)
            }
        
        except Exception as e:
            print(f"⚠️  Report generation failed: {e}")
            raise
    
    def _build_system_prompt(self) -> str:
        """Build system prompt defining analyst persona"""
        return """You are a senior financial analyst specializing in the semiconductor and technology industry.

Your expertise includes:
- Supply chain analysis (ASML, TSMC, Nvidia, memory manufacturers)
- Geopolitical risk assessment (Taiwan, US-China relations)
- Technology roadmaps (process nodes, HBM, advanced packaging)
- Regulatory analysis (CHIPS Act, EU AI Act, export controls)
- Corporate financial analysis

Writing Style:
- Professional investment research tone
- Data-driven with specific metrics when available
- Balanced view showing both opportunities and risks
- Clear logical structure with evidence citations

Report Structure (Required):
Generate a JSON with exactly these 4 sections:

1. "executive_summary": 2-3 sentence core conclusion answering the question directly
2. "market_context": Latest market developments based on web search results (3-4 sentences)
3. "supply_chain_analysis": Analysis based on knowledge graph relationships showing multi-hop dependencies (4-5 sentences)
4. "risk_and_outlook": Risk assessment and forward-looking perspective (3-4 sentences)

Also include:
- "confidence": 0.0-1.0 based on evidence strength
- "key_findings": List of 3-5 bullet points

Important:
- Use specific company names, metrics, and relationships
- Cite evidence from provided search results and graph paths
- Maintain objectivity - acknowledge uncertainties
- Write in present tense for current facts, future tense for projections"""
    
    def _build_user_prompt(
        self,
        question: str,
        web_search_results: Dict[str, Any],
        graph_reasoning: Dict[str, Any],
        additional_context: Optional[str]
    ) -> str:
        """Build user prompt with all context"""
        
        prompt_parts = [
            f"**Question:** {question}\n",
            "---\n"
        ]
        
        # Add web search results
        if web_search_results and 'answer' in web_search_results:
            prompt_parts.append("## Latest Market Intelligence (Web Search)")
            prompt_parts.append(web_search_results['answer'])
            
            if 'citations' in web_search_results and web_search_results['citations']:
                prompt_parts.append("\n**Sources:**")
                for i, citation in enumerate(web_search_results['citations'][:5], 1):
                    prompt_parts.append(f"{i}. {citation}")
            
            prompt_parts.append("\n---\n")
        
        # Add graph reasoning
        if graph_reasoning and 'reasoning_paths' in graph_reasoning:
            prompt_parts.append("## Supply Chain Knowledge Graph Analysis")
            prompt_parts.append(f"**Reasoning Type:** {graph_reasoning.get('reasoning_type', 'unknown')}")
            prompt_parts.append(f"**Paths Found:** {len(graph_reasoning['reasoning_paths'])}")
            
            if 'inference' in graph_reasoning:
                prompt_parts.append(f"\n**Inference:** {graph_reasoning['inference']}")
            
            if 'reasoning_steps' in graph_reasoning:
                prompt_parts.append("\n**Reasoning Chain:**")
                for i, step in enumerate(graph_reasoning['reasoning_steps'], 1):
                    prompt_parts.append(f"{i}. {step}")
            
            # Show top 3 paths
            prompt_parts.append("\n**Key Evidence Paths:**")
            for i, path in enumerate(graph_reasoning['reasoning_paths'][:3], 1):
                nodes = path.get('nodes', [])
                rels = path.get('relationships', [])
                
                if nodes:
                    path_str = " → ".join([
                        f"{nodes[j].get('name', 'Unknown')}"
                        + (f" --[{rels[j]}]-->" if j < len(rels) else "")
                        for j in range(len(nodes))
                    ])
                    
                    prompt_parts.append(f"{i}. {path_str}")
            
            prompt_parts.append("\n---\n")
        
        # Add additional PDF context
        if additional_context:
            prompt_parts.append("## Additional Context from User Documents")
            prompt_parts.append(additional_context[:1000])  # Limit length
            prompt_parts.append("\n---\n")
        
        prompt_parts.append("\nGenerate a professional financial analysis report in JSON format with the 4 required sections.")
        
        return "\n".join(prompt_parts)
    
    def _format_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """Format JSON report as markdown"""
        
        output = []
        
        # Title
        output.append("# Financial Analysis Report\n")
        
        # Executive Summary
        output.append("## [Executive Summary]")
        output.append(report_data.get('executive_summary', ''))
        output.append("")
        
        # Market Context
        output.append("## [Market Context]")
        output.append(report_data.get('market_context', ''))
        output.append("")
        
        # Supply Chain Analysis
        output.append("## [Supply Chain Analysis]")
        output.append(report_data.get('supply_chain_analysis', ''))
        output.append("")
        
        # Risk & Outlook
        output.append("## [Risk & Outlook]")
        output.append(report_data.get('risk_and_outlook', ''))
        output.append("")
        
        # Key Findings
        if 'key_findings' in report_data:
            output.append("## Key Findings")
            for finding in report_data['key_findings']:
                output.append(f"- {finding}")
            output.append("")
        
        # Confidence
        confidence = report_data.get('confidence', 0.7)
        output.append(f"**Analysis Confidence:** {confidence:.0%}")
        
        return "\n".join(output)
    
    async def generate_quick_summary(
        self,
        question: str,
        context: str,
        max_words: int = 100
    ) -> str:
        """
        Generate quick summary (for sidebar or preview)
        
        Args:
            question: User question
            context: Combined context
            max_words: Maximum words in summary
        
        Returns:
            Concise summary text
        """
        
        prompt = f"""Question: {question}

Context: {context[:1500]}

Provide a {max_words}-word executive summary answering the question directly."""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial analyst providing concise summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            return f"Summary generation failed: {e}"


async def example_usage():
    """Example: How to use FinancialReporter"""
    
    reporter = FinancialReporter()
    
    # Mock data
    question = "How does Taiwan geopolitical tension affect Nvidia?"
    
    web_search_results = {
        'answer': "Recent tensions in the Taiwan Strait have raised concerns about TSMC's operations. TSMC manufactures over 90% of the world's most advanced chips, including Nvidia's H100 GPUs. Any disruption would severely impact AI infrastructure deployment.",
        'sources': [
            {'title': 'Reuters: Taiwan Tension Analysis', 'url': 'https://example.com/1'},
            {'title': 'Bloomberg: TSMC Supply Risk', 'url': 'https://example.com/2'}
        ],
        'citations': ['https://example.com/1', 'https://example.com/2']
    }
    
    graph_reasoning = {
        'reasoning_type': 'risk_chain',
        'inference': 'Taiwan geopolitical risk propagates through TSMC to Nvidia, creating critical supply chain vulnerability.',
        'reasoning_steps': [
            'Taiwan Strait Tension → AFFECTS → Taiwan (severity: 0.95)',
            'Taiwan → LOCATION_OF → TSMC (100% fab concentration)',
            'TSMC → MANUFACTURES_FOR → Nvidia H100 (critical dependency)',
            'Conclusion: Single point of failure in AI supply chain'
        ],
        'reasoning_paths': [
            {
                'nodes': [
                    {'name': 'Taiwan Strait Tension', 'type': 'MacroIndicator'},
                    {'name': 'Taiwan', 'type': 'Country'},
                    {'name': 'TSMC', 'type': 'Company'},
                    {'name': 'Nvidia', 'type': 'Company'}
                ],
                'relationships': ['AFFECTS', 'LOCATION_OF', 'MANUFACTURES_FOR'],
                'hops': 3
            }
        ],
        'confidence': 0.9
    }
    
    # Generate report
    report = await reporter.generate_report(
        question=question,
        web_search_results=web_search_results,
        graph_reasoning=graph_reasoning
    )
    
    print("\n" + "="*60)
    print("GENERATED REPORT")
    print("="*60)
    print(report['full_report'])
    print("\n" + "="*60)
    print(f"Confidence: {report['confidence']:.0%}")
    print(f"Sources: {len(report['sources'])}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
