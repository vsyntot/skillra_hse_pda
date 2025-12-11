"""Execute the main notebook and export an input-free HTML report."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import nbformat
from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.skillra_pda import config  # noqa: E402

NOTEBOOK = config.NOTEBOOKS_DIR / "01_hse_project.ipynb"
DEFAULT_TIMEOUT = int(os.environ.get("NBEXEC_TIMEOUT", "900"))
OUTPUT_HTML = config.NOTEBOOK_REPORTS_DIR / "01_hse_project.html"

CUSTOM_CSS = """
body {
    font-family: "Segoe UI", Arial, sans-serif;
    margin: 24px;
    line-height: 1.6;
}
h1, h2, h3 {
    font-weight: 600;
    margin-top: 28px;
    margin-bottom: 12px;
}
#toc-container {
    background: #f5f7fb;
    border: 1px solid #e1e5f2;
    border-radius: 8px;
    padding: 16px 18px;
    margin-bottom: 24px;
}
#toc-container ul {
    list-style: none;
    padding-left: 0;
    margin: 8px 0 0 0;
}
#toc-container li {
    margin: 4px 0;
}
#toc-container a {
    color: #1d4ed8;
    text-decoration: none;
}
#toc-container a:hover {
    text-decoration: underline;
}
.jp-OutputArea img, .jp-OutputArea canvas, .jp-OutputArea svg {
    max-width: 100%;
    height: auto;
}
.jp-Cell-outputArea {
    padding: 8px 0 16px 0;
}
"""

TOC_SNIPPET = """
<div id=\"toc-container\">
  <h2>Оглавление</h2>
  <ul id=\"toc-list\"></ul>
</div>
<script>
document.addEventListener('DOMContentLoaded', () => {
  const tocList = document.getElementById('toc-list');
  if (!tocList) return;
  const headings = Array.from(document.querySelectorAll('h1, h2'));
  headings.forEach((h) => {
    const text = h.textContent?.trim();
    if (!text) return;
    if (!h.id) {
      const slug = text.toLowerCase().replace(/[^a-z0-9\u0400-\u04ff]+/g, '-').replace(/(^-|-$)/g, '');
      h.id = slug;
    }
    const li = document.createElement('li');
    if (h.tagName === 'H2') li.style.marginLeft = '12px';
    const link = document.createElement('a');
    link.textContent = text;
    link.href = `#${h.id}`;
    li.appendChild(link);
    tocList.appendChild(li);
  });
});
</script>
"""


def inject_toc(html: str) -> str:
    """Insert a lightweight table of contents after the <body> tag."""

    marker = "<body>"
    if marker not in html:
        return html
    return html.replace(marker, f"{marker}\n{TOC_SNIPPET}", 1)


def execute_notebook() -> nbformat.NotebookNode:
    """Run the primary notebook and return the executed notebook node."""

    with NOTEBOOK.open("r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    executor = ExecutePreprocessor(timeout=DEFAULT_TIMEOUT, kernel_name="python3")
    executor.preprocess(nb, {"metadata": {"path": NOTEBOOK.parent}})
    return nb


def export_to_html(nb: nbformat.NotebookNode) -> str:
    """Render notebook to HTML with hidden inputs and inline styling."""

    exporter = HTMLExporter(template_name="lab")
    exporter.exclude_input = True
    exporter.exclude_input_prompt = True
    exporter.exclude_output_prompt = True

    resources = {
        "metadata": {"name": NOTEBOOK.stem},
        "inlining": {"css": [CUSTOM_CSS]},
    }

    body, _ = exporter.from_notebook_node(nb, resources=resources)
    return inject_toc(body)


def main() -> None:
    """Run pipeline, execute notebook, and export an investor-ready HTML report."""

    config.ensure_directories()

    pipeline_script = Path(__file__).resolve().parent / "run_pipeline.py"
    subprocess.run([sys.executable, str(pipeline_script)], check=True)

    executed_nb = execute_notebook()
    html = export_to_html(executed_nb)
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")

    print(f"HTML-отчёт сохранён в {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
