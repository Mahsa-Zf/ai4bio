#!/usr/bin/env python3
"""
Split PubMed abstracts into sentences and bulk-load them into MySQL.

This module is intended to be run once per TSV input file. It creates the
sentences table if needed, tokenizes title/abstract records into sentences, and
inserts them in batches while skipping duplicate (pubmed_id, sentence_number)
entries via INSERT IGNORE.
"""

import argparse
import os

from sqlalchemy import create_engine, text
import spacy


PIPE_BATCH = 2_000

INSERT_SQL = text(
    "INSERT IGNORE INTO sentences (pubmed_id, sentence_number, sentence) "
    "VALUES (:pubmed_id, :sentence_number, :sentence)"
)


def parse_args():
    """Parse command-line arguments for the sentence-loading job.

    Returns:
        argparse.Namespace: Parsed arguments including the input TSV path, worker
        count, and insertion batch size.
    """
    parser = argparse.ArgumentParser(
        description="Split abstracts from a PMID<TAB>abstract TSV into sentences "
        "and bulk-load them into MySQL."
    )
    parser.add_argument("input_file", help="path to the input TSV file")
    parser.add_argument(
        "-n",
        "--n-process",
        type=int,
        default=int(os.environ.get("N_PROCESS", 1)),
        help="spaCy worker processes (default: $N_PROCESS or 1)",
    )
    parser.add_argument(
        "-b",
        "--batch-size",
        type=int,
        default=50_000,
        help="sentence rows per INSERT (default: 50000)",
    )
    return parser.parse_args()


def create_nlp_pipeline():
    """Create the spaCy pipeline used to segment text into sentences.

    Returns:
        spacy.Language: A minimal English spaCy pipeline configured with the
        sentencizer component.
    """
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    return nlp


def load_engine():
    """Create the SQLAlchemy engine for the local MySQL database.

    Returns:
        sqlalchemy.engine.Engine: Database engine loaded from mysql.txt.
    """
    with open("mysql.txt", encoding="utf-8") as conn_file:
        connectionstring = conn_file.read().strip()
    return create_engine(connectionstring, pool_pre_ping=True)


def row_reader(path):
    """Yield title/abstract pairs as (text, pmid) records for spaCy processing.

    Args:
        path: Path to the input TSV file.

    Yields:
        tuple[str, str]: A combined title-and-abstract string and its PMID.

    Notes:
        The title is prepended to the abstract, with the title normalized to end
        with a sentence terminator when needed. Records with neither a title nor
        an abstract are skipped.
    """
    with open(path, "r", encoding="utf-8") as infile:
        for line in infile:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            pmid = parts[0]
            title = parts[1].strip()
            abstract = parts[2].strip() if len(parts) >= 3 else ""
            if title and not title.endswith((".", "?", "!")):
                title += "."
            combined = " ".join(p for p in (title, abstract) if p)
            if combined:
                yield combined, pmid


def main():
    """Process a TSV file and bulk-insert sentence rows into MySQL."""
    args = parse_args()
    input_file = args.input_file
    n_process = args.n_process
    batch_size = args.batch_size

    nlp = create_nlp_pipeline()
    engine = load_engine()

    with engine.connect() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS sentences (
                    sentence_id     BIGINT AUTO_INCREMENT,
                    pubmed_id       BIGINT,
                    sentence_number INT,
                    sentence        TEXT,
                    PRIMARY KEY (sentence_id),
                    UNIQUE KEY uq_pmid_sentnum (pubmed_id, sentence_number)
                )
                """
            )
        )
        conn.commit()

        batch, processed = [], 0
        pmid = 0
        try:
            docs = nlp.pipe(
                row_reader(input_file),
                as_tuples=True,
                batch_size=PIPE_BATCH,
                n_process=n_process,
            )
            for doc, pmid in docs:
                for sent_num, sent in enumerate(doc.sents):
                    sent_text = sent.text.strip()
                    if sent_text:
                        batch.append(
                            {
                                "pubmed_id": pmid,
                                "sentence_number": sent_num,
                                "sentence": sent_text,
                            }
                        )
                if len(batch) >= batch_size:
                    conn.execute(INSERT_SQL, batch)
                    conn.commit()
                    batch.clear()
                processed += 1
                if processed % 100_000 == 0:
                    print(f"{input_file}: {processed:,} abstracts...", flush=True)

            if batch:
                conn.execute(INSERT_SQL, batch)
                conn.commit()
        except Exception as exc:
            print(
                f"{input_file}: failed after {processed:,} abstracts on pmid {pmid}: {exc}"
            )
            conn.rollback()
            raise

    print(f"{input_file}: done.")


if __name__ == "__main__":
    main()