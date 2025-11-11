# Location: /src/ice_evaluation/__init__.py
# Purpose: ICE evaluation framework - minimal, defensive, no silent failures
# Why: Automated RAG evaluation with explicit error tracking for ICE solution
# Relevant Files: minimal_evaluator.py

from .minimal_evaluator import ICEMinimalEvaluator, MinimalEvaluationConfig

__all__ = ['ICEMinimalEvaluator', 'MinimalEvaluationConfig']
