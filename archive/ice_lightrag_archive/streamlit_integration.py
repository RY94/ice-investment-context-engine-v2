# lightrag/streamlit_integration.py
"""
Simple Streamlit integration for ICE LightRAG
Minimal UI components for document upload and querying
"""

import streamlit as st
from ice_rag import SimpleICERAG


def render_rag_interface():
    """Render the LightRAG interface in Streamlit"""
    
    # Initialize RAG system
    if 'ice_rag' not in st.session_state:
        st.session_state.ice_rag = SimpleICERAG()
    
    rag = st.session_state.ice_rag
    
    # Check if system is ready
    if not rag.is_ready():
        st.error("🚫 LightRAG not available. Please check installation and API key.")
        st.info("Set OPENAI_API_KEY environment variable and run: pip install lightrag")
        return
    
    st.success("✅ LightRAG ready for financial analysis")
    
    # Query interface
    st.subheader("🤖 Ask About Investments")
    
    query = st.text_input(
        "Your question:",
        placeholder="e.g., What are the risks for NVIDIA?"
    )
    
    if st.button("🔍 Analyze") and query:
        with st.spinner("Analyzing..."):
            result = rag.query(query)
            
        if result["status"] == "success":
            st.write("**Answer:**")
            st.write(result["result"])
        else:
            st.error(f"Error: {result['message']}")
    
    # Add document count info
    with st.expander("📊 Knowledge Base Status", expanded=False):
        try:
            import json
            from pathlib import Path
            docs_file = Path("lightrag/storage/kv_store_full_docs.json")
            if docs_file.exists():
                with open(docs_file, 'r') as f:
                    docs = json.load(f)
                st.info(f"📚 Total documents in knowledge base: {len(docs)}")
                for i, (doc_id, doc_data) in enumerate(docs.items(), 1):
                    content = doc_data.get('content', '')[:150]
                    st.text(f"{i}. {content}...")
            else:
                st.warning("No documents found in knowledge base")
        except Exception as e:
            st.error(f"Error reading knowledge base: {e}")
    
    # Document upload
    st.subheader("📄 Add Financial Document")
    
    # Text input option
    doc_text = st.text_area(
        "Paste document text:",
        placeholder="Paste SEC filing, earnings report, or financial news here..."
    )
    
    doc_type = st.selectbox(
        "Document type:",
        ["SEC Filing", "Earnings Report", "Financial News", "Analysis Report"]
    )
    
    if st.button("📤 Add Document") and doc_text:
        with st.spinner("Processing document..."):
            result = rag.add_document(doc_text, doc_type.lower().replace(" ", "_"))
            
        if result["status"] == "success":
            st.success("✅ Document added to knowledge base!")
        else:
            st.error(f"Error: {result['message']}")


def render_simple_demo():
    """Render a simple demo with sample data"""
    st.subheader("📋 Quick Demo")
    
    sample_doc = """
    NVIDIA Corporation reported Q3 2024 revenue of $18.1 billion, up 206% year-over-year.
    Data center revenue reached $14.5 billion, driven by strong AI chip demand.
    Key risks include dependency on TSMC manufacturing and China export restrictions.
    Gaming revenue was $2.9 billion, down from previous quarters due to market conditions.
    """
    
    if st.button("🎯 Load Sample Financial Data"):
        if 'ice_rag' in st.session_state:
            rag = st.session_state.ice_rag
            if rag.is_ready():
                result = rag.add_document(sample_doc, "earnings_report")
                if result["status"] == "success":
                    st.success("✅ Sample data loaded! Try asking questions about NVIDIA.")
                else:
                    st.error(f"Error loading sample: {result['message']}")
            else:
                st.error("LightRAG not ready")
        else:
            st.error("Please initialize RAG system first")
