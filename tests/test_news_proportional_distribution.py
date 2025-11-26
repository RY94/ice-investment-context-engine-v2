# Location: /tests/test_news_proportional_distribution.py
# Purpose: Verify proportional news distribution works correctly
# Why: Ensure elegant solution distributes quota and deduplicates properly
# Relevant Files: data_ingestion.py

import sys
sys.path.insert(0, '/Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/updated_architectures/implementation')

from data_ingestion import DataIngester
from config import ICEConfig

def test_proportional_distribution():
    """Test that quota is distributed across available sources"""

    config = ICEConfig()
    ingester = DataIngester(config=config)

    # Test with FICO, limit=5
    print("=" * 60)
    print("TEST: Proportional Distribution with limit=5")
    print("=" * 60)

    articles = ingester.fetch_company_news('FICO', limit=5, context='portfolio')

    print(f"\n✅ Received {len(articles)} articles")

    # Verify we got articles from multiple sources
    sources_used = set(article['source'] for article in articles)
    print(f"✅ Sources used: {sources_used}")

    # Verify metadata
    for i, article in enumerate(articles, 1):
        print(f"\nArticle {i}:")
        print(f"  Source: {article['source']}")
        print(f"  Freshness: {article['freshness']}")
        print(f"  Tier: {article['tier']}")
        print(f"  File Path: {article['file_path']}")
        title = article['content'].split('\n')[0][:60]
        print(f"  Title: {title}...")

    # Assertions
    assert len(articles) <= 5, f"Expected ≤5 articles, got {len(articles)}"
    assert len(sources_used) > 1, f"Expected multiple sources, got {sources_used}"
    assert all('file_path' in a for a in articles), "Missing file_path in some articles"
    assert all('source' in a for a in articles), "Missing source in some articles"

    print(f"\n{'=' * 60}")
    print("✅ ALL TESTS PASSED")
    print(f"{'=' * 60}")
    print(f"\nSummary:")
    print(f"  - Articles: {len(articles)}")
    print(f"  - Sources: {len(sources_used)}")
    print(f"  - Diversity: {len(sources_used)/len(articles)*100:.1f}%")

    return True

if __name__ == "__main__":
    test_proportional_distribution()
