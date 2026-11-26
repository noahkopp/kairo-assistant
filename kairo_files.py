"""Kairo's files folder: documents you want Kairo to know (syllabi, schedules, notes).

Put PDFs, Word docs (.docx), or text files in the `files` folder inside Kairo's folder.
"""
from pathlib import Path

FILES = Path(__file__).resolve().parent / "files"
TEXT = {".txt", ".md", ".csv", ".json", ".html", ".htm"}
MAX_CHARS = 30000


def list_files(folder=""):
    FILES.mkdir(exist_ok=True)
    base = (FILES / folder).resolve()
    if not str(base).startswith(str(FILES.resolve())):
        raise ValueError("Only the files folder can be listed.")
    return [{"name": str(p.relative_to(FILES)), "kb": round(p.stat().st_size / 1024)}
            for p in sorted(base.rglob("*")) if p.is_file() and not p.name.startswith(".")]


def _find(name):
    p = (FILES / name).resolve()
    if not str(p).startswith(str(FILES.resolve())):
        raise ValueError("Only files in the files folder can be read.")
    if p.exists():
        return p
    matches = [f for f in FILES.rglob("*") if f.is_file() and name.lower() in f.name.lower()]
    if not matches:
        raise FileNotFoundError(f"No file matching '{name}'. Use list_files to see what's there.")
    return matches[0]


def read_file(name, search=""):
    """Text of a file (PDF, .docx, or text). With search=, only paragraphs containing it."""
    p = _find(name)
    ext = p.suffix.lower()
    if ext == ".pdf":
        from pypdf import PdfReader
        text = "\n".join((page.extract_text() or "") for page in PdfReader(str(p)).pages)
    elif ext == ".docx":
        import docx
        d = docx.Document(str(p))
        text = "\n".join(par.text for par in d.paragraphs)
        for table in d.tables:
            for row in table.rows:
                text += "\n" + " | ".join(c.text for c in row.cells)
    elif ext in TEXT or not ext:
        text = p.read_text(errors="replace")
    else:
        raise ValueError(f"Can't read {ext} files yet. Use PDF, .docx, or text.")
    if search:
        paras = [x for x in text.split("\n\n") if search.lower() in x.lower()] or \
                [x for x in text.splitlines() if search.lower() in x.lower()]
        text = "\n\n".join(paras) or f"(No mention of '{search}' in {p.name})"
    cut = len(text) > MAX_CHARS
    return {"file": str(p.relative_to(FILES)), "text": text[:MAX_CHARS],
            "truncated": cut, "note": "Use search= to find a specific part." if cut else ""}
