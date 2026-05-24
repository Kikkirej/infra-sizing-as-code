import sys
from pathlib import Path

from src.build_runner import run

if __name__ == "__main__":
    sys.exit(run(repo_root=Path.cwd()))
