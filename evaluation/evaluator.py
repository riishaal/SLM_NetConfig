"""
Evaluation and Benchmarking Module
Implements Equations (1)-(9) from Section VII-B of IEEE OJCOMS 2026:
- Equation 2 & 3: Syntax Accuracy (1: full valid, 0: partial/unusual, -1: invalid)
- Equation 4: Goal Accuracy (1: full compliance, 0: partial, -1: failure)
- Equation 5 & 6: Normalized Translation Latency (min-max scaling)
- Equation 7-9: Complexity Score (arithmetic mean of normalized length and time)

Runs against the 150-scenario benchmark dataset and outputs comprehensive metrics.
"""

import json
import os
import sys
import time
from typing import Dict, Any, List, Optional
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controller.agent import NetworkConfigAgent
from dataset.dataset_loader import DatasetLoader


class BenchmarkEvaluator:
    """Evaluates the SLM-netconfig framework on the 150 benchmark test cases."""

    def __init__(self, agent: Optional[NetworkConfigAgent] = None, output_dir: Optional[str] = None):
        self.agent = agent or NetworkConfigAgent()
        self.loader = DatasetLoader()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir = output_dir or os.path.join(base_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)

    def run_benchmark(self, sample_limit: int = 150) -> Dict[str, Any]:
        """
        Execute evaluation across benchmark scenarios.
        """
        test_cases = self.loader.load_benchmark_150()
        if not test_cases:
            raise ValueError("No benchmark scenarios loaded from dataset/test/test_benchmark_150.jsonl")

        selected_cases = test_cases[:sample_limit]
        print(f"Beginning evaluation on {len(selected_cases)} benchmark scenarios...")

        results = []
        raw_durations = []
        raw_lengths = []

        start_all = time.time()

        for idx, case in enumerate(selected_cases, 1):
            req_text = case.get("requirement", "")
            expected_cfg = case.get("expected_configuration", "")
            cat = case.get("category", "GENERAL")

            t0 = time.time()
            record = self.agent.process_request(req_text, device_name=f"SW_{idx}")
            duration_sec = time.time() - t0

            val_rep = record["last_validation"]
            syntax_score = val_rep.get("syntax_score", 1)
            goal_score = val_rep.get("goal_score", 1)

            final_cfg = record.get("final_config", "")
            total_len = len(req_text) + len(final_cfg)

            raw_durations.append(duration_sec)
            raw_lengths.append(total_len)

            results.append({
                "benchmark_id": case.get("benchmark_id", idx),
                "category": cat,
                "requirement": req_text,
                "syntax_score": syntax_score,
                "goal_score": goal_score,
                "verified": record.get("verified", False),
                "iterations": record.get("iterations_count", 1),
                "duration_sec": duration_sec,
                "total_len": total_len,
                "errors": val_rep.get("errors", [])
            })

            if idx % 25 == 0 or idx == len(selected_cases):
                print(f"  Processed {idx}/{len(selected_cases)} scenarios...")

        total_eval_time = round(time.time() - start_all, 2)

        # Compute min-max normalized duration and length (Equations 6 & 8)
        min_d, max_d = min(raw_durations), max(raw_durations)
        min_l, max_l = min(raw_lengths), max(raw_lengths)

        d_range = (max_d - min_d) if (max_d - min_d) > 0 else 1.0
        l_range = (max_l - min_l) if (max_l - min_l) > 0 else 1.0

        for r in results:
            norm_dur = (r["duration_sec"] - min_d) / d_range
            norm_len = (r["total_len"] - min_l) / l_range
            complexity = (norm_dur + norm_len) / 2.0  # Equation 7
            r["norm_duration"] = round(norm_dur, 4)
            r["norm_len"] = round(norm_len, 4)
            r["complexity_score"] = round(complexity, 4)

        # Aggregated Metrics
        total_count = len(results)
        syntax_correct = sum(1 for r in results if r["syntax_score"] == 1)
        syntax_partial = sum(1 for r in results if r["syntax_score"] == 0)
        syntax_incorrect = sum(1 for r in results if r["syntax_score"] == -1)

        goal_correct = sum(1 for r in results if r["goal_score"] == 1)
        goal_partial = sum(1 for r in results if r["goal_score"] == 0)
        goal_incorrect = sum(1 for r in results if r["goal_score"] == -1)

        avg_duration = round(float(np.mean(raw_durations)), 4)
        avg_complexity = round(float(np.mean([r["complexity_score"] for r in results])), 4)
        verified_count = sum(1 for r in results if r["verified"])

        report = {
            "evaluation_timestamp": time.ctime(),
            "total_scenarios_evaluated": total_count,
            "total_benchmark_duration_sec": total_eval_time,
            "average_latency_sec": avg_duration,
            "mean_complexity_score": avg_complexity,
            "overall_verification_rate": round((verified_count / total_count) * 100, 2),
            "syntax_accuracy": {
                "correct_count": syntax_correct,
                "partially_correct_count": syntax_partial,
                "incorrect_count": syntax_incorrect,
                "correct_pct": round((syntax_correct / total_count) * 100, 2),
                "partially_correct_pct": round((syntax_partial / total_count) * 100, 2),
                "incorrect_pct": round((syntax_incorrect / total_count) * 100, 2)
            },
            "goal_accuracy": {
                "correct_count": goal_correct,
                "partially_correct_count": goal_partial,
                "incorrect_count": goal_incorrect,
                "correct_pct": round((goal_correct / total_count) * 100, 2),
                "partially_correct_pct": round((goal_partial / total_count) * 100, 2),
                "incorrect_pct": round((goal_incorrect / total_count) * 100, 2)
            },
            "individual_results": results
        }

        # Save to disk
        out_json = os.path.join(self.output_dir, "benchmark_evaluation_report.json")
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print(f"\nEvaluation Complete!")
        print(f"  Syntax Correct Rate: {report['syntax_accuracy']['correct_pct']}%")
        print(f"  Goal Correct Rate:   {report['goal_accuracy']['correct_pct']}%")
        print(f"  Average Latency:     {report['average_latency_sec']}s")
        print(f"  Mean Complexity:     {report['mean_complexity_score']}")
        print(f"  Report saved to:     {out_json}")

        return report


if __name__ == "__main__":
    evaluator = BenchmarkEvaluator()
    # Run evaluation on first 20 cases for fast demonstration
    report = evaluator.run_benchmark(sample_limit=20)
