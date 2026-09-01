"""Create and prepare the Qdrant collection used for sentence embeddings."""

from qdrant_client import QdrantClient, models

COLLECTION_NAME = "pubmed_sbiobert_v2"
DIM = 768  # S-BioBERT embedding size


def main() -> None:
    """Create the Qdrant collection and disable automatic indexing for bulk load.

    The collection is created once, with a cosine-distance vector configuration
    matching the S-BioBERT embedding dimension. Automatic indexing is disabled to
    speed up the initial bulk insert phase, after which indexing can be turned
    back on for query performance.
    """
    client = QdrantClient(host="assemblix2019", port=6333)

    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=DIM,
                distance=models.Distance.COSINE,
                datatype=models.Datatype.FLOAT16,
                on_disk=False,
            ),
            on_disk_payload=True,
        )
        print(f"Created collection '{COLLECTION_NAME}'")
    else:
        print(f"Collection '{COLLECTION_NAME}' already exists")

    client.update_collection(
        collection_name=COLLECTION_NAME,
        optimizers_config=models.OptimizersConfigDiff(indexing_threshold=0),
    )
    print("Indexing disabled — ready for bulk load.")


if __name__ == "__main__":
    main()