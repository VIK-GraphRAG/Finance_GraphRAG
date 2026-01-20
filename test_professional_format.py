#!/usr/bin/env python3
"""
Professional Markdown 형식 테스트
"""

import requests
import json
import time

print("=" * 80)
print("Professional Markdown 형식 테스트")
print("=" * 80)

# 서버 확인
try:
    health = requests.get("http://localhost:8000/health", timeout=5)
    print("\n✅ FastAPI 서버 실행 중")
except:
    print("\n❌ FastAPI 서버가 꺼져있습니다!")
    exit(1)

# 테스트 질문
test_questions = [
    "Nvidia의 매출은 얼마인가요?",
    "TSMC는 어떤 회사인가요?",
    "반도체 공급망 리스크는 무엇인가요?"
]

for i, question in enumerate(test_questions, 1):
    print(f"\n{'='*80}")
    print(f"테스트 {i}: {question}")
    print('='*80)
    
    try:
        response = requests.post(
            "http://localhost:8000/query",
            json={"question": question, "enable_web_search": False},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "")
            sources = result.get("sources", [])
            
            # 출처 분석
            neo4j_count = sum(1 for s in sources if s.get('type') == 'neo4j')
            web_count = sum(1 for s in sources if 'Perplexity' in s.get('file', ''))
            
            print(f"\n 출처: {len(sources)}개 (Neo4j: {neo4j_count}, Web: {web_count})")
            
            # 형식 체크
            has_summary = "## 핵심 인사이트" in answer or "## 🎯 핵심 인사이트" in answer
            has_diagram = "→" in answer
            has_analysis = "## 상세 분석" in answer
            has_agent_comment = "## 에이전트의 한 줄 평" in answer
            has_bold_numbers = "**" in answer
            has_inline_code = "`" in answer
            has_citations = "[1]" in answer or "[2]" in answer
            
            print(f"\n✅ 형식 체크:")
            print(f"   {'✅' if has_summary else '❌'} 핵심 인사이트 섹션")
            print(f"   {'✅' if has_diagram else '❌'} 인과관계 다이어그램 (→)")
            print(f"   {'✅' if has_analysis else '❌'} 상세 분석 섹션")
            print(f"   {'✅' if has_agent_comment else '❌'} 에이전트의 한 줄 평")
            print(f"   {'✅' if has_bold_numbers else '❌'} 굵은 수치 (**)")
            print(f"   {'✅' if has_inline_code else '❌'} Inline code (`)")
            print(f"   {'✅' if has_citations else '❌'} 인용 표시 ([1], [2])")
            print(f"   {'✅' if neo4j_count > 0 else '❌'} Neo4j 그래프 사용")
            
            # 점수 계산
            score = sum([
                has_summary, has_diagram, has_analysis, has_agent_comment,
                has_bold_numbers, has_inline_code, has_citations, neo4j_count > 0
            ])
            
            print(f"\n 점수: {score}/8")
            
            # 답변 미리보기
            print(f"\n 답변 미리보기:")
            print("-" * 80)
            lines = answer.split('\n')
            for line in lines[:15]:  # 처음 15줄만
                print(line)
            if len(lines) > 15:
                print("...")
            print("-" * 80)
            
            if score >= 6:
                print(" Professional Markdown 형식이 잘 적용되었습니다!")
            else:
                print(" 형식 개선이 필요합니다.")
        
        else:
            print(f"❌ 에러: {response.status_code}")
    
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
    
    time.sleep(2)  # 서버 부하 방지

print(f"\n{'='*80}")
print("💡 결론")
print('='*80)
print("""
기대하는 Professional Markdown 형식:
✅ 모든 수치는 **굵게**
✅ 핵심 용어는 `inline code`로
✅ 인과관계는 A → B → C 다이어그램
✅ 마지막에 **에이전트의 한 줄 평**
✅ 테이블은 Markdown Table 형식
✅ Neo4j 그래프 기반 답변

Streamlit UI에서 확인:
http://localhost:8501
""")
