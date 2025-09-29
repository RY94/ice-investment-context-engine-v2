#!/usr/bin/env python3
"""
Python code to view SEC filing content
This demonstrates the actual filing data that feeds into your AI pipeline
"""

import asyncio
import sys
import os

# Add project path
sys.path.append('/Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project')

from ice_data_ingestion.sec_edgar_connector import sec_edgar_connector

async def view_sec_filing_content(ticker='AAPL', filing_index=0):
    """View SEC filing content and metadata"""
    
    print(f"🔍 Fetching SEC filing content for {ticker}...")
    
    # Get company info
    company_info = await sec_edgar_connector.get_company_info(ticker)
    if not company_info:
        print(f"❌ No company info found for {ticker}")
        return
    
    print(f"\n🏢 Company: {company_info.name}")
    print(f"CIK: {company_info.cik}")
    print(f"SIC: {company_info.sic} - {company_info.sic_description}")
    
    # Get recent filings
    filings = await sec_edgar_connector.get_recent_filings(ticker, 5)
    if not filings:
        print(f"❌ No filings found for {ticker}")
        return
    
    print(f"\n📄 Found {len(filings)} recent filings")
    
    # Show the specific filing
    if filing_index >= len(filings):
        print(f"❌ Filing index {filing_index} out of range")
        return
    
    filing = filings[filing_index]
    print(f"\n📋 Filing #{filing_index} Details:")
    print(f"Form Type: {filing.form}")
    print(f"Filing Date: {filing.filing_date}")
    print(f"Accession: {filing.accession_number}")
    print(f"Primary Doc: {filing.primary_document}")
    print(f"Description: {filing.primary_doc_description}")
    print(f"Size: {filing.size:,} bytes")
    
    # Get the actual filing content
    print(f"\n📖 Fetching filing content...")
    cik = await sec_edgar_connector.get_cik_by_ticker(ticker)
    content = await sec_edgar_connector.get_filing_content(filing, cik)
    
    if content:
        print(f"✅ Successfully retrieved {len(content):,} characters of content")
        
        # Show content preview
        print("\n" + "="*60)
        print("📄 FILING CONTENT PREVIEW (First 2000 characters)")
        print("="*60)
        print(content[:2000])
        print("="*60)
        print(f"... (showing first 2000 of {len(content):,} total characters)")
        print("="*60)
        
        # Show content structure analysis
        print(f"\n🔍 Content Analysis:")
        print(f"- Total length: {len(content):,} characters")
        print(f"- Contains HTML: {'Yes' if '<html>' in content.lower() else 'No'}")
        print(f"- Contains XML: {'Yes' if '<?xml' in content else 'No'}")
        print(f"- Contains XBRL: {'Yes' if 'xbrl' in content.lower() else 'No'}")
        
        # Extract key sections for AI processing
        lines = content.split('\n')
        print(f"- Total lines: {len(lines):,}")
        print(f"- Non-empty lines: {len([l for l in lines if l.strip()]):,}")
        
        # Document URL for reference
        accession_clean = filing.accession_number.replace('-', '')
        cik_clean = cik.lstrip('0') or '0'
        doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession_clean}/{filing.primary_document}"
        print(f"\n🔗 Full Document URL:")
        print(f"{doc_url}")
        
        return {
            'filing_metadata': {
                'form': filing.form,
                'date': filing.filing_date,
                'accession': filing.accession_number,
                'size': filing.size,
                'document': filing.primary_document,
                'description': filing.primary_doc_description
            },
            'company_info': {
                'name': company_info.name,
                'cik': company_info.cik,
                'sic': company_info.sic,
                'sic_description': company_info.sic_description
            },
            'content_preview': content[:2000],
            'content_length': len(content),
            'full_content': content,  # Full content for AI processing
            'document_url': doc_url
        }
    else:
        print("❌ Failed to retrieve filing content")
        return None

async def show_multiple_filings(ticker='AAPL', count=3):
    """Show content from multiple recent filings"""
    print(f"🔍 Showing {count} recent filings for {ticker}\n")
    
    filings = await sec_edgar_connector.get_recent_filings(ticker, count)
    
    for i, filing in enumerate(filings):
        print(f"\n{'='*20} FILING #{i} {'='*20}")
        print(f"Form: {filing.form} | Date: {filing.filing_date} | Size: {filing.size:,} bytes")
        
        # Get content preview
        cik = await sec_edgar_connector.get_cik_by_ticker(ticker)
        content = await sec_edgar_connector.get_filing_content(filing, cik)
        
        if content:
            print(f"Content preview (first 500 chars):")
            print("-" * 50)
            print(content[:500])
            print("-" * 50)
        else:
            print("❌ Could not retrieve content")

# Main execution
if __name__ == '__main__':
    print("🚀 SEC Filing Content Viewer")
    print("=" * 50)
    
    # Example 1: View single filing content
    print("\n1️⃣ SINGLE FILING DETAILED VIEW")
    result = asyncio.run(view_sec_filing_content('AAPL', 0))
    
    # Example 2: View multiple filings overview
    print("\n2️⃣ MULTIPLE FILINGS OVERVIEW")
    asyncio.run(show_multiple_filings('AAPL', 3))
    
    print("\n✅ This data structure feeds directly into your ICE AI system!")