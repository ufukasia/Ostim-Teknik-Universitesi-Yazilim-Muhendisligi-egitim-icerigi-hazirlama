from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


KEYWORD_ROLES: list[tuple[re.Pattern[str], list[str]]] = [
    (re.compile(r"\b(example|ornek)\b", re.IGNORECASE), ["worked-example", "question"]),
    (re.compile(r"\b(exercise|problem|soru)\b", re.IGNORECASE), ["question", "solution"]),
    (re.compile(r"\b(definition|tanim)\b", re.IGNORECASE), ["definition", "mini-example"]),
    (re.compile(r"\b(theorem|lemma|teorem)\b", re.IGNORECASE), ["theorem", "interpretation"]),
    (re.compile(r"\b(distribution|dagilim|expectation|variance|probability|cdf|pdf|pmf)\b", re.IGNORECASE), ["concept", "formula", "example"]),
]


def infer_frame_roles(title: str, page_count: int) -> list[str]:
    for pattern, roles in KEYWORD_ROLES:
        if pattern.search(title):
            return roles
    if page_count >= 6:
        return ["bridge", "concept", "formula", "example", "question"]
    if page_count >= 3:
        return ["concept", "example", "question"]
    return ["concept", "example"]


def summarize_ingest_signals(page_sources: list[dict]) -> dict[str, list[int] | bool]:
    formula_pages: list[int] = []
    table_pages: list[int] = []
    placeholder_pages: list[int] = []
    ocr_pages: list[int] = []

    for page in page_sources:
        signals = page.get("signal_summary") or {}
        page_number = int(page["page_number"])
        if signals.get("formula_regions"):
            formula_pages.append(page_number)
        if signals.get("table_regions"):
            table_pages.append(page_number)
        if signals.get("picture_placeholders"):
            placeholder_pages.append(page_number)
        if page.get("ocr_requested"):
            ocr_pages.append(page_number)

    return {
        "formula_pages": formula_pages,
        "table_pages": table_pages,
        "placeholder_pages": placeholder_pages,
        "ocr_attempted_pages": ocr_pages,
        "needs_extraction_attention": bool(formula_pages or table_pages or placeholder_pages),
    }


def build_pack(manifest_path: Path, output_dir: Path, chunk_filter: str | None, max_chunks: int | None) -> tuple[Path, Path]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = payload.get("entries", [])
    pages = payload.get("pages", [])

    pattern = re.compile(chunk_filter, re.IGNORECASE) if chunk_filter else None
    selected = []
    for entry in entries:
        title = str(entry.get("title", ""))
        if pattern and not pattern.search(title):
            continue
        selected.append(entry)
        if max_chunks is not None and len(selected) >= max_chunks:
            break

    page_map = {int(page["page_number"]): page for page in pages}
    units = []
    for order, entry in enumerate(selected, start=1):
        start_page = int(entry["start_page"])
        end_page = int(entry["end_page"])
        page_sources = []
        for page_number in range(start_page, end_page + 1):
            package = page_map.get(page_number)
            if package:
                page_sources.append(
                    {
                        "page_number": page_number,
                        "source": package.get("preferred_source"),
                        "markdown_file": package.get("markdown_file"),
                        "text_file": package.get("text_file"),
                        "ocr_requested": package.get("ocr_requested"),
                        "ocr_reasons": package.get("ocr_reasons"),
                        "signal_summary": package.get("page_signal_summary"),
                    }
                )
        ingest_signals = summarize_ingest_signals(page_sources)
        units.append(
            {
                "order": order,
                "source_id": entry["id"],
                "title": entry["title"],
                "kind": entry["kind"],
                "page_range": f"{start_page}-{end_page}",
                "page_count": entry["page_count"],
                "path": entry.get("path", []),
                "markdown_file": entry.get("markdown_file"),
                "text_file": entry.get("text_file"),
                "frame_roles": infer_frame_roles(entry["title"], int(entry["page_count"])),
                "ingest_signals": ingest_signals,
                "page_sources": page_sources,
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_out = output_dir / "deck_source_manifest.json"
    brief_out = output_dir / "deck_source_brief.md"

    manifest_out.write_text(
        json.dumps(
            {
                "source_manifest": str(manifest_path),
                "source_pdf": payload.get("source_pdf"),
                "unit_count": len(units),
                "units": units,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    lines = [
        "# Deck Source Brief",
        "",
        f"- Source manifest: {manifest_path}",
        f"- Source PDF: {payload.get('source_pdf')}",
        f"- Selected units: {len(units)}",
        "",
        "## Authoring contract",
        "",
        "- Write the deck from these units in order unless the week scope requires a tighter subset.",
        "- Keep notation and page grounding from the linked chunk files.",
        "- Do not invent definitions or examples outside the listed source units.",
        "- Prefer one concept arc plus one example/question arc per source unit.",
        "- If a unit carries extraction notes, inspect the linked chunk/page files before simplifying formulas, tables, or figures.",
        "",
        "## Units",
    ]

    for unit in units:
        lines.extend(
            [
                "",
                f"### {unit['order']}. {unit['title']}",
                "",
                f"- Pages: {unit['page_range']}",
                f"- Kind: {unit['kind']}",
                f"- Suggested frames: {', '.join(unit['frame_roles'])}",
                f"- Chunk markdown: {unit.get('markdown_file')}",
                f"- Chunk text: {unit.get('text_file')}",
            ]
        )
        signals = unit.get("ingest_signals") or {}
        if signals.get("formula_pages"):
            lines.append(f"- Formula pages: {', '.join(str(page) for page in signals['formula_pages'])}")
        if signals.get("table_pages"):
            lines.append(f"- Table pages: {', '.join(str(page) for page in signals['table_pages'])}")
        if signals.get("placeholder_pages"):
            lines.append(f"- Placeholder pages: {', '.join(str(page) for page in signals['placeholder_pages'])}")
        if signals.get("ocr_attempted_pages"):
            lines.append(f"- OCR attempted: {', '.join(str(page) for page in signals['ocr_attempted_pages'])}")
        if signals.get("needs_extraction_attention"):
            lines.append("- Extraction note: inspect linked chunk/page files before simplifying formulas, tables, or figures.")

    brief_out.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return manifest_out, brief_out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a slide-source pack from a subsection manifest so weekly decks can stay grounded in the book."
    )
    parser.add_argument("--manifest", required=True, help="Path to subsection_manifest.json")
    parser.add_argument("--output-dir", required=True, help="Output directory for deck source pack files")
    parser.add_argument("--chunk-filter", help="Regex filter applied to chunk titles before packaging")
    parser.add_argument("--max-chunks", type=int, help="Optional maximum number of chunks to include")
    args = parser.parse_args()

    manifest_out, brief_out = build_pack(
        manifest_path=Path(args.manifest),
        output_dir=Path(args.output_dir),
        chunk_filter=args.chunk_filter,
        max_chunks=args.max_chunks,
    )

    print(f"Deck source manifest: {manifest_out}")
    print(f"Deck source brief: {brief_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
