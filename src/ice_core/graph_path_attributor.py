# Location: src/ice_core/graph_path_attributor.py
# Purpose: Attribute reasoning graph paths to source documents for traceability
# Why: Enable per-hop source attribution for multi-hop reasoning queries
# Relevant Files: ice_query_processor.py, src/ice_lightrag/context_parser.py

import logging
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)


class GraphPathAttributor:
    """
    Map multi-hop reasoning paths to source documents for granular traceability.

    Given a causal path like:
    [NVIDIA] --DEPENDS_ON--> [TSMC] --LOCATED_IN--> [Taiwan] --HAS_RISK--> [China_Tensions]

    Outputs per-hop attribution:
    [
        {
            "hop": 1,
            "path": "NVIDIA --DEPENDS_ON--> TSMC",
            "source_chunks": [chunk1, chunk2],  # Chunks supporting this relationship
            "confidence": 0.92,
            "date": "2025-08-15"
        },
        ...
    ]
    """

    def __init__(self):
        """Initialize graph path attributor"""
        pass

    def attribute_paths(
        self,
        causal_paths: List[List[Dict[str, Any]]],
        parsed_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Attribute each hop in causal paths to source chunks.

        Args:
            causal_paths: List of paths, each path is list of relationship dicts
                Example: [
                    [
                        {"entity1": "NVIDIA", "relation": "DEPENDS_ON", "entity2": "TSMC"},
                        {"entity1": "TSMC", "relation": "LOCATED_IN", "entity2": "Taiwan"}
                    ]
                ]
            parsed_context: Output from LightRAGContextParser.parse_context()

        Returns:
            List of attributed paths with per-hop source information:
            [
                {
                    "path_id": 0,
                    "path_length": 2,
                    "path_description": "NVIDIA → TSMC → Taiwan",
                    "hops": [
                        {
                            "hop_number": 1,
                            "relationship": "NVIDIA --DEPENDS_ON--> TSMC",
                            "supporting_chunks": [...],  # Chunks mentioning this edge
                            "confidence": 0.90,
                            "sources": ["email", "api"],
                            "date": "2025-08-15"
                        },
                        ...
                    ],
                    "overall_confidence": 0.85  # Min confidence across hops
                }
            ]
        """
        if not causal_paths:
            logger.debug("No causal paths to attribute")
            return []

        attributed_paths = []

        for path_idx, path in enumerate(causal_paths):
            attributed_path = self._attribute_single_path(
                path_id=path_idx,
                path=path,
                parsed_context=parsed_context
            )
            attributed_paths.append(attributed_path)

        logger.info(f"Attributed {len(attributed_paths)} causal paths")
        return attributed_paths

    def _attribute_single_path(
        self,
        path_id: int,
        path: List[Dict[str, Any]],
        parsed_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Attribute a single causal path (list of relationship hops).

        Args:
            path_id: Index of this path
            path: List of relationship dicts (each hop)
            parsed_context: Parsed context with entities, relationships, chunks

        Returns:
            {
                "path_id": 0,
                "path_length": 2,
                "path_description": "NVIDIA → TSMC → Taiwan",
                "hops": [...],
                "overall_confidence": 0.85
            }
        """
        # Extract entities from parsed context for matching
        entities = parsed_context.get('entities', [])
        relationships = parsed_context.get('relationships', [])
        chunks = parsed_context.get('chunks', [])

        # Build path description
        path_description = self._build_path_description(path)

        # Attribute each hop
        attributed_hops = []
        confidences = []

        for hop_idx, hop_relation in enumerate(path, start=1):
            entity1 = hop_relation.get('entity1', hop_relation.get('source'))
            entity2 = hop_relation.get('entity2', hop_relation.get('target'))
            relation = hop_relation.get('relation', hop_relation.get('description', 'RELATED_TO'))

            # Find chunks that mention both entities (supporting evidence)
            supporting_chunks = self._find_supporting_chunks(
                entity1=entity1,
                entity2=entity2,
                chunks=chunks
            )

            # Calculate hop confidence (from supporting chunks)
            hop_confidence = self._calculate_hop_confidence(supporting_chunks)
            confidences.append(hop_confidence)

            # Extract source types from supporting chunks
            sources = list(set([c.get('source_type', 'unknown') for c in supporting_chunks]))

            # Get most recent date from supporting chunks
            dates = [c.get('date') for c in supporting_chunks if c.get('date')]
            most_recent_date = max(dates) if dates else None

            attributed_hop = {
                "hop_number": hop_idx,
                "relationship": f"{entity1} --{relation}--> {entity2}",
                "entity1": entity1,
                "relation": relation,
                "entity2": entity2,
                "supporting_chunks": supporting_chunks,
                "num_supporting_chunks": len(supporting_chunks),
                "confidence": hop_confidence,
                "sources": sources,
                "date": most_recent_date
            }
            attributed_hops.append(attributed_hop)

        # Overall path confidence = minimum hop confidence (weakest link)
        overall_confidence = min(confidences) if confidences else 0.50

        return {
            "path_id": path_id,
            "path_length": len(path),
            "path_description": path_description,
            "hops": attributed_hops,
            "overall_confidence": round(overall_confidence, 2)
        }

    def _build_path_description(self, path: List[Dict[str, Any]]) -> str:
        """
        Build human-readable path description.

        Example: "NVIDIA → TSMC → Taiwan → China_Tensions"
        """
        if not path:
            return ""

        entities = []

        # Extract entity sequence from path
        for hop in path:
            entity1 = hop.get('entity1', hop.get('source'))
            if entity1 and entity1 not in entities:
                entities.append(entity1)

            entity2 = hop.get('entity2', hop.get('target'))
            if entity2 and entity2 not in entities:
                entities.append(entity2)

        return " → ".join(entities)

    def _find_supporting_chunks(
        self,
        entity1: str,
        entity2: str,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find chunks that mention both entities (supporting evidence for this hop).

        Args:
            entity1: First entity in relationship
            entity2: Second entity in relationship
            chunks: List of chunks from parsed context

        Returns:
            List of chunks that mention both entities
        """
        if not entity1 or not entity2:
            return []

        supporting_chunks = []

        # Normalize entity names for matching
        entity1_lower = entity1.lower()
        entity2_lower = entity2.lower()

        for chunk in chunks:
            content = chunk.get('content', '').lower()

            # Check if both entities mentioned in this chunk
            if entity1_lower in content and entity2_lower in content:
                supporting_chunks.append(chunk)

        logger.debug(
            f"Found {len(supporting_chunks)} chunks supporting "
            f"{entity1} → {entity2}"
        )

        return supporting_chunks

    def _calculate_hop_confidence(self, supporting_chunks: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence for a single hop based on supporting chunks.

        Strategy:
        - 0 chunks = 0.40 (low confidence, inferred relationship)
        - 1 chunk = chunk's confidence
        - 2+ chunks = average confidence, boosted by redundancy

        Args:
            supporting_chunks: Chunks supporting this relationship hop

        Returns:
            Confidence score (0.0-1.0)
        """
        if not supporting_chunks:
            # No direct evidence, relationship may be inferred by graph traversal
            return 0.40

        # Extract confidence scores from chunks
        chunk_confidences = [
            c.get('confidence', 0.70)
            for c in supporting_chunks
        ]

        if len(supporting_chunks) == 1:
            # Single source, use its confidence
            return chunk_confidences[0]
        else:
            # Multiple sources, average + redundancy boost
            avg_confidence = sum(chunk_confidences) / len(chunk_confidences)

            # Redundancy boost: +0.05 per additional chunk (max +0.15)
            redundancy_boost = min(0.15, (len(supporting_chunks) - 1) * 0.05)

            final_confidence = min(1.0, avg_confidence + redundancy_boost)
            return round(final_confidence, 2)

    def format_attributed_path(self, attributed_path: Dict[str, Any]) -> str:
        """
        Format attributed path for human-readable display.

        Args:
            attributed_path: Output from _attribute_single_path()

        Returns:
            Formatted string like:
            ```
            Path: NVIDIA → TSMC → Taiwan (Confidence: 0.85)

            Hop 1: NVIDIA --DEPENDS_ON--> TSMC
               Sources: email (0.90), api (0.85)
               Date: 2025-08-15
               Supporting chunks: 2

            Hop 2: TSMC --LOCATED_IN--> Taiwan
               Sources: email (0.88)
               Date: 2025-08-12
               Supporting chunks: 1
            ```
        """
        lines = []

        # Path header
        lines.append(f"Path: {attributed_path['path_description']} "
                     f"(Confidence: {attributed_path['overall_confidence']})")
        lines.append("")

        # Each hop
        for hop in attributed_path['hops']:
            lines.append(f"Hop {hop['hop_number']}: {hop['relationship']}")
            lines.append(f"   Sources: {', '.join(hop['sources'])}")
            lines.append(f"   Confidence: {hop['confidence']}")
            lines.append(f"   Date: {hop.get('date', 'N/A')}")
            lines.append(f"   Supporting chunks: {hop['num_supporting_chunks']}")
            lines.append("")

        return "\n".join(lines)


# Export for use in ICE modules
__all__ = ['GraphPathAttributor']
