from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import fitz


PIPELINE_DIR = Path(__file__).resolve().parents[2] / "book_to_slide_source_pipeline" / "scripts"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from book_pipeline import (  # noqa: E402
    chunks_from_outline_rows,
    detect_headings_from_pages,
    extract_page_packages,
    load_outline_rows,
    microchunk_large_sections,
    selected_chunks,
    summarize_page_sources,
    write_chunk_exports,
    write_chunk_manifest,
    write_page_exports,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract subsection-level context using TOC-aware PyMuPDF extraction with optional local OCR rescue."
    )
    parser.add_argument("--pdf", required=True, help="Path to the chapter PDF.")
    parser.add_argument("--chapter-prefix", help="Chapter prefix such as 5 or 10.")
    parser.add_argument(
        "--max-relative-depth",
        type=int,
        default=1,
        help="Largest numbered heading depth below the chapter to keep in the manifest.",
    )
    parser.add_argument(
        "--max-pages-per-chunk",
        type=int,
        default=4,
        help="Target page size for fallback micro-chunks.",
    )
    parser.add_argument(
        "--min-pages-for-microchunk",
        type=int,
        default=6,
        help="Only heading chunks this large or larger are split into fallback micro-chunks.",
    )
    parser.add_argument(
        "--skip-heading-regex",
        default="",
        help="Regex for headings to ignore. Empty keeps exercise headings in scope.",
    )
    parser.add_argument("--ocr-mode", default="auto", choices=["off", "auto", "force"])
    parser.add_argument("--prefer-ocr", action="store_true", help="Prefer OCR text when available.")
    parser.add_argument(
        "--output-dir",
        help="Output directory for manifest, page files, and chunk files. Defaults next to the PDF.",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: file not found -> {pdf_path}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir) if args.output_dir else pdf_path.resolve().parent / f"{pdf_path.stem}_subsections"
    output_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    try:
        total_pages = doc.page_count
    finally:
        doc.close()

    page_packages = extract_page_packages(
        pdf_path,
        ocr_mode=args.ocr_mode,
        prefer_ocr=args.prefer_ocr,
        glm_api_key=os.getenv("GLM_API_KEY"),
        glm_cache_dir=output_dir / "ocr_cache",
        prefer_ollama=True,
    )
    page_manifest_path = write_page_exports(page_packages, output_dir)

    skip_pattern = re.compile(args.skip_heading_regex, re.IGNORECASE) if args.skip_heading_regex else None
    outline_rows = load_outline_rows(pdf_path)
    chunks = chunks_from_outline_rows(
        outline_rows,
        total_pages,
        prefix=args.chapter_prefix,
        skip_pattern=skip_pattern,
    )
    if not chunks:
        chunks = detect_headings_from_pages(
            page_packages,
            prefix=args.chapter_prefix,
            skip_pattern=skip_pattern,
        )
    if not chunks:
        print("No numbered headings found in chapter PDF.", file=sys.stderr)
        return 1

    expanded = microchunk_large_sections(
        chunks=chunks,
        max_relative_depth=args.max_relative_depth,
        max_pages_per_chunk=args.max_pages_per_chunk,
        min_pages_for_microchunk=args.min_pages_for_microchunk,
    )
    final_chunks = selected_chunks(expanded, args.max_relative_depth)
    write_chunk_exports(final_chunks, page_packages, output_dir)
    manifest_path, index_path = write_chunk_manifest(pdf_path, final_chunks, page_packages, output_dir)

    print(f"PDF: {pdf_path}")
    print(f"Detected heading chunks: {len(chunks)}")
    print(f"Final exported chunks: {len(final_chunks)}")
    print(f"Page manifest: {page_manifest_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Index: {index_path}")
    print(f"Extraction mix: {summarize_page_sources(page_packages)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
