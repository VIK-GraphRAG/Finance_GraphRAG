#!/usr/bin/env python3
"""
Neo4j Graph Visualizer for Streamlit
Real-time graph visualization using vis.js
"""

import streamlit as st
import streamlit.components.v1 as components
from neo4j import GraphDatabase
import json
import os

# Load environment
from dotenv import load_dotenv
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def fetch_graph_data(query: str = None, limit: int = 100):
    """Fetch graph data from Neo4j"""
    
    if not query:
        # Default: Show all nodes and relationships
        query = f"""
        MATCH (n)-[r]->(m)
        RETURN n, r, m
        LIMIT {limit}
        """
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    nodes = {}
    edges = []
    
    with driver.session() as session:
        result = session.run(query)
        
        for record in result:
            # Process source node
            if 'n' in record:
                n = record['n']
                node_id = n.element_id
                if node_id not in nodes:
                    nodes[node_id] = {
                        'id': node_id,
                        'label': n.get('name', str(n.element_id)[:8]),
                        'title': f"{list(n.labels)[0] if n.labels else 'Node'}: {n.get('name', 'Unknown')}",
                        'group': list(n.labels)[0] if n.labels else 'default',
                        'properties': dict(n)
                    }
            
            # Process target node
            if 'm' in record:
                m = record['m']
                node_id = m.element_id
                if node_id not in nodes:
                    nodes[node_id] = {
                        'id': node_id,
                        'label': m.get('name', str(m.element_id)[:8]),
                        'title': f"{list(m.labels)[0] if m.labels else 'Node'}: {m.get('name', 'Unknown')}",
                        'group': list(m.labels)[0] if m.labels else 'default',
                        'properties': dict(m)
                    }
            
            # Process relationship
            if 'r' in record:
                r = record['r']
                edges.append({
                    'from': record['n'].element_id,
                    'to': record['m'].element_id,
                    'label': r.type,
                    'title': f"{r.type}: {dict(r)}",
                    'arrows': 'to'
                })
    
    driver.close()
    
    return list(nodes.values()), edges


def create_vis_html(nodes, edges):
    """Create vis.js HTML for graph visualization"""
    
    # Color scheme for different node types
    colors = {
        'Company': '#FF6B6B',
        'Country': '#4ECDC4',
        'Industry': '#45B7D1',
        'MacroIndicator': '#FFA07A',
        'FinancialMetric': '#98D8C8',
        'default': '#95A5A6'
    }
    
    # Prepare nodes with colors
    for node in nodes:
        group = node.get('group', 'default')
        node['color'] = colors.get(group, colors['default'])
        node['shape'] = 'dot'
        node['size'] = 20
    
    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: #0e1117;
            }}
            #mynetwork {{
                width: 100%;
                height: 800px;
                border: 1px solid #2d3142;
                background-color: #1a1d29;
            }}
            .legend {{
                position: absolute;
                top: 10px;
                right: 10px;
                background: rgba(30, 35, 48, 0.9);
                padding: 15px;
                border-radius: 8px;
                color: white;
                font-family: monospace;
                font-size: 12px;
                border: 1px solid #4a9eff;
            }}
            .legend-item {{
                display: flex;
                align-items: center;
                margin: 5px 0;
            }}
            .legend-color {{
                width: 15px;
                height: 15px;
                border-radius: 50%;
                margin-right: 10px;
            }}
        </style>
    </head>
    <body>
        <div id="mynetwork"></div>
        <div class="legend">
            <div style="font-weight: bold; margin-bottom: 10px;">📊 Node Types</div>
            <div class="legend-item">
                <div class="legend-color" style="background: #FF6B6B;"></div>
                <span>Company</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #4ECDC4;"></div>
                <span>Country</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #45B7D1;"></div>
                <span>Industry</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #FFA07A;"></div>
                <span>MacroIndicator</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #98D8C8;"></div>
                <span>FinancialMetric</span>
            </div>
        </div>
        
        <script type="text/javascript">
            var nodes = new vis.DataSet({nodes_json});
            var edges = new vis.DataSet({edges_json});
            
            var container = document.getElementById('mynetwork');
            var data = {{
                nodes: nodes,
                edges: edges
            }};
            
            var options = {{
                nodes: {{
                    font: {{
                        color: '#ffffff',
                        size: 14
                    }},
                    borderWidth: 2,
                    borderWidthSelected: 4
                }},
                edges: {{
                    width: 2,
                    color: {{
                        color: '#4a9eff',
                        highlight: '#6bb3ff',
                        hover: '#6bb3ff'
                    }},
                    font: {{
                        color: '#ffffff',
                        size: 12,
                        background: 'rgba(30, 35, 48, 0.8)'
                    }},
                    smooth: {{
                        type: 'continuous'
                    }}
                }},
                physics: {{
                    enabled: true,
                    barnesHut: {{
                        gravitationalConstant: -8000,
                        centralGravity: 0.3,
                        springLength: 150,
                        springConstant: 0.04
                    }},
                    stabilization: {{
                        iterations: 150
                    }}
                }},
                interaction: {{
                    hover: true,
                    tooltipDelay: 200,
                    navigationButtons: true,
                    keyboard: true
                }}
            }};
            
            var network = new vis.Network(container, data, options);
            
            network.on("stabilizationIterationsDone", function () {{
                network.setOptions({{ physics: false }});
            }});
            
            // Highlight connected nodes on click
            network.on("selectNode", function(params) {{
                var nodeId = params.nodes[0];
                var connectedNodes = network.getConnectedNodes(nodeId);
                var connectedEdges = network.getConnectedEdges(nodeId);
                
                console.log("Selected:", nodes.get(nodeId).label);
                console.log("Connected to:", connectedNodes.map(id => nodes.get(id).label));
            }});
        </script>
    </body>
    </html>
    """
    
    return html


def main():
    st.set_page_config(
        page_title="Knowledge Graph Visualizer",
        page_icon="🕸️",
        layout="wide"
    )
    
    st.title("🕸️ Financial Knowledge Graph Visualizer")
    st.markdown("---")
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Settings")
        
        viz_mode = st.radio(
            "Visualization Mode",
            ["All Nodes", "Company Focus", "Risk Analysis", "Custom Query"],
            help="Choose what to visualize"
        )
        
        limit = st.slider("Max Nodes", 10, 500, 100, 10)
        
        if viz_mode == "Company Focus":
            company = st.selectbox(
                "Select Company",
                ["Nvidia", "TSMC", "AMD", "Intel", "Samsung Electronics"]
            )
        
        refresh = st.button("🔄 Refresh Graph", type="primary")
    
    # Generate query based on mode
    query = None
    if viz_mode == "All Nodes":
        query = f"MATCH (n)-[r]->(m) RETURN n, r, m LIMIT {limit}"
    elif viz_mode == "Company Focus":
        query = f"""
        MATCH (c:Company {{name: '{company}'}})-[r*1..2]-(related)
        WITH c, r, related
        MATCH (c)-[direct_r]-(related)
        RETURN c as n, direct_r as r, related as m
        LIMIT {limit}
        """
    elif viz_mode == "Risk Analysis":
        query = f"""
        MATCH (m:MacroIndicator)-[r1:IMPACTS|AFFECTS]->(target)
        MATCH (target)-[r2:OPERATES_IN|LOCATED_IN]-(entity)
        RETURN m as n, r1 as r, target as m
        UNION
        MATCH (target)-[r2]-(entity)
        WHERE target:Country OR target:Industry
        RETURN target as n, r2 as r, entity as m
        LIMIT {limit}
        """
    elif viz_mode == "Custom Query":
        custom_query = st.text_area(
            "Cypher Query",
            "MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50",
            height=100
        )
        if st.button("Execute Query"):
            query = custom_query
    
    # Fetch and display graph
    try:
        with st.spinner("Fetching graph data..."):
            nodes, edges = fetch_graph_data(query, limit)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nodes", len(nodes))
        with col2:
            st.metric("Edges", len(edges))
        with col3:
            st.metric("Density", f"{len(edges) / max(len(nodes), 1):.2f}")
        
        if nodes and edges:
            # Create and display visualization
            html = create_vis_html(nodes, edges)
            components.html(html, height=850, scrolling=False)
            
            # Show node details
            with st.expander("📊 Node Details"):
                st.json({
                    node['label']: {
                        'type': node['group'],
                        'properties': node.get('properties', {})
                    }
                    for node in nodes[:10]  # Show first 10
                })
        else:
            st.warning("No graph data found. Run seed_financial_data.py first!")
            
    except Exception as e:
        st.error(f"Error: {e}")
        st.info("💡 Make sure Neo4j is running and seed data is loaded")
        
        if st.button("Run Seed Data"):
            st.code("python3 seed_financial_data.py", language="bash")


if __name__ == "__main__":
    main()
