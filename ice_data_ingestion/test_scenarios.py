# ice_data_ingestion/test_scenarios.py
"""
Comprehensive Test Scenarios for ICE Data Ingestion
Defines test cases covering edge cases, market conditions, and data variations
Ensures thorough validation of all data sources across different scenarios
Relevant files: ice_data_sources_demo.ipynb, financial_news_connectors.py, sec_edgar_connector.py
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import random
import pytz

logger = logging.getLogger(__name__)


class MarketCondition(Enum):
    """Market trading conditions"""
    PRE_MARKET = "pre_market"  # 4:00 AM - 9:30 AM ET
    REGULAR_HOURS = "regular_hours"  # 9:30 AM - 4:00 PM ET
    AFTER_HOURS = "after_hours"  # 4:00 PM - 8:00 PM ET
    CLOSED = "closed"  # Weekends and holidays
    HOLIDAY = "holiday"  # Market holidays
    HALT = "halt"  # Trading halt
    VOLATILE = "volatile"  # High volatility period


class TickerType(Enum):
    """Types of ticker symbols for testing"""
    US_LARGE_CAP = "us_large_cap"
    US_MID_CAP = "us_mid_cap"
    US_SMALL_CAP = "us_small_cap"
    US_PENNY_STOCK = "us_penny_stock"
    INTERNATIONAL = "international"
    ADR = "adr"  # American Depositary Receipt
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    CRYPTO = "crypto"
    FOREX = "forex"
    COMMODITY = "commodity"
    INDEX = "index"
    OPTION = "option"
    DELISTED = "delisted"
    INVALID = "invalid"
    SPECIAL_CHAR = "special_char"  # Tickers with special characters
    IPO_RECENT = "ipo_recent"  # Recently IPO'd
    SPAC = "spac"


@dataclass
class TestScenario:
    """Individual test scenario configuration"""
    name: str
    description: str
    ticker: str
    ticker_type: TickerType
    market_condition: MarketCondition
    test_data: Dict[str, Any] = field(default_factory=dict)
    expected_behavior: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    priority: int = 1  # 1 = Critical, 2 = Important, 3 = Nice to have


@dataclass
class TestSuite:
    """Collection of test scenarios"""
    name: str
    scenarios: List[TestScenario]
    setup: Optional[Callable] = None
    teardown: Optional[Callable] = None
    parallel: bool = False  # Whether scenarios can run in parallel


class TestScenarioGenerator:
    """
    Generates comprehensive test scenarios for data ingestion validation
    """

    def __init__(self):
        """Initialize test scenario generator"""
        # US Market holidays 2024-2025
        self.market_holidays = [
            datetime(2024, 1, 1),   # New Year's Day
            datetime(2024, 1, 15),  # MLK Day
            datetime(2024, 2, 19),  # Presidents Day
            datetime(2024, 3, 29),  # Good Friday
            datetime(2024, 5, 27),  # Memorial Day
            datetime(2024, 6, 19),  # Juneteenth
            datetime(2024, 7, 4),   # Independence Day
            datetime(2024, 9, 2),   # Labor Day
            datetime(2024, 11, 28), # Thanksgiving
            datetime(2024, 12, 25), # Christmas
        ]

        # Ticker examples by type
        self.ticker_examples = {
            TickerType.US_LARGE_CAP: ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"],
            TickerType.US_MID_CAP: ["DOCU", "SNAP", "ROKU", "SQ", "PINS", "ZM", "DDOG"],
            TickerType.US_SMALL_CAP: ["BBBY", "CLOV", "WISH", "RIDE", "NKLA"],
            TickerType.US_PENNY_STOCK: ["SNDL", "NAKD", "GNUS", "SHIP"],
            TickerType.INTERNATIONAL: ["TSM", "BABA", "NVO", "ASML", "SAP", "TM", "SONY"],
            TickerType.ADR: ["NIO", "BIDU", "PDD", "JD", "LI", "XPEV"],
            TickerType.ETF: ["SPY", "QQQ", "IWM", "DIA", "VOO", "VTI", "ARKK"],
            TickerType.MUTUAL_FUND: ["VFIAX", "FXAIX", "VTSAX", "FZROX"],
            # Crypto removed: not part of ICE workflow
            TickerType.FOREX: ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X"],
            TickerType.COMMODITY: ["GC=F", "CL=F", "SI=F", "NG=F"],  # Gold, Oil, Silver, Natural Gas
            TickerType.INDEX: ["^GSPC", "^DJI", "^IXIC", "^RUT", "^VIX"],
            TickerType.OPTION: ["AAPL250117C00200000", "SPY240119P00450000"],
            TickerType.DELISTED: ["LEHM", "ENRNQ", "WAMU", "BRNAQ"],  # Lehman, Enron, WaMu, Barneys
            TickerType.INVALID: ["INVALID", "FAKE123", "NOTREAL", "", "   ", "NULL", None],
            TickerType.SPECIAL_CHAR: ["BRK.B", "BF.B", "GOOGL", "META"],  # Berkshire B, Brown-Forman B
            TickerType.IPO_RECENT: ["RDDT", "ARM", "KVUE", "BIRK"],  # Recent IPOs 2024
            TickerType.SPAC: ["DWAC", "LCID", "NKLA", "SPCE"],
        }

        # Expected data availability by source and ticker type
        self.data_availability = {
            "yfinance": {
                TickerType.US_LARGE_CAP: True,
                TickerType.US_MID_CAP: True,
                TickerType.US_SMALL_CAP: True,
                TickerType.US_PENNY_STOCK: True,
                TickerType.INTERNATIONAL: True,
                TickerType.ADR: True,
                TickerType.ETF: True,
                TickerType.CRYPTO: True,
                TickerType.FOREX: True,
                TickerType.COMMODITY: True,
                TickerType.INDEX: True,
                TickerType.DELISTED: False,
                TickerType.INVALID: False,
            },
            "sec_edgar": {
                TickerType.US_LARGE_CAP: True,
                TickerType.US_MID_CAP: True,
                TickerType.US_SMALL_CAP: True,
                TickerType.US_PENNY_STOCK: True,
                TickerType.INTERNATIONAL: False,  # Foreign companies may not file
                TickerType.ADR: True,  # ADRs file with SEC
                TickerType.ETF: True,
                TickerType.CRYPTO: False,
                TickerType.DELISTED: True,  # Historical filings available
                TickerType.INVALID: False,
            },
            "news": {
                TickerType.US_LARGE_CAP: True,
                TickerType.US_MID_CAP: True,
                TickerType.US_SMALL_CAP: "limited",
                TickerType.US_PENNY_STOCK: "limited",
                TickerType.INTERNATIONAL: True,
                TickerType.CRYPTO: True,
                TickerType.DELISTED: False,
                TickerType.INVALID: False,
            }
        }

    def get_market_condition(self, dt: Optional[datetime] = None) -> MarketCondition:
        """
        Determine market condition for given datetime

        Args:
            dt: Datetime to check (defaults to now)

        Returns:
            Current market condition
        """
        if dt is None:
            dt = datetime.now(pytz.timezone('US/Eastern'))
        elif dt.tzinfo is None:
            dt = pytz.timezone('US/Eastern').localize(dt)

        # Check if holiday
        if dt.date() in [h.date() for h in self.market_holidays]:
            return MarketCondition.HOLIDAY

        # Check if weekend
        if dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return MarketCondition.CLOSED

        # Check time of day
        hour = dt.hour
        minute = dt.minute
        time_decimal = hour + minute / 60

        if 4 <= time_decimal < 9.5:
            return MarketCondition.PRE_MARKET
        elif 9.5 <= time_decimal < 16:
            return MarketCondition.REGULAR_HOURS
        elif 16 <= time_decimal < 20:
            return MarketCondition.AFTER_HOURS
        else:
            return MarketCondition.CLOSED

    def generate_core_scenarios(self) -> TestSuite:
        """Generate core test scenarios that must pass"""
        scenarios = []

        # Critical US large cap stocks
        for ticker in ["AAPL", "MSFT", "GOOGL"]:
            scenarios.append(TestScenario(
                name=f"core_{ticker.lower()}_regular",
                description=f"Test {ticker} during regular trading hours",
                ticker=ticker,
                ticker_type=TickerType.US_LARGE_CAP,
                market_condition=MarketCondition.REGULAR_HOURS,
                expected_behavior={
                    "yfinance": {"has_data": True, "has_price": True},
                    "sec_edgar": {"has_filings": True, "min_filings": 10},
                    "news": {"has_articles": True, "min_articles": 5}
                },
                tags=["core", "critical", "us_equity"],
                priority=1
            ))

        # Major ETFs
        scenarios.append(TestScenario(
            name="core_spy_etf",
            description="Test SPY ETF data retrieval",
            ticker="SPY",
            ticker_type=TickerType.ETF,
            market_condition=MarketCondition.REGULAR_HOURS,
            expected_behavior={
                "yfinance": {"has_data": True, "has_volume": True},
                "news": {"has_articles": True}
            },
            tags=["core", "etf"],
            priority=1
        ))

        # International ADR
        scenarios.append(TestScenario(
            name="core_baba_adr",
            description="Test Alibaba ADR data",
            ticker="BABA",
            ticker_type=TickerType.ADR,
            market_condition=MarketCondition.REGULAR_HOURS,
            expected_behavior={
                "yfinance": {"has_data": True},
                "sec_edgar": {"has_filings": True}
            },
            tags=["core", "international", "adr"],
            priority=1
        ))

        return TestSuite(
            name="Core Scenarios",
            scenarios=scenarios,
            parallel=True
        )

    def generate_edge_case_scenarios(self) -> TestSuite:
        """Generate edge case test scenarios"""
        scenarios = []

        # Invalid tickers
        for invalid in ["INVALID", "", None, "   ", "123456"]:
            scenarios.append(TestScenario(
                name=f"edge_invalid_{str(invalid).replace(' ', 'space')}",
                description=f"Test invalid ticker: {invalid}",
                ticker=invalid if invalid is not None else "NULL",
                ticker_type=TickerType.INVALID,
                market_condition=MarketCondition.REGULAR_HOURS,
                expected_behavior={
                    "yfinance": {"has_data": False, "error_expected": True},
                    "sec_edgar": {"has_filings": False},
                    "news": {"has_articles": False}
                },
                tags=["edge_case", "invalid"],
                priority=2
            ))

        # Delisted companies
        scenarios.append(TestScenario(
            name="edge_delisted_lehman",
            description="Test delisted company (Lehman Brothers)",
            ticker="LEHMQ",
            ticker_type=TickerType.DELISTED,
            market_condition=MarketCondition.REGULAR_HOURS,
            expected_behavior={
                "yfinance": {"has_data": False},
                "sec_edgar": {"has_filings": True, "all_historical": True},
                "news": {"has_articles": False}
            },
            tags=["edge_case", "delisted"],
            priority=2
        ))

        # Special character tickers
        scenarios.append(TestScenario(
            name="edge_special_brk_b",
            description="Test ticker with dot (BRK.B)",
            ticker="BRK.B",
            ticker_type=TickerType.SPECIAL_CHAR,
            market_condition=MarketCondition.REGULAR_HOURS,
            expected_behavior={
                "yfinance": {"has_data": True, "ticker_normalization": True},
                "sec_edgar": {"has_filings": True, "parent_company": "Berkshire Hathaway"}
            },
            tags=["edge_case", "special_char"],
            priority=2
        ))

        # Penny stocks
        scenarios.append(TestScenario(
            name="edge_penny_stock",
            description="Test penny stock with limited data",
            ticker="SNDL",
            ticker_type=TickerType.US_PENNY_STOCK,
            market_condition=MarketCondition.REGULAR_HOURS,
            expected_behavior={
                "yfinance": {"has_data": True, "low_price": True},
                "news": {"has_articles": "limited"}
            },
            tags=["edge_case", "penny_stock"],
            priority=3
        ))

        # Crypto ticker testing removed as crypto is not part of ICE workflow

        return TestSuite(
            name="Edge Case Scenarios",
            scenarios=scenarios,
            parallel=True
        )

    def generate_market_condition_scenarios(self) -> TestSuite:
        """Generate scenarios for different market conditions"""
        scenarios = []
        test_ticker = "AAPL"

        # Pre-market test
        scenarios.append(TestScenario(
            name="market_pre_market",
            description="Test data retrieval during pre-market hours",
            ticker=test_ticker,
            ticker_type=TickerType.US_LARGE_CAP,
            market_condition=MarketCondition.PRE_MARKET,
            test_data={"test_time": "07:00 ET"},
            expected_behavior={
                "yfinance": {"has_pre_market": True, "limited_volume": True},
                "news": {"has_articles": True}
            },
            tags=["market_condition", "pre_market"],
            priority=2
        ))

        # After-hours test
        scenarios.append(TestScenario(
            name="market_after_hours",
            description="Test data retrieval during after-hours trading",
            ticker=test_ticker,
            ticker_type=TickerType.US_LARGE_CAP,
            market_condition=MarketCondition.AFTER_HOURS,
            test_data={"test_time": "17:30 ET"},
            expected_behavior={
                "yfinance": {"has_after_hours": True, "limited_volume": True}
            },
            tags=["market_condition", "after_hours"],
            priority=2
        ))

        # Weekend test
        scenarios.append(TestScenario(
            name="market_weekend",
            description="Test data retrieval on weekend",
            ticker=test_ticker,
            ticker_type=TickerType.US_LARGE_CAP,
            market_condition=MarketCondition.CLOSED,
            test_data={"test_day": "Saturday"},
            expected_behavior={
                "yfinance": {"has_data": True, "last_close_available": True},
                "sec_edgar": {"has_filings": True},
                "news": {"has_articles": "possible"}
            },
            tags=["market_condition", "weekend"],
            priority=3
        ))

        # Holiday test
        scenarios.append(TestScenario(
            name="market_holiday",
            description="Test data retrieval on market holiday",
            ticker=test_ticker,
            ticker_type=TickerType.US_LARGE_CAP,
            market_condition=MarketCondition.HOLIDAY,
            test_data={"test_date": "2024-12-25"},  # Christmas
            expected_behavior={
                "yfinance": {"has_data": True, "no_trading_volume": True},
                "news": {"has_articles": "limited"}
            },
            tags=["market_condition", "holiday"],
            priority=3
        ))

        # High volatility test
        scenarios.append(TestScenario(
            name="market_volatile",
            description="Test during high volatility period",
            ticker="VIX",
            ticker_type=TickerType.INDEX,
            market_condition=MarketCondition.VOLATILE,
            test_data={"vix_level": ">30"},
            expected_behavior={
                "yfinance": {"has_data": True, "high_volume": True},
                "news": {"has_articles": True, "high_frequency": True}
            },
            tags=["market_condition", "volatility"],
            priority=2
        ))

        return TestSuite(
            name="Market Condition Scenarios",
            scenarios=scenarios,
            parallel=False  # Time-sensitive tests should run sequentially
        )

    def generate_corporate_action_scenarios(self) -> TestSuite:
        """Generate scenarios around corporate actions"""
        scenarios = []

        # Stock split scenario
        scenarios.append(TestScenario(
            name="corp_stock_split",
            description="Test data around stock split date",
            ticker="NVDA",  # Had recent splits
            ticker_type=TickerType.US_LARGE_CAP,
            market_condition=MarketCondition.REGULAR_HOURS,
            test_data={
                "action": "stock_split",
                "split_ratio": "4:1",
                "test_date": "around_split_date"
            },
            expected_behavior={
                "yfinance": {"has_split_info": True, "adjusted_prices": True},
                "sec_edgar": {"has_8k_filing": True},
                "news": {"has_articles": True, "mentions_split": True}
            },
            tags=["corporate_action", "stock_split"],
            priority=2
        ))

        # Dividend ex-date scenario
        scenarios.append(TestScenario(
            name="corp_dividend_ex",
            description="Test data on dividend ex-date",
            ticker="JNJ",  # Consistent dividend payer
            ticker_type=TickerType.US_LARGE_CAP,
            market_condition=MarketCondition.REGULAR_HOURS,
            test_data={
                "action": "dividend",
                "test_date": "ex_dividend_date"
            },
            expected_behavior={
                "yfinance": {"has_dividend_info": True, "price_adjustment": True}
            },
            tags=["corporate_action", "dividend"],
            priority=3
        ))

        # Earnings release scenario
        scenarios.append(TestScenario(
            name="corp_earnings",
            description="Test data around earnings release",
            ticker="AAPL",
            ticker_type=TickerType.US_LARGE_CAP,
            market_condition=MarketCondition.AFTER_HOURS,
            test_data={
                "action": "earnings_release",
                "test_time": "after_close"
            },
            expected_behavior={
                "yfinance": {"high_volume": True, "price_movement": True},
                "sec_edgar": {"has_10q_or_10k": True},
                "news": {"has_articles": True, "high_frequency": True}
            },
            tags=["corporate_action", "earnings"],
            priority=1
        ))

        # IPO scenario
        scenarios.append(TestScenario(
            name="corp_ipo_recent",
            description="Test recently IPO'd company",
            ticker="RDDT",  # Reddit IPO 2024
            ticker_type=TickerType.IPO_RECENT,
            market_condition=MarketCondition.REGULAR_HOURS,
            test_data={
                "action": "ipo",
                "ipo_date": "2024-03-21"
            },
            expected_behavior={
                "yfinance": {"limited_history": True},
                "sec_edgar": {"has_s1_filing": True},
                "news": {"has_articles": True, "ipo_coverage": True}
            },
            tags=["corporate_action", "ipo"],
            priority=2
        ))

        return TestSuite(
            name="Corporate Action Scenarios",
            scenarios=scenarios,
            parallel=True
        )

    def generate_data_quality_scenarios(self) -> TestSuite:
        """Generate scenarios to test data quality and consistency"""
        scenarios = []

        # Data completeness test
        scenarios.append(TestScenario(
            name="quality_completeness",
            description="Test data completeness for major stock",
            ticker="MSFT",
            ticker_type=TickerType.US_LARGE_CAP,
            market_condition=MarketCondition.REGULAR_HOURS,
            test_data={
                "required_fields": ["open", "high", "low", "close", "volume", "market_cap"]
            },
            expected_behavior={
                "yfinance": {"all_fields_present": True, "no_nulls": True},
                "sec_edgar": {"recent_filing": True}
            },
            tags=["data_quality", "completeness"],
            priority=1
        ))

        # Data freshness test
        scenarios.append(TestScenario(
            name="quality_freshness",
            description="Test data freshness and timeliness",
            ticker="GOOGL",
            ticker_type=TickerType.US_LARGE_CAP,
            market_condition=MarketCondition.REGULAR_HOURS,
            test_data={
                "max_delay_minutes": 15
            },
            expected_behavior={
                "yfinance": {"recent_timestamp": True},
                "news": {"recent_articles": True}
            },
            tags=["data_quality", "freshness"],
            priority=1
        ))

        # Cross-source consistency
        scenarios.append(TestScenario(
            name="quality_consistency",
            description="Test price consistency across sources",
            ticker="AMZN",
            ticker_type=TickerType.US_LARGE_CAP,
            market_condition=MarketCondition.REGULAR_HOURS,
            test_data={
                "tolerance_percent": 0.1  # 0.1% price difference tolerance
            },
            expected_behavior={
                "cross_validation": True,
                "price_match": True
            },
            tags=["data_quality", "consistency"],
            priority=2
        ))

        return TestSuite(
            name="Data Quality Scenarios",
            scenarios=scenarios,
            parallel=True
        )

    def generate_all_scenarios(self) -> Dict[str, TestSuite]:
        """Generate all test scenario suites"""
        return {
            "core": self.generate_core_scenarios(),
            "edge_cases": self.generate_edge_case_scenarios(),
            "market_conditions": self.generate_market_condition_scenarios(),
            "corporate_actions": self.generate_corporate_action_scenarios(),
            "data_quality": self.generate_data_quality_scenarios()
        }

    def get_priority_scenarios(self, priority: int = 1) -> List[TestScenario]:
        """Get all scenarios of specified priority or higher"""
        all_suites = self.generate_all_scenarios()
        priority_scenarios = []

        for suite in all_suites.values():
            for scenario in suite.scenarios:
                if scenario.priority <= priority:
                    priority_scenarios.append(scenario)

        return priority_scenarios

    def get_scenarios_by_tag(self, tag: str) -> List[TestScenario]:
        """Get all scenarios with specified tag"""
        all_suites = self.generate_all_scenarios()
        tagged_scenarios = []

        for suite in all_suites.values():
            for scenario in suite.scenarios:
                if tag in scenario.tags:
                    tagged_scenarios.append(scenario)

        return tagged_scenarios


# Convenience functions
def get_test_scenarios(suite_name: Optional[str] = None) -> Union[Dict[str, TestSuite], TestSuite]:
    """
    Get test scenarios

    Args:
        suite_name: Specific suite name or None for all

    Returns:
        Test suite(s)
    """
    generator = TestScenarioGenerator()

    if suite_name:
        all_suites = generator.generate_all_scenarios()
        return all_suites.get(suite_name)
    else:
        return generator.generate_all_scenarios()


def get_critical_scenarios() -> List[TestScenario]:
    """Get only critical (priority 1) scenarios"""
    generator = TestScenarioGenerator()
    return generator.get_priority_scenarios(priority=1)