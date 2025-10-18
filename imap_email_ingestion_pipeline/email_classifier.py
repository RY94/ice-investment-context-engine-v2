# Location: /imap_email_ingestion_pipeline/email_classifier.py
# Purpose: Simple 2-tier email classification (whitelist + vector similarity)
# Why: Replace keyword filtering with semantic similarity for better investment email detection
# Relevant Files: process_emails.py (integration point)

import numpy as np
from typing import Tuple

# Lazy import to avoid startup overhead if not used
_MODEL = None
_INV_EMB = None
_NON_INV_EMB = None

# Tier 1: Trusted financial domains (instant classification)
WHITELIST_DOMAINS = [
    'bloomberg.com', 'reuters.com', 'marketwatch.com', 'cnbc.com', 'wsj.com',
    'goldmansachs.com', 'jpmorgan.com', 'morganstanley.com', 'barclays.com',
    'ubs.com', 'citi.com', 'dbs.com', 'uobkayhian.com', 'ocbc.com',
    'agtpartners.com.sg', 'research.com', 'analyst.com'
]

# Tier 2: Reference examples for vector similarity
INVESTMENT_EXAMPLES = [
    "Goldman Sachs upgrades NVDA to BUY with price target $500. Strong AI demand.",
    "Q3 2024 earnings beat estimates. EPS $1.25 vs $1.10 expected. Revenue up 45%.",
    "JPMorgan analyst raises price target on AAPL citing iPhone sales momentum.",
    "Market update: Tech sector rally continues. Semiconductor stocks surge on AI chip demand.",
    "Portfolio alert: TSMC announces capex expansion. Supply chain diversification positive."
]

NON_INVESTMENT_EXAMPLES = [
    "Your Amazon order has shipped. Track your package: ORDER-12345. Delivery Friday.",
    "Meeting reminder: Team standup at 10 AM tomorrow. Conference room B.",
    "IT password reset required. Your password expires in 3 days. Click here to update.",
    "Flight booking confirmed: SQ123 Singapore to Tokyo. Departure Dec 15 9:30 AM.",
    "Dinner plans tonight? Let's meet at the Italian restaurant at 7 PM."
]


def _init_model():
    """Initialize sentence-transformers model and reference embeddings (lazy load)"""
    global _MODEL, _INV_EMB, _NON_INV_EMB

    if _MODEL is not None:
        return

    try:
        from sentence_transformers import SentenceTransformer

        # Load lightweight model (80MB, auto-downloads on first run)
        _MODEL = SentenceTransformer('all-MiniLM-L6-v2')

        # Compute reference embeddings (one-time cost)
        inv_embeddings = _MODEL.encode(INVESTMENT_EXAMPLES)
        non_inv_embeddings = _MODEL.encode(NON_INVESTMENT_EXAMPLES)

        # Average multiple examples to create prototype embeddings
        _INV_EMB = np.mean(inv_embeddings, axis=0)
        _NON_INV_EMB = np.mean(non_inv_embeddings, axis=0)

    except ImportError:
        raise ImportError(
            "sentence-transformers not installed. "
            "Install with: pip install sentence-transformers"
        )


def classify_email(subject: str, body: str, sender: str) -> Tuple[str, float]:
    """
    Classify email as INVESTMENT or NON_INVESTMENT

    Two-tier system:
      1. Whitelist: Instant classification for known financial domains
      2. Vector Similarity: Semantic comparison to reference examples

    Args:
        subject: Email subject line
        body: Email body text
        sender: Email sender address

    Returns:
        Tuple of (classification, confidence)
        - classification: 'INVESTMENT' or 'NON_INVESTMENT'
        - confidence: 0.0-1.0 similarity score
    """
    # Tier 1: Whitelist check (instant)
    sender_lower = sender.lower()
    if any(domain in sender_lower for domain in WHITELIST_DOMAINS):
        return ('INVESTMENT', 1.0)

    # Tier 2: Vector similarity
    _init_model()  # Lazy load model

    # Combine subject and body preview (limit to 500 chars for speed)
    text = f"{subject}\n{body[:500]}"

    # Get embedding for email
    email_embedding = _MODEL.encode([text])[0]

    # Compute cosine similarity to both prototypes
    inv_similarity = np.dot(email_embedding, _INV_EMB) / (
        np.linalg.norm(email_embedding) * np.linalg.norm(_INV_EMB)
    )
    non_inv_similarity = np.dot(email_embedding, _NON_INV_EMB) / (
        np.linalg.norm(email_embedding) * np.linalg.norm(_NON_INV_EMB)
    )

    # Return class with higher similarity
    if inv_similarity > non_inv_similarity:
        return ('INVESTMENT', float(inv_similarity))
    else:
        return ('NON_INVESTMENT', float(non_inv_similarity))
