#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

LATEX_AUXILIARY_ENDINGS = (
    ".aux",
    ".bbl",
    ".bcf",
    ".blg",
    ".dvi",
    ".fdb_latexmk",
    ".fls",
    ".idx",
    ".ilg",
    ".ind",
    ".lof",
    ".log",
    ".lot",
    ".nav",
    ".out",
    ".ps",
    ".run.xml",
    ".snm",
    ".synctex.gz",
    ".toc",
    ".tmp",
    ".vrb",
    ".xdv",
)

SPECIAL_FILE_ENDINGS = (
    ".synctex(busy)",
    "-SAVE-ERROR",
)

SPECIAL_FILE_NAMES = {
    "texput.log",
}

PYTHON_CACHE_ENDINGS = (
    ".pyc",
)

SKIP_DIR_NAMES = {
    ".git",
}

DISPOSABLE_DIR_NAMES = {
    "__pycache__",
}

TEMP_DIR_NAMES = {
    "temp",
    "tmp",
}


@dataclass(frozen=True)
class DeletionCandidate:
    path: Path
    kind: str
    size_bytes: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "LaTeX derleme artigi dosyalari ve istege bagli gecici klasorleri "
            "temizler. Varsayilan olarak PDF dosyalarini korur."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Temizlenecek kok klasor. Varsayilan: scriptin bulundugu klasor.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Silecegi dosyalari sadece listeler, gercek silme yapmaz.",
    )
    parser.add_argument(
        "--include-pdf",
        action="store_true",
        help="Kaynak .tex dosyasina baglanabilen uretilmis PDF dosyalarini da siler.",
    )
    parser.add_argument(
        "--purge-temp-dirs",
        action="store_true",
        help="Adi temp/tmp olan klasorleri icerigiyle birlikte siler.",
    )
    parser.add_argument(
        "--aggressive",
        action="store_true",
        help="--purge-temp-dirs ve --include-pdf bayraklarini birlikte acar.",
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Ozet yerine silinecek tum yollarin listesini yazdirir.",
    )
    return parser.parse_args()


def should_skip_dir(path: Path, root: Path) -> bool:
    if path == root:
        return False
    name = path.name
    return name in SKIP_DIR_NAMES or name.startswith(".")


def iter_project_tree(root: Path, purge_temp_dirs: bool) -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    disposable_dirs: list[Path] = []

    for current_root, dir_names, file_names in os.walk(root):
        current_path = Path(current_root)

        kept_dirs: list[str] = []
        for dir_name in dir_names:
            dir_path = current_path / dir_name
            lowered = dir_name.lower()
            if should_skip_dir(dir_path, root):
                continue
            if dir_name in DISPOSABLE_DIR_NAMES:
                disposable_dirs.append(dir_path)
                continue
            if purge_temp_dirs and lowered in TEMP_DIR_NAMES:
                disposable_dirs.append(dir_path)
                continue
            kept_dirs.append(dir_name)
        dir_names[:] = kept_dirs

        if should_skip_dir(current_path, root):
            continue

        for file_name in file_names:
            files.append(current_path / file_name)

    return files, disposable_dirs


def is_generated_pdf(path: Path) -> bool:
    direct_source = path.with_suffix(".tex")
    if direct_source.exists():
        return True

    parent = path.parent
    if parent.name.lower() == "outputs":
        sibling_source = parent.parent / f"{path.stem}.tex"
        if sibling_source.exists():
            return True

    return False


def classify_file(path: Path, include_pdf: bool) -> str | None:
    name = path.name

    if name in SPECIAL_FILE_NAMES or any(name.endswith(ending) for ending in SPECIAL_FILE_ENDINGS):
        return "special_artifact"

    if any(name.endswith(ending) for ending in LATEX_AUXILIARY_ENDINGS):
        return "latex_auxiliary"

    if any(name.endswith(ending) for ending in PYTHON_CACHE_ENDINGS):
        return "python_cache"

    if include_pdf and name.lower().endswith(".pdf") and is_generated_pdf(path):
        return "generated_pdf"

    return None


def build_candidates(root: Path, include_pdf: bool, purge_temp_dirs: bool) -> list[DeletionCandidate]:
    files, disposable_dirs = iter_project_tree(root, purge_temp_dirs=purge_temp_dirs)
    candidates: list[DeletionCandidate] = []

    for dir_path in disposable_dirs:
        size_bytes = directory_size(dir_path)
        kind = "temp_directory" if dir_path.name.lower() in TEMP_DIR_NAMES else "python_cache_directory"
        candidates.append(DeletionCandidate(path=dir_path, kind=kind, size_bytes=size_bytes))

    for file_path in files:
        if any(parent == file_path.parent or parent in file_path.parents for parent in disposable_dirs):
            continue
        kind = classify_file(file_path, include_pdf=include_pdf)
        if kind is None:
            continue
        size_bytes = safe_file_size(file_path)
        candidates.append(DeletionCandidate(path=file_path, kind=kind, size_bytes=size_bytes))

    candidates.sort(key=lambda item: (str(item.path).lower(), item.kind))
    return candidates


def safe_file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def directory_size(path: Path) -> int:
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += safe_file_size(child)
    return total


def delete_candidate(candidate: DeletionCandidate) -> None:
    if candidate.path.is_dir():
        shutil.rmtree(candidate.path)
        return
    candidate.path.unlink(missing_ok=True)


def prune_empty_dirs(root: Path) -> int:
    removed = 0
    for current_root, dir_names, _ in os.walk(root, topdown=False):
        current_path = Path(current_root)
        if current_path == root or should_skip_dir(current_path, root):
            continue
        try:
            if not any(current_path.iterdir()):
                current_path.rmdir()
                removed += 1
        except OSError:
            continue
    return removed


def human_size(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size_bytes)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size_bytes} B"


def print_report(root: Path, candidates: list[DeletionCandidate], show_all: bool) -> None:
    total_size = sum(item.size_bytes for item in candidates)
    counts = Counter(item.kind for item in candidates)

    print(f"Kok klasor: {root}")
    print(f"Silinecek oge sayisi: {len(candidates)}")
    print(f"Tahmini bosalacak alan: {human_size(total_size)}")

    if counts:
        print("Tur dagilimi:")
        for kind, count in sorted(counts.items()):
            print(f"  - {kind}: {count}")

    if not candidates:
        return

    if show_all:
        print("Yollar:")
        for candidate in candidates:
            relative_path = candidate.path.relative_to(root)
            print(f"  - {relative_path}")
        return

    preview = candidates[:20]
    print("Onizleme:")
    for candidate in preview:
        relative_path = candidate.path.relative_to(root)
        print(f"  - {relative_path}")
    if len(candidates) > len(preview):
        print(f"  ... ve {len(candidates) - len(preview)} oge daha.")


def main() -> int:
    args = parse_args()

    if args.aggressive:
        args.include_pdf = True
        args.purge_temp_dirs = True

    root = args.root.resolve()
    if not root.exists():
        print(f"Hata: kok klasor bulunamadi: {root}", file=sys.stderr)
        return 1
    if not root.is_dir():
        print(f"Hata: kok klasor bir dizin degil: {root}", file=sys.stderr)
        return 1

    candidates = build_candidates(
        root=root,
        include_pdf=args.include_pdf,
        purge_temp_dirs=args.purge_temp_dirs,
    )

    print_report(root=root, candidates=candidates, show_all=args.show_all)

    if args.dry_run:
        print("Dry-run modu: hicbir dosya silinmedi.")
        return 0

    failures: list[tuple[Path, str]] = []
    for candidate in candidates:
        try:
            delete_candidate(candidate)
        except OSError as exc:
            failures.append((candidate.path, str(exc)))

    pruned_count = prune_empty_dirs(root)

    deleted_count = len(candidates) - len(failures)
    print(f"Silinen oge sayisi: {deleted_count}")
    if pruned_count:
        print(f"Silinen bos klasor sayisi: {pruned_count}")

    if failures:
        print("Silinemeyen ogeler:", file=sys.stderr)
        for path, message in failures:
            print(f"  - {path}: {message}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
