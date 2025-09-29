# ice_data_ingestion/data_validator.py
"""
Data Validation Framework for ICE Data Ingestion
Validates schema, data quality, consistency, and integrity across all sources
Implements financial data validation rules and cross-source verification
Relevant files: financial_news_connectors.py, sec_edgar_connector.py, test_scenarios.py
"""

import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
from decimal import Decimal, InvalidOperation
import statistics

# Import numpy types for compatibility checking
try:
    import numpy as np
    NUMPY_AVAILABLE = True
    NUMPY_FLOAT_TYPES = (np.floating, np.float16, np.float32, np.float64)
    NUMPY_INT_TYPES = (np.integer, np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64)
except ImportError:
    NUMPY_AVAILABLE = False
    NUMPY_FLOAT_TYPES = ()
    NUMPY_INT_TYPES = ()

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation strictness levels"""
    STRICT = "strict"  # All validations must pass
    NORMAL = "normal"  # Critical validations must pass
    LENIENT = "lenient"  # Best effort validation


class ValidationResult(Enum):
    """Validation result types"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class ValidationError:
    """Individual validation error"""
    field: str
    message: str
    severity: str  # critical, warning, info
    actual_value: Any
    expected_value: Any = None
    error_code: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report"""
    source: str
    ticker: str
    timestamp: datetime
    result: ValidationResult
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    data_hash: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        """Check if validation passed"""
        return self.result in [ValidationResult.PASS, ValidationResult.WARNING]

    @property
    def critical_errors(self) -> List[ValidationError]:
        """Get only critical errors"""
        return [e for e in self.errors if e.severity == "critical"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'source': self.source,
            'ticker': self.ticker,
            'timestamp': self.timestamp.isoformat(),
            'result': self.result.value,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'critical_errors': [e.message for e in self.critical_errors],
            'metrics': self.metrics,
            'data_hash': self.data_hash
        }


class SchemaValidator:
    """Validates data against expected schemas"""

    # Expected schemas for different data types
    STOCK_PRICE_SCHEMA = {
        'required': ['open', 'high', 'low', 'close', 'volume'],
        'optional': ['adjusted_close', 'dividend', 'split_ratio', 'vwap'],
        'types': {
            'open': (float, int, Decimal),
            'high': (float, int, Decimal),
            'low': (float, int, Decimal),
            'close': (float, int, Decimal),
            'volume': (int, float),
            'timestamp': (datetime, str)
        }
    }

    COMPANY_INFO_SCHEMA = {
        'required': ['name', 'ticker', 'exchange'],
        'optional': ['market_cap', 'sector', 'industry', 'employees', 'description'],
        'types': {
            'name': str,
            'ticker': str,
            'market_cap': (int, float),
            'employees': int
        }
    }

    NEWS_ARTICLE_SCHEMA = {
        'required': ['title', 'url', 'published_date'],
        'optional': ['summary', 'author', 'source', 'sentiment', 'symbols'],
        'types': {
            'title': str,
            'url': str,
            'published_date': (datetime, str),
            'sentiment': (str, float)
        }
    }

    SEC_FILING_SCHEMA = {
        'required': ['form_type', 'filing_date', 'accession_number'],
        'optional': ['file_number', 'acceptance_datetime', 'documents'],
        'types': {
            'form_type': str,
            'filing_date': (datetime, str),
            'accession_number': str
        }
    }

    @classmethod
    def validate_schema(
        cls,
        data: Dict[str, Any],
        schema: Dict[str, Any],
        level: ValidationLevel = ValidationLevel.NORMAL
    ) -> List[ValidationError]:
        """
        Validate data against schema

        Args:
            data: Data to validate
            schema: Expected schema
            level: Validation strictness

        Returns:
            List of validation errors
        """
        errors = []

        # Check required fields
        for field in schema.get('required', []):
            if field not in data or data[field] is None:
                errors.append(ValidationError(
                    field=field,
                    message=f"Required field '{field}' is missing",
                    severity="critical",
                    actual_value=None,
                    expected_value="not null"
                ))

        # Check optional fields in strict mode
        if level == ValidationLevel.STRICT:
            for field in schema.get('optional', []):
                if field not in data:
                    errors.append(ValidationError(
                        field=field,
                        message=f"Optional field '{field}' is missing",
                        severity="warning",
                        actual_value=None,
                        expected_value="present"
                    ))

        # Type validation with numpy compatibility
        type_specs = schema.get('types', {})
        for field, expected_types in type_specs.items():
            if field in data and data[field] is not None:
                value = data[field]
                if not isinstance(expected_types, tuple):
                    expected_types = (expected_types,)

                # Check if value matches expected types (including numpy compatibility)
                type_match = False

                # Standard type checking
                if isinstance(value, expected_types):
                    type_match = True

                # Numpy compatibility checking
                elif NUMPY_AVAILABLE:
                    # Check if float types match (including numpy float types)
                    if (float in expected_types or int in expected_types or Decimal in expected_types):
                        if isinstance(value, NUMPY_FLOAT_TYPES) or isinstance(value, NUMPY_INT_TYPES):
                            try:
                                # Try to convert numpy type to native Python type
                                if isinstance(value, NUMPY_FLOAT_TYPES):
                                    native_value = float(value)
                                    if float in expected_types or Decimal in expected_types:
                                        type_match = True
                                elif isinstance(value, NUMPY_INT_TYPES):
                                    native_value = int(value)
                                    if int in expected_types or float in expected_types:
                                        type_match = True
                            except (ValueError, OverflowError):
                                # If conversion fails, keep type_match as False
                                pass

                if not type_match:
                    # Provide helpful error message with numpy type info
                    actual_type = type(value).__name__
                    if NUMPY_AVAILABLE and hasattr(value, 'dtype'):
                        actual_type += f" (numpy {value.dtype})"

                    errors.append(ValidationError(
                        field=field,
                        message=f"Field '{field}' has incorrect type. Consider converting numpy types to native Python types.",
                        severity="critical",
                        actual_value=actual_type,
                        expected_value=str(expected_types)
                    ))

        return errors


class DataQualityValidator:
    """Validates data quality metrics"""

    @staticmethod
    def validate_price_data(price_data: Dict[str, Any]) -> List[ValidationError]:
        """
        Validate stock price data quality

        Args:
            price_data: Price data dictionary

        Returns:
            List of validation errors
        """
        errors = []

        # Price sanity checks
        open_price = price_data.get('open')
        high = price_data.get('high')
        low = price_data.get('low')
        close = price_data.get('close')
        volume = price_data.get('volume')

        # High should be >= all other prices
        if high is not None:
            for price_type, price in [('open', open_price), ('low', low), ('close', close)]:
                if price is not None and high < price:
                    errors.append(ValidationError(
                        field='high',
                        message=f"High price ({high}) is less than {price_type} ({price})",
                        severity="critical",
                        actual_value=high,
                        expected_value=f">= {price}"
                    ))

        # Low should be <= all other prices
        if low is not None:
            for price_type, price in [('open', open_price), ('high', high), ('close', close)]:
                if price is not None and low > price:
                    errors.append(ValidationError(
                        field='low',
                        message=f"Low price ({low}) is greater than {price_type} ({price})",
                        severity="critical",
                        actual_value=low,
                        expected_value=f"<= {price}"
                    ))

        # Check for negative prices
        for field, value in [('open', open_price), ('high', high), ('low', low), ('close', close)]:
            if value is not None and value < 0:
                errors.append(ValidationError(
                    field=field,
                    message=f"{field} price cannot be negative",
                    severity="critical",
                    actual_value=value,
                    expected_value=">= 0"
                ))

        # Check for zero prices (except for special cases)
        if all(p == 0 for p in [open_price, high, low, close] if p is not None):
            errors.append(ValidationError(
                field='prices',
                message="All prices are zero",
                severity="warning",
                actual_value=0,
                expected_value="> 0"
            ))

        # Volume validation
        if volume is not None:
            if volume < 0:
                errors.append(ValidationError(
                    field='volume',
                    message="Volume cannot be negative",
                    severity="critical",
                    actual_value=volume,
                    expected_value=">= 0"
                ))
            elif volume > 1e12:  # Trillion shares - likely error
                errors.append(ValidationError(
                    field='volume',
                    message="Volume suspiciously high",
                    severity="warning",
                    actual_value=volume,
                    expected_value="< 1 trillion"
                ))

        return errors

    @staticmethod
    def validate_timestamp(
        timestamp: Union[datetime, str],
        max_age_hours: int = 24,
        allow_future: bool = False
    ) -> List[ValidationError]:
        """
        Validate timestamp freshness and validity

        Args:
            timestamp: Timestamp to validate
            max_age_hours: Maximum age in hours
            allow_future: Whether to allow future timestamps

        Returns:
            List of validation errors
        """
        errors = []

        # Convert string to datetime if needed
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                errors.append(ValidationError(
                    field='timestamp',
                    message="Invalid timestamp format",
                    severity="critical",
                    actual_value=timestamp,
                    expected_value="ISO format datetime"
                ))
                return errors

        now = datetime.now()

        # Check for future timestamps
        if not allow_future and timestamp > now:
            errors.append(ValidationError(
                field='timestamp',
                message="Timestamp is in the future",
                severity="warning",
                actual_value=timestamp,
                expected_value=f"<= {now}"
            ))

        # Check age
        age = now - timestamp
        if age.total_seconds() > max_age_hours * 3600:
            errors.append(ValidationError(
                field='timestamp',
                message=f"Data is older than {max_age_hours} hours",
                severity="warning",
                actual_value=timestamp,
                expected_value=f"within {max_age_hours} hours"
            ))

        # Check for suspiciously old data (> 10 years)
        if age.days > 3650:
            errors.append(ValidationError(
                field='timestamp',
                message="Timestamp is suspiciously old (>10 years)",
                severity="critical",
                actual_value=timestamp,
                expected_value="within reasonable range"
            ))

        return errors

    @staticmethod
    def validate_ticker_symbol(ticker: str) -> List[ValidationError]:
        """
        Validate ticker symbol format

        Args:
            ticker: Ticker symbol to validate

        Returns:
            List of validation errors
        """
        errors = []

        if not ticker:
            errors.append(ValidationError(
                field='ticker',
                message="Ticker symbol is empty",
                severity="critical",
                actual_value=ticker,
                expected_value="non-empty string"
            ))
            return errors

        # Check length (most tickers are 1-5 characters)
        if len(ticker) > 10:
            errors.append(ValidationError(
                field='ticker',
                message="Ticker symbol is unusually long",
                severity="warning",
                actual_value=ticker,
                expected_value="1-10 characters"
            ))

        # Check for valid characters (letters, numbers, dots, hyphens)
        if not re.match(r'^[A-Z0-9.\-=^]+$', ticker.upper()):
            errors.append(ValidationError(
                field='ticker',
                message="Ticker contains invalid characters",
                severity="warning",
                actual_value=ticker,
                expected_value="letters, numbers, dots, hyphens only"
            ))

        return errors


class CrossSourceValidator:
    """Validates consistency across multiple data sources"""

    @staticmethod
    def validate_price_consistency(
        prices: Dict[str, float],
        tolerance_percent: float = 0.5
    ) -> List[ValidationError]:
        """
        Validate price consistency across sources

        Args:
            prices: Dictionary of source -> price
            tolerance_percent: Acceptable percentage difference

        Returns:
            List of validation errors
        """
        errors = []

        if len(prices) < 2:
            return errors  # Need at least 2 sources to compare

        # Calculate statistics
        price_values = list(prices.values())
        mean_price = statistics.mean(price_values)
        std_dev = statistics.stdev(price_values) if len(price_values) > 1 else 0

        # Check each price against mean
        for source, price in prices.items():
            diff_percent = abs(price - mean_price) / mean_price * 100 if mean_price else 0

            if diff_percent > tolerance_percent:
                errors.append(ValidationError(
                    field=f'price_{source}',
                    message=f"Price from {source} deviates {diff_percent:.2f}% from mean",
                    severity="warning" if diff_percent < tolerance_percent * 2 else "critical",
                    actual_value=price,
                    expected_value=f"within {tolerance_percent}% of {mean_price:.2f}"
                ))

        # Check for outliers using z-score
        if std_dev > 0:
            for source, price in prices.items():
                z_score = abs(price - mean_price) / std_dev
                if z_score > 3:  # 3 standard deviations
                    errors.append(ValidationError(
                        field=f'price_{source}',
                        message=f"Price from {source} is an outlier (z-score: {z_score:.2f})",
                        severity="warning",
                        actual_value=price,
                        expected_value="within 3 standard deviations"
                    ))

        return errors

    @staticmethod
    def validate_volume_consistency(
        volumes: Dict[str, int],
        tolerance_percent: float = 10.0
    ) -> List[ValidationError]:
        """
        Validate volume consistency across sources

        Args:
            volumes: Dictionary of source -> volume
            tolerance_percent: Acceptable percentage difference

        Returns:
            List of validation errors
        """
        errors = []

        if len(volumes) < 2:
            return errors

        # Volume can vary more than price, so be more lenient
        volume_values = list(volumes.values())
        mean_volume = statistics.mean(volume_values)

        for source, volume in volumes.items():
            if mean_volume > 0:
                diff_percent = abs(volume - mean_volume) / mean_volume * 100

                if diff_percent > tolerance_percent:
                    errors.append(ValidationError(
                        field=f'volume_{source}',
                        message=f"Volume from {source} deviates {diff_percent:.2f}% from mean",
                        severity="info" if diff_percent < tolerance_percent * 2 else "warning",
                        actual_value=volume,
                        expected_value=f"within {tolerance_percent}% of {mean_volume:.0f}"
                    ))

        return errors


class DataIntegrityValidator:
    """Validates data integrity and completeness"""

    @staticmethod
    def calculate_data_hash(data: Any) -> str:
        """Calculate hash of data for integrity checking"""
        # Convert to string representation for hashing
        data_str = str(sorted(data.items()) if isinstance(data, dict) else data)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    @staticmethod
    def validate_data_completeness(
        data: Dict[str, Any],
        required_fields: List[str],
        min_completeness: float = 0.8
    ) -> List[ValidationError]:
        """
        Validate data completeness

        Args:
            data: Data to validate
            required_fields: List of required fields
            min_completeness: Minimum completeness ratio

        Returns:
            List of validation errors
        """
        errors = []

        present_fields = [f for f in required_fields if f in data and data[f] is not None]
        completeness = len(present_fields) / len(required_fields) if required_fields else 0

        if completeness < min_completeness:
            missing = [f for f in required_fields if f not in present_fields]
            errors.append(ValidationError(
                field='completeness',
                message=f"Data completeness {completeness:.1%} below threshold",
                severity="warning" if completeness > 0.5 else "critical",
                actual_value=f"{completeness:.1%}",
                expected_value=f">= {min_completeness:.1%}",
                error_code=f"missing_fields: {', '.join(missing)}"
            ))

        return errors

    @staticmethod
    def validate_duplicate_detection(
        current_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
        key_fields: List[str]
    ) -> List[ValidationError]:
        """
        Detect duplicate data entries

        Args:
            current_data: Current data entry
            historical_data: Historical data to check against
            key_fields: Fields to use for duplicate detection

        Returns:
            List of validation errors
        """
        errors = []

        # Create key from current data
        current_key = tuple(current_data.get(f) for f in key_fields)

        # Check against historical data
        for hist_entry in historical_data:
            hist_key = tuple(hist_entry.get(f) for f in key_fields)

            if current_key == hist_key:
                errors.append(ValidationError(
                    field='duplicate',
                    message=f"Duplicate entry detected on fields: {', '.join(key_fields)}",
                    severity="warning",
                    actual_value=current_key,
                    expected_value="unique"
                ))
                break

        return errors


class DataValidationService:
    """Main service for comprehensive data validation"""

    def __init__(self, level: ValidationLevel = ValidationLevel.NORMAL):
        """Initialize validation service"""
        self.level = level
        self.schema_validator = SchemaValidator()
        self.quality_validator = DataQualityValidator()
        self.cross_source_validator = CrossSourceValidator()
        self.integrity_validator = DataIntegrityValidator()

    @staticmethod
    def normalize_data_types(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert numpy types to native Python types for compatibility

        Args:
            data: Dictionary containing mixed data types

        Returns:
            Dictionary with normalized types
        """
        normalized = {}

        for key, value in data.items():
            if value is None:
                normalized[key] = value
            elif NUMPY_AVAILABLE and isinstance(value, NUMPY_FLOAT_TYPES):
                normalized[key] = float(value)
            elif NUMPY_AVAILABLE and isinstance(value, NUMPY_INT_TYPES):
                normalized[key] = int(value)
            else:
                normalized[key] = value

        return normalized

    def validate_stock_data(
        self,
        source: str,
        ticker: str,
        data: Dict[str, Any]
    ) -> ValidationReport:
        """
        Comprehensive stock data validation

        Args:
            source: Data source name
            ticker: Stock ticker
            data: Stock data to validate

        Returns:
            Validation report
        """
        report = ValidationReport(
            source=source,
            ticker=ticker,
            timestamp=datetime.now(),
            result=ValidationResult.PASS
        )

        # Schema validation
        schema_errors = self.schema_validator.validate_schema(
            data,
            SchemaValidator.STOCK_PRICE_SCHEMA,
            self.level
        )
        report.errors.extend(schema_errors)

        # Quality validation
        quality_errors = self.quality_validator.validate_price_data(data)
        report.errors.extend(quality_errors)

        # Ticker validation
        ticker_errors = self.quality_validator.validate_ticker_symbol(ticker)
        report.errors.extend(ticker_errors)

        # Timestamp validation if present
        if 'timestamp' in data:
            timestamp_errors = self.quality_validator.validate_timestamp(data['timestamp'])
            report.errors.extend(timestamp_errors)

        # Calculate data hash
        report.data_hash = self.integrity_validator.calculate_data_hash(data)

        # Determine overall result
        if any(e.severity == "critical" for e in report.errors):
            report.result = ValidationResult.FAIL
        elif report.errors:
            report.result = ValidationResult.WARNING

        # Calculate metrics
        report.metrics = {
            'total_errors': len(report.errors),
            'critical_errors': len([e for e in report.errors if e.severity == "critical"]),
            'warnings': len([e for e in report.errors if e.severity == "warning"]),
            'data_fields': len(data),
            'validation_level': self.level.value
        }

        return report

    def validate_cross_source(
        self,
        ticker: str,
        source_data: Dict[str, Dict[str, Any]]
    ) -> ValidationReport:
        """
        Validate data consistency across sources

        Args:
            ticker: Stock ticker
            source_data: Dictionary of source -> data

        Returns:
            Validation report
        """
        report = ValidationReport(
            source="cross_source",
            ticker=ticker,
            timestamp=datetime.now(),
            result=ValidationResult.PASS
        )

        # Extract prices from each source
        prices = {}
        volumes = {}

        for source, data in source_data.items():
            if 'close' in data and data['close'] is not None:
                prices[source] = float(data['close'])
            if 'volume' in data and data['volume'] is not None:
                volumes[source] = int(data['volume'])

        # Validate price consistency
        if prices:
            price_errors = self.cross_source_validator.validate_price_consistency(prices)
            report.errors.extend(price_errors)

        # Validate volume consistency
        if volumes:
            volume_errors = self.cross_source_validator.validate_volume_consistency(volumes)
            report.warnings.extend(volume_errors)

        # Determine result
        if any(e.severity == "critical" for e in report.errors):
            report.result = ValidationResult.FAIL
        elif report.errors or report.warnings:
            report.result = ValidationResult.WARNING

        # Metrics
        report.metrics = {
            'sources_compared': len(source_data),
            'price_sources': len(prices),
            'volume_sources': len(volumes),
            'consistency_score': 1.0 - (len(report.errors) / max(len(source_data), 1))
        }

        return report

    def generate_summary_report(self, reports: List[ValidationReport]) -> Dict[str, Any]:
        """Generate summary of multiple validation reports"""
        total = len(reports)
        passed = sum(1 for r in reports if r.result == ValidationResult.PASS)
        failed = sum(1 for r in reports if r.result == ValidationResult.FAIL)
        warnings = sum(1 for r in reports if r.result == ValidationResult.WARNING)

        return {
            'total_validations': total,
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'success_rate': passed / total if total > 0 else 0,
            'critical_errors': sum(len(r.critical_errors) for r in reports),
            'validation_time': datetime.now().isoformat(),
            'by_source': self._group_by_source(reports),
            'by_ticker': self._group_by_ticker(reports)
        }

    def _group_by_source(self, reports: List[ValidationReport]) -> Dict[str, Dict[str, int]]:
        """Group validation results by source"""
        by_source = {}
        for report in reports:
            if report.source not in by_source:
                by_source[report.source] = {'pass': 0, 'fail': 0, 'warning': 0}
            by_source[report.source][report.result.value] += 1
        return by_source

    def _group_by_ticker(self, reports: List[ValidationReport]) -> Dict[str, Dict[str, int]]:
        """Group validation results by ticker"""
        by_ticker = {}
        for report in reports:
            if report.ticker not in by_ticker:
                by_ticker[report.ticker] = {'pass': 0, 'fail': 0, 'warning': 0}
            by_ticker[report.ticker][report.result.value] += 1
        return by_ticker