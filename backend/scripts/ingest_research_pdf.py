from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")
sys.path.insert(0, str(BACKEND_DIR))

from app.rag import (  # noqa: E402
    ResearchMetadata,
    chunk_pages,
    connect_database,
    ensure_new_pdf,
    ensure_ingestion_permitted,
    extract_pdf_pages,
    generate_embeddings,
    ingest_pdf,
)


async def embed_all(texts: list[str]) -> list[list[float]]:
    vectors: list[list[float]] = []
    for offset in range(0, len(texts), 64):
        vectors.extend(await generate_embeddings(texts[offset : offset + 64]))
    return vectors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract, embed, and ingest one PDF research/technical document."
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument(
        "--metadata",
        type=Path,
        required=True,
        help="JSON file containing known title and any verified authors/year/source_url/doi/license.",
    )
    args = parser.parse_args()

    metadata_data = json.loads(args.metadata.read_text(encoding="utf-8"))
    metadata = ResearchMetadata.from_dict(metadata_data)
    ensure_ingestion_permitted(metadata)
    with connect_database() as connection:
        ensure_new_pdf(args.pdf, connection)
        chunks = chunk_pages(extract_pdf_pages(args.pdf))
        vectors = asyncio.run(embed_all([chunk["text"] for chunk in chunks]))
        inserted = ingest_pdf(args.pdf, metadata, vectors, connection)
    print(f"Ingested {inserted} page-preserving chunks for {metadata.title!r}.")


if __name__ == "__main__":
    main()
