"""
Entity Resolution Module
엔티티 동일성 확인 및 정규화를 담당하는 모듈
"""

import re
from typing import List, Dict, Tuple, Set
from difflib import SequenceMatcher


class EntityResolver:
    """
    엔티티 정규화 및 통합을 위한 클래스
    
    Fuzzy matching을 사용하여 유사한 엔티티를 하나로 통합합니다.
    예: "삼성전자", "Samsung Electronics", "SAMSUNG" -> "Samsung Electronics (삼성전자)"
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Args:
            similarity_threshold: 엔티티 유사도 임계값 (0.0 ~ 1.0)
        """
        self.similarity_threshold = similarity_threshold
        self.entity_aliases = {}  # {canonical_name: [aliases]}
        self.normalized_cache = {}  # {original_name: canonical_name}
        
        # 한영 매핑 테이블 (자주 사용되는 기업명)
        self.korean_english_map = {
            "삼성전자": "Samsung Electronics",
            "삼성": "Samsung",
            "엘지전자": "LG Electronics",
            "엘지": "LG",
            "현대자동차": "Hyundai Motor",
            "현대": "Hyundai",
            "기아": "Kia",
            "에스케이하이닉스": "SK Hynix",
            "네이버": "Naver",
            "카카오": "Kakao",
            "엔비디아": "NVIDIA",
            "애플": "Apple",
            "마이크로소프트": "Microsoft",
            "구글": "Google",
            "아마존": "Amazon",
            "테슬라": "Tesla",
        }
        
        # 약어 매핑
        self.abbreviation_map = {
            "NVDA": "NVIDIA",
            "MSFT": "Microsoft",
            "AAPL": "Apple",
            "GOOGL": "Google",
            "AMZN": "Amazon",
            "TSLA": "Tesla",
            "META": "Meta",
            "NFLX": "Netflix",
        }
    
    def normalize_entity(self, entity_name: str) -> str:
        """
        엔티티 이름을 정규화합니다.
        
        Args:
            entity_name: 원본 엔티티 이름
            
        Returns:
            정규화된 엔티티 이름
        """
        if not entity_name or not entity_name.strip():
            return entity_name
        
        # 캐시 확인
        if entity_name in self.normalized_cache:
            return self.normalized_cache[entity_name]
        
        # 1. 기본 정규화
        normalized = self._basic_normalization(entity_name)
        
        # 2. 약어 확장
        if normalized.upper() in self.abbreviation_map:
            normalized = self.abbreviation_map[normalized.upper()]
        
        # 3. 한영 매핑 확인
        canonical = self._check_korean_english_mapping(normalized)
        
        # 4. 기존 엔티티와 fuzzy matching
        if canonical == normalized:  # 매핑되지 않은 경우
            canonical = self._find_similar_entity(normalized)
        
        # 캐시에 저장
        self.normalized_cache[entity_name] = canonical
        
        # 별칭 등록
        if canonical not in self.entity_aliases:
            self.entity_aliases[canonical] = set()
        self.entity_aliases[canonical].add(entity_name)
        
        return canonical
    
    def _basic_normalization(self, text: str) -> str:
        """
        기본 정규화: 공백, 특수문자 제거, 대소문자 통일
        """
        # 앞뒤 공백 제거
        text = text.strip()
        
        # 연속된 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        
        # 괄호 안의 내용 추출 (예: "삼성전자 (Samsung)" -> "삼성전자", "Samsung")
        # 나중에 매칭에 사용
        
        return text
    
    def _check_korean_english_mapping(self, entity_name: str) -> str:
        """
        한영 매핑 테이블 확인
        """
        # 한글 -> 영어
        for korean, english in self.korean_english_map.items():
            if korean in entity_name:
                # 한영 병기 형태로 반환
                return f"{english} ({korean})"
        
        # 영어 -> 한영 병기
        for korean, english in self.korean_english_map.items():
            if english.lower() in entity_name.lower():
                return f"{english} ({korean})"
        
        return entity_name
    
    def _find_similar_entity(self, entity_name: str) -> str:
        """
        기존 엔티티 중 유사한 것을 찾습니다.
        """
        best_match = entity_name
        best_score = 0.0
        
        for canonical_name in self.entity_aliases.keys():
            score = self.fuzzy_match(entity_name, canonical_name)
            if score > best_score and score >= self.similarity_threshold:
                best_score = score
                best_match = canonical_name
        
        return best_match
    
    def fuzzy_match(self, entity1: str, entity2: str) -> float:
        """
        두 엔티티 간의 유사도를 계산합니다.
        
        Args:
            entity1: 첫 번째 엔티티
            entity2: 두 번째 엔티티
            
        Returns:
            유사도 (0.0 ~ 1.0)
        """
        # 대소문자 무시
        e1 = entity1.lower()
        e2 = entity2.lower()
        
        # SequenceMatcher 사용
        ratio = SequenceMatcher(None, e1, e2).ratio()
        
        # 부분 문자열 매칭 보너스
        if e1 in e2 or e2 in e1:
            ratio = max(ratio, 0.9)
        
        # 단어 기반 매칭
        words1 = set(e1.split())
        words2 = set(e2.split())
        if words1 and words2:
            word_overlap = len(words1 & words2) / max(len(words1), len(words2))
            ratio = max(ratio, word_overlap)
        
        return ratio
    
    def merge_entities(self, entities: List[Dict]) -> List[Dict]:
        """
        유사한 엔티티들을 하나로 통합합니다.
        
        Args:
            entities: 엔티티 리스트 [{"name": "...", "type": "...", ...}, ...]
            
        Returns:
            통합된 엔티티 리스트
        """
        if not entities:
            return entities
        
        # 엔티티 이름으로 그룹화
        entity_groups = {}
        
        for entity in entities:
            entity_name = entity.get("name", entity.get("entity_name", ""))
            if not entity_name:
                continue
            
            # 정규화된 이름 얻기
            canonical_name = self.normalize_entity(entity_name)
            
            # 그룹에 추가
            if canonical_name not in entity_groups:
                entity_groups[canonical_name] = []
            entity_groups[canonical_name].append(entity)
        
        # 각 그룹에서 대표 엔티티 선택 및 정보 병합
        merged_entities = []
        for canonical_name, group in entity_groups.items():
            # 첫 번째 엔티티를 베이스로 사용
            merged = group[0].copy()
            merged["name"] = canonical_name
            merged["entity_name"] = canonical_name
            
            # 별칭 정보 추가
            aliases = [e.get("name", e.get("entity_name", "")) for e in group]
            merged["aliases"] = list(set(aliases))
            
            # 설명 병합 (가장 긴 것 선택)
            descriptions = [e.get("description", "") for e in group if e.get("description")]
            if descriptions:
                merged["description"] = max(descriptions, key=len)
            
            merged_entities.append(merged)
        
        return merged_entities
    
    def get_aliases(self, canonical_name: str) -> List[str]:
        """
        정규화된 이름의 모든 별칭을 반환합니다.
        """
        return list(self.entity_aliases.get(canonical_name, set()))
    
    def get_statistics(self) -> Dict[str, int]:
        """
        엔티티 정규화 통계를 반환합니다.
        """
        total_aliases = sum(len(aliases) for aliases in self.entity_aliases.values())
        return {
            "unique_entities": len(self.entity_aliases),
            "total_aliases": total_aliases,
            "cached_normalizations": len(self.normalized_cache)
        }
