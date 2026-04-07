"""
Tests for the benchmark scoring script.
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.scripts.score_benchmark import compute_precision_at_k, score, fetch_data, print_report


class TestComputePrecisionAtK:
    """Tests for the P@5 calculation."""

    def test_all_relevant(self):
        judgments = [{"rank": i, "relevant": True} for i in range(1, 6)]
        assert compute_precision_at_k(judgments) == 1.0

    def test_none_relevant(self):
        judgments = [{"rank": i, "relevant": False} for i in range(1, 6)]
        assert compute_precision_at_k(judgments) == 0.0

    def test_partial_relevant(self):
        judgments = [
            {"rank": 1, "relevant": True},
            {"rank": 2, "relevant": False},
            {"rank": 3, "relevant": True},
            {"rank": 4, "relevant": False},
            {"rank": 5, "relevant": True},
        ]
        assert compute_precision_at_k(judgments) == 0.6

    def test_missing_ranks_treated_as_not_relevant(self):
        # Only ranks 1 and 3 judged as relevant, 2/4/5 missing
        judgments = [
            {"rank": 1, "relevant": True},
            {"rank": 3, "relevant": True},
        ]
        assert compute_precision_at_k(judgments) == 0.4

    def test_empty_judgments(self):
        assert compute_precision_at_k([]) == 0.0

    def test_custom_k(self):
        judgments = [
            {"rank": 1, "relevant": True},
            {"rank": 2, "relevant": True},
            {"rank": 3, "relevant": False},
        ]
        assert compute_precision_at_k(judgments, k=3) == pytest.approx(2 / 3)


class TestScore:
    """Tests for the scoring aggregation logic."""

    def _make_result(self, result_id, query_id, arm):
        return {
            "_id": result_id,
            "query_id": query_id,
            "experiment_arm": arm,
            "results": [],
        }

    def test_basic_scoring(self):
        results = [
            self._make_result("r1", "q1", "baseline"),
            self._make_result("r2", "q1", "expanded"),
        ]
        judgments = {
            "r1": [{"rank": i, "relevant": i <= 2} for i in range(1, 6)],  # 2/5
            "r2": [{"rank": i, "relevant": i <= 4} for i in range(1, 6)],  # 4/5
        }
        query_map = {"q1": "test query"}

        report = score(results, judgments, query_map)

        assert report["summary"]["baseline_avg_p5"] == 0.4
        assert report["summary"]["expanded_avg_p5"] == 0.8
        assert report["summary"]["baseline_n"] == 1
        assert report["summary"]["expanded_n"] == 1
        assert report["comparisons"]["wins"] == 1
        assert report["comparisons"]["losses"] == 0
        assert report["comparisons"]["ties"] == 0
        assert report["skipped"] == 0

    def test_skipped_results_without_judgments(self):
        results = [
            self._make_result("r1", "q1", "baseline"),
            self._make_result("r2", "q2", "baseline"),
        ]
        judgments = {
            "r1": [{"rank": 1, "relevant": True}],
        }
        query_map = {"q1": "query 1", "q2": "query 2"}

        report = score(results, judgments, query_map)

        assert report["skipped"] == 1
        assert len(report["per_query"]) == 1

    def test_tie_when_equal_scores(self):
        results = [
            self._make_result("r1", "q1", "baseline"),
            self._make_result("r2", "q1", "expanded"),
        ]
        same_judgments = [{"rank": i, "relevant": i <= 3} for i in range(1, 6)]
        judgments = {"r1": same_judgments, "r2": same_judgments}
        query_map = {"q1": "test query"}

        report = score(results, judgments, query_map)

        assert report["comparisons"]["ties"] == 1
        assert report["comparisons"]["wins"] == 0
        assert report["comparisons"]["losses"] == 0

    def test_loss_when_baseline_better(self):
        results = [
            self._make_result("r1", "q1", "baseline"),
            self._make_result("r2", "q1", "expanded"),
        ]
        judgments = {
            "r1": [{"rank": i, "relevant": True} for i in range(1, 6)],   # 5/5
            "r2": [{"rank": i, "relevant": False} for i in range(1, 6)],  # 0/5
        }
        query_map = {"q1": "test query"}

        report = score(results, judgments, query_map)

        assert report["comparisons"]["losses"] == 1
        assert report["summary"]["baseline_avg_p5"] == 1.0
        assert report["summary"]["expanded_avg_p5"] == 0.0

    def test_no_comparison_when_only_one_arm(self):
        results = [self._make_result("r1", "q1", "baseline")]
        judgments = {"r1": [{"rank": 1, "relevant": True}]}
        query_map = {"q1": "query"}

        report = score(results, judgments, query_map)

        assert report["comparisons"]["compared"] == 0
        assert report["summary"]["baseline_n"] == 1
        assert report["summary"]["expanded_n"] == 0

    def test_empty_results(self):
        report = score([], {}, {})

        assert report["per_query"] == []
        assert report["summary"]["baseline_avg_p5"] == 0.0
        assert report["summary"]["expanded_avg_p5"] == 0.0
        assert report["comparisons"]["compared"] == 0
        assert report["skipped"] == 0

    def test_multiple_queries(self):
        results = [
            self._make_result("r1", "q1", "baseline"),
            self._make_result("r2", "q1", "expanded"),
            self._make_result("r3", "q2", "baseline"),
            self._make_result("r4", "q2", "expanded"),
        ]
        judgments = {
            "r1": [{"rank": i, "relevant": i <= 2} for i in range(1, 6)],  # 0.4
            "r2": [{"rank": i, "relevant": i <= 4} for i in range(1, 6)],  # 0.8
            "r3": [{"rank": i, "relevant": i <= 3} for i in range(1, 6)],  # 0.6
            "r4": [{"rank": i, "relevant": i <= 3} for i in range(1, 6)],  # 0.6
        }
        query_map = {"q1": "query one", "q2": "query two"}

        report = score(results, judgments, query_map)

        assert report["summary"]["baseline_n"] == 2
        assert report["summary"]["expanded_n"] == 2
        assert report["summary"]["baseline_avg_p5"] == 0.5   # (0.4 + 0.6) / 2
        assert report["summary"]["expanded_avg_p5"] == 0.7   # (0.8 + 0.6) / 2
        assert report["comparisons"]["wins"] == 1     # query one
        assert report["comparisons"]["ties"] == 1     # query two
        assert report["comparisons"]["losses"] == 0

    def test_query_id_used_when_text_not_in_map(self):
        results = [self._make_result("r1", "q-unknown", "baseline")]
        judgments = {"r1": [{"rank": 1, "relevant": True}]}
        query_map = {}  # no mapping

        report = score(results, judgments, query_map)

        assert report["per_query"][0]["query_text"] == "q-unknown"


class TestFetchData:
    """Tests for database fetching."""

    @patch("backend.scripts.score_benchmark.relevance_judgments_col")
    @patch("backend.scripts.score_benchmark.benchmark_results_col")
    def test_fetch_all(self, mock_results_col, mock_judgments_col):
        mock_results_col.find.return_value = [{"_id": "r1"}]
        mock_judgments_col.find.return_value = [
            {"benchmark_result_id": "r1", "judgments": [{"rank": 1, "relevant": True}]}
        ]

        results, judgments = fetch_data()

        mock_results_col.find.assert_called_once_with({})
        mock_judgments_col.find.assert_called_once_with({})
        assert len(results) == 1
        assert "r1" in judgments

    @patch("backend.scripts.score_benchmark.relevance_judgments_col")
    @patch("backend.scripts.score_benchmark.benchmark_results_col")
    def test_fetch_with_evaluator_filter(self, mock_results_col, mock_judgments_col):
        mock_results_col.find.return_value = []
        mock_judgments_col.find.return_value = []

        fetch_data(evaluator_id="alice")

        mock_judgments_col.find.assert_called_once_with({"evaluator_id": "alice"})

    @patch("backend.scripts.score_benchmark.relevance_judgments_col")
    @patch("backend.scripts.score_benchmark.benchmark_results_col")
    def test_fetch_empty(self, mock_results_col, mock_judgments_col):
        mock_results_col.find.return_value = []
        mock_judgments_col.find.return_value = []

        results, judgments = fetch_data()

        assert results == []
        assert judgments == {}


class TestPrintReport:
    """Test that print_report runs without errors on various inputs."""

    def test_prints_full_report(self, capsys):
        report = {
            "per_query": [],
            "summary": {
                "baseline_avg_p5": 0.6,
                "expanded_avg_p5": 0.8,
                "baseline_n": 5,
                "expanded_n": 5,
            },
            "comparisons": {
                "wins": 3,
                "losses": 1,
                "ties": 1,
                "compared": 5,
                "details": [
                    {"query": "test q", "baseline_p5": 0.4, "expanded_p5": 0.8, "outcome": "win"},
                ],
            },
            "skipped": 2,
        }
        print_report(report)
        output = capsys.readouterr().out
        assert "Baseline" in output
        assert "Expanded" in output
        assert "Wins" in output

    def test_prints_no_comparisons(self, capsys):
        report = {
            "per_query": [],
            "summary": {
                "baseline_avg_p5": 0.0,
                "expanded_avg_p5": 0.0,
                "baseline_n": 0,
                "expanded_n": 0,
            },
            "comparisons": {
                "wins": 0, "losses": 0, "ties": 0, "compared": 0, "details": [],
            },
            "skipped": 0,
        }
        print_report(report)
        output = capsys.readouterr().out
        assert "No head-to-head comparisons" in output
