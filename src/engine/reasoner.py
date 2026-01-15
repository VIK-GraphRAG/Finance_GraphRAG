"""
Multi-Hop Reasoning Engine
Performs 2-3 hop logical inference on knowledge graph
"""

import json
from typing import Dict, List, Any, Tuple
from openai import AsyncOpenAI
from neo4j import GraphDatabase

from config import OPENAI_API_KEY, OPENAI_BASE_URL, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD


class MultiHopReasoner:
    """
    Performs multi-hop reasoning on knowledge graph
    Example: A → B → C → D logical chain
    """
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )
        self.neo4j_driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        self.model = "gpt-4o-mini"
    
    def close(self):
        """Close Neo4j connection"""
        self.neo4j_driver.close()
    
    async def generate_multihop_query(
        self,
        question: str,
        max_hops: int = 3
    ) -> Dict[str, Any]:
        """
        Generate Cypher query for multi-hop reasoning
        
        Args:
            question: User question
            max_hops: Maximum relationship depth (2-3)
        
        Returns:
            {
                'cypher': str,
                'explanation': str,
                'target_entities': List[str],
                'reasoning_type': str
            }
        """
        
        system_prompt = """You are an expert in knowledge graph reasoning and Cypher query generation.

Your task: Generate a multi-hop Cypher query (2-3 hops) to answer complex questions.

Output JSON with:
1. "cypher": The Cypher query (MUST use variable-length patterns like [*1..3])
2. "explanation": Brief explanation of the reasoning strategy
3. "target_entities": List of entities to start from
4. "reasoning_type": One of ["risk_chain", "influence_propagation", "causal_inference", "impact_analysis"]

Query Requirements:
- Use variable-length path patterns: (start)-[*1..3]->(end)
- Capture full path: WITH path, nodes(path) as pathNodes, relationships(path) as pathRels
- Filter by relationship types: WHERE ALL(r IN pathRels WHERE type(r) IN [...])
- Return structured results with path details

Examples:

Q: "How does Taiwan tension affect Nvidia?"
A: {
  "cypher": "MATCH path = (m:MacroIndicator {name: 'Taiwan Strait Tension'})-[*1..3]->(n) WHERE n.name =~ '(?i).*nvidia.*' WITH path, nodes(path) as pathNodes, [r IN relationships(path) | type(r)] as pathRels RETURN pathNodes, pathRels, length(path) as hops ORDER BY hops ASC LIMIT 10",
  "explanation": "Find paths from Taiwan tension to Nvidia through intermediate nodes (country, industry, suppliers)",
  "target_entities": ["Taiwan Strait Tension", "Nvidia"],
  "reasoning_type": "risk_chain"
}

Q: "What are the cascading effects of US-China trade war?"
A: {
  "cypher": "MATCH path = (m:MacroIndicator {name: 'US-China Trade War'})-[*1..3]->(target) WHERE type(target) IN ['Company', 'Industry', 'Country'] WITH path, nodes(path) as pathNodes, [r IN relationships(path) | {type: type(r), props: properties(r)}] as pathRels RETURN DISTINCT pathNodes, pathRels, length(path) as hops ORDER BY hops ASC LIMIT 20",
  "explanation": "Trace multi-hop impact propagation from trade war through industries to specific companies",
  "target_entities": ["US-China Trade War"],
  "reasoning_type": "influence_propagation"
}

Q: "Why is Nvidia exposed to geopolitical risk?"
A: {
  "cypher": "MATCH path = (c:Company {name: 'Nvidia'})-[*1..3]-(geo) WHERE geo:MacroIndicator AND geo.type = 'geopolitical' WITH path, nodes(path) as pathNodes, [r IN relationships(path) | type(r)] as pathRels, [n IN nodes(path) | labels(n)[0] + ': ' + n.name] as pathLabels RETURN pathNodes, pathRels, pathLabels, length(path) as hops ORDER BY hops ASC LIMIT 15",
  "explanation": "Find all paths connecting Nvidia to geopolitical macro indicators through supply chain and location dependencies",
  "target_entities": ["Nvidia"],
  "reasoning_type": "causal_inference"
}

Now generate a query for the user's question."""

        user_message = f"Question: {question}\n\nGenerate multi-hop Cypher query (max {max_hops} hops)."
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            print(f"🔍 Generated query type: {result.get('reasoning_type', 'unknown')}")
            return result
            
        except Exception as e:
            print(f"⚠️  Query generation failed: {e}")
            # Fallback: generic multi-hop query
            return {
                'cypher': f"MATCH path = (n)-[*1..{max_hops}]->(m) RETURN path LIMIT 10",
                'explanation': 'Generic multi-hop exploration',
                'target_entities': [],
                'reasoning_type': 'generic'
            }
    
    def execute_multihop_query(self, cypher: str) -> List[Dict[str, Any]]:
        """
        Execute Cypher query and return paths
        
        Returns:
            List of paths with nodes and relationships
        """
        paths = []
        
        with self.neo4j_driver.session() as session:
            result = session.run(cypher)
            
            for record in result:
                path_data = {
                    'nodes': [],
                    'relationships': [],
                    'hops': record.get('hops', 0)
                }
                
                # Extract path nodes
                if 'pathNodes' in record:
                    path_data['nodes'] = [
                        {
                            'name': node.get('name', 'Unknown'),
                            'type': list(node.labels)[0] if node.labels else 'Unknown',
                            'properties': dict(node)
                        }
                        for node in record['pathNodes']
                    ]
                
                # Extract relationships
                if 'pathRels' in record:
                    if isinstance(record['pathRels'], list):
                        # Handle both string list and object list
                        path_data['relationships'] = [
                            rel if isinstance(rel, str) else rel.get('type', 'RELATED')
                            for rel in record['pathRels']
                        ]
                
                # Extract labels if available
                if 'pathLabels' in record:
                    path_data['labels'] = record['pathLabels']
                
                paths.append(path_data)
        
        return paths
    
    async def reason(self, question: str, max_hops: int = 3) -> Dict[str, Any]:
        """
        Perform complete multi-hop reasoning
        
        Args:
            question: User question
            max_hops: Maximum reasoning depth
        
        Returns:
            {
                'question': str,
                'reasoning_paths': List[Dict],
                'inference': str,  # Logical conclusion
                'confidence': float
            }
        """
        
        # Step 1: Generate query
        query_spec = await self.generate_multihop_query(question, max_hops)
        
        # Step 2: Execute query
        paths = self.execute_multihop_query(query_spec['cypher'])
        
        if not paths:
            return {
                'question': question,
                'reasoning_paths': [],
                'inference': 'No reasoning paths found in knowledge graph.',
                'confidence': 0.0
            }
        
        # Step 3: Generate logical inference
        inference = await self._generate_inference(question, paths, query_spec)
        
        return {
            'question': question,
            'reasoning_type': query_spec.get('reasoning_type', 'unknown'),
            'reasoning_paths': paths,
            'inference': inference['conclusion'],
            'confidence': inference['confidence'],
            'reasoning_steps': inference.get('steps', [])
        }
    
    async def _generate_inference(
        self,
        question: str,
        paths: List[Dict[str, Any]],
        query_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate logical inference from reasoning paths
        
        Returns:
            {
                'conclusion': str,
                'confidence': float,
                'steps': List[str]  # Reasoning chain
            }
        """
        
        # Format paths for LLM
        path_descriptions = []
        for i, path in enumerate(paths[:10], 1):  # Limit to top 10
            nodes = path.get('nodes', [])
            rels = path.get('relationships', [])
            
            if nodes:
                node_names = [n.get('name', 'Unknown') for n in nodes]
                path_str = " → ".join([
                    f"{node_names[j]} --[{rels[j] if j < len(rels) else 'RELATED'}]->"
                    for j in range(len(node_names) - 1)
                ]) + f" {node_names[-1]}"
                
                path_descriptions.append(f"{i}. {path_str} ({path.get('hops', 0)} hops)")
        
        paths_text = "\n".join(path_descriptions)
        
        system_prompt = """You are a financial analyst performing logical reasoning on knowledge graph data.

Your task: Analyze multi-hop reasoning paths and generate a logical inference.

Output JSON with:
1. "conclusion": Final inference (2-3 sentences explaining A→B→C→D logic)
2. "confidence": 0.0-1.0 (based on path strength and evidence)
3. "steps": List of reasoning steps showing the causal chain

Requirements:
- Start with "Because A affects B, and B affects C, therefore..."
- Explain the logical chain clearly
- Quantify confidence based on:
  * Number of paths found
  * Relationship strength (criticality, severity)
  * Path diversity (multiple routes = higher confidence)

Example:
{
  "conclusion": "Because Nvidia depends on TSMC (high criticality), and TSMC is located in Taiwan, and Taiwan faces geopolitical tension, therefore Nvidia is exposed to significant supply chain disruption risk from Taiwan Strait conflict.",
  "confidence": 0.85,
  "steps": [
    "Nvidia → DEPENDS_ON → TSMC (high criticality dependency)",
    "TSMC → LOCATED_IN → Taiwan (manufacturing base)",
    "Taiwan Strait Tension → AFFECTS → Taiwan (severity: 0.95)",
    "Conclusion: Geopolitical risk propagates through supply chain"
  ]
}"""

        user_message = f"""Question: {question}

Reasoning Type: {query_spec.get('reasoning_type', 'unknown')}

Found Paths:
{paths_text}

Perform logical inference and explain the causal chain."""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"⚠️  Inference generation failed: {e}")
            return {
                'conclusion': f'Found {len(paths)} reasoning paths. Manual analysis required.',
                'confidence': 0.5,
                'steps': []
            }
    
    def format_reasoning_for_display(self, reasoning_result: Dict[str, Any]) -> str:
        """
        Format reasoning result for Streamlit display
        
        Returns:
            Markdown formatted text
        """
        output = [
            f"# 🧠 Multi-Hop Reasoning Analysis\n",
            f"**Question:** {reasoning_result['question']}\n",
            f"**Reasoning Type:** {reasoning_result.get('reasoning_type', 'unknown').replace('_', ' ').title()}\n",
            f"**Confidence:** {reasoning_result['confidence']:.1%}\n",
            "---\n",
            "## 💡 Logical Inference\n",
            reasoning_result['inference'],
            "\n\n## 🔗 Reasoning Chain\n"
        ]
        
        for i, step in enumerate(reasoning_result.get('reasoning_steps', []), 1):
            output.append(f"{i}. {step}")
        
        output.append("\n\n## 📊 Evidence Paths\n")
        
        for i, path in enumerate(reasoning_result.get('reasoning_paths', [])[:5], 1):
            nodes = path.get('nodes', [])
            rels = path.get('relationships', [])
            
            if nodes:
                path_str = " → ".join([
                    f"**{nodes[j].get('name', 'Unknown')}** ({nodes[j].get('type', 'Unknown')})"
                    + (f" --[{rels[j]}]-->" if j < len(rels) else "")
                    for j in range(len(nodes))
                ])
                
                output.append(f"\n### Path {i} ({path.get('hops', 0)} hops)")
                output.append(path_str)
        
        return "\n".join(output)


async def example_reasoning():
    """Example: How to use MultiHopReasoner"""
    
    reasoner = MultiHopReasoner()
    
    # Example questions
    questions = [
        "How does Taiwan tension affect Nvidia?",
        "What are the cascading effects of US-China trade war?",
        "Why is Nvidia exposed to geopolitical risk?"
    ]
    
    for question in questions:
        print(f"\n{'='*60}")
        print(f"Q: {question}")
        print('='*60)
        
        result = await reasoner.reason(question, max_hops=3)
        
        print(f"\n💡 Inference:")
        print(result['inference'])
        print(f"\n📊 Confidence: {result['confidence']:.1%}")
        print(f"\n🔗 Found {len(result['reasoning_paths'])} reasoning paths")
        
        # Show first path
        if result['reasoning_paths']:
            path = result['reasoning_paths'][0]
            nodes = [n.get('name') for n in path.get('nodes', [])]
            print(f"\nExample path: {' → '.join(nodes)}")
    
    reasoner.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_reasoning())
