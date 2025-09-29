# data_loader.py  
# Unified data loading utilities for ICE system
# Provides functions to load data from both Python modules and Excel files
# Supports flexible data source switching for development and production scenarios

import pandas as pd
import os
from typing import List, Dict, Any, Optional
from sample_data import PORTFOLIO_ROWS, WATCHLIST_ROWS, TICKER_BUNDLE, EDGE_RECORDS

# Excel file path constants
EXCEL_FILE_PATH = 'data/investment_data.xlsx'

def load_from_excel(file_path: str = EXCEL_FILE_PATH) -> Optional[Dict[str, Any]]:
    """
    Load all data from consolidated Excel file.
    
    Args:
        file_path: Path to Excel file (default: data/investment_data.xlsx)
        
    Returns:
        Dictionary with all loaded data, or None if file not found
    """
    if not os.path.exists(file_path):
        print(f"⚠️ Excel file not found: {file_path}")
        return None
    
    try:
        # Load all sheets
        portfolio_df = pd.read_excel(file_path, sheet_name='Portfolio')
        watchlist_df = pd.read_excel(file_path, sheet_name='Watchlist') 
        ticker_df = pd.read_excel(file_path, sheet_name='Ticker_Info')
        edges_df = pd.read_excel(file_path, sheet_name='Graph_Edges')
        
        # Convert DataFrames back to original format
        portfolio_rows = portfolio_df.to_dict('records')
        watchlist_rows = watchlist_df.to_dict('records')
        
        # Reconstruct ticker bundle format
        ticker_bundle = {}
        for _, row in ticker_df.iterrows():
            ticker_bundle[row['Ticker']] = {
                'meta': {'name': row['Name'], 'sector': row['Sector']},
                'priority': row['Priority'],
                'confidence': row['Confidence'],
                'tldr': row['TL;DR']
            }
        
        # Convert edges DataFrame to tuple format
        edge_records = []
        for _, row in edges_df.iterrows():
            edge_records.append((
                row['Source'], row['Target'], row['Edge_Type'],
                row['Confidence'], row['Days_Ago'], row['Is_Contrarian']
            ))
        
        return {
            'portfolio_rows': portfolio_rows,
            'watchlist_rows': watchlist_rows, 
            'ticker_bundle': ticker_bundle,
            'edge_records': edge_records
        }
        
    except Exception as e:
        print(f"❌ Error loading Excel file: {e}")
        return None

def load_from_python() -> Dict[str, Any]:
    """
    Load data from Python sample_data module.
    
    Returns:
        Dictionary with all sample data
    """
    return {
        'portfolio_rows': PORTFOLIO_ROWS,
        'watchlist_rows': WATCHLIST_ROWS,
        'ticker_bundle': TICKER_BUNDLE,
        'edge_records': EDGE_RECORDS
    }

def load_data(source: str = 'auto') -> Dict[str, Any]:
    """
    Load data from specified source with smart fallback.
    
    Args:
        source: 'excel', 'python', or 'auto' (default)
        
    Returns:
        Dictionary with loaded data
    """
    if source == 'excel':
        data = load_from_excel()
        if data is None:
            print("⚠️ Excel loading failed, falling back to Python data")
            return load_from_python()
        return data
    
    elif source == 'python':
        return load_from_python()
    
    else:  # auto mode
        # Try Excel first, fallback to Python
        data = load_from_excel()
        if data is not None:
            print("✅ Data loaded from Excel file")
            return data
        else:
            print("✅ Data loaded from Python module (Excel fallback)")
            return load_from_python()

def get_portfolio_data(source: str = 'auto') -> List[Dict[str, Any]]:
    """Get portfolio data only"""
    data = load_data(source)
    return data['portfolio_rows']

def get_watchlist_data(source: str = 'auto') -> List[Dict[str, Any]]:
    """Get watchlist data only"""
    data = load_data(source)
    return data['watchlist_rows']

def get_ticker_bundle(source: str = 'auto') -> Dict[str, Any]:
    """Get ticker bundle data only"""
    data = load_data(source)
    return data['ticker_bundle']

def get_edge_records(source: str = 'auto') -> List[tuple]:
    """Get graph edge records only"""
    data = load_data(source)
    return data['edge_records']

if __name__ == "__main__":
    # Test data loading
    print("🧪 Testing data loading...")
    
    # Test auto mode
    data = load_data('auto')
    print(f"📊 Auto mode - Portfolio: {len(data['portfolio_rows'])}, Watchlist: {len(data['watchlist_rows'])}")
    
    # Test individual functions
    portfolio = get_portfolio_data()
    watchlist = get_watchlist_data()
    print(f"📋 Individual functions - Portfolio: {len(portfolio)}, Watchlist: {len(watchlist)}")
    
    print("✅ Data loader test completed")