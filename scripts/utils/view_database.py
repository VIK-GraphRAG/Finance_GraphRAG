#!/usr/bin/env python3
"""
Neo4j 데이터베이스 내용 확인 스크립트
View Neo4j database contents
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from db.neo4j_db import Neo4jDatabase
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD


def view_database_stats(db: Neo4jDatabase):
    """데이터베이스 통계 보기"""
    print("\n" + "=" * 70)
    print("📊 데이터베이스 통계")
    print("=" * 70)
    
    # 전체 노드 수
    total_query = "MATCH (n) RETURN count(n) as total"
    total = db.execute_query(total_query)[0]['total']
    print(f"\n전체 노드 수: {total}")
    
    # 노드 타입별 개수
    stats_query = """
    MATCH (n)
    RETURN labels(n)[0] as type, count(n) as count
    ORDER BY count DESC
    """
    
    stats = db.execute_query(stats_query)
    
    print("\n노드 타입별 개수:")
    for record in stats:
        print(f"  - {record['type']}: {record['count']}")
    
    # 전체 관계 수
    rel_total_query = "MATCH ()-[r]->() RETURN count(r) as total"
    rel_total = db.execute_query(rel_total_query)[0]['total']
    print(f"\n전체 관계 수: {rel_total}")
    
    # 관계 타입별 개수
    rel_query = """
    MATCH ()-[r]->()
    RETURN type(r) as type, count(r) as count
    ORDER BY count DESC
    """
    
    rel_stats = db.execute_query(rel_query)
    
    print("\n관계 타입별 개수:")
    for record in rel_stats:
        print(f"  - {record['type']}: {record['count']}")


def view_sample_companies(db: Neo4jDatabase, limit: int = 10):
    """샘플 회사 데이터 보기"""
    print("\n" + "=" * 70)
    print(f"🏢 샘플 회사 데이터 (최대 {limit}개)")
    print("=" * 70)
    
    query = f"""
    MATCH (c:Company)
    RETURN c.name as name, 
           c.tier as tier, 
           c.role as role, 
           c.criticality as criticality,
           c.location as location
    ORDER BY c.tier, c.name
    LIMIT {limit}
    """
    
    companies = db.execute_query(query)
    
    if not companies:
        print("\n⚠️  회사 데이터가 없습니다.")
        return
    
    print("\n")
    for i, company in enumerate(companies, 1):
        print(f"{i}. {company['name']}")
        if company.get('tier'):
            print(f"   Tier: {company['tier']}")
        if company.get('role'):
            print(f"   Role: {company['role']}")
        if company.get('criticality'):
            print(f"   Criticality: {company['criticality']}")
        if company.get('location'):
            print(f"   Location: {company['location']}")
        print()


def view_company_relationships(db: Neo4jDatabase, company_name: str):
    """특정 회사의 관계 보기"""
    print("\n" + "=" * 70)
    print(f"🔗 {company_name}의 관계")
    print("=" * 70)
    
    # 의존 관계
    dep_query = """
    MATCH (c:Company {name: $name})-[r:DEPENDS_ON]->(target)
    RETURN target.name as target, type(r) as relationship
    """
    
    dependencies = db.execute_query(dep_query, {'name': company_name})
    
    if dependencies:
        print(f"\n{company_name}가 의존하는 회사:")
        for dep in dependencies:
            print(f"  → {dep['target']}")
    else:
        print(f"\n{company_name}의 의존 관계가 없습니다.")
    
    # 역방향 관계
    rev_query = """
    MATCH (source)-[r:DEPENDS_ON]->(c:Company {name: $name})
    RETURN source.name as source, type(r) as relationship
    """
    
    dependents = db.execute_query(rev_query, {'name': company_name})
    
    if dependents:
        print(f"\n{company_name}에 의존하는 회사:")
        for dep in dependents:
            print(f"  ← {dep['source']}")
    else:
        print(f"\n{company_name}에 의존하는 회사가 없습니다.")


def search_companies(db: Neo4jDatabase, keyword: str):
    """회사 검색"""
    print("\n" + "=" * 70)
    print(f"🔍 '{keyword}' 검색 결과")
    print("=" * 70)
    
    query = """
    MATCH (c:Company)
    WHERE toLower(c.name) CONTAINS toLower($keyword)
    RETURN c.name as name, 
           c.tier as tier, 
           c.role as role
    ORDER BY c.name
    LIMIT 20
    """
    
    results = db.execute_query(query, {'keyword': keyword})
    
    if not results:
        print(f"\n⚠️  '{keyword}'와 일치하는 회사가 없습니다.")
        return
    
    print(f"\n검색된 회사 ({len(results)}개):")
    for i, company in enumerate(results, 1):
        print(f"{i}. {company['name']}")
        if company.get('tier'):
            print(f"   Tier: {company['tier']}")
        if company.get('role'):
            print(f"   Role: {company['role']}")
        print()


def interactive_menu(db: Neo4jDatabase):
    """인터랙티브 메뉴"""
    while True:
        print("\n" + "=" * 70)
        print("📊 Neo4j 데이터베이스 뷰어")
        print("=" * 70)
        print("\n메뉴:")
        print("1. 데이터베이스 통계 보기")
        print("2. 샘플 회사 데이터 보기")
        print("3. 특정 회사의 관계 보기")
        print("4. 회사 검색")
        print("5. 모든 회사 목록 보기")
        print("0. 종료")
        
        choice = input("\n선택 (0-5): ").strip()
        
        if choice == '0':
            print("\n👋 종료합니다.")
            break
        
        elif choice == '1':
            view_database_stats(db)
        
        elif choice == '2':
            limit = input("표시할 개수 (기본 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            view_sample_companies(db, limit)
        
        elif choice == '3':
            company_name = input("회사 이름: ").strip()
            if company_name:
                view_company_relationships(db, company_name)
        
        elif choice == '4':
            keyword = input("검색 키워드: ").strip()
            if keyword:
                search_companies(db, keyword)
        
        elif choice == '5':
            query = """
            MATCH (c:Company)
            RETURN c.name as name
            ORDER BY c.name
            """
            companies = db.execute_query(query)
            
            print("\n" + "=" * 70)
            print(f"🏢 전체 회사 목록 ({len(companies)}개)")
            print("=" * 70)
            print()
            
            for i, company in enumerate(companies, 1):
                print(f"{i}. {company['name']}")
        
        else:
            print("\n⚠️  잘못된 선택입니다.")
        
        input("\nEnter를 눌러 계속...")


def main():
    """메인 함수"""
    print("=" * 70)
    print("🚀 Neo4j 데이터베이스 뷰어")
    print("=" * 70)
    
    # Neo4j 연결
    if not NEO4J_URI or not NEO4J_PASSWORD:
        print("❌ Neo4j 설정이 없습니다. .env 파일을 확인하세요.")
        sys.exit(1)
    
    db = Neo4jDatabase(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    print(f"✅ Neo4j 연결 성공: {NEO4J_URI}")
    
    # 인터랙티브 메뉴
    try:
        interactive_menu(db)
    except KeyboardInterrupt:
        print("\n\n👋 종료합니다.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
