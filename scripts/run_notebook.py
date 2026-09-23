"""
Executes notebooks/rag_pipeline.ipynb cell by cell, verifying zero errors,
and populates the cell outputs and execution counts.
"""

import io
import json
import os
import sys
import contextlib

NOTEBOOK_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "notebooks", "rag_pipeline.ipynb")


def execute_notebook():
    print(f"[*] Loading notebook: {NOTEBOOK_PATH}")
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb = json.load(f)

    exec_globals = {"__name__": "__main__"}
    execution_counter = 1

    for idx, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue

        source_code = "".join(cell["source"])
        print(f"[*] Executing code cell {execution_counter} (cell index {idx})...")

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                exec(source_code, exec_globals)
        except Exception as e:
            print(f"[ERROR] Execution failed in cell {execution_counter}:\n{e}")
            raise

        stdout_val = stdout_capture.getvalue()
        stderr_val = stderr_capture.getvalue()

        outputs = []
        if stdout_val:
            outputs.append({
                "output_type": "stream",
                "name": "stdout",
                "text": [line + "\n" for line in stdout_val.split("\n")[:-1]] + ([stdout_val.split("\n")[-1]] if stdout_val.split("\n")[-1] else [])
            })
        if stderr_val:
            outputs.append({
                "output_type": "stream",
                "name": "stderr",
                "text": [line + "\n" for line in stderr_val.split("\n")[:-1]] + ([stderr_val.split("\n")[-1]] if stderr_val.split("\n")[-1] else [])
            })

        cell["execution_count"] = execution_counter
        cell["outputs"] = outputs
        print(f"    [OK] Cell {execution_counter} completed successfully ({len(stdout_val)} chars output)")
        execution_counter += 1

    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)

    print(f"\n[SUCCESS] Entire notebook executed top-to-bottom with 0 errors! Updated: {NOTEBOOK_PATH}")


if __name__ == "__main__":
    execute_notebook()
