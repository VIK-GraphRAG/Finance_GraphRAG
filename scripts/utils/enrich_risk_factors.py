#!/usr/bin/env python3
"""
Risk Factor 데이터 보강 스크립트
기존 Risk 노드에 impact_level과 description 추가
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.db.neo4j_db import Neo4jDatabase
from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD


# Risk Factor 샘플 데이터 (일반적인 반도체 산업 리스크)
RISK_ENRICHMENT_DATA = {
    "Supply Chain Disruption": {
        "impact_level": "high",
        "description": "Disruptions in semiconductor supply chain affecting production and delivery"
    },
    "Geopolitical Tensions": {
        "impact_level": "high", 
        "description": "Trade restrictions and political conflicts impacting global semiconductor trade"
    },
    "Taiwan Strait": {
        "impact_level": "high",
        "description": "Geopolitical risk from Taiwan Strait tensions affecting TSMC and regional stability"
    },
    "China Export Controls": {
        "impact_level": "high",
        "description": "US export controls on advanced chips and equipment to China"
    },
    "Earthquake": {
        "impact_level": "medium",
        "description": "Natural disaster risk affecting semiconductor fabs in earthquake-prone regions"
    },
    "Chip Shortage": {
        "impact_level": "high",
        "description": "Global semiconductor shortage impacting automotive and electronics industries"
    },
    "Technology Obsolescence": {
        "impact_level": "medium",
        "description": "Risk of current technology becoming outdated due to rapid innovation"
    },
    "Cybersecurity Threats": {
        "impact_level": "medium",
        "description": "Cyber attacks targeting semiconductor IP and manufacturing facilities"
    },
    "Talent Shortage": {
        "impact_level": "medium",
        "description": "Shortage of skilled semiconductor engineers and researchers"
    },
    "Equipment Dependency": {
        "impact_level": "high",
        "description": "Heavy dependency on limited suppliers (e.g., ASML for EUV equipment)"
    },
}


def enrich_risks():
    """Risk Factor 노드에 속성 추가"""
    print("=" * 70)
    print("🔧 Risk Factor 데이터 보강")
    print("=" * 70)
    
    db = Neo4jDatabase(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    print(f"✅ Neo4j 연결 성공: {NEO4J_URI}\n")
    
    # 1. 기존 Risk 노드 확인
    print("📊 기존 Risk 노드 확인...")
    existing_risks = db.execute_query("""
        MATCH (r:Risk)
        RETURN r.name as name, r.impact_level as impact, r.description as description
    """)
    
    if not existing_risks:
        print("⚠️ Risk 노드가 없습니다. 먼저 seed 스크립트를 실행하세요:")
        print("   python scripts/seed/seed_semiconductor.py")
        db.close()
        return
    
    print(f"   발견: {len(existing_risks)}개 Risk 노드")
    
    # 2. 속성이 없는 Risk 찾기
    incomplete_risks = [r for r in existing_risks if not r['impact'] or not r['description']]
    print(f"   보강 필요: {len(incomplete_risks)}개\n")
    
    if not incomplete_risks:
        print("✅ 모든 Risk Factor가 이미 완전합니다!")
        db.close()
        return
    
    # 3. Risk 노드 보강
    print("🔧 Risk 노드 보강 중...")
    updated_count = 0
    
    for risk in incomplete_risks:
        risk_name = risk['name']
        
        # 이름에서 키워드 찾기
        enrichment = None
        for key, data in RISK_ENRICHMENT_DATA.items():
            if key.lower() in risk_name.lower() or risk_name.lower() in key.lower():
                enrichment = data
                break
        
        # 기본값 설정
        if not enrichment:
            # 일반적인 기본값
            enrichment = {
                "impact_level": "medium",
                "description": f"Risk factor: {risk_name}"
            }
        
        # 업데이트 쿼리
        query = """
        MATCH (r:Risk {name: $name})
        SET r.impact_level = $impact_level,
            r.description = $description,
            r.enriched = true,
            r.enriched_at = datetime()
        RETURN r.name as name
        """
        
        result = db.execute_query(query, {
            'name': risk_name,
            'impact_level': enrichment['impact_level'],
            'description': enrichment['description']
        })
        
        if result:
            updated_count += 1
            print(f"   ✅ {risk_name}: {enrichment['impact_level']}")
    
    db.close()
    
    print(f"\n{'='*70}")
    print(f"✅ 완료: {updated_count}개 Risk Factor 보강")
    print(f"{'='*70}")
    print("\n💡 Streamlit UI (http://localhost:8501)에서 확인하세요:")
    print("   Visualization 탭 → Risk Factors")


def add_common_risks():
    """일반적인 Risk Factor 추가"""
    print("\n" + "=" * 70)
    print("➕ 일반적인 Risk Factor 추가")
    print("=" * 70)
    
    db = Neo4jDatabase(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    
    added_count = 0
    
    for risk_name, data in RISK_ENRICHMENT_DATA.items():
        query = """
        MERGE (r:Risk {name: $name})
        ON CREATE SET 
            r.impact_level = $impact_level,
            r.description = $description,
            r.created_at = datetime(),
            r.source = 'enrichment_script'
        ON MATCH SET
            r.impact_level = COALESCE(r.impact_level, $impact_level),
            r.description = COALESCE(r.description, $description)
        RETURN r.name as name
        """
        
        result = db.execute_query(query, {
            'name': risk_name,
            'impact_level': data['impact_level'],
            'description': data['description']
        })
        
        if result:
            added_count += 1
            print(f"   ✅ {risk_name}")
    
    db.close()
    
    print(f"\n✅ 추가/업데이트: {added_count}개 Risk Factor")


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Risk Factor 데이터 보강')
    parser.add_argument('--add', action='store_true', help='일반적인 Risk Factor 추가')
    args = parser.parse_args()
    
    if args.add:
        add_common_risks()
    else:
        enrich_risks()


if __name__ == "__main__":
    main()
