#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import re
import sys


SUSPICIOUS_PATTERNS: list[tuple[str, str]] = [
    (r"\bIcindekiler\b", "İçindekiler"),
    (r"\b[Cc]ozum\b", "Çözüm"),
    (r"\b[Oo]rnek\b", "Örnek"),
    (r"\b[Tt]urkce\b", "Türkçe"),
    (r"\b[Oo]grenci\b", "öğrenci"),
    (r"\b[Oo]gretim\b", "öğretim"),
    (r"\b[Oo]gretim\b", "öğretim"),
    (r"\b[Bb]aglanti(si|sı|nin)?\b", "bağlantı"),
    (r"\b[Ss]ecim(i|in|ler)?\b", "seçim"),
    (r"\b[Yy]api(si|sı|lar|lari)?\b", "yapı"),
    (r"\b[Uu]zanti(si|sı|lar)?\b", "uzantı"),
    (r"\b[Kk]apanis\b", "kapanış"),
    (r"\b[Dd]onemi\b", "dönemi"),
    (r"\b[Bb]asari(li|lı|ya)?\b", "başarı"),
    (r"\b[Ss]ayisi\b", "sayısı"),
    (r"\b[Oo]lasiligi\b", "olasılığı"),
    (r"\b[Yy]aklas", "yaklaş"),
    (r"\b[Gg]orme\b", "görme"),
    (r"\b[Gg]oster", "göster"),
    (r"\b[Cc]ekis", "çekiş"),
    (r"\b[Dd]egil\b", "değil"),
    (r"\b[Oo]nce\b", "önce"),
    (r"\b[Ii]lac\b", "ilaç"),
    (r"\b[Ii]lk\b", "ilk / İlk -> İlk"),
]

MISSING_CHAR_LOG_PATTERNS = (
    "Missing character",
    "There is no ",
)


def scan_text(text: str) -> list[str]:
    findings: list[str] = []
    for pattern, suggestion in SUSPICIOUS_PATTERNS:
        for match in re.finditer(pattern, text):
            findings.append(
                f"suspicious transliteration '{match.group(0)}' at byte {match.start()} -> try '{suggestion}'"
            )
    return findings


def scan_log(log_path: pathlib.Path) -> list[str]:
    if not log_path.exists():
        return []
    findings: list[str] = []
    for line_no, line in enumerate(log_path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        if any(token in line for token in MISSING_CHAR_LOG_PATTERNS):
            findings.append(f"log issue at line {line_no}: {line.strip()}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Turkish character integrity in LaTeX decks.")
    parser.add_argument("tex_file", type=pathlib.Path)
    parser.add_argument("--log", type=pathlib.Path, default=None)
    args = parser.parse_args()

    tex_path = args.tex_file
    if not tex_path.exists():
        print(f"file not found: {tex_path}", file=sys.stderr)
        return 2

    text = tex_path.read_text(encoding="utf-8", errors="ignore")
    findings = scan_text(text)

    log_path = args.log or tex_path.with_suffix(".log")
    findings.extend(scan_log(log_path))

    if findings:
        print("Turkish integrity check failed:")
        for item in findings:
            print(f"- {item}")
        return 1

    print("Turkish integrity check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
