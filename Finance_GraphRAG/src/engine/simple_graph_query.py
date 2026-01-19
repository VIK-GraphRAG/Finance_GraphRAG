"""
Simple Graph Query Engine
간단한 그래프 쿼리 엔진 - 멀티홉보다 직접적인 패턴 매칭 사용
"""

from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase


class SimpleGraphQuery:
    """간단한 그래프 쿼리 엔진"""
    
    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
    
    def close(self):
        """연결 종료"""
        self.driver.close()
    
    def query_risks(self, subject: str) -> Dict[str, Any]:
        """특정 대상의 리스크 조회"""
        with self.driver.session() as session:
            # 1. 직접 연결된 리스크 찾기
            result = session.run("""
                MATCH (n)-[r]->(risk:Risk)
                WHERE toLower(n.name) CONTAINS toLower($subject)
                   OR labels(n)[0] CONTAINS $subject
                RETURN n.name as entity, labels(n)[0] as entity_type, 
                       type(r) as relationship, 
                       risk.name as risk_name, risk.severity as severity
                LIMIT 20
            """, subject=subject)
            
            records = list(result)
            
            if records:
                answer = f"The {subject} faces the following risks:\n\n"
                for r in records:
                    severity = r['severity'] or 'unknown'
                    answer += f"- **{r['risk_name']}** (Severity: {severity})\n"
                
                return {
                    "answer": answer,
                    "confidence": 0.9,
                    "source": "neo4j_direct",
                    "records": len(records)
                }
            
            # 2. 간접 연결 찾기 (1-hop)
            result = session.run("""
                MATCH (n)-[r1]->(m)-[r2]->(risk:Risk)
                WHERE toLower(n.name) CONTAINS toLower($subject)
                   OR labels(n)[0] CONTAINS $subject
                RETURN n.name as entity, m.name as intermediate,
                       risk.name as risk_name, risk.severity as severity
                LIMIT 10
            """, subject=subject)
            
            records = list(result)
            
            if records:
                answer = f"The {subject} has indirect risk exposure through:\n\n"
                for r in records:
                    severity = r['severity'] or 'unknown'
                    answer += f"- **{r['risk_name']}** via {r['intermediate']} (Severity: {severity})\n"
                
                return {
                    "answer": answer,
                    "confidence": 0.7,
                    "source": "neo4j_indirect",
                    "records": len(records)
                }
            
            return None
    
    def query_general(self, question: str) -> Dict[str, Any]:
        """일반 질문 처리"""
        with self.driver.session() as session:
            # 키워드 추출 (간단한 방식)
            keywords = [word for word in question.lower().split() 
                       if len(word) > 3 and word not in ['what', 'where', 'when', 'how', 'does', 'the']]
            
            if not keywords:
                return None
            
            # 관련 노드 찾기
            result = session.run("""
                MATCH (n)
                WHERE any(keyword IN $keywords WHERE toLower(n.name) CONTAINS keyword)
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN n.name as name, labels(n)[0] as type, 
                       collect(DISTINCT type(r)) as relationships,
                       collect(DISTINCT m.name) as connected_entities
                LIMIT 10
            """, keywords=keywords)
            
            records = list(result)
            
            if records:
                answer = "Based on the knowledge graph:\n\n"
                for r in records:
                    answer += f"**{r['name']}** ({r['type']})\n"
                    if r['relationships']:
                        answer += f"  Relationships: {', '.join(r['relationships'])}\n"
                    if r['connected_entities'] and r['connected_entities'][0]:
                        entities = [e for e in r['connected_entities'] if e][:5]
                        answer += f"  Connected to: {', '.join(entities)}\n"
                    answer += "\n"
                
                return {
                    "answer": answer,
                    "confidence": 0.6,
                    "source": "neo4j_general",
                    "records": len(records)
                }
            
            return None
