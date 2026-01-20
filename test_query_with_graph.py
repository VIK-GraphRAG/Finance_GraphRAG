#!/usr/bin/env python3
"""
실제 쿼리를 실행하여 그래프 사용 여부 확인
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()


async def test_streamlit_query():
    """Streamlit UI처럼 쿼리 실행"""
    print("=" * 80)
    print("🧪 Streamlit UI 시뮬레이션 테스트")
    print("=" * 80)
    
    # Simulate what Streamlit does
    import requests
    
    test_queries = [
        "TSMC supply chain risks",
        "Nvidia와 관련된 회사들은?",
        "Taiwan 관련 지정학적 리스크는?"
    ]
    
    print("\n📡 FastAPI 서버 상태 확인...")
    try:
        health = requests.get("http://localhost:8000/health")
        print(f"✅ 서버 실행 중: {health.json()}")
    except:
        print("❌ FastAPI 서버가 실행되지 않았습니다.")
        print("💡 서버 시작: uvicorn src.app:app --reload")
        return
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"🔍 쿼리: {query}")
        print(f"{'='*80}")
        
        try:
            response = requests.post(
                "http://localhost:8000/query",
                json={"question": query},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                answer = result.get("answer", "")
                sources = result.get("sources", [])
                
                print(f"\n📊 결과:")
                print(f"   답변 길이: {len(answer)} 문자")
                print(f"   출처 수: {len(sources)}개")
                
                if sources:
                    print(f"\n   📚 출처:")
                    for i, source in enumerate(sources[:5], 1):
                        print(f"      [{i}] {source.get('file', 'N/A')}")
                
                # Analyze answer content
                print(f"\n   📝 답변 시작:")
                print(f"      {answer[:300]}...")
                
                # Check if Neo4j data is used
                keywords = ['TSMC', 'Nvidia', 'Taiwan', 'supply chain']
                found_keywords = [k for k in keywords if k.lower() in answer.lower()]
                
                if found_keywords:
                    print(f"\n   ✅ 그래프 데이터 키워드 발견: {found_keywords}")
                else:
                    print(f"\n   ⚠️  그래프 데이터 키워드 없음")
                
            else:
                print(f"❌ 에러: {response.status_code}")
                print(response.text)
        
        except Exception as e:
            print(f"❌ 요청 실패: {e}")


async def test_direct_engine():
    """직접 GraphRAG Engine 사용"""
    print("\n\n" + "=" * 80)
    print("🧪 GraphRAG Engine 직접 테스트")
    print("=" * 80)
    
    try:
        from src.engine.graphrag_engine import PrivacyGraphRAGEngine
        
        engine = PrivacyGraphRAGEngine()
        
        test_query = "What companies are related to TSMC?"
        print(f"\n🔍 쿼리: {test_query}")
        print("⏳ 실행 중...\n")
        
        result = await engine.aquery(test_query, return_context=True)
        
        if isinstance(result, dict):
            answer = result.get("answer", "")
            sources = result.get("sources", [])
            backend = result.get("retrieval_backend", "unknown")
            
            print(f"\n📊 결과:")
            print(f"   답변 길이: {len(answer)} 문자")
            print(f"   출처 수: {len(sources)}개")
            print(f"   검색 백엔드: {backend}")
            
            print(f"\n   📝 답변:")
            print(f"      {answer}")
            
            if "Neo4j" in answer or "그래프" in answer:
                print(f"\n   ✅ Neo4j 그래프 데이터를 사용했습니다!")
            elif "TSMC" in answer or "Taiwan" in answer:
                print(f"\n   ✅ 관련 데이터를 반환했습니다!")
            else:
                print(f"\n   ⚠️  일반적인 답변만 제공되었습니다.")
                
        else:
            print(f"   답변: {result}")
        
    except Exception as e:
        print(f"❌ 실행 실패: {e}")
        import traceback
        traceback.print_exc()


async def test_neo4j_retrieval():
    """Neo4j Retriever 직접 테스트"""
    print("\n\n" + "=" * 80)
    print("🧪 Neo4j Retriever 직접 테스트")
    print("=" * 80)
    
    try:
        from src.engine.neo4j_retriever import Neo4jRetriever
        from src.db.neo4j_db import Neo4jDatabase
        from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
        
        db = Neo4jDatabase(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
        retriever = Neo4jRetriever(db)
        
        test_queries = [
            "TSMC",
            "supply chain",
            "Taiwan geopolitical risk"
        ]
        
        for query in test_queries:
            print(f"\n🔍 쿼리: '{query}'")
            
            results = await retriever.retrieve(query, top_k=5)
            
            if results:
                print(f"✅ {len(results)}개 결과 발견:")
                for i, result in enumerate(results, 1):
                    entity = result.get('entity', result.get('name', 'N/A'))
                    entity_type = result.get('type', result.get('label', 'N/A'))
                    print(f"   [{i}] {entity} ({entity_type})")
            else:
                print(f"❌ 결과 없음")
        
        db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("  🧪 실제 쿼리 테스트")
    print("  Neo4j 그래프 사용 여부 확인")
    print("=" * 80)
    
    # Test 1: Neo4j Retriever
    neo4j_works = await test_neo4j_retrieval()
    
    # Test 2: Direct Engine (if Neo4j works)
    if neo4j_works:
        await test_direct_engine()
    
    # Test 3: Streamlit simulation
    await test_streamlit_query()
    
    print("\n" + "=" * 80)
    print("📊 테스트 완료")
    print("=" * 80)
    
    if neo4j_works:
        print("""
✅ 결론: 시스템은 Neo4j 그래프를 사용할 수 있습니다!

다음 단계:
1. Streamlit UI 접속: http://localhost:8501
2. Query 탭에서 질문하기
3. Visualization 탭에서 그래프 확인

테스트 질문:
- "TSMC의 공급망 리스크는?"
- "Nvidia와 관련된 회사들은?"
- "Taiwan 지정학적 리스크는?"

답변이 구체적인 회사명과 관계를 포함하면 그래프를 사용한 것입니다!
        """)
    else:
        print("""
❌ 결론: Neo4j Retriever에 문제가 있습니다.

확인 사항:
1. Neo4j 실행 여부: docker ps | grep neo4j
2. 데이터 확인: python test_neo4j_direct.py
3. 스키마 확인: Neo4j Browser (http://localhost:7474)
        """)


if __name__ == "__main__":
    asyncio.run(main())
