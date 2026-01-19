#!/usr/bin/env python3
"""
모든 베이스라인 데이터를 Neo4j에 영구 저장하는 스크립트
Upload all baseline data to Neo4j (persistent storage)

Features:
- OpenAI API를 사용한 고품질 엔티티 추출
- Neo4j에 영구 저장 (세션 종료 후에도 유지)
- 그래프 시각화 지원
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from db.neo4j_db import Neo4jDatabase
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, OPENAI_API_KEY, OPENAI_BASE_URL

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


async def upload_pdf_file_with_openai(pdf_path: str, db: Neo4jDatabase):
    """
    OpenAI API를 사용하여 PDF를 처리하고 Neo4j에 영구 저장
    
    Args:
        pdf_path: PDF 파일 경로
        db: Neo4j 데이터베이스 인스턴스
        
    Returns:
        처리 결과 딕셔너리
    """
    print(f"\n📄 Processing PDF with OpenAI: {os.path.basename(pdf_path)}")
    
    try:
        import pymupdf
        from openai import AsyncOpenAI
        
        # 1. PDF에서 텍스트 추출
        doc = pymupdf.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        if not text or len(text.strip()) < 10:
            print(f"⚠️ PDF contains no extractable text")
            return None
        
        print(f"  ✅ Extracted {len(text)} characters from PDF")
        
        # 2. OpenAI로 엔티티 및 관계 추출
        client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        
        chunk_size = 3000  # 큰 청크로 처리 (OpenAI는 컨텍스트가 크므로)
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        
        # 최대 30개 청크만 처리 (비용 절감)
        max_chunks = 30
        if len(chunks) > max_chunks:
            print(f"  ⚠️ Limiting to first {max_chunks} chunks (out of {len(chunks)})")
            chunks = chunks[:max_chunks]
        
        all_entities = []
        all_relationships = []
        
        print(f"  🤖 Processing {len(chunks)} chunks with GPT-4o-mini...")
        
        for i, chunk in enumerate(chunks):
            if i > 0 and i % 5 == 0:
                print(f"    Progress: {i}/{len(chunks)} chunks ({i*100//len(chunks)}%)")
            
            prompt = f"""Extract business entities and relationships from this semiconductor/financial text.
Return ONLY valid JSON format:

{{
  "entities": [
    {{"name": "EntityName", "type": "COMPANY|PERSON|PRODUCT|TECHNOLOGY|FINANCIAL_METRIC|LOCATION|REGULATION|RISK", "properties": {{"key": "value"}}}}
  ],
  "relationships": [
    {{"source": "EntityA", "target": "EntityB", "type": "RELATIONSHIP_TYPE", "properties": {{"key": "value"}}}}
  ]
}}

Entity types: COMPANY, PERSON, PRODUCT, TECHNOLOGY, FINANCIAL_METRIC, LOCATION, REGULATION, RISK, MARKET, SUPPLY_CHAIN
Relationship types: SUPPLIES, PURCHASES, COMPETES_WITH, HAS_CEO, EMPLOYS, LOCATED_IN, PRODUCES, IMPACTS, DEPENDS_ON, REGULATES

Text:
{chunk[:3000]}

JSON output:"""
            
            try:
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a financial document analyzer. Extract structured entities and relationships. Respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000
                )
                
                content = response.choices[0].message.content.strip()
                
                # Parse JSON from response
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                extracted = json.loads(content)
                all_entities.extend(extracted.get("entities", []))
                all_relationships.extend(extracted.get("relationships", []))
                
            except Exception as e:
                print(f"    ⚠️ Chunk {i} extraction failed: {e}")
                continue
        
        print(f"  ✅ Extracted {len(all_entities)} entities, {len(all_relationships)} relationships")
        
        # 3. Neo4j에 저장
        from engine.integrator import DataIntegrator
        
        integrator = DataIntegrator()
        graph_data = {
            "entities": all_entities,
            "relationships": all_relationships
        }
        
        source_file = os.path.basename(pdf_path)
        source_label = Path(pdf_path).stem
        
        merge_stats = integrator.ingestPdfGraph(
            graphData=graph_data,
            sourceFile=source_file,
            sourceLabel=source_label
        )
        integrator.close()
        
        print(f"  ✅ Merged into Neo4j: {merge_stats.get('entitiesMerged', 0)} entities, {merge_stats.get('relationshipsCreated', 0)} relationships")
        
        return {
            'text_length': len(text),
            'entities_extracted': len(all_entities),
            'relationships_extracted': len(all_relationships),
            'merge_stats': merge_stats,
            'source_file': source_file
        }
    
    except Exception as e:
        print(f"  ❌ Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main_async():
    """메인 함수 (비동기)"""
    print("=" * 70)
    print("🚀 베이스라인 데이터 Neo4j 영구 저장 시작")
    print("=" * 70)
    
    # 설정 확인
    if not NEO4J_URI or not NEO4J_PASSWORD:
        print("❌ Neo4j 설정이 없습니다. .env 파일을 확인하세요.")
        sys.exit(1)
    
    if not OPENAI_API_KEY:
        print("❌ OpenAI API 키가 없습니다. .env 파일을 확인하세요.")
        sys.exit(1)
    
    # Neo4j 연결
    db = Neo4jDatabase(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    print(f"✅ Neo4j 연결 성공: {NEO4J_URI}")
    
    # 데이터 폴더
    data_dir = Path(__file__).parent / 'data' / 'baseline'
    
    if not data_dir.exists():
        print(f"❌ 데이터 폴더가 없습니다: {data_dir}")
        sys.exit(1)
    
    # 1. JSON 파일 업로드
    print("\n" + "=" * 70)
    print("📦 1단계: JSON 파일 업로드")
    print("=" * 70)
    
    json_files = list(data_dir.glob('*.json'))
    total_nodes = 0
    total_rels = 0
    
    for json_file in json_files:
        nodes, rels = upload_json_file(db, str(json_file))
        total_nodes += nodes
        total_rels += rels
    
    print(f"\n✅ JSON 업로드 완료: {total_nodes} nodes, {total_rels} relationships")
    
    # 2. PDF 파일 업로드 (OpenAI API 사용)
    print("\n" + "=" * 70)
    print("📄 2단계: PDF 파일 업로드 (OpenAI GPT-4o-mini 사용)")
    print("=" * 70)
    
    pdf_files = list(data_dir.glob('*.pdf'))
    
    if not pdf_files:
        print("⚠️ PDF 파일이 없습니다.")
    else:
        print(f"발견된 PDF 파일: {len(pdf_files)}개")
        for pdf in pdf_files:
            print(f"  - {pdf.name}")
        
        pdf_count = 0
        total_entities = 0
        total_relationships = 0
        
        for pdf_file in pdf_files:
            result = await upload_pdf_file_with_openai(str(pdf_file), db)
            if result:
                pdf_count += 1
                total_entities += result.get('entities_extracted', 0)
                total_relationships += result.get('relationships_extracted', 0)
        
        print(f"\n✅ PDF 업로드 완료:")
        print(f"  - 처리된 파일: {pdf_count}/{len(pdf_files)}")
        print(f"  - 추출된 엔티티: {total_entities}")
        print(f"  - 추출된 관계: {total_relationships}")
    
    # 3. 데이터베이스 통계
    print("\n" + "=" * 70)
    print("📊 3단계: Neo4j 데이터베이스 통계")
    print("=" * 70)
    
    # 노드 통계
    stats_query = """
    MATCH (n)
    RETURN labels(n)[0] as type, count(n) as count
    ORDER BY count DESC
    """
    
    stats = db.execute_query(stats_query)
    
    print("\n노드 타입별 개수:")
    total_node_count = 0
    for record in stats:
        count = record['count']
        total_node_count += count
        print(f"  - {record['type']}: {count:,}")
    print(f"  📊 총 노드 수: {total_node_count:,}")
    
    # 관계 통계
    rel_query = """
    MATCH ()-[r]->()
    RETURN type(r) as type, count(r) as count
    ORDER BY count DESC
    """
    
    rel_stats = db.execute_query(rel_query)
    
    print("\n관계 타입별 개수:")
    total_rel_count = 0
    for record in rel_stats:
        count = record['count']
        total_rel_count += count
        print(f"  - {record['type']}: {count:,}")
    print(f"  🔗 총 관계 수: {total_rel_count:,}")
    
    # 데이터 소스별 통계
    source_query = """
    MATCH (n)
    WHERE n.source_file IS NOT NULL
    RETURN n.source_file as source, count(n) as count
    ORDER BY count DESC
    LIMIT 10
    """
    
    source_stats = db.execute_query(source_query)
    
    if source_stats:
        print("\n소스 파일별 노드 개수 (Top 10):")
        for record in source_stats:
            print(f"  - {record['source']}: {record['count']:,}")
    
    db.close()
    
    print("\n" + "=" * 70)
    print("✅ 모든 데이터 Neo4j 영구 저장 완료!")
    print("   세션 종료 후에도 데이터가 유지됩니다.")
    print("   Streamlit UI의 Visualization 탭에서 그래프를 확인하세요.")
    print("=" * 70)


def main():
    """동기 래퍼 함수"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
