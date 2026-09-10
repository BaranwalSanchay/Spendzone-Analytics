"""Run the real 7-section report job end to end -- this is the same work `python
main.py` does, MINUS the final PDF-conversion step -- to produce
backend/reports/token_usage_metrics.json with real per-section timing, token usage,
and cost (see backend/utils/token_tracking.py, wired into backend/main.py).

Why not `python main.py` directly: this machine's WeasyPrint install can't find its
native Pango/GObject libraries (a Windows GTK runtime dependency -- `pip install
weasyprint` succeeds, but importing it fails with "cannot load library
'libgobject-2.0-0'"). That's unrelated to the LLM pipeline and happens only in
markdown_to_pdf(), which runs after generate_markdown_report() has already written
report.md and token_usage_metrics.json. Rather than install a system-wide GTK runtime
to work around a step this measurement doesn't need, this script stubs out
utils.report_to_pdf's import and calls generate_markdown_report() directly -- the exact
same function `python main.py` calls for the part that matters here. `python main.py`
remains the real production command once WeasyPrint's native deps are available in a
given environment.

SPENDS REAL MONEY against GROQ_API_KEY/TAVILY_API_KEY in backend/.env -- requires
--confirm.

Run (from Spendzone-Analytics/, using backend/.venv or any environment with
backend/pyproject.toml's dependencies installed and backend/.env populated):
    backend/.venv/Scripts/python.exe scripts/metrics/run_report_job.py --confirm
"""
import argparse
import json
import os
import sys
import types

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm", action="store_true", required=True,
        help="Required acknowledgement that this spends real Groq/Tavily API credits.",
    )
    parser.add_argument(
        "--data-path", default=os.path.join(REPO_ROOT, "scripts", "sample_data"),
        help="Directory of CSVs for the agents to analyze (default: scripts/sample_data/, "
             "so the run has real data to query instead of an empty default backend/data/).",
    )
    args = parser.parse_args()

    sys.path.insert(0, BACKEND_DIR)
    os.chdir(BACKEND_DIR)  # main.py's relative paths (logs, reports/) assume this cwd

    # Stub out the PDF-conversion import so importing main.py doesn't require a
    # working WeasyPrint install -- see module docstring.
    stub = types.ModuleType("utils.report_to_pdf")

    def markdown_to_pdf(*args, **kwargs):
        raise RuntimeError(
            "PDF conversion unavailable in this environment (WeasyPrint needs native "
            "Pango/GObject libraries not installed here) -- this script only exercises "
            "generate_markdown_report(), not the PDF step."
        )

    stub.markdown_to_pdf = markdown_to_pdf
    sys.modules["utils.report_to_pdf"] = stub

    import main  # noqa: E402

    print("Running the full 7-section report job -- this spends real Groq/Tavily API credits.")
    print(f"Data path: {args.data_path}")
    md_file = main.generate_markdown_report(data_path=args.data_path)
    print(f"\nMarkdown report written to: {md_file}")

    metrics_path = os.path.join(BACKEND_DIR, "reports", "token_usage_metrics.json")
    with open(metrics_path, encoding="utf-8") as f:
        metrics = json.load(f)
    print(f"\nToken usage / cost metrics ({metrics_path}):")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
