"""Embed PubMed sentences into vectors and upload them to Qdrant.

This module runs as a worker in a SLURM array. Each process is assigned a
subset of sentence IDs, reads rows from MySQL, encodes them with a sentence
transformer, and writes vectors to Qdrant while checkpointing its progress.
"""

import os
import torch
import pandas as pd
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
from qdrant_client import QdrantClient


COLLECTION_NAME = "pubmed_sbiobert_v2"
MODEL_NAME = "pritamdeka/S-BioBert-snli-multinli-stsb"
CHUNK_SIZE = 100_000  # rows read + encoded per page


def get_device_and_batch_size():
    """Return the best available compute device and embedding batch size.

    Returns:
        tuple[str, int]: The device name and a batch size suited to that device.
    """
    if torch.cuda.is_available():
        return "cuda", 256
    if torch.backends.mps.is_available():
        return "mps", 64
    return "cpu", 64


def set_num_threads():
    """Configure the number of CPU threads used by PyTorch.

    The value is taken from the SLURM task environment when available; otherwise
    it falls back to the default CPU count. This helps SentenceTransformers make
    efficient use of CPU resources during embedding.
    """
    torch.set_num_threads(
        int(os.environ.get("SLURM_CPUS_PER_TASK", os.cpu_count() or 1))
    )


def load_engine():
    """Create and return a SQLAlchemy engine configured for MySQL.

    Returns:
        sqlalchemy.engine.Engine: A SQLAlchemy engine connected to the database
        described in the local mysql.txt file.
    """
    with open("mysql.txt", encoding="utf-8") as f:
        return create_engine(f.read().strip(), pool_pre_ping=True)


def get_id_range(engine, task_id: int, num_tasks: int):
    """Compute the sentence ID slice assigned to a worker.

    Args:
        engine: SQLAlchemy engine for the MySQL database.
        task_id: Index of the current worker in the SLURM array.
        num_tasks: Total number of workers in the array.

    Returns:
        tuple[int, int]: The inclusive lower bound and exclusive upper bound of
        the IDs to process in this task.
    """
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT MIN(sentence_id), MAX(sentence_id) FROM sentences")
        ).one()
    min_id, max_id = int(row[0]), int(row[1])

    span = max_id - min_id + 1
    per_task = (span + num_tasks - 1) // num_tasks
    lo = min_id + task_id * per_task
    hi = min(lo + per_task, max_id + 1)
    return lo, hi


def get_checkpoint_path(task_id: int) -> str:
    """Build the path used to store the last processed sentence ID for a task.

    Args:
        task_id: Index of the current worker.

    Returns:
        str: Path to the checkpoint file for that task.
    """
    return f"last_id_{task_id}.txt"


def load_last_id(task_id: int) -> int | None:
    """Read the last processed sentence ID from the checkpoint for a task.

    Args:
        task_id: Index of the current worker.

    Returns:
        int | None: The last processed sentence ID, or None if no checkpoint yet
        exists.
    """
    path = get_checkpoint_path(task_id)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return int(f.read())
    return None


def save_last_id(task_id: int, last_id: int) -> None:
    """Persist the last processed sentence ID for a task.

    Args:
        task_id: Index of the current worker.
        last_id: Final sentence ID processed in the current batch.
    """
    with open(get_checkpoint_path(task_id), "w", encoding="utf-8") as f:
        f.write(str(last_id))


def create_qdrant_client() -> QdrantClient:
    """Create and return the Qdrant client used for uploads.

    Returns:
        QdrantClient: Connected client for the local Qdrant server.
    """
    return QdrantClient(host="assemblix2019", port=6333)


def main():
    """Run a single embedding worker for one range of sentence IDs.

    The function sets up the embedding model, locates the task's ID slice,
    resumes from a checkpoint if present, and streams rows from MySQL into Qdrant
    until the assigned range is fully processed.
    """
    set_num_threads()
    device, batch_size = get_device_and_batch_size()

    print(
        f" Number of cores used: {torch.get_num_threads()}, "
        f"device={device}, batch_size={batch_size}"
    )

    model = SentenceTransformer(MODEL_NAME, device=device)
    if device == "cuda":
        model = model.half()

    engine = load_engine()

    task_id = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))
    num_tasks = int(os.environ.get("SLURM_ARRAY_TASK_COUNT", 1))

    lo, hi = get_id_range(engine, task_id, num_tasks)
    last_id = load_last_id(task_id)
    if last_id is None:
        last_id = lo - 1

    print(
        f"[task {task_id}/{num_tasks}] device={device} "
        f"range=[{lo},{hi}) resume_from={last_id}"
    )

    client = create_qdrant_client()

    total_uploaded = 0
    while True:
        page = text(
            """
            SELECT sentence_id, sentence
            FROM sentences
            WHERE sentence_id > :last_id AND sentence_id < :hi
            ORDER BY sentence_id
            LIMIT :limit
            """
        )
        chunk_df = pd.read_sql(
            page,
            engine,
            params={"last_id": last_id, "hi": hi, "limit": CHUNK_SIZE},
        )
        if chunk_df.empty:
            break
        last_id = int(chunk_df["sentence_id"].iloc[-1])

        chunk_df = chunk_df.dropna(subset=["sentence"])
        chunk_df = chunk_df[chunk_df["sentence"].str.strip() != ""]
        if chunk_df.empty:
            continue

        texts = chunk_df["sentence"].tolist()
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=True,
            normalize_embeddings=True,
        )

        ids = chunk_df["sentence_id"].tolist()
        client.upload_collection(
            collection_name=COLLECTION_NAME,
            vectors=vectors,
            ids=ids,
        )

        save_last_id(task_id, last_id)
        total_uploaded += len(ids)
        print(f"[task {task_id}] {total_uploaded} points (through sentence_id {last_id})")

    print(f"[task {task_id}] DONE. uploaded {total_uploaded} points.")


if __name__ == "__main__":
    main()