# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/ice_data_ingestion/tests/__init__.py
# Test suite for ICE data ingestion module
# Provides comprehensive testing for news API clients and data processing
# RELEVANT FILES: test_news_apis.py, test_config.py, test_news_processor.py, ../news_apis.py

"""
ICE Data Ingestion Test Suite

This module contains comprehensive tests for the ICE news data ingestion system.
Tests cover API clients, configuration management, data processing, and integration.

Test Categories:
- Unit tests for individual API clients
- Integration tests for news manager
- Configuration validation tests
- Data processing pipeline tests
- Error handling and edge cases

Usage:
    # Run all tests
    python -m pytest ice_data_ingestion/tests/
    
    # Run specific test file
    python -m pytest ice_data_ingestion/tests/test_news_apis.py
    
    # Run with coverage
    python -m pytest ice_data_ingestion/tests/ --cov=ice_data_ingestion
"""

__version__ = "0.1.0"