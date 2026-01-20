#!/usr/bin/env python3
"""
GraphRAG 시스템이 실제로 Neo4j 그래프를 사용하는지 테스트
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from src.db.neo4j_db import Neo4jDatabase
from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD


def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def check_neo4j_data():
    """Check if Neo4j has data"""
    print_section("1️⃣  Neo4j 데이터베이스 상태 확인")
    
    db = Neo4jDatabase(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    
    # Count nodes
    node_result = db.execute_query("MATCH (n) RETURN count(n) as count")
    node_count = node_result[0]['count'] if node_result else 0
    
    # Count relationships
    rel_result = db.execute_query("MATCH ()-[r]->() RETURN count(r) as count")
    rel_count = rel_result[0]['count'] if rel_result else 0
    
    print(f"📊 노드 수: {node_count}")
    print(f"🔗 관계 수: {rel_count}")
    
    if node_count == 0:
        print("❌ Neo4j 데이터베이스가 비어있습니다!")
        print("\n💡 해결 방법:")
        print("   1. 샘플 데이터 시딩:")
        print("      python scripts/seed/seed_semiconductor.py")
        print("\n   2. PDF 업로드:")
        print("      python scripts/upload/upload_baseline_pdfs.py")
        print("\n   3. Streamlit UI에서 Database Upload 탭 사용")
        return False
    else:
        print("✅ Neo4j 데이터베이스에 데이터가 있습니다!")
        
        # Show sample nodes
        sample = db.execute_query("""
            MATCH (n)
            RETURN labels(n)[0] as type, count(n) as count
            ORDER BY count DESC
            LIMIT 10
        """)
        
        print("\n📋 노드 타입별 개수:")
        for row in sample:
            print(f"   {row['type']}: {row['count']}개")
        
        db.close()
        return True


async def test_graph_retrieval():
    """Test if system uses Neo4j for retrieval"""
    print_section("2️⃣  그래프 기반 검색 테스트")
    
    try:
        from src.engine.neo4j_retriever import Neo4jRetriever
        
        retriever = Neo4jRetriever()
        
        # Test query
        test_query = "TSMC supply chain risks"
        print(f"🔍 테스트 쿼리: '{test_query}'")
        
        # Retrieve context
        results = await retriever.retrieve(test_query, top_k=5)
        
        if results:
            print(f"✅ Neo4j에서 {len(results)}개 결과 검색됨:")
            for i, result in enumerate(results, 1):
                print(f"\n   [{i}] {result.get('entity', 'N/A')}")
                print(f"       타입: {result.get('type', 'N/A')}")
                print(f"       관계: {result.get('relationships', [])[:3]}")
        else:
            print("❌ Neo4j에서 결과를 찾을 수 없습니다.")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 그래프 검색 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_privacy_analyst():
    """Test Privacy Analyst Agent"""
    print_section("3️⃣  Privacy Analyst Agent 테스트")
    
    try:
        from src.agents.privacy_analyst import PrivacyAnalystAgent
        from src.db.neo4j_db import Neo4jDatabase
        
        db = Neo4jDatabase(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
        agent = PrivacyAnalystAgent(neo4j_db=db)
        
        test_query = "What companies are in the database?"
        print(f"🔍 테스트 쿼리: '{test_query}'")
        
        # Test Neo4j search
        results = await agent.neo4j_search("TSMC")
        
        if results:
            print(f"✅ Agent가 Neo4j에서 {len(results)}개 결과 찾음:")
            for result in results[:3]:
                print(f"   - {result.get('name')} ({result.get('type')})")
            return True
        else:
            print("❌ Agent가 Neo4j에서 결과를 찾을 수 없습니다.")
            return False
        
    except Exception as e:
        print(f"❌ Privacy Analyst Agent 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_web_search_usage():
    """Check if system is using web search (Perplexity-like)"""
    print_section("4️⃣  웹 검색 사용 여부 확인")
    
    # Check if Tavily or similar web search is configured
    tavily_key = os.getenv("TAVILY_API_KEY")
    serp_key = os.getenv("SERP_API_KEY")
    
    print(f"🌐 Tavily API Key: {'설정됨' if tavily_key else '없음'}")
    print(f"🌐 SERP API Key: {'설정됨' if serp_key else '없음'}")
    
    # Check if multi-agent system uses web search
    try:
        from src.agents.collector_agent import CollectorAgent
        
        print("\n📋 CollectorAgent 분석:")
        # This would require looking at the code
        print("   CollectorAgent는 웹 검색 도구를 사용할 수 있습니다.")
        
        # Check if it's actually being used
        import inspect
        source = inspect.getsource(CollectorAgent)
        
        if "tavily" in source.lower() or "web_search" in source.lower():
            print("   ⚠️  CollectorAgent에서 웹 검색 도구 발견!")
            return True
        else:
            print("   ✅ CollectorAgent는 웹 검색을 사용하지 않습니다.")
            return False
            
    except Exception as e:
        print(f"   ⚠️  분석 실패: {e}")
        return False


def analyze_query_flow():
    """Analyze how queries are processed"""
    print_section("5️⃣  쿼리 처리 흐름 분석")
    
    print("📋 예상 쿼리 흐름:")
    print("   1. User Query → Streamlit UI")
    print("   2. Streamlit → FastAPI (/query endpoint)")
    print("   3. FastAPI → GraphRAG Engine (aquery)")
    print("   4. GraphRAG Engine → ?")
    print("")
    
    try:
        from src.engine.graphrag_engine import PrivacyGraphRAGEngine
        import inspect
        
        # Get aquery source code
        source = inspect.getsource(PrivacyGraphRAGEngine.aquery)
        
        print("🔍 aquery() 메서드 분석:")
        
        if "PrivacyAnalystAgent" in source:
            print("   ✅ Privacy Analyst Agent 사용")
        
        if "neo4j" in source.lower():
            print("   ✅ Neo4j 관련 코드 발견")
        
        if "tavily" in source.lower() or "web_search" in source.lower():
            print("   ⚠️  웹 검색 관련 코드 발견")
        
        if "perplexity" in source.lower():
            print("   ⚠️  Perplexity 관련 코드 발견")
        
        # Check what happens when Neo4j is empty
        if "_simple_analyze" in source or "fallback" in source.lower():
            print("   ⚠️  Fallback 로직 발견 (Neo4j 비어있을 때)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 분석 실패: {e}")
        return False


async def test_actual_query():
    """Test with actual query to see what happens"""
    print_section("6️⃣  실제 쿼리 테스트")
    
    try:
        from src.engine.graphrag_engine import PrivacyGraphRAGEngine
        
        engine = PrivacyGraphRAGEngine()
        
        test_query = "What is TSMC?"
        print(f"🔍 테스트 쿼리: '{test_query}'")
        print("⏳ 쿼리 실행 중...\n")
        
        # Run query with verbose output
        result = await engine.aquery(test_query, return_context=True)
        
        print("\n📊 결과 분석:")
        
        if isinstance(result, dict):
            answer = result.get("answer", "")
            sources = result.get("sources", [])
            backend = result.get("retrieval_backend", "unknown")
            
            print(f"   답변 길이: {len(answer)} 문자")
            print(f"   출처 수: {len(sources)}개")
            print(f"   검색 백엔드: {backend}")
            
            if backend == "privacy_mode_neo4j":
                print("   ✅ Neo4j 기반 검색 사용!")
            elif backend == "web_search":
                print("   ⚠️  웹 검색 사용!")
            else:
                print(f"   ⚠️  알 수 없는 백엔드: {backend}")
            
            if sources:
                print("\n   📚 출처:")
                for i, source in enumerate(sources[:3], 1):
                    print(f"      [{i}] {source.get('file', 'N/A')}")
            
            # Check if answer is generic or specific
            if "데이터" in answer and "없" in answer:
                print("\n   ⚠️  답변이 '데이터 없음' 메시지일 수 있습니다.")
            
        else:
            print(f"   답변: {result[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 쿼리 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results: dict):
    """Print test summary"""
    print_section("📊 테스트 결과 요약")
    
    print("\n✅ 성공한 테스트:")
    for name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")
    
    print("\n" + "=" * 80)
    print("💡 결론:")
    print("=" * 80)
    
    has_data = results.get("neo4j_data", False)
    uses_graph = results.get("graph_retrieval", False)
    uses_web = results.get("web_search", False)
    
    if not has_data:
        print("""
❌ 문제: Neo4j 데이터베이스가 비어있습니다!

현재 상태:
- GraphRAG 시스템이 설치되어 있음
- Neo4j가 실행 중
- 하지만 데이터가 없어서 그래프 기반 검색 불가능

결과:
- 답변이 일반적인 내용만 포함 (Perplexity처럼 보임)
- 실제로는 그래프를 사용하지 못하고 있음

해결 방법:
1. 샘플 데이터 시딩:
   python scripts/seed/seed_semiconductor.py

2. PDF 업로드:
   python scripts/utils/enrich_risk_factors.py --add
   python scripts/upload/upload_baseline_pdfs.py

3. Streamlit UI에서 Database Upload 탭 사용

데이터 추가 후 다시 테스트하세요!
        """)
    
    elif uses_graph:
        print("""
✅ 정상: 시스템이 Neo4j 그래프를 올바르게 사용하고 있습니다!

현재 상태:
- Neo4j에 데이터 있음
- 그래프 기반 검색 작동
- 답변이 그래프 데이터를 기반으로 생성됨

이것은 Perplexity와 다릅니다:
- Perplexity: 웹 검색 → 요약
- 이 시스템: Neo4j 그래프 → 관계 분석 → 답변
        """)
    
    elif uses_web:
        print("""
⚠️  경고: 시스템이 웹 검색을 사용하고 있습니다!

현재 상태:
- Neo4j에 데이터 있음
- 하지만 웹 검색을 주로 사용
- Perplexity와 유사한 동작

권장 사항:
- Multi-Agent 시스템 설정 확인
- CollectorAgent가 웹 검색 대신 Neo4j 사용하도록 설정
        """)


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("  🧪 GraphRAG 시스템 분석")
    print("  Neo4j 그래프 vs 웹 검색 (Perplexity-like)")
    print("=" * 80)
    print(f"  시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test 1: Check Neo4j data
    results["neo4j_data"] = check_neo4j_data()
    
    # Test 2: Test graph retrieval (only if data exists)
    if results["neo4j_data"]:
        results["graph_retrieval"] = await test_graph_retrieval()
        results["privacy_analyst"] = await test_privacy_analyst()
    else:
        results["graph_retrieval"] = False
        results["privacy_analyst"] = False
        print("\n⏭️  Neo4j 데이터가 없어서 나머지 테스트를 건너뜁니다.")
    
    # Test 3: Check web search usage
    results["web_search"] = check_web_search_usage()
    
    # Test 4: Analyze query flow
    results["query_flow"] = analyze_query_flow()
    
    # Test 5: Actual query test (only if data exists)
    if results["neo4j_data"]:
        results["actual_query"] = await test_actual_query()
    else:
        results["actual_query"] = False
    
    # Print summary
    print_summary(results)
    
    print(f"\n  종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
