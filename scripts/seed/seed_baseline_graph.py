#!/usr/bin/env python3
"""
Seed Baseline Graph - Load baseline data into Neo4j
베이스라인 데이터를 Neo4j에 로드
"""

import json
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from db.neo4j_db import Neo4jDatabase
except ImportError:
    print("❌ Cannot import Neo4jDatabase")
    sys.exit(1)


def load_json_data(filepath: str) -> dict:
    """Load JSON data from file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def seed_supply_chain(db: Neo4jDatabase, data: dict):
    """
    Seed supply chain data into Neo4j
    
    Args:
        db: Neo4j database instance
        data: Supply chain data
    """
    print("\n📊 Seeding Supply Chain Data...")
    
    supply_chain = data.get('supply_chain', {})
    tiers = supply_chain.get('tiers', [])
    
    # Create companies
    company_count = 0
    for tier in tiers:
        tier_num = tier.get('tier')
        tier_name = tier.get('name')
        
        for company in tier.get('companies', []):
            # Create Company node
                query = """
                MERGE (c:Company {name: $name})
                SET c.ticker = $ticker,
                    c.country = $country,
                c.role = $role,
                c.tier = $tier,
                c.tier_name = $tier_name,
                c.market_share = $market_share,
                c.criticality = $criticality,
                    c.updated_at = datetime()
            RETURN c.name as name
            """
            
            params = {
                'name': company.get('name'),
                'ticker': company.get('ticker', ''),
                'country': company.get('country', ''),
                'role': company.get('role', ''),
                'tier': tier_num,
                'tier_name': tier_name,
                'market_share': company.get('market_share', ''),
                'criticality': company.get('criticality', 'MEDIUM')
            }
            
            with db.driver.session() as session:
                result = session.run(query, **params)
                if result:
                    company_count += 1
                    print(f"  ✅ Created: {company.get('name')} ({tier_name})")
    
    print(f"\n✅ Created {company_count} companies")
    
    # Create relationships
    relationships = supply_chain.get('relationships', [])
    rel_count = 0
    
    for rel in relationships:
        query = """
        MATCH (from:Company {name: $from_name})
        MATCH (to:Company {name: $to_name})
        MERGE (from)-[r:SUPPLIES_TO]->(to)
        SET r.type = $rel_type,
            r.description = $description,
            r.dependency_level = $dependency_level,
            r.lead_time = $lead_time,
            r.capacity_allocation = $capacity_allocation
        RETURN from.name as from, to.name as to
        """
        
        params = {
            'from_name': rel.get('from'),
            'to_name': rel.get('to'),
            'rel_type': rel.get('type', 'SUPPLIES_TO'),
            'description': rel.get('description', ''),
            'dependency_level': rel.get('dependency_level', 'MEDIUM'),
            'lead_time': rel.get('lead_time', ''),
            'capacity_allocation': rel.get('capacity_allocation', '')
        }
        
        with db.driver.session() as session:
            result = session.run(query, **params)
            if result:
                rel_count += 1
                print(f"  ✅ Created: {rel.get('from')} → {rel.get('to')}")
    
    print(f"\n✅ Created {rel_count} relationships")
    
    # Create risk factors
    risk_factors = supply_chain.get('risk_factors', [])
    risk_count = 0
    
    for risk in risk_factors:
        # Create Risk node
        query = """
        MERGE (r:Risk {name: $name})
        SET r.impact_level = $impact_level,
            r.description = $description,
            r.updated_at = datetime()
        RETURN r.name as name
        """
        
        params = {
            'name': risk.get('name'),
            'impact_level': risk.get('impact_level', 'MEDIUM'),
            'description': risk.get('description', '')
        }
        
        with db.driver.session() as session:
            result = session.run(query, **params)
            if result:
                risk_count += 1
                print(f"  ✅ Created risk: {risk.get('name')}")
        
        # Link risk to affected companies
        for company_name in risk.get('affected_entities', []):
            link_query = """
            MATCH (c:Company {name: $company_name})
            MATCH (r:Risk {name: $risk_name})
            MERGE (c)-[rel:EXPOSED_TO]->(r)
            SET rel.impact_level = $impact_level
            """
            
            with db.driver.session() as session:
                session.run(link_query, 
                    company_name=company_name,
                    risk_name=risk.get('name'),
                    impact_level=risk.get('impact_level')
                )
    
    print(f"\n✅ Created {risk_count} risk factors")


def seed_technologies(db: Neo4jDatabase):
    """Seed technology nodes"""
    print("\n🔬 Seeding Technology Data...")
    
    technologies = [
        {
            "name": "EUV Lithography",
            "category": "Manufacturing",
            "node_size": "< 7nm",
            "maturity": "Production",
            "key_players": ["ASML"]
        },
        {
            "name": "3nm Process",
            "category": "Node Technology",
            "node_size": "3nm",
            "maturity": "Production",
            "key_players": ["TSMC", "Samsung"]
        },
        {
            "name": "2nm Process",
            "category": "Node Technology",
            "node_size": "2nm",
            "maturity": "Development",
            "timeline": "2025 (TSMC)",
            "key_players": ["TSMC"]
        },
        {
            "name": "GAA Transistor",
            "category": "Transistor Architecture",
            "maturity": "Production",
            "key_players": ["Samsung", "TSMC"]
        },
        {
            "name": "HBM3",
            "category": "Memory",
            "maturity": "Production",
            "bandwidth": "819 GB/s",
            "key_players": ["SK Hynix", "Samsung", "Micron"]
        },
        {
            "name": "HBM4",
            "category": "Memory",
            "maturity": "Development",
            "timeline": "2026",
            "bandwidth": "> 1 TB/s",
            "key_players": ["SK Hynix"]
        }
    ]
    
    tech_count = 0
    for tech in technologies:
        query = """
        MERGE (t:Technology {name: $name})
        SET t.category = $category,
            t.maturity = $maturity,
            t.node_size = $node_size,
            t.timeline = $timeline,
            t.bandwidth = $bandwidth,
            t.updated_at = datetime()
        RETURN t.name as name
        """
        
        params = {
            'name': tech.get('name'),
            'category': tech.get('category', ''),
            'maturity': tech.get('maturity', ''),
            'node_size': tech.get('node_size', ''),
            'timeline': tech.get('timeline', ''),
            'bandwidth': tech.get('bandwidth', '')
        }
        
        with db.driver.session() as session:
            result = session.run(query, **params)
        if result:
            tech_count += 1
            print(f"  ✅ Created: {tech.get('name')}")
        
        # Link to companies
        for company_name in tech.get('key_players', []):
            link_query = """
            MATCH (c:Company {name: $company_name})
            MATCH (t:Technology {name: $tech_name})
            MERGE (c)-[r:DEVELOPS]->(t)
            """
            
            with db.driver.session() as session:
                session.run(link_query,
                    company_name=company_name,
                    tech_name=tech.get('name')
                )
    
    print(f"\n✅ Created {tech_count} technologies")


def seed_regulations(db: Neo4jDatabase):
    """Seed regulation nodes"""
    print("\n📜 Seeding Regulation Data...")
    
    regulations = [
        {
            "name": "CHIPS Act",
            "country": "USA",
            "type": "Subsidy",
            "budget": "$52 billion",
            "impact": "Incentivizes domestic chip manufacturing",
            "affected_companies": ["Intel", "TSMC", "Samsung"]
        },
        {
            "name": "EU Chips Act",
            "country": "EU",
            "type": "Subsidy",
            "budget": "€43 billion",
            "impact": "Aims to double EU chip production share",
            "affected_companies": ["Intel", "TSMC", "ASML"]
        },
        {
            "name": "Export Controls (China)",
            "country": "USA",
            "type": "Restriction",
            "impact": "Restricts advanced chip exports to China",
            "affected_companies": ["Nvidia", "AMD", "Intel", "ASML"]
        },
        {
            "name": "EU AI Act",
            "country": "EU",
            "type": "Regulation",
            "impact": "Regulates AI system deployment",
            "affected_companies": ["Microsoft", "Google", "Meta", "Amazon"]
        }
    ]
    
    reg_count = 0
    for reg in regulations:
        query = """
        MERGE (r:Regulation {name: $name})
        SET r.country = $country,
            r.type = $type,
            r.budget = $budget,
            r.impact = $impact,
            r.updated_at = datetime()
        RETURN r.name as name
        """
        
        params = {
            'name': reg.get('name'),
            'country': reg.get('country', ''),
            'type': reg.get('type', ''),
            'budget': reg.get('budget', ''),
            'impact': reg.get('impact', '')
        }
        
        with db.driver.session() as session:
            result = session.run(query, **params)
            if result:
                reg_count += 1
                print(f"  ✅ Created: {reg.get('name')}")
        
        # Link to companies
        for company_name in reg.get('affected_companies', []):
            link_query = """
            MATCH (c:Company {name: $company_name})
            MATCH (r:Regulation {name: $reg_name})
            MERGE (c)-[rel:SUBJECT_TO]->(r)
            """
            
            with db.driver.session() as session:
                session.run(link_query, 
                    company_name=company_name,
                    reg_name=reg.get('name')
                )
    
    print(f"\n✅ Created {reg_count} regulations")


def main():
    """Main seeding function"""
    print("=" * 60)
    print("🌱 Seeding Baseline Graph Data")
    print("=" * 60)
    
    # Connect to Neo4j
    try:
        db = Neo4jDatabase()
        print("✅ Connected to Neo4j")
    except Exception as e:
        print(f"❌ Failed to connect to Neo4j: {e}")
        print("Make sure Neo4j is running and credentials are correct in .env")
        return
    
    # Load JSON data
    json_path = "data/baseline/supply_chain_mapping.json"
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        return
    
    data = load_json_data(json_path)
    print(f"✅ Loaded JSON data from {json_path}")
    
    # Seed data
    try:
        seed_supply_chain(db, data)
        seed_technologies(db)
        seed_regulations(db)
        
        print("\n" + "=" * 60)
        print("✅ Baseline graph seeding completed successfully!")
        print("=" * 60)
        
        # Print summary
        summary_query = """
        MATCH (c:Company) WITH count(c) as companies
        MATCH (t:Technology) WITH companies, count(t) as technologies
        MATCH (r:Risk) WITH companies, technologies, count(r) as risks
        MATCH (reg:Regulation) WITH companies, technologies, risks, count(reg) as regulations
        MATCH ()-[rel]->() WITH companies, technologies, risks, regulations, count(rel) as relationships
        RETURN companies, technologies, risks, regulations, relationships
        """
        
        with db.driver.session() as session:
            result = session.run(summary_query).data()
        if result:
            stats = result[0]
            print(f"\n📊 Graph Statistics:")
            print(f"  Companies: {stats['companies']}")
            print(f"  Technologies: {stats['technologies']}")
            print(f"  Risks: {stats['risks']}")
            print(f"  Regulations: {stats['regulations']}")
            print(f"  Relationships: {stats['relationships']}")
        
    except Exception as e:
        print(f"\n❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
        print("\n✅ Database connection closed")


if __name__ == "__main__":
    main()
