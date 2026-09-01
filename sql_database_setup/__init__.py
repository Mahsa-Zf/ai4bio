"""Utilities for preparing PubMed text data and loading it into MySQL.

This package handles the ingestion pipeline that parses TSV records, splits
abstracts into sentences, and stores them in the database table used by the
embedding and search workflows.
"""
