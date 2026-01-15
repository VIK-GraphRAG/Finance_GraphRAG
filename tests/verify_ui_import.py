
import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/src")

def test_imports():
    print("Testing UI Module Imports...")
    
    try:
        from agents.privacy_analyst import PrivacyAnalystAgent
        print("✅ Import `PrivacyAnalystAgent` Success")
    except ImportError as e:
        print(f"❌ Import `PrivacyAnalystAgent` Failed: {e}")
        return

    try:
        from db.neo4j_db import Neo4jDatabase
        print("✅ Import `Neo4jDatabase` Success")
    except ImportError as e:
        print(f"❌ Import `Neo4jDatabase` Failed: {e}")
        return

    # instantiation check
    try:
        # Mock env vars usually handled in config, but we pass explicit args
        db = Neo4jDatabase(uri="bolt://localhost:7687", username="neo4j", password="password")
        # Mock connection 
        db.driver = MagicMock() 
        print("✅ Instantiate `Neo4jDatabase` Success")
        
        agent = PrivacyAnalystAgent(neo4j_db=db)
        print("✅ Instantiate `PrivacyAnalystAgent` Success")
        
    except Exception as e:
        print(f"❌ Instantiation Failed: {e}")

if __name__ == "__main__":
    test_imports()
