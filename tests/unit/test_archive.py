import zipfile
from pathlib import Path

from src.stages.archive import archive


def test_archive_two_pdfs(tmp_path):
    pdf_a = tmp_path / "product-a.pdf"
    pdf_b = tmp_path / "product-b.pdf"
    pdf_a.write_bytes(b"%PDF-a")
    pdf_b.write_bytes(b"%PDF-b")

    (tmp_path / "output").mkdir()
    zip_path = archive(tmp_path, [pdf_a, pdf_b])

    assert zip_path is not None
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert "product-a.pdf" in names
    assert "product-b.pdf" in names


def test_archive_empty_list_returns_none(tmp_path):
    (tmp_path / "output").mkdir()
    result = archive(tmp_path, [])
    assert result is None


def test_archive_member_names_are_basenames(tmp_path):
    pdf = tmp_path / "some" / "nested" / "product-x.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(b"%PDF-x")

    (tmp_path / "output").mkdir()
    zip_path = archive(tmp_path, [pdf])

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert names == ["product-x.pdf"]
