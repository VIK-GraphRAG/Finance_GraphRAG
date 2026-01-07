# search.py - 웹 검색 모듈
# DuckDuckGo를 사용하여 최신 정보를 검색하는 기능을 제공해요!

from duckduckgo_search import DDGS
from typing import List, Dict, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

# 로거 설정
logger = logging.getLogger(__name__)

# ThreadPoolExecutor for async execution
executor = ThreadPoolExecutor(max_workers=3)


async def web_search(query: str, max_results: int = 5, timeout: int = 10) -> List[Dict[str, str]]:
    """
    DuckDuckGo를 사용한 웹 검색
    
    Args:
        query: 검색할 질문/키워드
        max_results: 최대 검색 결과 개수 (기본값: 5)
        timeout: 검색 타임아웃 시간(초) (기본값: 10)
    
    Returns:
        검색 결과 리스트:
        [{
            "title": "검색 결과 제목",
            "snippet": "검색 결과 요약",
            "url": "출처 URL"
        }, ...]
    
    Raises:
        Exception: 검색 실패 시 예외 발생
    """
    try:
        logger.info(f"🔍 웹 검색 시작: '{query}' (최대 {max_results}개 결과)")
        
        # DuckDuckGo 검색을 별도 스레드에서 실행 (블로킹 방지)
        def _search():
            with DDGS() as ddgs:
                # text() 메서드로 웹 검색
                results = list(ddgs.text(
                    keywords=query,
                    max_results=max_results,
                    region='wt-wt',  # Worldwide
                    safesearch='moderate',
                    timelimit='m'  # 최근 1개월 이내 결과 우선
                ))
                return results
        
        # 비동기로 검색 실행 (타임아웃 포함)
        loop = asyncio.get_event_loop()
        results = await asyncio.wait_for(
            loop.run_in_executor(executor, _search),
            timeout=timeout
        )
        
        # 결과를 표준 형식으로 변환
        formatted_results = []
        for item in results:
            formatted_results.append({
                "title": item.get("title", "No title"),
                "snippet": item.get("body", "No description"),
                "url": item.get("href", "")
            })
        
        logger.info(f"✅ 웹 검색 완료: {len(formatted_results)}개 결과 발견")
        return formatted_results
        
    except asyncio.TimeoutError:
        logger.error(f"❌ 웹 검색 타임아웃: {timeout}초 초과")
        raise Exception(f"웹 검색이 {timeout}초를 초과했어요. 나중에 다시 시도해주세요.")
    
    except Exception as e:
        logger.error(f"❌ 웹 검색 실패: {type(e).__name__}: {str(e)}")
        raise Exception(f"웹 검색 중 에러가 발생했어요: {str(e)}")


async def format_search_results(results: List[Dict[str, str]]) -> str:
    """
    검색 결과를 읽기 쉬운 텍스트 형식으로 변환
    
    Args:
        results: web_search()의 반환값
    
    Returns:
        포맷된 검색 결과 문자열
    """
    if not results:
        return "검색 결과가 없습니다."
    
    formatted = "웹 검색 결과:\n\n"
    for idx, result in enumerate(results, 1):
        formatted += f"{idx}. {result['title']}\n"
        formatted += f"   {result['snippet']}\n"
        formatted += f"   출처: {result['url']}\n\n"
    
    return formatted


# 테스트용 메인 함수
async def main():
    """테스트용 함수"""
    try:
        # 테스트 쿼리
        query = "NVIDIA stock price today"
        results = await web_search(query, max_results=3)
        
        print(f"\n검색 쿼리: {query}")
        print(f"결과 개수: {len(results)}")
        print("\n" + await format_search_results(results))
        
    except Exception as e:
        print(f"에러: {e}")


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # 비동기 실행
    asyncio.run(main())

