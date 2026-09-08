#!/usr/bin/env python3
"""Search PubMed sentences by semantic similarity with Qdrant."""

import argparse
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
from sqlalchemy import create_engine, text


COLLECTION_NAME = "pubmed_sbiobert_v2"
MODEL_NAME = "pritamdeka/S-BioBert-snli-multinli-stsb"


def load_engine():
    """Create the SQLAlchemy engine used to look up sentence metadata.

    Returns:
        sqlalchemy.engine.Engine: Database engine loaded from the local
        mysql.txt credentials file.
    """
    with open("mysql.txt", encoding="utf-8") as f:
        return create_engine(f.read().strip(), pool_pre_ping=True)


def search(model, client, sentence, k, threshold):
    """Query Qdrant for the nearest matching sentences to a natural-language input.

    Args:
        model: Sentence-transformer model used to encode the query text.
        client: Qdrant client connected to the vector collection.
        sentence: Query sentence to embed and search for.
        k: Number of nearest matches to return.
        threshold: Optional cosine similarity minimum; values below this are
            filtered out.

    Returns:
        list: Qdrant result points containing sentence IDs and similarity scores.
    """
    vec = model.encode(sentence, normalize_embeddings=True).tolist()
    return client.query_points(
        collection_name=COLLECTION_NAME,
        query=vec,
        limit=k,
        score_threshold=threshold,
        with_payload=False,
        with_vectors=False,
        search_params=models.SearchParams(hnsw_ef=100),
    ).points


def fetch_rows(ids, engine):
    """Look up sentence metadata for a list of sentence IDs.

    Args:
        ids: Sequence of sentence IDs to resolve.
        engine: SQLAlchemy engine connected to the MySQL database.

    Returns:
        dict: Mapping from sentence_id to a tuple of (pubmed_id, sentence).
    """
    if not ids:
        return {}
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT sentence_id, pubmed_id, sentence "
                "FROM sentences WHERE sentence_id IN :ids"
            ),
            {"ids": tuple(ids)},
        ).all()
    return {r.sentence_id: (r.pubmed_id, r.sentence) for r in rows}


def show(points, engine):
    """Print a ranked Qdrant result set with the associated PMID and sentence text.

    Args:
        points: Sequence of Qdrant points returned by the query.
        engine: SQLAlchemy engine used to rehydrate the original text.
    """
    if not points:
        print("  (no matches)")
        return
    lookup = fetch_rows([p.id for p in points], engine)
    for p in points:
        pmid, sentence = lookup.get(p.id, ("?", "<not found in DB>"))
        print(f"  {p.score:.3f}  [PMID {pmid}]  {sentence}")


def main():
    """Run the command-line semantic search interface."""
    ap = argparse.ArgumentParser(
        description="Search PubMed sentences by similarity."
    )
    ap.add_argument(
        "query", nargs="?", help="Query sentence. Omit for interactive mode."
    )
    ap.add_argument(
        "-k",
        "--top-k",
        type=int,
        default=5,
        help="Number of results (default 5).",
    )
    ap.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=None,
        help="Min cosine score, e.g. 0.6.",
    )
    ap.add_argument("--host", default="assemblix2019")
    ap.add_argument("--port", type=int, default=6333)
    args = ap.parse_args()

    print("Loading model...")
    model = SentenceTransformer(MODEL_NAME)
    client = QdrantClient(host=args.host, port=args.port, timeout=180)
    engine = load_engine()

    if args.query:
        points = search(model, client, args.query, args.top_k, args.threshold)
        show(points, engine)
    else:
        print(
            "Interactive search: type a sentence, Enter to search. "
            "'quit' or Ctrl-D to exit."
        )
        while True:
            q = input("\nquery> ").strip()
            if not q:
                continue
            if q.lower() in {"quit", "exit"}:
                print("bye"); break
            # to make the interactive mode more robust against time out errors
            # catch any exceptions and allow the user to try again without restarting the program
            try:
                points = search(model, client, q, args.top_k, args.threshold)
                show(points, engine)
            except Exception as exc:
                print(f"Query failed: {exc}")
                print("You can try another query.")


if __name__ == "__main__":
    main()


# one-shot
# python query_qdrant.py "SARS-CoV-2 spike protein antibody binding" -k 15


# top 10, only matches scoring >= 0.6
# python query_qdrant.py "surgical strategy in difficult cholecystectomy" -k 10 -t 0.6


# interactive: model loads once, then ask as many as you like
# python query_qdrant.py


# "what are the protein binding ligands for CXCR3"
# "CXCR3 expression in regulatory T cells"