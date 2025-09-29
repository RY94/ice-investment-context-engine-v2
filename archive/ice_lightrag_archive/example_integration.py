# lightrag/example_integration.py
"""
Example showing how to integrate LightRAG with existing ICE UI
Minimal addition to your ice_ui_v17.py
"""

import streamlit as st
from streamlit_integration import render_rag_interface

# Your existing imports and data would go here
# from ice_ui_v17 import your_existing_functions

def enhanced_ice_ui():
    """
    Example of how to add LightRAG to your existing ICE UI
    This shows the minimal changes needed to ice_ui_v17.py
    """
    
    st.set_page_config(
        page_title="ICE - Investment Context Engine", 
        page_icon="🧊",
        layout="wide"
    )
    
    st.title("🧊 ICE - Investment Context Engine")
    st.subheader("Graph-Based RAG for Financial Analysis")
    
    # Create tabs for different features
    tab1, tab2, tab3 = st.tabs(["🤖 AI Analysis", "🕸️ Graph View", "📊 Portfolio"])
    
    with tab1:
        # This is the only new addition - the LightRAG interface
        render_rag_interface()
    
    with tab2:
        # Your existing graph visualization code would go here
        st.info("Your existing NetworkX/Pyvis graph visualization from ice_ui_v17.py")
        # render_investment_graph()  # Your existing function
    
    with tab3:
        # Your existing portfolio/ticker analysis would go here  
        st.info("Your existing ticker analysis and portfolio tracking")
        # render_ticker_analysis()  # Your existing function


def minimal_addition_example():
    """
    Even simpler - just add LightRAG as an expander to existing UI
    """
    
    # Your existing ice_ui_v17.py code here...
    
    # Add this single block anywhere in your existing app:
    with st.expander("🤖 AI Financial Analysis", expanded=False):
        render_rag_interface()
    
    # Rest of your existing code continues...


if __name__ == "__main__":
    enhanced_ice_ui()
