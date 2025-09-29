# /Users/royyeo/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/Capstone Project/ice_data_ingestion/tests/test_news_integration.py
# Integration tests for ICE news API system
# Tests complete news ingestion workflow with real API calls and data processing
# RELEVANT FILES: ../config.py, ../news_apis.py, ../news_processor.py, test_config.py

"""
Integration Tests for ICE News System

These tests verify the complete news ingestion workflow including:
- API client initialization and configuration
- News fetching from multiple providers
- Data processing and graph integration
- Error handling and fallback mechanisms
- Cache functionality and persistence

Note: These tests may make real API calls if API keys are configured.
Use mock responses for CI/CD environments.
"""

import os
import pytest
import tempfile
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from config import ICEConfig
from news_apis import NewsAPIManager, NewsArticle, NewsAPIProvider, SentimentScore
from news_processor import NewsProcessor
from alpha_vantage_client import AlphaVantageClient
from fmp_client import FMPClient
from marketaux_client import MarketAuxClient

class TestNewsIntegration:
    """Integration tests for the complete news system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        
        # Create test configuration
        self.config = ICEConfig(config_file=self.config_file)
        
        # Mock API keys for testing
        self.test_api_keys = {
            'ALPHA_VANTAGE_API_KEY': 'test_av_key_123',
            'FMP_API_KEY': 'test_fmp_key_123',
            'MARKETAUX_API_TOKEN': 'test_ma_token_123'
        }
    
    def create_mock_article(self, ticker="NVDA", sentiment=0.5) -> NewsArticle:
        """Create a mock news article for testing"""
        return NewsArticle(
            title=f"Breaking: {ticker} announces major AI breakthrough",
            content=f"{ticker} has announced a revolutionary new AI chip that could transform the industry. The company expects significant growth in the coming quarters. Supply chain dependencies on TSMC remain a key risk factor.",
            url=f"https://example.com/news/{ticker.lower()}-breakthrough",
            source="Tech News Daily",
            published_at=datetime.now() - timedelta(hours=2),
            provider=NewsAPIProvider.ALPHA_VANTAGE,
            ticker=ticker,
            sentiment_score=sentiment,
            sentiment_label=SentimentScore.POSITIVE if sentiment > 0.2 else SentimentScore.NEUTRAL,
            confidence=0.85,
            keywords=["AI", "chip", "technology"],
            entities=[ticker, "TSMC", "supply chain"],
            category="technology",
            metadata={"test": True}
        )
    
    @patch.dict(os.environ, {'ALPHA_VANTAGE_API_KEY': 'test_key'})
    def test_config_initialization(self):
        """Test configuration loading and validation"""
        config = ICEConfig()
        
        # Test configuration validation
        validation = config.validate_configuration()
        
        assert 'enabled_apis' in validation
        assert 'primary_api' in validation
        
        # Test manager creation
        manager = config.create_news_manager()
        assert isinstance(manager, NewsAPIManager)
    
    def test_news_manager_with_mock_clients(self):
        """Test news manager with mock API clients"""
        manager = NewsAPIManager()
        
        # Create mock client
        mock_client = Mock()
        mock_client.provider = NewsAPIProvider.ALPHA_VANTAGE
        mock_client.get_news.return_value = [
            self.create_mock_article("NVDA", 0.7),
            self.create_mock_article("TSMC", -0.3)
        ]
        mock_client.get_sentiment.return_value = 0.4
        
        # Register mock client
        manager.register_client(mock_client, set_as_primary=True)
        
        # Test news retrieval
        articles = manager.get_financial_news("NVDA", limit=5)
        assert len(articles) == 2
        assert all(isinstance(article, NewsArticle) for article in articles)
        
        # Test sentiment retrieval
        sentiment = manager.get_aggregated_sentiment("NVDA")
        assert sentiment is not None
        assert 'average' in sentiment
    
    def test_news_processor_integration(self):
        """Test news processor with sample articles"""
        processor = NewsProcessor(cache_dir=self.temp_dir)
        
        # Create test articles
        articles = [
            self.create_mock_article("NVDA", 0.8),
            self.create_mock_article("TSMC", -0.2),
            self.create_mock_article("AMD", 0.3)
        ]
        
        # Process articles
        entities, edges = processor.process_articles(articles)
        
        # Verify entities were extracted
        assert len(entities) > 0
        entity_names = [e.name for e in entities]
        assert "NVDA" in entity_names
        
        # Verify edges were created
        assert len(edges) > 0
        edge_types = set(e.relationship_type for e in edges)
        assert len(edge_types) > 0
        
        # Test LightRAG export format
        lightrag_doc = processor.export_to_lightrag_format(articles)
        assert "FINANCIAL NEWS ARTICLE" in lightrag_doc
        assert "NVDA" in lightrag_doc
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end news processing workflow"""
        # Setup components
        manager = NewsAPIManager()
        processor = NewsProcessor(cache_dir=self.temp_dir)
        
        # Mock API client
        mock_client = Mock()
        mock_client.provider = NewsAPIProvider.ALPHA_VANTAGE
        mock_client.get_news.return_value = [
            self.create_mock_article("AAPL", 0.6),
            self.create_mock_article("GOOGL", 0.2)
        ]
        
        manager.register_client(mock_client, set_as_primary=True)
        
        # Execute workflow
        # 1. Fetch news
        articles = manager.get_financial_news("AAPL", limit=10)
        assert len(articles) > 0
        
        # 2. Process for graph
        entities, edges = processor.process_articles(articles)
        assert len(entities) > 0
        assert len(edges) > 0
        
        # 3. Export for LightRAG
        lightrag_content = processor.export_to_lightrag_format(articles)
        assert len(lightrag_content) > 0
        
        # 4. Verify data quality
        for article in articles:
            assert article.title
            assert article.content
            assert article.published_at
            assert article.provider
    
    def test_error_handling_and_fallback(self):
        """Test error handling and fallback mechanisms"""
        manager = NewsAPIManager()
        
        # Mock primary client that fails
        failing_client = Mock()
        failing_client.provider = NewsAPIProvider.ALPHA_VANTAGE
        failing_client.get_news.side_effect = Exception("API Error")
        
        # Mock fallback client that works
        working_client = Mock()
        working_client.provider = NewsAPIProvider.FMP
        working_client.get_news.return_value = [self.create_mock_article()]
        
        # Register both clients
        manager.register_client(failing_client, set_as_primary=True)
        manager.register_client(working_client)
        
        # Test fallback functionality
        articles = manager.get_financial_news("TEST", limit=5, fallback=True)
        assert len(articles) > 0  # Should get results from fallback
    
    def test_cache_functionality(self):
        """Test caching mechanism"""
        from news_apis import NewsCache
        
        cache = NewsCache(cache_dir=self.temp_dir, ttl_hours=1)
        provider = NewsAPIProvider.ALPHA_VANTAGE
        endpoint = "test_endpoint"
        params = {"symbol": "TEST"}
        test_data = {"articles": [{"title": "Test Article"}]}
        
        # Test cache miss
        cached_data = cache.get(provider, endpoint, params)
        assert cached_data is None
        
        # Test cache set and hit
        cache.set(provider, endpoint, params, test_data)
        cached_data = cache.get(provider, endpoint, params)
        assert cached_data == test_data
    
    @pytest.mark.integration
    @patch.dict(os.environ, {'ALPHA_VANTAGE_API_KEY': 'demo'})
    def test_real_api_call(self):
        """Test with real API call (requires actual API key)"""
        # Skip this test if no real API key is available
        if not os.getenv('ALPHA_VANTAGE_API_KEY') or os.getenv('ALPHA_VANTAGE_API_KEY') == 'demo':
            pytest.skip("No real Alpha Vantage API key available")
        
        config = ICEConfig()
        manager = config.create_news_manager()
        
        # Make real API call
        articles = manager.get_financial_news("AAPL", limit=3)
        
        # Verify real data structure
        if articles:  # Only verify if we got results
            article = articles[0]
            assert isinstance(article.title, str)
            assert isinstance(article.content, str)
            assert isinstance(article.published_at, datetime)
            assert article.provider in [NewsAPIProvider.ALPHA_VANTAGE, NewsAPIProvider.FMP, NewsAPIProvider.MARKETAUX]
    
    def test_quota_tracking(self):
        """Test API quota tracking functionality"""
        from news_apis import APIQuota, NewsAPIProvider
        
        quota = APIQuota(
            provider=NewsAPIProvider.ALPHA_VANTAGE,
            requests_per_day=100,
            requests_used=0
        )
        
        # Test quota availability
        assert quota.can_make_request()
        
        # Test quota recording
        for i in range(50):
            quota.record_request()
        
        assert quota.requests_used == 50
        assert quota.can_make_request()
        
        # Test quota exhaustion
        for i in range(50):
            quota.record_request()
        
        assert quota.requests_used == 100
        assert not quota.can_make_request()
    
    def test_sentiment_aggregation(self):
        """Test sentiment aggregation across providers"""
        manager = NewsAPIManager()
        
        # Mock multiple clients with different sentiments
        client1 = Mock()
        client1.provider = NewsAPIProvider.ALPHA_VANTAGE
        client1.get_sentiment.return_value = 0.7
        
        client2 = Mock()
        client2.provider = NewsAPIProvider.FMP
        client2.get_sentiment.return_value = 0.3
        
        manager.register_client(client1)
        manager.register_client(client2)
        
        # Test aggregated sentiment
        sentiment_data = manager.get_aggregated_sentiment("TEST")
        
        assert sentiment_data is not None
        assert 'individual_scores' in sentiment_data
        assert 'average' in sentiment_data
        assert sentiment_data['average'] == 0.5  # (0.7 + 0.3) / 2
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])