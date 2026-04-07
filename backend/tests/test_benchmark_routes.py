"""
Tests for benchmark routes (/benchmark).
"""
import pytest
from unittest.mock import patch, MagicMock


class TestBenchmarkResults:
    """Test cases for listing and fetching benchmark results."""

    def test_list_results_empty(self, client):
        """Test listing results when none exist."""
        with patch("backend.api.benchmark_routes.benchmark_results_col") as mock_col:
            mock_col.find.return_value = []
            response = client.get("/benchmark/results")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["results"] == []

    def test_list_results_with_data(self, client):
        """Test listing results returns documents."""
        fake_results = [
            {"_id": "br1", "query_id": "q1", "experiment_arm": "baseline", "results": [], "timestamp": "t1"},
            {"_id": "br2", "query_id": "q1", "experiment_arm": "expanded", "results": [], "timestamp": "t2"},
        ]
        with patch("backend.api.benchmark_routes.benchmark_results_col") as mock_col, \
             patch("backend.api.benchmark_routes.relevance_judgments_col") as mock_jcol:
            mock_col.find.return_value = fake_results
            mock_jcol.find.return_value = []
            response = client.get("/benchmark/results?evaluator_id=eval1")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["pending"] == 2

    def test_list_results_tracks_judged(self, client):
        """Test that judged results are marked correctly."""
        fake_results = [
            {"_id": "br1", "query_id": "q1", "experiment_arm": "baseline", "results": [], "timestamp": "t1"},
            {"_id": "br2", "query_id": "q1", "experiment_arm": "expanded", "results": [], "timestamp": "t2"},
        ]
        with patch("backend.api.benchmark_routes.benchmark_results_col") as mock_col, \
             patch("backend.api.benchmark_routes.relevance_judgments_col") as mock_jcol:
            mock_col.find.return_value = fake_results
            mock_jcol.find.return_value = [{"benchmark_result_id": "br1"}]
            response = client.get("/benchmark/results?evaluator_id=eval1")

        assert response.status_code == 200
        data = response.json()
        assert data["judged"] == 1
        assert data["pending"] == 1
        assert data["results"][0]["judged"] is True
        assert data["results"][1]["judged"] is False

    def test_get_result_not_found(self, client):
        """Test fetching a non-existent result returns 404."""
        with patch("backend.api.benchmark_routes.benchmark_results_col") as mock_col:
            mock_col.find_one.return_value = None
            response = client.get("/benchmark/results/nonexistent")

        assert response.status_code == 404

    def test_get_result_found(self, client):
        """Test fetching an existing result returns it."""
        fake = {"_id": "br1", "query_id": "q1", "experiment_arm": "baseline", "results": [], "timestamp": "t"}
        with patch("backend.api.benchmark_routes.benchmark_results_col") as mock_col:
            mock_col.find_one.return_value = fake
            response = client.get("/benchmark/results/br1")

        assert response.status_code == 200
        data = response.json()
        assert data["_id"] == "br1"


class TestSubmitJudgments:
    """Test cases for submitting relevance judgments."""

    def test_submit_judgment_success(self, client):
        """Test successful judgment submission."""
        fake_result = {"_id": "br1", "query_id": "q1", "experiment_arm": "baseline", "results": []}
        with patch("backend.api.benchmark_routes.benchmark_results_col") as mock_col, \
             patch("backend.api.benchmark_routes.relevance_judgments_col") as mock_jcol, \
             patch("backend.api.benchmark_routes.make_relevance_judgment_doc") as mock_make:
            mock_col.find_one.return_value = fake_result
            mock_make.return_value = {
                "_id": "j1",
                "benchmark_result_id": "br1",
                "evaluator_id": "eval1",
                "judgments": [{"rank": 1, "relevant": True}],
                "timestamp": "t",
            }
            response = client.post("/benchmark/judgments", json={
                "benchmark_result_id": "br1",
                "evaluator_id": "eval1",
                "judgments": [{"rank": 1, "relevant": True}],
            })

        assert response.status_code == 200
        data = response.json()
        assert data["judgment_id"] == "j1"
        assert data["status"] == "saved"
        mock_jcol.delete_many.assert_called_once()
        mock_jcol.insert_one.assert_called_once()

    def test_submit_judgment_result_not_found(self, client):
        """Test submission fails when benchmark result doesn't exist."""
        with patch("backend.api.benchmark_routes.benchmark_results_col") as mock_col:
            mock_col.find_one.return_value = None
            response = client.post("/benchmark/judgments", json={
                "benchmark_result_id": "nonexistent",
                "evaluator_id": "eval1",
                "judgments": [{"rank": 1, "relevant": True}],
            })

        assert response.status_code == 404


class TestEvaluationProgress:
    """Test cases for evaluation progress endpoint."""

    def test_progress_returns_counts(self, client):
        """Test progress endpoint returns correct counts."""
        with patch("backend.api.benchmark_routes.benchmark_results_col") as mock_col, \
             patch("backend.api.benchmark_routes.relevance_judgments_col") as mock_jcol:
            mock_col.count_documents.return_value = 10
            mock_jcol.count_documents.return_value = 3
            response = client.get("/benchmark/progress?evaluator_id=eval1")

        assert response.status_code == 200
        data = response.json()
        assert data["evaluator_id"] == "eval1"
        assert data["total"] == 10
        assert data["judged"] == 3
        assert data["pending"] == 7

    def test_progress_requires_evaluator_id(self, client):
        """Test progress endpoint requires evaluator_id parameter."""
        response = client.get("/benchmark/progress")
        assert response.status_code == 422
