"""
Multi-Hop Reasoning System Test Script
Tests integrator, reasoner, and end-to-end workflow
"""

import asyncio
import json
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from engine.integrator import DataIntegrator, EntityResolver
from engine.reasoner import MultiHopReasoner


def test_entity_resolver():
    """Test 1: Entity name resolution"""
    print("\n" + "="*60)
    print("TEST 1: Entity Resolver")
    print("="*60)
    
    test_cases = [
        ('NVDA', 'Nvidia'),
        ('nvidia', 'Nvidia'),
        ('NVIDIA Corporation', 'Nvidia'),
        ('TSM', 'TSMC'),
        ('Intel Corp', 'Intel'),
    ]
    
    passed = 0
    for input_name, expected in test_cases:
        result = EntityResolver.resolve(input_name)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_name}' → '{result}' (expected: '{expected}')")
        if result == expected:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_data_integrator():
    """Test 2: Data integration"""
    print("\n" + "="*60)
    print("TEST 2: Data Integrator")
    print("="*60)
    
    integrator = DataIntegrator()
    
    try:
        # Test entity merge
        print("\n📝 Testing entity merge...")
        integrator.merge_entity('Nvidia', 'Company', {'industry': 'Semiconductor'})
        integrator.merge_entity('TSMC', 'Company', {'industry': 'Semiconductor'})
        integrator.merge_entity('Taiwan', 'Country', {'region': 'Asia'})
        print("✅ Entities merged")
        
        # Test relationship creation
        print("\n🔗 Testing relationship creation...")
        integrator.create_relationship('Nvidia', 'TSMC', 'DEPENDS_ON', {'criticality': 0.9})
        integrator.create_relationship('TSMC', 'Taiwan', 'LOCATED_IN', {})
        print("✅ Relationships created")
        
        # Test PDF entity ingestion
        print("\n📚 Testing PDF entity ingestion...")
        pdf_entities = [
            {'name': 'Nvidia', 'type': 'Company', 'context': 'Leading GPU manufacturer'},
            {'name': 'Jensen Huang', 'type': 'Person', 'context': 'CEO of Nvidia'}
        ]
        integrator.ingest_pdf_entities(pdf_entities)
        print("✅ PDF entities ingested")
        
        # Test metrics linking
        print("\n🔢 Testing metrics linking...")
        metrics = [
            {'company': 'Nvidia', 'metric': 'Revenue', 'value': 60.9, 'period': 'FY2024'}
        ]
        integrator.link_metrics_to_entities(metrics)
        print("✅ Metrics linked")
        
        # Get stats
        stats = integrator.get_stats()
        print(f"\n📊 Integration Stats:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        integrator.close()
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        integrator.close()
        return False


async def test_reasoner():
    """Test 3: Multi-hop reasoner"""
    print("\n" + "="*60)
    print("TEST 3: Multi-Hop Reasoner")
    print("="*60)
    
    reasoner = MultiHopReasoner()
    
    try:
        # Test query generation
        print("\n🔍 Testing query generation...")
        question = "How does Taiwan tension affect Nvidia?"
        query_spec = await reasoner.generate_multihop_query(question, max_hops=3)
        
        print(f"✅ Query generated:")
        print(f"   Type: {query_spec.get('reasoning_type', 'unknown')}")
        print(f"   Cypher: {query_spec.get('cypher', 'N/A')[:100]}...")
        
        # Test query execution
        print("\n⚙️  Testing query execution...")
        paths = reasoner.execute_multihop_query(query_spec['cypher'])
        print(f"✅ Found {len(paths)} reasoning paths")
        
        if paths:
            print("\nExample path:")
            path = paths[0]
            nodes = [n.get('name', 'Unknown') for n in path.get('nodes', [])]
            print(f"   {' → '.join(nodes)}")
        
        # Test full reasoning
        print("\n🧠 Testing full reasoning...")
        result = await reasoner.reason(question, max_hops=3)
        
        print(f"✅ Reasoning complete:")
        print(f"   Inference: {result['inference'][:100]}...")
        print(f"   Confidence: {result['confidence']:.1%}")
        print(f"   Paths found: {len(result['reasoning_paths'])}")
        
        reasoner.close()
        return True
        
    except Exception as e:
        print(f"❌ Reasoner test failed: {e}")
        import traceback
        traceback.print_exc()
        reasoner.close()
        return False


async def test_end_to_end():
    """Test 4: End-to-end workflow"""
    print("\n" + "="*60)
    print("TEST 4: End-to-End Workflow")
    print("="*60)
    
    # Step 1: Create sample data
    print("\n1️⃣  Creating sample data...")
    integrator = DataIntegrator()
    
    # Companies
    integrator.merge_entity('Nvidia', 'Company', {'revenue': 60.9, 'market_cap': 1200})
    integrator.merge_entity('Intel', 'Company', {'revenue': 54.2, 'market_cap': 180})
    integrator.merge_entity('TSMC', 'Company', {'revenue': 69.3, 'market_cap': 550})
    
    # Countries
    integrator.merge_entity('Taiwan', 'Country', {'region': 'Asia'})
    integrator.merge_entity('USA', 'Country', {'region': 'North America'})
    
    # Industries
    integrator.merge_entity('Semiconductor', 'Industry', {})
    
    # Macro indicators
    integrator.merge_entity('Taiwan Strait Tension', 'MacroIndicator', {'type': 'geopolitical', 'severity': 0.95})
    integrator.merge_entity('US-China Trade War', 'MacroIndicator', {'type': 'geopolitical', 'severity': 0.85})
    
    # Relationships
    integrator.create_relationship('Nvidia', 'TSMC', 'DEPENDS_ON', {'criticality': 0.9})
    integrator.create_relationship('Nvidia', 'Semiconductor', 'OPERATES_IN', {})
    integrator.create_relationship('TSMC', 'Taiwan', 'LOCATED_IN', {})
    integrator.create_relationship('Taiwan Strait Tension', 'Taiwan', 'THREATENS', {'probability': 0.7})
    integrator.create_relationship('US-China Trade War', 'Semiconductor', 'IMPACTS', {'severity': 0.8})
    
    print("✅ Sample data created")
    integrator.close()
    
    # Step 2: Perform reasoning
    print("\n2️⃣  Performing multi-hop reasoning...")
    reasoner = MultiHopReasoner()
    
    questions = [
        "How does Taiwan tension affect Nvidia?",
        "What are Nvidia's geopolitical risks?",
        "How does US-China trade war impact semiconductor companies?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n   Question {i}: {question}")
        result = await reasoner.reason(question, max_hops=3)
        
        print(f"   💡 Inference: {result['inference'][:80]}...")
        print(f"   📊 Confidence: {result['confidence']:.1%}")
        print(f"   🔗 Paths: {len(result['reasoning_paths'])}")
    
    reasoner.close()
    
    print("\n✅ End-to-end test complete")
    return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 Multi-Hop Reasoning System Test Suite")
    print("="*60)
    
    tests = [
        ("Entity Resolver", test_entity_resolver, False),
        ("Data Integrator", test_data_integrator, False),
        ("Multi-Hop Reasoner", test_reasoner, True),
        ("End-to-End Workflow", test_end_to_end, True)
    ]
    
    results = []
    
    for name, test_func, is_async in tests:
        try:
            if is_async:
                result = await test_func()
            else:
                result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    asyncio.run(main())
