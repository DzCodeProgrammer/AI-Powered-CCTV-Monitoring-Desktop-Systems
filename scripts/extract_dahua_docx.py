"""Extract plain text from Dahua.docx (manager spec) into docs/extracted/."""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DOCX = Path.home() / "Documents" / "Dahua.docx"
OUT_PATH = PROJECT_ROOT / "docs" / "extracted" / "Dahua-docx.txt"


def extract_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
    text = re.sub(r"<w:tab[^/]*/>", "\t", xml)
    text = re.sub(r"</w:p>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def main() -> int:
    docx = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DOCX
    if not docx.is_file():
        print(f"FAIL: docx not found: {docx}")
        return 1
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = extract_docx(docx)
    OUT_PATH.write_text(text, encoding="utf-8")
    print(f"OK: wrote {OUT_PATH} ({len(text)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
