"""
Tech-Analyst GraphRAG - Simplified UI
"""

import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="Tech-Analyst GraphRAG",
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
st.markdown("Real-time Search + Knowledge Graph for Financial Analysis")

# Privacy Mode 강제 활성화 알림
st.success("Privacy Mode 활성화: 모든 사용자 데이터는 로컬 Ollama 모델로만 처리되며 외부로 전송되지 않습니다.")
st.divider()

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Query", "Upload PDF", "Database Upload", "Graph Visualization"])

# Tab 1: Query
with tab1:
    # Fixed settings (no UI controls)
    enable_web_search = True  # Always enabled for real-time intelligence
    temperature = 0.2  # Fixed for consistent analysis

    # Main content
    col1 = st.container()

    with col1:
        st.subheader("Ask a Question")
        
        # 분석 모드 설명 추가
        with st.expander("분석 모드 차이점", expanded=False):
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                st.markdown("""
                ### Analyze (빠른 분석)
                - **처리 시간**: 10-30초
                - **방식**: 단일 GraphRAG 검색
                - **용도**: 간단한 질문, 빠른 답변
                - **모델**: 로컬 Ollama (qwen2.5-coder:3b)
                - **예시**: "Nvidia의 매출은?"
                """)
            
            with col_info2:
                st.markdown("""
                ### Deep Analysis (심층 분석)
                - **처리 시간**: 30-60초
                - **방식**: Multi-Agent 협업 파이프라인
                - **용도**: 복잡한 분석, 다각도 검토
                - **파이프라인**: Master → KB Collector → Analyst → Writer
                - **예시**: "Nvidia의 공급망 리스크 분석"
                """)
    
    # Query input
    user_query = st.text_area(
        "Enter your question",
        placeholder="e.g., What is Nvidia's latest GPU architecture?",
        height=100,
        key="query_input"
    )
    
    # Submit button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        multihop_button = st.button("Multi-Hop", type="primary", use_container_width=True, help="멀티홉 추론 + Perplexity 폴백 (10-30초)")
    
    with col_btn2:
        agentic_button = st.button("Deep Analysis", use_container_width=True, help="Multi-Agent 심층 분석 (30-60초)")
    
    # Process query
    if multihop_button and user_query:
        with st.spinner("Multi-hop reasoning..."):
            try:
                # Call Multi-Hop API
                response = requests.post(
                    f"{API_BASE_URL}/query_multihop",
                    json={
                        "question": user_query,
                        "mode": "local",
                        "temperature": temperature,
                        "enable_web_search": enable_web_search
                    },
                    timeout=90
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "Unable to generate answer.")
                    confidence = data.get("confidence", 0.0)
                    source_type = data.get("source_type", "unknown")
                    fallback_used = data.get("fallback_used", False)
                    
                    # Add to history
                    st.session_state.chat_history.append({
                        "query": user_query,
                        "answer": answer,
                        "type": "multihop",
                        "confidence": confidence,
                        "source": source_type
                    })
                    
                    # Display answer
                    st.markdown("### Multi-Hop Reasoning Result")
                    
                    # Source indicator
                    if fallback_used:
                        st.info("Perplexity API fallback used (low confidence from knowledge graph)")
                    elif "low_confidence" in source_type:
                        st.warning(f"Low confidence result: {confidence:.1%}")
                    else:
                        st.success(f"Knowledge graph result: {confidence:.1%}")
                    
                    st.markdown(f'<div class="report-container">{answer}</div>', unsafe_allow_html=True)
                    
                    # Show reasoning path if available
                    if data.get("reasoning_path"):
                        with st.expander("Reasoning Path"):
                            for i, step in enumerate(data["reasoning_path"], 1):
                                st.markdown(f"**Step {i}:** {step.get('description', '')}")
                    
                    # Show sources
                    if data.get("sources"):
                        with st.expander("Sources"):
                            for source in data["sources"]:
                                st.markdown(f"- **{source.get('file', 'Unknown')}**")
                                if source.get('url'):
                                    st.markdown(f"  URL: {source['url']}")
                                if source.get('content'):
                                    st.markdown(f"  {source['content'][:200]}...")
                else:
                    st.error(f"Error: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    elif agentic_button and user_query:
        with st.spinner("Deep analysis in progress... (30-60 seconds)"):
            try:
                # Call Agentic API
                response = requests.post(
                    f"{API_BASE_URL}/agentic-query",
                    json={
                        "question": user_query,
                        "enable_web_search": enable_web_search
                    },
                    timeout=120
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "Unable to generate answer.")
                    
                    # Add to history
                    st.session_state.chat_history.append({
                        "query": user_query,
                        "answer": answer,
                        "type": "agentic"
                    })
                    
                    # Display answer
                    st.markdown("### Deep Analysis Result")
                    st.markdown(f'<div class="report-container">{answer}</div>', unsafe_allow_html=True)
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

# Tab 2: Upload PDF
with tab2:
    st.subheader("Upload PDF Document")
    
    # 보안 정보 표시
    st.info("보안 모드: 업로드된 PDF는 로컬 Ollama 모델(qwen2.5-coder:3b)로만 처리됩니다. 외부 API로 전송되지 않습니다.")
    
    st.markdown("Upload financial reports, supply chain documents, or industry analysis PDFs")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload PDF documents to add to the knowledge base (로컬 처리)"
    )
    
    if uploaded_file is not None:
        st.info(f"File: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        
        # Storage option
        storage_mode = st.radio(
            "Storage Mode",
            ["Temporary (Session only)", "Permanent (Save to database)"],
            help="Temporary: Use for one-time analysis. Permanent: Save to database forever.",
            horizontal=True
        )
        
        permanent = storage_mode == "Permanent (Save to database)"
        
        if st.button("Process PDF (Local Only)", type="primary"):
            storage_label = "Permanent" if permanent else "Temporary"
            with st.spinner(f"Processing with local model ({storage_label})..."):
                try:
                    # Send PDF to backend
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'application/pdf')}
                    data_form = {'permanent': 'true' if permanent else 'false'}
                    response = requests.post(
                        f"{API_BASE_URL}/ingest_pdf",
                        files=files,
                        data=data_form,
                        timeout=300
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        storage_type = data.get('storage_type', 'unknown')
                        st.success(f"PDF processed successfully ({storage_type})")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("엔티티 추출", data.get('entities_extracted', 'N/A'))
                        with col2:
                            st.metric("관계 추출", data.get('relationships_extracted', 'N/A'))
                        with col3:
                            st.metric("민감 정보", data.get('sensitive_count', 'N/A'))
                        
                        st.info(data.get('message', 'Processing complete'))
                        
                        # 처리 세부사항 표시
                        if data.get('entities'):
                            with st.expander("추출된 엔티티 보기"):
                                st.json(data.get('entities', [])[:10])  # 처음 10개만 표시
                    else:
                        st.error(f"Error processing PDF: {response.status_code}")
                        try:
                            error_detail = response.json()
                            st.error(f"상세 오류: {error_detail.get('detail', 'Unknown error')}")
                        except:
                            st.error(f"응답 내용: {response.text[:500]}")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    import traceback
                    with st.expander("상세 오류 정보"):
                        st.code(traceback.format_exc())

# Tab 3: Database Upload
with tab3:
    st.subheader("데이터베이스 직접 업로드")
    st.markdown("CSV/JSON 파일을 Neo4j 그래프 데이터베이스에 직접 업로드합니다")
    
    # 보안 정보
    st.info("보안 모드: 업로드된 데이터는 로컬 Neo4j 데이터베이스에만 저장되며, 외부로 전송되지 않습니다.")
    
    # 업로드 타입 선택
    upload_type = st.radio(
        "업로드 데이터 타입",
        ["CSV (테이블 데이터)", "JSON (구조화된 데이터)"],
        horizontal=True
    )
    
    if "CSV" in upload_type:
        st.markdown("### CSV 파일 업로드")
        st.markdown("**예시 형식**: Company, Revenue, MarketCap, Country")
        
        csv_file = st.file_uploader(
            "CSV 파일 선택",
            type=['csv'],
            help="회사 정보, 재무 데이터 등을 포함한 CSV 파일"
        )
        
        if csv_file:
            st.info(f"File: {csv_file.name} ({csv_file.size / 1024:.1f} KB)")
            
            # CSV 미리보기
            import pandas as pd
            try:
                df = pd.read_csv(csv_file)
                st.markdown("#### 데이터 미리보기 (처음 5행)")
                st.dataframe(df.head(), use_container_width=True)
                
                # 컬럼 매핑 설정 (선택사항)
                st.markdown("#### 컬럼 매핑 설정 (선택사항)")
                
                # 기본값 자동 설정
                default_entity_col = df.columns[0]  # 첫 번째 컬럼을 기본 엔티티로
                default_property_cols = list(df.columns[1:])  # 나머지를 속성으로
                
                with st.expander("고급 설정 (기본값 사용 가능)", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        entity_col = st.selectbox("엔티티 이름 컬럼", df.columns, index=0, help="회사명, 인물명 등 (기본: 첫 번째 컬럼)")
                        entity_type = st.selectbox("엔티티 타입", ["Company", "Person", "Technology", "Country"], help="노드 타입")
                    
                    with col2:
                        property_cols = st.multiselect("속성 컬럼", df.columns, default=default_property_cols, help="Revenue, MarketCap 등 (기본: 나머지 모든 컬럼)")
                
                # 엔티티 컬럼이 선택되지 않았으면 기본값 사용
                if 'entity_col' not in locals():
                    entity_col = default_entity_col
                if 'property_cols' not in locals():
                    property_cols = default_property_cols
                if 'entity_type' not in locals():
                    entity_type = "Company"
                
                if st.button("CSV 데이터베이스에 업로드", type="primary"):
                    with st.spinner("로컬 데이터베이스에 업로드 중..."):
                        try:
                            # CSV를 JSON으로 변환하여 백엔드로 전송
                            # NaN 값을 None으로 변환 (JSON 호환)
                            df_clean = df.fillna('')  # NaN을 빈 문자열로 변환
                            csv_data = df_clean.to_dict(orient='records')
                            
                            response = requests.post(
                                f"{API_BASE_URL}/upload_csv",
                                json={
                                    "data": csv_data,
                                    "entity_column": entity_col,
                                    "entity_type": entity_type,
                                    "property_columns": property_cols
                                },
                                timeout=300
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                st.success(f"{result.get('nodes_created', 0)}개 노드 생성 완료!")
                                
                                col_m1, col_m2 = st.columns(2)
                                with col_m1:
                                    st.metric("생성된 노드", result.get('nodes_created', 0))
                                with col_m2:
                                    st.metric("생성된 관계", result.get('relationships_created', 0))
                            else:
                                st.error(f"업로드 실패: {response.status_code}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            except Exception as e:
                st.error(f"CSV 파일 읽기 오류: {str(e)}")
    
    else:  # JSON
        st.markdown("### JSON 파일 업로드")
        st.markdown("**예시 형식**: `{\"companies\": [{\"name\": \"Nvidia\", \"revenue\": 60.9}]}`")
        
        json_file = st.file_uploader(
            "JSON 파일 선택",
            type=['json'],
            help="구조화된 JSON 데이터"
        )
        
        if json_file:
            st.info(f"File: {json_file.name} ({json_file.size / 1024:.1f} KB)")
            
            try:
                import json
                json_data = json.load(json_file)
                
                # JSON 미리보기
                st.markdown("#### 데이터 미리보기")
                st.json(json_data)
                
                # JSON 스키마 설정
                st.markdown("#### 스키마 설정")
                
                root_key = st.text_input("루트 키", value="companies", help="데이터 배열의 키 (없으면 비워두기)")
                entity_key = st.text_input("엔티티 키", value="name", help="엔티티 이름을 나타내는 키")
                entity_type_json = st.selectbox("엔티티 타입", ["Company", "Person", "Technology", "Country"])
                
                if st.button("JSON 데이터베이스에 업로드", type="primary"):
                    with st.spinner("로컬 데이터베이스에 업로드 중..."):
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/upload_json",
                                json={
                                    "data": json_data,
                                    "root_key": root_key if root_key else None,
                                    "entity_key": entity_key,
                                    "entity_type": entity_type_json
                                },
                                timeout=300
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                st.success(f"{result.get('nodes_created', 0)}개 노드 생성 완료!")
                                
                                col_m1, col_m2 = st.columns(2)
                                with col_m1:
                                    st.metric("생성된 노드", result.get('nodes_created', 0))
                                with col_m2:
                                    st.metric("생성된 관계", result.get('relationships_created', 0))
                            else:
                                st.error(f"업로드 실패: {response.status_code}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            except Exception as e:
                st.error(f"JSON 파일 읽기 오류: {str(e)}")

# Tab 4: Graph Visualization
with tab4:
            try:
                # Query for database stats
                response = requests.get(f"{API_BASE_URL}/graph_stats", timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    stats = data.get('stats', {})
                    
                    # Display metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Companies", stats.get('node_count', 0))
                    with col2:
                        st.metric("Technologies", stats.get('technology_count', 0))
                    with col3:
                        st.metric("Risks", stats.get('risk_count', 0))
                    with col4:
                        st.metric("Relationships", stats.get('edge_count', 0))
                    
                    st.divider()
                    
                    # Show sample data
                    st.subheader("Sample Companies")
                    
                    # Query for companies
                    try:
                        from neo4j import GraphDatabase
                        NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
                        NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
                        NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
                        
                        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
                        
                        with driver.session() as session:
                            # Get companies
                            result = session.run("""
                                MATCH (c:Company)
                                RETURN c.name as name, c.ticker as ticker, c.role as role, c.criticality as criticality
                                ORDER BY c.criticality DESC
                                LIMIT 10
                            """)
                            
                            companies = result.data()
                            
                            if companies:
                                import pandas as pd
                                df = pd.DataFrame(companies)
                                st.dataframe(df, use_container_width=True)
                            else:
                                st.info("No companies found in database")
                            
                            # Get technologies
                            st.subheader("Technologies")
                            result = session.run("""
                                MATCH (t:Technology)
                                RETURN t.name as name, t.category as category, t.maturity as maturity
                                LIMIT 10
                            """)
                            
                            techs = result.data()
                            if techs:
                                df_tech = pd.DataFrame(techs)
                                st.dataframe(df_tech, use_container_width=True)
                            
                            # Get risks
                            st.subheader("Risk Factors")
                            result = session.run("""
                                MATCH (r:Risk)
                                RETURN r.name as name, r.impact_level as impact
                                LIMIT 10
                            """)
                            
                            risks = result.data()
                            if risks:
                                df_risk = pd.DataFrame(risks)
                                st.dataframe(df_risk, use_container_width=True)
                        
                        driver.close()
                        
                    except Exception as e:
                        st.error(f"Error querying database: {str(e)}")
                        st.info("Make sure Neo4j is running and credentials are correct")
                else:
                    st.error(f"Error: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Tab 4: Graph Visualization
with tab4:
    st.subheader("Knowledge Graph Visualization")
    st.markdown("Interactive visualization of the supply chain network")
    
    # Base data loader
    reset_db = st.checkbox("Reset database before loading", value=True)
    if st.button("Load Base Data from /data/baseline", type="secondary"):
        with st.spinner("Loading base data..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/load_base_data",
                    data={
                        "resetDb": "true" if reset_db else "false"
                    },
                    timeout=600
                )
                if response.status_code == 200:
                    st.success("Base data loaded successfully")
                else:
                    st.error(f"Error: {response.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Visualization options
    col1, col2 = st.columns(2)
    with col1:
        max_nodes = st.slider("Max Nodes", 10, 100, 30)
    with col2:
        layout = st.selectbox("Layout", ["Force-directed", "Hierarchical", "Circular"])

    include_temp = st.checkbox("Include Temporary Overlay", value=True)
    
    if st.button("Generate Graph Visualization", type="primary"):
        with st.spinner("Generating graph visualization..."):
            try:
                # Direct Neo4j query for visualization
                NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
                NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
                NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
                
                from neo4j import GraphDatabase
                import json
                
                driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
                
                with driver.session() as session:
                    # Get nodes and relationships
                    query = """
                    MATCH (n)
                    WHERE ($include_temp = true OR n.temporary IS NULL OR n.temporary = false)
                    WITH n LIMIT $max_nodes
                    OPTIONAL MATCH (n)-[r]->(m)
                    WHERE ($include_temp = true OR m.temporary IS NULL OR m.temporary = false)
                    RETURN n, r, m
                    """
                    
                    result = session.run(query, max_nodes=max_nodes, include_temp=include_temp)
                    
                    nodes = {}
                    edges = []
                    
                    for record in result:
                        # Process source node
                        if record['n']:
                            node = record['n']
                            node_id = id(node)
                            if node_id not in nodes:
                                labels = list(node.labels)
                                is_temp = node.get('temporary', False)
                                group_name = "Temporary" if is_temp else (labels[0] if labels else 'Unknown')
                                nodes[node_id] = {
                                    'id': node_id,
                                    'label': node.get('name', str(node_id)),
                                    'group': group_name,
                                    'title': f"{group_name}: {node.get('name', 'N/A')}"
                                }
                        
                        # Process target node and relationship
                        if record['m'] and record['r']:
                            target = record['m']
                            target_id = id(target)
                            
                            if target_id not in nodes:
                                labels = list(target.labels)
                                is_temp = target.get('temporary', False)
                                group_name = "Temporary" if is_temp else (labels[0] if labels else 'Unknown')
                                nodes[target_id] = {
                                    'id': target_id,
                                    'label': target.get('name', str(target_id)),
                                    'group': group_name,
                                    'title': f"{group_name}: {target.get('name', 'N/A')}"
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
    Tech-Analyst GraphRAG v2.0 | Powered by GPT-4o-mini & Perplexity
</div>
""", unsafe_allow_html=True)
