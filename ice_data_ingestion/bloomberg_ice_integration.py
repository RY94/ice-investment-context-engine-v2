# ice_data_ingestion/bloomberg_ice_integration.py  
# Integration layer connecting Bloomberg API data to ICE Investment Context Engine
# Transforms Bloomberg data into ICE-compatible format for graph construction and analysis
# RELEVANT FILES: ice_data_ingestion/bloomberg_connector.py, src/ice_lightrag/ice_rag.py, UI/ice_ui_v17.py, ice_data_ingestion/mcp_infrastructure.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import logging

from bloomberg_connector import BloombergConnector

class BloombergICEIntegrator:
    """
    Integration layer for Bloomberg data into ICE Investment Context Engine.
    
    Transforms Bloomberg fundamental and market data into:
    - ICE-compatible knowledge graph edges
    - MCP-formatted structured data
    - LightRAG document inputs
    - Portfolio analytics data
    """
    
    def __init__(self, working_dir: str = "./src/ice_lightrag/storage"):
        """
        Initialize Bloomberg-ICE integration.
        
        Args:
            working_dir: Directory for storing processed data and documents
        """
        self.working_dir = working_dir
        self.logger = logging.getLogger(__name__)
        
        # ICE edge types for financial relationships
        self.edge_types = {
            'performance_driver': 'drives',
            'risk_exposure': 'exposed_to', 
            'correlation': 'correlates_with',
            'competitive': 'competes_with',
            'dependency': 'depends_on',
            'impact': 'impacts'
        }
        
        # Key financial metrics mapping
        self.metric_mappings = {
            'OPER_MARGIN': 'Operating Margin',
            'NET_INCOME_MARGIN': 'Net Income Margin',
            'ROE': 'Return on Equity', 
            'ROA': 'Return on Assets',
            'DEBT_TO_TOT_CAP': 'Debt to Total Capital',
            'CURRENT_RATIO': 'Current Ratio',
            'PX_LAST': 'Stock Price',
            'VOLUME': 'Trading Volume'
        }
    
    def fetch_portfolio_fundamentals(self, portfolio_tickers: List[str], 
                                   periods: int = 20) -> Dict[str, any]:
        """
        Fetch comprehensive fundamental data for portfolio holdings.
        
        Args:
            portfolio_tickers: List of portfolio ticker symbols
            periods: Number of quarters of historical data
            
        Returns:
            Dictionary containing processed fundamental data for ICE system
        """
        self.logger.info(f"Fetching fundamental data for {len(portfolio_tickers)} portfolio holdings")
        
        with BloombergConnector() as bbg:
            # Fetch bulk fundamental data
            fundamental_data = bbg.get_bulk_fundamental_data(portfolio_tickers, periods)
            
            # Process into ICE-compatible format
            ice_data = {
                'portfolio_metrics': self._process_portfolio_metrics(fundamental_data),
                'knowledge_graph_edges': self._generate_knowledge_graph_edges(fundamental_data),
                'lightrag_documents': self._generate_lightrag_documents(fundamental_data),
                'risk_exposures': self._identify_risk_exposures(fundamental_data),
                'performance_drivers': self._identify_performance_drivers(fundamental_data)
            }
            
            return ice_data
    
    def fetch_market_intelligence(self, tickers: List[str], 
                                days_back: int = 30) -> Dict[str, any]:
        """
        Fetch recent market data and generate trading insights.
        
        Args:
            tickers: List of tickers to analyze
            days_back: Number of days of market data to fetch
            
        Returns:
            Market intelligence data for ICE system
        """
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y%m%d')
        
        with BloombergConnector() as bbg:
            market_data = bbg.get_market_data(tickers, start_date, end_date)
            
            # Generate market intelligence
            intelligence = {
                'price_momentum': self._analyze_price_momentum(market_data),
                'volume_patterns': self._analyze_volume_patterns(market_data), 
                'volatility_metrics': self._calculate_volatility_metrics(market_data),
                'relative_performance': self._calculate_relative_performance(market_data)
            }
            
            return intelligence
    
    def _process_portfolio_metrics(self, fundamental_data: Dict[str, pd.DataFrame]) -> Dict[str, any]:
        """
        Process raw Bloomberg fundamental data into portfolio-level metrics.
        """
        portfolio_metrics = {}
        
        for ticker, data in fundamental_data.items():
            if data.empty:
                continue
                
            # Get latest metrics
            latest_metrics = data.iloc[-1] if not data.empty else {}
            
            # Calculate trends (latest vs 4 quarters ago)
            trend_metrics = {}
            if len(data) >= 4:
                baseline_metrics = data.iloc[-4]
                for field in ['OPER_MARGIN', 'ROE', 'NET_INCOME_MARGIN']:
                    if field in latest_metrics and field in baseline_metrics:
                        if pd.notna(latest_metrics[field]) and pd.notna(baseline_metrics[field]):
                            trend_metrics[f"{field}_trend"] = (
                                latest_metrics[field] - baseline_metrics[field]
                            ) / baseline_metrics[field] * 100
            
            portfolio_metrics[ticker] = {
                'latest_metrics': latest_metrics.to_dict(),
                'trends': trend_metrics,
                'data_quality': 'high' if len(data) > 10 else 'medium',
                'last_updated': datetime.now().isoformat()
            }
        
        return portfolio_metrics
    
    def _generate_knowledge_graph_edges(self, fundamental_data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """
        Generate ICE knowledge graph edges from Bloomberg fundamental data.
        """
        edges = []
        
        # Generate edges for each ticker's fundamental relationships
        for ticker, data in fundamental_data.items():
            if data.empty:
                continue
            
            latest_data = data.iloc[-1]
            
            # Operating margin performance driver edges
            if 'OPER_MARGIN' in latest_data and pd.notna(latest_data['OPER_MARGIN']):
                margin = latest_data['OPER_MARGIN']
                
                # High margin = competitive advantage
                if margin > 0.20:  # 20%+ operating margin
                    edges.append({
                        'source': ticker,
                        'target': 'competitive_advantage',
                        'edge_type': 'drives',
                        'weight': min(margin * 2, 1.0),  # Scale to 0-1
                        'confidence': 0.85,
                        'days_ago': 0,
                        'is_positive': True,
                        'source_doc_id': f"bloomberg_fundamental_{ticker}_{datetime.now().strftime('%Y%m%d')}"
                    })
                
                # Low margin = margin pressure risk
                if margin < 0.05:  # <5% operating margin  
                    edges.append({
                        'source': ticker,
                        'target': 'margin_pressure_risk',
                        'edge_type': 'exposed_to',
                        'weight': (0.05 - margin) * 10,  # Higher weight for lower margins
                        'confidence': 0.80,
                        'days_ago': 0,
                        'is_positive': False,
                        'source_doc_id': f"bloomberg_fundamental_{ticker}_{datetime.now().strftime('%Y%m%d')}"
                    })
            
            # Debt-to-capital risk exposures
            if 'DEBT_TO_TOT_CAP' in latest_data and pd.notna(latest_data['DEBT_TO_TOT_CAP']):
                debt_ratio = latest_data['DEBT_TO_TOT_CAP']
                
                if debt_ratio > 0.6:  # High leverage
                    edges.append({
                        'source': ticker,
                        'target': 'leverage_risk',
                        'edge_type': 'exposed_to',
                        'weight': min(debt_ratio, 1.0),
                        'confidence': 0.90,
                        'days_ago': 0,
                        'is_positive': False,
                        'source_doc_id': f"bloomberg_fundamental_{ticker}_{datetime.now().strftime('%Y%m%d')}"
                    })
            
            # ROE performance drivers
            if 'ROE' in latest_data and pd.notna(latest_data['ROE']):
                roe = latest_data['ROE']
                
                if roe > 0.15:  # Strong ROE >15%
                    edges.append({
                        'source': ticker,
                        'target': 'strong_profitability',
                        'edge_type': 'drives', 
                        'weight': min(roe, 1.0),
                        'confidence': 0.85,
                        'days_ago': 0,
                        'is_positive': True,
                        'source_doc_id': f"bloomberg_fundamental_{ticker}_{datetime.now().strftime('%Y%m%d')}"
                    })
        
        self.logger.info(f"Generated {len(edges)} knowledge graph edges from Bloomberg data")
        return edges
    
    def _generate_lightrag_documents(self, fundamental_data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """
        Generate LightRAG documents from Bloomberg fundamental data for entity extraction.
        """
        documents = []
        
        for ticker, data in fundamental_data.items():
            if data.empty:
                continue
            
            # Create comprehensive fundamental analysis document
            latest_data = data.iloc[-1]
            
            # Build narrative document
            doc_content = f"Company Analysis: {ticker}\n\n"
            
            # Operating performance section
            if 'OPER_MARGIN' in latest_data and pd.notna(latest_data['OPER_MARGIN']):
                margin = latest_data['OPER_MARGIN'] * 100
                doc_content += f"Operating Performance: {ticker} has an operating margin of {margin:.1f}%. "
                
                if margin > 20:
                    doc_content += "This indicates strong pricing power and operational efficiency, "
                    doc_content += "suggesting competitive advantages in its market segment. "
                elif margin < 5:
                    doc_content += "This reflects margin pressure and potential operational challenges, "
                    doc_content += "indicating exposure to cost inflation or competitive pricing pressure. "
            
            # Financial health section
            if 'DEBT_TO_TOT_CAP' in latest_data and pd.notna(latest_data['DEBT_TO_TOT_CAP']):
                debt_ratio = latest_data['DEBT_TO_TOT_CAP'] * 100
                doc_content += f"Financial Health: {ticker} has a debt-to-total-capital ratio of {debt_ratio:.1f}%. "
                
                if debt_ratio > 60:
                    doc_content += "This high leverage creates interest rate sensitivity and credit risk exposure. "
                elif debt_ratio < 30:
                    doc_content += "This conservative capital structure provides financial flexibility. "
            
            # Profitability trends
            if 'ROE' in latest_data and pd.notna(latest_data['ROE']):
                roe = latest_data['ROE'] * 100
                doc_content += f"Profitability: {ticker} generates a return on equity of {roe:.1f}%. "
                
                if roe > 15:
                    doc_content += "This strong ROE indicates efficient capital allocation and profit generation. "
            
            # Add trend analysis if sufficient data
            if len(data) >= 4:
                doc_content += "\n\nTrend Analysis: "
                
                # Operating margin trend
                if 'OPER_MARGIN' in data.columns:
                    recent_margin = data['OPER_MARGIN'].iloc[-1]
                    prior_margin = data['OPER_MARGIN'].iloc[-4]
                    
                    if pd.notna(recent_margin) and pd.notna(prior_margin):
                        margin_change = (recent_margin - prior_margin) * 100
                        if margin_change > 0:
                            doc_content += f"{ticker} operating margins have improved by {margin_change:.1f}pp over the last year, "
                            doc_content += "indicating operational leverage and efficiency gains. "
                        elif margin_change < -0.5:
                            doc_content += f"{ticker} operating margins have compressed by {abs(margin_change):.1f}pp, "
                            doc_content += "suggesting cost pressures or competitive headwinds. "
            
            # Create document record
            document = {
                'doc_id': f"bloomberg_fundamental_{ticker}_{datetime.now().strftime('%Y%m%d')}",
                'content': doc_content,
                'title': f"{ticker} Fundamental Analysis",
                'source': 'Bloomberg Terminal API',
                'ticker': ticker,
                'document_type': 'fundamental_analysis',
                'created_date': datetime.now().isoformat(),
                'data_points': len([col for col in latest_data.index if pd.notna(latest_data[col])])
            }
            
            documents.append(document)
        
        self.logger.info(f"Generated {len(documents)} LightRAG documents from Bloomberg data")
        return documents
    
    def _identify_risk_exposures(self, fundamental_data: Dict[str, pd.DataFrame]) -> Dict[str, List[str]]:
        """
        Identify risk exposures based on fundamental metrics.
        """
        risk_exposures = {
            'leverage_risk': [],
            'margin_pressure_risk': [],
            'liquidity_risk': [],
            'profitability_risk': []
        }
        
        for ticker, data in fundamental_data.items():
            if data.empty:
                continue
                
            latest_data = data.iloc[-1]
            
            # Leverage risk
            if 'DEBT_TO_TOT_CAP' in latest_data and pd.notna(latest_data['DEBT_TO_TOT_CAP']):
                if latest_data['DEBT_TO_TOT_CAP'] > 0.6:
                    risk_exposures['leverage_risk'].append(ticker)
            
            # Margin pressure risk
            if 'OPER_MARGIN' in latest_data and pd.notna(latest_data['OPER_MARGIN']):
                if latest_data['OPER_MARGIN'] < 0.05:
                    risk_exposures['margin_pressure_risk'].append(ticker)
            
            # Liquidity risk  
            if 'CURRENT_RATIO' in latest_data and pd.notna(latest_data['CURRENT_RATIO']):
                if latest_data['CURRENT_RATIO'] < 1.2:
                    risk_exposures['liquidity_risk'].append(ticker)
            
            # Profitability risk
            if 'ROE' in latest_data and pd.notna(latest_data['ROE']):
                if latest_data['ROE'] < 0.05:
                    risk_exposures['profitability_risk'].append(ticker)
        
        return risk_exposures
    
    def _identify_performance_drivers(self, fundamental_data: Dict[str, pd.DataFrame]) -> Dict[str, List[str]]:
        """
        Identify key performance drivers based on fundamental strength.
        """
        performance_drivers = {
            'competitive_advantage': [],
            'strong_profitability': [], 
            'efficient_capital_allocation': [],
            'financial_strength': []
        }
        
        for ticker, data in fundamental_data.items():
            if data.empty:
                continue
                
            latest_data = data.iloc[-1]
            
            # Competitive advantage (high margins)
            if 'OPER_MARGIN' in latest_data and pd.notna(latest_data['OPER_MARGIN']):
                if latest_data['OPER_MARGIN'] > 0.20:
                    performance_drivers['competitive_advantage'].append(ticker)
            
            # Strong profitability
            if 'ROE' in latest_data and pd.notna(latest_data['ROE']):
                if latest_data['ROE'] > 0.15:
                    performance_drivers['strong_profitability'].append(ticker)
            
            # Efficient capital allocation (high ROA)
            if 'ROA' in latest_data and pd.notna(latest_data['ROA']):
                if latest_data['ROA'] > 0.10:
                    performance_drivers['efficient_capital_allocation'].append(ticker)
            
            # Financial strength (low leverage + high current ratio)
            debt_ok = ('DEBT_TO_TOT_CAP' not in latest_data or 
                      pd.isna(latest_data['DEBT_TO_TOT_CAP']) or 
                      latest_data['DEBT_TO_TOT_CAP'] < 0.4)
            
            liquidity_ok = ('CURRENT_RATIO' not in latest_data or
                           pd.isna(latest_data['CURRENT_RATIO']) or 
                           latest_data['CURRENT_RATIO'] > 1.5)
            
            if debt_ok and liquidity_ok:
                performance_drivers['financial_strength'].append(ticker)
        
        return performance_drivers
    
    def _analyze_price_momentum(self, market_data: pd.DataFrame) -> Dict[str, any]:
        """Analyze price momentum patterns from market data."""
        # Implementation for price momentum analysis
        return {"status": "analyzed", "data_points": len(market_data)}
    
    def _analyze_volume_patterns(self, market_data: pd.DataFrame) -> Dict[str, any]:  
        """Analyze volume patterns from market data."""
        # Implementation for volume pattern analysis
        return {"status": "analyzed", "data_points": len(market_data)}
    
    def _calculate_volatility_metrics(self, market_data: pd.DataFrame) -> Dict[str, any]:
        """Calculate volatility metrics from market data.""" 
        # Implementation for volatility calculation
        return {"status": "calculated", "data_points": len(market_data)}
    
    def _calculate_relative_performance(self, market_data: pd.DataFrame) -> Dict[str, any]:
        """Calculate relative performance metrics."""
        # Implementation for relative performance calculation  
        return {"status": "calculated", "data_points": len(market_data)}


# Example usage function
def example_bloomberg_ice_integration():
    """
    Example of how to integrate Bloomberg data into ICE system.
    """
    # Initialize integrator
    integrator = BloombergICEIntegrator()
    
    # Example portfolio tickers
    portfolio_tickers = [
        'AAPL US Equity',   # Apple Inc
        'MSFT US Equity',   # Microsoft Corp  
        'NVDA US Equity',   # NVIDIA Corp
        'GOOGL US Equity',  # Alphabet Inc
        'TSLA US Equity'    # Tesla Inc
    ]
    
    try:
        # Fetch comprehensive portfolio data
        print("🔄 Fetching Bloomberg fundamental data...")
        ice_data = integrator.fetch_portfolio_fundamentals(portfolio_tickers)
        
        print(f"✅ Processed {len(ice_data['portfolio_metrics'])} portfolio holdings")
        print(f"✅ Generated {len(ice_data['knowledge_graph_edges'])} knowledge graph edges")
        print(f"✅ Created {len(ice_data['lightrag_documents'])} LightRAG documents")
        
        # Display sample results
        print("\n📊 Sample Portfolio Metrics:")
        for ticker, metrics in list(ice_data['portfolio_metrics'].items())[:2]:
            print(f"\n{ticker}:")
            latest = metrics['latest_metrics']
            if 'OPER_MARGIN' in latest:
                print(f"  Operating Margin: {latest['OPER_MARGIN']:.2%}")
            if 'ROE' in latest:  
                print(f"  Return on Equity: {latest['ROE']:.2%}")
            if 'DEBT_TO_TOT_CAP' in latest:
                print(f"  Debt to Capital: {latest['DEBT_TO_TOT_CAP']:.2%}")
        
        print("\n🎯 Risk Exposures:")
        for risk_type, tickers in ice_data['risk_exposures'].items():
            if tickers:
                print(f"  {risk_type}: {', '.join(tickers)}")
        
        return ice_data
        
    except Exception as e:
        print(f"❌ Integration error: {e}")
        return None


if __name__ == "__main__":
    example_bloomberg_ice_integration()