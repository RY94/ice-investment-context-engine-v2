# ice_data_ingestion/ice_integration.py
"""
Integration layer between data ingestion system and ICE LightRAG
Bridges real-time financial data with graph-based knowledge system
Formats ingested data for optimal LightRAG processing and knowledge graph construction
Relevant files: ../src/ice_lightrag/ice_rag.py, mcp_data_manager.py, free_api_connectors.py
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from .mcp_data_manager import mcp_data_manager, DataType, FinancialDataQuery
from .free_api_connectors import free_api_manager

logger = logging.getLogger(__name__)


class ICEDataIntegrationManager:
    """Integration manager for ICE data ingestion and LightRAG system"""
    
    def __init__(self):
        """Initialize ICE integration manager"""
        self.mcp_manager = mcp_data_manager
        self.fallback_manager = free_api_manager
        self.ice_rag = None
        self._initialize_ice_rag()
        
    def _initialize_ice_rag(self):
        """Initialize ICE LightRAG system with lazy import to avoid circular dependencies"""
        try:
            # Lazy import to avoid circular dependencies
            from src.ice_lightrag import ICELightRAG
            self.ice_rag = ICELightRAG(working_dir="./src/ice_lightrag/storage")
            logger.info("ICE LightRAG system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ICE LightRAG: {e}")
            self.ice_rag = None
    
    async def ingest_company_intelligence(self, symbol: str, add_to_knowledge_base: bool = True) -> Dict[str, Any]:
        """
        Ingest comprehensive company intelligence and optionally add to knowledge base
        
        Returns structured intelligence suitable for both immediate use and long-term storage
        """
        try:
            # First try MCP servers for best performance and zero cost
            logger.info(f"Fetching intelligence for {symbol} via MCP servers")
            
            # Parallel fetch of different data types
            tasks = []
            data_types = [
                (DataType.STOCK_DATA, "stock information"),
                (DataType.NEWS, "recent news"),
                (DataType.SEC_FILINGS, "SEC filings")
            ]
            
            for data_type, description in data_types:
                query = FinancialDataQuery(data_type=data_type, symbol=symbol)
                task = self.mcp_manager.fetch_financial_data(query)
                tasks.append((data_type, description, task))
            
            # Execute all queries concurrently
            results = {}
            for data_type, description, task in tasks:
                try:
                    result = await task
                    results[data_type.value] = result
                    if result.success:
                        logger.info(f"Successfully fetched {description} for {symbol}")
                    else:
                        logger.warning(f"⚠️  MCP {description} unavailable, will use fallback sources")
                except Exception as e:
                    logger.error(f"Error fetching {description}: {e}")
                    results[data_type.value] = None
            
            # If MCP fails, try free API fallback
            fallback_used = False
            if not any(r and r.success for r in results.values() if r):
                logger.info(f"✅ Zero-cost fallback active: Using free APIs for {symbol} (MCP servers unavailable)")
                fallback_data = await free_api_manager.get_comprehensive_data(symbol)
                fallback_used = True
            else:
                fallback_data = None
            
            # Format intelligence for ICE system
            intelligence = self._format_intelligence(
                symbol, results, fallback_data, fallback_used
            )
            
            # Add to knowledge base if requested and ICE RAG is available
            if add_to_knowledge_base and self.ice_rag and self.ice_rag.is_ready():
                await self._add_to_knowledge_base(intelligence)
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Error ingesting intelligence for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "success": False
            }
    
    def _format_intelligence(self, symbol: str, mcp_results: Dict, fallback_data: Optional[Dict], fallback_used: bool) -> Dict[str, Any]:
        """Format raw data into structured intelligence suitable for ICE system"""
        
        intelligence = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "data_sources": [],
            "success": True,
            "fallback_used": fallback_used,
            
            # Core data sections
            "stock_data": {},
            "news_articles": [],
            "sec_filings": [],
            "key_insights": [],
            
            # Metadata
            "data_quality": {
                "confidence_score": 0.0,
                "sources_count": 0,
                "completeness_score": 0.0
            },
            
            # ICE-specific formatting
            "knowledge_graph_ready": True,
            "entity_extractions": [],
            "relationship_candidates": []
        }
        
        if fallback_used and fallback_data:
            # Use fallback data
            intelligence["stock_data"] = fallback_data.get("stock_data", {})
            intelligence["news_articles"] = fallback_data.get("news", [])
            intelligence["data_sources"] = fallback_data.get("sources_used", ["fallback_apis"])
            intelligence["data_quality"]["confidence_score"] = 0.7  # Lower confidence for fallback
            
        else:
            # Use MCP results
            total_confidence = 0.0
            source_count = 0
            
            # Process stock data
            stock_result = mcp_results.get("stock_data")
            if stock_result and stock_result.success and stock_result.stock_data:
                intelligence["stock_data"] = stock_result.stock_data[0]
                intelligence["data_sources"].extend(stock_result.sources)
                total_confidence += stock_result.confidence_score
                source_count += 1
            
            # Process news
            news_result = mcp_results.get("news")
            if news_result and news_result.success:
                intelligence["news_articles"] = news_result.news_articles
                intelligence["data_sources"].extend(news_result.sources)
                total_confidence += news_result.confidence_score
                source_count += 1
            
            # Process SEC filings
            sec_result = mcp_results.get("sec_filings")
            if sec_result and sec_result.success:
                intelligence["sec_filings"] = sec_result.sec_filings
                intelligence["data_sources"].extend(sec_result.sources)
                total_confidence += sec_result.confidence_score
                source_count += 1
            
            # Calculate overall quality metrics
            if source_count > 0:
                intelligence["data_quality"]["confidence_score"] = total_confidence / source_count
                intelligence["data_quality"]["sources_count"] = source_count
                intelligence["data_quality"]["completeness_score"] = min(1.0, source_count / 3.0)  # 3 expected data types
        
        # Extract key insights
        intelligence["key_insights"] = self._extract_key_insights(intelligence)
        
        # Prepare for knowledge graph integration
        intelligence["entity_extractions"] = self._extract_entities(intelligence)
        intelligence["relationship_candidates"] = self._identify_relationships(intelligence)
        
        return intelligence
    
    def _extract_key_insights(self, intelligence: Dict[str, Any]) -> List[str]:
        """Extract key insights from the intelligence data"""
        insights = []
        
        # Stock data insights
        stock_data = intelligence.get("stock_data", {})
        if stock_data:
            price = stock_data.get("price", 0)
            change_percent = stock_data.get("change_percent", 0)
            
            if abs(change_percent) > 5:
                direction = "gained" if change_percent > 0 else "declined"
                insights.append(f"{intelligence['symbol']} {direction} {abs(change_percent):.1f}% today")
            
            market_cap = stock_data.get("market_cap", 0)
            if market_cap > 1e12:  # > $1T
                insights.append(f"{intelligence['symbol']} is a mega-cap stock with ${market_cap/1e12:.1f}T market cap")
        
        # News insights
        news_articles = intelligence.get("news_articles", [])
        if news_articles:
            recent_count = len([a for a in news_articles if 
                             (datetime.now() - datetime.fromisoformat(a.get("published_at", "2020-01-01T00:00:00"))).days < 1])
            if recent_count > 3:
                insights.append(f"High news activity: {recent_count} articles in last 24 hours")
            
            # Sentiment analysis
            sentiments = [a.get("sentiment", 0) for a in news_articles if "sentiment" in a]
            if sentiments:
                avg_sentiment = sum(sentiments) / len(sentiments)
                if avg_sentiment > 0.6:
                    insights.append("Overall positive news sentiment")
                elif avg_sentiment < 0.4:
                    insights.append("Overall negative news sentiment")
        
        # SEC filing insights
        sec_filings = intelligence.get("sec_filings", [])
        if sec_filings:
            recent_filings = [f for f in sec_filings if 
                            (datetime.now() - datetime.fromisoformat(f.get("filing_date", "2020-01-01T00:00:00"))).days < 30]
            if recent_filings:
                insights.append(f"Recent regulatory activity: {len(recent_filings)} filings in last 30 days")
        
        return insights
    
    def _extract_entities(self, intelligence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract entities for knowledge graph construction"""
        entities = []
        
        # Company entity
        entities.append({
            "type": "company",
            "name": intelligence["symbol"],
            "attributes": intelligence.get("stock_data", {}),
            "confidence": 1.0
        })
        
        # Extract entities from news articles
        for article in intelligence.get("news_articles", []):
            # Simple entity extraction (in production, would use NLP)
            title = article.get("title", "")
            if "earnings" in title.lower():
                entities.append({
                    "type": "event",
                    "name": f"{intelligence['symbol']} earnings",
                    "attributes": {"article_title": title},
                    "confidence": 0.8
                })
        
        return entities
    
    def _identify_relationships(self, intelligence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify relationship candidates for knowledge graph"""
        relationships = []
        
        symbol = intelligence["symbol"]
        
        # Price movement relationships
        stock_data = intelligence.get("stock_data", {})
        if stock_data.get("change_percent", 0) != 0:
            relationships.append({
                "source": symbol,
                "target": "market_performance",
                "relationship": "exhibits",
                "attributes": {
                    "change_percent": stock_data.get("change_percent", 0),
                    "confidence": 0.9
                }
            })
        
        # News-based relationships
        for article in intelligence.get("news_articles", []):
            if "earnings" in article.get("title", "").lower():
                relationships.append({
                    "source": symbol,
                    "target": "earnings_event",
                    "relationship": "reported",
                    "attributes": {
                        "article_url": article.get("url", ""),
                        "confidence": 0.8
                    }
                })
        
        return relationships
    
    async def _add_to_knowledge_base(self, intelligence: Dict[str, Any]) -> bool:
        """Add intelligence data to ICE LightRAG knowledge base"""
        if not self.ice_rag or not self.ice_rag.is_ready():
            logger.warning("ICE LightRAG not available, skipping knowledge base update")
            return False
        
        try:
            documents_added = 0
            
            # Add stock data as structured document
            if intelligence.get("stock_data"):
                stock_doc = self._format_stock_document(intelligence)
                result = await self.ice_rag.add_document(stock_doc, doc_type="market_data")
                if result["status"] == "success":
                    documents_added += 1
            
            # Add news articles
            for article in intelligence.get("news_articles", []):
                news_doc = self._format_news_document(article, intelligence["symbol"])
                result = await self.ice_rag.add_document(news_doc, doc_type="news")
                if result["status"] == "success":
                    documents_added += 1
            
            # Add SEC filings
            for filing in intelligence.get("sec_filings", []):
                filing_doc = self._format_filing_document(filing, intelligence["symbol"])
                result = await self.ice_rag.add_document(filing_doc, doc_type="regulatory")
                if result["status"] == "success":
                    documents_added += 1
            
            logger.info(f"Added {documents_added} documents to knowledge base for {intelligence['symbol']}")
            return documents_added > 0
            
        except Exception as e:
            logger.error(f"Error adding to knowledge base: {e}")
            return False
    
    def _format_stock_document(self, intelligence: Dict[str, Any]) -> str:
        """Format stock data as LightRAG document"""
        symbol = intelligence["symbol"]
        stock_data = intelligence["stock_data"]
        
        doc = f"STOCK ANALYSIS: {symbol}\n"
        doc += f"Current Price: ${stock_data.get('price', 'N/A')}\n"
        doc += f"Daily Change: {stock_data.get('change_percent', 'N/A')}%\n"
        doc += f"Market Cap: ${stock_data.get('market_cap', 'N/A'):,}\n"
        doc += f"Volume: {stock_data.get('volume', 'N/A'):,}\n"
        
        if intelligence.get("key_insights"):
            doc += f"\nKey Insights:\n"
            for insight in intelligence["key_insights"]:
                doc += f"- {insight}\n"
        
        doc += f"\nData Sources: {', '.join(intelligence.get('data_sources', []))}\n"
        doc += f"Timestamp: {intelligence['timestamp']}\n"
        
        return doc
    
    def _format_news_document(self, article: Dict[str, Any], symbol: str) -> str:
        """Format news article as LightRAG document"""
        doc = f"NEWS ARTICLE: {symbol}\n"
        doc += f"Title: {article.get('title', 'No title')}\n"
        doc += f"Summary: {article.get('summary', 'No summary')}\n"
        doc += f"Published: {article.get('published_at', 'Unknown date')}\n"
        
        if "sentiment" in article:
            sentiment_label = "Positive" if article["sentiment"] > 0.6 else "Negative" if article["sentiment"] < 0.4 else "Neutral"
            doc += f"Sentiment: {sentiment_label} ({article['sentiment']:.2f})\n"
        
        doc += f"Source: {article.get('source', 'Unknown')}\n"
        
        if article.get('url'):
            doc += f"URL: {article['url']}\n"
        
        return doc
    
    def _format_filing_document(self, filing: Dict[str, Any], symbol: str) -> str:
        """Format SEC filing as LightRAG document"""
        doc = f"SEC FILING: {symbol}\n"
        doc += f"Form Type: {filing.get('form_type', 'Unknown')}\n"
        doc += f"Filing Date: {filing.get('filing_date', 'Unknown')}\n"
        doc += f"Company: {filing.get('company_name', symbol)}\n"
        
        if filing.get("key_metrics"):
            doc += "\nKey Financial Metrics:\n"
            for metric, value in filing["key_metrics"].items():
                doc += f"- {metric}: ${value:,}\n"
        
        doc += f"Accession Number: {filing.get('accession_number', 'Unknown')}\n"
        
        return doc
    
    async def query_enhanced_intelligence(self, query: str, context_symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Query the enhanced intelligence system combining real-time data and historical knowledge
        
        This method leverages both fresh data ingestion and stored knowledge for comprehensive analysis
        """
        if not self.ice_rag or not self.ice_rag.is_ready():
            return {
                "error": "ICE LightRAG not available",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # If context symbols provided, refresh their data first
            if context_symbols:
                logger.info(f"Refreshing data for context symbols: {context_symbols}")
                for symbol in context_symbols[:3]:  # Limit to 3 for performance
                    await self.ingest_company_intelligence(symbol, add_to_knowledge_base=True)
            
            # Query the knowledge base
            result = await self.ice_rag.query(query, mode="hybrid")
            
            if result["status"] == "success":
                return {
                    "query": query,
                    "answer": result["result"],
                    "timestamp": datetime.now().isoformat(),
                    "context_refreshed": context_symbols or [],
                    "success": True
                }
            else:
                return {
                    "query": query,
                    "error": result["message"],
                    "timestamp": datetime.now().isoformat(),
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Error in enhanced intelligence query: {e}")
            return {
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "success": False
            }


# Global instance for easy access
ice_integration_manager = ICEDataIntegrationManager()


async def get_live_company_intelligence(symbol: str, include_in_kb: bool = True) -> Dict[str, Any]:
    """
    High-level function to get live company intelligence
    
    This is the main entry point for getting fresh, comprehensive company data
    integrated with the ICE knowledge system
    """
    return await ice_integration_manager.ingest_company_intelligence(
        symbol, add_to_knowledge_base=include_in_kb
    )


async def query_ice_with_live_context(query: str, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Query ICE system with live market context
    
    Refreshes data for relevant symbols before querying to ensure most current context
    """
    return await ice_integration_manager.query_enhanced_intelligence(query, symbols)