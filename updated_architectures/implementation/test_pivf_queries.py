# Location: /updated_architectures/implementation/test_pivf_queries.py
# Purpose: Week 6 PIVF golden query validation
# Why: Execute 20 golden queries from ICE_VALIDATION_FRAMEWORK.md with manual scoring
# Relevant Files: ICE_VALIDATION_FRAMEWORK.md, ice_simplified.py, test_integration.py

"""
Week 6: PIVF (Portfolio Intelligence Validation Framework) Query Validation

Executes 20 golden queries from ICE_VALIDATION_FRAMEWORK.md:
- 5 Portfolio Risk queries (Q001-Q005)
- 5 Portfolio Opportunity queries (Q006-Q010)
- 5 Entity Extraction queries (Q011-Q015) - with automated F1 scoring
- 3 Multi-Hop Reasoning queries (Q016-Q018)
- 2 Comparative Analysis queries (Q019-Q020)

Generates scoring worksheet for manual 9-dimensional evaluation:
Technical (5): Relevance, Accuracy, Completeness, Actionability, Traceability
Business (4): Decision Clarity, Risk Awareness, Opportunity Recognition, Time Horizon

Target: Average score ≥7/10 (equivalent to 3.5/5.0)
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime
import csv

# Add project root to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))


# 20 Golden Queries from ICE_VALIDATION_FRAMEWORK.md
GOLDEN_QUERIES = {
    "portfolio_risk": [
        {"id": "Q001", "query": "What are the main business and market risks facing NVDA?",
         "holdings": ["NVDA"], "mode": "hybrid"},
        {"id": "Q002", "query": "What regulatory and legal risks does AAPL face?",
         "holdings": ["AAPL"], "mode": "hybrid"},
        {"id": "Q003", "query": "What are the key operational risks for TSLA's manufacturing?",
         "holdings": ["TSLA"], "mode": "hybrid"},
        {"id": "Q004", "query": "What competitive threats is GOOGL facing in search and cloud?",
         "holdings": ["GOOGL"], "mode": "hybrid"},
        {"id": "Q005", "query": "What are the main risks to MSFT's cloud growth trajectory?",
         "holdings": ["MSFT"], "mode": "hybrid"},
    ],
    "portfolio_opportunity": [
        {"id": "Q006", "query": "What are the key growth drivers and opportunities for NVDA?",
         "holdings": ["NVDA"], "mode": "global"},
        {"id": "Q007", "query": "What new product opportunities does AAPL have in AI and services?",
         "holdings": ["AAPL"], "mode": "global"},
        {"id": "Q008", "query": "What are the main growth catalysts for TSLA in 2024-2025?",
         "holdings": ["TSLA"], "mode": "global"},
        {"id": "Q009", "query": "What opportunities does GOOGL have in AI and cloud expansion?",
         "holdings": ["GOOGL"], "mode": "global"},
        {"id": "Q010", "query": "What are the key growth areas for MSFT beyond Azure?",
         "holdings": ["MSFT"], "mode": "global"},
    ],
    "entity_extraction": [
        {"id": "Q011", "query": "Extract tickers from: 'Goldman Sachs upgrades NVDA to BUY with $500 PT, downgrades INTC to SELL.'",
         "ground_truth": {"tickers": ["NVDA", "INTC"], "ratings": [{"ticker": "NVDA", "rating": "BUY"}, {"ticker": "INTC", "rating": "SELL"}]},
         "mode": "local"},
        {"id": "Q012", "query": "Extract analyst and firm from: 'John Doe at Morgan Stanley maintains OVERWEIGHT on AAPL.'",
         "ground_truth": {"analysts": [{"name": "John Doe", "firm": "Morgan Stanley"}], "tickers": ["AAPL"]},
         "mode": "local"},
        {"id": "Q013", "query": "Extract price targets from: 'Barclays raises TSLA PT to $275 from $225.'",
         "ground_truth": {"tickers": ["TSLA"], "price_targets": [{"ticker": "TSLA", "old_value": 225, "new_value": 275}]},
         "mode": "local"},
        {"id": "Q014", "query": "Extract all entities from: 'JPMorgan analyst Sarah Smith upgrades GOOGL to BUY, PT $150.'",
         "ground_truth": {"analysts": [{"name": "Sarah Smith", "firm": "JPMorgan"}], "tickers": ["GOOGL"], "ratings": [{"ticker": "GOOGL", "rating": "BUY"}]},
         "mode": "local"},
        {"id": "Q015", "query": "Extract entities from: 'Citi maintains NEUTRAL on MSFT, sees upside to $400 from Azure growth.'",
         "ground_truth": {"analysts": [{"firm": "Citi"}], "tickers": ["MSFT"], "ratings": [{"ticker": "MSFT", "rating": "NEUTRAL"}]},
         "mode": "local"},
    ],
    "multi_hop_reasoning": [
        {"id": "Q016", "query": "NVDA supplies GPUs to Microsoft Azure. How do Microsoft's cloud business risks indirectly affect my NVDA position?",
         "holdings": ["NVDA"], "expected_hops": 3, "mode": "hybrid"},
        {"id": "Q017", "query": "AAPL uses TSMC for chip manufacturing. How do TSMC's geopolitical risks affect AAPL's supply chain?",
         "holdings": ["AAPL"], "expected_hops": 2, "mode": "hybrid"},
        {"id": "Q018", "query": "GOOGL competes with MSFT in cloud and enterprise AI. How does this competitive dynamic affect both my GOOGL and MSFT holdings?",
         "holdings": ["GOOGL", "MSFT"], "expected_hops": 2, "mode": "hybrid"},
    ],
    "comparative_analysis": [
        {"id": "Q019", "query": "Compare the AI positioning of NVDA vs AMD. Which has stronger competitive moat?",
         "holdings": ["NVDA", "AMD"], "mode": "global"},
        {"id": "Q020", "query": "How correlated are AAPL, MSFT, and GOOGL in terms of regulatory risks?",
         "holdings": ["AAPL", "MSFT", "GOOGL"], "mode": "global"},
    ]
}


def run_golden_queries(ice_system):
    """Execute all 20 golden queries and save results"""
    print("\n" + "=" * 70)
    print("PIVF GOLDEN QUERY EXECUTION")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total queries: 20 across 5 categories\n")

    results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_queries": 20,
            "framework": "ICE Portfolio Intelligence Validation Framework (PIVF)"
        },
        "queries": []
    }

    query_count = 0

    # Execute each category
    for category, queries in GOLDEN_QUERIES.items():
        print(f"\n{'=' * 70}")
        print(f"Category: {category.replace('_', ' ').title()}")
        print(f"{'=' * 70}")

        for q_data in queries:
            query_count += 1
            query_id = q_data["id"]
            query_text = q_data["query"]
            mode = q_data.get("mode", "hybrid")

            print(f"\n[{query_count}/20] {query_id}: {query_text[:60]}...")

            try:
                # Execute query
                start_time = datetime.now()
                result = ice_system.core.query(query_text, mode=mode, use_graph_context=True)
                execution_time = (datetime.now() - start_time).total_seconds()

                if result.get('status') == 'success':
                    answer = result.get('answer', '')
                    sources = result.get('sources', [])

                    print(f"   ✅ Response ({len(answer)} chars, {execution_time:.2f}s)")
                    print(f"   Answer preview: {answer[:100]}...")

                    query_result = {
                        "id": query_id,
                        "category": category,
                        "query": query_text,
                        "mode": mode,
                        "response": {
                            "answer": answer,
                            "sources": sources if isinstance(sources, list) else str(sources),
                            "execution_time": execution_time,
                            "status": "success"
                        }
                    }

                    # Add ground truth for entity extraction queries
                    if category == "entity_extraction":
                        query_result["ground_truth"] = q_data.get("ground_truth", {})

                    results["queries"].append(query_result)

                else:
                    print(f"   ❌ Failed: {result.get('message', 'Unknown error')}")
                    results["queries"].append({
                        "id": query_id,
                        "category": category,
                        "query": query_text,
                        "mode": mode,
                        "response": {
                            "status": "failed",
                            "error": result.get('message', 'Unknown error')
                        }
                    })

            except Exception as e:
                print(f"   ❌ Exception: {str(e)[:80]}")
                results["queries"].append({
                    "id": query_id,
                    "category": category,
                    "query": query_text,
                    "mode": mode,
                    "response": {
                        "status": "error",
                        "error": str(e)
                    }
                })

    return results


def generate_scoring_worksheet(results, output_path):
    """Generate CSV scoring worksheet for manual 9-dimensional evaluation"""
    print("\n" + "=" * 70)
    print("GENERATING SCORING WORKSHEET")
    print("=" * 70)

    # 9 dimensions from PIVF framework
    dimensions = [
        "Relevance", "Accuracy", "Completeness", "Actionability", "Traceability",
        "Decision_Clarity", "Risk_Awareness", "Opportunity_Recognition", "Time_Horizon"
    ]

    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ["Query_ID", "Category", "Query"] + dimensions + ["Overall", "Notes"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for query_data in results["queries"]:
            row = {
                "Query_ID": query_data["id"],
                "Category": query_data["category"],
                "Query": query_data["query"][:80] + "..." if len(query_data["query"]) > 80 else query_data["query"]
            }

            # Leave scoring columns blank for manual entry
            for dim in dimensions:
                row[dim] = ""
            row["Overall"] = ""
            row["Notes"] = ""

            writer.writerow(row)

    print(f"✅ Scoring worksheet created: {output_path}")
    print(f"\nManual Scoring Instructions:")
    print(f"1. Open {output_path} in spreadsheet application")
    print(f"2. For each query, score 9 dimensions on 1-5 scale:")
    print(f"   - 5 = Excellent (exceeds expectations)")
    print(f"   - 4 = Good (high quality, actionable)")
    print(f"   - 3 = Acceptable (meets minimum bar)")
    print(f"   - 2 = Poor (major gaps)")
    print(f"   - 1 = Unusable (misleading/incorrect)")
    print(f"3. Calculate Overall = Average of 9 dimensions")
    print(f"4. Add brief notes for borderline scores")
    print(f"\nTarget: Average Overall ≥3.5/5.0 (equivalent to ≥7/10)")


def save_results(results, output_path):
    """Save query results as JSON snapshot"""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✅ Query results saved: {output_path}")


def calculate_entity_f1(results):
    """Calculate automated F1 score for entity extraction queries (Q011-Q015)"""
    import re

    print("\n" + "=" * 70)
    print("ENTITY EXTRACTION F1 SCORE (Automated)")
    print("=" * 70)

    entity_queries = [q for q in results["queries"] if q["category"] == "entity_extraction"]

    if not entity_queries:
        print("⚠️  No entity extraction queries found")
        return None

    print(f"Analyzing {len(entity_queries)} entity extraction queries...")
    print("Extracting ticker symbols from responses and comparing to ground truth\n")

    f1_scores = []
    detailed_results = []

    for query_data in entity_queries:
        query_id = query_data["id"]
        response = query_data.get("response", {})

        if response.get("status") != "success":
            print(f"   {query_id}: ⚠️  Query failed, skipping")
            continue

        # Extract tickers from ICE response
        response_text = response.get("answer", "")

        # Pattern for ticker symbols (2-5 uppercase letters, word boundaries)
        # Filter out common words that match pattern
        found_tickers_raw = set(re.findall(r'\b[A-Z]{2,5}\b', response_text))
        # Remove common false positives
        excluded_words = {'BUY', 'SELL', 'HOLD', 'NEUTRAL', 'OVERWEIGHT', 'UNDERWEIGHT',
                          'PRICE', 'TARGET', 'FROM', 'WITH', 'ANALYST', 'RATING', 'PT'}
        found_tickers = found_tickers_raw - excluded_words

        # Get ground truth tickers
        ground_truth = query_data.get("ground_truth", {})
        expected_tickers = set(ground_truth.get("tickers", []))

        # Calculate metrics
        true_positives = len(found_tickers & expected_tickers)
        false_positives = len(found_tickers - expected_tickers)
        false_negatives = len(expected_tickers - found_tickers)

        # Precision, Recall, F1
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        f1_scores.append(f1)

        status_icon = "✅" if f1 >= 0.85 else "⚠️" if f1 >= 0.70 else "❌"
        print(f"   {query_id}: {status_icon} F1={f1:.2f} | P={precision:.2f} R={recall:.2f}")
        print(f"      Found: {found_tickers}")
        print(f"      Expected: {expected_tickers}")

        detailed_results.append({
            "query_id": query_id,
            "f1": f1,
            "precision": precision,
            "recall": recall,
            "found_tickers": list(found_tickers),
            "expected_tickers": list(expected_tickers),
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives
        })

    if not f1_scores:
        print("\n⚠️  No successful entity extraction queries to score")
        return None

    avg_f1 = sum(f1_scores) / len(f1_scores)

    print(f"\n📊 Entity Extraction F1 Results:")
    print(f"   Average F1: {avg_f1:.3f}")
    print(f"   Queries analyzed: {len(f1_scores)}")
    print(f"   Min F1: {min(f1_scores):.3f}")
    print(f"   Max F1: {max(f1_scores):.3f}")

    print(f"\n🎯 Decision Gate (Modified Option 4):")
    if avg_f1 >= 0.85:
        print(f"   ✅ F1 ≥ 0.85 → Baseline sufficient")
    elif avg_f1 >= 0.70:
        print(f"   ⚠️  F1 < 0.85 → Try targeted fix")
    else:
        print(f"   ❌ F1 < 0.70 → Consider enhanced documents")

    return {
        "metric": "entity_extraction_f1",
        "average_f1": avg_f1,
        "num_queries": len(f1_scores),
        "min_f1": min(f1_scores),
        "max_f1": max(f1_scores),
        "passed": avg_f1 >= 0.85,
        "detailed_results": detailed_results
    }


def main():
    """Run PIVF golden query validation"""
    print("\n" + "=" * 70)
    print("WEEK 6: PIVF GOLDEN QUERY VALIDATION")
    print("=" * 70)
    print("Portfolio Intelligence Validation Framework")
    print("20 Golden Queries + 9-Dimensional Scoring\n")

    # Import ICE system
    from updated_architectures.implementation.ice_simplified import create_ice_system

    try:
        # Initialize ICE
        print("Initializing ICE system...")
        ice = create_ice_system()

        if not ice.is_ready():
            raise RuntimeError("ICE system not ready")

        print("✅ ICE system ready\n")

        # Create output directory
        output_dir = project_root / "validation" / "pivf_results"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Execute golden queries
        results = run_golden_queries(ice)

        # Save results snapshot
        results_path = output_dir / f"pivf_snapshot_{timestamp}.json"
        save_results(results, results_path)

        # Generate scoring worksheet
        worksheet_path = output_dir / f"pivf_scoring_{timestamp}.csv"
        generate_scoring_worksheet(results, worksheet_path)

        # Calculate entity F1 (automated component)
        calculate_entity_f1(results)

        # Summary
        print("\n" + "=" * 70)
        print("PIVF VALIDATION SUMMARY")
        print("=" * 70)

        successful = sum(1 for q in results["queries"] if q["response"].get("status") == "success")
        print(f"Queries executed: {len(results['queries'])}/20")
        print(f"Successful responses: {successful}/20")
        print(f"Success rate: {successful/20*100:.1f}%")

        print(f"\n✅ Next Steps:")
        print(f"1. Review query responses in: {results_path}")
        print(f"2. Complete manual scoring in: {worksheet_path}")
        print(f"3. Calculate average Overall score across all 20 queries")
        print(f"4. Target: Average ≥3.5/5.0 (≥7/10)")
        print(f"5. If below target, run failure analysis to identify bottlenecks")

        print("\n" + "=" * 70)
        print("Week 6 Task 2: COMPLETE")
        print("=" * 70)

        return successful == 20

    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Execution error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
