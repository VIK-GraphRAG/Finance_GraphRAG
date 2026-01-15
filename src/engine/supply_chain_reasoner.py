"""
Supply Chain Path Reasoning Engine
공급망 경로 추론 엔진 - 포트폴리오 리스크 분석
"""

from typing import List, Dict, Any, Tuple
from neo4j import GraphDatabase
from openai import AsyncOpenAI
import json
import asyncio

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, OPENAI_API_KEY, OPENAI_BASE_URL


class SupplyChainReasoner:
    """
    Analyze supply chain risk propagation with multi-hop reasoning
    
    Example scenario:
    "대만 지진 발생 -> TSMC 생산 차질 -> Nvidia 출하량 감소 -> HBM 수요 급감"
    """
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        self.openai_client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )
        self.model = "gpt-4o-mini"
    
    def close(self):
        """Close connections"""
        self.driver.close()
    
    def find_supply_chain_paths(
        self, 
        trigger_entity: str,
        affected_companies: List[str],
        max_hops: int = 4
    ) -> List[Dict]:
        """
        Find all supply chain paths from trigger to affected companies
        
        Args:
            trigger_entity: Starting point (e.g., "Taiwan Earthquake Risk")
            affected_companies: Companies in portfolio (e.g., ["Nvidia", "Samsung Electronics"])
            max_hops: Maximum path length
        
        Returns:
            List of paths with nodes and relationships
        """
        
        # Build companies filter
        companies_filter = "'" + "', '".join(affected_companies) + "'"
        
        query = f"""
        MATCH path = (trigger)-[*1..{max_hops}]->(company:Company)
        WHERE trigger.name = '{trigger_entity}'
          AND company.name IN [{companies_filter}]
          AND ALL(rel IN relationships(path) WHERE 
              type(rel) IN ['DISRUPTS', 'BLOCKS', 'DEPENDS_ON', 'DEPENDS_ON_COMPANY', 
                           'REQUIRES_PROCESS', 'PRODUCES', 'REQUIRES_COMPONENT'])
        WITH path,
             [n IN nodes(path) | {{
               name: n.name,
               type: labels(n)[0],
               properties: properties(n)
             }}] as node_list,
             [r IN relationships(path) | {{
               type: type(r),
               properties: properties(r)
             }}] as rel_list,
             length(path) as hops
        RETURN node_list as nodes,
               rel_list as relationships,
               hops
        ORDER BY hops ASC
        LIMIT 20
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            paths = []
            
            for record in result:
                paths.append({
                    'nodes': record['nodes'],
                    'relationships': record['relationships'],
                    'hops': record['hops']
                })
            
            return paths
    
    async def analyze_impact_chain(
        self,
        paths: List[Dict],
        scenario: str
    ) -> Dict[str, Any]:
        """
        Analyze impact propagation using LLM
        
        Args:
            paths: Supply chain paths from find_supply_chain_paths
            scenario: Scenario description (e.g., "Taiwan earthquake")
        
        Returns:
            {
                'scenario': str,
                'impact_summary': str,
                'cascade_analysis': [...],
                'risk_level': str,
                'recommendations': [...]
            }
        """
        
        # Format paths for LLM
        paths_desc = []
        for i, path in enumerate(paths[:5], 1):  # Top 5 paths
            nodes = path['nodes']
            rels = path['relationships']
            
            path_str = f"Path {i} ({path['hops']} hops):\n  "
            for j, node in enumerate(nodes):
                path_str += f"{node['type']}: {node['name']}"
                if j < len(rels):
                    path_str += f" --[{rels[j]['type']}]-> "
            
            paths_desc.append(path_str)
        
        paths_text = "\n\n".join(paths_desc)
        
        system_prompt = """You are a semiconductor supply chain risk analyst.

Your task: Analyze multi-hop impact propagation in the supply chain.

Provide detailed analysis in Korean, covering:
1. **시나리오 요약**: What happens in the scenario
2. **연쇄 영향 분석**: Step-by-step cascade (A→B→C logic)
3. **리스크 수준**: Overall risk level (Critical/High/Medium/Low)
4. **포트폴리오 영향**: Impact on each company in portfolio
5. **대응 방안**: Recommendations

Output JSON:
{
  "scenario_summary": "시나리오 한줄 요약",
  "impact_summary": "전체 영향 요약 (2-3 문장)",
  "cascade_analysis": [
    {
      "stage": 1,
      "event": "Initial impact",
      "description": "Detailed explanation",
      "severity": 0.0-1.0
    }
  ],
  "risk_level": "Critical|High|Medium|Low",
  "company_impacts": {
    "Company Name": {
      "impact_type": "Direct|Indirect",
      "severity": 0.0-1.0,
      "description": "How this company is affected",
      "financial_impact": "Revenue/profit impact estimate"
    }
  },
  "recommendations": [
    "Actionable recommendation 1",
    "Actionable recommendation 2"
  ],
  "timeline": "Expected duration of impact"
}

Example cascade analysis format:
Stage 1: Taiwan earthquake damages TSMC fab (severity: 0.9)
Stage 2: TSMC 4nm production halts, affecting GPU wafer supply (severity: 0.95)
Stage 3: Nvidia H100 GPU shipments delayed by 3-6 months (severity: 0.8)
Stage 4: Data center customers cancel orders, reducing HBM demand from Samsung (severity: 0.6)

Be specific about numbers, percentages, and timeline where possible."""

        user_message = f"""Scenario: {scenario}

Supply Chain Paths:
{paths_text}

Analyze the cascading impact on the portfolio companies through these supply chain paths."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                timeout=60
            )
            
            analysis = json.loads(response.choices[0].message.content)
            analysis['scenario'] = scenario
            analysis['paths_analyzed'] = len(paths)
            
            return analysis
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return {
                'scenario': scenario,
                'impact_summary': 'Analysis failed',
                'error': str(e)
            }
    
    async def portfolio_risk_analysis(
        self,
        scenario: str,
        portfolio: List[str],
        max_hops: int = 4
    ) -> Dict[str, Any]:
        """
        Complete portfolio risk analysis for a given scenario
        
        Args:
            scenario: Risk scenario (e.g., "대만 지진")
            portfolio: List of company names in portfolio
            max_hops: Maximum supply chain hops to analyze
        
        Returns:
            Complete analysis with paths, impact assessment, and recommendations
        """
        
        print(f"\n🔍 Analyzing scenario: {scenario}")
        print(f"📊 Portfolio: {', '.join(portfolio)}")
        
        # Map scenario to trigger entity
        trigger_mapping = {
            '대만 지진': 'Taiwan Earthquake Risk',
            'taiwan earthquake': 'Taiwan Earthquake Risk',
            '대만 해협 긴장': 'Taiwan Strait Tension',
            'taiwan tension': 'Taiwan Strait Tension',
            '미중 무역전쟁': 'US-China Tech War',
            'us china trade war': 'US-China Tech War',
            'asml 수출 금지': 'ASML Export Ban',
            'euv ban': 'ASML Export Ban'
        }
        
        trigger = trigger_mapping.get(scenario.lower(), scenario)
        
        # Find supply chain paths
        print(f"\n🔗 Finding supply chain paths from '{trigger}'...")
        paths = self.find_supply_chain_paths(trigger, portfolio, max_hops)
        
        if not paths:
            print(f"⚠️  No direct paths found")
            return {
                'scenario': scenario,
                'portfolio': portfolio,
                'paths': [],
                'analysis': {
                    'impact_summary': f'No direct supply chain connection found between {trigger} and portfolio companies.',
                    'risk_level': 'Low'
                }
            }
        
        print(f"✅ Found {len(paths)} supply chain paths")
        
        # Analyze impact
        print(f"\n🧠 Analyzing impact cascade...")
        analysis = await self.analyze_impact_chain(paths, scenario)
        
        return {
            'scenario': scenario,
            'trigger_entity': trigger,
            'portfolio': portfolio,
            'paths': paths,
            'analysis': analysis
        }
    
    def format_report(self, result: Dict[str, Any]) -> str:
        """
        Format analysis result as readable report
        """
        
        analysis = result.get('analysis', {})
        
        report = [
            "="*60,
            "🔴 공급망 리스크 분석 리포트",
            "="*60,
            "",
            f"📋 시나리오: {result['scenario']}",
            f"💼 포트폴리오: {', '.join(result['portfolio'])}",
            f"🔗 분석된 경로: {len(result['paths'])}개",
            "",
            "─"*60,
            "📊 영향 요약",
            "─"*60,
            analysis.get('impact_summary', 'N/A'),
            "",
            f"⚠️  리스크 수준: **{analysis.get('risk_level', 'Unknown')}**",
            f"⏱️  예상 기간: {analysis.get('timeline', 'N/A')}",
            "",
            "─"*60,
            "🔗 연쇄 영향 분석",
            "─"*60,
        ]
        
        for stage in analysis.get('cascade_analysis', []):
            report.append(f"\n▶️  Stage {stage['stage']}: {stage['event']}")
            report.append(f"   심각도: {'🔴' * int(stage['severity'] * 5)} {stage['severity']:.1%}")
            report.append(f"   {stage['description']}")
        
        report.extend([
            "",
            "─"*60,
            "💼 포트폴리오 기업별 영향",
            "─"*60,
        ])
        
        for company, impact in analysis.get('company_impacts', {}).items():
            report.append(f"\n🏢 {company}")
            report.append(f"   영향 유형: {impact['impact_type']}")
            report.append(f"   심각도: {'🔴' * int(impact['severity'] * 5)} {impact['severity']:.1%}")
            report.append(f"   설명: {impact['description']}")
            report.append(f"   재무 영향: {impact.get('financial_impact', 'N/A')}")
        
        report.extend([
            "",
            "─"*60,
            "💡 대응 방안",
            "─"*60,
        ])
        
        for i, rec in enumerate(analysis.get('recommendations', []), 1):
            report.append(f"{i}. {rec}")
        
        report.extend([
            "",
            "─"*60,
            "🛤️  주요 공급망 경로",
            "─"*60,
        ])
        
        for i, path in enumerate(result['paths'][:3], 1):
            nodes = path['nodes']
            rels = path['relationships']
            
            report.append(f"\n경로 {i} ({path['hops']} hops):")
            for j, node in enumerate(nodes):
                report.append(f"  {node['type']}: {node['name']}")
                if j < len(rels):
                    report.append(f"    ↓ [{rels[j]['type']}]")
        
        report.append("\n" + "="*60)
        
        return "\n".join(report)


async def example_scenario():
    """Example: Portfolio risk analysis"""
    
    reasoner = SupplyChainReasoner()
    
    # Scenario: Taiwan earthquake
    result = await reasoner.portfolio_risk_analysis(
        scenario="대만 지진",
        portfolio=["Nvidia", "Samsung Electronics"],
        max_hops=4
    )
    
    # Print report
    report = reasoner.format_report(result)
    print(report)
    
    reasoner.close()


if __name__ == "__main__":
    asyncio.run(example_scenario())
