"""Embedding utilities for creating and indexing sentence embeddings.

This package contains the workflow used to read PubMed sentences from MySQL,
encode them with a SentenceTransformer model, upload vectors to Qdrant, and
re-enable indexing after the bulk-load phase completes.
"""
