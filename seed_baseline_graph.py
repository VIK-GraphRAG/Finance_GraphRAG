"""
Seed Baseline Knowledge Graph
Constructs industry backbone graph from baseline data (JSON + PDFs)
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from neo4j import GraphDatabase

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from src.engine.extractor import KnowledgeExtractor
from src.engine.translator import CypherTranslator


class BaselineGraphBuilder:
    """
    Build baseline industry knowledge graph from:
    1. supply_chain_mapping.json (structured data)
    2. PDF documents (unstructured knowledge)
    """
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        self.extractor = KnowledgeExtractor()
        self.translator = CypherTranslator()
        self.stats = {
            'companies': 0,
            'relationships': 0,
            'pdf_entities': 0,
            'pdf_relationships': 0
        }
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()
    
    def clear_baseline_data(self):
        """Clear existing baseline data (optional, for fresh start)"""
        print("🗑️  Clearing existing baseline data...")
        
        with self.driver.session() as session:
            # Delete only baseline-tagged data
            session.run("""
                MATCH (n)
                WHERE n.source = 'baseline'
                DETACH DELETE n
            """)
        
        print("✅ Baseline data cleared")
    
    def load_json_supply_chain(self, json_path: str):
        """
        Load supply chain data from JSON
        Creates Company nodes and SUPPLIES_TO/DEPENDS_ON relationships
        """
        print(f"📊 Loading supply chain data: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        companies = data.get('companies', [])
        relationships = data.get('supply_chain_relationships', [])
        
        with self.driver.session() as session:
            # Create Company nodes
            for company in companies:
                query = """
                MERGE (c:Company {name: $name})
                SET c.ticker = $ticker,
                    c.country = $country,
                    c.industry = $industry,
                    c.market_position = $market_position,
                    c.products = $products,
                    c.source = 'baseline',
                    c.updated_at = datetime()
                """
                
                session.run(
                    query,
                    name=company['name'],
                    ticker=company.get('ticker', ''),
                    country=company.get('country', ''),
                    industry=company.get('industry', ''),
                    market_position=company.get('market_position', ''),
                    products=company.get('products', [])
                )
                
                self.stats['companies'] += 1
            
            print(f"✅ Created {self.stats['companies']} Company nodes")
            
            # Create supply chain relationships
            for rel in relationships:
                rel_type = rel.get('relationship', 'SUPPLIES_TO')
                
                query = f"""
                MATCH (a:Company {{name: $from_name}})
                MATCH (b:Company {{name: $to_name}})
                MERGE (a)-[r:{rel_type}]->(b)
                SET r.product = $product,
                    r.criticality = $criticality,
                    r.dependency_level = $dependency_level,
                    r.notes = $notes,
                    r.source = 'baseline',
                    r.updated_at = datetime()
                """
                
                session.run(
                    query,
                    from_name=rel['from'],
                    to_name=rel['to'],
                    product=rel.get('product', ''),
                    criticality=rel.get('criticality', 'medium'),
                    dependency_level=rel.get('dependency_level', 0.5),
                    notes=rel.get('notes', '')
                )
                
                self.stats['relationships'] += 1
            
            print(f"✅ Created {self.stats['relationships']} supply chain relationships")
    
    async def ingest_pdf_knowledge(self, pdf_path: str, category: str):
        """
        Extract knowledge from baseline PDFs
        
        Args:
            pdf_path: Path to PDF file
            category: Type of knowledge (risk_factors, regulations, tech_roadmap)
        """
        print(f"📄 Processing PDF: {pdf_path} (category: {category})")
        
        try:
            import fitz  # PyMuPDF
        except ImportError:
            print("⚠️  PyMuPDF not installed. Run: pip install pymupdf")
            return
        
        # Read PDF text
        doc = fitz.open(pdf_path)
        full_text = ""
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            full_text += page.get_text()
        
        doc.close()
        
        # Process in chunks (500 characters for 8GB RAM optimization)
        chunk_size = 500
        chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
        
        print(f"   Processing {len(chunks)} chunks...")
        
        all_entities = []
        all_relationships = []
        
        for i, chunk in enumerate(chunks[:20]):  # Limit to first 20 chunks for baseline
            if i % 5 == 0:
                print(f"   Chunk {i+1}/{min(20, len(chunks))}...")
            
            try:
                # Extract entities and relationships
                extracted = await self.extractor.extract_entities(chunk)
                
                if extracted:
                    all_entities.extend(extracted.get('entities', []))
                    all_relationships.extend(extracted.get('relationships', []))
            
            except Exception as e:
                print(f"⚠️  Error processing chunk {i}: {e}")
                continue
        
        # Store entities based on category
        with self.driver.session() as session:
            for entity in all_entities:
                entity_name = entity.get('name', '')
                entity_type = entity.get('type', 'Entity')
                
                # Determine node label based on category
                if category == 'risk_factors':
                    node_label = 'RiskFactor'
                elif category == 'regulations':
                    node_label = 'Regulation'
                elif category == 'tech_roadmap':
                    node_label = 'Technology'
                else:
                    node_label = entity_type
                
                query = f"""
                MERGE (e:{node_label} {{name: $name}})
                SET e.category = $category,
                    e.description = $description,
                    e.source = 'baseline',
                    e.source_file = $source_file,
                    e.updated_at = datetime()
                """
                
                session.run(
                    query,
                    name=entity_name,
                    category=category,
                    description=entity.get('description', '')[:500],
                    source_file=Path(pdf_path).name
                )
                
                self.stats['pdf_entities'] += 1
            
            # Create relationships
            for rel in all_relationships:
                source = rel.get('source', '')
                target = rel.get('target', '')
                rel_type = rel.get('type', 'RELATED_TO')
                
                if not source or not target:
                    continue
                
                # Sanitize relationship type
                rel_type = rel_type.upper().replace(' ', '_').replace('-', '_')
                
                query = f"""
                MATCH (a {{name: $source}})
                MATCH (b {{name: $target}})
                MERGE (a)-[r:{rel_type}]->(b)
                SET r.context = $context,
                    r.source = 'baseline',
                    r.updated_at = datetime()
                """
                
                try:
                    session.run(
                        query,
                        source=source,
                        target=target,
                        context=rel.get('context', '')[:300]
                    )
                    
                    self.stats['pdf_relationships'] += 1
                
                except Exception as e:
                    # Skip if relationship type is invalid
                    continue
        
        print(f"✅ Extracted {self.stats['pdf_entities']} entities, {self.stats['pdf_relationships']} relationships")
    
    def create_industry_structure(self):
        """
        Create high-level industry structure nodes
        (Industry sectors, countries, macro indicators)
        """
        print("🏗️  Creating industry structure...")
        
        with self.driver.session() as session:
            # Create Industry sectors
            industries = [
                {'name': 'Semiconductor Equipment', 'description': 'Lithography, deposition, etching systems'},
                {'name': 'Semiconductor Foundry', 'description': 'Contract chip manufacturing'},
                {'name': 'Semiconductor IDM', 'description': 'Integrated device manufacturers'},
                {'name': 'Memory Chips', 'description': 'DRAM, NAND, HBM production'},
                {'name': 'GPU & AI Chips', 'description': 'Graphics processors and AI accelerators'},
                {'name': 'Cloud Service Provider', 'description': 'Hyperscale cloud infrastructure'},
            ]
            
            for industry in industries:
                session.run("""
                    MERGE (i:Industry {name: $name})
                    SET i.description = $description,
                        i.source = 'baseline',
                        i.updated_at = datetime()
                """, **industry)
            
            # Create Country nodes
            countries = ['USA', 'Taiwan', 'Netherlands', 'South Korea', 'China', 'Japan', 'Germany']
            
            for country in countries:
                session.run("""
                    MERGE (c:Country {name: $name})
                    SET c.source = 'baseline',
                        c.updated_at = datetime()
                """, name=country)
            
            # Link companies to industries and countries
            session.run("""
                MATCH (c:Company)
                WHERE c.industry IS NOT NULL
                MATCH (i:Industry)
                WHERE i.name = c.industry
                MERGE (c)-[r:OPERATES_IN]->(i)
                SET r.source = 'baseline'
            """)
            
            session.run("""
                MATCH (c:Company)
                WHERE c.country IS NOT NULL
                MATCH (co:Country)
                WHERE co.name = c.country
                MERGE (c)-[r:LOCATED_IN]->(co)
                SET r.source = 'baseline'
            """)
            
            # Create macro indicators
            macro_indicators = [
                {
                    'name': 'US-China Trade War',
                    'type': 'geopolitical',
                    'severity': 0.85,
                    'description': 'Technology decoupling and export controls'
                },
                {
                    'name': 'Taiwan Strait Tension',
                    'type': 'geopolitical',
                    'severity': 0.95,
                    'description': 'Military conflict risk affecting TSMC'
                },
                {
                    'name': 'Interest Rate Volatility',
                    'type': 'economic',
                    'severity': 0.65,
                    'description': 'Impact on CAPEX and valuations'
                },
                {
                    'name': 'Power Supply Constraints',
                    'type': 'infrastructure',
                    'severity': 0.70,
                    'description': 'Data center and fab power limitations'
                },
            ]
            
            for indicator in macro_indicators:
                session.run("""
                    MERGE (m:MacroIndicator {name: $name})
                    SET m.type = $type,
                        m.severity = $severity,
                        m.description = $description,
                        m.source = 'baseline',
                        m.updated_at = datetime()
                """, **indicator)
            
            # Link macro indicators to affected industries/countries
            session.run("""
                MATCH (m:MacroIndicator {name: 'Taiwan Strait Tension'})
                MATCH (c:Country {name: 'Taiwan'})
                MERGE (m)-[r:AFFECTS]->(c)
                SET r.severity = 0.95, r.source = 'baseline'
            """)
            
            session.run("""
                MATCH (m:MacroIndicator {name: 'US-China Trade War'})
                MATCH (i:Industry {name: 'Semiconductor Equipment'})
                MERGE (m)-[r:IMPACTS]->(i)
                SET r.severity = 0.85, r.impact_type = 'export restrictions', r.source = 'baseline'
            """)
            
            print("✅ Industry structure created")
    
    def print_stats(self):
        """Print build statistics"""
        print("\n" + "="*60)
        print("📊 Baseline Graph Construction Stats")
        print("="*60)
        print(f"Companies: {self.stats['companies']}")
        print(f"Supply Chain Relationships: {self.stats['relationships']}")
        print(f"PDF-extracted Entities: {self.stats['pdf_entities']}")
        print(f"PDF-extracted Relationships: {self.stats['pdf_relationships']}")
        print("="*60)


async def main():
    """Main execution"""
    print("🚀 Building Baseline Knowledge Graph")
    print("="*60)
    
    builder = BaselineGraphBuilder()
    
    # Optional: Clear existing data for fresh start
    # Uncomment if you want to rebuild from scratch
    # builder.clear_baseline_data()
    
    # Step 1: Load JSON supply chain data
    json_path = "data/baseline/supply_chain_mapping.json"
    if Path(json_path).exists():
        builder.load_json_supply_chain(json_path)
    else:
        print(f"⚠️  {json_path} not found, skipping")
    
    # Step 2: Create industry structure
    builder.create_industry_structure()
    
    # Step 3: Ingest PDF knowledge (skip for now - Ollama may not be running)
    print("\n📄 PDF Knowledge Ingestion")
    print("⚠️  Skipping PDF extraction (requires Ollama server)")
    print("💡 To enable PDF processing:")
    print("   1. Start Ollama: ollama serve")
    print("   2. Pull model: ollama pull qwen2.5-coder:3b")
    print("   3. Re-run this script")
    
    # Uncomment when Ollama is available:
    # pdf_mappings = [
    #     ('data/baseline/industry_risk_factors.pdf', 'risk_factors'),
    #     ('data/baseline/regulation_guidelines.pdf', 'regulations'),
    #     ('data/baseline/tech_roadmap.pdf', 'tech_roadmap'),
    # ]
    # 
    # for pdf_path, category in pdf_mappings:
    #     if Path(pdf_path).exists():
    #         await builder.ingest_pdf_knowledge(pdf_path, category)
    #     else:
    #         print(f"⚠️  {pdf_path} not found, skipping")
    
    # Print final statistics
    builder.print_stats()
    
    builder.close()
    
    print("\n✅ Baseline graph construction complete!")
    print("💡 Next step: Run Streamlit app to query the graph")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
