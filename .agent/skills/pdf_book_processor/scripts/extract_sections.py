from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import fitz


PIPELINE_DIR = Path(__file__).resolve().parents[2] / "book_to_slide_source_pipeline" / "scripts"
import sys

if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from book_pipeline import (  # noqa: E402
    build_outline_nodes,
    export_outline_slice,
    output_directory_for,
    output_name_for,
    select_outline_nodes,
    write_outline_manifest,
)


def analyze_and_split_pdf(
    pdf_path: Path,
    output_dir: Path | None,
    min_depth: int,
    max_depth: int,
    leaf_only: bool,
    title_filter: str | None,
    manifest_path: Path | None,
) -> int:
    if not pdf_path.exists():
        print(f"Error: File not found -> {pdf_path}")
        return 1

    doc = fitz.open(str(pdf_path))
    try:
        total_pages = doc.page_count
        nodes = build_outline_nodes(doc)
        if not nodes:
            print("Warning: No internal outline found on this PDF.")
            return 1

        selected = select_outline_nodes(
            nodes=nodes,
            min_depth=min_depth,
            max_depth=max_depth,
            leaf_only=leaf_only,
            title_filter=title_filter,
        )
        if not selected:
            print("No outline entries matched the requested depth/filter.")
            return 1

        if output_dir is None:
            output_dir = pdf_path.resolve().parent / "Split_Sections"

        grouped = not (min_depth == max_depth == 1 and not leaf_only and not title_filter)
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Loading PDF: {pdf_path}")
        print(f"Total Pages: {total_pages}")
        print(f"Outline entries found: {len(nodes)}")
        print(f"Entries selected for export: {len(selected)}")

        for index, node in enumerate(selected, start=1):
            destination_dir = output_directory_for(node, output_dir, grouped)
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination = destination_dir / output_name_for(node)

            sidecar_payload = export_outline_slice(doc, node, nodes, destination)
            sidecar_path = destination.with_suffix(".json")
            sidecar_path.write_text(
                json.dumps(
                    {
                        "source_pdf": str(pdf_path),
                        "export_node": asdict(node),
                        **sidecar_payload,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            node.output_pdf = str(destination)
            node.sidecar_json = str(sidecar_path)

            print(
                f"[{index}/{len(selected)}] L{node.level} '{node.title}' "
                f"(Pages {node.start_page}-{node.end_page}) -> {destination.name}"
            )

        if manifest_path is None:
            manifest_path = output_dir / "outline_manifest.json"
        write_outline_manifest(selected, manifest_path, pdf_path, total_pages)
        print(f"Manifest written to: {manifest_path}")
        print(f"Processing complete. Files saved in: {output_dir}")
        return 0
    finally:
        doc.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Split a PDF by outline levels and preserve relative TOC metadata in exported slices."
    )
    parser.add_argument("input_pdf", help="Path to the source PDF file.")
    parser.add_argument("--output_dir", help="Custom output directory.", default=None)
    parser.add_argument("--min-depth", type=int, default=1, help="Smallest outline level to export.")
    parser.add_argument("--max-depth", type=int, default=1, help="Largest outline level to export.")
    parser.add_argument(
        "--leaf-only",
        action="store_true",
        help="Export only leaf outline nodes inside the requested depth range.",
    )
    parser.add_argument(
        "--title-filter",
        help="Regex filter applied to the full breadcrumb path before exporting.",
    )
    parser.add_argument(
        "--manifest",
        help="Optional JSON manifest path. Defaults to <output_dir>/outline_manifest.json",
        default=None,
    )
    args = parser.parse_args()

    return analyze_and_split_pdf(
        pdf_path=Path(args.input_pdf),
        output_dir=Path(args.output_dir) if args.output_dir else None,
        min_depth=args.min_depth,
        max_depth=args.max_depth,
        leaf_only=args.leaf_only,
        title_filter=args.title_filter,
        manifest_path=Path(args.manifest) if args.manifest else None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
