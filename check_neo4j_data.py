#!/usr/bin/env python3
"""
Neo4j 데이터베이스 상태 확인
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from db.neo4j_db import Neo4jDatabase
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD


def main():
    """Neo4j 데이터베이스 통계 확인"""
    print("=" * 70)
    print("📊 Neo4j 데이터베이스 현황")
    print("=" * 70)
    
    # 연결
    db = Neo4jDatabase(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    print(f"✅ Neo4j 연결 성공: {NEO4J_URI}\n")
    
    # 노드 타입별 통계
    print("📈 노드 타입별 개수:")
    node_stats = db.execute_query("""
        MATCH (n)
        RETURN labels(n)[0] as type, count(n) as count
        ORDER BY count DESC
    """)
    
    total_nodes = 0
    if node_stats:
        for record in node_stats:
            count = record['count']
            total_nodes += count
            print(f"   - {record['type']}: {count:,}")
    else:
        print("   (노드 없음)")
    
    print(f"\n   📊 총 노드 수: {total_nodes:,}")
    
    # 관계 타입별 통계
    print(f"\n🔗 관계 타입별 개수:")
    rel_stats = db.execute_query("""
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        ORDER BY count DESC
    """)
    
    total_rels = 0
    if rel_stats:
        for record in rel_stats:
            count = record['count']
            total_rels += count
            print(f"   - {record['type']}: {count:,}")
    else:
        print("   (관계 없음)")
    
    print(f"\n   🔗 총 관계 수: {total_rels:,}")
    
    # 소스 파일별 통계
    print(f"\n📄 소스 파일별 노드 개수:")
    source_stats = db.execute_query("""
        MATCH (n)
        WHERE n.source_file IS NOT NULL
        RETURN n.source_file as source, count(n) as count
        ORDER BY count DESC
    """)
    
    if source_stats:
        for record in source_stats:
            print(f"   - {record['source']}: {record['count']:,} nodes")
    else:
        print("   (소스 파일 정보 없음)")
    
    # 샘플 데이터 (Company 노드)
    print(f"\n🏢 샘플 Company 노드 (처음 10개):")
    companies = db.execute_query("""
        MATCH (c:Company)
        RETURN c.name as name, labels(c) as labels
        LIMIT 10
    """)
    
    if companies:
        for record in companies:
            labels_str = ", ".join(record['labels'])
            print(f"   - {record['name']} ({labels_str})")
    else:
        print("   (Company 노드 없음)")
    
    # 샘플 데이터 (Technology 노드)
    print(f"\n💻 샘플 Technology 노드 (처음 10개):")
    techs = db.execute_query("""
        MATCH (t:Technology)
        RETURN t.name as name
        LIMIT 10
    """)
    
    if techs:
        for record in techs:
            print(f"   - {record['name']}")
    else:
        print("   (Technology 노드 없음)")
    
    # 샘플 데이터 (Risk 노드)
    print(f"\n⚠️  샘플 Risk 노드 (처음 10개):")
    risks = db.execute_query("""
        MATCH (r:Risk)
        RETURN r.name as name
        LIMIT 10
    """)
    
    if risks:
        for record in risks:
            print(f"   - {record['name']}")
    else:
        print("   (Risk 노드 없음)")
    
    db.close()
    
    print("\n" + "=" * 70)
    print("✅ 데이터베이스 확인 완료!")
    print("💡 세션을 종료해도 이 데이터는 Neo4j에 영구 저장됩니다.")
    print("=" * 70)


if __name__ == "__main__":
    main()
