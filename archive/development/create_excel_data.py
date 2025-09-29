# create_excel_data.py
# Extract dummy portfolio holdings from sample_data.py and save to Excel files in data folder
# Provides clean separation between code and data, enabling easier data management

import pandas as pd
from sample_data import PORTFOLIO_ROWS, WATCHLIST_ROWS, TICKER_BUNDLE, EDGE_RECORDS
import os

def create_excel_files():
    """Create single consolidated Excel file with all investment data"""
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Create consolidated Excel file with multiple sheets
    combined_file = 'data/investment_data.xlsx'
    
    # Convert data to DataFrames
    portfolio_df = pd.DataFrame(PORTFOLIO_ROWS)
    watchlist_df = pd.DataFrame(WATCHLIST_ROWS)
    
    with pd.ExcelWriter(combined_file, engine='openpyxl') as writer:
        # Portfolio sheet
        portfolio_df.to_excel(writer, sheet_name='Portfolio', index=False)
        
        # Watchlist sheet
        watchlist_df.to_excel(writer, sheet_name='Watchlist', index=False)
        
        # Ticker bundle data as flattened sheet
        ticker_data = []
        for ticker, data in TICKER_BUNDLE.items():
            row = {
                'Ticker': ticker,
                'Name': data['meta']['name'],
                'Sector': data['meta']['sector'],
                'Priority': data['priority'],
                'Confidence': data['confidence'],
                'TL;DR': data['tldr']
            }
            ticker_data.append(row)
        
        ticker_df = pd.DataFrame(ticker_data)
        ticker_df.to_excel(writer, sheet_name='Ticker_Info', index=False)
        
        # Graph edges sheet
        edge_df = pd.DataFrame(EDGE_RECORDS, columns=[
            'Source', 'Target', 'Edge_Type', 'Confidence', 'Days_Ago', 'Is_Contrarian'
        ])
        edge_df.to_excel(writer, sheet_name='Graph_Edges', index=False)
    
    print(f"✅ Created {combined_file} with all investment data (4 sheets)")
    
    # Print summary
    print(f"\n📊 Data Summary:")
    print(f"- Portfolio positions: {len(portfolio_df)}")
    print(f"- Watchlist items: {len(watchlist_df)}")
    print(f"- Ticker bundles: {len(TICKER_BUNDLE)}")
    print(f"- Graph edges: {len(EDGE_RECORDS)}")
    
    return {
        'combined_file': combined_file
    }

if __name__ == "__main__":
    files_created = create_excel_files()
    print(f"\n🎯 File created in data/ folder:")
    print(f"  - {files_created['combined_file']}")