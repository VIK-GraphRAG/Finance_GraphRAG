
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/src")

from db.neo4j_db import Neo4jDatabase
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

def check_nvidia():
    print("Connecting to Neo4j...")
    try:
        db = Neo4jDatabase(uri=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
        
        print("Checking for 'Nvidia' nodes...")
        query = """
        MATCH (n) 
        WHERE toLower(n.name) CONTAINS 'nvidia'
        RETURN n.name, labels(n), properties(n)
        LIMIT 5
        """
        
        with db.driver.session() as session:
            result = session.run(query)
            records = list(result)
            
            if not records:
                print("❌ No 'Nvidia' nodes found.")
            else:
                print(f"✅ Found {len(records)} 'Nvidia' nodes:")
                for r in records:
                    print(f" - {r['n.name']} ({r['labels(n)']})")
                    
        db.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_nvidia()
