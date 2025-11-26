# Location: tests/test_temporal_enhancements_2025_11_18.py
# Purpose: Validate temporal architecture enhancements (event_date fix, recency ranking)
# Why: Ensure Q2 earnings announced July 15 (ingested Aug 1) appear in July queries
# Relevant Files: signal_store.py, config.py, temporal_enhancer.py

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from updated_architectures.implementation.signal_store import SignalStore
from updated_architectures.implementation.config import ICEConfig


def test_event_date_inference():
    """Test helper function that infers event_date from fiscal periods"""
    print("=" * 70)
    print("TEST 1: Event Date Inference from Fiscal Periods")
    print("=" * 70)

    test_cases = [
        # (period, fiscal_year, fiscal_quarter, expected_date)
        ("Q2 2024", None, None, "2024-07-15"),  # Q2 announced mid-July
        ("Q4 2023", None, None, "2024-01-15"),  # Q4 announced mid-January (next year)
        ("FY2024", None, None, "2025-02-15"),   # Annual announced mid-February (next year)
        ("TTM", None, None, None),               # TTM uses current date (skip exact match)
        (None, 2024, 2, "2024-07-15"),          # From fiscal_year + fiscal_quarter
        (None, 2023, 4, "2024-01-15"),          # Q4 rolls to next year
    ]

    passed = 0
    failed = 0

    for period, fy, fq, expected in test_cases:
        result = SignalStore._infer_event_date_from_period(period, fy, fq)

        # Special handling for TTM (current date)
        if period and 'TTM' in period:
            if result and result == datetime.now().strftime('%Y-%m-%d'):
                print(f"✅ PASS: period='{period}' → {result} (current date)")
                passed += 1
            else:
                print(f"❌ FAIL: period='{period}' → {result} (expected current date)")
                failed += 1
            continue

        if result == expected:
            print(f"✅ PASS: period='{period}', fy={fy}, fq={fq} → {result}")
            passed += 1
        else:
            print(f"❌ FAIL: period='{period}', fy={fy}, fq={fq} → {result} (expected {expected})")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_event_date_date_range_query():
    """Test get_metrics_by_date_range uses event_date instead of created_at"""
    print("\n" + "=" * 70)
    print("TEST 2: Date Range Query with Event Date (Critical Bug Fix)")
    print("=" * 70)

    # Create temporary test database
    test_db_path = "data/signal_store/test_temporal_signal_store.db"
    os.makedirs("data/signal_store", exist_ok=True)

    # Clean up existing test db
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    store = SignalStore(db_path=test_db_path)

    # Scenario: Q2 2024 earnings announced July 15, but ingested Aug 1
    # Query for July 1-31 should FIND this metric (using event_date)
    # Old bug: Would NOT find it (used created_at = Aug 1)

    try:
        # Insert test metrics into the METRICS table (email extraction table)
        # Note: get_metrics_by_date_range queries the 'metrics' table, not 'financial_metrics'
        cursor = store.conn.cursor()

        # Manually insert with event_date for testing
        cursor.execute("""
            INSERT INTO metrics
            (ticker, metric_type, metric_value, period, confidence,
             source_document_id, event_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'NVDA', 'Revenue', '$26.97B', 'Q2 2024', 0.95,
            'test_q2_earnings', '2024-07-15', '2024-08-01'  # event_date=July, created_at=August
        ))

        cursor.execute("""
            INSERT INTO metrics
            (ticker, metric_type, metric_value, period, confidence,
             source_document_id, event_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'NVDA', 'Operating Margin', '62.5%', 'Q3 2024', 0.90,
            'test_q3_earnings', '2024-10-15', '2024-11-01'  # event_date=Oct, created_at=Nov
        ))

        store.conn.commit()
        print(f"📊 Inserted 2 test metrics (with event_date != created_at)")

        # Test 1: Query for July (should find Q2 2024 with event_date=2024-07-15)
        # Even though created_at=2024-08-01 (August)
        july_results = store.get_metrics_by_date_range(
            ticker='NVDA',
            start_date='2024-07-01',
            end_date='2024-07-31',
            limit=10
        )

        q2_found = any(m.get('period') == 'Q2 2024' for m in july_results)

        if q2_found:
            print("✅ PASS: Q2 2024 metric found in July date range (event_date=2024-07-15)")
            print(f"   Found {len(july_results)} metrics in July range")
        else:
            print("❌ FAIL: Q2 2024 metric NOT found in July date range")
            print(f"   Results: {july_results}")
            return False

        # Test 2: Query for October (should find Q3 2024 with event_date=2024-10-15)
        october_results = store.get_metrics_by_date_range(
            ticker='NVDA',
            start_date='2024-10-01',
            end_date='2024-10-31',
            limit=10
        )

        q3_found = any(m.get('period') == 'Q3 2024' for m in october_results)

        if q3_found:
            print("✅ PASS: Q3 2024 metric found in October date range (event_date=2024-10-15)")
            print(f"   Found {len(october_results)} metrics in October range")
        else:
            print("❌ FAIL: Q3 2024 metric NOT found in October date range")
            return False

        # Test 3: Query for June (should NOT find Q2 or Q3)
        june_results = store.get_metrics_by_date_range(
            ticker='NVDA',
            start_date='2024-06-01',
            end_date='2024-06-30',
            limit=10
        )

        if len(june_results) == 0:
            print("✅ PASS: No metrics found in June (Q2 not announced yet)")
        else:
            print(f"⚠️  WARNING: Found {len(june_results)} metrics in June (unexpected)")

        print("\n✅ Date range query fix validated successfully")
        return True

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        store.close()
        # Clean up test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)


def test_recency_aware_ranking():
    """Test get_latest_signals_ranked combines freshness + confidence"""
    print("\n" + "=" * 70)
    print("TEST 3: Recency-Aware Signal Ranking")
    print("=" * 70)

    # Create temporary test database
    test_db_path = "data/signal_store/test_ranking_signal_store.db"
    os.makedirs("data/signal_store", exist_ok=True)

    # Clean up existing test db
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    store = SignalStore(db_path=test_db_path)

    try:
        now = datetime.now()

        # Insert test ratings with varying freshness and confidence
        test_ratings = [
            # Recent but low confidence
            {
                'ticker': 'NVDA',
                'rating': 'BUY',
                'analyst': 'Analyst A',
                'firm': 'Firm A',
                'confidence': 0.6,
                'timestamp': (now - timedelta(days=2)).isoformat(),  # Very fresh
                'source_document_id': 'test_rating_1'
            },
            # Old but high confidence
            {
                'ticker': 'NVDA',
                'rating': 'BUY',
                'analyst': 'Analyst B',
                'firm': 'Firm B',
                'confidence': 0.95,
                'timestamp': (now - timedelta(days=90)).isoformat(),  # Stale
                'source_document_id': 'test_rating_2'
            },
            # Recent and high confidence (should rank highest)
            {
                'ticker': 'NVDA',
                'rating': 'STRONG_BUY',
                'analyst': 'Analyst C',
                'firm': 'Firm C',
                'confidence': 0.90,
                'timestamp': (now - timedelta(days=5)).isoformat(),  # Fresh
                'source_document_id': 'test_rating_3'
            }
        ]

        for rating in test_ratings:
            store.insert_rating(**rating)

        print(f"📊 Inserted {len(test_ratings)} test ratings")

        # Get ranked signals (50% freshness, 50% confidence)
        ranked_signals = store.get_latest_signals_ranked(
            ticker='NVDA',
            signal_types=['rating'],
            limit=10,
            freshness_weight=0.5
        )

        print(f"\n🏆 Ranked Signals (freshness_weight=0.5):")
        for i, signal in enumerate(ranked_signals, 1):
            print(f"  {i}. {signal.get('rating', 'N/A')} by {signal.get('analyst', 'Unknown')}")
            print(f"     Composite Rank: {signal.get('composite_rank', 0):.3f}")
            print(f"     Freshness: {signal.get('freshness_score', 0):.3f}, "
                  f"Confidence: {signal.get('confidence', 0):.3f}")

        # Verify ranking logic
        if len(ranked_signals) >= 3:
            # Top signal should be recent + high confidence (Analyst C)
            top_signal = ranked_signals[0]
            if top_signal.get('analyst') == 'Analyst C':
                print("\n✅ PASS: Top signal is recent + high confidence (Analyst C)")
            else:
                print(f"\n❌ FAIL: Top signal should be Analyst C, got {top_signal.get('analyst')}")
                return False

            # Verify all signals have composite_rank
            all_have_rank = all(s.get('composite_rank') is not None for s in ranked_signals)
            if all_have_rank:
                print("✅ PASS: All signals have composite_rank")
            else:
                print("❌ FAIL: Some signals missing composite_rank")
                return False

            # Verify descending order
            ranks = [s.get('composite_rank', 0) for s in ranked_signals]
            is_descending = all(ranks[i] >= ranks[i + 1] for i in range(len(ranks) - 1))
            if is_descending:
                print("✅ PASS: Signals sorted by composite_rank DESC")
            else:
                print("❌ FAIL: Signals not properly sorted")
                return False

            print("\n✅ Recency-aware ranking validated successfully")
            return True
        else:
            print(f"❌ FAIL: Expected 3 signals, got {len(ranked_signals)}")
            return False

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        store.close()
        # Clean up test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)


def test_temporal_config():
    """Test temporal configuration parameters"""
    print("\n" + "=" * 70)
    print("TEST 4: Temporal Configuration")
    print("=" * 70)

    try:
        # Set valid test API key for config validation
        os.environ['OPENAI_API_KEY'] = 'sk-test-123456789'

        config = ICEConfig()
        temporal_status = config.get_temporal_config_status()

        print("📋 Temporal Configuration:")
        for key, value in temporal_status.items():
            print(f"  {key}: {value}")

        # Verify defaults
        expected_defaults = {
            'news_lookback_days': 7,
            'financial_lookback_days': 90,
            'freshness_half_life_days': 30,
            'stale_threshold_days': 365,
            'recency_ranking_weight': 0.5
        }

        all_correct = True
        for key, expected_value in expected_defaults.items():
            actual_value = temporal_status.get(key)
            if actual_value == expected_value:
                print(f"✅ {key}: {actual_value} (correct)")
            else:
                print(f"❌ {key}: {actual_value} (expected {expected_value})")
                all_correct = False

        if all_correct:
            print("\n✅ Temporal configuration validated successfully")
            return True
        else:
            print("\n❌ Some configuration values incorrect")
            return False

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 ICE Temporal Enhancements Test Suite (2025-11-18)")
    print("=" * 70)

    results = {
        "Event Date Inference": test_event_date_inference(),
        "Event Date Query Fix": test_event_date_date_range_query(),
        "Recency-Aware Ranking": test_recency_aware_ranking(),
        "Temporal Configuration": test_temporal_config()
    }

    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")

    total_passed = sum(1 for p in results.values() if p)
    total_tests = len(results)

    print("\n" + "=" * 70)
    if total_passed == total_tests:
        print(f"🎉 ALL TESTS PASSED ({total_passed}/{total_tests})")
        print("=" * 70)
        exit(0)
    else:
        print(f"⚠️  SOME TESTS FAILED ({total_passed}/{total_tests} passed)")
        print("=" * 70)
        exit(1)
