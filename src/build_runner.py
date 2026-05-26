import sys
from pathlib import Path

from src.loader import (
    check_products_json,
    check_theme,
    load_product,
    load_product_registry,
)
from src.stages.generate import generate
from src.stages.build_pdf import build_pdf
from src.stages.archive import archive


def run(repo_root: Path) -> int:
    check_theme(repo_root)
    check_products_json(repo_root)

    registry = load_product_registry(repo_root)

    errors: list[str] = []
    products = []
    for entry in registry:
        product = load_product(repo_root, entry["shortname"], entry["display_name"])
        if product is not None:
            products.append(product)
        else:
            errors.append(f"[{entry['shortname']}]: failed to load")

    adoc_paths = generate(repo_root, products, errors)
    pdf_paths = build_pdf(repo_root, adoc_paths, errors)
    zip_path = archive(repo_root, pdf_paths)

    if pdf_paths:
        print(f"Built {len(pdf_paths)} PDF(s): {', '.join(p.name for p in pdf_paths)}")
    if zip_path:
        print(f"Archive: {zip_path}")

    if errors:
        print(f"{len(errors)} error(s) occurred.", file=sys.stderr)
        return 1
    return 0
