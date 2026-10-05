"""
Dataset Loader Utility Module
Provides standardized accessors for training, validation, and benchmark datasets.
"""

import json
import os
from typing import List, Dict, Any, Generator


class DatasetLoader:
    """Utility class to read and iterate over network configuration datasets."""

    def __init__(self, dataset_dir: str = None):
        if dataset_dir is None:
            dataset_dir = os.path.dirname(os.path.abspath(__file__))
        self.dataset_dir = dataset_dir

        self.train_req_file = os.path.join(dataset_dir, "train", "train_requirement_config.jsonl")
        self.train_ques_file = os.path.join(dataset_dir, "train", "train_question_config.jsonl")
        self.val_file = os.path.join(dataset_dir, "validation", "val_dataset.jsonl")
        self.test_file = os.path.join(dataset_dir, "test", "test_benchmark_150.jsonl")

    def _read_jsonl(self, filepath: str) -> List[Dict[str, Any]]:
        records = []
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
        return records

    def load_training_requirements(self) -> List[Dict[str, Any]]:
        return self._read_jsonl(self.train_req_file)

    def load_training_questions(self) -> List[Dict[str, Any]]:
        return self._read_jsonl(self.train_ques_file)

    def load_validation_set(self) -> List[Dict[str, Any]]:
        return self._read_jsonl(self.val_file)

    def load_benchmark_150(self) -> List[Dict[str, Any]]:
        return self._read_jsonl(self.test_file)

    def get_benchmark_case(self, benchmark_id: int) -> Dict[str, Any]:
        """Retrieve a specific benchmark scenario (1-150)."""
        benchmark = self.load_benchmark_150()
        for case in benchmark:
            if case.get("benchmark_id") == benchmark_id:
                return case
        return {}


if __name__ == "__main__":
    loader = DatasetLoader()
    bm = loader.load_benchmark_150()
    print(f"Loaded {len(bm)} benchmark scenarios.")
    if bm:
        print("Sample Case 1:", bm[0]["requirement"])
        print("Expected Config:\n", bm[0]["expected_configuration"])
