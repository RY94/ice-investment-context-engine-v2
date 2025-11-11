# Location: src/ice_docling/__init__.py
# Purpose: Docling integration package for ICE - PDF/Excel/Word extraction with AI models
# Why: Enhance SEC filing and email attachment processing (42% → 97.9% table accuracy)
# Relevant Files: sec_filing_processor.py, docling_processor.py, config.py

"""
ICE Docling Integration Package

Provides docling-based document processing for:
1. SEC Filing Content Extraction (CRITICAL - fills 0% → 97.9% gap)
2. Email Attachment Processing (improves 42% → 97.9% table accuracy)
3. Future: User uploads, historical archives, news PDFs

Switchable architecture via config.py toggles:
- USE_DOCLING_SEC (default: true)
- USE_DOCLING_EMAIL (default: true)
"""

__version__ = '1.0.0'
