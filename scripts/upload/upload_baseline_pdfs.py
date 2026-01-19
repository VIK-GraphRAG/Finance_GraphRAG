#!/usr/bin/env python3
"""
Baseline PDF 파일들을 Neo4j에 영구 저장
- 세션 종료 후에도 데이터 유지
- 진행 상황 실시간 표시
- 에러 발생 시에도 계속 진행
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from db.neo4j_db import Neo4jDatabase
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, OPENAI_API_KEY, OPENAI_BASE_URL


async def process_pdf_to_neo4j(pdf_path: Path, db: Neo4jDatabase):
    """
    단일 PDF를 처리하여 Neo4j에 저장
    """
    print(f"\n{'='*70}")
    print(f"📄 {pdf_path.name}")
    print(f"{'='*70}")
    
    try:
        import pymupdf
        from openai import AsyncOpenAI
        from engine.integrator import DataIntegrator
        
        # 파일 크기 확인
        file_size_kb = pdf_path.stat().st_size / 1024
        print(f"   📊 파일 크기: {file_size_kb:.1f} KB")
        
        # 1. 텍스트 추출 (타임아웃 적용)
        print(f"   ⏳ 텍스트 추출 중...")
        
        try:
            doc = pymupdf.open(str(pdf_path))
            text = ""
            page_count = len(doc)
            
            # 페이지 수가 너무 많으면 제한
            max_pages = 200
            if page_count > max_pages:
                print(f"      ⚠️ 페이지 수 제한: {page_count} → {max_pages}")
                page_count = max_pages
            
            for page_num in range(min(page_count, len(doc))):
                try:
                    page = doc[page_num]
                    text += page.get_text()
                    if (page_num + 1) % 50 == 0:
                        print(f"      Progress: {page_num + 1}/{page_count} pages")
                except Exception as page_error:
                    print(f"      ⚠️ Page {page_num + 1} 에러, 스킵: {str(page_error)[:50]}")
                    continue
            
            doc.close()
            
        except Exception as extraction_error:
            print(f"   ❌ 텍스트 추출 실패: {str(extraction_error)[:100]}")
            return None
        
        if not text or len(text.strip()) < 10:
            print(f"   ⚠️ 텍스트가 없습니다. 스킵합니다.")
            return None
        
        print(f"   ✅ {len(text):,} 문자 추출 ({page_count} 페이지)")
        
        # 2. 청크 분할
        chunk_size = 3000
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        
        # 대용량 PDF는 청크 수 제한 (비용 절감)
        max_chunks = 50
        if len(chunks) > max_chunks:
            print(f"   ⚠️ 청크 수 제한: {len(chunks)} → {max_chunks} (비용 절감)")
            chunks = chunks[:max_chunks]
        
        print(f"   📦 {len(chunks)}개 청크로 분할")
        
        # 3. OpenAI로 엔티티 추출
        print(f"   🤖 GPT-4o-mini로 엔티티 추출 중...")
        client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        
        all_entities = []
        all_relationships = []
        
        for i, chunk in enumerate(chunks, 1):
            if i % 10 == 0 or i == 1:
                print(f"      Progress: {i}/{len(chunks)} chunks ({i*100//len(chunks)}%)")
            
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
{chunk}

JSON output:"""
            
            try:
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a financial document analyzer. Extract structured entities and relationships. Respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000,
                    timeout=30
                )
                
                content = response.choices[0].message.content.strip()
                
                # JSON 파싱
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
                print(f"      ⚠️ Chunk {i} 실패: {str(e)[:50]}")
                continue
        
        print(f"   ✅ 총 {len(all_entities)} 엔티티, {len(all_relationships)} 관계 추출")
        
        # 엔티티 샘플 출력
        if all_entities:
            print(f"   📋 추출된 엔티티 샘플 (처음 5개):")
            for ent in all_entities[:5]:
                print(f"      - {ent.get('name')} ({ent.get('type')})")
        
        # 4. Neo4j에 저장
        print(f"   💾 Neo4j에 저장 중...")
        integrator = DataIntegrator()
        graph_data = {
            "entities": all_entities,
            "relationships": all_relationships
        }
        
        merge_stats = integrator.ingestPdfGraph(
            graphData=graph_data,
            sourceFile=pdf_path.name,
            sourceLabel=pdf_path.stem
        )
        integrator.close()
        
        print(f"   ✅ Neo4j 저장 완료:")
        print(f"      - 병합된 엔티티: {merge_stats.get('entitiesMerged', 0):,}")
        print(f"      - 생성된 관계: {merge_stats.get('relationshipsCreated', 0):,}")
        
        return {
            'file': pdf_path.name,
            'text_length': len(text),
            'entities': len(all_entities),
            'relationships': len(all_relationships),
            'merged': merge_stats
        }
        
    except Exception as e:
        print(f"   ❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """메인 함수"""
    start_time = datetime.now()
    
    print("=" * 70)
    print("🚀 Baseline PDF 파일들을 Neo4j에 영구 저장")
    print("=" * 70)
    print(f"시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
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
    
    # PDF 파일 목록 (크기 순으로 정렬 - 작은 것부터)
    data_dir = Path(__file__).parent / 'data' / 'baseline'
    pdf_files = sorted(data_dir.glob('*.pdf'), key=lambda p: p.stat().st_size)
    
    if not pdf_files:
        print("❌ PDF 파일이 없습니다.")
        sys.exit(1)
    
    print(f"\n📚 발견된 PDF 파일: {len(pdf_files)}개")
    for i, pdf in enumerate(pdf_files, 1):
        size_kb = pdf.stat().st_size / 1024
        print(f"   {i}. {pdf.name} ({size_kb:.1f} KB)")
    
    # 각 PDF 처리
    results = []
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n\n{'='*70}")
        print(f"진행 상황: {i}/{len(pdf_files)} ({i*100//len(pdf_files)}%)")
        print(f"{'='*70}")
        
        result = await process_pdf_to_neo4j(pdf_file, db)
        if result:
            results.append(result)
    
    # 최종 통계
    print(f"\n\n{'='*70}")
    print("📊 최종 통계")
    print(f"{'='*70}")
    
    # 처리된 파일 통계
    print(f"\n✅ 처리 완료: {len(results)}/{len(pdf_files)} 파일")
    
    total_entities = sum(r['entities'] for r in results)
    total_relationships = sum(r['relationships'] for r in results)
    
    print(f"   - 총 추출된 엔티티: {total_entities:,}")
    print(f"   - 총 추출된 관계: {total_relationships:,}")
    
    # Neo4j 데이터베이스 통계
    print(f"\n📈 Neo4j 데이터베이스 통계:")
    
    # 노드 타입별
    node_stats = db.execute_query("""
        MATCH (n)
        RETURN labels(n)[0] as type, count(n) as count
        ORDER BY count DESC
        LIMIT 10
    """)
    
    print(f"\n   노드 타입 (Top 10):")
    total_nodes = 0
    for record in node_stats:
        count = record['count']
        total_nodes += count
        print(f"   - {record['type']}: {count:,}")
    
    # 관계 타입별
    rel_stats = db.execute_query("""
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        ORDER BY count DESC
        LIMIT 10
    """)
    
    print(f"\n   관계 타입 (Top 10):")
    total_rels = 0
    for record in rel_stats:
        count = record['count']
        total_rels += count
        print(f"   - {record['type']}: {count:,}")
    
    print(f"\n   📊 총 노드 수: {total_nodes:,}")
    print(f"   🔗 총 관계 수: {total_rels:,}")
    
    db.close()
    
    # 소요 시간
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{'='*70}")
    print("✅ 모든 PDF 파일이 Neo4j에 영구 저장되었습니다!")
    print(f"{'='*70}")
    print(f"종료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"소요 시간: {duration}")
    print(f"\n💡 세션을 종료해도 데이터가 Neo4j에 유지됩니다.")
    print(f"💡 Streamlit UI의 Visualization 탭에서 그래프를 확인하세요.")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
