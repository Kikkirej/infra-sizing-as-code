import zipfile
from pathlib import Path


def archive(repo_root: Path, pdf_paths: list[Path]) -> Path | None:
    zip_path = repo_root / "output" / "documents.zip"
    if not pdf_paths:
        return None
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for pdf in pdf_paths:
            zf.write(pdf, pdf.name)
    return zip_path
