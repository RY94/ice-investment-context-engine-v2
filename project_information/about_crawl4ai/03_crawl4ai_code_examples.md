# Crawl4AI Code Examples & Usage Patterns
# Location: /project_information/about_crawl4ai/03_crawl4ai_code_examples.md
# Purpose: Practical code examples for using Crawl4AI in ICE
# Why: Quick reference for developers implementing Crawl4AI features
# Relevant Files: crawl4ai_connector.py, data_ingestion.py, ice_building_workflow.ipynb

**Document Date:** 2025-10-18
**Target Audience:** Developers implementing Crawl4AI
**Complexity:** Beginner to Advanced

---

## Table of Contents

1. [Installation & Setup](#1-installation--setup)
2. [Basic Usage Examples](#2-basic-usage-examples)
3. [ICE-Specific Patterns](#3-ice-specific-patterns)
4. [Advanced Use Cases](#4-advanced-use-cases)
5. [Notebook Examples](#5-notebook-examples)
6. [Troubleshooting Common Issues](#6-troubleshooting-common-issues)

---

## 1. Installation & Setup

### 1.1 Install Crawl4AI

```bash
# Install Crawl4AI
pip install -U crawl4ai

# Post-installation setup (installs Playwright browsers)
crawl4ai-setup

# Verify installation
crawl4ai-doctor
```

**Expected Output:**
```
✅ Crawl4AI installed successfully
✅ Playwright browsers installed
✅ System ready for crawling
```

### 1.2 ICE Configuration

```bash
# Enable Crawl4AI in ICE
export ENABLE_CRAWL4AI=true

# Optional: Enable LLM extraction (costs money!)
export ENABLE_LLM_EXTRACTION=false  # Default: false (use CSS/XPath)

# Optional: Configure LLM provider
export LLM_PROVIDER="ollama/llama3.1:8b"  # Local LLM (free)

# Optional: Premium portal credentials
export GOLDMAN_RESEARCH_USER="your_username"
export GOLDMAN_RESEARCH_PASS="your_password"
```

### 1.3 Verify Setup

```python
from ice_data_ingestion.crawl4ai_connector import Crawl4AIConnector

# Create connector
connector = Crawl4AIConnector()

# Test basic fetch
import asyncio
result = asyncio.run(connector.fetch("https://example.com"))

if result['success']:
    print("✅ Crawl4AI working!")
    print(f"Content length: {len(result['content'])} chars")
else:
    print(f"❌ Error: {result['error']}")
```

---

## 2. Basic Usage Examples

### 2.1 Simple Markdown Extraction

**Use Case:** Extract clean Markdown from any webpage

```python
import asyncio
from ice_data_ingestion.crawl4ai_connector import Crawl4AIConnector

async def extract_markdown_example():
    connector = Crawl4AIConnector()

    # Fetch page
    result = await connector.fetch(
        url="https://example.com",
        extraction_strategy="markdown"  # Default
    )

    if result['success']:
        print(result['content'])  # Clean Markdown
        print(f"\nMetadata: {result['metadata']}")
    else:
        print(f"Error: {result['error']}")

# Run
asyncio.run(extract_markdown_example())
```

**Output:**
```markdown
# Example Domain

This domain is for use in illustrative examples...
```

### 2.2 JavaScript Execution

**Use Case:** Scrape JavaScript-heavy sites (React, Angular, Vue)

```python
async def javascript_example():
    connector = Crawl4AIConnector()

    result = await connector.fetch(
        url="https://investor.nvidia.com",
        wait_for="css:.earnings-section",  # Wait for specific element
        js_code="""
        // Execute JavaScript before extraction
        window.scrollTo(0, document.body.scrollHeight);  // Load all content
        await new Promise(r => setTimeout(r, 2000));      // Wait 2 seconds
        """
    )

    print(f"Extracted {len(result['content'])} chars")
    print(result['content'][:500])  # First 500 chars

asyncio.run(javascript_example())
```

### 2.3 Session Management

**Use Case:** Multi-page crawling with persistent state

```python
async def session_example():
    connector = Crawl4AIConnector()

    # Page 1: Create session
    result1 = await connector.fetch(
        url="https://example.com/page1",
        session_id="my_session"
    )

    # Page 2: Reuse session (cookies, auth state preserved)
    result2 = await connector.fetch(
        url="https://example.com/page2",
        session_id="my_session"  # Same session ID
    )

    print(f"Page 1: {len(result1['content'])} chars")
    print(f"Page 2: {len(result2['content'])} chars")

asyncio.run(session_example())
```

### 2.4 CSS Extraction

**Use Case:** Extract structured data with CSS selectors

```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def css_extraction_example():
    connector = Crawl4AIConnector()

    # Define extraction schema
    strategy = JsonCssExtractionStrategy(
        schema={
            "name": "News Articles",
            "baseSelector": ".article",  # Parent element
            "fields": [
                {"name": "title", "selector": "h2"},
                {"name": "author", "selector": ".author"},
                {"name": "date", "selector": "time"},
                {"name": "content", "selector": ".article-body"}
            ]
        }
    )

    result = await connector.fetch(
        url="https://news.example.com",
        extraction_strategy="css"  # Use custom strategy
    )

    # Result is structured JSON
    print(result['content'])

asyncio.run(css_extraction_example())
```

**Output:**
```json
[
    {
        "title": "Breaking News: ...",
        "author": "John Doe",
        "date": "2025-01-18",
        "content": "Full article text..."
    },
    ...
]
```

### 2.5 LLM Extraction (Optional)

**Use Case:** Extract unstructured data using AI

```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy

async def llm_extraction_example():
    # WARNING: This costs money (uses OpenAI/Ollama)
    connector = Crawl4AIConnector(enable_llm_extraction=True)

    strategy = LLMExtractionStrategy(
        provider="ollama/llama3.1:8b",  # Local LLM (free!)
        instruction="Extract: Company names, stock tickers, price targets, and analyst ratings"
    )

    result = await connector.fetch(
        url="https://research.example.com/report",
        extraction_strategy="llm"
    )

    # LLM extracts structured data from unstructured text
    print(result['content'])

asyncio.run(llm_extraction_example())
```

**Output:**
```json
{
    "companies": ["NVIDIA", "AMD", "Intel"],
    "tickers": ["NVDA", "AMD", "INTC"],
    "price_targets": [500, 150, 45],
    "ratings": ["Buy", "Hold", "Sell"]
}
```

---

## 3. ICE-Specific Patterns

### 3.1 Pattern 1: Scrape Investor Relations Page

**Use Case:** Extract earnings transcripts, presentations, financial data

```python
from updated_architectures.implementation.ice_simplified import create_ice_system

# Create ICE system with Crawl4AI enabled
import os
os.environ['ENABLE_CRAWL4AI'] = 'true'
ice = create_ice_system()

# Scrape NVIDIA investor relations
async def scrape_nvidia_ir():
    result = await ice.data_ingester.fetch_company_investor_relations('NVDA')

    print(f"Extracted {len(result)} chars from NVIDIA IR")
    print(result[:1000])  # First 1000 chars

    # Feed into LightRAG
    ice.ingest_text_document(
        content=result,
        metadata={
            'source': 'investor_relations',
            'ticker': 'NVDA',
            'type': 'earnings_transcript'
        }
    )

asyncio.run(scrape_nvidia_ir())
```

### 3.2 Pattern 2: Access Premium Research Portal

**Use Case:** Download reports from authenticated portals (Goldman Sachs, Morgan Stanley)

```python
from ice_data_ingestion.crawl4ai_connector import Crawl4AIConnector
from ice_data_ingestion.crawl4ai_config import PORTAL_CREDENTIALS

async def access_goldman_portal():
    connector = Crawl4AIConnector()

    # Login and download report
    result = await connector.fetch_with_auth(
        url="https://research.goldmansachs.com/report/12345",
        credentials=PORTAL_CREDENTIALS['goldman_sachs'],
        login_url=PORTAL_CREDENTIALS['goldman_sachs']['login_url'],
        session_id="goldman_session"
    )

    if result['success']:
        print("✅ Successfully downloaded Goldman research report!")
        print(f"Length: {len(result['content'])} chars")

        # Feed into ICE
        ice.ingest_text_document(
            content=result['content'],
            metadata={
                'source': 'goldman_sachs_research',
                'url': result['metadata']['url'],
                'timestamp': result['metadata']['timestamp']
            }
        )
    else:
        print(f"❌ Failed: {result['error']}")

asyncio.run(access_goldman_portal())
```

### 3.3 Pattern 3: Multi-Step Link Following

**Use Case:** Follow link chains from emails (email → portal → report)

```python
async def follow_email_link_chain():
    connector = Crawl4AIConnector()

    # Email contains this link
    initial_link = "https://research.example.com/landing"

    # Step 1: Portal landing page
    landing_result = await connector.fetch(
        url=initial_link,
        session_id="portal_session"
    )

    # Step 2: Navigate to search page
    search_result = await connector.fetch(
        url="https://research.example.com/search",
        session_id="portal_session",  # Reuse session
        js_code="""
        document.querySelector('#search_ticker').value = 'NVDA';
        document.querySelector('#submit').click();
        """
    )

    # Step 3: Extract report links
    # (Assume search_result contains links)

    # Step 4: Download report
    report_result = await connector.fetch(
        url="https://research.example.com/report/xyz",
        session_id="portal_session"  # Reuse session
    )

    print(f"Final report: {len(report_result['content'])} chars")

asyncio.run(follow_email_link_chain())
```

### 3.4 Pattern 4: Enhanced IntelligentLinkProcessor

**Use Case:** Automatically use Crawl4AI for complex links in email pipeline

```python
from imap_email_ingestion_pipeline.intelligent_link_processor import (
    IntelligentLinkProcessor, ClassifiedLink
)

async def process_email_links_with_crawl4ai():
    processor = IntelligentLinkProcessor()

    # Classified link from email
    link = ClassifiedLink(
        url="https://research.goldmansachs.com/report/12345",
        context="Download Full Report",
        classification="portal",  # Requires Crawl4AI
        priority=1,
        confidence=0.95,
        expected_content_type="pdf"
    )

    # Processor automatically uses Crawl4AI for portal links
    report = await processor.download_report(link)

    if report:
        print(f"✅ Downloaded: {report.url}")
        print(f"Content: {len(report.text_content)} chars")
    else:
        print("❌ Download failed")

asyncio.run(process_email_links_with_crawl4ai())
```

### 3.5 Pattern 5: Hybrid Strategy (Simple HTTP vs Crawl4AI)

**Use Case:** Automatically choose the right tool based on URL complexity

```python
from ice_data_ingestion.crawl4ai_config import is_complex_site

async def hybrid_fetch_example():
    ice = create_ice_system()

    urls = [
        "https://api.polygon.io/v2/aggs/ticker/NVDA",  # API - use simple HTTP
        "https://investor.nvidia.com/earnings",        # JS-heavy - use Crawl4AI
        "https://www.sec.gov/cgi-bin/browse-edgar",   # Static - use simple HTTP
        "https://research.goldmansachs.com/portal"     # Portal - use Crawl4AI
    ]

    for url in urls:
        if is_complex_site(url):
            print(f"🚀 Crawl4AI: {url}")
            result = await ice.data_ingester.crawl4ai.fetch(url)
        else:
            print(f"⚡ Simple HTTP: {url}")
            result = await ice.data_ingester.fetch_url_content(url)

        print(f"  → {len(result)} chars\n")

asyncio.run(hybrid_fetch_example())
```

---

## 4. Advanced Use Cases

### 4.1 Advanced: Concurrent Crawling

**Use Case:** Crawl multiple URLs in parallel (faster!)

```python
async def concurrent_crawling():
    connector = Crawl4AIConnector(max_concurrent=5)

    urls = [
        "https://investor.nvidia.com",
        "https://ir.amd.com",
        "https://investor.tsmc.com",
        "https://ir.intel.com",
        "https://investor.micron.com"
    ]

    # Crawl all URLs concurrently
    tasks = [connector.fetch(url) for url in urls]
    results = await asyncio.gather(*tasks)

    for url, result in zip(urls, results):
        status = "✅" if result['success'] else "❌"
        print(f"{status} {url}: {len(result['content']) if result['success'] else 'FAILED'} chars")

asyncio.run(concurrent_crawling())
```

### 4.2 Advanced: Custom Extraction Strategy

**Use Case:** Define custom extraction logic for specific sites

```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

def create_earnings_transcript_strategy():
    """Custom strategy for earnings call transcripts"""
    return JsonCssExtractionStrategy(
        schema={
            "name": "Earnings Transcript",
            "baseSelector": ".transcript-entry",
            "fields": [
                {"name": "speaker", "selector": ".speaker-name"},
                {"name": "role", "selector": ".speaker-title"},
                {"name": "timestamp", "selector": ".timestamp"},
                {"name": "text", "selector": ".speaker-text"},
                {"name": "sentiment", "selector": ".sentiment-indicator"}  # If available
            ]
        }
    )

async def extract_earnings_transcript():
    connector = Crawl4AIConnector()

    result = await connector.fetch(
        url="https://investor.nvidia.com/earnings/q4-2024",
        extraction_strategy=create_earnings_transcript_strategy()
    )

    # Structured transcript data
    transcript = result['content']
    for entry in transcript:
        print(f"[{entry['timestamp']}] {entry['speaker']} ({entry['role']}): {entry['text'][:100]}...")

asyncio.run(extract_earnings_transcript())
```

### 4.3 Advanced: Caching and Performance Optimization

**Use Case:** Reduce costs and improve performance with caching

```python
async def caching_example():
    connector = Crawl4AIConnector()

    url = "https://investor.nvidia.com"

    # First fetch (not cached, slow)
    import time
    start = time.time()
    result1 = await connector.fetch(url, use_cache=True)
    time1 = time.time() - start
    print(f"First fetch: {time1:.2f}s, {len(result1['content'])} chars")

    # Second fetch (cached, fast!)
    start = time.time()
    result2 = await connector.fetch(url, use_cache=True)
    time2 = time.time() - start
    print(f"Second fetch: {time2:.2f}s, {len(result2['content'])} chars (cached!)")

    # Check statistics
    stats = connector.get_stats()
    print(f"\nStats: {stats}")
    # {
    #   'total_crawls': 2,
    #   'successful_crawls': 2,
    #   'cached_results': 1,
    #   'cache_hit_rate': 0.50
    # }

asyncio.run(caching_example())
```

### 4.4 Advanced: Error Handling and Retries

**Use Case:** Robust error handling for production

```python
async def robust_crawling():
    connector = Crawl4AIConnector()

    urls = [
        "https://valid-site.com",
        "https://broken-site.com/404",
        "https://timeout-site.com/slow"
    ]

    for url in urls:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await connector.fetch(url)

                if result['success']:
                    print(f"✅ {url}: Success")
                    break
                else:
                    print(f"⚠️ {url}: Attempt {attempt+1}/{max_retries} failed - {result['error']}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                print(f"❌ {url}: Exception - {e}")
                if attempt == max_retries - 1:
                    print(f"❌ {url}: All retries exhausted")

asyncio.run(robust_crawling())
```

---

## 5. Notebook Examples

### 5.1 Building Workflow Notebook

**File:** `ice_building_workflow.ipynb`

```python
# Cell 1: Setup
import os
import asyncio
os.environ['ENABLE_CRAWL4AI'] = 'true'

from updated_architectures.implementation.ice_simplified import create_ice_system
ice = create_ice_system()

# Cell 2: Scrape Investor Relations Pages
tickers = ['NVDA', 'AMD', 'TSMC', 'INTC']

async def scrape_all_ir_pages():
    for ticker in tickers:
        print(f"\nScraping {ticker} IR page...")
        result = await ice.data_ingester.fetch_company_investor_relations(ticker)

        if result:
            print(f"✅ {ticker}: {len(result)} chars")
            # Ingest into LightRAG
            ice.ingest_text_document(
                content=result,
                metadata={'source': 'ir_page', 'ticker': ticker}
            )
        else:
            print(f"❌ {ticker}: Failed")

await scrape_all_ir_pages()

# Cell 3: Verify Data Ingested
print(f"\nTotal documents in LightRAG: {ice.get_document_count()}")

# Cell 4: Query with Enhanced Data
result = ice.query(
    "What did NVDA say about AI in the latest earnings call?",
    mode="hybrid"
)
print(result)
```

### 5.2 Query Workflow Notebook

**File:** `ice_query_workflow.ipynb`

```python
# Cell 1: Compare Simple HTTP vs Crawl4AI
import os

# Test 1: Without Crawl4AI
os.environ['ENABLE_CRAWL4AI'] = 'false'
ice_simple = create_ice_system()

query = "What are NVDA's recent earnings highlights?"
result_simple = ice_simple.query(query, mode="hybrid")
print(f"Simple HTTP Result: {len(result_simple)} chars")

# Test 2: With Crawl4AI
os.environ['ENABLE_CRAWL4AI'] = 'true'
ice_crawl4ai = create_ice_system()

result_crawl4ai = ice_crawl4ai.query(query, mode="hybrid")
print(f"Crawl4AI Result: {len(result_crawl4ai)} chars")

# Compare
print(f"\nImprovement: {len(result_crawl4ai) - len(result_simple)} chars (+{(len(result_crawl4ai) / len(result_simple) - 1) * 100:.1f}%)")

# Cell 2: Crawl4AI Statistics
if ice_crawl4ai.data_ingester.crawl4ai:
    stats = ice_crawl4ai.data_ingester.crawl4ai.get_stats()
    print("\nCrawl4AI Statistics:")
    print(f"  Total crawls: {stats['total_crawls']}")
    print(f"  Successful: {stats['successful_crawls']}")
    print(f"  Failed: {stats['failed_crawls']}")
    print(f"  Success rate: {stats['success_rate']:.1%}")
    print(f"  Cache hit rate: {stats['cache_hit_rate']:.1%}")
```

---

## 6. Troubleshooting Common Issues

### 6.1 Issue: "Playwright browsers not installed"

**Error:**
```
playwright._impl._api_types.Error: Executable doesn't exist
```

**Solution:**
```bash
# Run post-installation setup
crawl4ai-setup

# Or manually install Playwright browsers
playwright install
```

### 6.2 Issue: "Session authentication failed"

**Error:**
```
Authentication failed: Login unsuccessful
```

**Solution:**
```python
# Debug login process
async def debug_login():
    connector = Crawl4AIConnector()

    # Add debugging
    result = await connector.fetch(
        url="https://research.example.com/login",
        js_code="""
        console.log('Username field:', document.querySelector('#username'));
        console.log('Password field:', document.querySelector('#password'));
        // Check if selectors are correct
        """
    )

# Fix: Update selectors in _login_to_portal() method
# Try alternative selectors:
# input[name="username"], input[type="email"], input[id="email"]
```

### 6.3 Issue: "JavaScript timeout"

**Error:**
```
Timeout waiting for element: css:.earnings-section
```

**Solution:**
```python
# Increase timeout
result = await connector.fetch(
    url="https://slow-site.com",
    wait_for="css:.earnings-section",
    js_code="await new Promise(r => setTimeout(r, 10000));",  # Wait 10s instead of 2s
    timeout=30000  # 30 second timeout
)
```

### 6.4 Issue: "Cache is stale"

**Problem:** Cached content is outdated

**Solution:**
```python
# Option 1: Disable cache
result = await connector.fetch(url, use_cache=False)

# Option 2: Clear cache
import shutil
shutil.rmtree("./data/crawl4ai_cache")
os.makedirs("./data/crawl4ai_cache")

# Option 3: Implement TTL (time-to-live) in cache
# TODO: Use smart_cache.py with TTL support
```

### 6.5 Issue: "LLM extraction is expensive"

**Problem:** High costs from OpenAI API

**Solution:**
```python
# Use local LLM (free!)
connector = Crawl4AIConnector(
    enable_llm_extraction=True,
    llm_provider="ollama/llama3.1:8b"  # Local Ollama
)

# Or disable LLM extraction entirely
connector = Crawl4AIConnector(
    enable_llm_extraction=False  # Use CSS extraction only
)
```

### 6.6 Issue: "Website blocks Crawl4AI"

**Problem:** Anti-bot detection

**Solution:**
```python
# Use stealth mode (built into Crawl4AI)
# Configure headers and user agent in session_config

# Or use proxy rotation
# TODO: Add proxy support to Crawl4AIConnector
```

### 6.7 Issue: "Graceful degradation not working"

**Problem:** Crawl4AI fails and system crashes

**Solution:**
```python
# Ensure fallback logic in data_ingestion.py
async def fetch_url_content(self, url: str) -> str:
    if self.crawl4ai and is_complex_site(url):
        try:
            result = await self.crawl4ai.fetch(url)
            if result['success']:
                return result['content']
        except Exception as e:
            logger.warning(f"Crawl4AI failed: {e}, falling back")
            # CRITICAL: Don't return here, fall through to simple HTTP

    # Fallback: Simple HTTP (ALWAYS execute if Crawl4AI fails)
    return requests.get(url, timeout=self.timeout).text
```

---

## Quick Reference

### Common Commands

```bash
# Install
pip install -U crawl4ai && crawl4ai-setup

# Enable/Disable
export ENABLE_CRAWL4AI=true    # Enable
export ENABLE_CRAWL4AI=false   # Disable

# Test
python -c "from ice_data_ingestion.crawl4ai_connector import Crawl4AIConnector; print('✅ Working')"
```

### Common Patterns

```python
# Pattern 1: Simple fetch
result = await connector.fetch("https://example.com")

# Pattern 2: JavaScript execution
result = await connector.fetch(url, wait_for="css:.content", js_code="window.scrollTo(0, 9999);")

# Pattern 3: Session
result = await connector.fetch(url, session_id="my_session")

# Pattern 4: CSS extraction
result = await connector.fetch(url, extraction_strategy="css")

# Pattern 5: LLM extraction
result = await connector.fetch(url, extraction_strategy="llm")
```

### Performance Tips

1. **Use caching**: `use_cache=True` (default)
2. **Limit concurrency**: `max_concurrent=3` (default)
3. **Prefer CSS over LLM**: CSS is free and fast
4. **Use local LLM if needed**: Ollama instead of OpenAI
5. **Hybrid strategy**: Crawl4AI only for complex sites

---

**Document Version:** 1.0
**Last Updated:** 2025-10-18
**Next Review:** After Phase 2 validation
**Status:** READY FOR USE ✅
