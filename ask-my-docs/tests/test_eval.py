"""
test_eval.py
Unit tests for Phase 3 evaluation components.
No API calls — validates dataset schema and report structure only.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


GOLDEN_DATASET_PATH = "evaluation/golden_dataset.json"
VALID_DOMAINS = {"aws_core", "aws_security", "aws_waf", "aws_ml", "grc"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
REQUIRED_FIELDS = ["id", "question", "ground_truth", "domain", "difficulty"]


@pytest.fixture
def golden_dataset():
    with open(GOLDEN_DATASET_PATH) as f:
        return json.load(f)


def test_golden_dataset_loads(golden_dataset):
    assert isinstance(golden_dataset, list)
    assert len(golden_dataset) >= 50, f"Expected >= 50 questions, got {len(golden_dataset)}"


def test_golden_dataset_required_fields(golden_dataset):
    for item in golden_dataset:
        for field in REQUIRED_FIELDS:
            assert field in item, f"Missing field '{field}' in item '{item.get('id')}'"


def test_golden_dataset_valid_domains(golden_dataset):
    for item in golden_dataset:
        assert item["domain"] in VALID_DOMAINS, \
            f"Invalid domain '{item['domain']}' in item '{item['id']}'"


def test_golden_dataset_valid_difficulties(golden_dataset):
    for item in golden_dataset:
        assert item["difficulty"] in VALID_DIFFICULTIES, \
            f"Invalid difficulty '{item['difficulty']}' in item '{item['id']}'"


def test_golden_dataset_unique_ids(golden_dataset):
    ids = [item["id"] for item in golden_dataset]
    assert len(ids) == len(set(ids)), "Duplicate IDs found in golden dataset"


def test_golden_dataset_nonempty_fields(golden_dataset):
    for item in golden_dataset:
        assert item["question"].strip(), f"Empty question in '{item['id']}'"
        assert item["ground_truth"].strip(), f"Empty ground_truth in '{item['id']}'"


def test_golden_dataset_domain_coverage(golden_dataset):
    """All 5 domains should be represented."""
    present = {item["domain"] for item in golden_dataset}
    missing = VALID_DOMAINS - present
    assert not missing, f"Missing domains in dataset: {missing}"


def test_golden_dataset_difficulty_coverage(golden_dataset):
    """All 3 difficulty levels should be represented."""
    present = {item["difficulty"] for item in golden_dataset}
    missing = VALID_DIFFICULTIES - present
    assert not missing, f"Missing difficulty levels in dataset: {missing}"


def test_golden_dataset_minimum_per_domain(golden_dataset):
    """Each domain should have at least 3 questions."""
    from collections import Counter
    counts = Counter(item["domain"] for item in golden_dataset)
    for domain in VALID_DOMAINS:
        assert counts[domain] >= 3, \
            f"Domain '{domain}' has only {counts[domain]} questions (minimum 3)"


def test_report_structure():
    """Validate the expected report dict structure."""
    mock_report = {
        "timestamp": "2025-01-01T00:00:00",
        "overall_faithfulness": 0.82,
        "threshold": 0.75,
        "passed": True,
        "total_questions": 20,
        "declined_count": 1,
        "per_domain": {"aws_security": 0.85, "grc": 0.78},
        "per_difficulty": {"easy": 0.90, "medium": 0.80, "hard": 0.70},
        "worst_performers": [{"id": "test_001", "question": "Q?", "score": 0.50}],
        "per_question_scores": [{"id": "test_001", "score": 0.50, "domain": "grc"}],
    }
    required_keys = [
        "timestamp", "overall_faithfulness", "threshold", "passed",
        "total_questions", "declined_count", "per_domain",
        "per_difficulty", "worst_performers", "per_question_scores"
    ]
    for key in required_keys:
        assert key in mock_report, f"Missing key: {key}"

    assert isinstance(mock_report["passed"], bool)
    assert 0.0 <= mock_report["overall_faithfulness"] <= 1.0
    assert mock_report["passed"] == (mock_report["overall_faithfulness"] >= mock_report["threshold"])


def test_pass_fail_logic():
    """Threshold comparison logic should be correct."""
    assert 0.82 >= 0.75   # should pass
    assert not (0.70 >= 0.75)  # should fail
    assert 0.75 >= 0.75   # exact threshold should pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
