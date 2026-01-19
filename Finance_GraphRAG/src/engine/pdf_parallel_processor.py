"""
PDF Parallel Processor
Async parallel processing of PDF pages using GPT-4o-mini with memory protection
Optimized for 8GB RAM with Semaphore-based concurrency control
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import fitz  # PyMuPDF
from openai import AsyncOpenAI

from config import OPENAI_API_KEY, OPENAI_BASE_URL, API_MODELS


class PDFParallelProcessor:
    """
    Process PDF pages in parallel using AsyncOpenAI with memory-safe concurrency
    """
    
    def __init__(
        self,
        max_concurrent: int = 5,
        model: str = "gpt-4o-mini",
        timeout: int = 60
    ):
        """
        Initialize PDF parallel processor
        
        Args:
            max_concurrent: Maximum concurrent API calls (default: 5 for 8GB RAM)
            model: OpenAI model to use
            timeout: API call timeout in seconds
        """
        self.max_concurrent = max_concurrent
        self.model = model
        self.timeout = timeout
        self.client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )
        
        # Statistics
        self.stats = {
            "total_pages": 0,
            "processed_pages": 0,
            "failed_pages": 0,
            "total_entities": 0,
            "total_relationships": 0
        }
    
    def _build_extraction_prompt(self) -> str:
        """Build system prompt for entity/relationship extraction"""
        return """You are a business analyst extracting structured data from financial documents.

Extract entities and relationships from the provided text and return ONLY valid JSON.

Required JSON format:
{
  "entities": [
    {"name": "EntityName", "type": "ENTITY_TYPE", "properties": {"key": "value"}}
  ],
  "relationships": [
    {"source": "EntityA", "target": "EntityB", "type": "RELATIONSHIP_TYPE", "properties": {"key": "value"}}
  ]
}

Entity Types:
- COMPANY: Business organizations
- PERSON: Individuals (CEOs, executives, employees)
- PRODUCT: Products or services
- LOCATION: Geographic locations
- FINANCIAL_METRIC: Revenue, profit, market cap, etc.
- EVENT: Business events, announcements

Common Relationship Types:
- SUPPLIES, PURCHASES, COMPETES_WITH (business operations)
- HAS_CEO, EMPLOYS, LOST_EMPLOYEE, HIRED (personnel)
- HAS_DEBT, OWNS_ASSET, INVESTS_IN (financial)
- LOCATED_IN, OPERATES_IN (geographic)
- PRODUCES, MANUFACTURES (production)
- ANNOUNCED, REPORTED (events)

Return ONLY the JSON object, no additional text."""
    
    async def _process_single_page(
        self,
        page_num: int,
        page_text: str,
        semaphore: asyncio.Semaphore,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Process a single PDF page with semaphore control
        
        Args:
            page_num: Page number (1-indexed)
            page_text: Extracted text from page
            semaphore: Asyncio semaphore for concurrency control
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with page_num, entities, relationships, and status
        """
        async with semaphore:  # Limit concurrent API calls
            try:
                if progress_callback:
                    await progress_callback(page_num, "processing")
                
                # Call OpenAI API with JSON mode
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": self._build_extraction_prompt()
                            },
                            {
                                "role": "user",
                                "content": f"Extract entities and relationships from page {page_num}:\n\n{page_text[:3000]}"
                            }
                        ],
                        response_format={"type": "json_object"},  # Force JSON response
                        temperature=0.1,
                        max_tokens=2000
                    ),
                    timeout=self.timeout
                )
                
                # Parse JSON response
                content = response.choices[0].message.content
                result = json.loads(content)
                
                # Update stats
                self.stats["processed_pages"] += 1
                self.stats["total_entities"] += len(result.get("entities", []))
                self.stats["total_relationships"] += len(result.get("relationships", []))
                
                if progress_callback:
                    await progress_callback(page_num, "completed")
                
                return {
                    "page_num": page_num,
                    "status": "success",
                    "entities": result.get("entities", []),
                    "relationships": result.get("relationships", []),
                    "error": None
                }
                
            except asyncio.TimeoutError:
                self.stats["failed_pages"] += 1
                if progress_callback:
                    await progress_callback(page_num, "timeout")
                return {
                    "page_num": page_num,
                    "status": "timeout",
                    "entities": [],
                    "relationships": [],
                    "error": f"Timeout after {self.timeout}s"
                }
            except json.JSONDecodeError as e:
                self.stats["failed_pages"] += 1
                if progress_callback:
                    await progress_callback(page_num, "json_error")
                return {
                    "page_num": page_num,
                    "status": "json_error",
                    "entities": [],
                    "relationships": [],
                    "error": f"JSON parse error: {str(e)}"
                }
            except Exception as e:
                self.stats["failed_pages"] += 1
                if progress_callback:
                    await progress_callback(page_num, "error")
                return {
                    "page_num": page_num,
                    "status": "error",
                    "entities": [],
                    "relationships": [],
                    "error": str(e)
                }
    
    async def process_pdf(
        self,
        pdf_path: str,
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Process entire PDF in parallel with ordered results
        
        Args:
            pdf_path: Path to PDF file
            progress_callback: Optional async callback(page_num, status) for progress updates
            
        Returns:
            List of results ordered by page number
            [
                {
                    "page_num": 1,
                    "status": "success",
                    "entities": [...],
                    "relationships": [...],
                    "error": None
                },
                ...
            ]
        """
        # Extract all pages first
        doc = fitz.open(pdf_path)
        pages_data = []
        
        for page_num in range(1, len(doc) + 1):
            page = doc[page_num - 1]
            page_text = page.get_text()
            
            if page_text.strip():
                pages_data.append({
                    "page_num": page_num,
                    "text": page_text
                })
        
        doc.close()
        
        self.stats["total_pages"] = len(pages_data)
        
        if not pages_data:
            return []
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Process all pages in parallel
        tasks = [
            self._process_single_page(
                page_data["page_num"],
                page_data["text"],
                semaphore,
                progress_callback
            )
            for page_data in pages_data
        ]
        
        # Gather results (maintains order)
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        # Sort by page number to ensure correct order
        results_sorted = sorted(results, key=lambda x: x["page_num"])
        
        return results_sorted
    
    def get_stats(self) -> Dict[str, int]:
        """Get processing statistics"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            "total_pages": 0,
            "processed_pages": 0,
            "failed_pages": 0,
            "total_entities": 0,
            "total_relationships": 0
        }


async def test_processor():
    """Test function for development"""
    import tempfile
    
    # Create a test PDF
    doc = fitz.open()
    
    # Add 3 test pages
    for i in range(1, 4):
        page = doc.new_page()
        page.insert_text(
            (50, 50),
            f"Test Page {i}\n\nCompany XYZ reported revenue of $100M.\nCEO John Smith announced expansion plans."
        )
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        pdf_path = f.name
        doc.save(pdf_path)
    doc.close()
    
    # Test processor
    processor = PDFParallelProcessor(max_concurrent=2)
    
    async def progress_callback(page_num, status):
        print(f"📄 Page {page_num}: {status}")
    
    print("🚀 Starting parallel PDF processing...")
    results = await processor.process_pdf(pdf_path, progress_callback)
    
    print("\n📊 Results:")
    for result in results:
        print(f"\nPage {result['page_num']}: {result['status']}")
        print(f"  Entities: {len(result['entities'])}")
        print(f"  Relationships: {len(result['relationships'])}")
        if result['error']:
            print(f"  Error: {result['error']}")
    
    print(f"\n📈 Stats: {processor.get_stats()}")
    
    # Cleanup
    import os
    os.unlink(pdf_path)
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(test_processor())
