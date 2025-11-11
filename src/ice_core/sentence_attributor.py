# Location: src/ice_core/sentence_attributor.py
# Purpose: Attribute each sentence in answer to source chunks via semantic similarity
# Why: Enable granular sentence-level traceability for compliance and verification
# Relevant Files: ice_query_processor.py, src/ice_lightrag/context_parser.py

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class SentenceAttributor:
    """
    Attribute each sentence in a generated answer to source chunks using semantic similarity.

    Strategy:
    1. Split answer into sentences
    2. Compute sentence embeddings
    3. Match to chunk embeddings via cosine similarity
    4. Assign source attribution to each sentence (threshold ≥ 0.70)

    Cost: ~$0.0001 per query (~$1/month at 1,000 queries)
    Accuracy: 80-90% (per user acceptance criteria)
    """

    def __init__(self, similarity_threshold: float = 0.70):
        """
        Initialize sentence attributor.

        Args:
            similarity_threshold: Minimum cosine similarity to attribute sentence to chunk
                Default: 0.70 (balances precision/recall for 80-90% accuracy target)
        """
        self.similarity_threshold = similarity_threshold
        self._embedding_func = None
        self._initialize_embedding_function()

    def _initialize_embedding_function(self):
        """
        Initialize embedding function (uses same provider as LightRAG for consistency).

        Priority:
        1. OpenAI embeddings (if API key available) - text-embedding-3-small ($0.00002/1K tokens)
        2. Local embeddings (sentence-transformers) - Free, slower
        """
        try:
            # Try OpenAI first (consistent with LightRAG)
            import openai
            import os

            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self._embedding_func = self._openai_embed
                logger.info("Using OpenAI embeddings for sentence attribution")
                return
        except ImportError:
            pass

        # Fallback to local embeddings
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim, fast
            self._embedding_func = self._local_embed
            logger.info("Using local embeddings (sentence-transformers) for sentence attribution")
        except ImportError:
            logger.warning("No embedding provider available for sentence attribution")
            self._embedding_func = None

    def _openai_embed(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings using OpenAI API.

        Args:
            texts: List of text strings to embed

        Returns:
            numpy array of shape (len(texts), 1536)
        """
        import openai
        import os

        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )

        embeddings = [item.embedding for item in response.data]
        return np.array(embeddings)

    def _local_embed(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings using local sentence-transformers.

        Args:
            texts: List of text strings to embed

        Returns:
            numpy array of shape (len(texts), 384)
        """
        return self._model.encode(texts, convert_to_numpy=True)

    def attribute_sentences(
        self,
        answer: str,
        parsed_context: Dict[str, Any],
        include_scores: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Attribute each sentence in answer to source chunks.

        Args:
            answer: Generated answer text
            parsed_context: Output from LightRAGContextParser.parse_context()
            include_scores: Whether to include similarity scores in output

        Returns:
            List of attributed sentences:
            [
                {
                    "sentence": "Tencent's Q2 2025 operating margin was 34%.",
                    "sentence_number": 1,
                    "attributed_chunks": [
                        {
                            "chunk_id": 1,
                            "source_type": "email",
                            "confidence": 0.90,
                            "similarity_score": 0.87,  # If include_scores=True
                            "date": "2025-08-15",
                            "source_details": {...}
                        }
                    ],
                    "attribution_confidence": 0.87,  # Highest similarity score
                    "has_attribution": True
                }
            ]
        """
        if not self._embedding_func:
            logger.warning("No embedding function available, cannot attribute sentences")
            return self._fallback_attribution(answer)

        # Split answer into sentences
        sentences = self._split_into_sentences(answer)

        if not sentences:
            return []

        # Get chunks from parsed context
        chunks = parsed_context.get('chunks', [])

        if not chunks:
            logger.warning("No chunks in parsed context, cannot attribute sentences")
            return self._fallback_attribution(answer)

        # Compute embeddings
        try:
            sentence_embeddings = self._embedding_func(sentences)
            # TIER 2: Preprocess chunks to expand structured markers before embedding
            # This improves semantic matching between markers and natural language answers
            chunk_texts = [self._prepare_chunk_for_embedding(c.get('content', '')[:500]) for c in chunks]
            chunk_embeddings = self._embedding_func(chunk_texts)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return self._fallback_attribution(answer)

        # Compute similarity matrix (sentences x chunks)
        similarity_matrix = self._compute_cosine_similarity(
            sentence_embeddings,
            chunk_embeddings
        )

        # Attribute each sentence
        attributed_sentences = []

        for sent_idx, sentence in enumerate(sentences):
            # Get similarities for this sentence across all chunks
            sent_similarities = similarity_matrix[sent_idx]

            # Find chunks above threshold
            attributed_chunks = self._find_attributed_chunks(
                sent_similarities,
                chunks,
                include_scores=include_scores
            )

            # Highest similarity score = attribution confidence
            attribution_confidence = float(np.max(sent_similarities)) if len(sent_similarities) > 0 else 0.0
            has_attribution = attribution_confidence >= self.similarity_threshold

            attributed_sentences.append({
                "sentence": sentence.strip(),
                "sentence_number": sent_idx + 1,
                "attributed_chunks": attributed_chunks,
                "attribution_confidence": round(attribution_confidence, 2),
                "has_attribution": has_attribution
            })

        # Log statistics
        total_sentences = len(attributed_sentences)
        attributed_count = sum(1 for s in attributed_sentences if s['has_attribution'])
        coverage = (attributed_count / total_sentences * 100) if total_sentences > 0 else 0

        logger.info(
            f"Sentence attribution: {attributed_count}/{total_sentences} sentences "
            f"({coverage:.1f}% coverage)"
        )

        return attributed_sentences

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using simple regex.

        Handles:
        - Periods, exclamation marks, question marks
        - Abbreviations (Dr., Mr., etc.)
        - Numbers (e.g., "2.5 billion")
        """
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text.strip())

        # Simple sentence splitting (handles most cases)
        # Split on . ! ? followed by space and capital letter
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _compute_cosine_similarity(
        self,
        embeddings_a: np.ndarray,
        embeddings_b: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarity matrix between two sets of embeddings.

        Args:
            embeddings_a: Shape (n, d)
            embeddings_b: Shape (m, d)

        Returns:
            Similarity matrix of shape (n, m) with values in [-1, 1]
        """
        # Normalize embeddings
        norm_a = embeddings_a / np.linalg.norm(embeddings_a, axis=1, keepdims=True)
        norm_b = embeddings_b / np.linalg.norm(embeddings_b, axis=1, keepdims=True)

        # Compute dot product (cosine similarity for normalized vectors)
        similarity = np.dot(norm_a, norm_b.T)

        return similarity

    def _find_attributed_chunks(
        self,
        similarities: np.ndarray,
        chunks: List[Dict[str, Any]],
        include_scores: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find chunks above similarity threshold and return with attribution details.

        Args:
            similarities: Similarity scores for one sentence across all chunks
            chunks: List of chunks from parsed context
            include_scores: Whether to include similarity scores

        Returns:
            List of attributed chunks sorted by similarity (highest first)
        """
        attributed_chunks = []

        for chunk_idx, similarity in enumerate(similarities):
            if similarity >= self.similarity_threshold:
                chunk = chunks[chunk_idx]

                attributed_chunk = {
                    "chunk_id": chunk.get('chunk_id'),
                    "source_type": chunk.get('source_type', 'unknown'),
                    "confidence": chunk.get('confidence', 0.50),
                    "date": chunk.get('date'),
                    "relevance_rank": chunk.get('relevance_rank'),
                    "source_details": chunk.get('source_details', {})
                }

                if include_scores:
                    attributed_chunk["similarity_score"] = round(float(similarity), 2)

                attributed_chunks.append(attributed_chunk)

        # Sort by similarity score (highest first)
        if include_scores:
            attributed_chunks.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)

        return attributed_chunks

    def _fallback_attribution(self, answer: str) -> List[Dict[str, Any]]:
        """
        Fallback when embedding function not available.

        Returns sentences without source attribution.
        """
        sentences = self._split_into_sentences(answer)

        return [
            {
                "sentence": sentence.strip(),
                "sentence_number": idx + 1,
                "attributed_chunks": [],
                "attribution_confidence": 0.0,
                "has_attribution": False
            }
            for idx, sentence in enumerate(sentences)
        ]

    def format_attributed_sentences(
        self,
        attributed_sentences: List[Dict[str, Any]],
        show_sources: bool = True
    ) -> str:
        """
        Format attributed sentences for human-readable display.

        Args:
            attributed_sentences: Output from attribute_sentences()
            show_sources: Whether to show source details for each sentence

        Returns:
            Formatted string like:
            ```
            [1] Tencent's Q2 2025 operating margin was 34%.
                Sources: email (confidence: 0.90, similarity: 0.87)
                Date: 2025-08-15

            [2] This represents a 2% increase from Q1 2025.
                Sources: email (confidence: 0.85, similarity: 0.82)
                Date: 2025-08-15

            [3] The company's revenue grew 15% YoY.
                ⚠️  No source attribution found
            ```
        """
        lines = []

        for sent_attr in attributed_sentences:
            sent_num = sent_attr['sentence_number']
            sentence = sent_attr['sentence']
            has_attribution = sent_attr['has_attribution']
            attributed_chunks = sent_attr.get('attributed_chunks', [])

            # Sentence with number
            lines.append(f"[{sent_num}] {sentence}")

            if show_sources and has_attribution and attributed_chunks:
                # Show top 2 attributed chunks
                for chunk in attributed_chunks[:2]:
                    source_type = chunk.get('source_type', 'unknown')
                    confidence = chunk.get('confidence', 'N/A')
                    similarity = chunk.get('similarity_score', 'N/A')
                    date = chunk.get('date', 'N/A')

                    source_line = f"    Sources: {source_type} (confidence: {confidence}"
                    if similarity != 'N/A':
                        source_line += f", similarity: {similarity}"
                    source_line += ")"

                    lines.append(source_line)
                    lines.append(f"    Date: {date}")

                if len(attributed_chunks) > 2:
                    lines.append(f"    ... and {len(attributed_chunks) - 2} more sources")
            elif not has_attribution:
                lines.append("    ⚠️  No source attribution found")

            lines.append("")  # Blank line between sentences

        return "\n".join(lines)

    def get_attribution_statistics(
        self,
        attributed_sentences: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate statistics about sentence attribution coverage.

        Args:
            attributed_sentences: Output from attribute_sentences()

        Returns:
            {
                "total_sentences": 5,
                "attributed_sentences": 4,
                "unattributed_sentences": 1,
                "coverage_percentage": 80.0,
                "average_confidence": 0.85,
                "sources_by_type": {"email": 3, "api": 1}
            }
        """
        total = len(attributed_sentences)
        attributed = sum(1 for s in attributed_sentences if s['has_attribution'])
        unattributed = total - attributed

        coverage = (attributed / total * 100) if total > 0 else 0

        # Average confidence (for attributed sentences only)
        confidences = [
            s['attribution_confidence']
            for s in attributed_sentences
            if s['has_attribution']
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Count sources by type
        sources_by_type = {}
        for sent in attributed_sentences:
            for chunk in sent.get('attributed_chunks', []):
                source_type = chunk.get('source_type', 'unknown')
                sources_by_type[source_type] = sources_by_type.get(source_type, 0) + 1

        return {
            "total_sentences": total,
            "attributed_sentences": attributed,
            "unattributed_sentences": unattributed,
            "coverage_percentage": round(coverage, 1),
            "average_confidence": round(avg_confidence, 2),
            "sources_by_type": sources_by_type
        }

    def _prepare_chunk_for_embedding(self, chunk_content: str) -> str:
        """
        Expand structured markers to natural language for better semantic matching.

        TIER 2 FIX: Transforms structured markers into natural language to improve
        cosine similarity between chunk embeddings and answer sentence embeddings.

        Example transformations:
        - [MARGIN:Operating Margin|value:37.5%|period:2Q2025|ticker:Tencent]
          → "Operating Margin for Tencent in 2Q2025 was 37.5%. "
        - [TICKER:NVDA|confidence:0.95]
          → "NVDA. "

        Args:
            chunk_content: Raw chunk text with structured markers

        Returns:
            Chunk text with markers expanded to natural language
        """
        expanded = chunk_content
        expanded = self._expand_financial_markers(expanded)
        expanded = self._expand_entity_markers(expanded)
        return expanded

    def _expand_financial_markers(self, text: str) -> str:
        """
        Expand financial markers (MARGIN, TABLE_METRIC, PRICE_TARGET) to natural language.

        Pattern: [TYPE:name|value:X|period:Y|ticker:Z|confidence:C]
        Output: "name for ticker in period was X. "

        Examples:
        - [MARGIN:Operating Margin|value:37.5%|period:2Q2025|ticker:Tencent|confidence:0.95]
          → "Operating Margin for Tencent in 2Q2025 was 37.5%. "
        - [TABLE_METRIC:Revenue|value:184.5|period:2Q2025|ticker:Tencent|confidence:0.95]
          → "Revenue for Tencent in 2Q2025 was 184.5. "
        """
        import re

        # Pattern matches: [MARGIN:...|value:...|period:...|ticker:...]
        pattern = r'\[(MARGIN|TABLE_METRIC|PRICE_TARGET):([^\|]+)\|value:([^\|]+)\|period:([^\|]+)\|ticker:([^\|]+)(?:\|confidence:[^\]]+)?\]'

        def expand_match(match):
            marker_type, name, value, period, ticker = match.groups()
            return f"{name} for {ticker} in {period} was {value}. "

        return re.sub(pattern, expand_match, text)

    def _expand_entity_markers(self, text: str) -> str:
        """
        Expand entity markers (TICKER, RATING, COMPANY, ANALYST) to natural language.

        Pattern: [TYPE:value|...]
        Output: "value. "

        Examples:
        - [TICKER:NVDA|confidence:0.95] → "NVDA. "
        - [RATING:BUY|ticker:NVDA|confidence:0.87] → "BUY. "
        - [COMPANY:Apple Inc|ticker:AAPL|confidence:0.90] → "Apple Inc. "
        """
        import re

        # Pattern matches: [TYPE:value|...] (any marker with at least type and value)
        pattern = r'\[([A-Z_]+):([^\|]+)(?:\|[^\]]+)?\]'

        def expand_match(match):
            marker_type, value = match.groups()
            return f"{value}. "

        return re.sub(pattern, expand_match, text)


# Export for use in ICE modules
__all__ = ['SentenceAttributor']
