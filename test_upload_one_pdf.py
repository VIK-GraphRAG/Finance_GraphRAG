#!/usr/bin/env python3
"""
단일 PDF 업로드 테스트 스크립트
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from db.neo4j_db import Neo4jDatabase
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, OPENAI_API_KEY, OPENAI_BASE_URL


async def test_upload_pdf():
    """단일 PDF 테스트"""
    print("=" * 70)
    print("🧪 단일 PDF 업로드 테스트")
    print("=" * 70)
    
    # 설정 확인
    if not NEO4J_URI or not NEO4J_PASSWORD:
        print("❌ Neo4j 설정이 없습니다.")
        return
    
    if not OPENAI_API_KEY:
        print("❌ OpenAI API 키가 없습니다.")
        return
    
    # Neo4j 연결
    db = Neo4jDatabase(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    print(f"✅ Neo4j 연결 성공: {NEO4J_URI}")
    
    # 가장 작은 PDF 선택 (industry_risk_factors.pdf)
    test_pdf = Path(__file__).parent / 'data' / 'baseline' / 'industry_risk_factors.pdf'
    
    if not test_pdf.exists():
        print(f"❌ 테스트 PDF를 찾을 수 없습니다: {test_pdf}")
        return
    
    print(f"\n📄 테스트 PDF: {test_pdf.name}")
    print(f"   크기: {test_pdf.stat().st_size / 1024:.1f} KB")
    
    # PDF 처리
    try:
        import pymupdf
        from openai import AsyncOpenAI
        from engine.integrator import DataIntegrator
        
        # 1. 텍스트 추출
        print("\n1️⃣ PDF 텍스트 추출 중...")
        doc = pymupdf.open(str(test_pdf))
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        print(f"   ✅ {len(text)} 문자 추출")
        
        # 2. OpenAI로 엔티티 추출 (1개 청크만)
        print("\n2️⃣ OpenAI GPT-4o-mini로 엔티티 추출 중...")
        client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        
        chunk = text[:3000]  # 첫 3000자만
        
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
        
        # JSON 파싱
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        extracted = json.loads(content)
        entities = extracted.get("entities", [])
        relationships = extracted.get("relationships", [])
        
        print(f"   ✅ {len(entities)} 엔티티, {len(relationships)} 관계 추출")
        
        # 추출된 엔티티 일부 출력
        print("\n   추출된 엔티티 샘플:")
        for ent in entities[:5]:
            print(f"     - {ent.get('name')} ({ent.get('type')})")
        
        # 3. Neo4j에 저장
        print("\n3️⃣ Neo4j에 저장 중...")
        integrator = DataIntegrator()
        graph_data = {
            "entities": entities,
            "relationships": relationships
        }
        
        merge_stats = integrator.ingestPdfGraph(
            graphData=graph_data,
            sourceFile=test_pdf.name,
            sourceLabel=test_pdf.stem
        )
        integrator.close()
        
        print(f"   ✅ Neo4j 저장 완료:")
        print(f"      - 병합된 엔티티: {merge_stats.get('entitiesMerged', 0)}")
        print(f"      - 생성된 관계: {merge_stats.get('relationshipsCreated', 0)}")
        
        # 4. 저장 확인
        print("\n4️⃣ 저장 확인 중...")
        verify_query = f"""
        MATCH (n)
        WHERE n.source_file = '{test_pdf.name}'
        RETURN count(n) as count
        """
        
        result = db.execute_query(verify_query)
        stored_count = result[0]['count'] if result else 0
        
        print(f"   ✅ Neo4j에 저장된 노드 수: {stored_count}")
        
        db.close()
        
        print("\n" + "=" * 70)
        print("✅ 테스트 성공! Neo4j에 데이터가 영구 저장되었습니다.")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        db.close()


if __name__ == "__main__":
    asyncio.run(test_upload_pdf())
