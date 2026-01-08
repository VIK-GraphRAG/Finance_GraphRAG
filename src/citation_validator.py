"""
Citation Validator Module
LLM 응답의 citation 정확성을 검증하는 모듈
"""

import re
from typing import List, Dict, Tuple
from difflib import SequenceMatcher


class CitationValidator:
    """
    LLM 응답의 각 citation이 실제 소스와 일치하는지 검증하는 클래스
    """
    
    def __init__(self, sources: List[Dict]):
        """
        Args:
            sources: 출처 리스트 [{"id": 1, "file": "...", "excerpt": "..."}, ...]
        """
        self.sources = {s['id']: s for s in sources}
        self.max_sources = max(self.sources.keys()) if self.sources else 0
    
    def validate_response(self, response: str) -> Dict:
        """
        LLM 응답의 각 citation이 실제 소스와 일치하는지 검증
        
        Args:
            response: LLM 응답 텍스트
            
        Returns:
            {
                "is_valid": bool,
                "invalid_citations": List[int],  # 존재하지 않는 citation 번호
                "missing_citations": List[str],  # 인용되어야 하는데 안된 부분
                "confidence_score": float,  # 0.0 ~ 1.0
                "total_citations": int,
                "valid_citations": int
            }
        """
        # 1. Citation 번호 추출
        citations = self._extract_citations(response)
        
        # 2. 존재하지 않는 citation 확인
        invalid_citations = [c for c in citations if c not in self.sources]
        
        # 3. 각 claim이 해당 소스에 실제 존재하는지 검증
        claims = self._extract_claims_with_citations(response)
        unsupported_claims = []
        
        for claim, citation_ids in claims:
            is_supported = False
            for cid in citation_ids:
                if cid in self.sources:
                    source_text = self.sources[cid].get('excerpt', '')
                    original = self.sources[cid].get('original_sentence', source_text)
                    
                    if self._claim_supported_by_source(claim, source_text) or \
                       self._claim_supported_by_source(claim, original):
                        is_supported = True
                        break
            
            if not is_supported and citation_ids:
                unsupported_claims.append(claim[:100])  # 처음 100자만

        # 3.5 인용이 없는 factual 문장 탐지 (한국어/보고서 대응)
        missing_citations = self._extract_uncited_factual_sentences(response)
        
        # 4. 신뢰도 점수 계산
        total_citations = len(citations)
        valid_citations = total_citations - len(invalid_citations)
        
        if total_citations > 0:
            citation_accuracy = valid_citations / total_citations
        else:
            citation_accuracy = 1.0  # citation이 없으면 100%
        
        # 클레임 지원도
        total_claims = len(claims)
        if total_claims > 0:
            claim_support = (total_claims - len(unsupported_claims)) / total_claims
        else:
            claim_support = 1.0
        
        # 최종 신뢰도: citation 정확도 70% + claim 지원도 30%
        confidence_score = citation_accuracy * 0.7 + claim_support * 0.3
        # 인용 누락이 많을수록 감점 (최대 50% 감점)
        if missing_citations:
            missing_rate = min(1.0, len(missing_citations) / max(1, len(self._split_sentences(response))))
            confidence_score = confidence_score * (1.0 - 0.5 * missing_rate)
        
        return {
            "is_valid": len(invalid_citations) == 0 and len(unsupported_claims) == 0 and len(missing_citations) == 0,
            "invalid_citations": invalid_citations,
            "unsupported_claims": unsupported_claims,
            "missing_citations": missing_citations,
            "confidence_score": confidence_score,
            "total_citations": total_citations,
            "valid_citations": valid_citations,
            "citation_accuracy": citation_accuracy,
            "claim_support": claim_support
        }

    def build_evidence(self, response: str) -> List[Dict]:
        """
        응답 텍스트에서 문장(클레임)과 citation을 추출해 근거 구조를 만든다.

        Returns:
            [{
              "claim_id": int,
              "claim_text": str,
              "citation_ids": List[int],
              "sources": List[Dict]  # 원본 sources 항목
            }, ...]
        """
        claims = self._extract_claims_with_citations(response)
        evidence: List[Dict] = []
        for i, (claim, citation_ids) in enumerate(claims, 1):
            srcs: List[Dict] = []
            for cid in citation_ids:
                if cid in self.sources:
                    srcs.append(self.sources[cid])
            evidence.append(
                {
                    "claim_id": i,
                    "claim_text": claim,
                    "citation_ids": citation_ids,
                    "sources": srcs,
                }
            )
        return evidence
    
    def _extract_citations(self, text: str) -> List[int]:
        """텍스트에서 모든 citation 번호 추출"""
        pattern = r'\[(\d+)\]'
        citations = re.findall(pattern, text)
        return [int(c) for c in citations]
    
    def _extract_claims_with_citations(self, text: str) -> List[Tuple[str, List[int]]]:
        """
        텍스트를 문장 단위로 분리하고 각 문장의 citation 추출
        
        Returns:
            [(claim_text, [citation_ids]), ...]
        """
        claims = []
        
        # 문장 단위로 분리 (한국어/보고서 대응)
        sentences = self._split_sentences(text)
        
        for sentence in sentences:
            # 이 문장의 citation 추출
            citations = self._extract_citations(sentence)
            
            if citations:
                # citation 제거한 순수 claim 텍스트
                clean_claim = re.sub(r'\[\d+\]', '', sentence).strip()
                if len(clean_claim) > 10:  # 너무 짧은 문장 제외
                    claims.append((clean_claim, citations))
        
        return claims

    def _split_sentences(self, text: str) -> List[str]:
        """
        한국어/영어/보고서형 텍스트에 대한 문장 분해.
        - 줄바꿈/불릿 기반 분해 우선
        - 그 다음 구두점 기반 분해
        """
        if not text:
            return []
        t = text.replace("\r\n", "\n")
        # 불릿/번호 목록을 줄바꿈으로 정규화
        t = re.sub(r"[\u2022•]\s*", "\n", t)  # bullet
        t = re.sub(r"\n{2,}", "\n", t)
        lines = [ln.strip() for ln in t.split("\n") if ln.strip()]
        sentences: List[str] = []
        for ln in lines:
            parts = re.split(r"(?<=[.!?])\s+", ln)
            for p in parts:
                p = p.strip()
                if p:
                    sentences.append(p)
        return sentences

    def _extract_uncited_factual_sentences(self, text: str) -> List[str]:
        """
        인용이 없는데 사실 주장처럼 보이는 문장을 찾아 반환.
        (신뢰성 강화용, 과도한 오탐 방지 위해 보수적)
        """
        missing: List[str] = []
        for s in self._split_sentences(text):
            if not s or len(s) < 25:
                continue
            if s.lstrip().startswith("#"):
                continue
            if "References" in s or "참고" in s:
                continue
            if self._extract_citations(s):
                continue
            # 숫자/퍼센트/통화 등 사실성 신호
            if re.search(r"\d", s) or "%" in s or "$" in s or "원" in s or "억" in s or "조" in s:
                missing.append(s[:120])
        return missing
    
    def _claim_supported_by_source(self, claim: str, source_text: str, threshold: float = 0.3) -> bool:
        """
        claim이 source_text에 의해 지원되는지 확인
        
        Args:
            claim: 검증할 주장
            source_text: 소스 텍스트
            threshold: 유사도 임계값
            
        Returns:
            지원 여부
        """
        if not claim or not source_text:
            return False
        
        # 대소문자 무시
        claim_lower = claim.lower()
        source_lower = source_text.lower()
        
        # 1. 직접 포함 확인
        if claim_lower in source_lower or source_lower in claim_lower:
            return True
        
        # 2. 키워드 매칭
        claim_words = set(re.findall(r'\w+', claim_lower))
        source_words = set(re.findall(r'\w+', source_lower))
        
        # 불용어 제거
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                     '은', '는', '이', '가', '을', '를', '에', '의', '와', '과', '도', '만'}
        claim_words -= stopwords
        source_words -= stopwords
        
        if not claim_words:
            return False
        
        # 키워드 오버랩 비율
        overlap = len(claim_words & source_words) / len(claim_words)
        if overlap >= threshold:
            return True
        
        # 3. 시퀀스 매칭 (더 정밀한 유사도)
        ratio = SequenceMatcher(None, claim_lower, source_lower).ratio()
        return ratio >= threshold
    
    def get_validation_summary(self, validation_result: Dict) -> str:
        """
        검증 결과를 사람이 읽기 쉬운 형식으로 변환
        """
        if validation_result["is_valid"]:
            return f"✅ 모든 citation이 유효합니다. (신뢰도: {validation_result['confidence_score']:.1%})"
        
        summary = []
        
        if validation_result["invalid_citations"]:
            summary.append(f"❌ 존재하지 않는 citation: {validation_result['invalid_citations']}")
        
        if validation_result["unsupported_claims"]:
            summary.append(f"⚠️  소스에서 지원되지 않는 주장: {len(validation_result['unsupported_claims'])}개")
        
        summary.append(f"📊 신뢰도: {validation_result['confidence_score']:.1%}")
        summary.append(f"   - Citation 정확도: {validation_result['citation_accuracy']:.1%}")
        summary.append(f"   - Claim 지원도: {validation_result['claim_support']:.1%}")
        
        return "\n".join(summary)
