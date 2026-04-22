#!/usr/bin/env python3
"""Convert PDF papers in raw/papers into markdown files."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import argparse
import importlib
import re

ROOT = Path(__file__).resolve().parents[1]
RAW_PAPERS = ROOT / "raw" / "papers"


@dataclass
class ExtractionResult:
    backend: str
    title: str | None
    text: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert PDFs under raw/papers into markdown files."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=RAW_PAPERS,
        help="Directory containing PDF files. Defaults to raw/papers.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing markdown files.",
    )
    parser.add_argument(
        "--backend",
        choices=["auto", "pypdf", "pymupdf"],
        default="auto",
        help="PDF extraction backend to use.",
    )
    return parser.parse_args()


def load_module(module_name: str):
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


def choose_backend(preferred: str) -> str:
    if preferred != "auto":
        return preferred

    if load_module("pypdf") is not None:
        return "pypdf"
    if load_module("fitz") is not None:
        return "pymupdf"

    raise RuntimeError(
        "No supported PDF library found. Install one of: `pip install pypdf` "
        "or `pip install pymupdf`."
    )


def clean_title(raw_title: str | None, fallback: str) -> str:
    title = (raw_title or "").strip()
    if title and title.lower() != "untitled":
        return title
    return fallback.strip() or "Untitled Paper"


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x0c", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_with_pypdf(pdf_path: Path) -> ExtractionResult:
    pypdf = load_module("pypdf")
    if pypdf is None:
        raise RuntimeError("`pypdf` is not installed.")

    reader = pypdf.PdfReader(str(pdf_path))
    chunks: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        page_text = page_text.strip()
        if page_text:
            chunks.append(f"## Page {index}\n\n{page_text}")

    metadata = reader.metadata or {}
    title = None
    if hasattr(metadata, "title"):
        title = metadata.title
    elif isinstance(metadata, dict):
        title = metadata.get("/Title")

    return ExtractionResult(
        backend="pypdf",
        title=title,
        text=clean_text("\n\n".join(chunks)),
    )


def extract_with_pymupdf(pdf_path: Path) -> ExtractionResult:
    fitz = load_module("fitz")
    if fitz is None:
        raise RuntimeError("`pymupdf` is not installed.")

    doc = fitz.open(pdf_path)
    try:
        chunks: list[str] = []
        for index, page in enumerate(doc, start=1):
            page_text = page.get_text("text").strip()
            if page_text:
                chunks.append(f"## Page {index}\n\n{page_text}")

        metadata = doc.metadata or {}
        title = metadata.get("title")
    finally:
        doc.close()

    return ExtractionResult(
        backend="pymupdf",
        title=title,
        text=clean_text("\n\n".join(chunks)),
    )


def extract_pdf(pdf_path: Path, backend: str) -> ExtractionResult:
    if backend == "pypdf":
        return extract_with_pypdf(pdf_path)
    if backend == "pymupdf":
        return extract_with_pymupdf(pdf_path)
    raise ValueError(f"Unsupported backend: {backend}")


def build_markdown(pdf_path: Path, backend: str, title: str, body: str) -> str:
    extracted_at = datetime.now().isoformat(timespec="seconds")
    source = pdf_path.relative_to(ROOT).as_posix()
    body = body or "_No extractable text found in this PDF._"
    return f"""---
source_pdf: {source}
extracted_at: {extracted_at}
extractor: {backend}
---

# {title}

> Auto-extracted from `{source}`.

{body}
"""


def convert_pdf(pdf_path: Path, *, force: bool, backend: str) -> str:
    md_path = pdf_path.with_suffix(".md")
    if md_path.exists() and not force:
        return f"skip existing: {md_path.relative_to(ROOT).as_posix()}"

    result = extract_pdf(pdf_path, backend)
    title = clean_title(result.title, pdf_path.stem)
    content = build_markdown(pdf_path, result.backend, title, result.text)
    md_path.write_text(content, encoding="utf-8")
    return f"created: {md_path.relative_to(ROOT).as_posix()}"


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    backend = choose_backend(args.backend)

    input_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = sorted(input_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"no pdf files found in {input_dir}")
        return

    created = 0
    skipped = 0

    for pdf_path in pdf_files:
        message = convert_pdf(pdf_path, force=args.force, backend=backend)
        print(message)
        if message.startswith("created:"):
            created += 1
        else:
            skipped += 1

    print(
        f"pdf_to_md done: created={created}, skipped={skipped}, backend={backend}"
    )


if __name__ == "__main__":
    main()
