#!/usr/bin/env python3
"""
Risk Factor 상세 확인
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from src.db.neo4j_db import Neo4jDatabase
from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD


def main():
    print("=" * 80)
    print("⚠️  Risk Factor 상세 확인")
    print("=" * 80)
    
    db = Neo4jDatabase(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    
    # Risk 노드 조회
    query = """
    MATCH (r:Risk)
    RETURN r.name as name, 
           r.impact_level as impact, 
           r.description as description,
           r.source_file as source
    ORDER BY r.name
    """
    
    results = db.execute_query(query)
    
    if not results:
        print("\n❌ Risk 노드가 없습니다!")
        db.close()
        return
    
    print(f"\n📊 총 {len(results)}개 Risk Factor 발견\n")
    
    # 속성 분석
    complete_risks = []
    incomplete_risks = []
    
    for r in results:
        name = r.get('name', 'N/A')
        impact = r.get('impact', None)
        description = r.get('description', None)
        
        if impact and description:
            complete_risks.append(r)
        else:
            incomplete_risks.append(r)
    
    print(f"✅ 완전한 Risk: {len(complete_risks)}개")
    print(f"⚠️  불완전한 Risk: {len(incomplete_risks)}개\n")
    
    # 완전한 Risk 샘플
    if complete_risks:
        print("=" * 80)
        print("✅ 완전한 Risk Factor 샘플 (처음 5개)")
        print("=" * 80)
        for i, r in enumerate(complete_risks[:5], 1):
            print(f"\n{i}. {r['name']}")
            print(f"   Impact: {r['impact']}")
            print(f"   Description: {r['description'][:100]}..." if len(r.get('description', '')) > 100 else f"   Description: {r['description']}")
    
    # 불완전한 Risk 샘플
    if incomplete_risks:
        print("\n" + "=" * 80)
        print("⚠️  불완전한 Risk Factor (처음 10개)")
        print("=" * 80)
        for i, r in enumerate(incomplete_risks[:10], 1):
            print(f"\n{i}. {r['name']}")
            print(f"   Impact: {r['impact'] or 'None'}")
            print(f"   Description: {r['description'][:50] if r['description'] else 'None'}...")
    
    db.close()
    
    print("\n" + "=" * 80)
    print("💡 해결 방법")
    print("=" * 80)
    
    if len(incomplete_risks) > len(results) * 0.3:  # 30% 이상 불완전
        print("""
⚠️  Risk Factor의 속성 정보가 부족합니다!

해결 방법:
1. Risk Factor 보강 스크립트 실행:
   python scripts/utils/enrich_risk_factors.py

2. 또는 일반적인 Risk 추가:
   python scripts/utils/enrich_risk_factors.py --add

3. 확인:
   python check_risk_factors.py
        """)
    else:
        print("""
✅ 대부분의 Risk Factor가 완전합니다!

Streamlit UI에서 확인:
http://localhost:8501
→ Visualization 탭 → Risk Factors
        """)


if __name__ == "__main__":
    main()
