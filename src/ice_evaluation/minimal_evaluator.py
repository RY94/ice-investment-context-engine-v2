# Location: /src/ice_evaluation/minimal_evaluator.py
# Purpose: Minimal evaluation framework with defensive programming and explicit error tracking
# Why: Robust RAG evaluation for ICE without silent failures, designed for LightRAG integration
# Relevant Files: ../ice_core/ice_query_processor.py, test_queries.csv, ICE_VALIDATION_FRAMEWORK.md

import re
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MinimalEvaluationConfig:
    """Configuration for minimal evaluator - defensive defaults"""
    batch_size: int = 3  # Small batches to avoid rate limits
    max_retries: int = 2
    timeout_seconds: int = 30
    fail_fast: bool = False  # Continue on failures by default
    evaluator_model: str = "gpt-4o-mini"  # Cost-conscious default

    def validate(self):
        """Validate configuration - no silent failures"""
        if self.batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {self.batch_size}")
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {self.max_retries}")
        if self.timeout_seconds < 1:
            raise ValueError(f"timeout_seconds must be >= 1, got {self.timeout_seconds}")
        logger.info(f"✅ Configuration validated: batch_size={self.batch_size}, model={self.evaluator_model}")


@dataclass
class EvaluationResult:
    """Evaluation result with explicit success/failure tracking - no NaN hiding"""
    query_id: str
    query_text: str
    status: str  # SUCCESS, PARTIAL_SUCCESS, FAILURE
    answer: str = ""  # Store the actual answer from ICE query
    scores: Dict[str, float] = field(default_factory=dict)
    failures: Dict[str, str] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    retry_count: int = 0

    def add_metric_result(self, metric_name: str, score: Optional[float] = None, error: Optional[str] = None):
        """Add metric result with explicit success/failure tracking"""
        if score is not None and not pd.isna(score) and not (isinstance(score, float) and score != score):
            self.scores[metric_name] = score
            logger.debug(f"✅ {metric_name}: {score:.3f}")
        else:
            self.failures[metric_name] = error or "NaN or None value returned"
            logger.warning(f"❌ {metric_name} failed: {self.failures[metric_name]}")

    def compute_status(self):
        """Compute overall status based on results"""
        if not self.scores and self.failures:
            self.status = "FAILURE"
        elif self.scores and not self.failures:
            self.status = "SUCCESS"
        else:
            self.status = "PARTIAL_SUCCESS"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DataFrame - ensures all metric columns present"""
        result = {
            'query_id': self.query_id,
            'query_text': self.query_text,
            'answer': self.answer,  # Include the actual answer text
            'status': self.status,
            'execution_time_ms': self.execution_time_ms,
            'retry_count': self.retry_count,
        }

        # Ensure all standard metrics are present (None if failed)
        standard_metrics = ['faithfulness', 'relevancy', 'entity_f1']
        for metric in standard_metrics:
            result[metric] = self.scores.get(metric, None)

        # Add any additional custom metrics
        for metric, score in self.scores.items():
            if metric not in standard_metrics:
                result[metric] = score

        # Add failure information
        result['failed_metrics'] = ', '.join(self.failures.keys()) if self.failures else ''
        result['failure_reasons'] = str(self.failures) if self.failures else ''
        return result


class ICEMinimalEvaluator:
    """
    Minimal RAG evaluator with defensive programming

    Design Principles:
    1. No silent failures - every error is logged and tracked
    2. Small batch sizes - avoid rate limits
    3. Rule-based metrics - no LLM calls initially
    4. Explicit status tracking - SUCCESS/PARTIAL/FAILURE
    5. LightRAG compatible - handles graph structures
    """

    def __init__(self, config: Optional[MinimalEvaluationConfig] = None):
        self.config = config or MinimalEvaluationConfig()
        self.config.validate()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.total_queries = 0
        self.successful_queries = 0
        self.failed_queries = 0

    def evaluate_queries(self, queries: pd.DataFrame, ice_query_processor) -> pd.DataFrame:
        """
        Main evaluation entry point

        Args:
            queries: DataFrame with columns: query_id, query_text, reference (optional)
            ice_query_processor: Initialized ICE query processor for running queries

        Returns:
            DataFrame with evaluation results and explicit failure tracking
        """
        self.logger.info(f"🔍 Starting evaluation of {len(queries)} queries in batches of {self.config.batch_size}")

        # Validate input
        if 'query_id' not in queries.columns or 'query_text' not in queries.columns:
            raise ValueError("queries DataFrame must have 'query_id' and 'query_text' columns")

        results = []
        self.total_queries = len(queries)

        # Process in small batches
        for batch_idx in range(0, len(queries), self.config.batch_size):
            batch = queries.iloc[batch_idx:batch_idx + self.config.batch_size]
            self.logger.info(f"📦 Processing batch {batch_idx//self.config.batch_size + 1}/{(len(queries)-1)//self.config.batch_size + 1}")

            for _, row in batch.iterrows():
                try:
                    result = self._evaluate_single_query(row, ice_query_processor)
                    results.append(result)

                    if result.status == "SUCCESS":
                        self.successful_queries += 1
                    elif result.status == "FAILURE":
                        self.failed_queries += 1
                        if self.config.fail_fast:
                            self.logger.error(f"❌ Fail-fast enabled, stopping evaluation")
                            break

                except Exception as e:
                    self.logger.error(f"❌ Query {row['query_id']} crashed: {e}")
                    results.append(self._create_failure_result(row, str(e)))
                    self.failed_queries += 1
                    if self.config.fail_fast:
                        break

            # Rate limiting between batches
            if batch_idx + self.config.batch_size < len(queries):
                time.sleep(1)

        # Log summary
        self._log_summary()

        # Convert to DataFrame
        results_df = pd.DataFrame([r.to_dict() for r in results])
        return results_df

    def _evaluate_single_query(self, row: pd.Series, ice_query_processor) -> EvaluationResult:
        """Evaluate a single query with defensive error handling"""
        query_id = row['query_id']
        query_text = row['query_text']
        reference = row.get('reference', None)

        self.logger.info(f"🔎 Evaluating query: {query_id}")
        start_time = time.time()

        result = EvaluationResult(
            query_id=query_id,
            query_text=query_text,
            status="UNKNOWN"
        )

        try:
            # Run query through ICE
            ice_response = self._run_ice_query(query_text, ice_query_processor)

            if ice_response is None:
                result.add_metric_result("all_metrics", error="ICE query returned None")
                result.compute_status()
                return result

            # Extract answer and contexts from ICE response
            answer = self._extract_answer(ice_response)
            contexts = self._extract_contexts(ice_response)

            # Store the answer in the result object
            result.answer = answer

            # Calculate metrics (rule-based, no LLM calls)
            self._calculate_faithfulness(result, answer, contexts)
            self._calculate_relevancy(result, query_text, answer)

            # Entity F1 if reference is provided
            if reference and pd.notna(reference):
                self._calculate_entity_f1(result, answer, reference)

            result.compute_status()

        except Exception as e:
            self.logger.error(f"❌ Error evaluating {query_id}: {e}")
            result.add_metric_result("all_metrics", error=str(e))
            result.status = "FAILURE"

        result.execution_time_ms = (time.time() - start_time) * 1000
        return result

    def _run_ice_query(self, query_text: str, ice_query_processor) -> Optional[Dict]:
        """Run query through ICE query processor"""
        try:
            # ICE query processor returns Dict with 'answer' and potentially 'contexts' or graph data
            response = ice_query_processor.query(query_text, mode='hybrid')
            return response
        except Exception as e:
            self.logger.error(f"❌ ICE query failed: {e}")
            return None

    def _extract_answer(self, ice_response: Dict) -> str:
        """Extract answer text from ICE response"""
        # ICE response structure: {'answer': '...', ...}
        if 'answer' in ice_response:
            return ice_response['answer']
        elif 'response' in ice_response:
            return ice_response['response']
        else:
            self.logger.warning("⚠️ No answer/response found in ICE response")
            return ""

    def _extract_contexts(self, ice_response: Dict) -> List[str]:
        """Extract contexts from ICE response - handles LightRAG graph structures"""
        contexts = []

        # Try ICE's singular 'context' field (ICEQueryProcessor returns this)
        if 'context' in ice_response and ice_response['context']:
            # Split context string into chunks for better faithfulness scoring
            context_str = ice_response['context']
            # Split by double newlines or periods for reasonable chunks
            chunks = [chunk.strip() for chunk in context_str.split('\n\n') if chunk.strip()]
            contexts.extend(chunks)

        # Try direct contexts field (plural)
        elif 'contexts' in ice_response:
            contexts = ice_response['contexts']

        # Try parsed_context field (ICE may return this)
        elif 'parsed_context' in ice_response:
            parsed = ice_response['parsed_context']
            if isinstance(parsed, dict):
                # Extract entities and relationships from parsed context
                if 'entities' in parsed and isinstance(parsed['entities'], list):
                    for entity in parsed['entities'][:10]:  # Limit to 10
                        if isinstance(entity, dict):
                            contexts.append(str(entity))
                if 'relationships' in parsed and isinstance(parsed['relationships'], list):
                    for rel in parsed['relationships'][:10]:  # Limit to 10
                        if isinstance(rel, dict):
                            contexts.append(str(rel))

        # Try source_docs field
        elif 'source_docs' in ice_response:
            contexts = list(ice_response['source_docs'].values())

        # Try LightRAG knowledge graph structure
        elif 'kg' in ice_response:
            kg = ice_response['kg']
            if 'entities' in kg:
                for entity in kg['entities'][:5]:  # Limit to 5 entities
                    context = f"Entity: {entity.get('name', 'Unknown')}\n"
                    context += f"Description: {entity.get('description', '')}"
                    contexts.append(context)
            if 'relationships' in kg:
                for rel in kg['relationships'][:5]:  # Limit to 5 relationships
                    context = f"Relationship: {rel.get('source')} → {rel.get('relation')} → {rel.get('target')}"
                    contexts.append(context)

        if not contexts:
            self.logger.warning("⚠️ No contexts extracted from ICE response")
            self.logger.debug(f"Available keys: {list(ice_response.keys())}")

        return contexts

    def _calculate_faithfulness(self, result: EvaluationResult, answer: str, contexts: List[str]):
        """
        Calculate faithfulness score (rule-based, no LLM)
        Faithfulness = (answer words in contexts) / (total answer words)
        """
        if not answer or not contexts:
            result.add_metric_result("faithfulness", error="Empty answer or contexts")
            return

        try:
            answer_words = set(answer.lower().split())
            context_text = ' '.join(contexts).lower()
            context_words = set(context_text.split())

            overlap = len(answer_words & context_words)
            total = len(answer_words)

            score = overlap / total if total > 0 else 0.0
            result.add_metric_result("faithfulness", score)

        except Exception as e:
            result.add_metric_result("faithfulness", error=str(e))

    def _calculate_relevancy(self, result: EvaluationResult, query: str, answer: str):
        """
        Calculate relevancy score (rule-based, no LLM)
        Relevancy = (query words in answer) / (total query words)
        """
        if not query or not answer:
            result.add_metric_result("relevancy", error="Empty query or answer")
            return

        try:
            query_words = set(query.lower().split())
            answer_words = set(answer.lower().split())

            overlap = len(query_words & answer_words)
            total = len(query_words)

            score = overlap / total if total > 0 else 0.0
            result.add_metric_result("relevancy", score)

        except Exception as e:
            result.add_metric_result("relevancy", error=str(e))

    def _calculate_entity_f1(self, result: EvaluationResult, predicted: str, reference: str):
        """
        Calculate entity F1 score (deterministic, no LLM)
        Extracts ticker symbols and computes F1
        """
        if not predicted or not reference:
            result.add_metric_result("entity_f1", error="Empty predicted or reference")
            return

        try:
            # Extract ticker symbols (2-5 uppercase letters)
            pattern = r'\b[A-Z][A-Z0-9]{1,4}\b'
            predicted_entities = set(re.findall(pattern, predicted.upper()))
            reference_entities = set(re.findall(pattern, reference.upper()))

            if not reference_entities:
                result.add_metric_result("entity_f1", error="No entities in reference")
                return

            # Calculate F1
            true_positives = len(predicted_entities & reference_entities)
            false_positives = len(predicted_entities - reference_entities)
            false_negatives = len(reference_entities - predicted_entities)

            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0

            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            result.add_metric_result("entity_f1", f1)

        except Exception as e:
            result.add_metric_result("entity_f1", error=str(e))

    def _create_failure_result(self, row: pd.Series, error_message: str) -> EvaluationResult:
        """Create failure result for crashed queries"""
        result = EvaluationResult(
            query_id=row['query_id'],
            query_text=row['query_text'],
            status="FAILURE"
        )
        result.failures['crash'] = error_message
        return result

    def _log_summary(self):
        """Log evaluation summary"""
        self.logger.info("=" * 60)
        self.logger.info("📊 EVALUATION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total Queries: {self.total_queries}")
        self.logger.info(f"✅ Successful: {self.successful_queries} ({self.successful_queries/self.total_queries*100:.1f}%)")
        self.logger.info(f"⚠️ Partial: {self.total_queries - self.successful_queries - self.failed_queries}")
        self.logger.info(f"❌ Failed: {self.failed_queries} ({self.failed_queries/self.total_queries*100:.1f}%)")
        self.logger.info("=" * 60)
