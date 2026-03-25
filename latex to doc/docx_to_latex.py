from __future__ import annotations

import re
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

import pypandoc


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "v": "urn:schemas-microsoft-com:vml",
}


@dataclass
class HeaderInfo:
    lines: list[str]
    has_image: bool


@dataclass
class DocxLayout:
    header: HeaderInfo
    instructions: list[str]
    question_blocks: list[str]
    page_breaks: int


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_turkish(text: str) -> str:
    table = str.maketrans(
        {
            "ð": "ğ",
            "Ð": "Ğ",
            "ý": "ı",
            "Ý": "İ",
            "þ": "ş",
            "Þ": "Ş",
        }
    )
    return text.translate(table)


def _extract_texts_from_xml(root: ET.Element) -> list[str]:
    lines: list[str] = []
    for para in root.findall(".//w:p", NS):
        text = "".join(t.text or "" for t in para.findall(".//w:t", NS))
        text = _normalize_ws(text)
        if text:
            lines.append(_normalize_turkish(text))
    return lines


def _read_header(zip_file: zipfile.ZipFile, header_name: str) -> HeaderInfo:
    root = ET.fromstring(zip_file.read(header_name))
    rel_name = f"word/_rels/{Path(header_name).name}.rels"
    has_image = False
    if rel_name in zip_file.namelist():
        rel_xml = zip_file.read(rel_name).decode("utf-8", errors="ignore")
        has_image = "relationships/image" in rel_xml
    has_image = has_image or bool(root.findall(".//v:imagedata", NS))
    return HeaderInfo(lines=_extract_texts_from_xml(root), has_image=has_image)


def _extract_layout(source: Path) -> DocxLayout:
    with zipfile.ZipFile(source) as zip_file:
        header_name = "word/header1.xml"
        if header_name not in zip_file.namelist():
            header_name = "word/header2.xml"
        header = (
            _read_header(zip_file, header_name)
            if header_name in zip_file.namelist()
            else HeaderInfo(lines=[], has_image=False)
        )

        root = ET.fromstring(zip_file.read("word/document.xml"))
        body = root.find("w:body", NS)
        if body is None:
            raise RuntimeError("DOCX body bulunamadi.")

        instructions: list[str] = []
        page_breaks = len(root.findall('.//w:br[@w:type="page"]', NS))

        for child in list(body):
            tag = child.tag.rsplit("}", 1)[-1]
            if tag != "p":
                continue
            text = "".join(t.text or "" for t in child.findall(".//w:t", NS))
            text = _normalize_ws(text)
            if not text:
                continue
            if text == "SORULAR":
                break
            instructions.append(_normalize_turkish(text))

    return DocxLayout(
        header=header,
        instructions=instructions,
        question_blocks=[],
        page_breaks=page_breaks,
    )


def _run_pandoc(source: Path, tmp_dir: Path) -> Path:
    temp_docx = tmp_dir / "source.docx"
    temp_tex = tmp_dir / "pandoc_output.tex"
    media_dir = tmp_dir / "media"
    shutil.copy2(source, temp_docx)
    pypandoc.convert_file(
        str(temp_docx),
        "latex",
        outputfile=str(temp_tex),
        extra_args=[
            "--standalone",
            "--wrap=none",
            f"--extract-media={media_dir}",
        ],
    )
    return temp_tex


def _extract_question_blocks(pandoc_tex: str) -> list[str]:
    pattern = re.compile(
        r"\\textbf\{(?P<num>\d+)\.\}\s*"
        r"\\end\{minipage\}\s*&\s*\\begin\{minipage\}\[b\]\{\\linewidth\}\\raggedright\s*"
        r"(?P<body>.*?)"
        r"\\end\{minipage\}",
        re.DOTALL,
    )
    blocks: list[str] = []
    for match in pattern.finditer(pandoc_tex):
        num = match.group("num")
        body = match.group("body").strip()
        body = _cleanup_latex_block(body)
        blocks.append(f"\\textbf{{Soru {num}}}\n\n{body}")
    if not blocks:
        raise RuntimeError("Pandoc cikisindan soru bloklari ayrilamadi.")
    return blocks


def _cleanup_latex_block(text: str) -> str:
    replacements = {
        r"\ \ \ \ \ ": " ",
        r"\ \ ": " ",
        r"\ dx": r"\,dx",
        r"\ dy": r"\,dy",
        r"\ ,": ",",
        r"\ \ ,": ",",
        r"\ y(": r" y(",
        r"y^{'''}": r"y'''",
        r"y^{''}": r"y''",
        r"y^{iv}": r"y^{(4)}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\\\(\s+", r"\\(", text)
    text = re.sub(r"\s+\\\)", r"\\)", text)
    text = re.sub(r"\[\s+", "[", text)
    text = re.sub(r"\s+\]", "]", text)
    return _normalize_turkish(text.strip())


def _latex_escape(text: str) -> str:
    text = text.replace("\\", r"\textbackslash{}")
    for old, new in {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }.items():
        text = text.replace(old, new)
    return text


def _build_header_block(header: HeaderInfo) -> str:
    left_lines = header.lines[:4]
    right_lines = header.lines[4:]

    left = r" \\ ".join(_latex_escape(line) for line in left_lines if line)
    right = r" \\ ".join(_latex_escape(line) for line in right_lines if line)

    logo = ""
    if header.has_image:
        logo = (
            r"\fbox{\begin{minipage}[c][1.7cm][c]{2.4cm}\centering"
            "\nLOGO\\par\nDummy\n\\end{minipage}}"
        )

    return rf"""
\newcommand{{\ExamHeader}}{{%
\noindent
\begin{{minipage}}[t]{{0.18\textwidth}}
{logo}
\end{{minipage}}
\hfill
\begin{{minipage}}[t]{{0.78\textwidth}}
\raggedright
\small
{left}
\par\medskip
\centering\bfseries
{right}
\end{{minipage}}
\par\medskip
\hrule
\vspace{{0.8em}}
}}
"""


def _build_document(layout: DocxLayout) -> str:
    question_pages = []
    total_pages = max(len(layout.question_blocks) + 1, layout.page_breaks + 1)
    for index, block in enumerate(layout.question_blocks, start=2):
        question_pages.append(
            "\\clearpage\n"
            "\\ExamHeader\n"
            f"\\pagestyle{{empty}}\n"
            f"\\textit{{Sayfa {index}/{total_pages}}}\n\n"
            f"{block}\n"
        )

    instruction_items = "\n".join(
        f"\\item {_latex_escape(line)}" for line in layout.instructions[1:]
    )
    title = _latex_escape(layout.instructions[0]) if layout.instructions else "SINAV"

    return rf"""\documentclass[12pt,a4paper]{{article}}
\usepackage{{geometry}}
\geometry{{margin=1.8cm}}
\usepackage{{fontspec}}
\usepackage{{unicode-math}}
\usepackage{{amsmath}}
\usepackage{{array}}
\usepackage{{booktabs}}
\usepackage{{enumitem}}
\usepackage{{graphicx}}
\usepackage{{xcolor}}
\usepackage{{fancyhdr}}
\usepackage{{titlesec}}
\usepackage{{setspace}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{0.6em}}
\setlist[itemize]{{leftmargin=1.5em, itemsep=0.4em}}
\pagestyle{{empty}}
\setmainfont{{Latin Modern Roman}}
\setmathfont{{Latin Modern Math}}
\titleformat{{\section}}{{\Large\bfseries}}{{}}{{0pt}}{{}}
{_build_header_block(layout.header)}
\begin{{document}}
\ExamHeader
\textit{{Sayfa 1/{total_pages}}}

\begin{{center}}
{{\Large\bfseries {title}}}
\end{{center}}

\begin{{itemize}}
{instruction_items}
\end{{itemize}}

\vfill
\begin{{center}}
{{\large\bfseries SORULAR}}
\end{{center}}
{''.join(question_pages)}
\end{{document}}
"""


def convert_docx_to_latex(source: Path, target: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Kaynak dosya bulunamadi: {source}")

    target.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="docx2tex_") as tmp_name:
        tmp_dir = Path(tmp_name)
        layout = _extract_layout(source)
        pandoc_tex_path = _run_pandoc(source, tmp_dir)
        pandoc_tex = pandoc_tex_path.read_text(encoding="utf-8")
        layout.question_blocks = _extract_question_blocks(pandoc_tex)
        final_tex = _build_document(layout)
        target.write_text(final_tex, encoding="utf-8")


def main() -> int:
    if len(sys.argv) not in {2, 3}:
        print(
            "Kullanim: python docx_to_latex.py <kaynak.docx> [hedef.tex]",
            file=sys.stderr,
        )
        return 1

    source = Path(sys.argv[1]).expanduser().resolve()
    target = (
        Path(sys.argv[2]).expanduser().resolve()
        if len(sys.argv) == 3
        else source.with_suffix(".tex")
    )

    convert_docx_to_latex(source, target)
    print(f"LaTeX dosyasi olusturuldu: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
