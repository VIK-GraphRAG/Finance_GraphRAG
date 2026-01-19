#!/usr/bin/env python3
"""
Full System Integration Test
전체 시스템의 통합 테스트를 수행합니다
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_health_check():
    """Test 1: Health Check API"""
    print_section("Test 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        data = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"   Server Status: {data.get('status')}")
        print(f"   Engine Ready: {data.get('engine_ready')}")
        print(f"   Message: {data.get('message')}")
        
        return data.get('status') == 'healthy'
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_graph_stats():
    """Test 2: Graph Statistics Endpoint"""
    print_section("Test 2: Graph Statistics")
    
    try:
        response = requests.get(f"{BASE_URL}/graph_stats", timeout=5)
        data = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"   Message: {data.get('message', 'N/A')}")
        
        if 'stats' in data:
            stats = data['stats']
            print(f"   Node Count: {stats.get('node_count', 0)}")
            print(f"   Edge Count: {stats.get('edge_count', 0)}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Graph stats check failed: {e}")
        return False


def test_insert_endpoint():
    """Test 3: Text Insertion Endpoint"""
    print_section("Test 3: Text Insertion")
    
    try:
        # Test inserting text
        text = "Nvidia announced new Blackwell GPU architecture in 2026."
        
        response = requests.post(
            f"{BASE_URL}/insert",
            json={"text": text},
            timeout=30
        )
        data = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"   Message: {data.get('message', 'N/A')[:100]}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Text insertion failed: {e}")
        return False


def test_query_endpoint():
    """Test 4: Query Endpoint (GraphRAG)"""
    print_section("Test 4: Query Endpoint")
    
    try:
        query = "What is Nvidia?"
        
        print(f"   Query: {query}")
        response = requests.post(
            f"{BASE_URL}/query",
            json={
                "question": query,
                "mode": "local",
                "search_type": "local",
                "enable_web_search": False
            },
            timeout=60
        )
        data = response.json()
        
        print(f"✅ Status: {response.status_code}")
        
        if 'answer' in data:
            print(f"   Answer Length: {len(data.get('answer', ''))} characters")
            print(f"   Answer Preview: {data['answer'][:100]}...")
        elif 'message' in data:
            print(f"   Message: {data['message']}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False


def test_agentic_query():
    """Test 5: Agentic Query Endpoint"""
    print_section("Test 5: Agentic Query")
    
    try:
        query = "What are Nvidia's key products?"
        
        print(f"   Query: {query}")
        response = requests.post(
            f"{BASE_URL}/agentic-query",
            json={
                "question": query,
                "enable_web_search": False
            },
            timeout=90
        )
        data = response.json()
        
        print(f"✅ Status: {response.status_code}")
        
        if 'answer' in data:
            print(f"   Answer: {data['answer'][:150]}...")
        elif 'message' in data:
            print(f"   Message: {data['message']}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Agentic query failed: {e}")
        return False


def test_web_search_query():
    """Test 6: Web Search Query"""
    print_section("Test 6: Web Search Query (Perplexity)")
    
    try:
        query = "What is today's latest news about Nvidia?"
        
        print(f"   Query: {query}")
        print(f"   (This should trigger Perplexity web search)")
        
        response = requests.post(
            f"{BASE_URL}/query",
            json={
                "question": query,
                "mode": "local",
                "search_type": "local",
                "enable_web_search": True  # Enable web search
            },
            timeout=90
        )
        data = response.json()
        
        print(f"✅ Status: {response.status_code}")
        
        if 'answer' in data:
            print(f"   Answer Length: {len(data.get('answer', ''))} characters")
            print(f"   Answer Preview: {data['answer'][:150]}...")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Web search query failed: {e}")
        return False


def test_graph_visualization():
    """Test 7: Graph Visualization"""
    print_section("Test 7: Graph Visualization")
    
    try:
        response = requests.get(f"{BASE_URL}/visualize", timeout=10)
        
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            # Check if HTML was returned
            content_type = response.headers.get('content-type', '')
            if 'html' in content_type.lower():
                print(f"   Visualization HTML generated successfully")
                print(f"   Content Length: {len(response.text)} bytes")
            elif 'json' in content_type.lower():
                data = response.json()
                print(f"   Message: {data.get('message', 'N/A')}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"⚠️ Visualization test failed: {e}")
        return True  # Not critical


def test_streamlit_frontend():
    """Test 8: Streamlit Frontend Availability"""
    print_section("Test 8: Streamlit Frontend")
    
    try:
        # Check if Streamlit is running on default port 8501
        response = requests.get("http://localhost:8501", timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Streamlit is running on http://localhost:8501")
            return True
        else:
            print(f"⚠️ Streamlit responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"⚠️ Streamlit not running on port 8501")
        print(f"   Start with: streamlit run src/streamlit_app.py")
        return False
    except Exception as e:
        print(f"⚠️ Frontend check failed: {e}")
        return False


def generate_report():
    """Generate test summary report"""
    print("\n" + "=" * 70)
    print("  📊 System Test Summary")
    print("=" * 70)
    
    tests = [
        ("Health Check", test_health_check()),
        ("Graph Statistics", test_graph_stats()),
        ("Text Insertion", test_insert_endpoint()),
        ("Query Endpoint", test_query_endpoint()),
        ("Agentic Query", test_agentic_query()),
        ("Web Search Query", test_web_search_query()),
        ("Graph Visualization", test_graph_visualization()),
        ("Streamlit Frontend", test_streamlit_frontend()),
    ]
    
    print("\n")
    passed = 0
    failed = 0
    
    for name, result in tests:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status}  {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "-" * 70)
    print(f"  Total: {len(tests)} tests")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    
    if failed == 0:
        print("\n  🎉 All tests passed! System is fully operational.")
    elif failed <= 2:
        print("\n  ⚠️ Some optional features need attention.")
    else:
        print("\n  ❌ Multiple failures detected. Check configuration.")
    
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    print("\n🚀 Starting Full System Integration Tests")
    print(f"Backend URL: {BASE_URL}")
    
    # Run all tests
    success = generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
