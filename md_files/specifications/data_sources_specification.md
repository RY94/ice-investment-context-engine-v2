# ICE Data Sources Specification
## Comprehensive Data Source Integration Guide

**Document Type**: Technical Data Source Specification  
**Author**: Senior AI Engineering Team  
**Project**: Investment Context Engine (ICE) Data Sources  
**Version**: 1.0  
**Date**: August 2025  

---

## Table of Contents

1. [Data Source Overview](#1-data-source-overview)
2. [Tier 1 Essential Sources](#2-tier-1-essential-sources)
3. [Tier 2 Enhancement Sources](#3-tier-2-enhancement-sources)
4. [Tier 3 Alternative Sources](#4-tier-3-alternative-sources)
5. [API Integration Specifications](#5-api-integration-specifications)
6. [Data Schemas & Models](#6-data-schemas--models)
7. [Quality & Validation Rules](#7-quality--validation-rules)
8. [Cost & Usage Management](#8-cost--usage-management)

---

## 1. Data Source Overview

### 1.1 Data Source Strategy

The Investment Context Engine requires diverse, high-quality financial data to power its graph-based reasoning capabilities. Our data strategy prioritizes:

1. **Coverage**: Comprehensive information across news, financial metrics, regulatory filings, and internal documents
2. **Timeliness**: Real-time to 15-minute delays for time-sensitive information  
3. **Quality**: Multiple source validation and cross-referencing
4. **Cost-Effectiveness**: Balanced approach to premium vs. free data sources
5. **Compliance**: Adherence to financial data usage regulations

### 1.2 Data Source Classification

```python
DATA_SOURCE_TIERS = {
    'tier_1_essential': {
        'priority': 'Critical',
        'implementation_timeline': 'Weeks 1-4',
        'budget_allocation': '70%',
        'sources': ['NewsAPI', 'Benzinga', 'SEC EDGAR', 'Enhanced Financial APIs']
    },
    'tier_2_enhancement': {
        'priority': 'Important', 
        'implementation_timeline': 'Weeks 5-8',
        'budget_allocation': '20%',
        'sources': ['Social Sentiment', 'Economic Data', 'Alternative Financial']
    },
    'tier_3_alternative': {
        'priority': 'Future Enhancement',
        'implementation_timeline': 'Post-MVP',
        'budget_allocation': '10%',
        'sources': ['Satellite Data', 'Patent Data', 'Supply Chain Intelligence']
    }
}
```

---

## 2. Tier 1 Essential Sources

### 2.1 News Intelligence Sources

#### 2.1.1 NewsAPI.org

**Purpose**: Primary financial news aggregation for market sentiment and breaking news analysis

**Technical Specifications**:
```python
NEWSAPI_CONFIG = {
    'base_url': 'https://newsapi.org/v2/',
    'endpoints': {
        'everything': 'everything',
        'top_headlines': 'top-headlines',
        'sources': 'sources'
    },
    'authentication': {
        'type': 'api_key',
        'header': 'X-API-Key'
    },
    'rate_limits': {
        'developer': '1000 requests/day',
        'business': '100,000 requests/day', 
        'enterprise': '500,000 requests/day'
    },
    'pricing': {
        'developer': '$0/month (limited)',
        'business': '$449/month',
        'enterprise': '$1,999/month'
    }
}
```

**Data Coverage**:
- **Sources**: 80,000+ news sources globally
- **Languages**: 14 languages (focus on English for ICE)
- **Update Frequency**: Real-time to 15 minutes
- **Historical Data**: Up to 1 month for free tier, unlimited for paid

**Sample Query for Financial News**:
```python
newsapi_query = {
    'q': '(stock OR market OR earnings OR SEC OR filing OR merger OR acquisition) AND (NASDAQ OR NYSE OR S&P)',
    'language': 'en',
    'sortBy': 'publishedAt',
    'domains': 'reuters.com,bloomberg.com,cnbc.com,wsj.com,ft.com',
    'from': '2025-08-30T00:00:00Z',
    'pageSize': 100
}
```

**Response Schema**:
```python
@dataclass
class NewsAPIArticle:
    title: str
    description: str
    url: str
    urlToImage: str
    publishedAt: datetime
    source: Dict[str, str]  # {'id': 'reuters', 'name': 'Reuters'}
    author: Optional[str]
    content: Optional[str]  # First 200 characters
    
    # ICE-specific enhancements
    extracted_entities: Dict[str, List[str]] = field(default_factory=dict)
    sentiment_score: Optional[float] = None
    investment_relevance: Optional[float] = None
```

#### 2.1.2 Benzinga News API

**Purpose**: Premium financial news with higher quality and faster delivery than general news sources

**Technical Specifications**:
```python
BENZINGA_CONFIG = {
    'base_url': 'https://api.benzinga.com/api/v2/',
    'endpoints': {
        'news': 'news',
        'calendar': 'calendar/earnings',
        'ratings': 'calendar/ratings',
        'signals': 'signals/movers'
    },
    'authentication': {
        'type': 'token',
        'parameter': 'token'
    },
    'rate_limits': {
        'basic': '120 requests/minute',
        'pro': '300 requests/minute'
    },
    'pricing': {
        'basic': '$99/month',
        'pro': '$299/month',
        'enterprise': 'Custom pricing'
    }
}
```

**Data Coverage**:
- **Focus**: US financial markets with some international coverage
- **Quality**: Professionally curated financial news
- **Speed**: <2 minute latency for breaking financial news
- **Specialties**: Earnings calendars, analyst ratings, market movers

**Sample Query**:
```python
benzinga_query = {
    'tickers': 'AAPL,GOOGL,MSFT,AMZN,NVDA',
    'channels': 'Analyst Ratings,Earnings,FDA,M&A',
    'date_from': '2025-08-30',
    'limit': 50,
    'display_output': 'full'
}
```

**Response Enhancement for ICE**:
```python
@dataclass  
class BenzingaNewsArticle:
    id: int
    title: str
    content: str
    url: str
    image_url: str
    published: datetime
    updated: datetime
    channels: List[str]
    stocks: List[str]  # Ticker symbols mentioned
    tags: List[str]
    
    # ICE processing additions
    entity_confidence: Dict[str, float] = field(default_factory=dict)
    market_impact_score: Optional[float] = None
    urgency_level: Optional[str] = None
```

### 2.2 Financial Data Sources

#### 2.2.1 Enhanced yfinance Integration

**Purpose**: Expand existing earnings fetcher with comprehensive financial metrics

**Current State**: Basic earnings data extraction
**Enhancement Plan**: Multi-metric financial analysis with validation

```python
YFINANCE_ENHANCED_CONFIG = {
    'data_types': {
        'price_data': {
            'fields': ['open', 'high', 'low', 'close', 'volume', 'dividends', 'stock_splits'],
            'frequencies': ['1d', '1wk', '1mo'],
            'max_period': '5y'
        },
        'financial_statements': {
            'income_statement': ['quarterly', 'annual'],
            'balance_sheet': ['quarterly', 'annual'], 
            'cash_flow': ['quarterly', 'annual']
        },
        'company_info': {
            'fields': ['marketCap', 'enterpriseValue', 'peRatio', 'pegRatio', 'bookValue', 
                      'priceToBook', 'earningsGrowth', 'revenueGrowth', 'operatingMargins',
                      'profitMargins', 'grossMargins', 'sector', 'industry']
        },
        'analyst_data': {
            'recommendations': True,
            'earnings_estimates': True,
            'revenue_estimates': True,
            'earnings_history': True
        }
    },
    'validation_rules': {
        'price_data': {
            'min_price': 0.01,
            'max_price': 100000,
            'volume_consistency': True
        },
        'financial_ratios': {
            'pe_ratio_range': [0, 1000],
            'profit_margin_range': [-1, 1],
            'debt_ratio_range': [0, 10]
        }
    }
}
```

#### 2.2.2 Financial Modeling Prep API

**Purpose**: Professional-grade financial data with extensive coverage and real-time updates

**Technical Specifications**:
```python
FMP_CONFIG = {
    'base_url': 'https://financialmodelingprep.com/api/v3/',
    'endpoints': {
        'company_profile': 'profile/{symbol}',
        'financial_statements': 'financials/income-statement/{symbol}',
        'key_metrics': 'key-metrics/{symbol}',
        'ratios': 'ratios/{symbol}',
        'market_cap': 'market-capitalization/{symbol}',
        'real_time_price': 'quote/{symbol}',
        'news': 'stock_news',
        'sec_filings': 'sec_filings/{symbol}'
    },
    'authentication': {
        'type': 'api_key',
        'parameter': 'apikey'
    },
    'rate_limits': {
        'free': '250 requests/day',
        'starter': '10,000 requests/month - $29',
        'professional': '100,000 requests/month - $99',
        'enterprise': 'Unlimited - $399'
    }
}
```

**Data Coverage**:
- **Symbols**: 15,000+ US stocks, ETFs, mutual funds, commodities, forex
- **Historical Data**: 30+ years of financial statements
- **Real-time Data**: <1 minute delay for market data
- **International**: Coverage of major global exchanges

**Enhanced Data Model**:
```python
@dataclass
class FMPFinancialData:
    symbol: str
    company_name: str
    last_updated: datetime
    
    # Price data
    current_price: float
    price_change: float
    price_change_percent: float
    day_high: float
    day_low: float
    volume: int
    
    # Valuation metrics
    market_cap: int
    pe_ratio: Optional[float]
    peg_ratio: Optional[float]
    price_to_book: Optional[float]
    price_to_sales: Optional[float]
    enterprise_value: Optional[int]
    
    # Financial health
    debt_to_equity: Optional[float]
    current_ratio: Optional[float]
    quick_ratio: Optional[float]
    operating_margin: Optional[float]
    profit_margin: Optional[float]
    
    # Growth metrics
    revenue_growth: Optional[float]
    earnings_growth: Optional[float]
    eps_growth: Optional[float]
    
    # ICE-specific enhancements
    data_quality_score: float = 0.0
    source_confidence: float = 0.0
    last_validation: Optional[datetime] = None
```

#### 2.2.3 Alpha Vantage API

**Purpose**: Real-time market data and technical indicators for comprehensive market analysis

**Technical Specifications**:
```python
ALPHA_VANTAGE_CONFIG = {
    'base_url': 'https://www.alphavantage.co/query',
    'functions': {
        'intraday': 'TIME_SERIES_INTRADAY',
        'daily': 'TIME_SERIES_DAILY',
        'weekly': 'TIME_SERIES_WEEKLY', 
        'monthly': 'TIME_SERIES_MONTHLY',
        'quote': 'GLOBAL_QUOTE',
        'search': 'SYMBOL_SEARCH',
        'company_overview': 'OVERVIEW',
        'income_statement': 'INCOME_STATEMENT',
        'earnings': 'EARNINGS',
        'news_sentiment': 'NEWS_SENTIMENT'
    },
    'rate_limits': {
        'free': '5 requests/minute, 500 requests/day',
        'premium': '75 requests/minute - $49.99/month'
    }
}
```

### 2.3 Regulatory Data Sources

#### 2.3.1 SEC EDGAR Database

**Purpose**: Authoritative source for all US public company regulatory filings

**Technical Specifications**:
```python
SEC_EDGAR_CONFIG = {
    'base_url': 'https://www.sec.gov/Archives/edgar/data/',
    'api_endpoints': {
        'company_tickers': 'https://www.sec.gov/files/company_tickers.json',
        'submissions': 'https://data.sec.gov/submissions/CIK{cik_padded}.json',
        'xbrl_companyfacts': 'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json',
        'filing_search': 'https://efts.sec.gov/LATEST/search-index'
    },
    'rate_limits': {
        'requests_per_second': 10,
        'user_agent_required': True
    },
    'filing_types': {
        '10-K': 'Annual Report',
        '10-Q': 'Quarterly Report',
        '8-K': 'Current Report',
        '4': 'Insider Trading',
        'DEF 14A': 'Proxy Statement',
        '13F-HR': 'Institutional Holdings'
    }
}
```

**Data Processing Pipeline**:
```python
@dataclass
class SECFiling:
    # Filing identification
    accession_number: str
    filing_type: str
    company_cik: str
    company_name: str
    ticker: Optional[str]
    
    # Filing details
    filing_date: datetime
    acceptance_datetime: datetime
    period_of_report: Optional[datetime]
    document_count: int
    
    # Document URLs
    filing_url: str
    interactive_data_url: Optional[str]
    xbrl_url: Optional[str]
    
    # Processed content
    extracted_text: Optional[str] = None
    financial_data: Optional[Dict[str, Any]] = None
    risk_factors: List[str] = field(default_factory=list)
    management_discussion: Optional[str] = None
    
    # Processing metadata
    processed_at: Optional[datetime] = None
    processing_confidence: float = 0.0
    extraction_errors: List[str] = field(default_factory=list)
```

#### 2.3.2 XBRL Data Processing

**Purpose**: Extract structured financial data from XBRL-formatted SEC filings

**Processing Architecture**:
```python
class XBRLProcessor:
    """Process XBRL financial data from SEC filings"""
    
    STANDARD_CONCEPTS = {
        # Income Statement
        'revenues': ['us-gaap:Revenues', 'us-gaap:SalesRevenueNet'],
        'cost_of_revenue': ['us-gaap:CostOfRevenue', 'us-gaap:CostOfGoodsAndServicesSold'],
        'gross_profit': ['us-gaap:GrossProfit'],
        'operating_expenses': ['us-gaap:OperatingExpenses'],
        'operating_income': ['us-gaap:OperatingIncomeLoss'],
        'net_income': ['us-gaap:NetIncomeLoss', 'us-gaap:ProfitLoss'],
        'eps_basic': ['us-gaap:EarningsPerShareBasic'],
        'eps_diluted': ['us-gaap:EarningsPerShareDiluted'],
        
        # Balance Sheet
        'total_assets': ['us-gaap:Assets'],
        'current_assets': ['us-gaap:AssetsCurrent'],
        'total_liabilities': ['us-gaap:Liabilities'],
        'current_liabilities': ['us-gaap:LiabilitiesCurrent'], 
        'stockholders_equity': ['us-gaap:StockholdersEquity'],
        'cash_and_equivalents': ['us-gaap:CashAndCashEquivalentsAtCarryingValue'],
        
        # Cash Flow
        'operating_cash_flow': ['us-gaap:NetCashProvidedByUsedInOperatingActivities'],
        'investing_cash_flow': ['us-gaap:NetCashProvidedByUsedInInvestingActivities'],
        'financing_cash_flow': ['us-gaap:NetCashProvidedByUsedInFinancingActivities']
    }
    
    def extract_financial_concepts(self, xbrl_data: Dict) -> Dict[str, float]:
        """Extract standardized financial concepts from XBRL"""
        
        extracted_data = {}
        
        for concept_name, gaap_tags in self.STANDARD_CONCEPTS.items():
            for gaap_tag in gaap_tags:
                if gaap_tag in xbrl_data:
                    # Get most recent value
                    concept_data = xbrl_data[gaap_tag]
                    if 'units' in concept_data and 'USD' in concept_data['units']:
                        usd_data = concept_data['units']['USD']
                        if usd_data:
                            # Get most recent period
                            latest_period = max(usd_data, key=lambda x: x.get('end', ''))
                            extracted_data[concept_name] = latest_period.get('val', 0)
                            break
                            
        return extracted_data
```

---

## 3. Tier 2 Enhancement Sources

### 3.1 Social Sentiment Sources

#### 3.1.1 Twitter/X API v2

**Purpose**: Real-time social sentiment analysis for retail investor sentiment

**Technical Specifications**:
```python
TWITTER_API_CONFIG = {
    'base_url': 'https://api.twitter.com/2/',
    'endpoints': {
        'recent_search': 'tweets/search/recent',
        'stream': 'tweets/search/stream',
        'tweet_counts': 'tweets/counts/recent'
    },
    'authentication': {
        'type': 'bearer_token',
        'header': 'Authorization: Bearer'
    },
    'rate_limits': {
        'essential': 'Free - 500,000 tweets/month',
        'elevated': 'Free - 2,000,000 tweets/month',
        'academic': 'Free - 10,000,000 tweets/month',
        'pro': '$5,000/month - 1,000,000 tweets/month'
    }
}
```

**Financial Twitter Analysis**:
```python
@dataclass
class TwitterFinancialSentiment:
    tweet_id: str
    text: str
    created_at: datetime
    author_id: str
    public_metrics: Dict[str, int]  # retweet_count, like_count, etc.
    
    # Extracted financial information
    mentioned_tickers: List[str] = field(default_factory=list)
    mentioned_companies: List[str] = field(default_factory=list)
    financial_keywords: List[str] = field(default_factory=list)
    
    # Sentiment analysis
    sentiment_score: float = 0.0  # -1 to 1
    sentiment_confidence: float = 0.0
    sentiment_label: str = 'neutral'
    
    # Context and influence
    author_influence_score: float = 0.0
    topic_relevance: float = 0.0
    viral_potential: float = 0.0
```

#### 3.1.2 Reddit API

**Purpose**: Long-form retail investor sentiment from financial subreddits

**Key Subreddits for Monitoring**:
```python
REDDIT_FINANCIAL_SUBREDDITS = {
    'r/investing': {
        'focus': 'Long-term investment discussion',
        'subscriber_count': 1900000,
        'quality': 'High',
        'sentiment_reliability': 0.8
    },
    'r/SecurityAnalysis': {
        'focus': 'Fundamental analysis and value investing',
        'subscriber_count': 180000,
        'quality': 'Very High',
        'sentiment_reliability': 0.9
    },
    'r/stocks': {
        'focus': 'General stock discussion',
        'subscriber_count': 4500000,
        'quality': 'Medium',
        'sentiment_reliability': 0.6
    },
    'r/wallstreetbets': {
        'focus': 'High-risk trading discussion',
        'subscriber_count': 15000000,
        'quality': 'Low (but high volume)',
        'sentiment_reliability': 0.4
    }
}
```

### 3.2 Economic Data Sources

#### 3.2.1 Federal Reserve Economic Data (FRED)

**Purpose**: Macroeconomic indicators and Federal Reserve data

**Technical Specifications**:
```python
FRED_CONFIG = {
    'base_url': 'https://api.stlouisfed.org/fred/',
    'endpoints': {
        'series_observations': 'series/observations',
        'series_info': 'series',
        'category_series': 'category/series',
        'releases': 'releases'
    },
    'authentication': {
        'type': 'api_key',
        'parameter': 'api_key'
    },
    'rate_limits': {
        'free': '120 requests/minute'
    },
    'cost': 'Free'
}
```

**Key Economic Indicators for ICE**:
```python
FRED_INDICATORS = {
    'interest_rates': {
        'fed_funds_rate': 'FEDFUNDS',
        '10yr_treasury': 'GS10', 
        '2yr_treasury': 'GS2',
        'yield_curve_spread': 'T10Y2Y'
    },
    'inflation': {
        'cpi_all_urban': 'CPIAUCSL',
        'core_cpi': 'CPILFESL',
        'pce_price_index': 'PCEPI'
    },
    'employment': {
        'unemployment_rate': 'UNRATE',
        'nonfarm_payrolls': 'PAYEMS',
        'labor_force_participation': 'CIVPART'
    },
    'economic_activity': {
        'gdp_growth': 'GDP',
        'industrial_production': 'INDPRO',
        'consumer_confidence': 'UMCSENT'
    }
}
```

---

## 4. Tier 3 Alternative Sources

### 4.1 Alternative Intelligence Sources

#### 4.1.1 Satellite Imagery Data (Planet Labs)

**Purpose**: Economic activity monitoring through satellite imagery analysis

**Use Cases for Investment Intelligence**:
- Retail foot traffic analysis (parking lot analysis)
- Industrial capacity utilization (factory activity)
- Agricultural yield predictions (crop monitoring)
- Infrastructure development tracking
- Environmental impact assessment

#### 4.1.2 Patent Data (USPTO)

**Purpose**: Innovation tracking and competitive intelligence

**Data Coverage**:
- Patent applications and grants
- Inventor and assignee information
- Technology classification codes
- Citation networks
- Patent litigation data

---

## 5. API Integration Specifications

### 5.1 Standard Integration Pattern

```python
class BaseDataSourceConnector:
    """Abstract base class for all data source integrations"""
    
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.session = aiohttp.ClientSession()
        self.rate_limiter = RateLimiter(config.rate_limit)
        self.auth_manager = AuthManager(config.auth)
        self.circuit_breaker = CircuitBreaker(config.circuit_breaker)
        
    async def fetch_data(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch data with error handling and rate limiting"""
        
        # Rate limiting
        await self.rate_limiter.acquire()
        
        # Authentication
        headers = await self.auth_manager.get_headers()
        
        # Circuit breaker protection
        async with self.circuit_breaker:
            response = await self.session.get(
                url=self.config.base_url,
                params=params,
                headers=headers,
                timeout=self.config.timeout
            )
            
        return await self.process_response(response)
        
    @abstractmethod
    async def process_response(self, response) -> List[Dict[str, Any]]:
        """Process API response into standard format"""
        pass
        
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate individual data record"""
        pass
```

### 5.2 Error Handling Strategy

```python
class DataSourceErrorHandler:
    """Centralized error handling for all data sources"""
    
    ERROR_CATEGORIES = {
        'rate_limit': {
            'retry_strategy': 'exponential_backoff',
            'max_retries': 5,
            'base_delay': 60
        },
        'authentication': {
            'retry_strategy': 'refresh_auth',
            'max_retries': 2,
            'escalation': 'alert_admin'
        },
        'server_error': {
            'retry_strategy': 'exponential_backoff',
            'max_retries': 3,
            'base_delay': 10
        },
        'data_quality': {
            'retry_strategy': 'no_retry',
            'action': 'log_and_skip',
            'alert_threshold': 10
        }
    }
    
    async def handle_error(self, error: Exception, context: Dict[str, Any]):
        """Handle errors based on type and context"""
        
        error_category = self.categorize_error(error)
        strategy = self.ERROR_CATEGORIES[error_category]
        
        if strategy['retry_strategy'] == 'exponential_backoff':
            return await self.exponential_backoff_retry(error, context, strategy)
        elif strategy['retry_strategy'] == 'refresh_auth':
            return await self.refresh_auth_retry(error, context, strategy)
        else:
            await self.log_error(error, context)
            return None
```

---

## 6. Data Schemas & Models

### 6.1 Universal Data Model

```python
@dataclass
class UniversalDataRecord:
    """Standardized data model for all sources"""
    
    # Universal identifiers
    record_id: str
    source: str
    data_type: DataType
    timestamp: datetime
    
    # Content
    raw_content: Dict[str, Any]
    processed_content: Optional[Dict[str, Any]] = None
    
    # Financial entities
    tickers: List[str] = field(default_factory=list)
    companies: List[str] = field(default_factory=list)
    financial_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Content analysis
    sentiment_score: Optional[float] = None
    relevance_score: float = 0.0
    quality_score: float = 0.0
    
    # Processing metadata
    processing_version: str = "1.0"
    processing_timestamp: Optional[datetime] = None
    validation_status: ValidationStatus = ValidationStatus.PENDING
    
    # Source-specific metadata
    source_metadata: Dict[str, Any] = field(default_factory=dict)
```

### 6.2 Source-Specific Models

#### 6.2.1 News Data Model

```python
@dataclass
class NewsDataModel:
    """Specialized model for news data"""
    
    # Inherits from UniversalDataRecord
    base_record: UniversalDataRecord
    
    # News-specific fields
    headline: str
    content: str
    url: str
    author: Optional[str]
    publication: str
    
    # News analysis
    entities_mentioned: List[EntityMention]
    topics: List[str]
    geographic_focus: List[str]
    
    # Impact assessment
    market_impact_score: float = 0.0
    urgency_level: UrgencyLevel = UrgencyLevel.NORMAL
    breaking_news: bool = False
```

#### 6.2.2 Financial Data Model

```python
@dataclass
class FinancialDataModel:
    """Specialized model for financial metrics data"""
    
    # Inherits from UniversalDataRecord
    base_record: UniversalDataRecord
    
    # Financial identifiers
    ticker: str
    company_name: str
    exchange: str
    sector: Optional[str]
    industry: Optional[str]
    
    # Price data
    price_data: Optional[PriceData] = None
    
    # Financial statements
    income_statement: Optional[IncomeStatement] = None
    balance_sheet: Optional[BalanceSheet] = None
    cash_flow: Optional[CashFlow] = None
    
    # Valuation metrics
    valuation_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Data quality indicators
    data_completeness: float = 0.0
    cross_source_consistency: float = 0.0
```

---

## 7. Quality & Validation Rules

### 7.1 Data Quality Framework

```python
class DataQualityAssessment:
    """Comprehensive data quality assessment"""
    
    QUALITY_DIMENSIONS = {
        'completeness': {
            'weight': 0.25,
            'thresholds': {'excellent': 0.95, 'good': 0.85, 'acceptable': 0.70}
        },
        'accuracy': {
            'weight': 0.30,
            'thresholds': {'excellent': 0.98, 'good': 0.90, 'acceptable': 0.80}
        },
        'timeliness': {
            'weight': 0.20,
            'thresholds': {'excellent': 0.95, 'good': 0.85, 'acceptable': 0.70}
        },
        'consistency': {
            'weight': 0.15,
            'thresholds': {'excellent': 0.95, 'good': 0.85, 'acceptable': 0.75}
        },
        'validity': {
            'weight': 0.10,
            'thresholds': {'excellent': 0.98, 'good': 0.92, 'acceptable': 0.85}
        }
    }
    
    def assess_quality(self, data_record: UniversalDataRecord) -> QualityAssessment:
        """Calculate comprehensive quality score"""
        
        dimension_scores = {}
        
        # Completeness: percentage of expected fields populated
        dimension_scores['completeness'] = self.calculate_completeness(data_record)
        
        # Accuracy: correctness through cross-validation
        dimension_scores['accuracy'] = self.calculate_accuracy(data_record)
        
        # Timeliness: data freshness relative to expectations
        dimension_scores['timeliness'] = self.calculate_timeliness(data_record)
        
        # Consistency: consistency with historical data and other sources
        dimension_scores['consistency'] = self.calculate_consistency(data_record)
        
        # Validity: compliance with business rules and constraints
        dimension_scores['validity'] = self.calculate_validity(data_record)
        
        # Calculate weighted overall score
        overall_score = sum(
            score * self.QUALITY_DIMENSIONS[dim]['weight']
            for dim, score in dimension_scores.items()
        )
        
        return QualityAssessment(
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            grade=self.determine_quality_grade(overall_score),
            recommendations=self.generate_quality_recommendations(dimension_scores)
        )
```

### 7.2 Business Rule Validation

```python
class FinancialDataValidator:
    """Investment-specific validation rules"""
    
    VALIDATION_RULES = {
        'ticker_format': {
            'pattern': r'^[A-Z]{1,5}$',
            'description': 'US equity ticker symbol format'
        },
        'financial_metrics': {
            'market_cap': {'min': 1e6, 'max': 1e13},
            'pe_ratio': {'min': -1000, 'max': 1000},
            'price': {'min': 0.01, 'max': 100000},
            'volume': {'min': 0, 'max': 1e10}
        },
        'temporal_consistency': {
            'max_future_date': 0,  # days
            'max_past_date': 1825  # 5 years
        }
    }
    
    def validate_financial_record(self, record: FinancialDataModel) -> ValidationResult:
        """Apply financial-specific validation rules"""
        
        validation_errors = []
        
        # Validate ticker format
        if not re.match(self.VALIDATION_RULES['ticker_format']['pattern'], record.ticker):
            validation_errors.append(
                ValidationError(
                    field='ticker',
                    value=record.ticker,
                    rule='ticker_format',
                    severity=ErrorSeverity.ERROR
                )
            )
        
        # Validate financial metrics ranges
        for metric, value in record.valuation_metrics.items():
            if metric in self.VALIDATION_RULES['financial_metrics']:
                range_config = self.VALIDATION_RULES['financial_metrics'][metric]
                if not (range_config['min'] <= value <= range_config['max']):
                    validation_errors.append(
                        ValidationError(
                            field=metric,
                            value=value,
                            rule='financial_metrics_range',
                            severity=ErrorSeverity.WARNING
                        )
                    )
        
        return ValidationResult(
            passed=len([e for e in validation_errors if e.severity == ErrorSeverity.ERROR]) == 0,
            warnings=len([e for e in validation_errors if e.severity == ErrorSeverity.WARNING]),
            errors=validation_errors
        )
```

---

## 8. Cost & Usage Management

### 8.1 Cost Optimization Strategy

```python
class CostOptimizationManager:
    """Manage API costs and optimize usage"""
    
    def __init__(self):
        self.cost_tracker = APICostTracker()
        self.usage_optimizer = APIUsageOptimizer()
        self.budget_manager = BudgetManager()
        
    async def optimize_api_usage(self):
        """Implement cost optimization strategies"""
        
        current_costs = await self.cost_tracker.get_daily_costs()
        budget_status = await self.budget_manager.get_budget_status()
        
        optimizations = []
        
        # Strategy 1: Smart caching
        if current_costs['total'] > budget_status['daily_target'] * 0.8:
            cache_optimization = await self.usage_optimizer.increase_cache_duration()
            optimizations.append(cache_optimization)
            
        # Strategy 2: Request batching
        batching_optimization = await self.usage_optimizer.optimize_request_batching()
        optimizations.append(batching_optimization)
        
        # Strategy 3: Data source prioritization
        if budget_status['remaining'] < 0.2:
            prioritization = await self.usage_optimizer.prioritize_high_value_sources()
            optimizations.append(prioritization)
            
        return optimizations
```

### 8.2 Budget Monitoring

```python
@dataclass
class BudgetAllocation:
    """Monthly budget allocation across data sources"""
    
    total_monthly_budget: float = 2000.0  # $2000/month total
    
    allocations: Dict[str, float] = field(default_factory=lambda: {
        'newsapi': 450.0,      # 22.5% - Primary news source
        'benzinga': 300.0,     # 15% - Premium financial news
        'fmp': 100.0,          # 5% - Financial data
        'alpha_vantage': 50.0, # 2.5% - Real-time data
        'twitter_api': 500.0,  # 25% - Social sentiment
        'contingency': 600.0   # 30% - Buffer and future sources
    })
    
    def get_daily_budget(self, source: str) -> float:
        """Calculate daily budget for source"""
        monthly_allocation = self.allocations.get(source, 0)
        return monthly_allocation / 30  # Approximate daily budget
        
    def check_budget_status(self, source: str, current_spend: float) -> BudgetStatus:
        """Check budget status for source"""
        daily_budget = self.get_daily_budget(source)
        utilization = current_spend / daily_budget if daily_budget > 0 else 0
        
        if utilization > 1.0:
            status = BudgetStatus.OVER_BUDGET
        elif utilization > 0.8:
            status = BudgetStatus.APPROACHING_LIMIT
        else:
            status = BudgetStatus.WITHIN_BUDGET
            
        return BudgetStatus(
            source=source,
            daily_budget=daily_budget,
            current_spend=current_spend,
            utilization=utilization,
            status=status
        )
```

---

## Conclusion

This comprehensive data sources specification provides the technical foundation for implementing a robust, multi-source data ingestion system for the Investment Context Engine. The specification emphasizes:

**Strategic Data Sourcing**: Balanced approach across news, financial, regulatory, and alternative data sources to provide comprehensive investment context.

**Technical Excellence**: Detailed API specifications, error handling, and quality validation ensure reliable data ingestion.

**Cost Management**: Proactive budget monitoring and optimization strategies maintain financial sustainability.

**Quality Assurance**: Multi-dimensional quality assessment ensures high-confidence investment insights.

**Scalable Architecture**: Modular design supports incremental implementation and future expansion.

The tiered implementation approach allows for immediate value delivery while building toward comprehensive market intelligence capabilities. Each data source integration follows standardized patterns while accommodating source-specific requirements and optimizations.

**Next Steps**: Begin Tier 1 implementation with NewsAPI integration, following the detailed technical specifications and integration patterns outlined in this document.

---

**Document Version**: 1.0  
**Last Updated**: August 2025  
**Implementation Priority**: Tier 1 sources (Weeks 1-4)  
**Budget Impact**: $2000/month for comprehensive data coverage