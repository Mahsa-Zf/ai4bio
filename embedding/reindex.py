"""Re-enable indexing for the Qdrant vector collection after bulk upload."""

from qdrant_client import QdrantClient, models


COLLECTION_NAME = "pubmed_sbiobert"


def create_qdrant_client() -> QdrantClient:
    """Create the Qdrant client used for collection maintenance.

    Returns:
        QdrantClient: Client connected to the local Qdrant server.
    """
    return QdrantClient(host="assemblix2019", port=6333)


def reindex_collection(collection_name: str = COLLECTION_NAME) -> None:
    """Re-enable HNSW indexing for a vector collection.

    Args:
        collection_name: Name of the Qdrant collection to reindex.

    Notes:
        This is intended to run after the bulk upload phase is complete. The
        indexing threshold is raised back to a normal value so Qdrant can build
        the vector index for efficient nearest-neighbor search.
    """
    client = create_qdrant_client()

    client.update_collection(
        collection_name=collection_name,
        optimizers_config=models.OptimizersConfigDiff(indexing_threshold=20000),
    )

    total = client.count(collection_name).count
    status = client.get_collection(collection_name).status
    print(f"Indexing re-enabled. Total points: {total}, status: {status}")


if __name__ == "__main__":
    reindex_collection()