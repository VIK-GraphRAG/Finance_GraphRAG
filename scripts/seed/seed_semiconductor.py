#!/usr/bin/env python3
"""
Semiconductor Industry Ontology - Comprehensive Supply Chain Model
반도체 산업 온톨로지 - 전체 공급망 모델
"""

import sys
import os
from neo4j import GraphDatabase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

def run_query(driver, query):
    with driver.session() as session:
        result = session.run(query)
        return list(result)

def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    print("✅ Connected to Neo4j")
    
    queries = [
        # === 1. Companies (기업) ===
        """MERGE (n:Company {name: 'Nvidia'}) 
           SET n.country = 'USA', n.market_cap = 1200, n.revenue = 60.9, 
               n.type = 'Fabless', n.specialty = 'GPU Design'""",
        
        """MERGE (t:Company {name: 'TSMC'}) 
           SET t.country = 'Taiwan', t.market_cap = 500, t.revenue = 69.3,
               t.type = 'Foundry', t.specialty = 'Advanced Process'""",
        
        """MERGE (a:Company {name: 'AMD'}) 
           SET a.country = 'USA', a.market_cap = 240, a.revenue = 22.7,
               a.type = 'Fabless', a.specialty = 'CPU/GPU Design'""",
        
        """MERGE (f:Company {name: 'FPT Semiconductor'}) 
           SET f.country = 'Vietnam', f.market_cap = 15, f.revenue = 4.5,
               f.type = 'OSAT', f.specialty = 'Packaging & Testing'""",
        
        """MERGE (s:Company {name: 'Samsung Electronics'}) 
           SET s.country = 'South Korea', s.market_cap = 350, s.revenue = 230,
               s.type = 'IDM', s.specialty = 'Memory & Foundry'""",
        
        # === 2. Components (반도체 부품) ===
        """MERGE (c:Component {name: 'H100 GPU'}) 
           SET c.type = 'GPU', c.process_node = '4nm', c.designer = 'Nvidia'""",
        
        """MERGE (c:Component {name: 'HBM3'}) 
           SET c.type = 'Memory', c.capacity = '24GB', c.producer = 'Samsung'""",
        
        """MERGE (c:Component {name: 'CoWoS Package'}) 
           SET c.type = 'Advanced Packaging', c.technology = '2.5D', c.provider = 'TSMC'""",
        
        """MERGE (c:Component {name: 'MI300 AI Accelerator'}) 
           SET c.type = 'AI Chip', c.process_node = '5nm', c.designer = 'AMD'""",
        
        """MERGE (c:Component {name: 'Interposer'}) 
           SET c.type = 'Packaging Component', c.material = 'Silicon'""",
        
        # === 3. Process (제조 공정) ===
        """MERGE (p:Process {name: 'EUV Lithography'}) 
           SET p.technology = '7nm and below', p.equipment = 'ASML EUV Scanner',
               p.criticality = 'critical'""",
        
        """MERGE (p:Process {name: 'Advanced Packaging'}) 
           SET p.technology = 'CoWoS, HBM Integration', p.location = 'Taiwan, Vietnam',
               p.criticality = 'high'""",
        
        """MERGE (p:Process {name: '4nm Process'}) 
           SET p.technology = 'FinFET', p.capacity = 'Limited',
               p.criticality = 'critical'""",
        
        """MERGE (p:Process {name: 'HBM Stacking'}) 
           SET p.technology = 'Vertical Stacking', p.yield_rate = '85%',
               p.criticality = 'high'""",
        
        """MERGE (p:Process {name: 'Wafer Fabrication'}) 
           SET p.technology = 'CMOS', p.location = 'Taiwan, South Korea',
               p.criticality = 'critical'""",
        
        # === 4. Geopolitics (지정학 리스크) ===
        """MERGE (g:Geopolitics {name: 'Taiwan Strait Tension'}) 
           SET g.type = 'Military Risk', g.severity = 0.95, 
               g.impact_area = 'TSMC Production', g.probability = 0.3""",
        
        """MERGE (g:Geopolitics {name: 'US-China Tech War'}) 
           SET g.type = 'Export Control', g.severity = 0.85,
               g.impact_area = 'Advanced Chip Export', g.probability = 0.9""",
        
        """MERGE (g:Geopolitics {name: 'Taiwan Earthquake Risk'}) 
           SET g.type = 'Natural Disaster', g.severity = 0.8,
               g.impact_area = 'Fab Shutdown', g.probability = 0.4""",
        
        """MERGE (g:Geopolitics {name: 'ASML Export Ban'}) 
           SET g.type = 'Equipment Restriction', g.severity = 0.9,
               g.impact_area = 'EUV Access', g.probability = 0.6""",
        
        # === 5. Financials (재무 지표) ===
        """MERGE (f:Financials {name: 'TSMC CAPEX 2024'}) 
           SET f.value = 40.0, f.unit = 'billion USD', f.category = 'Investment',
               f.year = 2024""",
        
        """MERGE (f:Financials {name: 'Nvidia AI Revenue'}) 
           SET f.value = 47.5, f.unit = 'billion USD', f.category = 'Revenue',
               f.year = 2024, f.growth = 1.26""",
        
        """MERGE (f:Financials {name: 'Samsung HBM Sales'}) 
           SET f.value = 8.5, f.unit = 'billion USD', f.category = 'Revenue',
               f.year = 2024, f.growth = 2.5""",
        
        # === 6. Company → Component (생산/설계) ===
        """MATCH (nvidia:Company {name: 'Nvidia'}), (gpu:Component {name: 'H100 GPU'})
           MERGE (nvidia)-[:PRODUCES {role: 'designer', dependency: 'critical'}]->(gpu)""",
        
        """MATCH (amd:Company {name: 'AMD'}), (mi300:Component {name: 'MI300 AI Accelerator'})
           MERGE (amd)-[:PRODUCES {role: 'designer', dependency: 'critical'}]->(mi300)""",
        
        """MATCH (samsung:Company {name: 'Samsung Electronics'}), (hbm:Component {name: 'HBM3'})
           MERGE (samsung)-[:PRODUCES {role: 'manufacturer', capacity: 'high'}]->(hbm)""",
        
        """MATCH (tsmc:Company {name: 'TSMC'}), (cowos:Component {name: 'CoWoS Package'})
           MERGE (tsmc)-[:PRODUCES {role: 'packager', monopoly: true}]->(cowos)""",
        
        # === 7. Component → Process (필수 공정) ===
        """MATCH (gpu:Component {name: 'H100 GPU'}), (proc:Process {name: '4nm Process'})
           MERGE (gpu)-[:REQUIRES_PROCESS {criticality: 'critical', alternative: 'none'}]->(proc)""",
        
        """MATCH (gpu:Component {name: 'H100 GPU'}), (euv:Process {name: 'EUV Lithography'})
           MERGE (gpu)-[:REQUIRES_PROCESS {criticality: 'critical', bottleneck: true}]->(euv)""",
        
        """MATCH (gpu:Component {name: 'H100 GPU'}), (pkg:Process {name: 'Advanced Packaging'})
           MERGE (gpu)-[:REQUIRES_PROCESS {criticality: 'high', lead_time: '3 months'}]->(pkg)""",
        
        """MATCH (hbm:Component {name: 'HBM3'}), (stack:Process {name: 'HBM Stacking'})
           MERGE (hbm)-[:REQUIRES_PROCESS {criticality: 'critical', yield_sensitive: true}]->(stack)""",
        
        # === 8. Process → Company (공정 의존성) ===
        """MATCH (proc:Process {name: '4nm Process'}), (tsmc:Company {name: 'TSMC'})
           MERGE (proc)-[:DEPENDS_ON {exclusivity: 'high', capacity_share: 0.7}]->(tsmc)""",
        
        """MATCH (euv:Process {name: 'EUV Lithography'}), (tsmc:Company {name: 'TSMC'})
           MERGE (euv)-[:DEPENDS_ON {monopoly: true, capex: 40}]->(tsmc)""",
        
        """MATCH (pkg:Process {name: 'Advanced Packaging'}), (tsmc:Company {name: 'TSMC'})
           MERGE (pkg)-[:DEPENDS_ON {capacity_share: 0.6}]->(tsmc)""",
        
        """MATCH (pkg:Process {name: 'Advanced Packaging'}), (fpt:Company {name: 'FPT Semiconductor'})
           MERGE (pkg)-[:DEPENDS_ON {capacity_share: 0.15, cost_competitive: true}]->(fpt)""",
        
        """MATCH (stack:Process {name: 'HBM Stacking'}), (samsung:Company {name: 'Samsung Electronics'})
           MERGE (stack)-[:DEPENDS_ON {market_share: 0.5}]->(samsung)""",
        
        # === 9. Geopolitics → Company (지정학 영향) ===
        """MATCH (geo:Geopolitics {name: 'Taiwan Strait Tension'}), (tsmc:Company {name: 'TSMC'})
           MERGE (geo)-[:DISRUPTS {impact: 'production_halt', severity: 0.95, duration: 'months'}]->(tsmc)""",
        
        """MATCH (geo:Geopolitics {name: 'Taiwan Earthquake Risk'}), (tsmc:Company {name: 'TSMC'})
           MERGE (geo)-[:DISRUPTS {impact: 'facility_damage', severity: 0.8, recovery_time: '2-6 months'}]->(tsmc)""",
        
        """MATCH (geo:Geopolitics {name: 'US-China Tech War'}), (nvidia:Company {name: 'Nvidia'})
           MERGE (geo)-[:DISRUPTS {impact: 'export_ban', severity: 0.7, revenue_loss: 0.2}]->(nvidia)""",
        
        """MATCH (geo:Geopolitics {name: 'ASML Export Ban'}), (tsmc:Company {name: 'TSMC'})
           MERGE (geo)-[:DISRUPTS {impact: 'equipment_shortage', severity: 0.85, capex_risk: true}]->(tsmc)""",
        
        # === 10. Geopolitics → Process (공정 차단) ===
        """MATCH (geo:Geopolitics {name: 'Taiwan Strait Tension'}), (proc:Process {name: 'EUV Lithography'})
           MERGE (geo)-[:BLOCKS {probability: 0.3, recovery_impossible: true}]->(proc)""",
        
        """MATCH (geo:Geopolitics {name: 'ASML Export Ban'}), (euv:Process {name: 'EUV Lithography'})
           MERGE (geo)-[:BLOCKS {probability: 0.6, alternative: 'DUV with multi-patterning'}]->(euv)""",
        
        # === 11. Component → Component (부품 의존성) ===
        """MATCH (gpu:Component {name: 'H100 GPU'}), (hbm:Component {name: 'HBM3'})
           MERGE (gpu)-[:REQUIRES_COMPONENT {quantity: 6, criticality: 'critical'}]->(hbm)""",
        
        """MATCH (gpu:Component {name: 'H100 GPU'}), (cowos:Component {name: 'CoWoS Package'})
           MERGE (gpu)-[:REQUIRES_COMPONENT {necessity: 'mandatory', lead_time: '4 months'}]->(cowos)""",
        
        """MATCH (cowos:Component {name: 'CoWoS Package'}), (inter:Component {name: 'Interposer'})
           MERGE (cowos)-[:REQUIRES_COMPONENT {material: 'silicon', supply: 'limited'}]->(inter)""",
        
        # === 12. Financials → Company (재무 연결) ===
        """MATCH (fin:Financials {name: 'TSMC CAPEX 2024'}), (tsmc:Company {name: 'TSMC'})
           MERGE (tsmc)-[:HAS_FINANCIAL {type: 'CAPEX', trend: 'increasing'}]->(fin)""",
        
        """MATCH (fin:Financials {name: 'Nvidia AI Revenue'}), (nvidia:Company {name: 'Nvidia'})
           MERGE (nvidia)-[:HAS_FINANCIAL {type: 'Revenue', segment: 'Data Center'}]->(fin)""",
        
        """MATCH (fin:Financials {name: 'Samsung HBM Sales'}), (samsung:Company {name: 'Samsung Electronics'})
           MERGE (samsung)-[:HAS_FINANCIAL {type: 'Revenue', segment: 'HBM'}]->(fin)""",
        
        # === 13. Cross-Company Dependencies (회사간 의존) ===
        """MATCH (nvidia:Company {name: 'Nvidia'}), (tsmc:Company {name: 'TSMC'})
           MERGE (nvidia)-[:DEPENDS_ON_COMPANY {
               type: 'manufacturing', 
               criticality: 0.95, 
               alternative: 'Samsung (limited)',
               capacity_allocation: '80%'
           }]->(tsmc)""",
        
        """MATCH (nvidia:Company {name: 'Nvidia'}), (samsung:Company {name: 'Samsung Electronics'})
           MERGE (nvidia)-[:DEPENDS_ON_COMPANY {
               type: 'HBM supply', 
               criticality: 0.9,
               supply_share: 0.6,
               contract: 'long-term'
           }]->(samsung)""",
        
        """MATCH (tsmc:Company {name: 'TSMC'}), (fpt:Company {name: 'FPT Semiconductor'})
           MERGE (tsmc)-[:PARTNERS_WITH {
               type: 'backend services',
               scope: 'packaging & testing',
               volume: 'growing'
           }]->(fpt)""",
        
        """MATCH (amd:Company {name: 'AMD'}), (tsmc:Company {name: 'TSMC'})
           MERGE (amd)-[:DEPENDS_ON_COMPANY {
               type: 'manufacturing',
               criticality: 0.9,
               capacity_allocation: '70%'
           }]->(tsmc)""",
    ]
    
    total = len(queries)
    for i, q in enumerate(queries, 1):
        try:
            run_query(driver, q)
            print(f"✅ {i}/{total}")
        except Exception as e:
            print(f"❌ {i}/{total} - Error: {str(e)[:100]}")
    
    # Test: Multi-hop supply chain risk
    print("\n🧪 Test: Nvidia supply chain paths (3-hop)")
    test = """
    MATCH path = (nvidia:Company {name: 'Nvidia'})-[*1..3]-(related)
    WHERE ANY(label IN labels(related) WHERE label IN ['Component', 'Process', 'Company', 'Geopolitics'])
    RETURN [n IN nodes(path) | labels(n)[0] + ': ' + n.name] AS path,
           length(path) as hops
    ORDER BY hops DESC
    LIMIT 10
    """
    results = run_query(driver, test)
    for r in results:
        print(f"  {r['hops']} hops: {' → '.join(r['path'])}")
    
    # Test: Geopolitical risk propagation
    print("\n🧪 Test: Taiwan risk cascading effects")
    test2 = """
    MATCH path = (geo:Geopolitics {name: 'Taiwan Strait Tension'})
                 -[:DISRUPTS|BLOCKS*1..3]->
                 (affected)
    WHERE affected:Company OR affected:Process
    RETURN [n IN nodes(path) | labels(n)[0] + ': ' + n.name] AS risk_chain,
           length(path) as depth
    ORDER BY depth
    LIMIT 10
    """
    results2 = run_query(driver, test2)
    for r in results2:
        print(f"  {r['depth']} hops: {' → '.join(r['risk_chain'])}")
    
    driver.close()
    print("\n✅ Semiconductor ontology seed complete!")
    print(f"📊 Total nodes: ~{total * 0.6:.0f}")
    print(f"🔗 Total relationships: ~{total * 0.4:.0f}")

if __name__ == "__main__":
    main()
