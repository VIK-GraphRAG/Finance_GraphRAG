#!/usr/bin/env python3
"""
Neo4j 직접 연결 테스트
"""

import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")


def main():
    print("=" * 70)
    print("🔍 Neo4j 직접 연결 테스트")
    print("=" * 70)
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # 1. 전체 노드 수
        result = session.run("MATCH (n) RETURN count(n) as count")
        count = result.single()['count']
        print(f"\n📊 전체 노드 수: {count}")
        
        # 2. 전체 관계 수
        result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
        rel_count = result.single()['count']
        print(f"🔗 전체 관계 수: {rel_count}")
        
        # 3. 모든 label 목록
        result = session.run("CALL db.labels()")
        labels = [record['label'] for record in result]
        print(f"\n📋 Labels: {labels}")
        
        # 4. 각 label별 노드 수
        if labels:
            print(f"\n📈 Label별 노드 수:")
            for label in labels:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                count = result.single()['count']
                print(f"   - {label}: {count}")
        
        # 5. 샘플 노드 (처음 5개)
        print(f"\n🔍 샘플 노드 (처음 5개):")
        result = session.run("MATCH (n) RETURN n LIMIT 5")
        for record in result:
            node = record['n']
            labels_str = ":".join(node.labels)
            name = node.get('name', 'N/A')
            print(f"   - ({labels_str}) name={name}")
        
        # 6. 샘플 관계 (처음 5개)
        print(f"\n🔗 샘플 관계 (처음 5개):")
        result = session.run("""
            MATCH (a)-[r]->(b)
            RETURN a.name as source, type(r) as rel, b.name as target
            LIMIT 5
        """)
        for record in result:
            print(f"   - {record['source']} --[{record['rel']}]--> {record['target']}")
    
    driver.close()
    print(f"\n{'='*70}")


if __name__ == "__main__":
    main()
