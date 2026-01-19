"""
Local Worker - PDF Processing with Qwen 2.5 Coder
로컬 보안 게이트웨이: 모든 민감 데이터는 로컬에서만 처리

SECURITY POLICY:
- 이 모듈은 민감 데이터를 처리합니다
- 반드시 로컬 Ollama 모델만 사용해야 합니다
- 클라우드 API 사용 절대 금지
"""

import os
import re
from typing import Dict, List, Tuple, Optional
import json
import sys

# Security Check: Verify local model before any processing
try:
    from engine.connection_check import check_local_model_before_processing
except ImportError:
    from .connection_check import check_local_model_before_processing

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("❌ SECURITY ERROR: ollama package not installed")
    print("Install with: pip install ollama")
    sys.exit(1)

try:
    from ..config import LOCAL_MODELS
except ImportError:
    from config import LOCAL_MODELS

# Force local model URL
LOCAL_LLM_URL = os.getenv("LOCAL_LLM_URL", "http://localhost:11434")


class LocalWorker:
    """
    로컬 PDF 처리 및 민감정보 보호
    
    Features:
    - PDF 파싱 (Qwen 2.5 Coder 사용)
    - 엔티티 추출 (회사명, 수치, 프로젝트명)
    - 민감정보 자동 태깅
    - Neo4j 저장 (원본 데이터)
    
    Security:
    - 외부 API 호출 없음
    - 모든 처리 로컬에서 완료
    """
    
    def __init__(
        self,
        model: str = "qwen2.5-coder:3b",
        enforce_security: bool = True
    ):
        # SECURITY: Force local model only
        self.model = model
        self.ollama_base_url = LOCAL_LLM_URL
        
        # Sensitive data counter
        self.sensitive_counter = 0
        self.sensitive_mapping = {}  # {tag: original_value}
        
        # SECURITY CHECK: Enforce local model availability
        if enforce_security:
            print("\n🔒 SECURITY: Checking local model availability...")
            check_local_model_before_processing()
        
        if not OLLAMA_AVAILABLE:
            print("❌ CRITICAL: Ollama not available")
            print("Cannot process sensitive data without local model")
            sys.exit(1)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            import pymupdf  # PyMuPDF
            
            doc = pymupdf.open(pdf_path)
            text = ""
            
            for page in doc:
                text += page.get_text()
            
            doc.close()
            return text
        
        except ImportError:
            print("❌ PyMuPDF not installed. Trying alternative method...")
            try:
                # Alternative: use PyPDF2
                import PyPDF2
                
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text()
                return text
            except ImportError:
                raise ImportError(
                    "PDF processing requires PyMuPDF or PyPDF2. "
                    "Install with: pip install pymupdf or pip install PyPDF2"
                )
            
        except Exception as e:
            print(f"❌ PDF extraction failed: {e}")
            return ""
    
    def extract_entities_with_qwen(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities using Qwen 2.5 Coder (Local LLM ONLY)
        
        SECURITY: This function processes sensitive data
        - Must use local Ollama model only
        - No cloud API fallback allowed
        
        Args:
            text: Document text
            
        Returns:
            Dictionary of entities by type
        """
        if not OLLAMA_AVAILABLE:
            print("❌ SECURITY VIOLATION: Ollama not available for sensitive data processing")
            print("Cannot fallback to cloud API for security reasons")
            sys.exit(1)
        
        try:
            # Prompt for entity extraction
            prompt = f"""Extract the following entities from the text:
1. Companies (회사명)
2. Technologies (기술명)
3. Numbers (수치 - 매출, 점유율 등)
4. Projects (프로젝트명)
5. Dates (날짜)

Text:
{text[:2000]}

Return JSON format:
{{
    "companies": ["Company1", "Company2"],
    "technologies": ["Tech1", "Tech2"],
    "numbers": ["$1.2B", "25%"],
    "projects": ["Project1"],
    "dates": ["2024 Q3"]
}}
"""
            
            # SECURITY: Call local Ollama only
            print(f"🔒 Processing with LOCAL model: {self.model}")
            print(f"🔒 Ollama URL: {self.ollama_base_url}")
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial document analyzer. Extract entities accurately."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.1  # Low temperature for consistent extraction
                }
            )
            
            # Parse response
            content = response['message']['content']
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                entities = json.loads(json_match.group())
                return entities
            else:
                return self._fallback_entity_extraction(text)
                
        except Exception as e:
            print(f"❌ CRITICAL ERROR: Qwen extraction failed: {e}")
            print("❌ Cannot process sensitive data without local model")
            print("❌ Cloud API fallback is DISABLED for security")
            sys.exit(1)
    
    def _fallback_entity_extraction(self, text: str) -> Dict[str, List[str]]:
        """
        Fallback entity extraction using regex
        
        Args:
            text: Document text
            
        Returns:
            Dictionary of entities
        """
        entities = {
            "companies": [],
            "technologies": [],
            "numbers": [],
            "projects": [],
            "dates": []
        }
        
        # Extract companies (capitalized words)
        company_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        companies = re.findall(company_pattern, text)
        entities["companies"] = list(set(companies[:20]))  # Top 20 unique
        
        # Extract numbers (currency, percentages)
        number_pattern = r'[\$€¥][\d,]+\.?\d*[BMK]?|\d+\.?\d*%'
        numbers = re.findall(number_pattern, text)
        entities["numbers"] = list(set(numbers[:10]))
        
        # Extract dates
        date_pattern = r'\d{4}\s*Q[1-4]|\d{4}-\d{2}-\d{2}|[A-Z][a-z]+\s+\d{4}'
        dates = re.findall(date_pattern, text)
        entities["dates"] = list(set(dates[:10]))
        
        return entities
    
    def tag_sensitive_data(self, entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Tag sensitive information with [INTERNAL_DATA_XX]
        
        Args:
            entities: Extracted entities
            
        Returns:
            Tagged entities with mapping
        """
        tagged_entities = {}
        
        for entity_type, values in entities.items():
            tagged_values = []
            
            for value in values:
                # Check if sensitive (numbers, project names)
                if self._is_sensitive(value, entity_type):
                    tag = self._create_tag()
                    self.sensitive_mapping[tag] = value
                    tagged_values.append(tag)
                else:
                    tagged_values.append(value)
            
            tagged_entities[entity_type] = tagged_values
        
        return tagged_entities
    
    def _is_sensitive(self, value: str, entity_type: str) -> bool:
        """
        Determine if data is sensitive
        
        Args:
            value: Entity value
            entity_type: Type of entity
            
        Returns:
            True if sensitive
        """
        # Numbers are always sensitive
        if entity_type == "numbers":
            return True
        
        # Project names are sensitive
        if entity_type == "projects":
            return True
        
        # Specific keywords indicate sensitive data
        sensitive_keywords = ["project", "internal", "confidential", "proprietary"]
        return any(keyword in value.lower() for keyword in sensitive_keywords)
    
    def _create_tag(self) -> str:
        """
        Create unique tag for sensitive data
        
        Returns:
            Tag string like [INTERNAL_DATA_01]
        """
        self.sensitive_counter += 1
        return f"[INTERNAL_DATA_{self.sensitive_counter:02d}]"
    
    def process_pdf(
        self,
        pdf_path: str,
        extract_entities: bool = True,
        tag_sensitive: bool = True
    ) -> Dict:
        """
        Complete PDF processing pipeline
        
        Args:
            pdf_path: Path to PDF file
            extract_entities: Whether to extract entities
            tag_sensitive: Whether to tag sensitive data
            
        Returns:
            Processing results
        """
        print(f"📄 Processing PDF: {pdf_path}")
        
        # Step 1: Extract text
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return {"error": "Failed to extract text from PDF"}
        
        print(f"✅ Extracted {len(text)} characters")
        
        # Step 2: Extract entities (if enabled)
        entities = {}
        if extract_entities:
            print("🔍 Extracting entities with Qwen 2.5 Coder...")
            entities = self.extract_entities_with_qwen(text)
            print(f"✅ Extracted {sum(len(v) for v in entities.values())} entities")
        
        # Step 3: Tag sensitive data (if enabled)
        tagged_entities = entities
        if tag_sensitive and entities:
            print("🔒 Tagging sensitive information...")
            tagged_entities = self.tag_sensitive_data(entities)
            print(f"✅ Tagged {len(self.sensitive_mapping)} sensitive items")
        
        return {
            "text": text,
            "text_length": len(text),
            "entities": entities,
            "tagged_entities": tagged_entities,
            "sensitive_mapping": self.sensitive_mapping,
            "sensitive_count": len(self.sensitive_mapping)
        }
    
    def get_anonymized_summary(self, entities: Dict[str, List[str]]) -> str:
        """
        Create anonymized summary for external use
        
        Args:
            entities: Tagged entities
            
        Returns:
            Anonymized text summary
        """
        summary_parts = []
        
        if entities.get("companies"):
            companies = [c for c in entities["companies"] if not c.startswith("[INTERNAL")]
            if companies:
                summary_parts.append(f"Companies: {', '.join(companies[:5])}")
        
        if entities.get("technologies"):
            techs = [t for t in entities["technologies"] if not t.startswith("[INTERNAL")]
            if techs:
                summary_parts.append(f"Technologies: {', '.join(techs[:5])}")
        
        if entities.get("dates"):
            dates = [d for d in entities["dates"] if not d.startswith("[INTERNAL")]
            if dates:
                summary_parts.append(f"Time Period: {', '.join(dates[:3])}")
        
        return " | ".join(summary_parts) if summary_parts else "No public information available"
    
    def clear_sensitive_mapping(self):
        """Clear sensitive data mapping"""
        self.sensitive_mapping.clear()
        self.sensitive_counter = 0


def test_local_worker():
    """Test LocalWorker functionality"""
    print("=" * 60)
    print("Testing LocalWorker")
    print("=" * 60)
    
    worker = LocalWorker()
    
    # Test with sample text
    sample_text = """
    Nvidia Corporation reported Q3 2024 revenue of $18.1 billion, up 206% year-over-year.
    The company's Project Blackwell is expected to launch in 2025.
    Key partners include TSMC, Samsung, and Microsoft Azure.
    """
    
    print("\n📝 Sample Text:")
    print(sample_text)
    
    # Extract entities
    print("\n🔍 Extracting entities...")
    entities = worker.extract_entities_with_qwen(sample_text)
    print(f"Entities: {json.dumps(entities, indent=2)}")
    
    # Tag sensitive data
    print("\n🔒 Tagging sensitive data...")
    tagged = worker.tag_sensitive_data(entities)
    print(f"Tagged: {json.dumps(tagged, indent=2)}")
    print(f"Mapping: {json.dumps(worker.sensitive_mapping, indent=2)}")
    
    # Get anonymized summary
    print("\n📊 Anonymized Summary:")
    summary = worker.get_anonymized_summary(tagged)
    print(summary)


if __name__ == "__main__":
    test_local_worker()
