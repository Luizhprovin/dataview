"""Convert a VS Code percent-format Python file to a basic .ipynb notebook."""

import json
from pathlib import Path


def flush_cell(cells, cell_type, source):
    if not source:
        return
    cells.append(
        {
            "cell_type": cell_type,
            "metadata": {},
            "source": source,
            **({"execution_count": None, "outputs": []} if cell_type == "code" else {}),
        }
    )


def clean_markdown(source):
    cleaned = []
    for line in source:
        if line.startswith("# "):
            cleaned.append(line[2:])
        elif line.startswith("#"):
            cleaned.append(line[1:])
        else:
            cleaned.append(line)
    return cleaned


def convert(py_path, ipynb_path):
    lines = py_path.read_text(encoding="utf-8").splitlines(keepends=True)
    cells = []
    current_type = "code"
    current = []

    for line in lines:
        if line.startswith("# %%"):
            if current:
                source = clean_markdown(current) if current_type == "markdown" else current
                flush_cell(cells, current_type, source)
            current_type = "markdown" if "[markdown]" in line else "code"
            current = []
        else:
            current.append(line)

    if current:
        source = clean_markdown(current) if current_type == "markdown" else current
        flush_cell(cells, current_type, source)

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    ipynb_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    convert(root / "notebooks" / "dataview.py", root / "notebooks" / "dataview.ipynb")
