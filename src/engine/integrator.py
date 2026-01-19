"""
Data Integrator: Merge PDF knowledge with structured data (CSV/JSON)
Handles entity resolution and deduplication

SECURITY POLICY:
- All PDF processing must use local Qwen 2.5 Coder
- No cloud API access for sensitive data
- Verify local model before processing
"""

import json
import csv
import re
from typing import Dict, List, Any, Set, Tuple, Optional
from pathlib import Path
from neo4j import GraphDatabase
from datetime import datetime

try:
    from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
    from engine.connection_check import check_local_model_before_processing
except ImportError:
    from ..config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
    from .connection_check import check_local_model_before_processing

try:
    from utils.error_logger import droneLogError
except Exception:
    def droneLogError(message: str, error: Exception | None = None) -> None:
        return


class EntityResolver:
    """
    Resolve entity aliases to canonical names
    Example: 'NVDA', 'Nvidia', 'NVIDIA Corporation' → 'Nvidia'
    
    Enhanced with baseline graph lookup for ticker-based matching
    """
    
    # Known aliases for common entities
    ALIASES = {
        'Nvidia': ['NVDA', 'nvidia', 'NVIDIA', 'Nvidia Corporation', 'NVIDIA Corp'],
        'TSMC': ['TSM', 'tsmc', 'Taiwan Semiconductor', 'Taiwan Semiconductor Manufacturing'],
        'Intel': ['INTC', 'intel', 'Intel Corporation', 'Intel Corp'],
        'AMD': ['amd', 'Advanced Micro Devices', 'AMD Inc'],
        'Apple': ['AAPL', 'apple', 'Apple Inc', 'Apple Inc.'],
        'Microsoft': ['MSFT', 'microsoft', 'Microsoft Corporation', 'Microsoft Corp'],
        'ASML': ['ASML', 'asml', 'ASML Holding'],
        'SK Hynix': ['000660.KS', 'SK hynix', 'SK Hynix Inc'],
        'Samsung Electronics': ['005930.KS', 'Samsung', 'Samsung Elec'],
        'Micron': ['MU', 'micron', 'Micron Technology'],
        'Applied Materials': ['AMAT', 'Applied Materials Inc'],
        'AWS': ['AMZN', 'Amazon Web Services', 'Amazon AWS'],
        'Microsoft Azure': ['MSFT', 'Azure', 'MS Azure'],
        'Google Cloud': ['GOOGL', 'GCP', 'Google Cloud Platform'],
    }
    
    @classmethod
    def resolve(cls, entity_name: str) -> str:
        """
        Resolve entity name to canonical form
        
        Args:
            entity_name: Raw entity name from data
        
        Returns:
            Canonical entity name
        """
        entity_clean = entity_name.strip()
        
        # Check against known aliases
        for canonical, aliases in cls.ALIASES.items():
            if entity_clean in aliases or entity_clean == canonical:
                return canonical
        
        # Fuzzy matching for unknown entities
        entity_lower = entity_clean.lower()
        for canonical, aliases in cls.ALIASES.items():
            for alias in aliases:
                if alias.lower() in entity_lower or entity_lower in alias.lower():
                    return canonical
        
        # Return as-is if no match
        return entity_clean
    
    @classmethod
    def add_alias(cls, canonical: str, aliases: List[str]):
        """Add new alias mapping"""
        if canonical not in cls.ALIASES:
            cls.ALIASES[canonical] = []
        cls.ALIASES[canonical].extend(aliases)
    
    @classmethod
    def resolve_with_baseline(cls, entity_name: str, neo4j_session) -> str:
        """
        Enhanced resolution using baseline graph lookup
        
        Args:
            entity_name: Raw entity name
            neo4j_session: Neo4j session for baseline lookup
        
        Returns:
            Canonical entity name (from baseline if found)
        """
        # First try local alias resolution
        resolved = cls.resolve(entity_name)
        
        # If no local match, try baseline graph ticker/name lookup
        if resolved == entity_name.strip():
            # Check if baseline graph has this ticker or name
            query = """
            MATCH (c:Company)
            WHERE c.ticker = $search_term 
               OR c.name = $search_term
               OR toLower(c.name) CONTAINS toLower($search_term)
            RETURN c.name as canonical_name
            LIMIT 1
            """
            
            result = neo4j_session.run(query, search_term=entity_name.strip())
            record = result.single()
            
            if record:
                return record['canonical_name']
        
        return resolved


class DataIntegrator:
    """
    Integrate multiple data sources into Neo4j knowledge graph
    - PDF extracted entities
    - CSV structured data
    - JSON indicator data
    """
    
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
            )
        except Exception as e:
            droneLogError("Neo4j driver initialization failed", e)
            raise
        self.resolver = EntityResolver()
        self.stats = {
            'entities_merged': 0,
            'relationships_created': 0,
            'csv_records': 0,
            'json_records': 0,
            'pdf_chunks': 0
        }

    def sanitizeLabel(self, label: str) -> str:
        """
        Sanitize Neo4j label to avoid injection
        """
        cleanLabel = re.sub(r'[^A-Za-z0-9_]', '', str(label))
        return cleanLabel if cleanLabel else "Entity"

    def sanitizeRelType(self, relType: str) -> str:
        """
        Sanitize Neo4j relationship type to avoid injection
        """
        cleanRelType = re.sub(r'[^A-Za-z0-9_]', '', str(relType).upper())
        return cleanRelType if cleanRelType else "RELATED"

    def normalizeEntityType(self, entityType: str) -> str:
        """
        Normalize entity type to Neo4j label
        """
        typeMap = {
            "COMPANY": "Company",
            "PERSON": "Person",
            "PRODUCT": "Product",
            "LOCATION": "Location",
            "FINANCIAL_METRIC": "FinancialMetric",
            "REGULATION": "Regulation",
            "CATALYST": "Catalyst",
            "RISK": "Risk",
            "TECH": "Technology"
        }
        return typeMap.get(str(entityType).upper(), "Entity")

    def filterProperties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter properties to Neo4j-safe primitive values
        """
        safeProps: Dict[str, Any] = {}
        for key, value in properties.items():
            if isinstance(value, (str, int, float, bool)):
                safeProps[key] = value
            else:
                safeProps[key] = str(value)
        return safeProps
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()
    
    def merge_entity(
        self,
        name: str,
        entity_type: str,
        properties: Dict[str, Any] = None
    ) -> str:
        """
        Merge entity into Neo4j (create or update)
        
        Args:
            name: Entity name (will be resolved)
            entity_type: Node label (Company, Country, etc.)
            properties: Additional properties
        
        Returns:
            Canonical entity name
        """
        canonical_name = self.resolver.resolve(name)
        props = properties or {}
        
        # Build SET clause for properties
        set_clauses = []
        for key, value in props.items():
            if isinstance(value, (int, float)):
                set_clauses.append(f"e.{key} = {value}")
            elif isinstance(value, str):
                safe_value = value.replace("'", "\\'")
                set_clauses.append(f"e.{key} = '{safe_value}'")
        
        set_clause = ", ".join(set_clauses) if set_clauses else "e.updated_at = datetime()"
        
        query = f"""
        MERGE (e:{entity_type} {{name: '{canonical_name}'}})
        SET {set_clause}
        RETURN e.name as name
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            self.stats['entities_merged'] += 1
            return canonical_name
    
    def create_relationship(
        self,
        from_entity: str,
        to_entity: str,
        rel_type: str,
        properties: Dict[str, Any] = None
    ):
        """Create relationship between entities"""
        from_canonical = self.resolver.resolve(from_entity)
        to_canonical = self.resolver.resolve(to_entity)
        
        props = properties or {}
        prop_str = ", ".join([
            f"{k}: {repr(v)}" for k, v in props.items()
        ])
        
        query = f"""
        MATCH (a {{name: '{from_canonical}'}})
        MATCH (b {{name: '{to_canonical}'}})
        MERGE (a)-[r:{rel_type} {{{prop_str}}}]->(b)
        RETURN type(r) as rel_type
        """
        
        with self.driver.session() as session:
            session.run(query)
            self.stats['relationships_created'] += 1
    
    def ingest_csv(self, csv_path: str, mapping: Dict[str, str]):
        """
        Ingest CSV file with column mapping
        
        Args:
            csv_path: Path to CSV file
            mapping: Column mapping, e.g.
                {
                    'company_name': 'entity_name',
                    'revenue': 'property',
                    'market_cap': 'property'
                }
        """
        print(f"📊 Ingesting CSV: {csv_path}")
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Extract entity name
                entity_name = None
                for col, mapping_type in mapping.items():
                    if mapping_type == 'entity_name' and col in row:
                        entity_name = row[col]
                        break
                
                if not entity_name:
                    continue
                
                # Extract properties
                properties = {}
                for col, mapping_type in mapping.items():
                    if mapping_type == 'property' and col in row:
                        value = row[col]
                        # Try to convert to number
                        try:
                            if '.' in value:
                                properties[col] = float(value)
                            else:
                                properties[col] = int(value)
                        except:
                            properties[col] = value
                
                # Merge entity
                self.merge_entity(
                    name=entity_name,
                    entity_type='Company',  # Default to Company
                    properties=properties
                )
                
                self.stats['csv_records'] += 1
        
        print(f"✅ Ingested {self.stats['csv_records']} records from CSV")
    
    def ingest_json(self, json_path: str, schema: Dict[str, Any]):
        """
        Ingest JSON file with schema definition
        
        Args:
            json_path: Path to JSON file
            schema: Schema definition, e.g.
                {
                    'root': 'companies',  # JSON root key
                    'entity_key': 'name',
                    'entity_type': 'Company',
                    'relationships': [
                        {
                            'type': 'LOCATED_IN',
                            'target_key': 'country',
                            'target_type': 'Country'
                        }
                    ]
                }
        """
        print(f"📄 Ingesting JSON: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Navigate to root
        if 'root' in schema and schema['root']:
            items = data.get(schema['root'], [])
        else:
            items = data if isinstance(data, list) else [data]
        
        for item in items:
            # Extract entity
            entity_name = item.get(schema['entity_key'])
            if not entity_name:
                continue
            
            # Extract properties
            properties = {
                k: v for k, v in item.items()
                if k not in [schema['entity_key'], 'relationships']
                and not isinstance(v, (dict, list))
            }
            
            # Merge entity
            canonical = self.merge_entity(
                name=entity_name,
                entity_type=schema.get('entity_type', 'Entity'),
                properties=properties
            )
            
            # Create relationships
            if 'relationships' in schema:
                for rel_schema in schema['relationships']:
                    target_name = item.get(rel_schema['target_key'])
                    if target_name:
                        # Ensure target exists
                        self.merge_entity(
                            name=target_name,
                            entity_type=rel_schema['target_type'],
                            properties={}
                        )
                        
                        # Create relationship
                        self.create_relationship(
                            from_entity=canonical,
                            to_entity=target_name,
                            rel_type=rel_schema['type'],
                            properties=rel_schema.get('properties', {})
                        )
            
            self.stats['json_records'] += 1
        
        print(f"✅ Ingested {self.stats['json_records']} records from JSON")
    
    def ingest_pdf_entities(self, entities: List[Dict[str, Any]]):
        """
        Ingest entities extracted from PDF
        
        SECURITY: This function handles sensitive data from PDFs
        - Must verify local model processed this data
        - No cloud API fallback allowed
        
        Args:
            entities: List of entities from KnowledgeExtractor
                [
                    {'name': 'Nvidia', 'type': 'Company', 'context': '...'},
                    ...
                ]
        """
        # SECURITY CHECK: Verify local model is available
        print("🔒 SECURITY: Verifying local model before PDF data ingestion...")
        check_local_model_before_processing()
        
        print(f"📚 Ingesting {len(entities)} entities from PDF")
        
        for entity in entities:
            name = entity.get('name')
            entity_type = entity.get('type', 'Entity')
            
            properties = {
                'source': 'PDF',
                'context': entity.get('context', '')[:500]  # Limit context
            }
            
            self.merge_entity(
                name=name,
                entity_type=entity_type,
                properties=properties
            )
            
            self.stats['pdf_chunks'] += 1
        
        print(f"✅ Merged {self.stats['pdf_chunks']} PDF entities")

    def ingestPdfGraph(
        self,
        graphData: Dict[str, Any],
        sourceFile: str,
        sourceLabel: str
    ) -> Dict[str, int]:
        """
        Ingest PDF graph data (entities + relationships) into Neo4j

        Args:
            graphData: Dict with 'entities' and 'relationships'
            sourceFile: Original PDF filename
            sourceLabel: Source label for provenance
        """
        try:
            entities = graphData.get("entities", [])
            relationships = graphData.get("relationships", [])
            localStats = {
                "entitiesMerged": 0,
                "relationshipsCreated": 0
            }

            with self.driver.session() as session:
                for entity in entities:
                    name = entity.get("name")
                    if not name:
                        continue

                    entityType = self.normalizeEntityType(entity.get("type", "Entity"))
                    label = self.sanitizeLabel(entityType)
                    rawProps = entity.get("properties", {}) if isinstance(entity.get("properties"), dict) else {}
                    properties = self.filterProperties(rawProps)
                    canonicalName = self.resolver.resolve(name)

                    query = f"""
                    MERGE (e:{label} {{name: $name}})
                    SET e += $props,
                        e.source = $source,
                        e.source_label = $sourceLabel,
                        e.source_file = $sourceFile,
                        e.updated_at = datetime()
                    """
                    session.run(
                        query,
                        name=canonicalName,
                        props=properties,
                        source="pdf",
                        sourceLabel=sourceLabel,
                        sourceFile=sourceFile
                    )
                    localStats["entitiesMerged"] += 1

                for rel in relationships:
                    source = rel.get("source")
                    target = rel.get("target")
                    if not source or not target:
                        continue

                    relType = self.sanitizeRelType(rel.get("type", "RELATED"))
                    rawRelProps = rel.get("properties", {}) if isinstance(rel.get("properties"), dict) else {}
                    relProps = self.filterProperties(rawRelProps)

                    query = f"""
                    MERGE (a {{name: $source}})
                    MERGE (b {{name: $target}})
                    MERGE (a)-[r:{relType}]->(b)
                    SET r += $props,
                        r.source = $sourceLabel,
                        r.source_file = $sourceFile,
                        r.updated_at = datetime()
                    """
                    session.run(
                        query,
                        source=self.resolver.resolve(source),
                        target=self.resolver.resolve(target),
                        props=relProps,
                        sourceLabel=sourceLabel,
                        sourceFile=sourceFile
                    )
                    localStats["relationshipsCreated"] += 1

            self.stats["entities_merged"] += localStats["entitiesMerged"]
            self.stats["relationships_created"] += localStats["relationshipsCreated"]
            return localStats
        except Exception as e:
            droneLogError("PDF graph ingestion failed", e)
            raise
    
    def link_metrics_to_entities(
        self,
        metrics: List[Dict[str, Any]],
        entity_key: str = 'company'
    ):
        """
        Link financial metrics to company entities
        
        Args:
            metrics: List of metric records
                [
                    {'company': 'Nvidia', 'metric': 'Revenue', 'value': 60.9},
                    ...
                ]
        """
        print(f"🔗 Linking {len(metrics)} metrics to entities")
        
        for metric in metrics:
            company = metric.get(entity_key)
            if not company:
                continue
            
            # Ensure company exists
            canonical = self.merge_entity(
                name=company,
                entity_type='Company',
                properties={}
            )
            
            # Create metric node
            metric_name = metric.get('metric', 'Unknown')
            value = metric.get('value', 0)
            period = metric.get('period', 'N/A')
            
            query = f"""
            MATCH (c:Company {{name: '{canonical}'}})
            MERGE (m:FinancialMetric {{name: '{metric_name}', company: '{canonical}'}})
            SET m.value = {value},
                m.period = '{period}',
                m.updated_at = datetime()
            MERGE (c)-[r:HAS_METRIC]->(m)
            """
            
            with self.driver.session() as session:
                session.run(query)
                self.stats['relationships_created'] += 1
        
        print(f"✅ Linked {len(metrics)} metrics")
    
    def get_stats(self) -> Dict[str, int]:
        """Get integration statistics"""
        return self.stats
    
    def merge_with_baseline(
        self,
        user_entities: List[Dict[str, Any]],
        source_label: str = "user_pdf"
    ) -> Dict[str, Any]:
        """
        Merge user PDF entities with baseline graph
        
        Strategy:
        1. Use ticker-based matching to find existing baseline nodes
        2. Merge new information into existing nodes (don't overwrite)
        3. Create new nodes for entities not in baseline
        4. Link new entities to baseline structure when possible
        
        Args:
            user_entities: Entities extracted from user PDF
            source_label: Label for source tracking
        
        Returns:
            Merge statistics
        """
        print(f"🔗 Merging {len(user_entities)} user entities with baseline graph...")
        
        merge_stats = {
            'matched_to_baseline': 0,
            'new_entities': 0,
            'relationships_added': 0,
            'properties_updated': 0
        }
        
        with self.driver.session() as session:
            for entity in user_entities:
                entity_name = entity.get('name', '')
                entity_type = entity.get('type', 'Entity')
                context = entity.get('context', '')
                
                if not entity_name:
                    continue
                
                # Resolve entity name using baseline graph
                canonical_name = EntityResolver.resolve_with_baseline(
                    entity_name,
                    session
                )
                
                # Check if entity exists in baseline
                check_query = """
                MATCH (n {name: $name})
                WHERE n.source = 'baseline'
                RETURN n, labels(n)[0] as label
                LIMIT 1
                """
                
                result = session.run(check_query, name=canonical_name)
                record = result.single()
                
                if record:
                    # Entity exists in baseline - merge new information
                    merge_stats['matched_to_baseline'] += 1
                    
                    node_label = record['label']
                    
                    # Add user context as additional property
                    update_query = f"""
                    MATCH (n:{node_label} {{name: $name}})
                    SET n.user_context = COALESCE(n.user_context, '') + '\\n' + $context,
                        n.user_source = $source_label,
                        n.last_user_update = datetime()
                    """
                    
                    session.run(
                        update_query,
                        name=canonical_name,
                        context=context[:500],
                        source_label=source_label
                    )
                    
                    merge_stats['properties_updated'] += 1
                
                else:
                    # New entity not in baseline - create it
                    merge_stats['new_entities'] += 1
                    
                    create_query = f"""
                    MERGE (n:{entity_type} {{name: $name}})
                    SET n.description = $context,
                        n.source = 'user',
                        n.source_label = $source_label,
                        n.created_at = datetime()
                    """
                    
                    session.run(
                        create_query,
                        name=canonical_name,
                        context=context[:500],
                        source_label=source_label
                    )
                    
                    # Try to link to baseline structure
                    # If it's a company, link to industry/country
                    if entity_type == 'Company':
                        # Try to infer industry from context
                        self._link_to_baseline_structure(
                            session,
                            canonical_name,
                            context
                        )
        
        print(f"✅ Merge complete:")
        print(f"   - Matched to baseline: {merge_stats['matched_to_baseline']}")
        print(f"   - New entities: {merge_stats['new_entities']}")
        print(f"   - Properties updated: {merge_stats['properties_updated']}")
        
        return merge_stats
    
    def _link_to_baseline_structure(
        self,
        session,
        company_name: str,
        context: str
    ):
        """
        Link user company to baseline industry/country structure
        Based on context keywords
        """
        # Industry keywords
        industry_keywords = {
            'Semiconductor Equipment': ['euv', 'lithography', 'equipment', 'asml'],
            'Semiconductor Foundry': ['foundry', 'manufacturing', 'fab', 'tsmc'],
            'Memory Chips': ['memory', 'dram', 'nand', 'hbm'],
            'GPU & AI Chips': ['gpu', 'graphics', 'ai chip', 'accelerator'],
            'Cloud Service Provider': ['cloud', 'data center', 'aws', 'azure'],
        }
        
        context_lower = context.lower()
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in context_lower for keyword in keywords):
                # Link to industry
                session.run("""
                    MATCH (c:Company {name: $company_name})
                    MATCH (i:Industry {name: $industry})
                    MERGE (c)-[r:OPERATES_IN]->(i)
                    SET r.source = 'inferred', r.confidence = 0.7
                """, company_name=company_name, industry=industry)
                
                break
    
    def ingest_user_pdf_with_baseline(
        self,
        pdf_path: str,
        extractor,
        source_label: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete workflow: Extract entities from user PDF and merge with baseline
        
        SECURITY: This function processes sensitive PDF data
        - Must use local model (Qwen 2.5 Coder) only
        - Verifies Ollama availability before processing
        
        Args:
            pdf_path: Path to user's PDF document
            extractor: KnowledgeExtractor instance
            source_label: Optional label for source tracking
        
        Returns:
            Combined statistics
        """
        # SECURITY CHECK: Verify local model is available
        print("🔒 SECURITY: Verifying local model before PDF processing...")
        check_local_model_before_processing()
        
        print(f"📄 Processing user PDF: {pdf_path}")
        
        if source_label is None:
            source_label = Path(pdf_path).stem
        
        # Step 1: Extract entities from PDF (using LOCAL model only)
        try:
            import fitz
        except ImportError:
            raise ImportError("PyMuPDF required: pip install pymupdf")
        
        doc = fitz.open(pdf_path)
        full_text = ""
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            full_text += page.get_text()
        
        doc.close()
        
        # Process in chunks
        chunk_size = 500
        chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
        
        print(f"   Extracting from {len(chunks)} chunks...")
        
        all_entities = []
        
        for i, chunk in enumerate(chunks):
            if i % 10 == 0 and i > 0:
                print(f"   Progress: {i}/{len(chunks)} chunks")
            
            try:
                extracted = extractor.extract_entities(chunk)
                if extracted:
                    all_entities.extend(extracted.get('entities', []))
            except Exception as e:
                continue
        
        print(f"✅ Extracted {len(all_entities)} entities from PDF")
        
        # Step 2: Merge with baseline
        merge_stats = self.merge_with_baseline(all_entities, source_label)
        
        return {
            'pdf_file': pdf_path,
            'source_label': source_label,
            'entities_extracted': len(all_entities),
            **merge_stats
        }


def example_usage():
    """Example: How to use DataIntegrator"""
    
    integrator = DataIntegrator()
    
    # 1. Ingest CSV (e.g., financial data)
    integrator.ingest_csv(
        csv_path='data/company_financials.csv',
        mapping={
            'Company': 'entity_name',
            'Revenue': 'property',
            'MarketCap': 'property'
        }
    )
    
    # 2. Ingest JSON (e.g., company profiles)
    integrator.ingest_json(
        json_path='data/companies.json',
        schema={
            'root': 'companies',
            'entity_key': 'name',
            'entity_type': 'Company',
            'relationships': [
                {
                    'type': 'LOCATED_IN',
                    'target_key': 'country',
                    'target_type': 'Country'
                },
                {
                    'type': 'OPERATES_IN',
                    'target_key': 'industry',
                    'target_type': 'Industry'
                }
            ]
        }
    )
    
    # 3. Ingest PDF entities
    pdf_entities = [
        {'name': 'Nvidia', 'type': 'Company', 'context': 'Leading GPU manufacturer...'},
        {'name': 'Jensen Huang', 'type': 'Person', 'context': 'CEO of Nvidia...'}
    ]
    integrator.ingest_pdf_entities(pdf_entities)
    
    # 4. Link metrics
    metrics = [
        {'company': 'Nvidia', 'metric': 'Revenue', 'value': 60.9, 'period': 'FY2024'},
        {'company': 'Nvidia', 'metric': 'Growth Rate', 'value': 126, 'period': 'YoY 2024'}
    ]
    integrator.link_metrics_to_entities(metrics)
    
    print("\n📊 Integration Stats:")
    print(integrator.get_stats())
    
    integrator.close()


if __name__ == "__main__":
    example_usage()
