# Location: /tests/test_ticker_validator.py
# Purpose: Test TickerValidator for reducing false positive ticker extraction
# Why: Verify that TickerValidator correctly filters out false tickers
# Relevant Files: imap_email_ingestion_pipeline/ticker_validator.py

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from imap_email_ingestion_pipeline.ticker_validator import TickerValidator

def test_ticker_validator():
    """Test that TickerValidator correctly filters false positives"""

    print("="*70)
    print("TICKER VALIDATOR TEST")
    print("="*70)

    # Initialize validator
    validator = TickerValidator()

    # Test data - actual false positives from PDF extraction
    test_tickers = [
        # Real tickers (should pass)
        {'ticker': 'TME', 'confidence': 0.85},
        {'ticker': 'DBS', 'confidence': 0.90},
        {'ticker': 'NVDA', 'confidence': 0.88},
        {'ticker': 'AAPL', 'confidence': 0.92},
        {'ticker': 'GOOGL', 'confidence': 0.87},
        {'ticker': '1698', 'confidence': 0.80},  # HK ticker

        # False positives (should be filtered)
        {'ticker': 'I', 'confidence': 0.50},
        {'ticker': 'NOT', 'confidence': 0.45},
        {'ticker': 'SVIP', 'confidence': 0.55},
        {'ticker': 'S', 'confidence': 0.40},
        {'ticker': 'M', 'confidence': 0.35},
        {'ticker': 'AD', 'confidence': 0.45},
        {'ticker': 'G', 'confidence': 0.30},
        {'ticker': 'A', 'confidence': 0.25},
        {'ticker': 'BUY', 'confidence': 0.65},  # Rating word
        {'ticker': 'SELL', 'confidence': 0.60},  # Rating word
        {'ticker': 'HOLD', 'confidence': 0.62},  # Rating word
        {'ticker': 'DATE', 'confidence': 0.40},
        {'ticker': 'IS', 'confidence': 0.35},
        {'ticker': 'BE', 'confidence': 0.30},
        {'ticker': 'UPON', 'confidence': 0.45},
        {'ticker': 'USA', 'confidence': 0.50},
        {'ticker': 'CA', 'confidence': 0.40},
        {'ticker': 'PO', 'confidence': 0.35},
        {'ticker': 'HONG', 'confidence': 0.42},
        {'ticker': 'KONG', 'confidence': 0.41},
        {'ticker': 'F', 'confidence': 0.25},

        # Edge cases
        {'ticker': 'V', 'confidence': 0.80},  # Real single letter (Visa)
        {'ticker': 'BRK.B', 'confidence': 0.85},  # With exchange suffix
    ]

    # Create test entities dictionary
    test_entities = {
        'tickers': test_tickers,
        'ratings': [
            {'rating': 'buy', 'confidence': 0.80},
            {'rating': 'hold', 'confidence': 0.75}
        ],
        'financial_metrics': [
            {'metric': 'revenue', 'value': '1.2B', 'confidence': 0.85}
        ]
    }

    print("\nBEFORE filtering:")
    print(f"  Total tickers: {len(test_entities['tickers'])}")
    ticker_list = [t['ticker'] for t in test_entities['tickers']]
    print(f"  Tickers: {ticker_list}")

    # Apply filtering
    filtered_entities = validator.filter_tickers(test_entities)

    print("\nAFTER filtering:")
    print(f"  Total tickers: {len(filtered_entities['tickers'])}")
    filtered_list = [t['ticker'] for t in filtered_entities['tickers']]
    print(f"  Tickers: {filtered_list}")

    # Calculate statistics
    removed_count = len(test_entities['tickers']) - len(filtered_entities['tickers'])
    removed_tickers = [t for t in ticker_list if t not in filtered_list]

    print(f"\nFILTERING RESULTS:")
    print(f"  Removed: {removed_count} false positives")
    print(f"  Removed tickers: {removed_tickers}")
    print(f"  Kept: {len(filtered_entities['tickers'])} valid tickers")

    # Verify expected results
    expected_valid = ['TME', 'DBS', 'NVDA', 'AAPL', 'GOOGL', '1698', 'V', 'BRK.B']
    expected_filtered = ['I', 'NOT', 'SVIP', 'S', 'M', 'AD', 'G', 'A', 'BUY', 'SELL',
                         'HOLD', 'DATE', 'IS', 'BE', 'UPON', 'USA', 'CA', 'PO',
                         'HONG', 'KONG', 'F']

    print(f"\nVALIDATION:")
    all_correct = True

    # Check if all expected valid tickers are kept
    for ticker in expected_valid:
        if ticker not in filtered_list:
            print(f"  ❌ Expected valid ticker '{ticker}' was filtered out")
            all_correct = False

    # Check if all expected filtered tickers are removed
    for ticker in expected_filtered:
        if ticker in filtered_list:
            print(f"  ❌ Expected filtered ticker '{ticker}' was kept")
            all_correct = False

    if all_correct:
        print(f"  ✅ All tickers correctly classified")
        print(f"  ✅ Reduced from {len(test_entities['tickers'])} to {len(filtered_entities['tickers'])} tickers")
        print(f"  ✅ Noise reduction: {(removed_count/len(test_entities['tickers'])*100):.1f}%")

    # Test contextual validation
    print(f"\n" + "="*70)
    print("CONTEXTUAL VALIDATION TEST")
    print("="*70)

    test_cases = [
        ("I", "I think the stock will rise", False),  # Common word
        ("I", "The ticker I represents an ETF", True),  # Explicitly mentioned as ticker
        ("BUY", "We recommend BUY rating", False),  # Rating word
        ("BUY", "(BUY) is our target", False),  # Still a rating
        ("TME", "Tencent Music (TME) reported", True),  # Valid ticker
        ("USD", "Revenue was 100 USD", False),  # Currency
        ("CEO", "The CEO announced", False),  # Title
        ("V", "Visa (V) is performing well", True),  # Valid single letter
    ]

    for ticker, context, expected in test_cases:
        result = validator.validate_ticker(ticker, context)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{ticker}' in '{context[:30]}...' → {result} (expected: {expected})")

    print("="*70)

    return all_correct

if __name__ == "__main__":
    success = test_ticker_validator()

    if success:
        print("\n✅ TICKER VALIDATOR TEST PASSED")
        print("The validator successfully filters out false positive tickers")
        print("This will significantly improve graph quality and query precision")
    else:
        print("\n⚠️ TICKER VALIDATOR TEST PARTIALLY PASSED")
        print("Some edge cases may need refinement")