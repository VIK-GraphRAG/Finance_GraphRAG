#!/usr/bin/env python3
"""
Streamlit UI 수정 스크립트
- PDF 업로드 성공 시 metrics 제거
- Visualization 탭에서 Companies, Technologies metrics 제거하고 Risk Factors만 남김
"""

with open('src/streamlit_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Tab 2 (Upload PDF) - metrics 제거
content = content.replace(
    """                    if response.status_code == 200:
                        data = response.json()
                        st.success("PDF processed successfully")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Entities", data.get('entities_extracted', 'N/A'))
                        with col2:
                            st.metric("Relationships", data.get('relationships_extracted', 'N/A'))
                        with col3:
                            st.metric("Sensitive", data.get('sensitive_count', 'N/A'))
                        
                        # 처리 세부사항 표시
                        if data.get('entities'):
                            with st.expander("View extracted entities"):
                                st.json(data.get('entities', [])[:10])""",
    """                    if response.status_code == 200:
                        st.success("PDF가 성공적으로 처리되었습니다.")"""
)

# 2. Tab 3 (Database Upload) - metrics 제거
content = content.replace(
    """                    if response.status_code == 200:
                        result = response.json()
                        st.success("PDF merged successfully")
                        col_p1, col_p2, col_p3 = st.columns(3)
                        with col_p1:
                            st.metric("Entities", result.get("entities_extracted", 0))
                        with col_p2:
                            st.metric("Relationships", result.get("relationships_extracted", 0))
                        with col_p3:
                            st.metric("Text Length", result.get("text_length", 0))""",
    """                    if response.status_code == 200:
                        result = response.json()
                        st.success("PDF가 성공적으로 업로드되어 Neo4j 데이터베이스에 저장되었습니다.")"""
)

# 3. Tab 4 (Visualization) - Companies/Technologies 메트릭 제거, Risk Factors만 유지
old_viz = """# Tab 4: Graph Visualization (moved from old tab 4)
with tab4:
            try:
                # Query for database stats
                response = requests.get(f"{API_BASE_URL}/graph_stats", timeout=10)
                
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

                        if not NEO4J_PASSWORD:
                            st.error("Neo4j password not set in .env")
                            droneLogError("Neo4j password missing for visualization (sample data)")
                        else:
                            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

                            with driver.session() as session:
                                # Get companies
                                result = session.run(\"\"\"
                                    MATCH (c:Company)
                                    RETURN c.name as name, c.ticker as ticker, c.role as role, c.criticality as criticality
                                    ORDER BY c.criticality DESC
                                    LIMIT 10
                                \"\"\")
                                
                                companies = result.data()
                                
                                if companies:
                                    import pandas as pd
                                    df = pd.DataFrame(companies)
                                    st.dataframe(df, use_container_width=True)
                                else:
                                    st.info("No companies found in database")
                                
                                # Get technologies
                                st.subheader("Technologies")
                                result = session.run(\"\"\"
                                    MATCH (t:Technology)
                                    RETURN t.name as name, t.category as category, t.maturity as maturity
                                    LIMIT 10
                                \"\"\")
                                
                                techs = result.data()
                                if techs:
                                    df_tech = pd.DataFrame(techs)
                                    st.dataframe(df_tech, use_container_width=True)
                                
                                # Get risks
                                st.subheader("Risk Factors")
                                result = session.run(\"\"\"
                                    MATCH (r:Risk)
                                    RETURN r.name as name, r.impact_level as impact
                                    LIMIT 10
                                \"\"\")
                                
                                risks = result.data()
                                if risks:
                                    df_risk = pd.DataFrame(risks)
                                    st.dataframe(df_risk, use_container_width=True)
                        
                            driver.close()

                    except Exception as e:
                        droneLogError("Neo4j query failed in visualization (sample data)", e)
                        st.error(f"Error querying database: {str(e)}")
                        st.info("Make sure Neo4j is running and credentials are correct")
                else:
                    st.error(f"Error: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")"""

new_viz = """# Tab 4: Graph Visualization
with tab4:
    try:
        from neo4j import GraphDatabase
        NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
        NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

        if not NEO4J_PASSWORD:
            st.error("Neo4j password not set in .env")
        else:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

            with driver.session() as session:
                # Risk Factors만 표시
                st.subheader("⚠️ Risk Factors")
                result = session.run(\"\"\"
                    MATCH (r:Risk)
                    RETURN r.name as name, r.impact_level as impact, r.description as description
                    ORDER BY r.impact_level DESC
                    LIMIT 20
                \"\"\")
                
                risks = result.data()
                if risks:
                    import pandas as pd
                    df_risk = pd.DataFrame(risks)
                    st.dataframe(df_risk, use_container_width=True)
                else:
                    st.info("데이터베이스에 Risk Factor가 없습니다. PDF를 업로드하거나 데이터를 시딩하세요.")
        
            driver.close()

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("Neo4j가 실행 중인지 확인하세요.")"""

content = content.replace(old_viz, new_viz)

# 파일 저장
with open('src/streamlit_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Streamlit UI 수정 완료!")
print("   - PDF 업로드 성공 시 metrics 제거")
print("   - Visualization 탭에서 Risk Factors만 표시")
