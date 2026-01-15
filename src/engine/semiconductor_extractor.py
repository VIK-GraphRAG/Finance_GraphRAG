"""
Semiconductor-Specific Multi-Hop Causal Relationship Extractor
반도체 전용 멀티홉 인과관계 추출기
"""

import json
from typing import List, Dict, Any
from openai import AsyncOpenAI
import asyncio

from config import OPENAI_API_KEY, OPENAI_BASE_URL


class SemiconductorCausalExtractor:
    """
    Extract multi-hop causal relationships from semiconductor industry documents
    전이 리스크(Transitive Risk) 추출: A → B → C 형태의 3단계 논리 구조
    """
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )
        self.model = "gpt-4o-mini"
    
    async def extract_causal_chain(self, text_chunk: str, context: Dict = None) -> Dict[str, Any]:
        """
        Extract multi-hop causal relationships from text
        
        Args:
            text_chunk: Text to analyze (max 500 chars for 8GB RAM)
            context: Additional context (file name, page number, etc.)
        
        Returns:
            {
                'causal_chains': [
                    {
                        'trigger': {...},  # A: 최초 원인
                        'intermediate': {...},  # B: 중간 매개
                        'consequence': {...},  # C: 최종 결과
                        'confidence': float,
                        'chain_type': str
                    }
                ],
                'entities': [...],
                'relationships': [...]
            }
        """
        
        system_prompt = """You are an expert in semiconductor supply chain analysis.

Your task: Extract multi-hop causal relationships (전이 리스크) from text.

CRITICAL: Focus on 3-stage logic: A causes B, B causes C, therefore A leads to C.

Output JSON structure:
{
  "causal_chains": [
    {
      "trigger": {
        "entity": "Entity name",
        "type": "Geopolitics|Company|Process|Component",
        "description": "What initiates the chain"
      },
      "intermediate": {
        "entity": "Entity name",
        "type": "Process|Company|Component",
        "description": "What gets affected first"
      },
      "consequence": {
        "entity": "Entity name",
        "type": "Company|Financials|Component",
        "description": "Final impact"
      },
      "chain_logic": "Explain A→B→C logic in one sentence",
      "confidence": 0.0-1.0,
      "chain_type": "supply_disruption|export_control|capacity_constraint|technology_ban"
    }
  ],
  "entities": [
    {
      "name": "Entity name",
      "type": "Company|Process|Component|Geopolitics|Financials",
      "attributes": {...}
    }
  ],
  "relationships": [
    {
      "from": "Entity A",
      "to": "Entity B",
      "type": "DEPENDS_ON|DISRUPTS|PRODUCES|REQUIRES_PROCESS",
      "properties": {...}
    }
  ]
}

Examples of causal chains to extract:

1. Supply Disruption:
"Taiwan earthquake → TSMC fab damage → Nvidia GPU shortage"
{
  "trigger": {"entity": "Taiwan Earthquake", "type": "Geopolitics"},
  "intermediate": {"entity": "TSMC", "type": "Company"},
  "consequence": {"entity": "Nvidia", "type": "Company"},
  "chain_logic": "Earthquake damages TSMC fabs, which are critical for Nvidia GPU production, leading to supply shortage",
  "chain_type": "supply_disruption"
}

2. Export Control:
"US chip ban → ASML EUV restriction → China foundry technology lag"
{
  "trigger": {"entity": "US Export Control", "type": "Geopolitics"},
  "intermediate": {"entity": "EUV Lithography", "type": "Process"},
  "consequence": {"entity": "SMIC", "type": "Company"},
  "chain_logic": "US restricts ASML EUV sales to China, blocking access to advanced process, causing technology gap",
  "chain_type": "export_control"
}

3. Capacity Constraint:
"AI boom → CoWoS demand surge → TSMC capacity bottleneck"
{
  "trigger": {"entity": "AI Boom", "type": "Geopolitics"},
  "intermediate": {"entity": "CoWoS Package", "type": "Component"},
  "consequence": {"entity": "TSMC", "type": "Company"},
  "chain_logic": "AI chip demand increases CoWoS package需求, but TSMC has limited capacity, creating bottleneck",
  "chain_type": "capacity_constraint"
}

Focus on:
- Geopolitical risks → Manufacturing disruptions → Company financials
- Export controls → Technology access → Competitive disadvantage
- Natural disasters → Fab shutdowns → Supply chain chaos
- Equipment restrictions → Process limitations → Product delays

Extract ONLY if clear 3-stage causality exists. Minimum confidence: 0.7"""

        user_message = f"""Text to analyze:
```
{text_chunk}
```

Context: {json.dumps(context or {}, ensure_ascii=False)}

Extract multi-hop causal chains following A→B→C logic."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                timeout=60
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate causal chains
            valid_chains = [
                chain for chain in result.get('causal_chains', [])
                if chain.get('confidence', 0) >= 0.7
            ]
            
            result['causal_chains'] = valid_chains
            
            print(f"✅ Extracted {len(valid_chains)} causal chains")
            return result
            
        except Exception as e:
            print(f"⚠️  Extraction failed: {e}")
            return {
                'causal_chains': [],
                'entities': [],
                'relationships': []
            }
    
    async def extract_from_pdf(
        self, 
        pdf_chunks: List[str], 
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        Extract causal chains from multiple PDF chunks in parallel
        
        Args:
            pdf_chunks: List of text chunks from PDF
            max_concurrent: Max concurrent API calls (8GB RAM limit)
        
        Returns:
            Aggregated extraction results
        """
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_chunk(chunk: str, index: int):
            async with semaphore:
                context = {'chunk_index': index, 'source': 'PDF'}
                return await self.extract_causal_chain(chunk, context)
        
        print(f"🔍 Processing {len(pdf_chunks)} chunks (max {max_concurrent} concurrent)")
        
        tasks = [process_chunk(chunk, i) for i, chunk in enumerate(pdf_chunks)]
        results = await asyncio.gather(*tasks)
        
        # Aggregate results
        all_chains = []
        all_entities = []
        all_relationships = []
        
        for result in results:
            all_chains.extend(result.get('causal_chains', []))
            all_entities.extend(result.get('entities', []))
            all_relationships.extend(result.get('relationships', []))
        
        # Deduplicate entities
        unique_entities = {e['name']: e for e in all_entities}.values()
        
        return {
            'causal_chains': all_chains,
            'entities': list(unique_entities),
            'relationships': all_relationships,
            'summary': {
                'total_chains': len(all_chains),
                'chain_types': self._count_chain_types(all_chains),
                'avg_confidence': sum(c.get('confidence', 0) for c in all_chains) / max(len(all_chains), 1)
            }
        }
    
    def _count_chain_types(self, chains: List[Dict]) -> Dict[str, int]:
        """Count causal chain types"""
        types = {}
        for chain in chains:
            chain_type = chain.get('chain_type', 'unknown')
            types[chain_type] = types.get(chain_type, 0) + 1
        return types
    
    def generate_cypher_from_chains(self, chains: List[Dict]) -> List[str]:
        """
        Generate Cypher queries from causal chains to populate Neo4j
        
        Returns:
            List of Cypher CREATE/MERGE statements
        """
        
        cypher_queries = []
        
        for chain in chains:
            trigger = chain.get('trigger', {})
            intermediate = chain.get('intermediate', {})
            consequence = chain.get('consequence', {})
            
            # Create nodes
            trigger_query = f"""
            MERGE (t:{trigger['type']} {{name: '{trigger['entity']}'}})
            SET t.description = '{trigger.get('description', '')}',
                t.last_updated = datetime()
            """
            cypher_queries.append(trigger_query)
            
            intermediate_query = f"""
            MERGE (i:{intermediate['type']} {{name: '{intermediate['entity']}'}})
            SET i.description = '{intermediate.get('description', '')}',
                i.last_updated = datetime()
            """
            cypher_queries.append(intermediate_query)
            
            consequence_query = f"""
            MERGE (c:{consequence['type']} {{name: '{consequence['entity']}'}})
            SET c.description = '{consequence.get('description', '')}',
                c.last_updated = datetime()
            """
            cypher_queries.append(consequence_query)
            
            # Create relationships (A→B→C)
            rel1_query = f"""
            MATCH (t:{trigger['type']} {{name: '{trigger['entity']}'}}),
                  (i:{intermediate['type']} {{name: '{intermediate['entity']}'}})
            MERGE (t)-[r1:CAUSES {{
                confidence: {chain.get('confidence', 0.8)},
                chain_type: '{chain.get('chain_type', 'unknown')}',
                hop: 1
            }}]->(i)
            """
            cypher_queries.append(rel1_query)
            
            rel2_query = f"""
            MATCH (i:{intermediate['type']} {{name: '{intermediate['entity']}'}}),
                  (c:{consequence['type']} {{name: '{consequence['entity']}'}})
            MERGE (i)-[r2:LEADS_TO {{
                confidence: {chain.get('confidence', 0.8)},
                chain_type: '{chain.get('chain_type', 'unknown')}',
                hop: 2
            }}]->(c)
            """
            cypher_queries.append(rel2_query)
            
            # Create transitive relationship (A→C)
            transitive_query = f"""
            MATCH (t:{trigger['type']} {{name: '{trigger['entity']}'}}),
                  (c:{consequence['type']} {{name: '{consequence['entity']}'}})
            MERGE (t)-[r:TRANSITIVE_IMPACT {{
                via: '{intermediate['entity']}',
                confidence: {chain.get('confidence', 0.8)},
                chain_logic: '{chain.get('chain_logic', '')}',
                chain_type: '{chain.get('chain_type', 'unknown')}'
            }}]->(c)
            """
            cypher_queries.append(transitive_query)
        
        return cypher_queries


async def example_usage():
    """Example: Extract causal chains from semiconductor text"""
    
    extractor = SemiconductorCausalExtractor()
    
    # Sample text
    sample_text = """
    The recent Taiwan Strait military tension has raised concerns about TSMC's 
    fab operations. TSMC manufactures over 90% of advanced chips for Nvidia's 
    H100 GPUs. Any disruption to TSMC's 4nm process would directly impact 
    Nvidia's data center revenue, which accounts for $47.5 billion annually.
    
    Meanwhile, US export controls on ASML's EUV lithography equipment to China
    have blocked SMIC's access to advanced process technology, creating a 
    multi-generation technology gap that affects China's domestic AI chip
    development capability.
    """
    
    result = await extractor.extract_causal_chain(sample_text)
    
    print("\n📊 Extraction Results:")
    print(f"Causal Chains: {len(result['causal_chains'])}")
    
    for i, chain in enumerate(result['causal_chains'], 1):
        print(f"\n Chain {i}:")
        print(f"  Trigger: {chain['trigger']['entity']} ({chain['trigger']['type']})")
        print(f"  → Intermediate: {chain['intermediate']['entity']}")
        print(f"  → Consequence: {chain['consequence']['entity']}")
        print(f"  Logic: {chain['chain_logic']}")
        print(f"  Confidence: {chain['confidence']:.1%}")
    
    # Generate Cypher
    cypher_queries = extractor.generate_cypher_from_chains(result['causal_chains'])
    print(f"\n🔗 Generated {len(cypher_queries)} Cypher queries")


if __name__ == "__main__":
    asyncio.run(example_usage())
