#!/usr/bin/env python3
"""
모든 베이스라인 데이터를 Neo4j에 업로드하는 스크립트
Upload all baseline data to Neo4j
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from db.neo4j_db import Neo4jDatabase
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

def upload_json_file(db: Neo4jDatabase, json_path: str):
    """JSON 파일을 Neo4j에 업로드"""
    print(f"\n📦 Processing: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # supply_chain_mapping.json 처리
    if 'supply_chain' in data:
        supply_chain = data['supply_chain']
        tiers = supply_chain.get('tiers', [])
        
        nodes_created = 0
        relationships_created = 0
        
        for tier in tiers:
            tier_num = tier.get('tier')
            tier_name = tier.get('name')
            
            for company in tier.get('companies', []):
                company_name = company.get('name')
                
                # Company 노드 생성
                query = """
                MERGE (c:Company {name: $name})
                SET c.tier = $tier,
                    c.tier_name = $tier_name,
                    c.role = $role,
                    c.criticality = $criticality,
                    c.location = $location
                RETURN c
                """
                
                db.execute_query(query, {
                    'name': company_name,
                    'tier': tier_num,
                    'tier_name': tier_name,
                    'role': company.get('role', ''),
                    'criticality': company.get('criticality', 'medium'),
                    'location': company.get('location', '')
                })
                nodes_created += 1
                
                # Dependencies (관계) 생성
                for dep in company.get('dependencies', []):
                    dep_query = """
                    MATCH (c1:Company {name: $company})
                    MERGE (c2:Company {name: $dependency})
                    MERGE (c1)-[r:DEPENDS_ON]->(c2)
                    RETURN r
                    """
                    
                    db.execute_query(dep_query, {
                        'company': company_name,
                        'dependency': dep
                    })
                    relationships_created += 1
        
        print(f"✅ Created {nodes_created} nodes and {relationships_created} relationships")
        return nodes_created, relationships_created
    
    return 0, 0


def upload_pdf_file(pdf_path: str):
    """PDF 파일을 로컬 모델로 처리"""
    print(f"\n📄 Processing PDF: {pdf_path}")
    
    try:
        from engine.local_worker import LocalWorker
        
        worker = LocalWorker(enforce_security=True)
        result = worker.process_pdf(
            pdf_path=pdf_path,
            extract_entities=True,
            tag_sensitive=True
        )
        
        print(f"✅ Extracted {result.get('entity_count', 0)} entities")
        print(f"✅ Found {result.get('sensitive_count', 0)} sensitive items")
        
        return result
    
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        return None


def main():
    """메인 함수"""
    print("=" * 70)
    print("🚀 베이스라인 데이터 업로드 시작")
    print("=" * 70)
    
    # Neo4j 연결
    if not NEO4J_URI or not NEO4J_PASSWORD:
        print("❌ Neo4j 설정이 없습니다. .env 파일을 확인하세요.")
        sys.exit(1)
    
    db = Neo4jDatabase(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    print(f"✅ Neo4j 연결 성공: {NEO4J_URI}")
    
    # 데이터 폴더
    data_dir = Path(__file__).parent / 'data' / 'baseline'
    
    # 1. JSON 파일 업로드
    print("\n" + "=" * 70)
    print("📦 JSON 파일 업로드")
    print("=" * 70)
    
    json_files = list(data_dir.glob('*.json'))
    total_nodes = 0
    total_rels = 0
    
    for json_file in json_files:
        nodes, rels = upload_json_file(db, str(json_file))
        total_nodes += nodes
        total_rels += rels
    
    print(f"\n✅ JSON 업로드 완료: {total_nodes} nodes, {total_rels} relationships")
    
    # 2. PDF 파일 업로드
    print("\n" + "=" * 70)
    print("📄 PDF 파일 업로드 (로컬 모델 사용)")
    print("=" * 70)
    
    pdf_files = list(data_dir.glob('*.pdf'))
    pdf_count = 0
    
    for pdf_file in pdf_files:
        result = upload_pdf_file(str(pdf_file))
        if result:
            pdf_count += 1
    
    print(f"\n✅ PDF 업로드 완료: {pdf_count} files processed")
    
    # 3. 데이터베이스 통계
    print("\n" + "=" * 70)
    print("📊 데이터베이스 통계")
    print("=" * 70)
    
    stats_query = """
    MATCH (n)
    RETURN labels(n)[0] as type, count(n) as count
    ORDER BY count DESC
    """
    
    stats = db.execute_query(stats_query)
    
    print("\n노드 타입별 개수:")
    for record in stats:
        print(f"  - {record['type']}: {record['count']}")
    
    # 관계 통계
    rel_query = """
    MATCH ()-[r]->()
    RETURN type(r) as type, count(r) as count
    ORDER BY count DESC
    """
    
    rel_stats = db.execute_query(rel_query)
    
    print("\n관계 타입별 개수:")
    for record in rel_stats:
        print(f"  - {record['type']}: {record['count']}")
    
    db.close()
    
    print("\n" + "=" * 70)
    print("✅ 모든 데이터 업로드 완료!")
    print("=" * 70)


if __name__ == "__main__":
    main()
