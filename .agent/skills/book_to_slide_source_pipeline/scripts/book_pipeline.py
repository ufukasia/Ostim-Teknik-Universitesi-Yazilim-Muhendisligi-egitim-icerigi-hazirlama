from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

import fitz
import requests

try:
    import pymupdf4llm
except Exception:  # pragma: no cover - optional dependency
    pymupdf4llm = None


INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]+')
WHITESPACE = re.compile(r"\s+")
TRAILING_PAGE_NUMBER = re.compile(r"\s+\d{1,4}$")
MARKDOWN_HEADER = re.compile(r"^\s{0,3}#{1,6}\s+")
NON_WORD = re.compile(r"\W+", re.UNICODE)
NUMBERED_HEADING = re.compile(
    r"^(?P<number>\d+(?:\.\d+)+)\s+(?P<title>.+)$|^(?P<chapter>Chapter\s+\d+\b.*)$",
    re.IGNORECASE,
)
CONNECTOR_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}
EXERCISE_OPENERS = {
    "according",
    "assume",
    "consider",
    "find",
    "if",
    "suppose",
}
PICTURE_PLACEHOLDER = re.compile(r"\*\*==>\s*picture\b.*?omitted\s*<==\*\*", re.IGNORECASE)
HTML_TAG = re.compile(r"<[^>]+>")
TABLE_MARKDOWN = re.compile(r"^\|.+\|$", re.MULTILINE)
MATH_TOKEN = re.compile(
    r"(?:[=<>]|\\frac|\\sum|\\prod|\\lambda|\\mu|\\sigma|"
    r"[α-ωΑ-ΩμλσπΠΣ]|P\(|f\(|b\s*\(|p\s*\(|\d+/\d+)",
    re.UNICODE,
)
TRIVIAL_HTML_TABLE = re.compile(
    r"^\s*<table[^>]*>\s*(?:<tr[^>]*>\s*(?:<td[^>]*>\s*</td>\s*)+</tr>\s*)+\s*</table>\s*$",
    re.IGNORECASE | re.DOTALL,
)
SEQUENTIAL_NUMBER_RUN = re.compile(r"(?:\b\d{1,3}\.\s*){10,}")
REPLACEMENTS = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\u2013": "-",
    "\u2014": "-",
    "\u2212": "-",
    "\xa0": " ",
}
GLM_LAYOUT_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/layout_parsing"


@dataclass
class OutlineNode:
    id: str
    level: int
    title: str
    start_page: int
    end_page: int
    page_count: int
    numbering: str | None
    parent_id: str | None
    path: list[str]
    output_pdf: str | None = None
    sidecar_json: str | None = None


@dataclass
class Chunk:
    id: str
    kind: str
    title: str
    numbering: str | None
    depth: int
    start_page: int
    end_page: int
    page_count: int
    parent_id: str | None
    path: list[str]
    markdown_file: str | None = None
    text_file: str | None = None


def clean_text(text: str) -> str:
    for bad, good in REPLACEMENTS.items():
        text = text.replace(bad, good)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split()).strip()
        if line:
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def sanitize_filename(name: str) -> str:
    cleaned = INVALID_FILENAME_CHARS.sub("_", name).strip().strip(".")
    cleaned = WHITESPACE.sub(" ", cleaned)
    return cleaned or "untitled"


def extract_numbering(title: str) -> str | None:
    match = re.match(r"^((?:Chapter\s+\d+)|(?:\d+(?:\.\d+)*))\b", title, re.IGNORECASE)
    if not match:
        return None
    numbering = match.group(1)
    return numbering.replace("Chapter ", "").strip()


def relative_depth(numbering: str | None, prefix: str | None) -> int:
    if numbering is None:
        return 0
    base = len(prefix.split(".")) if prefix else 1
    return max(len(numbering.split(".")) - base, 0)


def normalize_heading_line(line: str) -> str:
    line = MARKDOWN_HEADER.sub("", line).strip()
    line = TRAILING_PAGE_NUMBER.sub("", line).strip()
    return line


def looks_like_structural_heading(line: str, numbering: str | None) -> bool:
    if line.lower().startswith("chapter "):
        return True

    if numbering is None:
        return False

    title_text = normalize_heading_line(line)
    title_text = title_text[len(numbering) :].strip()
    if not title_text:
        return False

    words = re.findall(r"[A-Za-z][A-Za-z'-]*", title_text)
    if not words or len(words) > 14:
        return False

    content_words = [word for word in words if word.lower() not in CONNECTOR_WORDS]
    if not content_words:
        return False

    if content_words[0].lower() in EXERCISE_OPENERS:
        return False

    capitalized = sum(1 for word in content_words if word[0].isupper())
    ratio = capitalized / len(content_words)
    return ratio >= 0.6


def open_pdf(pdf_path: Path) -> fitz.Document:
    return fitz.open(str(pdf_path))


def build_outline_nodes(doc: fitz.Document) -> list[OutlineNode]:
    toc = doc.get_toc(simple=False)
    if not toc:
        return []

    nodes: list[OutlineNode] = []
    stack: list[OutlineNode] = []

    for index, row in enumerate(toc, start=1):
        if len(row) < 3:
            continue
        level = int(row[0])
        title = str(row[1]).strip()
        start_page = max(int(row[2]), 1)

        while stack and stack[-1].level >= level:
            stack.pop()

        parent_id = stack[-1].id if stack else None
        path = [ancestor.title for ancestor in stack] + [title]
        node = OutlineNode(
            id=f"L{level}_P{start_page:04d}_{index:04d}",
            level=level,
            title=title,
            start_page=start_page,
            end_page=start_page,
            page_count=1,
            numbering=extract_numbering(title),
            parent_id=parent_id,
            path=path,
        )
        nodes.append(node)
        stack.append(node)

    total_pages = doc.page_count
    for index, node in enumerate(nodes):
        next_page = total_pages + 1
        for candidate in nodes[index + 1 :]:
            if candidate.level <= node.level:
                next_page = candidate.start_page
                break
        node.end_page = max(next_page - 1, node.start_page)
        node.page_count = max(node.end_page - node.start_page + 1, 1)

    return nodes


def select_outline_nodes(
    nodes: Sequence[OutlineNode],
    min_depth: int,
    max_depth: int,
    leaf_only: bool,
    title_filter: str | None,
) -> list[OutlineNode]:
    selected = [node for node in nodes if min_depth <= node.level <= max_depth]

    if leaf_only:
        parent_ids = {node.parent_id for node in nodes if node.parent_id}
        selected = [node for node in selected if node.id not in parent_ids]

    if title_filter:
        pattern = re.compile(title_filter, re.IGNORECASE)
        selected = [node for node in selected if pattern.search(" / ".join(node.path))]

    return selected


def descendants_for(node: OutlineNode, nodes: Sequence[OutlineNode]) -> list[OutlineNode]:
    prefix = tuple(node.path)
    descendants: list[OutlineNode] = []
    for candidate in nodes:
        if candidate.id == node.id:
            continue
        if tuple(candidate.path[: len(prefix)]) == prefix:
            descendants.append(candidate)
    return descendants


def relative_toc_for(node: OutlineNode, nodes: Sequence[OutlineNode]) -> list[list[Any]]:
    toc_rows: list[list[Any]] = [[1, node.title, 1]]
    for candidate in descendants_for(node, nodes):
        rel_page = candidate.start_page - node.start_page + 1
        if rel_page < 1 or rel_page > node.page_count:
            continue
        rel_level = max(candidate.level - node.level + 1, 1)
        toc_rows.append([rel_level, candidate.title, rel_page])
    return toc_rows


def output_directory_for(node: OutlineNode, root: Path, grouped: bool) -> Path:
    if grouped:
        return root / f"L{node.level}"
    return root


def output_name_for(node: OutlineNode) -> str:
    title = sanitize_filename(node.title)
    prefix = f"L{node.level}_p{node.start_page:04d}"
    if node.numbering:
        prefix = f"{prefix}_{sanitize_filename(node.numbering)}"
    return f"{prefix}__{title}.pdf"


def export_outline_slice(
    doc: fitz.Document,
    node: OutlineNode,
    nodes: Sequence[OutlineNode],
    destination: Path,
) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)

    exported = fitz.open()
    exported.insert_pdf(doc, from_page=node.start_page - 1, to_page=node.end_page - 1)
    rel_toc = relative_toc_for(node, nodes)
    if rel_toc:
        try:
            exported.set_toc(rel_toc)
        except Exception:
            pass
    exported.save(str(destination))
    exported.close()

    descendants_payload: list[dict[str, Any]] = []
    for candidate in descendants_for(node, nodes):
        descendants_payload.append(
            {
                **asdict(candidate),
                "relative_start_page": candidate.start_page - node.start_page + 1,
                "relative_end_page": candidate.end_page - node.start_page + 1,
            }
        )

    return {
        "source_title": node.title,
        "source_page_range": [node.start_page, node.end_page],
        "relative_page_count": node.page_count,
        "toc": rel_toc,
        "descendants": descendants_payload,
    }


def write_outline_manifest(nodes: Sequence[OutlineNode], path: Path, source_pdf: Path, total_pages: int) -> None:
    payload = {
        "source_pdf": str(source_pdf),
        "total_pages": total_pages,
        "entry_count": len(nodes),
        "entries": [asdict(node) for node in nodes],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def markdown_chunks_for_pages(doc: fitz.Document, pdf_path: Path, pages_1_based: Sequence[int]) -> dict[int, dict[str, Any]]:
    page_numbers = sorted({page for page in pages_1_based if 1 <= page <= doc.page_count})
    if not page_numbers:
        return {}

    chunk_map: dict[int, dict[str, Any]] = {}
    if pymupdf4llm is not None:
        try:
            chunks = pymupdf4llm.to_markdown(
                doc,
                pages=[page - 1 for page in page_numbers],
                page_chunks=True,
                show_progress=False,
                use_ocr=False,
                force_text=True,
                table_strategy="lines_strict",
            )
            for chunk in chunks:
                metadata = chunk.get("metadata", {})
                page_number = int(metadata.get("page_number", 0))
                if page_number:
                    chunk["_provider"] = "pymupdf4llm"
                    chunk_map[page_number] = chunk
        except Exception:
            chunk_map = {}

    toc_rows = doc.get_toc()
    toc_by_page: dict[int, list[list[Any]]] = {}
    for row in toc_rows:
        if len(row) < 3:
            continue
        page_number = int(row[2])
        toc_by_page.setdefault(page_number, []).append(row[:3])

    for page_number in page_numbers:
        if page_number in chunk_map:
            continue
        page = doc[page_number - 1]
        chunk_map[page_number] = {
            "metadata": {
                "file_path": str(pdf_path),
                "page_count": doc.page_count,
                "page_number": page_number,
            },
            "_provider": "pymupdf",
            "toc_items": toc_by_page.get(page_number, []),
            "tables": [],
            "images": page.get_image_info() or [],
            "graphics": [],
            "text": clean_text(page.get_text("text") or ""),
            "page_boxes": [],
        }

    return chunk_map


def compute_text_quality(text: str) -> dict[str, float]:
    stripped = clean_text(text)
    if not stripped:
        return {
            "char_count": 0.0,
            "word_count": 0.0,
            "alpha_ratio": 0.0,
            "printable_ratio": 0.0,
            "suspicious_ratio": 1.0,
            "score": 0.0,
        }

    char_count = len(stripped)
    word_count = len([token for token in NON_WORD.split(stripped) if token])
    alpha_count = sum(1 for ch in stripped if ch.isalpha())
    printable_count = sum(1 for ch in stripped if ch.isprintable())
    suspicious_count = sum(1 for ch in stripped if ord(ch) < 32 and ch not in "\n\t")

    alpha_ratio = alpha_count / char_count
    printable_ratio = printable_count / char_count
    suspicious_ratio = suspicious_count / char_count
    density = min(word_count / 160.0, 1.0)
    score = (
        density * 0.45
        + alpha_ratio * 0.30
        + printable_ratio * 0.20
        + max(0.0, 1.0 - suspicious_ratio * 10.0) * 0.05
    )

    return {
        "char_count": float(char_count),
        "word_count": float(word_count),
        "alpha_ratio": round(alpha_ratio, 4),
        "printable_ratio": round(printable_ratio, 4),
        "suspicious_ratio": round(suspicious_ratio, 4),
        "score": round(score, 4),
    }


def picture_placeholder_count(text: str) -> int:
    return len(PICTURE_PLACEHOLDER.findall(text or ""))


def math_signal_score(text: str) -> int:
    if not text:
        return 0
    score = len(MATH_TOKEN.findall(text))
    if TABLE_MARKDOWN.search(text):
        score += 2
    return score


def summarize_page_boxes(page_boxes: Sequence[dict[str, Any]] | None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for box in page_boxes or []:
        box_class = str(box.get("class") or "").strip().lower()
        if not box_class:
            continue
        counts[box_class] = counts.get(box_class, 0) + 1
    return counts


def extraction_coverage_score(
    text: str,
    metrics: dict[str, float],
    *,
    box_counts: dict[str, int],
) -> float:
    score = metrics["score"]
    placeholders = picture_placeholder_count(text)
    if placeholders:
        score -= min(placeholders * 0.18, 0.45)

    if box_counts.get("formula", 0):
        score += min(math_signal_score(text) * 0.03, 0.18)
    if box_counts.get("table", 0):
        if TABLE_MARKDOWN.search(text):
            score += 0.08
        elif metrics["word_count"] >= 40:
            score += 0.04

    return round(score, 4)


def select_base_extraction(
    *,
    native_text: str,
    markdown_text: str,
    native_provider: str,
    box_counts: dict[str, int],
) -> tuple[str, str, dict[str, Any]]:
    native_text_metrics = compute_text_quality(native_text)
    markdown_metrics = compute_text_quality(markdown_text)
    native_score = extraction_coverage_score(native_text, native_text_metrics, box_counts=box_counts)
    markdown_score = extraction_coverage_score(markdown_text, markdown_metrics, box_counts=box_counts)

    diagnostics = {
        "native_text_metrics": native_text_metrics,
        "markdown_metrics": markdown_metrics,
        "native_text_score": native_score,
        "markdown_score": markdown_score,
        "selected_base_source": native_provider if markdown_text else "pymupdf",
        "selection_reasons": [],
    }

    if markdown_text and markdown_score >= native_score + 0.08:
        return markdown_text, native_provider, diagnostics

    if markdown_text and native_text:
        if picture_placeholder_count(markdown_text):
            diagnostics["selection_reasons"].append("native-preserves-omitted-objects")
        if box_counts.get("formula", 0) and math_signal_score(native_text) > math_signal_score(markdown_text):
            diagnostics["selection_reasons"].append("native-preserves-more-math")
        diagnostics["selected_base_source"] = "pymupdf-text"
        return native_text, "pymupdf-text", diagnostics

    return native_text or markdown_text, "pymupdf", diagnostics


def should_run_ocr(
    native_text: str,
    markdown_text: str,
    image_count: int,
    ocr_mode: str,
    box_counts: dict[str, int] | None = None,
    native_math_score: int = 0,
    markdown_math_score: int = 0,
    force_ocr: bool = False,
) -> tuple[bool, list[str]]:
    mode = (ocr_mode or "auto").lower()
    if mode == "off":
        return False, []
    if force_ocr or mode == "force":
        return True, ["forced"]

    native_metrics = compute_text_quality(native_text)
    markdown_metrics = compute_text_quality(markdown_text)
    reasons: list[str] = []

    if native_metrics["word_count"] < 20:
        reasons.append("low-native-word-count")
    if markdown_metrics["score"] < 0.30:
        reasons.append("weak-markdown-score")
    if image_count and markdown_metrics["word_count"] < 50:
        reasons.append("image-heavy-page")
    if picture_placeholder_count(markdown_text):
        reasons.append("picture-placeholder")

    box_counts = box_counts or {}
    if box_counts.get("formula", 0) and native_math_score >= markdown_math_score + 2:
        reasons.append("formula-coverage-gap")
    if box_counts.get("table", 0) and not TABLE_MARKDOWN.search(markdown_text):
        reasons.append("table-coverage-gap")

    return bool(reasons), reasons


def _extract_markdown_block(text: str) -> str | None:
    fenced = re.search(r"```(?:markdown|md)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    stripped = text.strip()
    return stripped or None


def _ollama_host() -> str:
    host = (os.getenv("OLLAMA_HOST") or "http://127.0.0.1:11434").strip()
    if not host.startswith(("http://", "https://")):
        host = f"http://{host}"
    return host.rstrip("/")


def looks_like_usable_ocr_markdown(text: str | None) -> bool:
    extracted = _extract_markdown_block(text or "")
    if not extracted:
        return False
    if TRIVIAL_HTML_TABLE.fullmatch(extracted.strip()):
        return False

    plain = clean_text(HTML_TAG.sub(" ", extracted))
    plain_metrics = compute_text_quality(plain)
    if len(plain) < 24:
        return False
    if SEQUENTIAL_NUMBER_RUN.search(plain):
        return False
    if plain_metrics["alpha_ratio"] < 0.20 and math_signal_score(extracted) < 4:
        return False
    return True


def _ollama_cli_ocr_page(
    image_path: Path,
    *,
    model: str = "glm-ocr:latest",
    task: str = "Text Recognition",
    timeout_seconds: int = 180,
) -> str | None:
    prompt = f"{task}: {image_path.as_posix()}"
    result = subprocess.run(
        ["ollama", "run", model, prompt],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
    )
    if result.returncode != 0:
        return None

    combined = "\n".join(
        part for part in [result.stdout.strip(), result.stderr.strip()] if part.strip()
    )
    cleaned = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", combined)
    cleaned = re.sub(r"Added image '.*?'\s*", "", cleaned)
    cleaned = re.sub(r"\r", "", cleaned)
    extracted = _extract_markdown_block(cleaned)
    if looks_like_usable_ocr_markdown(extracted):
        return extracted
    return None


def ollama_ocr_page(
    image_path: Path,
    *,
    model: str = "glm-ocr:latest",
    task: str = "Convert this textbook page to markdown. Preserve formulas, tables, graph labels, captions, and symbols. Do not summarize.",
    timeout_seconds: int = 180,
) -> str | None:
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": task,
                "images": [base64.b64encode(image_path.read_bytes()).decode("utf-8")],
            }
        ],
    }
    try:
        response = requests.post(
            f"{_ollama_host()}/api/chat",
            json=payload,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        content = str(
            data.get("message", {}).get("content")
            or data.get("response")
            or ""
        )
        extracted = _extract_markdown_block(content)
        if looks_like_usable_ocr_markdown(extracted):
            return extracted
    except Exception:
        pass

    return _ollama_cli_ocr_page(
        image_path,
        model=model,
        task=task,
        timeout_seconds=timeout_seconds,
    )


def glm_ocr_request(
    image_bytes: bytes,
    api_key: str,
    *,
    endpoint: str = GLM_LAYOUT_ENDPOINT,
    model: str = "glm-ocr",
    timeout_seconds: int = 180,
    user_id: str = "bookslide",
) -> dict[str, Any]:
    payload = {
        "model": model,
        "file": base64.b64encode(image_bytes).decode("utf-8"),
        "request_id": f"req_{uuid.uuid4().hex[:20]}",
        "user_id": user_id[:128],
    }
    response = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def glm_ocr_page_via_api(
    page: fitz.Page,
    *,
    cache_dir: Path | None,
    cache_key: str,
    api_key: str | None,
    ocr_mode: str,
    dpi: int = 220,
    timeout_seconds: int = 180,
    user_id: str = "bookslide",
) -> tuple[str | None, str | None]:
    if (ocr_mode or "auto").lower() == "off" or not api_key:
        return None, None

    cache_path: Path | None = None
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / f"{cache_key}.json"
        if cache_path.exists():
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            return payload.get("md_results"), str(cache_path)

    matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    payload = glm_ocr_request(
        pix.tobytes("png"),
        api_key,
        timeout_seconds=timeout_seconds,
        user_id=user_id,
    )
    if cache_path is not None:
        cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload.get("md_results"), str(cache_path) if cache_path is not None else None


def extract_page_packages(
    pdf_path: Path,
    *,
    page_numbers: Sequence[int] | None = None,
    ocr_mode: str = "auto",
    force_ocr: bool = False,
    prefer_ocr: bool = False,
    glm_api_key: str | None = None,
    glm_cache_dir: Path | None = None,
    glm_user_id: str = "bookslide",
    ollama_model: str = "glm-ocr:latest",
    prefer_ollama: bool = True,
) -> list[dict[str, Any]]:
    doc = open_pdf(pdf_path)
    try:
        if page_numbers is None:
            pages = list(range(1, doc.page_count + 1))
        else:
            pages = sorted({page for page in page_numbers if 1 <= page <= doc.page_count})

        markdown_map = markdown_chunks_for_pages(doc, pdf_path, pages)
        packages: list[dict[str, Any]] = []

        image_cache_dir = None if glm_cache_dir is None else glm_cache_dir / "images"
        if image_cache_dir is not None:
            image_cache_dir.mkdir(parents=True, exist_ok=True)

        for page_number in pages:
            page = doc[page_number - 1]
            native_text = clean_text(page.get_text("text") or "")
            chunk = markdown_map.get(page_number, {})
            markdown_text = str(chunk.get("text", "") or "").strip()
            native_provider = str(chunk.get("_provider") or "pymupdf")
            image_count = len(chunk.get("images", []) or page.get_image_info() or [])
            page_boxes = chunk.get("page_boxes", [])
            box_counts = summarize_page_boxes(page_boxes)

            preferred_markdown, preferred_source, base_diagnostics = select_base_extraction(
                native_text=native_text,
                markdown_text=markdown_text,
                native_provider=native_provider,
                box_counts=box_counts,
            )
            base_metrics = compute_text_quality(preferred_markdown)
            page_signal_summary = {
                "formula_regions": box_counts.get("formula", 0),
                "table_regions": box_counts.get("table", 0),
                "list_regions": box_counts.get("list-item", 0),
                "picture_placeholders": picture_placeholder_count(markdown_text),
                "native_math_signal": math_signal_score(native_text),
                "markdown_math_signal": math_signal_score(markdown_text),
            }

            needs_ocr, ocr_reasons = should_run_ocr(
                native_text=native_text,
                markdown_text=markdown_text,
                image_count=image_count,
                ocr_mode=ocr_mode,
                box_counts=box_counts,
                native_math_score=page_signal_summary["native_math_signal"],
                markdown_math_score=page_signal_summary["markdown_math_signal"],
                force_ocr=force_ocr,
            )

            ocr_markdown: str | None = None
            ocr_json_file: str | None = None

            if needs_ocr and prefer_ollama and image_cache_dir is not None:
                image_path = image_cache_dir / f"{pdf_path.stem}_p{page_number:04d}.png"
                if not image_path.exists():
                    pix = page.get_pixmap(matrix=fitz.Matrix(220 / 72.0, 220 / 72.0), alpha=False)
                    pix.save(image_path)
                try:
                    ocr_markdown = ollama_ocr_page(image_path, model=ollama_model)
                    if ocr_markdown:
                        ocr_json_file = str(image_path)
                        ocr_reasons.append("ollama-glm-ocr")
                    else:
                        ocr_reasons.append("ollama-empty-or-trivial")
                except Exception as exc:
                    ocr_reasons.append(f"ollama-error:{exc.__class__.__name__}")

            if needs_ocr and not ocr_markdown and glm_api_key:
                cache_key = f"{pdf_path.stem}_p{page_number:04d}"
                try:
                    ocr_markdown, ocr_json_file = glm_ocr_page_via_api(
                        page,
                        cache_dir=glm_cache_dir,
                        cache_key=cache_key,
                        api_key=glm_api_key,
                        ocr_mode=ocr_mode,
                        user_id=glm_user_id,
                    )
                    if ocr_markdown:
                        ocr_reasons.append("glm-api-ocr")
                except Exception as exc:
                    ocr_reasons.append(f"glm-error:{exc.__class__.__name__}")

            ocr_metrics = compute_text_quality(ocr_markdown or "")
            ocr_score = extraction_coverage_score(ocr_markdown or "", ocr_metrics, box_counts=box_counts)
            base_score = extraction_coverage_score(preferred_markdown, base_metrics, box_counts=box_counts)
            ocr_math_signal = math_signal_score(ocr_markdown or "")

            if ocr_markdown:
                if (
                    prefer_ocr
                    and (
                        ocr_score >= base_score - 0.02
                        and (
                            ocr_metrics["word_count"] >= max(base_metrics["word_count"] * 0.5, 30)
                            or ocr_math_signal >= page_signal_summary["native_math_signal"] + 2
                        )
                    )
                ) or (
                    ocr_score > base_score + 0.05
                    and ocr_metrics["word_count"] >= max(base_metrics["word_count"] * 0.8, 20)
                ):
                    preferred_markdown = ocr_markdown
                    preferred_source = "ocr"
                else:
                    preferred_source = f"{preferred_source}+ocr"

            preferred_text = clean_text(preferred_markdown)
            packages.append(
                {
                    "page_number": page_number,
                    "native_text": native_text,
                    "native_markdown": markdown_text,
                    "ocr_markdown": ocr_markdown,
                    "preferred_markdown": preferred_markdown,
                    "preferred_text": preferred_text,
                    "preferred_source": preferred_source,
                    "ocr_requested": needs_ocr,
                    "ocr_reasons": ocr_reasons,
                    "ocr_json_file": ocr_json_file,
                    "native_metrics": base_metrics,
                    "base_selection": base_diagnostics,
                    "ocr_metrics": ocr_metrics if ocr_markdown else None,
                    "toc_items": chunk.get("toc_items", []),
                    "tables": chunk.get("tables", []),
                    "images": chunk.get("images", []),
                    "page_boxes": page_boxes,
                    "page_signal_summary": page_signal_summary,
                }
            )

        return packages
    finally:
        doc.close()


def write_page_exports(page_packages: Sequence[dict[str, Any]], output_dir: Path) -> Path:
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = output_dir / "page_manifest.json"
    manifest_payload = []
    for package in page_packages:
        page_number = int(package["page_number"])
        stem = f"p{page_number:04d}"
        markdown_file = pages_dir / f"{stem}.md"
        text_file = pages_dir / f"{stem}.txt"
        markdown_file.write_text(
            (package.get("preferred_markdown") or "").strip() + "\n",
            encoding="utf-8",
        )
        text_file.write_text(
            (package.get("preferred_text") or "").strip() + "\n",
            encoding="utf-8",
        )
        package["markdown_file"] = str(markdown_file)
        package["text_file"] = str(text_file)
        manifest_payload.append(
            {
                **package,
            }
        )

    manifest_path.write_text(
        json.dumps({"pages": manifest_payload}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


def chunk_markdown(chunk: Chunk, page_packages: Sequence[dict[str, Any]]) -> str:
    pieces = [
        f"# {chunk.title}",
        "",
        f"- Kind: {chunk.kind}",
        f"- Pages: {chunk.start_page}-{chunk.end_page}",
        f"- Path: {' > '.join(chunk.path)}",
        "",
    ]

    page_map = {int(package["page_number"]): package for package in page_packages}
    for page_number in range(chunk.start_page, chunk.end_page + 1):
        package = page_map.get(page_number)
        if not package:
            continue
        signals = package.get("page_signal_summary") or {}
        pieces.append(f"## Page {page_number}")
        pieces.append("")
        pieces.append(f"Source: {package['preferred_source']}")
        if package.get("ocr_requested"):
            reasons = ", ".join(package.get("ocr_reasons") or [])
            pieces.append(f"OCR requested: yes ({reasons})")
        signal_bits = []
        if signals.get("formula_regions"):
            signal_bits.append(f"formula={signals['formula_regions']}")
        if signals.get("table_regions"):
            signal_bits.append(f"table={signals['table_regions']}")
        if signals.get("picture_placeholders"):
            signal_bits.append(f"picture_placeholders={signals['picture_placeholders']}")
        if signal_bits:
            pieces.append(f"Signals: {', '.join(signal_bits)}")
        pieces.append("")
        pieces.append((package.get("preferred_markdown") or "").strip())
        pieces.append("")

    return "\n".join(pieces).strip() + "\n"


def chunk_text(chunk: Chunk, page_packages: Sequence[dict[str, Any]]) -> str:
    pieces = [
        f"Title: {chunk.title}",
        f"Kind: {chunk.kind}",
        f"Pages: {chunk.start_page}-{chunk.end_page}",
        f"Path: {' > '.join(chunk.path)}",
        "",
        "== Extracted Text ==",
        "",
    ]

    page_map = {int(package["page_number"]): package for package in page_packages}
    for page_number in range(chunk.start_page, chunk.end_page + 1):
        package = page_map.get(page_number)
        if not package:
            continue
        signals = package.get("page_signal_summary") or {}
        pieces.append(f"--- PAGE {page_number} [{package['preferred_source']}] ---")
        if package.get("ocr_requested"):
            reasons = ", ".join(package.get("ocr_reasons") or [])
            pieces.append(f"OCR requested: yes ({reasons})")
        signal_bits = []
        if signals.get("formula_regions"):
            signal_bits.append(f"formula={signals['formula_regions']}")
        if signals.get("table_regions"):
            signal_bits.append(f"table={signals['table_regions']}")
        if signals.get("picture_placeholders"):
            signal_bits.append(f"picture_placeholders={signals['picture_placeholders']}")
        if signal_bits:
            pieces.append(f"Signals: {', '.join(signal_bits)}")
        pieces.append(package.get("preferred_text") or "")
        pieces.append("")

    return "\n".join(pieces).strip() + "\n"


def write_chunk_exports(
    chunks: Sequence[Chunk],
    page_packages: Sequence[dict[str, Any]],
    output_dir: Path,
) -> None:
    chunk_dir = output_dir / "chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)

    for chunk in chunks:
        stem = f"p{chunk.start_page:04d}-p{chunk.end_page:04d}__{sanitize_filename(chunk.title)}"
        markdown_path = chunk_dir / f"{stem}.md"
        text_path = chunk_dir / f"{stem}.txt"
        markdown_path.write_text(chunk_markdown(chunk, page_packages), encoding="utf-8")
        text_path.write_text(chunk_text(chunk, page_packages), encoding="utf-8")
        chunk.markdown_file = str(markdown_path)
        chunk.text_file = str(text_path)


def load_outline_rows(pdf_path: Path) -> list[list[Any]]:
    doc = open_pdf(pdf_path)
    try:
        return doc.get_toc()
    finally:
        doc.close()


def chunks_from_outline_rows(
    outline_rows: Sequence[Sequence[Any]],
    total_pages: int,
    *,
    prefix: str | None = None,
    skip_pattern: re.Pattern[str] | None = None,
) -> list[Chunk]:
    if not outline_rows:
        return []

    filtered_rows: list[list[Any]] = []
    for row in outline_rows:
        if len(row) < 3:
            continue
        level = int(row[0])
        title = str(row[1]).strip()
        page_number = max(int(row[2]), 1)
        numbering = extract_numbering(title)
        if prefix and numbering and not numbering.startswith(prefix):
            if not title.lower().startswith(f"chapter {prefix}"):
                continue
        if skip_pattern and skip_pattern.search(title):
            continue
        filtered_rows.append([level, title, page_number])

    if not filtered_rows:
        return []

    base_level = min(int(row[0]) for row in filtered_rows)
    chunks: list[Chunk] = []
    stack: list[Chunk] = []

    for index, row in enumerate(filtered_rows, start=1):
        level = int(row[0])
        title = str(row[1]).strip()
        start_page = max(int(row[2]), 1)

        while stack and stack[-1].depth >= (level - base_level):
            stack.pop()

        numbering = extract_numbering(title)
        depth = max(level - base_level, 0)
        parent_id = stack[-1].id if stack else None
        path = [ancestor.title for ancestor in stack] + [title]

        chunk = Chunk(
            id=f"O_P{start_page:04d}_{index:04d}",
            kind="outline",
            title=title,
            numbering=numbering,
            depth=depth,
            start_page=start_page,
            end_page=start_page,
            page_count=1,
            parent_id=parent_id,
            path=path,
        )
        chunks.append(chunk)
        stack.append(chunk)

    for index, chunk in enumerate(chunks):
        next_page = total_pages + 1
        for candidate in chunks[index + 1 :]:
            if candidate.depth <= chunk.depth:
                next_page = candidate.start_page
                break
        chunk.end_page = max(next_page - 1, chunk.start_page)
        chunk.page_count = max(chunk.end_page - chunk.start_page + 1, 1)

    return chunks


def detect_headings_from_pages(
    page_packages: Sequence[dict[str, Any]],
    *,
    prefix: str | None = None,
    skip_pattern: re.Pattern[str] | None = None,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    seen_titles: set[str] = set()

    for package in page_packages:
        page_number = int(package["page_number"])
        text = package.get("preferred_markdown") or package.get("preferred_text") or ""
        for line in text.splitlines()[:16]:
            candidate = normalize_heading_line(line)
            if not candidate or len(candidate) > 180:
                continue

            match = NUMBERED_HEADING.match(candidate)
            if not match:
                continue

            numbering = match.group("number")
            if prefix and numbering and not numbering.startswith(prefix):
                if not candidate.lower().startswith(f"chapter {prefix}"):
                    continue
            if skip_pattern and skip_pattern.search(candidate):
                continue
            if not looks_like_structural_heading(candidate, numbering):
                continue
            if candidate in seen_titles:
                continue

            seen_titles.add(candidate)
            chunks.append(
                Chunk(
                    id=f"H_P{page_number:04d}_{len(chunks) + 1:04d}",
                    kind="heading",
                    title=candidate,
                    numbering=numbering,
                    depth=relative_depth(numbering, prefix),
                    start_page=page_number,
                    end_page=page_number,
                    page_count=1,
                    parent_id=None,
                    path=[candidate],
                )
            )

    chunks.sort(key=lambda item: (item.start_page, item.depth))
    if not chunks:
        return []
    total_pages = max(int(pkg["page_number"]) for pkg in page_packages)
    return attach_chunk_hierarchy(chunks, total_pages=total_pages)


def attach_chunk_hierarchy(chunks: list[Chunk], total_pages: int) -> list[Chunk]:
    stack: list[Chunk] = []
    for index, chunk in enumerate(chunks):
        while stack and stack[-1].depth >= chunk.depth:
            stack.pop()

        chunk.parent_id = stack[-1].id if stack else None
        chunk.path = [ancestor.title for ancestor in stack] + [chunk.title]
        stack.append(chunk)

        next_page = total_pages + 1
        for candidate in chunks[index + 1 :]:
            if candidate.depth <= chunk.depth:
                next_page = candidate.start_page
                break
        chunk.end_page = max(next_page - 1, chunk.start_page)
        chunk.page_count = max(chunk.end_page - chunk.start_page + 1, 1)

    return chunks


def microchunk_large_sections(
    chunks: Sequence[Chunk],
    *,
    max_relative_depth: int,
    max_pages_per_chunk: int,
    min_pages_for_microchunk: int,
) -> list[Chunk]:
    children_by_parent: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        if chunk.parent_id:
            children_by_parent.setdefault(chunk.parent_id, []).append(chunk)

    expanded = list(chunks)
    for chunk in chunks:
        if chunk.depth > max_relative_depth:
            continue
        if chunk.id in children_by_parent:
            continue
        if chunk.page_count < min_pages_for_microchunk:
            continue

        parts = (chunk.page_count + max_pages_per_chunk - 1) // max_pages_per_chunk
        if parts <= 1:
            continue

        for index in range(parts):
            start_page = chunk.start_page + index * max_pages_per_chunk
            end_page = min(chunk.end_page, start_page + max_pages_per_chunk - 1)
            expanded.append(
                Chunk(
                    id=f"{chunk.id}_M{index + 1:02d}",
                    kind="microchunk",
                    title=f"{chunk.title} (Part {index + 1})",
                    numbering=chunk.numbering,
                    depth=chunk.depth + 1,
                    start_page=start_page,
                    end_page=end_page,
                    page_count=end_page - start_page + 1,
                    parent_id=chunk.id,
                    path=chunk.path + [f"Part {index + 1}"],
                )
            )

    expanded.sort(key=lambda item: (item.start_page, item.depth, item.kind != "outline"))
    return expanded


def selected_chunks(chunks: Sequence[Chunk], max_relative_depth: int) -> list[Chunk]:
    return [chunk for chunk in chunks if chunk.depth <= max_relative_depth or chunk.kind == "microchunk"]


def write_chunk_manifest(
    pdf_path: Path,
    chunks: Sequence[Chunk],
    page_packages: Sequence[dict[str, Any]],
    output_dir: Path,
) -> tuple[Path, Path]:
    manifest_path = output_dir / "subsection_manifest.json"
    payload = {
        "source_pdf": str(pdf_path),
        "page_count": len(page_packages),
        "entry_count": len(chunks),
        "pages": page_packages,
        "entries": [asdict(chunk) for chunk in chunks],
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    index_path = output_dir / "subsection_index.md"
    lines = [f"# Subsection Index for {pdf_path.name}", ""]
    for chunk in chunks:
        lines.append(
            f"- `{chunk.kind}` L{chunk.depth} p.{chunk.start_page}-{chunk.end_page}: "
            f"{chunk.title}"
        )
    index_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return manifest_path, index_path


def summarize_page_sources(page_packages: Sequence[dict[str, Any]]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for package in page_packages:
        source = str(package.get("preferred_source", "unknown"))
        summary[source] = summary.get(source, 0) + 1
    return summary
