import sys
from pathlib import Path

from src.loader import Product
from src.renderer import render_product_document


def generate(repo_root: Path, products: list[Product], errors: list[str]) -> list[Path]:
    output_dir = repo_root / "output"
    output_dir.mkdir(exist_ok=True)

    written = []
    for product in products:
        try:
            content = render_product_document(product)
            adoc_path = output_dir / f"{product.shortname}.adoc"
            adoc_path.write_text(content)
            print(f"[generate] {product.shortname} … OK")
            written.append(adoc_path)
        except Exception as e:
            msg = f"[{product.shortname}]: generate failed: {e}"
            errors.append(msg)
            print(f"ERROR {msg}", file=sys.stderr)

    return written
