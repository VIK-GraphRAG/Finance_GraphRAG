"""
Query Processor with Multi-Hop Reasoning and Perplexity Fallback
멀티홉 추론 + Perplexity API 폴백 통합 쿼리 프로세서
"""

import os
import asyncio
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class QueryProcessor:
    """
    통합 쿼리 프로세서
    
    Perplexity API 호출 가이드라인:
    1. 시간적 민감성 질문 (오늘, 이번 주, 최신, real-time)
    2. 변동 수치 (주가, 환율, 지표)
    3. 내부 분석 결과가 불확실하거나 데이터 부족
    
    처리 순서:
    1. 질문 유형 분석 (시간 민감/변동 수치 여부)
    2. Neo4j 멀티홉 추론 시도
    3. 가이드라인 조건 충족 시만 Perplexity 호출
    """
    
    def __init__(self, neo4j_db=None, perplexity_api_key: Optional[str] = None):
        self.neo4j_db = neo4j_db
        self.perplexity_api_key = perplexity_api_key or os.getenv("PERPLEXITY_API_KEY")
        
        # Time-sensitive keywords
        self.time_sensitive_keywords = [
            'today', 'this week', 'this month', 'latest', 'recent', 'current',
            'now', 'real-time', '오늘', '이번주', '이번달', '최신', '현재', 'real time'
        ]
        
        # Dynamic value keywords
        self.dynamic_value_keywords = [
            'price', 'stock', 'rate', 'exchange', 'value', 'trading',
            '주가', '환율', '가격', '시세', '거래'
        ]
        
        # Uncertainty indicators
        self.uncertainty_indicators = [
            'uncertain', 'unclear', 'insufficient', 'not enough', 'limited',
            '불확실', '불명확', '부족', '데이터 없음'
        ]
        
        
    def _should_use_perplexity(self, question: str, neo4j_result: Optional[Dict] = None) -> tuple[bool, str]:
        """
        Perplexity API 사용 여부 판단
        
        Returns:
            (should_use, reason)
        """
        question_lower = question.lower()
        
        # 1. 시간적 민감성 체크
        if any(keyword in question_lower for keyword in self.time_sensitive_keywords):
            return True, "Time-sensitive query"
        
        # 2. 변동 수치 체크
        if any(keyword in question_lower for keyword in self.dynamic_value_keywords):
            return True, "Dynamic value query"
        
        # 3. Neo4j 결과 없음
        if not neo4j_result:
            return True, "No Neo4j results"
        
        # 4. Neo4j 결과의 불확실성 체크
        answer = neo4j_result.get("answer", "").lower()
        if any(indicator in answer for indicator in self.uncertainty_indicators):
            return True, "Uncertain Neo4j result"
        
        # 5. 매우 낮은 신뢰도 (<30%)
        confidence = neo4j_result.get("confidence", 0.0)
        if confidence < 0.3:
            return True, f"Low confidence ({confidence:.1%})"
        
        return False, "Neo4j result sufficient"
    
    async def processQuery(
        self,
        question: str,
        max_hops: int = 3,
        use_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        질문 처리 (멀티홉 추론 + 스마트 폴백)
        
        Args:
            question: 사용자 질문
            max_hops: 최대 홉 수
            use_fallback: Perplexity 폴백 사용 여부
            
        Returns:
            처리 결과 딕셔너리
        """
        result = {
            "question": question,
            "answer": "",
            "source": "unknown",
            "confidence": 0.0,
            "reasoning_path": [],
            "fallback_used": False
        }
        
        # Step 1: Neo4j 멀티홉 추론 시도
        print(f"\n[1/3] Neo4j Multi-Hop Reasoning...")
        neo4j_result = await self._queryNeo4jMultihop(question, max_hops)
        
        # Step 2: Perplexity 사용 여부 판단
        should_use_perplexity, reason = self._should_use_perplexity(question, neo4j_result)
        
        if neo4j_result:
            confidence = neo4j_result.get("confidence", 0.0)
            print(f"  ✓ Neo4j result: {confidence:.2%}")
            
            if not should_use_perplexity:
                # Neo4j 결과 충분 → 바로 반환
                print(f"  ✓ Neo4j result sufficient, skipping Perplexity")
                result.update({
                    "answer": neo4j_result["answer"],
                    "source": "neo4j_multihop",
                    "confidence": confidence,
                    "reasoning_path": neo4j_result.get("path", []),
                    "entities_found": neo4j_result.get("entities", [])
                })
                return result
            else:
                print(f"  ⚠ Perplexity needed: {reason}")
        else:
            print(f"  ⚠ No Neo4j results")
        
        # Step 3: Perplexity API 호출 (조건 충족 시만)
        if use_fallback and self.perplexity_api_key and should_use_perplexity:
            print(f"\n[2/3] Perplexity API Fallback ({reason})...")
            perplexity_result = await self._queryPerplexity(question)
            
            if perplexity_result:
                print(f"  ✓ Perplexity response received")
                
                # Citations 추출 및 포맷팅
                citations = perplexity_result.get("citations", [])
                citations_text = ""
                if citations:
                    citations_text = "\n\n**출처 (Citations):**\n"
                    for i, url in enumerate(citations, 1):
                        citations_text += f"{i}. {url}\n"
                
                # 답변에 Citations 추가
                answer_with_citations = perplexity_result["answer"] + citations_text
                
                result.update({
                    "answer": answer_with_citations,
                    "source": "perplexity_api",
                    "confidence": 0.8,
                    "fallback_used": True,
                    "fallback_reason": reason,
                    "citations": citations
                })
                
                # Neo4j 결과가 있었다면 함께 제공
                if neo4j_result:
                    result["neo4j_context"] = {
                        "answer": neo4j_result["answer"],
                        "confidence": neo4j_result["confidence"],
                        "path": neo4j_result.get("path", [])
                    }
                
                return result
        
        # Step 4: 폴백 실패 또는 비활성화
        if neo4j_result:
            # 낮은 신뢰도지만 Neo4j 결과라도 반환
            print(f"\n[3/3] Using low-confidence Neo4j result")
            result.update({
                "answer": neo4j_result["answer"],
                "source": "neo4j_multihop_low_confidence",
                "confidence": neo4j_result["confidence"],
                "reasoning_path": neo4j_result.get("path", []),
                "warning": "Low confidence result. Consider enabling Perplexity fallback."
            })
        else:
            # 아무 결과도 없음
            print(f"\n[3/3] No results available")
            result.update({
                "answer": "I couldn't find relevant information in the knowledge graph or external sources.",
                "source": "no_results",
                "confidence": 0.0,
                "error": "No data available"
            })
        
        return result
    
    async def _queryNeo4jMultihop(
        self,
        question: str,
        max_hops: int = 3
    ) -> Optional[Dict[str, Any]]:
        """Neo4j 쿼리 (간단한 패턴 매칭 우선)"""
        try:
            from engine.simple_graph_query import SimpleGraphQuery
            
            if not self.neo4j_db:
                print("  ⚠ Neo4j not available")
                return None
            
            # Simple query engine 사용
            simple_query = SimpleGraphQuery(
                uri=self.neo4j_db.uri,
                username=self.neo4j_db.username,
                password=self.neo4j_db.password
            )
            
            # Risk query detection
            question_lower = question.lower()
            
            if 'risk' in question_lower:
                # Extract subject
                subject = 'semiconductor'  # default
                if 'nvidia' in question_lower:
                    subject = 'nvidia'
                elif 'tsmc' in question_lower:
                    subject = 'tsmc'
                elif 'taiwan' in question_lower:
                    subject = 'taiwan'
                elif 'semiconductor' in question_lower or 'chip' in question_lower:
                    subject = 'semiconductor'
                
                result = simple_query.query_risks(subject)
                simple_query.close()
                
                if result:
                    return result
            
            # General query
            result = simple_query.query_general(question)
            simple_query.close()
            
            return result
            
        except Exception as e:
            print(f"  ✗ Neo4j error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _queryPerplexity(self, question: str) -> Optional[Dict[str, Any]]:
        """Perplexity API 호출"""
        try:
            import aiohttp
            import ssl
            
            url = "https://api.perplexity.ai/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful financial analyst. Provide accurate, concise answers with citations."
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 1000
            }
            
            # SSL 컨텍스트 생성 (인증서 검증 비활성화)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        answer = data["choices"][0]["message"]["content"]
                        citations = data.get("citations", [])
                        
                        return {
                            "answer": answer,
                            "citations": citations
                        }
                    else:
                        print(f"  ✗ Perplexity API error: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"  ✗ Perplexity error: {e}")
            return None
    
    def _calculateConfidence(self, reasoning_result: Dict[str, Any]) -> float:
        """
        추론 결과의 신뢰도 계산
        
        고려 요소:
        - 경로 길이 (짧을수록 높음)
        - 엔티티 수 (많을수록 높음)
        - 관계 타입 다양성
        """
        confidence = 0.5  # 기본값
        
        # 경로가 있으면 +0.2
        if reasoning_result.get("path"):
            confidence += 0.2
            
            # 경로 길이에 따라 조정 (2-3 hop이 최적)
            path_length = len(reasoning_result["path"])
            if 2 <= path_length <= 3:
                confidence += 0.2
            elif path_length == 1:
                confidence += 0.1
        
        # 엔티티가 발견되면 +0.1
        if reasoning_result.get("entities"):
            confidence += 0.1
        
        # 추론 단계가 있으면 +0.1
        if reasoning_result.get("reasoning_steps"):
            confidence += 0.1
        
        return min(confidence, 1.0)  # 최대 1.0


# Utility function
async def processQueryWithFallback(
    question: str,
    neo4j_db=None,
    max_hops: int = 3,
    use_fallback: bool = True
) -> Dict[str, Any]:
    """
    간편 함수: 질문 처리 (멀티홉 + 폴백)
    
    Usage:
        result = await process_query_with_fallback(
            "How does Taiwan tension affect Nvidia?",
            neo4j_db=db
        )
    """
    processor = QueryProcessor(neo4j_db=neo4j_db)
    return await processor.processQuery(
        question=question,
        max_hops=max_hops,
        use_fallback=use_fallback
    )
