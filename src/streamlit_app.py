"""
Tech-Analyst GraphRAG - Simplified UI
"""

import streamlit as st
import requests
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from utils.error_logger import droneLogError
except Exception:
    def droneLogError(message: str, error: Exception | None = None) -> None:
        return

load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="Tech-Analyst GraphRAG",
    page_icon="📊",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: #ffffff;
}

.report-container {
    background: #1a1d29;
    padding: 2rem;
    border-radius: 12px;
    margin: 1.5rem 0;
    border: 1px solid #2d3142;
}

.report-container h2 {
    color: #ffffff !important;
    font-size: 1.5rem;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    border-bottom: 2px solid #3d4461;
    padding-bottom: 0.5rem;
}

.report-container p {
    color: #e0e0e0 !important;
    line-height: 1.7;
}

.metric-card {
    background: #1e2330;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #3d4461;
    text-align: center;
}

.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #4a9eff;
}

.metric-label {
    font-size: 0.9rem;
    color: #a0a0a0;
    margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Header
st.title("Tech-Analyst GraphRAG")
st.markdown("Knowledge Graph for Financial Analysis")

st.divider()

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Query", "Upload PDF", "Database Upload", "Visualization"])

# Tab 1: Query
with tab1:
    # Fixed settings (no UI controls)
    enable_web_search = False  # 기본값: Neo4j 그래프 우선 사용
    temperature = 0.2  # Fixed for consistent analysis

    # Main content
    col1 = st.container()

    with col1:
        st.subheader("Ask a Question")
    
    # Query input
    user_query = st.text_area(
        "Enter your question",
        placeholder="e.g., What is Nvidia's latest GPU architecture?",
        height=100,
        key="query_input"
    )
    
    # Submit button
    submit_button = st.button("Analyze", type="primary", use_container_width=True)
    
    # Process query (통합)
    if submit_button and user_query:
        with st.spinner("Analyzing with GraphRAG..."):
            try:
                # Call API
                response = requests.post(
                    f"{API_BASE_URL}/query",
                    json={
                        "question": user_query,
                        "mode": "local",
                        "temperature": temperature,
                        "enable_web_search": False,  # 웹 검색 비활성화 (로컬만)
                        "search_type": "local",
                        "top_k": 30
                    },
                    timeout=90
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "Unable to generate answer.")
                    sources = data.get("sources", [])
                    
                    # Add to history
                    st.session_state.chat_history.append({
                        "query": user_query,
                        "answer": answer,
                        "type": "graphrag"
                    })
                    
                    # Display answer (참조 자료 섹션 제거)
                    st.markdown("### Analysis Result")
                    st.markdown(f'<div class="report-container">{answer}</div>', unsafe_allow_html=True)
                
                elif response.status_code == 500:
                    st.error("서버 처리 중 오류가 발생했습니다.")
                elif response.status_code == 503:
                    st.error("서비스를 사용할 수 없습니다.")
                else:
                    st.error(f"Error: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
        # Chat History
        if st.session_state.chat_history:
            st.divider()
            st.subheader("Recent Queries")
            
            for i, item in enumerate(reversed(st.session_state.chat_history[-3:])):
                with st.expander(f"{item['query'][:60]}..."):
                    st.markdown(item['answer'])

# Tab 2: Upload PDF (로컬 모델만 사용)
with tab2:
    st.subheader("Upload PDF Document")
    
    st.markdown("📄 Upload financial reports or industry analysis PDFs")
    st.info("로컬 모델(Ollama)을 사용하여 PDF를 처리하고 기존 그래프에 병합합니다.")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf']
    )
    
    if uploaded_file is not None:
        st.info(f"File: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        
        if st.button("Process PDF", type="primary"):
            with st.spinner("로컬 모델로 처리 중... (시간이 걸릴 수 있습니다)"):
                try:
                    # Send PDF to backend (로컬 모델 사용)
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'application/pdf')}
                    response = requests.post(
                        f"{API_BASE_URL}/ingest_pdf",
                        files=files,
                        timeout=600  # 10분 타임아웃 (Ollama 처리 시간)
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ PDF가 성공적으로 처리되어 그래프에 병합되었습니다!")
                        
                        # 결과 표시
                        if result.get("entities_extracted"):
                            st.info(f"추출된 엔티티: {result['entities_extracted']}개")
                        if result.get("relationships_created"):
                            st.info(f"생성된 관계: {result['relationships_created']}개")
                    else:
                        st.error(f"Error processing PDF: {response.status_code}")
                        droneLogError("PDF upload failed in UI (tab2)", Exception(f"status={response.status_code}"))

                except Exception as e:
                    droneLogError("PDF upload exception in UI (tab2)", e)
                    st.error(f"Error: {str(e)}")

# Tab 3: Database Upload
with tab3:
    st.subheader("Database Upload (OpenAI)")
    st.markdown("Merge PDF into Neo4j graph database")
    
    pdf_db_file = st.file_uploader(
        "Choose PDF file",
        type=['pdf'],
        key="db_pdf_upload"
    )

    if pdf_db_file:
        st.info(f"File: {pdf_db_file.name} ({pdf_db_file.size / 1024:.1f} KB)")
        if st.button("Process & Merge", type="primary", key="db_pdf_upload_btn"):
            with st.spinner("Processing with OpenAI API..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/ingest_pdf_db",
                        files={"file": pdf_db_file},
                        timeout=600  # 10분으로 증가
                    )
                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ PDF가 성공적으로 업로드되어 Neo4j 데이터베이스에 저장되었습니다.")
                        
                        # 업로드 결과 요약
                        col_info1, col_info2 = st.columns(2)
                        with col_info1:
                            st.info(f"📄 파일: {pdf_db_file.name}")
                        with col_info2:
                            st.info(f"📊 추출: {result.get('entities_extracted', 0)} 엔티티, {result.get('relationships_extracted', 0)} 관계")
                        
                        # 새로고침 안내
                        st.markdown("💡 **Visualization 탭**으로 이동하여 업로드된 데이터를 확인하세요.")
                        
                        # 자동 새로고침을 위한 session state 업데이트
                        if 'last_upload_time' not in st.session_state:
                            st.session_state.last_upload_time = 0
                        import time
                        st.session_state.last_upload_time = time.time()
                    else:
                        st.error(f"Upload failed: {response.status_code}")
                        droneLogError("PDF DB upload failed in UI (tab3)", Exception(f"status={response.status_code}"))
                except Exception as e:
                    droneLogError("PDF DB upload exception in UI (tab3)", e)
                    st.error(f"Error: {str(e)}")

# CSV/JSON upload sections removed per user request

# Tab 4: Graph Visualization
with tab4:
    try:
        from neo4j import GraphDatabase
        import pandas as pd
        
        NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
        NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

        if not NEO4J_PASSWORD:
            st.error("Neo4j password not set in .env")
        else:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

            with driver.session() as session:
                # 데이터베이스에 저장된 파일 목록 표시
                st.subheader("📁 데이터베이스에 저장된 파일")
                files_result = session.run("""
                    MATCH (n)
                    WHERE n.source_file IS NOT NULL
                    RETURN DISTINCT n.source_file as file, count(n) as node_count
                    ORDER BY file
                """)
                
                files_data = files_result.data()
                if files_data:
                    df_files = pd.DataFrame(files_data)
                    df_files.columns = ['파일명', '노드 수']
                    st.dataframe(df_files, use_container_width=True)
                    st.caption(f"총 {len(files_data)}개 파일, {df_files['노드 수'].sum()}개 노드")
                else:
                    st.info("데이터베이스에 저장된 파일이 없습니다. Database Upload 탭에서 PDF를 업로드하세요.")
                
                st.divider()
                
                # Risk Factors 표시
                st.subheader("⚠️ Risk Factors")
                result = session.run("""
                    MATCH (r:Risk)
                    RETURN r.name as name, r.impact_level as impact, r.description as description, r.source_file as source
                    ORDER BY r.impact_level DESC
                    LIMIT 20
                """)
                
                risks = result.data()
                if risks:
                    df_risk = pd.DataFrame(risks)
                    df_risk.columns = ['Risk Name', 'Impact Level', 'Description', 'Source']
                    # None 값을 빈 문자열로 변경
                    df_risk = df_risk.fillna('')
                    st.dataframe(df_risk, use_container_width=True)
                    
                    # None 값이 많은 경우 안내 메시지
                    none_count = sum(1 for r in risks if not r['impact'] and not r['description'])
                    if none_count > len(risks) * 0.5:
                        st.warning(f"⚠️ Risk Factor의 속성 정보가 부족합니다 ({none_count}/{len(risks)}개). 더 나은 데이터를 위해 아래 명령어를 실행하세요:")
                        st.code("python scripts/seed/seed_semiconductor.py", language="bash")
                else:
                    st.info("데이터베이스에 Risk Factor가 없습니다.")
                    st.markdown("**Risk Factor 추가 방법:**")
                    st.code("python scripts/seed/seed_semiconductor.py", language="bash")
        
            driver.close()

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("Neo4j가 실행 중인지 확인하세요.")

# Tab 4: Graph Visualization
with tab4:
    st.subheader("Graph Visualization")
    
    # Visualization options
    col1, col2 = st.columns(2)
    with col1:
        max_nodes = st.slider("Max Nodes", 10, 100, 30)
    with col2:
        layout = st.selectbox("Layout", ["Force-directed", "Hierarchical", "Circular"])
    
    if st.button("Generate", type="primary"):
        with st.spinner("Generating graph visualization..."):
            try:
                # Direct Neo4j query for visualization
                NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
                NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
                NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

                from neo4j import GraphDatabase
                import json

                if not NEO4J_PASSWORD:
                    st.error("Neo4j password not set in .env")
                    droneLogError("Neo4j password missing for visualization (graph view)")
                    raise RuntimeError("Neo4j password missing")

                driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

                with driver.session() as session:
                    # Get nodes and relationships
                    query = f"""
                    MATCH (n)
                    WITH n LIMIT {max_nodes}
                    OPTIONAL MATCH (n)-[r]->(m)
                    RETURN n, r, m
                    """
                    
                    result = session.run(query)
                    
                    nodes = {}
                    edges = []
                    
                    for record in result:
                        # Process source node
                        if record['n']:
                            node = record['n']
                            node_id = id(node)
                            if node_id not in nodes:
                                labels = list(node.labels)
                                nodes[node_id] = {
                                    'id': node_id,
                                    'label': node.get('name', str(node_id)),
                                    'group': labels[0] if labels else 'Unknown',
                                    'title': f"{labels[0] if labels else 'Node'}: {node.get('name', 'N/A')}"
                                }
                        
                        # Process target node and relationship
                        if record['m'] and record['r']:
                            target = record['m']
                            target_id = id(target)
                            
                            if target_id not in nodes:
                                labels = list(target.labels)
                                nodes[target_id] = {
                                    'id': target_id,
                                    'label': target.get('name', str(target_id)),
                                    'group': labels[0] if labels else 'Unknown',
                                    'title': f"{labels[0] if labels else 'Node'}: {target.get('name', 'N/A')}"
                                }
                            
                            rel = record['r']
                            edges.append({
                                'from': node_id,
                                'to': target_id,
                                'label': type(rel).__name__,
                                'title': type(rel).__name__
                            })
                
                driver.close()
                
                if not nodes:
                    st.warning("No data found in database. Please seed the database first.")
                else:
                    st.success(f"Found {len(nodes)} nodes and {len(edges)} relationships")
                    
                    # Create visualization HTML
                    nodes_list = list(nodes.values())
                    
                    # Color mapping for different node types
                    color_map = {
                        'Company': '#4A9EFF',
                        'Technology': '#FF6B6B',
                        'Risk': '#FFA500',
                        'Regulation': '#9B59B6',
                        'Entity': '#95E1D3'
                    }
                    
                    # Add colors to nodes
                    for node in nodes_list:
                        node['color'] = color_map.get(node['group'], '#CCCCCC')
                    
                    # Generate HTML
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
                        <style>
                            #mynetwork {{
                                width: 100%;
                                height: 600px;
                                border: 1px solid #ddd;
                                background: #1a1d29;
                            }}
                            .legend {{
                                position: absolute;
                                top: 10px;
                                right: 10px;
                                background: rgba(26, 29, 41, 0.9);
                                padding: 10px;
                                border-radius: 5px;
                                color: white;
                                font-size: 12px;
                            }}
                            .legend-item {{
                                margin: 5px 0;
                            }}
                            .legend-color {{
                                display: inline-block;
                                width: 15px;
                                height: 15px;
                                margin-right: 5px;
                                border-radius: 3px;
                            }}
                        </style>
                    </head>
                    <body>
                        <div id="mynetwork"></div>
                        <div class="legend">
                            <div class="legend-item"><span class="legend-color" style="background: #4A9EFF;"></span>Company</div>
                            <div class="legend-item"><span class="legend-color" style="background: #FF6B6B;"></span>Technology</div>
                            <div class="legend-item"><span class="legend-color" style="background: #FFA500;"></span>Risk</div>
                            <div class="legend-item"><span class="legend-color" style="background: #9B59B6;"></span>Regulation</div>
                        </div>
                        <script type="text/javascript">
                            var nodes = new vis.DataSet({json.dumps(nodes_list)});
                            var edges = new vis.DataSet({json.dumps(edges)});
                            
                            var container = document.getElementById('mynetwork');
                            var data = {{
                                nodes: nodes,
                                edges: edges
                            }};
                            
                            var options = {{
                                nodes: {{
                                    shape: 'dot',
                                    size: 16,
                                    font: {{
                                        size: 12,
                                        color: '#ffffff'
                                    }},
                                    borderWidth: 2,
                                    borderWidthSelected: 4
                                }},
                                edges: {{
                                    width: 2,
                                    color: {{
                                        color: '#848484',
                                        highlight: '#4A9EFF'
                                    }},
                                    arrows: {{
                                        to: {{
                                            enabled: true,
                                            scaleFactor: 0.5
                                        }}
                                    }},
                                    smooth: {{
                                        type: 'continuous'
                                    }},
                                    font: {{
                                        size: 10,
                                        color: '#ffffff',
                                        strokeWidth: 0
                                    }}
                                }},
                                physics: {{
                                    enabled: {'true' if layout == 'Force-directed' else 'false'},
                                    stabilization: {{
                                        iterations: 200
                                    }},
                                    barnesHut: {{
                                        gravitationalConstant: -8000,
                                        springConstant: 0.04,
                                        springLength: 95
                                    }}
                                }},
                                layout: {{
                                    {'hierarchical: { direction: "UD", sortMethod: "directed" }' if layout == 'Hierarchical' else ''}
                                }},
                                interaction: {{
                                    hover: true,
                                    tooltipDelay: 100,
                                    zoomView: true,
                                    dragView: true
                                }}
                            }};
                            
                            var network = new vis.Network(container, data, options);
                            
                            network.on("click", function(params) {{
                                if (params.nodes.length > 0) {{
                                    var nodeId = params.nodes[0];
                                    var node = nodes.get(nodeId);
                                    console.log("Clicked node:", node);
                                }}
                            }});
                        </script>
                    </body>
                    </html>
                    """
                    
                    # Display in Streamlit
                    st.components.v1.html(html_content, height=650, scrolling=False)
                    
                    # Show statistics
                    st.divider()
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Nodes", len(nodes))
                    with col2:
                        st.metric("Total Edges", len(edges))
                    with col3:
                        node_types = {}
                        for node in nodes_list:
                            group = node['group']
                            node_types[group] = node_types.get(group, 0) + 1
                        st.metric("Node Types", len(node_types))
                    
                    # Show node type breakdown
                    st.subheader("Node Distribution")
                    import pandas as pd
                    df = pd.DataFrame(list(node_types.items()), columns=['Type', 'Count'])
                    st.dataframe(df, use_container_width=True)
                    
            except Exception as e:
                droneLogError("Graph visualization generation failed", e)
                st.error(f"Error generating visualization: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

# Footer
st.divider()

# Clear history button
if st.button("Clear History", use_container_width=True):
    st.session_state.chat_history = []
    st.rerun()

st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem; margin-top: 2rem;'>
    Tech-Analyst GraphRAG v2.0
</div>
""", unsafe_allow_html=True)
