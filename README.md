# ai4bio

Tool for biomedical data workflows. Embedding about 300 million abstract sentences gathered from over 40 million pubmed articles in a Qdrant vectorized database for semantic search and enabling future developement.

Documentation site: https://mahsa-zf.github.io/ai4bio/

## Features
- SQL database setup utilities (sql_database_setup/)
- Qdrant setup and integration helpers (qdrant_database_setup/)
- Produce embeddings from data (embedding/)
- Reindexing utilities to rebuild embedding indexes (embedding/reindex.py)
- Example query code for Qdrant (query/)


## Quickstart

Prerequisites
- Python 3.10+
- (Optional) Qdrant running for vector DB features

Setup

1. Create and activate a virtual environment:

```
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```
pip install -r requirements.txt
```

If your environment requires additional packages, install them as needed.

## Repository layout

- sql_database_setup/ — helper to create a SQL dataset with sentences as rows for over 40 million pubmed abstracts.
- qdrant_database_setup/ — scripts to initialize and configure Qdrant collections.
- embedding/ — embedding and reindex scripts for encoding the sentences.
- query/ — example query clients against Qdrant for semantic search.
- docs/ — Sphinx documentation and API references.


Note: each script may accept configuration via environment variables or command-line args; run `--help` for details.

## Documentation
See the rendered docs in the `docs/` directory. To build locally:

```
cd docs
make html
```

## Development
- Follow the Quickstart to set up a venv
- Run the scripts in the `sql_database_setup/`,`qdrant_database_setup/`, `embedding/` and `query/` folders
