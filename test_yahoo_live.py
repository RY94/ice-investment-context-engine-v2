#!/usr/bin/env python3
"""Test Yahoo Finance historical data with real API call"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "updated_architectures" / "implementation"))

from updated_architectures.implementation.data_ingestion import DataIngester
from updated_architectures.implementation.config import ICEConfig

# Set up config with 7-day lookback for testing
config = ICEConfig()
config.financial_lookback_days = 7  # Small lookback for quick test

# Create ingester
print(f"Creating DataIngester with {config.financial_lookback_days}-day lookback...")
ingester = DataIngester(config=config)

# Fetch real Yahoo data for AAPL
print(f"Fetching Yahoo Finance data for AAPL...")
documents = ingester._fetch_yahoo_market_data('AAPL')

# Analyze results
print(f"\nResults:")
print(f"Total documents: {len(documents)}")

# Count different document types
summary_docs = [d for d in documents if '-Day Price Summary' in d]
daily_docs = [d for d in documents if 'Historical Market Data' in d]
other_docs = [d for d in documents if 'Historical Market Data' not in d and '-Day Price Summary' not in d]

print(f"  Summary documents: {len(summary_docs)}")
print(f"  Daily historical documents: {len(daily_docs)}")
print(f"  Other category documents: {len(other_docs)}")

# Check event_date tagging
if daily_docs:
    print(f"\nChecking EVENT_DATE tags in daily documents:")
    for i, doc in enumerate(daily_docs[:3]):  # Show first 3
        if '[EVENT_DATE:' in doc:
            import re
            date_match = re.search(r'\[EVENT_DATE:(\d{4}-\d{2}-\d{2})\]', doc)
            if date_match:
                print(f"  Document {i+1}: Has EVENT_DATE: {date_match.group(1)}")
        else:
            print(f"  Document {i+1}: MISSING EVENT_DATE tag")

# Show sample daily document
if daily_docs:
    print(f"\nSample daily document (first 500 chars):")
    print("=" * 50)
    print(daily_docs[0][:500])
    print("=" * 50)

print("\n✅ Test complete!")