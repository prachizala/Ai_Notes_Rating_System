"""
NoteIQ Ratings Calibration Script
Compares automated AI evaluation scores against human-expert benchmark CSV ratings.
Outputs Mean Absolute Error (MAE) and root-mean-squared deviation per dimension
to enable systematic prompt and rubric tuning.
"""

import csv
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.analysis import evaluate_document_notes
from app.services.extraction import extract_document_text


def calibrate(documents_dir: str, benchmark_csv_path: str):
    print(f"[CALIBRATE] Loading benchmark scores from: {benchmark_csv_path}")
    if not os.path.exists(benchmark_csv_path):
        print(f"[ERROR] Benchmark CSV file not found at {benchmark_csv_path}")
        return

    benchmarks: Dict[str, Dict[str, float]] = {}
    with open(benchmark_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row["filename"]
            benchmarks[filename] = {
                "accuracy": float(row["human_accuracy"]),
                "explanation": float(row["human_explanation"]),
                "depth": float(row["human_depth"]),
                "examples": float(row["human_examples"]),
                "overall": float(row.get("human_overall", 0.0)),
            }

    print(f"[CALIBRATE] Found {len(benchmarks)} benchmark entries. Evaluating documents in {documents_dir}...")

    deviations = {"accuracy": [], "explanation": [], "depth": [], "examples": [], "overall": []}

    for filename, human_scores in benchmarks.items():
        doc_path = os.path.join(documents_dir, filename)
        if not os.path.exists(doc_path):
            print(f"[WARN] File {filename} not found in {documents_dir}, skipping.")
            continue

        with open(doc_path, "rb") as f:
            content = f.read()

        ext = filename.rsplit(".", 1)[-1]
        extraction = extract_document_text(ext, content)
        if extraction.failure_reason:
            print(f"[WARN] Extraction failed for {filename}: {extraction.failure_reason}")
            continue

        eval_res = evaluate_document_notes(
            units=extraction.units,
            stream="BCA",
            semester=1,
            subject="Computer Science",
            topic="Programming Fundamentals",
        )

        acc_diff = abs(eval_res["accuracy_score"] - human_scores["accuracy"])
        exp_diff = abs(eval_res["explanation_score"] - human_scores["explanation"])
        dep_diff = abs(eval_res["depth_score"] - human_scores["depth"])
        exm_diff = abs(eval_res["examples_score"] - human_scores["examples"])
        overall_diff = abs(eval_res["overall_score_display"] - human_scores["overall"])

        deviations["accuracy"].append(acc_diff)
        deviations["explanation"].append(exp_diff)
        deviations["depth"].append(dep_diff)
        deviations["examples"].append(exm_diff)
        deviations["overall"].append(overall_diff)

        print(f" -> {filename}: AI Display={eval_res['overall_score_display']} vs Human={human_scores['overall']} (diff={overall_diff:.2f})")

    print("\n" + "=" * 50)
    print(" CALIBRATION REPORT: MEAN ABSOLUTE ERROR (MAE)")
    print("=" * 50)
    for dim, diffs in deviations.items():
        if diffs:
            mae = sum(diffs) / len(diffs)
            print(f" - {dim.capitalize():<15}: MAE = {mae:.3f} stars")
        else:
            print(f" - {dim.capitalize():<15}: No data")
    print("=" * 50)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Calibrate NoteIQ AI Ratings against human ground-truth")
    parser.add_argument("--docs", default="./sample_docs", help="Path to sample documents directory")
    parser.add_argument("--csv", default="./sample_docs/benchmarks.csv", help="Path to ground truth CSV")
    args = parser.parse_args()

    calibrate(args.docs, args.csv)
