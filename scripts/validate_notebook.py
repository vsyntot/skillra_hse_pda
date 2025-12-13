"""Execute the main notebook and export an input-free HTML report."""

from __future__ import annotations

import base64
import mimetypes
import os
import re
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
CUSTOM_CSS_PATH = config.NOTEBOOK_REPORTS_DIR / "style.css"

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
  const slugCounts = {};

  const slugify = (text) => {
    const base = text.toLowerCase().replace(/[^a-z0-9\u0400-\u04ff]+/g, '-').replace(/(^-|-$)/g, '');
    const count = slugCounts[base] ?? 0;
    slugCounts[base] = count + 1;
    return count ? `${base}-${count}` : base;
  };

  let currentSection;

  headings.forEach((h) => {
    const text = h.textContent?.trim();
    if (!text) return;

    if (!h.id) {
      h.id = slugify(text);
    }

    if (h.tagName === 'H1') {
      const li = document.createElement('li');
      li.classList.add('toc-level-1');
      const link = document.createElement('a');
      link.textContent = text;
      link.href = `#${h.id}`;
      li.appendChild(link);

      const nested = document.createElement('ul');
      nested.classList.add('toc-sublist');
      li.appendChild(nested);
      tocList.appendChild(li);
      currentSection = nested;
      return;
    }

    if (h.tagName === 'H2') {
      const targetList = currentSection || tocList;
      const li = document.createElement('li');
      li.classList.add('toc-level-2');
      const link = document.createElement('a');
      link.textContent = text;
      link.href = `#${h.id}`;
      li.appendChild(link);
      targetList.appendChild(li);
    }
  });
});
</script>
"""


DEFAULT_INLINE_CSS = """
:root {
    color-scheme: light;
}

body {
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    background: #f8fafc;
    color: #0f172a;
    margin: 0;
    line-height: 1.7;
}

.jp-Notebook {
    max-width: 1100px;
    margin: 28px auto 40px auto;
    padding: 28px 36px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    box-shadow: 0 10px 26px rgba(15, 23, 42, 0.07);
}
"""


def load_custom_css() -> str:
    """Load CSS from the repository so the HTML report stays stylized.

    Falls back to a minimal inline theme if the file is missing to avoid
    breaking the export step in constrained environments.
    """

    try:
        return CUSTOM_CSS_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(
            f"Предупреждение: не найден {CUSTOM_CSS_PATH}, "
            "используется встроенный базовый стиль."
        )
        return DEFAULT_INLINE_CSS


def inject_toc(html: str) -> str:
    """Insert a lightweight table of contents after the <body> tag."""

    marker = "<body>"
    if marker not in html:
        return html
    return html.replace(marker, f"{marker}\n{TOC_SNIPPET}", 1)


def embed_local_images(html: str) -> str:
    """Inline local images referenced by <img src> into data URLs.

    Nbconvert already embeds matplotlib outputs, but images referenced via
    ``<img src="reports/figures/...">`` may remain as external files.
    This helper reads such files and replaces the ``src`` attribute with a
    base64-encoded data URL to guarantee the HTML report is self-contained.
    """

    def to_data_uri(src: str) -> str:
        if src.startswith(("data:", "http://", "https://")):
            return src

        candidate_paths = [ROOT / src, NOTEBOOK.parent / src]
        for path in candidate_paths:
            if path.exists():
                mime, _ = mimetypes.guess_type(path.name)
                encoded = base64.b64encode(path.read_bytes()).decode("ascii")
                return f"data:{mime or 'application/octet-stream'};base64,{encoded}"

        return src

    pattern = re.compile(r"(<img[^>]+src=)([\"'])([^\"']+)([\"'][^>]*>)", re.IGNORECASE)

    def replacer(match: re.Match[str]) -> str:
        prefix, quote, src, suffix = match.groups()
        inlined = to_data_uri(src)
        return f"{prefix}{quote}{inlined}{quote}{suffix}"

    return pattern.sub(replacer, html)


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
    exporter.embed_images = True

    resources = {
        "metadata": {"name": NOTEBOOK.stem},
        "inlining": {"css": [load_custom_css()]},
        "config": {
            "InlineBackend": {
                "figure_format": "png",
                "rc": {"figure.dpi": 110},
            }
        },
    }

    body, _ = exporter.from_notebook_node(nb, resources=resources)
    body = inject_toc(body)
    return embed_local_images(body)


def main() -> None:
    """Run pipeline, execute notebook, and export an investor-ready HTML report."""

    config.ensure_directories()

    pipeline_script = Path(__file__).resolve().parent / "run_pipeline.py"
    subprocess.run([sys.executable, str(pipeline_script)], check=True)

    executed_nb = execute_notebook()
    html = export_to_html(executed_nb)
    html_path = OUTPUT_HTML.resolve()
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")

    print(f"HTML-отчёт сохранён в {html_path}")


if __name__ == "__main__":
    main()
