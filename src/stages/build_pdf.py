import subprocess
import sys
from pathlib import Path


def build_pdf(repo_root: Path, adoc_paths: list[Path], errors: list[str]) -> list[Path]:
    produced = []
    for adoc_path in adoc_paths:
        shortname = adoc_path.stem
        result = subprocess.run(
            [
                "asciidoctor-pdf",
                "-r", "asciidoctor-diagram",
                "-a", f"pdf-theme=theme.yml",
                "-a", f"pdf-themesdir={repo_root}",
                "-B", str(repo_root),
                "-D", str(repo_root / "output"),
                str(adoc_path),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            msg = f"[{shortname}]: asciidoctor-pdf failed: {result.stderr.strip()}"
            errors.append(msg)
            print(f"ERROR {msg}", file=sys.stderr)
        else:
            pdf_path = repo_root / "output" / f"{shortname}.pdf"
            print(f"[build_pdf] {shortname} … OK")
            produced.append(pdf_path)

    return produced
