from __future__ import annotations

import argparse
import os
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
    summarize_page_sources,
    write_page_exports,
)


def page_slice(total_pages: int, page_start: int, page_end: int | None, max_pages: int | None) -> tuple[int, int]:
    start_page = max(page_start, 1)
    end_page = total_pages if page_end is None else min(page_end, total_pages)

    if max_pages is not None:
        end_page = min(end_page, start_page + max_pages - 1)
    if end_page < start_page:
        end_page = start_page
    return start_page, end_page


def output_dir_for(pdf_path: Path, output: str | None, explicit_output_dir: str | None) -> Path:
    if explicit_output_dir:
        return Path(explicit_output_dir)
    if output:
        output_path = Path(output)
        return output_path.with_suffix("")
    return pdf_path.resolve().parent / f"{pdf_path.stem}_chapter_context"


def build_report(
    pdf_path: Path,
    *,
    heading_prefix: str | None,
    page_start: int,
    page_end: int | None,
    max_pages: int | None,
    ocr_mode: str,
    prefer_ocr: bool,
    output_dir: Path,
) -> str:
    doc = fitz.open(str(pdf_path))
    try:
        total_pages = doc.page_count
    finally:
        doc.close()

    start_page, end_page = page_slice(total_pages, page_start, page_end, max_pages)
    page_numbers = list(range(start_page, end_page + 1))
    page_packages = extract_page_packages(
        pdf_path,
        page_numbers=page_numbers,
        ocr_mode=ocr_mode,
        prefer_ocr=prefer_ocr,
        glm_api_key=os.getenv("GLM_API_KEY"),
        glm_cache_dir=output_dir / "ocr_cache",
        prefer_ollama=True,
    )
    page_manifest = write_page_exports(page_packages, output_dir)

    outline_rows = load_outline_rows(pdf_path)
    chunks = chunks_from_outline_rows(outline_rows, total_pages, prefix=heading_prefix)
    if not chunks:
        chunks = detect_headings_from_pages(page_packages, prefix=heading_prefix)

    lines = [
        f"# Chapter Context for {pdf_path.name}",
        "",
        f"- PDF: {pdf_path}",
        f"- Total pages: {total_pages}",
        f"- Page window: {start_page}-{end_page}",
        f"- Page manifest: {page_manifest}",
        f"- Extraction mix: {summarize_page_sources(page_packages)}",
        "",
        "## Candidate headings",
    ]

    if chunks:
        for chunk in chunks:
            if chunk.end_page < start_page or chunk.start_page > end_page:
                continue
            lines.append(
                f"- p.{chunk.start_page}-{chunk.end_page}: {chunk.title}"
            )
    else:
        lines.append("- (none)")

    lines.extend(["", "## Extracted pages"])
    for package in page_packages:
        lines.extend(
            [
                "",
                f"### Page {package['page_number']} [{package['preferred_source']}]",
                "",
                package.get("preferred_markdown") or package.get("preferred_text") or "(empty)",
            ]
        )

    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract chapter context with PyMuPDF/PyMuPDF4LLM and optional local Ollama OCR rescue."
    )
    parser.add_argument("--pdf", required=True, help="Path to the chapter PDF.")
    parser.add_argument("--heading-prefix", help="Optional chapter prefix such as 4 or 6.")
    parser.add_argument("--page-start", type=int, default=1, help="1-based start page.")
    parser.add_argument("--page-end", type=int, help="1-based inclusive end page.")
    parser.add_argument("--max-pages", type=int, help="Maximum number of pages to dump.")
    parser.add_argument("--ocr-mode", default="auto", choices=["off", "auto", "force"])
    parser.add_argument("--prefer-ocr", action="store_true", help="Prefer OCR text when available.")
    parser.add_argument("--output-dir", help="Directory for page manifests and extracted page files.")
    parser.add_argument("--output", help="Optional UTF-8 output markdown file.")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: file not found -> {pdf_path}", file=sys.stderr)
        return 1

    output_dir = output_dir_for(pdf_path, args.output, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report = build_report(
        pdf_path=pdf_path,
        heading_prefix=args.heading_prefix,
        page_start=args.page_start,
        page_end=args.page_end,
        max_pages=args.max_pages,
        ocr_mode=args.ocr_mode,
        prefer_ocr=args.prefer_ocr,
        output_dir=output_dir,
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
    else:
        sys.stdout.buffer.write(report.encode("utf-8", "replace"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
