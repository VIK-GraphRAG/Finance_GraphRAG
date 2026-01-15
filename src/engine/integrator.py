"""
Data Integrator: Merge PDF knowledge with structured data (CSV/JSON)
Handles entity resolution and deduplication
"""

import json
import csv
import re
from typing import Dict, List, Any, Set, Tuple
from pathlib import Path
from neo4j import GraphDatabase

from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD


class EntityResolver:
    """
    Resolve entity aliases to canonical names
    Example: 'NVDA', 'Nvidia', 'NVIDIA Corporation' → 'Nvidia'
    """
    
    # Known aliases for common entities
    ALIASES = {
        'Nvidia': ['NVDA', 'nvidia', 'NVIDIA', 'Nvidia Corporation', 'NVIDIA Corp'],
        'TSMC': ['TSM', 'tsmc', 'Taiwan Semiconductor', 'Taiwan Semiconductor Manufacturing'],
        'Intel': ['INTC', 'intel', 'Intel Corporation', 'Intel Corp'],
        'AMD': ['amd', 'Advanced Micro Devices', 'AMD Inc'],
        'Apple': ['AAPL', 'apple', 'Apple Inc', 'Apple Inc.'],
        'Microsoft': ['MSFT', 'microsoft', 'Microsoft Corporation', 'Microsoft Corp'],
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


class DataIntegrator:
    """
    Integrate multiple data sources into Neo4j knowledge graph
    - PDF extracted entities
    - CSV structured data
    - JSON indicator data
    """
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        self.resolver = EntityResolver()
        self.stats = {
            'entities_merged': 0,
            'relationships_created': 0,
            'csv_records': 0,
            'json_records': 0,
            'pdf_chunks': 0
        }
    
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
        
        Args:
            entities: List of entities from KnowledgeExtractor
                [
                    {'name': 'Nvidia', 'type': 'Company', 'context': '...'},
                    ...
                ]
        """
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
