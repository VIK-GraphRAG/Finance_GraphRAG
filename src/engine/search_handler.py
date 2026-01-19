"""
Search Handler - Real-time Web Search Trigger
실시간 검색 트리거: 질문 분석 및 Perplexity API 호출 관리
"""

import re
from typing import Dict, List, Optional, Tuple

try:
    from .search_engine import PerplexitySearchEngine
except ImportError:
    from search_engine import PerplexitySearchEngine


class SearchHandler:
    """
    실시간 웹 검색 트리거 및 관리
    
    Features:
    - 질문 분석 (실시간 정보 필요 여부 판단)
    - Perplexity API 호출
    - 공개 정보만 전달 (내부 문서 내용 차단)
    
    Security:
    - 기업명과 공개 키워드만 전송
    - 내부 문서 내용 절대 불가
    """
    
    # Trigger keywords for real-time search
    REALTIME_KEYWORDS_KR = [
        "최근", "뉴스", "현재", "오늘", "지금",
        "시장 반응", "주가", "동향", "트렌드",
        "발표", "공시", "보도", "언론"
    ]
    
    REALTIME_KEYWORDS_EN = [
        "latest", "news", "current", "today", "now",
        "recent", "breaking", "update", "announcement",
        "market reaction", "stock price", "trend"
    ]
    
    def __init__(self, perplexity_api_key: Optional[str] = None):
        """
        Initialize SearchHandler
        
        Args:
            perplexity_api_key: Perplexity API key (optional)
        """
        self.search_engine = PerplexitySearchEngine(api_key=perplexity_api_key)
    
    def should_trigger_search(self, query: str) -> Tuple[bool, str]:
        """
        Determine if real-time search should be triggered
        
        Args:
            query: User query
            
        Returns:
            (should_search, reason)
        """
        query_lower = query.lower()
        
        # Check Korean keywords
        for keyword in self.REALTIME_KEYWORDS_KR:
            if keyword in query_lower:
                return True, f"Keyword detected: '{keyword}'"
        
        # Check English keywords
        for keyword in self.REALTIME_KEYWORDS_EN:
            if keyword in query_lower:
                return True, f"Keyword detected: '{keyword}'"
        
        return False, "No real-time keywords detected"
    
    def extract_public_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract public entities from query (safe to send to external API)
        
        Args:
            query: User query
            
        Returns:
            Dictionary of public entities
        """
        entities = {
            "companies": [],
            "technologies": [],
            "general_terms": []
        }
        
        # Known public companies (safe to send)
        public_companies = [
            "Nvidia", "NVDA", "엔비디아",
            "TSMC", "TSM", "대만반도체",
            "ASML", "Samsung", "삼성",
            "Intel", "AMD", "Qualcomm",
            "Microsoft", "Google", "Amazon", "AWS",
            "Apple", "Meta", "Tesla"
        ]
        
        for company in public_companies:
            if company.lower() in query.lower():
                entities["companies"].append(company)
        
        # Known public technologies
        public_techs = [
            "GPU", "AI", "chip", "semiconductor", "반도체",
            "HBM", "GDDR", "EUV", "2nm", "3nm", "5nm",
            "Blackwell", "Hopper", "Ada", "Ampere"
        ]
        
        for tech in public_techs:
            if tech.lower() in query.lower():
                entities["technologies"].append(tech)
        
        return entities
    
    def sanitize_query(self, query: str, internal_keywords: Optional[List[str]] = None) -> str:
        """
        Remove internal/sensitive information from query
        
        Args:
            query: Original query
            internal_keywords: List of internal keywords to remove
            
        Returns:
            Sanitized query
        """
        sanitized = query
        
        # Remove internal data tags
        sanitized = re.sub(r'\[INTERNAL_DATA_\d+\]', '', sanitized)
        
        # Remove custom internal keywords
        if internal_keywords:
            for keyword in internal_keywords:
                sanitized = sanitized.replace(keyword, '')
        
        # Remove common sensitive patterns
        sensitive_patterns = [
            r'Project\s+\w+',  # Project names
            r'confidential',
            r'internal',
            r'proprietary'
        ]
        
        for pattern in sensitive_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    def search(
        self,
        query: str,
        max_results: int = 5,
        sanitize: bool = True,
        internal_keywords: Optional[List[str]] = None
    ) -> Dict:
        """
        Perform real-time web search
        
        Args:
            query: User query
            max_results: Maximum number of results
            sanitize: Whether to sanitize query
            internal_keywords: Internal keywords to remove
            
        Returns:
            Search results
        """
        # Sanitize query if enabled
        search_query = query
        if sanitize:
            search_query = self.sanitize_query(query, internal_keywords)
            print(f"🔒 Sanitized query: '{search_query}'")
        
        # Extract public entities
        entities = self.extract_public_entities(search_query)
        
        # Enhance query with entities
        if entities["companies"]:
            company_context = " ".join(entities["companies"][:2])
            search_query = f"{company_context} {search_query}"
        
        # Perform search
        try:
            result = self.search_engine.search(
                query=search_query,
                max_results=max_results
            )
            
            # Add metadata
            result["extracted_entities"] = entities
            result["sanitized"] = sanitize
            
            return result
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return {
                "query": search_query,
                "answer": "",
                "citations": [],
                "error": str(e)
            }
    
    def search_company_news(
        self,
        company_name: str,
        context: str = "latest developments",
        sanitize: bool = True
    ) -> Dict:
        """
        Search for company-specific news
        
        Args:
            company_name: Company name (public only)
            context: Search context
            sanitize: Whether to sanitize
            
        Returns:
            Search results
        """
        # Verify company is public
        public_entities = self.extract_public_entities(company_name)
        
        if not public_entities["companies"]:
            print(f"⚠️ Company '{company_name}' not in public list")
            return {
                "error": "Company not recognized as public entity"
            }
        
        return self.search_engine.search_company_news(
            company_name=company_name,
            context=context
        )
    
    def search_supply_chain_risk(
        self,
        event: str,
        affected_companies: List[str]
    ) -> Dict:
        """
        Search for supply chain risk analysis
        
        Args:
            event: Risk event (public information only)
            affected_companies: List of affected companies
            
        Returns:
            Search results
        """
        # Filter to public companies only
        public_companies = []
        for company in affected_companies:
            entities = self.extract_public_entities(company)
            if entities["companies"]:
                public_companies.extend(entities["companies"])
        
        if not public_companies:
            return {
                "error": "No public companies identified"
            }
        
        return self.search_engine.search_supply_chain_risk(
            event=event,
            affected_companies=public_companies[:3]  # Limit to 3
        )
    
    def format_for_report(self, search_result: Dict) -> str:
        """
        Format search results for report inclusion
        
        Args:
            search_result: Search results
            
        Returns:
            Formatted markdown text
        """
        if "error" in search_result:
            return f"⚠️ Search Error: {search_result['error']}"
        
        return self.search_engine.format_for_report(search_result)


def test_search_handler():
    """Test SearchHandler functionality"""
    print("=" * 60)
    print("Testing SearchHandler")
    print("=" * 60)
    
    handler = SearchHandler()
    
    # Test 1: Trigger detection
    print("\n1️⃣ Testing trigger detection:")
    
    test_queries = [
        "Nvidia의 최신 GPU는?",
        "What is Nvidia's latest GPU?",
        "Nvidia GPU 아키텍처 설명",
        "오늘 Nvidia 뉴스는?"
    ]
    
    for query in test_queries:
        should_search, reason = handler.should_trigger_search(query)
        print(f"  Query: '{query}'")
        print(f"  Trigger: {should_search} ({reason})")
    
    # Test 2: Entity extraction
    print("\n2️⃣ Testing entity extraction:")
    
    query = "Nvidia와 TSMC의 최근 협력 뉴스"
    entities = handler.extract_public_entities(query)
    print(f"  Query: '{query}'")
    print(f"  Entities: {entities}")
    
    # Test 3: Query sanitization
    print("\n3️⃣ Testing query sanitization:")
    
    sensitive_query = "Project Phoenix의 [INTERNAL_DATA_01] 관련 Nvidia 뉴스"
    sanitized = handler.sanitize_query(sensitive_query)
    print(f"  Original: '{sensitive_query}'")
    print(f"  Sanitized: '{sanitized}'")
    
    # Test 4: Real search (if API key available)
    print("\n4️⃣ Testing real search:")
    
    try:
        result = handler.search_company_news("Nvidia", "AI chip developments")
        print(f"  Answer length: {len(result.get('answer', ''))} characters")
        print(f"  Citations: {len(result.get('citations', []))}")
    except Exception as e:
        print(f"  ⚠️ Search test skipped: {e}")


if __name__ == "__main__":
    test_search_handler()
