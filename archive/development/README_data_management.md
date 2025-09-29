# ICE Data Management Documentation

## Overview
The ICE system now uses a unified data management approach with smart Excel/Python fallback loading.

## Files Structure

### Data Files
- **`data/investment_data.xlsx`** - Single consolidated Excel file with 4 sheets:
  - `Portfolio` - Current portfolio holdings (5 positions)
  - `Watchlist` - Securities being monitored (4 items)  
  - `Ticker_Info` - Detailed ticker metadata (1 ticker: NVDA)
  - `Graph_Edges` - Knowledge graph relationships (10 edges)

### Code Files
- **`sample_data.py`** - Core Python data definitions (always available)
- **`data_loader.py`** - Smart data loading with Excel/Python fallback
- **`create_excel_data.py`** - Utility to generate Excel file from Python data

## Usage Patterns

### Loading Data in Code

#### Option 1: Smart Auto-Loading (Recommended)
```python
from data_loader import load_data

# Automatically tries Excel first, falls back to Python
data = load_data('auto')  
portfolio = data['portfolio_rows']
watchlist = data['watchlist_rows']
```

#### Option 2: Specific Source
```python
from data_loader import get_portfolio_data, get_watchlist_data

# Load from specific source
portfolio = get_portfolio_data('excel')  # or 'python' or 'auto'
watchlist = get_watchlist_data('auto')
```

#### Option 3: Direct Python Import (Legacy)
```python
from sample_data import PORTFOLIO_ROWS, WATCHLIST_ROWS
```

### Regenerating Excel File
```bash
python create_excel_data.py
```

## Migration Changes

### Before (Multiple Files)
- `data/dummy_portfolio_holdings.xlsx` ❌ Removed
- `data/dummy_watchlist.xlsx` ❌ Removed  
- `data/dummy_investment_data.xlsx` ❌ Removed

### After (Single File)
- `data/investment_data.xlsx` ✅ Single consolidated file

### Code Updates
- **ice_development.ipynb**: Updated to use smart data loader
- **sample_data.py**: Added Excel file reference in header
- **New data_loader.py**: Provides unified loading interface

## Benefits

1. **Single Source of Truth**: One Excel file eliminates confusion
2. **Smart Fallback**: Code works with or without Excel file
3. **Flexible Loading**: Choose data source based on needs
4. **Easy Maintenance**: Simple regeneration of Excel from Python
5. **Development Friendly**: Fallback ensures code always runs

## File Locations
```
data/
└── investment_data.xlsx          # Single consolidated data file

# Python modules  
├── sample_data.py               # Core data definitions
├── data_loader.py               # Smart loading utilities
└── create_excel_data.py         # Excel generation utility
```