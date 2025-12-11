from __future__ import annotations

"""Execute the main project notebook after running the pipeline."""
import os
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.skillra_pda import config  # noqa: E402

NOTEBOOK = config.NOTEBOOKS_DIR / "01_hse_project.ipynb"
DEFAULT_TIMEOUT = int(os.environ.get("NBEXEC_TIMEOUT", "900"))


def main() -> None:
    """Run the pipeline and then execute the primary notebook."""
    config.ensure_directories()

    pipeline_script = Path(__file__).resolve().parent / "run_pipeline.py"
    subprocess.run([sys.executable, str(pipeline_script)], check=True)

    subprocess.run(
        [
            "jupyter",
            "nbconvert",
            "--to",
            "html",
            "--execute",
            "--no-input",
            f"--ExecutePreprocessor.timeout={DEFAULT_TIMEOUT}",
            "--output-dir",
            str(config.NOTEBOOK_REPORTS_DIR),
            "--output",
            "01_hse_project",
            str(NOTEBOOK),
        ],
        check=True,
    )

    print(f"HTML-отчёт сохранён в {config.NOTEBOOK_REPORTS_DIR / '01_hse_project.html'}")


if __name__ == "__main__":
    main()
