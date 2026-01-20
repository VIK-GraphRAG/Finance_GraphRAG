#!/usr/bin/env python3
"""
멀티홉 추론 테스트
그래프를 따라 복잡한 추론이 가능한지 확인
"""

import requests
import json

print("=" * 80)
print("🧠 멀티홉 추론 테스트")
print("=" * 80)

# 서버 확인
try:
    health = requests.get("http://localhost:8000/health", timeout=5)
    print("\n✅ FastAPI 서버 실행 중")
except:
    print("\n❌ FastAPI 서버가 꺼져있습니다!")
    print("💡 서버 시작: uvicorn src.app:app --reload")
    exit(1)

# 멀티홉 추론 테스트 질문
test_cases = [
    {
        "name": "1-hop (단순 조회)",
        "question": "Nvidia의 매출은 얼마인가요?",
        "expected_hops": 1,
        "expected_entities": ["Nvidia"],
        "description": "단일 엔티티 정보 조회"
    },
    {
        "name": "2-hop (관계 추론)",
        "question": "Nvidia는 어느 회사에서 칩을 제조하나요?",
        "expected_hops": 2,
        "expected_entities": ["Nvidia", "TSMC"],
        "description": "Nvidia → MANUFACTURES_AT → TSMC"
    },
    {
        "name": "3-hop (복잡한 추론)",
        "question": "Nvidia의 주요 고객사는 누구이고, 그들이 사용하는 제품은 무엇인가요?",
        "expected_hops": 3,
        "expected_entities": ["Nvidia", "Customer", "Product"],
        "description": "Nvidia → SUPPLIES_TO → Customer → USES → Product"
    },
    {
        "name": "Multi-entity (여러 엔티티)",
        "question": "TSMC와 Samsung의 기술 경쟁 관계는 어떤가요?",
        "expected_hops": 2,
        "expected_entities": ["TSMC", "Samsung"],
        "description": "TSMC ← COMPETES_WITH → Samsung"
    },
    {
        "name": "Risk Analysis (리스크 분석)",
        "question": "반도체 공급망 차질이 Nvidia에 미치는 영향은?",
        "expected_hops": 3,
        "expected_entities": ["Supply Chain Risk", "TSMC", "Nvidia"],
        "description": "Risk → AFFECTS → TSMC → SUPPLIES → Nvidia"
    }
]

results = []

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*80}")
    print(f"테스트 {i}: {test['name']}")
    print(f"질문: {test['question']}")
    print(f"예상 홉: {test['expected_hops']}")
    print(f"설명: {test['description']}")
    print('='*80)
    
    try:
        response = requests.post(
            "http://localhost:8000/query",
            json={"question": test['question']},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "")
            sources = result.get("sources", [])
            
            # 출처 분석
            neo4j_sources = [s for s in sources if 'Perplexity' not in s.get('file', '')]
            web_sources = [s for s in sources if 'Perplexity' in s.get('file', '')]
            
            # 엔티티 추출 (간단한 텍스트 매칭)
            found_entities = []
            for entity in test['expected_entities']:
                if entity.lower() in answer.lower() or any(entity.lower() in s.get('excerpt', '').lower() for s in neo4j_sources):
                    found_entities.append(entity)
            
            # 인용 분석
            citations = []
            for i in range(1, 11):
                if f"[{i}]" in answer:
                    citations.append(i)
            
            # 평가
            uses_neo4j = len(neo4j_sources) > 0
            has_citations = len(citations) > 0
            entity_coverage = len(found_entities) / len(test['expected_entities']) if test['expected_entities'] else 0
            
            print(f"\n📊 결과:")
            print(f"   출처: {len(sources)}개 (Neo4j: {len(neo4j_sources)}, Web: {len(web_sources)})")
            print(f"   인용: {len(citations)}개 {citations}")
            print(f"   엔티티: {found_entities} ({entity_coverage*100:.0f}% 커버)")
            
            print(f"\n✅ 평가:")
            print(f"   {'✅' if uses_neo4j else '❌'} Neo4j 그래프 사용")
            print(f"   {'✅' if has_citations else '❌'} 인용 표시")
            print(f"   {'✅' if entity_coverage >= 0.5 else '❌'} 엔티티 커버리지 ({entity_coverage*100:.0f}%)")
            
            # 답변 미리보기
            print(f"\n📄 답변 미리보기:")
            print("-" * 80)
            preview = answer[:300]
            print(preview)
            if len(answer) > 300:
                print("...")
            print("-" * 80)
            
            # 점수 계산
            score = 0
            if uses_neo4j: score += 40
            if has_citations: score += 30
            if entity_coverage >= 0.5: score += 30
            
            print(f"\n⭐ 점수: {score}/100")
            
            results.append({
                "test": test['name'],
                "score": score,
                "uses_neo4j": uses_neo4j,
                "citations": len(citations),
                "entity_coverage": entity_coverage
            })
        
        else:
            print(f"❌ 에러: {response.status_code}")
            results.append({
                "test": test['name'],
                "score": 0,
                "error": response.status_code
            })
    
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        results.append({
            "test": test['name'],
            "score": 0,
            "error": str(e)
        })

# 최종 요약
print(f"\n{'='*80}")
print("📊 최종 요약")
print('='*80)

total_score = sum(r.get('score', 0) for r in results)
avg_score = total_score / len(results)

print(f"\n평균 점수: {avg_score:.1f}/100")
print(f"\n개별 점수:")
for r in results:
    score = r.get('score', 0)
    emoji = "✅" if score >= 70 else "⚠️" if score >= 40 else "❌"
    print(f"  {emoji} {r['test']}: {score}/100")

print(f"\n{'='*80}")
print("💡 결론")
print('='*80)

if avg_score >= 70:
    print("✅ 멀티홉 추론이 잘 작동하고 있습니다!")
elif avg_score >= 40:
    print("⚠️  부분적으로 작동하지만 개선이 필요합니다.")
else:
    print("❌ 멀티홉 추론이 제대로 작동하지 않습니다.")

print(f"""
권장 사항:
1. Neo4j 그래프 사용률: {sum(1 for r in results if r.get('uses_neo4j', False))}/{len(results)}
2. 인용 평균: {sum(r.get('citations', 0) for r in results)/len(results):.1f}개
3. 엔티티 커버리지: {sum(r.get('entity_coverage', 0) for r in results)/len(results)*100:.0f}%

다음 단계:
- Neo4j Retriever의 depth 파라미터 조정
- 관계 타입 확장 (MANUFACTURES_AT, SUPPLIES_TO 등)
- 엔티티 매칭 알고리즘 개선
""")
