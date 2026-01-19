"""
Perplexity API Integration for Real-time Web Search
Provides latest news, market trends, and regulatory updates for tech companies
"""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests

try:
    from ..config import (
        PERPLEXITY_API_KEY,
        PERPLEXITY_BASE_URL,
        PERPLEXITY_MODEL,
        PERPLEXITY_MAX_RESULTS
    )
except ImportError:
    from config import (
        PERPLEXITY_API_KEY,
        PERPLEXITY_BASE_URL,
        PERPLEXITY_MODEL,
        PERPLEXITY_MAX_RESULTS
    )


class PerplexitySearchEngine:
    """
    Real-time web search engine using Perplexity API
    Optimized for financial and tech industry queries
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        cache_ttl: int = 3600  # Cache results for 1 hour
    ):
        self.api_key = api_key or PERPLEXITY_API_KEY
        self.base_url = PERPLEXITY_BASE_URL
        self.model = model or PERPLEXITY_MODEL
        self.cache_ttl = cache_ttl
        
        # Simple in-memory cache
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        if not self.api_key:
            raise ValueError(
                "Perplexity API key not found. "
                "Set PERPLEXITY_API_KEY in .env file."
            )
    
    def search(
        self,
        query: str,
        max_results: int = PERPLEXITY_MAX_RESULTS,
        focus: str = "internet",  # or "scholar", "writing", "wolfram", "youtube"
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Perform real-time web search
        
        Args:
            query: Search query (e.g., "Taiwan earthquake semiconductor impact")
            max_results: Maximum number of results
            focus: Search focus mode
            use_cache: Use cached results if available
        
        Returns:
            {
                'query': str,
                'answer': str,  # Synthesized answer from Perplexity
                'sources': List[Dict],  # List of source URLs with titles
                'citations': List[str],  # Citation URLs
                'timestamp': str,
                'cached': bool
            }
        """
        
        # Check cache
        cache_key = f"{query}:{focus}:{max_results}"
        if use_cache and cache_key in self._cache:
            cached_result = self._cache[cache_key]
            if time.time() - cached_result['_cache_time'] < self.cache_ttl:
                print(f"🔄 Using cached result for: {query[:50]}...")
                result = cached_result.copy()
                result['cached'] = True
                del result['_cache_time']
                return result
        
        print(f"🔍 Searching Perplexity: {query[:50]}...")
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Build payload based on 2026 Perplexity API format
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a financial analyst assistant. "
                        "Provide accurate, up-to-date information about tech companies, "
                        "semiconductor industry, regulations, and market trends. "
                        "Always cite your sources."
                    )
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.2,
            "top_p": 0.9,
            "search_mode": "web",  # Updated parameter (was search_domain_filter)
            "return_images": False,
            "return_related_questions": False,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract answer and citations (updated format for 2026 API)
            answer = data['choices'][0]['message']['content']
            
            # Extract citations from search_results or citations field
            citations = []
            if 'citations' in data:
                citations = data['citations']
            elif 'search_results' in data:
                # Extract URLs from search_results
                citations = [result.get('url', '') for result in data.get('search_results', []) if result.get('url')]
            
            result = {
                'query': query,
                'answer': answer,
                'citations': citations,
                'sources': self._extract_sources(answer, citations),
                'timestamp': datetime.now().isoformat(),
                'cached': False
            }
            
            # Cache result
            cache_entry = result.copy()
            cache_entry['_cache_time'] = time.time()
            self._cache[cache_key] = cache_entry
            
            print(f"✅ Found {len(citations)} citations")
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid Perplexity API key")
            elif e.response.status_code == 429:
                raise RuntimeError("Perplexity API rate limit exceeded")
            else:
                raise RuntimeError(f"Perplexity API error: {e}")
        except Exception as e:
            raise RuntimeError(f"Search failed: {e}")
    
    def _extract_sources(
        self,
        answer: str,
        citations: List[str]
    ) -> List[Dict[str, str]]:
        """
        Extract source information from answer and citations
        
        Returns:
            List of {title, url, snippet}
        """
        sources = []
        
        for i, url in enumerate(citations, 1):
            # Extract domain for title
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            
            sources.append({
                'title': f"Source {i} ({domain})",
                'url': url,
                'snippet': ''  # Perplexity doesn't provide snippets separately
            })
        
        return sources
    
    def search_company_news(
        self,
        company_name: str,
        context: str = "latest news and developments"
    ) -> Dict[str, Any]:
        """
        Search for company-specific news
        
        Args:
            company_name: Company name (e.g., "Nvidia", "TSMC")
            context: Additional context (e.g., "supply chain risk")
        
        Returns:
            Search results with company focus
        """
        query = f"{company_name} {context} in the last 30 days"
        return self.search(query, focus="internet")
    
    def search_regulation(
        self,
        regulation_name: str,
        impact_on: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for regulation updates
        
        Args:
            regulation_name: Regulation (e.g., "CHIPS Act", "EU AI Act")
            impact_on: Entity affected (e.g., "Intel", "semiconductor industry")
        
        Returns:
            Search results with regulation focus
        """
        query = regulation_name
        if impact_on:
            query += f" impact on {impact_on}"
        query += " latest updates"
        
        return self.search(query, focus="internet")
    
    def search_supply_chain_risk(
        self,
        event: str,
        affected_companies: List[str]
    ) -> Dict[str, Any]:
        """
        Search for supply chain risk analysis
        
        Args:
            event: Risk event (e.g., "Taiwan earthquake", "US-China tension")
            affected_companies: Companies to analyze
        
        Returns:
            Search results with supply chain focus
        """
        companies_str = ", ".join(affected_companies[:3])  # Limit to 3
        query = f"{event} impact on {companies_str} supply chain"
        
        return self.search(query, focus="internet")
    
    def search_tech_milestone(
        self,
        technology: str,
        milestone_type: str = "development timeline"
    ) -> Dict[str, Any]:
        """
        Search for technology roadmap updates
        
        Args:
            technology: Technology (e.g., "2nm chip", "HBM4")
            milestone_type: Type of milestone
        
        Returns:
            Search results with tech focus
        """
        query = f"{technology} {milestone_type} latest updates"
        return self.search(query, focus="internet")
    
    def format_for_report(self, search_result: Dict[str, Any]) -> str:
        """
        Format search results for inclusion in financial report
        
        Args:
            search_result: Result from search()
        
        Returns:
            Markdown formatted text
        """
        output = []
        
        output.append(f"**Latest Intelligence ({search_result['timestamp'][:10]})**\n")
        output.append(search_result['answer'])
        output.append("\n\n**Sources:**")
        
        for source in search_result['sources']:
            output.append(f"- [{source['title']}]({source['url']})")
        
        return "\n".join(output)
    
    def clear_cache(self):
        """Clear cached search results"""
        self._cache.clear()
        print("🗑️  Search cache cleared")


def example_usage():
    """Example: How to use PerplexitySearchEngine"""
    
    try:
        engine = PerplexitySearchEngine()
        
        # Example 1: Company news
        print("\n" + "="*60)
        print("Example 1: Company News")
        print("="*60)
        
        result = engine.search_company_news(
            company_name="Nvidia",
            context="AI chip demand and supply chain"
        )
        print(result['answer'][:300] + "...")
        print(f"Citations: {len(result['citations'])}")
        
        # Example 2: Regulation search
        print("\n" + "="*60)
        print("Example 2: Regulation Impact")
        print("="*60)
        
        result = engine.search_regulation(
            regulation_name="CHIPS Act",
            impact_on="Intel"
        )
        print(result['answer'][:300] + "...")
        
        # Example 3: Supply chain risk
        print("\n" + "="*60)
        print("Example 3: Supply Chain Risk")
        print("="*60)
        
        result = engine.search_supply_chain_risk(
            event="Taiwan geopolitical tension",
            affected_companies=["TSMC", "Nvidia", "AMD"]
        )
        print(result['answer'][:300] + "...")
        
        # Example 4: Tech milestone
        print("\n" + "="*60)
        print("Example 4: Technology Roadmap")
        print("="*60)
        
        result = engine.search_tech_milestone(
            technology="2nm chip manufacturing",
            milestone_type="mass production timeline"
        )
        print(result['answer'][:300] + "...")
        
        # Example 5: Format for report
        print("\n" + "="*60)
        print("Example 5: Formatted Report Section")
        print("="*60)
        
        formatted = engine.format_for_report(result)
        print(formatted[:500] + "...")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("💡 Set PERPLEXITY_API_KEY in .env file")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    example_usage()
