"""
Main Application Entrypoint
SLM-Based Intelligent Network Configuration
Provides CLI, Web UI, Evaluation, and Test Suite runners.
"""

import argparse
import os
import subprocess
import sys

# Ensure root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from controller.agent import NetworkConfigAgent
from evaluation.evaluator import BenchmarkEvaluator


def main():
    parser = argparse.ArgumentParser(
        description="SLM-Based Intelligent Network Configuration (IEEE OJCOMS 2026)"
    )
    parser.add_argument("--ui", action="store_true", help="Launch Web Interface")
    parser.add_argument("--port", type=int, default=5000, help="Port for Web Interface (default: 5000)")
    parser.add_argument("--streamlit", action="store_true", help="Launch Streamlit Dashboard")
    parser.add_argument("--cli", action="store_true", help="Run interactive CLI pipeline")
    parser.add_argument("--query", type=str, default=None, help="Input requirement text for CLI mode")
    parser.add_argument("--device", type=str, default="Switch1", help="Target device hostname")
    parser.add_argument("--eval", action="store_true", help="Run 150-scenario benchmark evaluation")
    parser.add_argument("--samples", type=int, default=20, help="Number of evaluation samples to run")
    parser.add_argument("--test", action="store_true", help="Run automated pytest test suite")

    args = parser.parse_args()

    if args.ui:
        print("Launching SLM-Based Intelligent Network Configuration Web Interface...")
        from app.server import run_server
        run_server(port=args.port, host="127.0.0.1")
        return

    if args.streamlit:
        print("Launching SLM NetConfig Streamlit Dashboard...")
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "ui.py")
        subprocess.run([sys.executable, "-m", "streamlit", "run", ui_path])
        return

    if args.eval:
        print(f"Executing Benchmark Evaluation on {args.samples} scenarios...")
        evaluator = BenchmarkEvaluator()
        evaluator.run_benchmark(sample_limit=args.samples)
        return

    if args.test:
        print("Running pytest automated test suite...")
        subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])
        return

    if args.cli or args.query:
        query = args.query or input("Enter network requirement: ")
        agent = NetworkConfigAgent()
        print("\n" + "=" * 60)
        print(f"Processing Requirement: {query}")
        print("=" * 60)
        res = agent.process_request(query, device_name=args.device)
        print(f"\n[Detected Category]: {res['detected_category']}")
        print(f"[Verification Status]: {'APPROVED (PASSED)' if res['verified'] else 'REFINEMENT NEEDED'}")
        print(f"[Total Duration]: {res['total_duration_sec']}s")
        print("\n--- Generated Cisco IOS Configuration ---")
        print(res["final_config"])
        print("-----------------------------------------")
        if res.get("saved_in_repo"):
            print(f"Persisted in ConfigsRepo: {res['saved_in_repo']}")
        if res.get("packet_tracer_export", {}).get("txt_path"):
            print(f"Packet Tracer Script:     {res['packet_tracer_export']['txt_path']}")
        return

    # Default if no arguments passed
    print("SLM-Based Intelligent Network Configuration")
    print("Usage:")
    print("  python run.py --ui                  # Launch Streamlit web dashboard")
    print("  python run.py --cli --query '...'   # Run single query via CLI")
    print("  python run.py --eval --samples 20   # Run benchmark evaluation")
    print("  python run.py --test                # Run test suite")


if __name__ == "__main__":
    main()
