# query_engine.py
"""
ICE Query Engine - Thin wrapper for portfolio analysis queries
Simple query patterns using LightRAG's built-in modes without complex optimization
Provides investment-focused query templates and portfolio analysis workflows
Relevant files: ice_core.py, ice_simplified.py
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class QueryEngine:
    """
    Thin wrapper for portfolio analysis queries

    Key principles:
    1. Simple query patterns, no complex planning or optimization
    2. Let LightRAG's built-in modes handle retrieval complexity
    3. Investment-focused query templates
    4. Direct passthrough to ICE core with minimal processing
    5. Portfolio-specific workflows without orchestration overhead
    """

    def __init__(self, ice_core):
        """
        Initialize query engine with ICE core

        Args:
            ice_core: ICECore instance for query execution
        """
        self.ice = ice_core
        self.query_templates = self._initialize_query_templates()

        logger.info("Query Engine initialized with investment-focused templates")

    def _initialize_query_templates(self) -> Dict[str, str]:
        """Initialize predefined query templates for common investment analysis"""
        return {
            'risks': "What are the main business and market risks facing {symbol}? Include supply chain, regulatory, competitive, and financial risks.",
            'opportunities': "What are the main growth opportunities and market advantages for {symbol}? Include technology trends, market expansion, and competitive positioning.",
            'fundamentals': "What are the key financial fundamentals and business metrics for {symbol}? Include revenue, profitability, and growth indicators.",
            'competitive_position': "What is {symbol}'s competitive position in its industry? How does it compare to competitors?",
            'valuation': "What is the current valuation and investment outlook for {symbol}? Is it undervalued or overvalued?",
            'recent_developments': "What are the most recent significant developments, news, and events affecting {symbol}?",
            'dependencies': "What are {symbol}'s key business dependencies, partnerships, and supply chain relationships?",
            'regulatory_exposure': "What regulatory and compliance risks does {symbol} face? How might policy changes affect the business?",
            'relationships': "What are the key business relationships, dependencies, and competitive dynamics between {symbols}?",
            'market_trends': "What are the major market trends and industry developments affecting {symbols}?",
            'portfolio_risks': "What are the aggregated risks across the portfolio of {symbols}? Identify correlations and systemic risks.",
            'portfolio_opportunities': "What are the combined growth opportunities and synergies across {symbols}?"
        }

    def analyze_portfolio_risks(self, holdings: List[str], mode: str = 'hybrid') -> Dict[str, Any]:
        """
        Analyze risks for portfolio holdings

        Args:
            holdings: List of ticker symbols
            mode: LightRAG query mode (default: hybrid)

        Returns:
            Dictionary mapping symbols to risk analysis results
        """
        logger.info(f"Analyzing portfolio risks for {len(holdings)} holdings using {mode} mode")

        results = {
            'analysis_type': 'portfolio_risks',
            'mode': mode,
            'timestamp': datetime.now().isoformat(),
            'holdings': holdings,
            'individual_analyses': {},
            'summary': {}
        }

        successful_analyses = 0

        for symbol in holdings:
            logger.info(f"Analyzing risks for {symbol}")

            # Use risk query template
            query = self.query_templates['risks'].format(symbol=symbol)

            try:
                result = self.ice.query(query, mode=mode)

                if result.get('status') == 'success':
                    results['individual_analyses'][symbol] = {
                        'status': 'success',
                        'risk_analysis': result.get('answer', ''),
                        'query_used': query,
                        'response_time': result.get('response_time', 0)
                    }
                    successful_analyses += 1
                    logger.info(f"✅ Risk analysis completed for {symbol}")
                else:
                    results['individual_analyses'][symbol] = {
                        'status': 'error',
                        'error': result.get('message', 'Unknown error'),
                        'query_used': query
                    }
                    logger.warning(f"❌ Risk analysis failed for {symbol}: {result.get('message')}")

            except Exception as e:
                results['individual_analyses'][symbol] = {
                    'status': 'exception',
                    'error': str(e),
                    'query_used': query
                }
                logger.error(f"❌ Exception during risk analysis for {symbol}: {e}")

        # Generate summary
        results['summary'] = {
            'total_holdings': len(holdings),
            'successful_analyses': successful_analyses,
            'success_rate': (successful_analyses / len(holdings)) * 100 if holdings else 0,
            'failed_analyses': len(holdings) - successful_analyses
        }

        logger.info(f"Portfolio risk analysis completed: {successful_analyses}/{len(holdings)} successful")
        return results

    def analyze_portfolio_opportunities(self, holdings: List[str], mode: str = 'hybrid') -> Dict[str, Any]:
        """
        Analyze opportunities for portfolio holdings

        Args:
            holdings: List of ticker symbols
            mode: LightRAG query mode (default: hybrid)

        Returns:
            Dictionary mapping symbols to opportunity analysis results
        """
        logger.info(f"Analyzing portfolio opportunities for {len(holdings)} holdings using {mode} mode")

        results = {
            'analysis_type': 'portfolio_opportunities',
            'mode': mode,
            'timestamp': datetime.now().isoformat(),
            'holdings': holdings,
            'individual_analyses': {},
            'summary': {}
        }

        successful_analyses = 0

        for symbol in holdings:
            logger.info(f"Analyzing opportunities for {symbol}")

            # Use opportunity query template
            query = self.query_templates['opportunities'].format(symbol=symbol)

            try:
                result = self.ice.query(query, mode=mode)

                if result.get('status') == 'success':
                    results['individual_analyses'][symbol] = {
                        'status': 'success',
                        'opportunity_analysis': result.get('answer', ''),
                        'query_used': query,
                        'response_time': result.get('response_time', 0)
                    }
                    successful_analyses += 1
                    logger.info(f"✅ Opportunity analysis completed for {symbol}")
                else:
                    results['individual_analyses'][symbol] = {
                        'status': 'error',
                        'error': result.get('message', 'Unknown error'),
                        'query_used': query
                    }
                    logger.warning(f"❌ Opportunity analysis failed for {symbol}: {result.get('message')}")

            except Exception as e:
                results['individual_analyses'][symbol] = {
                    'status': 'exception',
                    'error': str(e),
                    'query_used': query
                }
                logger.error(f"❌ Exception during opportunity analysis for {symbol}: {e}")

        # Generate summary
        results['summary'] = {
            'total_holdings': len(holdings),
            'successful_analyses': successful_analyses,
            'success_rate': (successful_analyses / len(holdings)) * 100 if holdings else 0,
            'failed_analyses': len(holdings) - successful_analyses
        }

        logger.info(f"Portfolio opportunity analysis completed: {successful_analyses}/{len(holdings)} successful")
        return results

    def analyze_market_relationships(self, symbols: List[str], mode: str = 'global') -> Dict[str, Any]:
        """
        Analyze relationships and dependencies between symbols

        Args:
            symbols: List of ticker symbols to analyze relationships
            mode: LightRAG query mode (default: global for cross-entity analysis)

        Returns:
            Analysis of inter-company relationships and dependencies
        """
        logger.info(f"Analyzing market relationships for {len(symbols)} symbols using {mode} mode")

        symbols_str = ", ".join(symbols)
        query = self.query_templates['relationships'].format(symbols=symbols_str)

        try:
            result = self.ice.query(query, mode=mode)

            if result.get('status') == 'success':
                analysis = {
                    'analysis_type': 'market_relationships',
                    'status': 'success',
                    'mode': mode,
                    'timestamp': datetime.now().isoformat(),
                    'symbols_analyzed': symbols,
                    'relationship_analysis': result.get('answer', ''),
                    'query_used': query,
                    'response_time': result.get('response_time', 0)
                }
                logger.info(f"✅ Market relationship analysis completed for {len(symbols)} symbols")
                return analysis
            else:
                logger.warning(f"❌ Market relationship analysis failed: {result.get('message')}")
                return {
                    'analysis_type': 'market_relationships',
                    'status': 'error',
                    'mode': mode,
                    'timestamp': datetime.now().isoformat(),
                    'symbols_analyzed': symbols,
                    'error': result.get('message', 'Unknown error'),
                    'query_used': query
                }

        except Exception as e:
            logger.error(f"❌ Exception during market relationship analysis: {e}")
            return {
                'analysis_type': 'market_relationships',
                'status': 'exception',
                'mode': mode,
                'timestamp': datetime.now().isoformat(),
                'symbols_analyzed': symbols,
                'error': str(e),
                'query_used': query
            }

    def analyze_symbol(self, symbol: str, analysis_types: List[str] = None, mode: str = 'hybrid') -> Dict[str, Any]:
        """
        Comprehensive analysis of a single symbol

        Args:
            symbol: Stock ticker symbol
            analysis_types: List of analysis types to perform (default: risks, opportunities, fundamentals)
            mode: LightRAG query mode

        Returns:
            Comprehensive analysis results for the symbol
        """
        if analysis_types is None:
            analysis_types = ['risks', 'opportunities', 'fundamentals']

        logger.info(f"Comprehensive analysis of {symbol} with {len(analysis_types)} analysis types")

        results = {
            'symbol': symbol,
            'analysis_types': analysis_types,
            'mode': mode,
            'timestamp': datetime.now().isoformat(),
            'analyses': {},
            'summary': {}
        }

        successful_analyses = 0

        for analysis_type in analysis_types:
            if analysis_type not in self.query_templates:
                logger.warning(f"Unknown analysis type: {analysis_type}")
                results['analyses'][analysis_type] = {
                    'status': 'error',
                    'error': f'Unknown analysis type: {analysis_type}'
                }
                continue

            logger.info(f"Running {analysis_type} analysis for {symbol}")

            query = self.query_templates[analysis_type].format(symbol=symbol)

            try:
                result = self.ice.query(query, mode=mode)

                if result.get('status') == 'success':
                    results['analyses'][analysis_type] = {
                        'status': 'success',
                        'analysis': result.get('answer', ''),
                        'query_used': query,
                        'response_time': result.get('response_time', 0)
                    }
                    successful_analyses += 1
                    logger.info(f"✅ {analysis_type} analysis completed for {symbol}")
                else:
                    results['analyses'][analysis_type] = {
                        'status': 'error',
                        'error': result.get('message', 'Unknown error'),
                        'query_used': query
                    }
                    logger.warning(f"❌ {analysis_type} analysis failed for {symbol}")

            except Exception as e:
                results['analyses'][analysis_type] = {
                    'status': 'exception',
                    'error': str(e),
                    'query_used': query
                }
                logger.error(f"❌ Exception during {analysis_type} analysis for {symbol}: {e}")

        # Generate summary
        results['summary'] = {
            'total_analyses': len(analysis_types),
            'successful_analyses': successful_analyses,
            'success_rate': (successful_analyses / len(analysis_types)) * 100 if analysis_types else 0,
            'failed_analyses': len(analysis_types) - successful_analyses
        }

        logger.info(f"Comprehensive analysis completed for {symbol}: {successful_analyses}/{len(analysis_types)} successful")
        return results

    def custom_query(self, query: str, mode: str = 'hybrid') -> Dict[str, Any]:
        """
        Execute custom investment-focused query

        Args:
            query: Custom query string
            mode: LightRAG query mode

        Returns:
            Query results with metadata
        """
        logger.info(f"Executing custom query: {query[:50]}{'...' if len(query) > 50 else ''}")

        try:
            result = self.ice.query(query, mode=mode)

            analysis = {
                'query_type': 'custom',
                'mode': mode,
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'status': result.get('status', 'unknown'),
                'response_time': result.get('response_time', 0)
            }

            if result.get('status') == 'success':
                analysis['answer'] = result.get('answer', '')
                logger.info(f"✅ Custom query completed successfully")
            else:
                analysis['error'] = result.get('message', 'Unknown error')
                logger.warning(f"❌ Custom query failed: {result.get('message')}")

            return analysis

        except Exception as e:
            logger.error(f"❌ Exception during custom query: {e}")
            return {
                'query_type': 'custom',
                'mode': mode,
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'status': 'exception',
                'error': str(e)
            }

    def get_available_templates(self) -> Dict[str, str]:
        """
        Get list of available query templates

        Returns:
            Dictionary of template names and their query patterns
        """
        return self.query_templates.copy()

    def test_query_modes(self, test_query: str = "What are the main risks in the semiconductor industry?") -> Dict[str, Any]:
        """
        Test different LightRAG query modes with a sample query

        Args:
            test_query: Query to test with all modes

        Returns:
            Results from all query modes
        """
        modes = ['naive', 'local', 'global', 'hybrid']
        logger.info(f"Testing {len(modes)} query modes with sample query")

        results = {
            'test_query': test_query,
            'timestamp': datetime.now().isoformat(),
            'mode_results': {},
            'summary': {}
        }

        successful_modes = 0

        for mode in modes:
            logger.info(f"Testing {mode} mode")

            try:
                result = self.ice.query(test_query, mode=mode)

                if result.get('status') == 'success':
                    results['mode_results'][mode] = {
                        'status': 'success',
                        'answer': result.get('answer', ''),
                        'response_time': result.get('response_time', 0),
                        'answer_length': len(result.get('answer', ''))
                    }
                    successful_modes += 1
                    logger.info(f"✅ {mode} mode test successful")
                else:
                    results['mode_results'][mode] = {
                        'status': 'error',
                        'error': result.get('message', 'Unknown error')
                    }
                    logger.warning(f"❌ {mode} mode test failed")

            except Exception as e:
                results['mode_results'][mode] = {
                    'status': 'exception',
                    'error': str(e)
                }
                logger.error(f"❌ Exception testing {mode} mode: {e}")

        # Generate summary
        results['summary'] = {
            'total_modes': len(modes),
            'successful_modes': successful_modes,
            'success_rate': (successful_modes / len(modes)) * 100,
            'failed_modes': len(modes) - successful_modes,
            'best_mode': None
        }

        # Identify best performing mode (shortest response time among successful modes)
        successful_results = {mode: data for mode, data in results['mode_results'].items()
                            if data.get('status') == 'success'}

        if successful_results:
            best_mode = min(successful_results.keys(),
                          key=lambda mode: successful_results[mode].get('response_time', float('inf')))
            results['summary']['best_mode'] = best_mode

        logger.info(f"Query mode testing completed: {successful_modes}/{len(modes)} modes successful")
        return results


# Convenience functions
def create_query_engine(ice_core) -> QueryEngine:
    """
    Create and initialize query engine

    Args:
        ice_core: ICECore instance

    Returns:
        Initialized QueryEngine instance
    """
    engine = QueryEngine(ice_core)
    logger.info("✅ Query Engine created successfully")
    return engine


def test_query_engine(ice_core, test_symbol: str = "AAPL") -> bool:
    """
    Test query engine functionality

    Args:
        ice_core: ICECore instance
        test_symbol: Symbol to test with

    Returns:
        True if test passes, False otherwise
    """
    try:
        logger.info(f"🧪 Testing query engine with {test_symbol}...")

        engine = create_query_engine(ice_core)

        # Test symbol analysis
        result = engine.analyze_symbol(test_symbol, analysis_types=['risks'], mode='hybrid')

        if result['summary']['success_rate'] > 0:
            logger.info("✅ Query engine test passed")
            return True
        else:
            logger.warning("⚠️ Query engine test completed but no successful analyses")
            return False

    except Exception as e:
        logger.error(f"❌ Query engine test failed: {e}")
        return False


if __name__ == "__main__":
    # Demo usage (requires ICE core to be initialized)
    print("🚀 Query Engine Demo")

    try:
        from ice_core import create_ice_core

        # Create ICE core
        core = create_ice_core()

        if not core.is_ready():
            print("❌ ICE core not ready - cannot demo query engine")
            exit(1)

        # Create query engine
        engine = create_query_engine(core)

        # Test query engine
        if test_query_engine(core):
            print("✅ Query engine is working correctly")
        else:
            print("❌ Query engine test failed")

        # Show available templates
        templates = engine.get_available_templates()
        print(f"\n📋 Available Analysis Templates ({len(templates)}):")
        for name, template in templates.items():
            print(f"  • {name}: {template[:60]}{'...' if len(template) > 60 else ''}")

    except Exception as e:
        print(f"❌ Demo failed: {e}")