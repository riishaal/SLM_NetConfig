"""
Agent / Controller Module
Central orchestrator of the SLM-Based Intelligent Network Configuration pipeline.
Implements the 4-component agent architecture from Section IV-B of IEEE OJCOMS 2026:
1. Requirement Loader
2. Prompt Manager
3. Execution Controller (Closed-Loop Refinement Cycle)
4. Result Logger
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.input_handler import InputHandler
from models.slm_engine import SLMEngine
from generation.config_generator import ConfigurationGenerator
from validation.validator import ConfigValidator
from correction.error_corrector import ErrorCorrector
from simulation.network_simulator import NetworkSimulator
from verification.verifier import NetworkVerifier
from simulation.packet_tracer_exporter import PacketTracerExporter


class NetworkConfigAgent:
    """Agent / Controller orchestrating end-to-end intent translation and closed-loop verification."""

    def __init__(
        self,
        output_dir: Optional[str] = None,
        max_refinement_loops: int = 3,
        load_model_weights: bool = False
    ):
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output"
        )
        os.makedirs(self.output_dir, exist_ok=True)
        self.configs_repo = os.path.join(self.output_dir, "ConfigsRepo")
        os.makedirs(self.configs_repo, exist_ok=True)

        self.max_refinement_loops = max_refinement_loops

        # Initialize subcomponents
        self.input_handler = InputHandler()
        self.slm_engine = SLMEngine(load_model_weights=load_model_weights)
        self.generator = ConfigurationGenerator(slm_engine=self.slm_engine)
        self.validator = ConfigValidator()
        self.corrector = ErrorCorrector()
        self.simulator = NetworkSimulator()
        self.verifier = NetworkVerifier(simulator=self.simulator)
        self.pt_exporter = PacketTracerExporter()

    def process_request(self, user_text: str, device_name: str = "Switch1") -> Dict[str, Any]:
        """
        Execute the complete autonomous agent perception-reasoning-action loop:
        Requirement Loader -> Prompt Manager -> SLM Generation -> Validation -> Error Correction -> Repo.
        """
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        cycle_history = []

        # 1. Requirement Loader
        raw_intake = self.input_handler.process_input(user_text)
        if not raw_intake["valid"]:
            return {
                "success": False,
                "error": raw_intake["error"],
                "total_duration_sec": 0,
                "cycles": []
            }

        # 2. Prompt Manager - Stage A: Intent Classification
        clf_result = self.slm_engine.classify_requirement(raw_intake["clean_text"])
        category = clf_result["category"]

        # 3. Prompt Manager - Stage B: Intermediate Steps Decomposition
        steps = self.slm_engine.generate_intermediate_steps(
            requirement_text=raw_intake["clean_text"],
            category=category,
            extracted_entities=raw_intake["extracted_entities"]
        )

        current_requirement = raw_intake["clean_text"]
        iteration = 1
        verified = False
        final_config = ""
        last_validation = {}
        last_correction = {}

        # 4. Closed-Loop Execution Controller
        while iteration <= self.max_refinement_loops and not verified:
            loop_start = time.time()

            # Generation Stage
            gen_result = self.generator.generate(
                requirement_text=current_requirement,
                category=category,
                steps=steps,
                extracted_entities=raw_intake["extracted_entities"],
                device_name=device_name
            )
            candidate_cli = gen_result["formatted_cli"]

            # Validation Stage (Batfish-style 3-tier checks)
            val_result = self.validator.validate_configuration(
                candidate_cli,
                user_intent=raw_intake
            )
            last_validation = val_result

            # Check approval criteria
            if val_result["status"] == "PASSED":
                verified = True
                final_config = candidate_cli
                cycle_history.append({
                    "iteration": iteration,
                    "action": "VALIDATION_PASSED",
                    "status": "APPROVED",
                    "config": candidate_cli,
                    "validation": val_result,
                    "duration_sec": round(time.time() - loop_start, 3)
                })
                break
            else:
                # Error Detection and Correction Stage
                corr_result = self.corrector.process_errors(candidate_cli, val_result)
                last_correction = corr_result

                cycle_history.append({
                    "iteration": iteration,
                    "action": "REFINEMENT_TRIGGERED",
                    "status": val_result["status"],
                    "config": candidate_cli,
                    "validation": val_result,
                    "correction": corr_result,
                    "duration_sec": round(time.time() - loop_start, 3)
                })

                # If auto-correctable, apply corrected config directly and re-validate
                if corr_result["is_fully_resolved"]:
                    re_val = self.validator.validate_configuration(corr_result["corrected_config"], user_intent=raw_intake)
                    if re_val["status"] == "PASSED":
                        verified = True
                        final_config = corr_result["corrected_config"]
                        last_validation = re_val
                        cycle_history.append({
                            "iteration": iteration + 1,
                            "action": "AUTO_CORRECTION_APPLIED",
                            "status": "APPROVED",
                            "config": final_config,
                            "validation": re_val,
                            "duration_sec": 0.05
                        })
                        break

                # Prepare refined prompt feedback for next iteration
                feedback_lines = [c["suggestion"] for c in corr_result["corrections"]]
                current_requirement = f"{raw_intake['clean_text']} (Correction instructions: {'; '.join(feedback_lines)})"
                iteration += 1

        total_duration = round(time.time() - start_time, 3)

        # 5. Network Simulation and Behavioral Verification
        sim_result = {}
        verif_result = {}
        pt_export = {}
        if verified and final_config:
            verif_result = self.verifier.verify_configuration(
                config_text=final_config,
                user_intent=raw_intake,
                hostname=device_name
            )
            sim_result = verif_result.get("snapshot", {})
            pt_export = self.pt_exporter.export_script(
                hostname=device_name,
                config_cli=final_config,
                scenario_name=f"{category}_{device_name}"
            )

        # 6. Result Logger and ConfigsRepo Transfer
        saved_file = None
        if verified and final_config:
            saved_file = self._save_to_configs_repo(device_name, final_config)

        execution_record = {
            "timestamp": timestamp,
            "user_input": user_text,
            "sanitized_input": raw_intake["clean_text"],
            "input_format": raw_intake["input_format"],
            "detected_category": category,
            "decomposed_steps": steps,
            "verified": verified,
            "final_config": final_config if verified else candidate_cli,
            "last_validation": last_validation,
            "last_correction": last_correction,
            "simulation_snapshot": sim_result,
            "verification_report": verif_result,
            "packet_tracer_export": pt_export,
            "iterations_count": len(cycle_history),
            "cycle_history": cycle_history,
            "total_duration_sec": total_duration,
            "saved_in_repo": saved_file
        }

        self._log_result(execution_record)
        return execution_record

    def _save_to_configs_repo(self, device_name: str, config_content: str) -> str:
        """Transfer approved configuration to ConfigsRepo for deployment and auditing."""
        ts_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{device_name}_{ts_slug}.cfg"
        filepath = os.path.join(self.configs_repo, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(config_content)
        return filepath

    def _log_result(self, record: Dict[str, Any]):
        """Persist execution log entry to JSONL log."""
        log_file = os.path.join(self.output_dir, "agent_execution_history.jsonl")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    agent = NetworkConfigAgent()
    req = "Create VLAN 10 named HR and VLAN 20 for Accounts on Switch1, and assign Fa0/1 to VLAN 10."
    print("Executing Agent Loop on requirement:", req)
    report = agent.process_request(req, device_name="Switch1")
    print("\nAgent Execution Result:")
    print("  Category:   ", report["detected_category"])
    print("  Verified:   ", report["verified"])
    print("  Iterations: ", report["iterations_count"])
    print("  Duration:   ", report["total_duration_sec"], "s")
    print("  ConfigsRepo:", report["saved_in_repo"])
    print("\nFinal Config Snippet:\n", report["final_config"][:250], "...\n")
