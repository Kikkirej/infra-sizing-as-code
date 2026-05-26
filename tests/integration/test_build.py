import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures" / "minimal-infra"
REPO_ROOT = Path(__file__).parent.parent.parent


@pytest.fixture
def infra_two_products(tmp_path):
    infra = tmp_path / "infra"
    shutil.copytree(FIXTURES, infra)
    shutil.copy(REPO_ROOT / "theme.yml", tmp_path / "theme.yml")
    return tmp_path


@pytest.fixture
def infra_one_broken(tmp_path):
    infra = tmp_path / "infra"
    shutil.copytree(FIXTURES, infra)
    shutil.copy(REPO_ROOT / "theme.yml", tmp_path / "theme.yml")
    shutil.rmtree(infra / "product-b" / "size-l")
    return tmp_path


@pytest.mark.integration
def test_two_product_build_produces_two_pdfs(infra_two_products):
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "build.py")],
        cwd=infra_two_products,
        capture_output=True,
        text=True,
    )
    output_dir = infra_two_products / "output"
    pdfs = list(output_dir.glob("*.pdf"))
    assert len(pdfs) == 2, f"Expected 2 PDFs, got {len(pdfs)}. stderr: {result.stderr}"
    assert result.returncode == 0


@pytest.mark.integration
def test_full_build_produces_zip(infra_two_products):
    subprocess.run(
        ["python3", str(REPO_ROOT / "build.py")],
        cwd=infra_two_products,
        capture_output=True,
    )
    zip_path = infra_two_products / "output" / "documents.zip"
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert len(names) == 2


@pytest.mark.integration
def test_partial_failure_zip_contains_only_successful_pdf(infra_one_broken):
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "build.py")],
        cwd=infra_one_broken,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    zip_path = infra_one_broken / "output" / "documents.zip"
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert len(names) == 1
    assert "product-a.pdf" in names
