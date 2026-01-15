
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/src")

from agents.privacy_analyst import PrivacyAnalystAgent

async def test_uncensored_persona():
    print("\n=== Testing Uncensored Tech Investor Persona ===")
    
    # Mock Neo4j
    mock_db = MagicMock()
    # Mock return for neo4j_search (called in analyze)
    mock_db.execute_query.side_effect = [
        # 1. neo4j_search("What about Nvidia?") -> returns list of nodes
         [{"name": "Nvidia", "type": "Company", "properties": {"status": "active"}}],
        # 2. neo4j_search("Nvidia") (in deep_dive) -> returns list of nodes
         [{"name": "Nvidia", "type": "Company", "properties": {"status": "active"}}],
        # 3. context_cypher (in deep_dive) -> returns dicts with specific keys
         [
             {"n.name": "H100", "type(r)": "PRODUCES", "label": "Product"},
             {"n.name": "AI Boom", "type(r)": "AFFECTED_BY", "label": "Catalyst"},
             {"n.name": "AMD", "type(r)": "COMPETES_WITH", "label": "Competitor"}
         ]
    ]
    
    agent = PrivacyAnalystAgent(neo4j_db=mock_db)
    
    # Mock Ollama Client
    agent.ollama_client = AsyncMock()
    agent.ollama_client.chat.return_value = {
        "message": {
            "content": "LISTEN UP. Nvidia is riding the H100 wave, but the AI Boom is a bubble waiting to burst. Don't be a bag holder."
        }
    }
    
    # Verify Deep Dive Tool Existence
    if "deep_dive_analysis" in agent.tools:
        print("✅ Deep Dive Tool Registered")
    else:
        print("❌ Deep Dive Tool MISSING")
        
    # Test Analyze (Persona)
    print("\n=== Testing Analyze (Persona) ===")
    result = await agent.analyze("Nvidia")
    print(f"Analyze Result: {result}")
    
    if "LISTEN UP" in result:
        print("✅ Persona Prompt Active")
    else:
        print("❌ Persona Prompt Inactive")

    # Test Deep Dive Execution
    print("\n=== Testing Deep Dive Execution ===")
    # Reset mock for deep dive interactions
    agent.ollama_client.chat.return_value = {"message": {"content": "This is a mocked deep dive section."}}
    
    report = await agent.deep_dive_analysis("Nvidia")
    print(f"Report Length: {len(report)}")
    
    if "# 🕵️ Uncensored Deep Dive: Nvidia" in report:
         print("✅ Deep Dive Report Generated with Correct Title")
    else:
         print("❌ Deep Dive Report Title Missing")

    if "The Bear Case (Risks)" in report and "The Bull Case (Moat)" in report:
         print("✅ Deep Dive Sections Present")
    else:
         print("❌ Deep Dive Sections Missing")

if __name__ == "__main__":
    asyncio.run(test_uncensored_persona())
