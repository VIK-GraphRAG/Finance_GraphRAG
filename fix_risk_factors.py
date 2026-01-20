#!/usr/bin/env python3
"""
Risk Factor 속성 직접 보강
Neo4j driver를 직접 사용
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")


# Risk Factor 보강 데이터
RISK_ENRICHMENT = {
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
    "US-China Technology Decoupling": {
        "impact_level": "high",
        "description": "US export controls on advanced chips and semiconductor equipment to China"
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
    "Cybersecurity": {
        "impact_level": "medium",
        "description": "Cyber attacks targeting semiconductor IP and manufacturing facilities"
    },
    "Semiconductor Expertise Shortage": {
        "impact_level": "medium",
        "description": "Shortage of skilled semiconductor engineers and researchers"
    },
    "IP Theft": {
        "impact_level": "high",
        "description": "Intellectual property theft risks in semiconductor industry"
    },
}


def main():
    print("=" * 80)
    print("🔧 Risk Factor 속성 보강")
    print("=" * 80)
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # 1. 기존 Risk 노드 확인
        result = session.run("MATCH (r:Risk) RETURN count(r) as count")
        risk_count = result.single()['count']
        print(f"\n📊 기존 Risk 노드: {risk_count}개")
        
        if risk_count == 0:
            print("❌ Risk 노드가 없습니다!")
            driver.close()
            return
        
        # 2. 속성이 없는 Risk 찾기
        result = session.run("""
            MATCH (r:Risk)
            WHERE r.impact_level IS NULL OR r.description IS NULL
            RETURN r.name as name
        """)
        
        incomplete_risks = [record['name'] for record in result]
        print(f"⚠️  보강 필요: {len(incomplete_risks)}개\n")
        
        if not incomplete_risks:
            print("✅ 모든 Risk Factor가 이미 완전합니다!")
            driver.close()
            return
        
        # 3. Risk 노드 보강
        print("🔧 Risk 노드 보강 중...")
        updated_count = 0
        
        for risk_name in incomplete_risks:
            # 이름에서 키워드 찾기
            enrichment = None
            for key, data in RISK_ENRICHMENT.items():
                if key.lower() in risk_name.lower() or risk_name.lower() in key.lower():
                    enrichment = data
                    break
            
            # 기본값 설정
            if not enrichment:
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
            
            result = session.run(query, {
                'name': risk_name,
                'impact_level': enrichment['impact_level'],
                'description': enrichment['description']
            })
            
            if result.single():
                updated_count += 1
                print(f"   ✅ {risk_name}: {enrichment['impact_level']}")
    
    driver.close()
    
    print(f"\n{'='*80}")
    print(f"✅ 완료: {updated_count}개 Risk Factor 보강")
    print(f"{'='*80}")
    
    # 결과 확인
    print("\n📊 보강 후 확인...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    with driver.session() as session:
        result = session.run("""
            MATCH (r:Risk)
            RETURN r.name as name, r.impact_level as impact, r.description as description
            ORDER BY r.impact_level DESC, r.name
            LIMIT 10
        """)
        
        print("\n✅ 보강된 Risk Factor 샘플 (처음 10개):")
        for i, record in enumerate(result, 1):
            print(f"\n{i}. {record['name']}")
            print(f"   Impact: {record['impact']}")
            desc = record['description']
            print(f"   Description: {desc[:80]}..." if len(desc) > 80 else f"   Description: {desc}")
    
    driver.close()
    
    print("\n" + "=" * 80)
    print("💡 Streamlit UI에서 확인하세요:")
    print("   http://localhost:8501")
    print("   → Visualization 탭 → Risk Factors")
    print("=" * 80)


if __name__ == "__main__":
    main()
