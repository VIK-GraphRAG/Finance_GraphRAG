#!/usr/bin/env python3
"""
GraphRAG 시스템 진단
왜 Neo4j를 사용하지 않는지 확인
"""

import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()


async def test_graphrag_engine():
    """GraphRAG Engine 직접 테스트"""
    print("=" * 80)
    print("1️⃣  GraphRAG Engine 테스트")
    print("=" * 80)
    
    try:
        from src.engine.graphrag_engine import PrivacyGraphRAGEngine
        
        engine = PrivacyGraphRAGEngine()
        
        test_query = "TSMC는 어떤 회사인가요?"
        print(f"\n🔍 쿼리: {test_query}")
        print("⏳ 실행 중...\n")
        
        result = await engine.aquery(test_query, return_context=True)
        
        if isinstance(result, dict):
            answer = result.get("answer", "")
            sources = result.get("sources", [])
            backend = result.get("retrieval_backend", "unknown")
            
            print(f"📊 결과:")
            print(f"   Backend: {backend}")
            print(f"   출처 수: {len(sources)}개")
            
            if sources:
                for i, source in enumerate(sources[:3], 1):
                    print(f"   [{i}] {source.get('file', 'N/A')}")
            
            return len(sources) > 0 and backend != "unknown"
        else:
            print(f"❌ 결과 형식 오류")
            return False
            
    except Exception as e:
        print(f"❌ GraphRAG Engine 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_neo4j_retriever():
    """Neo4j Retriever 직접 테스트"""
    print("\n" + "=" * 80)
    print("2️⃣  Neo4j Retriever 테스트")
    print("=" * 80)
    
    try:
        from src.engine.neo4j_retriever import Neo4jRetriever
        
        retriever = Neo4jRetriever()
        
        test_query = "TSMC"
        print(f"\n🔍 쿼리: {test_query}")
        
        result = retriever.retrieve(test_query, depth=2, limit=10, top_sources=5)
        
        context = result.get('context', '')
        sources = result.get('sources', [])
        
        print(f"\n📊 결과:")
        print(f"   Context 길이: {len(context)} 문자")
        print(f"   Sources: {len(sources)}개")
        
        if sources:
            print(f"\n   ✅ Neo4j Retriever 작동!")
            for i, source in enumerate(sources[:3], 1):
                print(f"   [{i}] {source.get('file', 'N/A')}")
            retriever.close()
            return True
        else:
            print(f"\n   ❌ Sources 없음 (Neo4j에서 데이터를 못 찾음)")
            retriever.close()
            return False
            
    except Exception as e:
        print(f"❌ Neo4j Retriever 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_neo4j_connection():
    """Neo4j 연결 및 데이터 확인"""
    print("\n" + "=" * 80)
    print("3️⃣  Neo4j 연결 및 데이터 확인")
    print("=" * 80)
    
    try:
        from neo4j import GraphDatabase
        import os
        
        uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        user = os.getenv('NEO4J_USERNAME', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', '')
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # 노드 수 확인
            result = session.run('MATCH (n) RETURN count(n) as count')
            node_count = result.single()['count']
            
            # TSMC 노드 확인
            result = session.run("""
                MATCH (n)
                WHERE toLower(n.name) CONTAINS 'tsmc'
                RETURN n.name as name, labels(n) as labels
                LIMIT 5
            """)
            
            tsmc_nodes = list(result)
            
            print(f"\n📊 Neo4j 상태:")
            print(f"   총 노드: {node_count}개")
            print(f"   TSMC 노드: {len(tsmc_nodes)}개")
            
            if tsmc_nodes:
                print(f"\n   ✅ TSMC 데이터 존재:")
                for node in tsmc_nodes:
                    print(f"      - {node['labels']}: {node['name']}")
                driver.close()
                return True
            else:
                print(f"\n   ❌ TSMC 노드 없음")
                driver.close()
                return False
                
    except Exception as e:
        print(f"❌ Neo4j 연결 실패: {e}")
        return False


async def main():
    """전체 진단 실행"""
    print("\n" + "=" * 80)
    print("  🔍 GraphRAG 시스템 진단")
    print("  왜 Neo4j를 사용하지 않는가?")
    print("=" * 80)
    
    results = {}
    
    # Test 1: Neo4j 연결 및 데이터
    results['neo4j_data'] = test_neo4j_connection()
    
    # Test 2: Neo4j Retriever
    if results['neo4j_data']:
        results['neo4j_retriever'] = await test_neo4j_retriever()
    else:
        results['neo4j_retriever'] = False
        print("\n⏭️  Neo4j 데이터가 없어서 Retriever 테스트 건너뜀")
    
    # Test 3: GraphRAG Engine
    if results['neo4j_data']:
        results['graphrag_engine'] = await test_graphrag_engine()
    else:
        results['graphrag_engine'] = False
        print("\n⏭️  Neo4j 데이터가 없어서 Engine 테스트 건너뜀")
    
    # 진단 결과
    print("\n" + "=" * 80)
    print("📋 진단 결과")
    print("=" * 80)
    
    print(f"\n✅ 통과한 테스트:")
    for name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")
    
    print("\n" + "=" * 80)
    print("💡 문제 원인 및 해결 방법")
    print("=" * 80)
    
    if not results['neo4j_data']:
        print("""
❌ 문제: Neo4j에 데이터가 없습니다!

해결:
1. 데이터 시딩:
   python scripts/seed/seed_semiconductor.py

2. 확인:
   python test_neo4j_direct.py
        """)
    
    elif not results['neo4j_retriever']:
        print("""
❌ 문제: Neo4j Retriever가 데이터를 찾지 못합니다!

원인:
- execute_query() 반환 형식 문제
- 노드 검색 쿼리 오류
- Label 매칭 문제

해결:
1. Neo4j Retriever 로그 확인
2. 직접 Cypher 쿼리 테스트
3. Label 확인 (Entity vs Company vs Product)
        """)
    
    elif not results['graphrag_engine']:
        print("""
❌ 문제: GraphRAG Engine이 Neo4j를 사용하지 않습니다!

원인:
- Privacy Analyst Agent 설정 문제
- Neo4j Retriever 연결 오류
- Perplexity 폴백이 너무 빨리 작동

해결:
1. Privacy Analyst Agent 로그 확인
2. Neo4j Retriever 연결 확인
3. Perplexity 폴백 조건 수정
        """)
    
    else:
        print("""
✅ 모든 테스트 통과!

하지만 FastAPI /query 엔드포인트에서 문제가 있습니다.

확인 사항:
1. FastAPI 로그 확인
2. /query 엔드포인트 코드 검토
3. Perplexity 폴백 로직 확인
        """)


if __name__ == "__main__":
    asyncio.run(main())
