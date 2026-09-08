.. Ai4Bio documentation master file, created by
   sphinx-quickstart on Tue Sep  1 22:59:14 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Ai4Bio documentation
====================

This project prepares PubMed text for semantic search by splitting abstracts into
sentences, storing them in MySQL, encoding them with a biomedical sentence
transformer, and querying the resulting embeddings in Qdrant.

Package overview
----------------

- ``sql_database_setup``: parses TSV records and inserts sentence rows into the
  database.
- ``qdrant_database_setup``: creates and configures the Qdrant collection for
  bulk embedding uploads.
- ``embedding``: loads sentence rows, encodes them into vectors, and uploads them
  to the vector database.
- ``query``: embeds a query string and searches for similar sentences in Qdrant.


.. toctree::
   :caption: Ai4Bio API

   api/modules