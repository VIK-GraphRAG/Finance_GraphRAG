"""
Integration Test for Tech-Analyst GraphRAG System
Tests the complete workflow: Perplexity Search + Neo4j Reasoning + Report Generation
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.engine.search_engine import PerplexitySearchEngine
from src.engine.reasoner import MultiHopReasoner
from src.engine.reporter import FinancialReporter
from src.config import PERPLEXITY_API_KEY, NEO4J_URI


class TechAnalystWorkflow:
    """
    Complete end-to-end workflow for tech company analysis
    """
    
    def __init__(self):
        # Check prerequisites
        if not PERPLEXITY_API_KEY:
            print("⚠️  PERPLEXITY_API_KEY not set. Web search will be skipped.")
            self.search_engine = None
        else:
            self.search_engine = PerplexitySearchEngine()
        
        if not NEO4J_URI:
            print("⚠️  NEO4J_URI not set. Graph reasoning will be skipped.")
            self.reasoner = None
        else:
            self.reasoner = MultiHopReasoner()
        
        self.reporter = FinancialReporter()
    
    async def analyze(self, question: str) -> dict:
        """
        Complete analysis workflow
        
        Args:
            question: User's question
        
        Returns:
            Complete analysis report
        """
        
        print(f"\n{'='*70}")
        print(f"🎯 Question: {question}")
        print('='*70)
        
        # Step 1: Web Search (if available)
        web_search_results = None
        
        if self.search_engine:
            try:
                print("\n📡 Step 1: Web Search (Perplexity API)")
                print("-" * 70)
                web_search_results = self.search_engine.search(question)
                print(f"✅ Found {len(web_search_results.get('citations', []))} sources")
                print(f"Answer preview: {web_search_results['answer'][:200]}...")
            except Exception as e:
                print(f"⚠️  Web search failed: {e}")
        else:
            print("\n⏭️  Step 1: Web Search - SKIPPED (no API key)")
        
        # Step 2: Graph Reasoning (if available)
        graph_reasoning = None
        
        if self.reasoner:
            try:
                print("\n🧠 Step 2: Knowledge Graph Reasoning (Neo4j)")
                print("-" * 70)
                graph_reasoning = await self.reasoner.reason(question, max_hops=3)
                print(f"✅ Found {len(graph_reasoning.get('reasoning_paths', []))} reasoning paths")
                print(f"Reasoning type: {graph_reasoning.get('reasoning_type', 'unknown')}")
                print(f"Confidence: {graph_reasoning.get('confidence', 0):.0%}")
                
                if 'inference' in graph_reasoning:
                    print(f"\nInference: {graph_reasoning['inference'][:150]}...")
            except Exception as e:
                print(f"⚠️  Graph reasoning failed: {e}")
                print(f"   Make sure baseline graph is built: python seed_baseline_graph.py")
        else:
            print("\n⏭️  Step 2: Graph Reasoning - SKIPPED (no Neo4j)")
        
        # Step 3: Generate Report
        print("\n📊 Step 3: Generate Financial Report")
        print("-" * 70)
        
        try:
            report = await self.reporter.generate_report(
                question=question,
                web_search_results=web_search_results or {},
                graph_reasoning=graph_reasoning or {}
            )
            
            print("✅ Report generated")
            
            return report
        
        except Exception as e:
            print(f"⚠️  Report generation failed: {e}")
            return {
                'question': question,
                'error': str(e),
                'full_report': f"# Error\n\nFailed to generate report: {e}"
            }
    
    def close(self):
        """Clean up connections"""
        if self.reasoner:
            self.reasoner.close()
        if self.search_engine:
            self.search_engine.clear_cache()


async def test_scenario_1():
    """
    Scenario 1: Taiwan earthquake impact on semiconductor industry
    """
    print("\n\n" + "="*70)
    print("TEST SCENARIO 1: Geopolitical Risk Analysis")
    print("="*70)
    
    workflow = TechAnalystWorkflow()
    
    question = "대만 지진이 반도체 산업에 미치는 영향은?"
    
    report = await workflow.analyze(question)
    
    print("\n" + "="*70)
    print("FINAL REPORT")
    print("="*70)
    print(report['full_report'])
    
    workflow.close()
    
    return report


async def test_scenario_2():
    """
    Scenario 2: CHIPS Act impact on Intel
    """
    print("\n\n" + "="*70)
    print("TEST SCENARIO 2: Regulation Analysis")
    print("="*70)
    
    workflow = TechAnalystWorkflow()
    
    question = "CHIPS Act가 Intel에 어떤 영향을 주나?"
    
    report = await workflow.analyze(question)
    
    print("\n" + "="*70)
    print("FINAL REPORT")
    print("="*70)
    print(report['full_report'])
    
    workflow.close()
    
    return report


async def test_scenario_3():
    """
    Scenario 3: HBM4 delay impact analysis
    """
    print("\n\n" + "="*70)
    print("TEST SCENARIO 3: Technology Roadmap Analysis")
    print("="*70)
    
    workflow = TechAnalystWorkflow()
    
    question = "HBM4 도입이 늦어지면 누가 영향받나?"
    
    report = await workflow.analyze(question)
    
    print("\n" + "="*70)
    print("FINAL REPORT")
    print("="*70)
    print(report['full_report'])
    
    workflow.close()
    
    return report


async def test_all_scenarios():
    """Run all test scenarios"""
    
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║     Tech-Analyst GraphRAG Integration Test                       ║
║                                                                    ║
║     Testing: Perplexity + Neo4j + Report Generation              ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run all scenarios
    results = []
    
    try:
        result1 = await test_scenario_1()
        results.append(('Scenario 1', result1))
    except Exception as e:
        print(f"❌ Scenario 1 failed: {e}")
        results.append(('Scenario 1', {'error': str(e)}))
    
    try:
        result2 = await test_scenario_2()
        results.append(('Scenario 2', result2))
    except Exception as e:
        print(f"❌ Scenario 2 failed: {e}")
        results.append(('Scenario 2', {'error': str(e)}))
    
    try:
        result3 = await test_scenario_3()
        results.append(('Scenario 3', result3))
    except Exception as e:
        print(f"❌ Scenario 3 failed: {e}")
        results.append(('Scenario 3', {'error': str(e)}))
    
    # Summary
    print("\n\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for scenario_name, result in results:
        if 'error' in result:
            print(f"❌ {scenario_name}: FAILED - {result['error']}")
        else:
            confidence = result.get('confidence', 0)
            sources = len(result.get('sources', []))
            print(f"✅ {scenario_name}: PASSED (confidence: {confidence:.0%}, sources: {sources})")
    
    print("="*70)
    
    # Check prerequisites
    print("\n📋 System Status:")
    print(f"   Perplexity API: {'✅ Configured' if PERPLEXITY_API_KEY else '❌ Missing'}")
    print(f"   Neo4j Database: {'✅ Configured' if NEO4J_URI else '❌ Missing'}")
    print(f"   OpenAI API: ✅ Required for report generation")
    
    if not PERPLEXITY_API_KEY:
        print("\n💡 To enable web search:")
        print("   Set PERPLEXITY_API_KEY in .env file")
    
    if not NEO4J_URI:
        print("\n💡 To enable graph reasoning:")
        print("   1. Start Neo4j: docker-compose up -d")
        print("   2. Build baseline graph: python seed_baseline_graph.py")
        print("   3. Set NEO4J_URI in .env file")
    
    print("\n" + "="*70)


async def quick_test():
    """
    Quick test with a single question
    For rapid iteration during development
    """
    
    print("\n🚀 Quick Test Mode\n")
    
    workflow = TechAnalystWorkflow()
    
    # Simple test question
    question = "What is Nvidia's main supply chain risk?"
    
    report = await workflow.analyze(question)
    
    print("\n" + "="*70)
    print("REPORT")
    print("="*70)
    print(report['full_report'])
    
    workflow.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # Quick test mode
        asyncio.run(quick_test())
    else:
        # Full test suite
        asyncio.run(test_all_scenarios())
