"""
Multi-Hop Reasoning UI for Streamlit
"""

import streamlit as st
import asyncio
import json
from typing import Dict, Any
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from engine.reasoner import MultiHopReasoner
from engine.integrator import DataIntegrator


def render_reasoning_path_graph(paths: list):
    """
    Render reasoning paths as interactive graph
    Uses simple HTML/CSS visualization
    """
    
    if not paths:
        st.warning("추론 경로를 찾을 수 없습니다.")
        return
    
    st.markdown("### 📊 추론 경로 그래프")
    
    for i, path in enumerate(paths[:3], 1):  # Show top 3 paths
        nodes = path.get('nodes', [])
        rels = path.get('relationships', [])
        hops = path.get('hops', 0)
        
        if not nodes:
            continue
        
        st.markdown(f"#### Path {i} ({hops} hops)")
        
        # Create path visualization
        path_html = '<div style="display: flex; align-items: center; overflow-x: auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin: 10px 0;">'
        
        for j, node in enumerate(nodes):
            node_name = node.get('name', 'Unknown')
            node_type = node.get('type', 'Unknown')
            
            # Node box
            path_html += f'''
            <div style="
                background: white;
                border: 3px solid #4CAF50;
                border-radius: 10px;
                padding: 15px 20px;
                margin: 0 10px;
                min-width: 150px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                <div style="font-weight: bold; color: #2196F3; font-size: 16px;">{node_name}</div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">{node_type}</div>
            </div>
            '''
            
            # Arrow with relationship
            if j < len(nodes) - 1:
                rel_type = rels[j] if j < len(rels) else 'RELATED'
                path_html += f'''
                <div style="
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    margin: 0 5px;
                ">
                    <div style="color: white; font-size: 12px; font-weight: bold; margin-bottom: 5px;">{rel_type}</div>
                    <div style="color: white; font-size: 24px;">→</div>
                </div>
                '''
        
        path_html += '</div>'
        st.markdown(path_html, unsafe_allow_html=True)
        
        # Show node details in expander
        with st.expander(f"🔍 Path {i} 상세 정보"):
            for j, node in enumerate(nodes):
                st.markdown(f"**{j+1}. {node.get('name')} ({node.get('type')})**")
                props = node.get('properties', {})
                if props:
                    st.json(props)
                
                if j < len(rels):
                    st.markdown(f"   ↓ `{rels[j]}`")


async def run_reasoning_interface():
    """Main reasoning interface"""
    
    st.title("🧠 Multi-Hop Reasoning Engine")
    st.markdown("---")
    
    # Sidebar: Data Integration
    with st.sidebar:
        st.header("📥 Data Integration")
        
        # File upload for CSV/JSON
        uploaded_csv = st.file_uploader("Upload CSV (Financial Data)", type=['csv'])
        uploaded_json = st.file_uploader("Upload JSON (Indicators)", type=['json'])
        
        if st.button("🔗 Integrate Data"):
            if uploaded_csv or uploaded_json:
                with st.spinner("데이터 통합 중..."):
                    integrator = DataIntegrator()
                    
                    try:
                        if uploaded_csv:
                            # Save temp file
                            csv_path = f"/tmp/{uploaded_csv.name}"
                            with open(csv_path, 'wb') as f:
                                f.write(uploaded_csv.read())
                            
                            # Default mapping
                            integrator.ingest_csv(
                                csv_path,
                                mapping={
                                    'Company': 'entity_name',
                                    'Revenue': 'property',
                                    'MarketCap': 'property'
                                }
                            )
                        
                        if uploaded_json:
                            json_path = f"/tmp/{uploaded_json.name}"
                            with open(json_path, 'wb') as f:
                                f.write(uploaded_json.read())
                            
                            # Default schema
                            integrator.ingest_json(
                                json_path,
                                schema={
                                    'root': None,
                                    'entity_key': 'name',
                                    'entity_type': 'Company'
                                }
                            )
                        
                        stats = integrator.get_stats()
                        st.success(f"✅ 통합 완료: {stats}")
                        integrator.close()
                        
                    except Exception as e:
                        st.error(f"❌ Integration failed: {e}")
            else:
                st.warning("파일을 업로드해주세요.")
        
        st.markdown("---")
        st.markdown("### ⚙️ Reasoning Settings")
        max_hops = st.slider("Maximum Hops", 1, 4, 3)
    
    # Main interface
    st.markdown("### 💬 Ask a Question")
    
    question = st.text_input(
        "질문을 입력하세요:",
        placeholder="예: How does Taiwan tension affect Nvidia?",
        key="reasoning_question"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        analyze_btn = st.button("🚀 Analyze", use_container_width=True)
    
    if analyze_btn and question:
        with st.spinner("🔍 Multi-hop reasoning in progress..."):
            try:
                reasoner = MultiHopReasoner()
                result = await reasoner.reason(question, max_hops=max_hops)
                reasoner.close()
                
                # Store in session state
                st.session_state['reasoning_result'] = result
                
            except Exception as e:
                st.error(f"❌ Reasoning failed: {e}")
                return
    
    # Display results
    if 'reasoning_result' in st.session_state:
        result = st.session_state['reasoning_result']
        
        # Inference
        st.markdown("---")
        st.markdown("## 💡 Logical Inference")
        
        confidence = result.get('confidence', 0.0)
        confidence_color = "green" if confidence > 0.7 else "orange" if confidence > 0.4 else "red"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            margin: 20px 0;
        ">
            <h3 style="margin-top: 0;">🎯 결론</h3>
            <p style="font-size: 18px; line-height: 1.6;">{result['inference']}</p>
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.3);">
                <strong>Confidence:</strong> 
                <span style="color: {confidence_color}; font-size: 24px; font-weight: bold;">
                    {confidence:.1%}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Reasoning steps
        if result.get('reasoning_steps'):
            st.markdown("### 🔗 Reasoning Chain")
            for i, step in enumerate(result['reasoning_steps'], 1):
                st.markdown(f"{i}. {step}")
        
        # Visualize paths
        if result.get('reasoning_paths'):
            st.markdown("---")
            render_reasoning_path_graph(result['reasoning_paths'])
        
        # Raw data
        with st.expander("📋 Raw Data (JSON)"):
            st.json(result)


def main():
    """Entry point"""
    st.set_page_config(
        page_title="Multi-Hop Reasoning",
        page_icon="🧠",
        layout="wide"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Run async interface
    asyncio.run(run_reasoning_interface())


if __name__ == "__main__":
    main()
