"""
Tests for search_service.search() – benchmark_mode behavior.

Verifies that benchmark_mode=True returns raw Google results
without personalization or reranking, while normal mode still
applies profile-based reranking.
"""
import pytest
from unittest.mock import patch, MagicMock


FAKE_GOOGLE_RESULTS = [
    {"title": f"Result {i}", "link": f"https://r{i}.com", "snippet": f"Snippet {i}"}
    for i in range(7)
]


class TestSearchBenchmarkMode:
    """Test that search() skips reranking when benchmark_mode=True."""

    @patch("backend.services.search_service.search_google")
    def test_benchmark_mode_returns_raw_results(self, mock_google):
        """benchmark_mode=True should return Google results unchanged."""
        mock_google.return_value = list(FAKE_GOOGLE_RESULTS)
        from backend.services.search_service import search

        results = search("test query", user_id="user1", benchmark_mode=True)

        assert results == FAKE_GOOGLE_RESULTS

    @patch("backend.services.search_service.search_google")
    @patch("backend.services.search_service.user_profiles_col")
    def test_benchmark_mode_skips_profile_lookup(self, mock_profiles, mock_google):
        """benchmark_mode=True should never query the user profile collection."""
        mock_google.return_value = list(FAKE_GOOGLE_RESULTS)
        from backend.services.search_service import search

        search("test query", user_id="user1", benchmark_mode=True)

        mock_profiles.find_one.assert_not_called()

    @patch("backend.services.search_service.search_google")
    @patch("backend.services.search_service._score_result")
    def test_benchmark_mode_skips_scoring(self, mock_score, mock_google):
        """benchmark_mode=True should never call _score_result."""
        mock_google.return_value = list(FAKE_GOOGLE_RESULTS)
        from backend.services.search_service import search

        search("test query", user_id="user1", benchmark_mode=True)

        mock_score.assert_not_called()

    @patch("backend.services.search_service.search_google")
    @patch("backend.services.search_service.user_profiles_col")
    def test_normal_mode_applies_reranking(self, mock_profiles, mock_google):
        """Normal mode with a profile should rerank top-N results."""
        mock_google.return_value = list(FAKE_GOOGLE_RESULTS)
        mock_profiles.find_one.return_value = {
            "user_id": "user1",
            "implicit_interests": {"r6": 10.0},  # heavily boost result 6
            "explicit_interests": [],
        }
        from backend.services.search_service import search

        results = search("test query", user_id="user1", benchmark_mode=False)

        # Profile lookup should have been called
        mock_profiles.find_one.assert_called_once_with({"user_id": "user1"})
        # Reranking may reorder, so results can differ from raw order
        assert len(results) == len(FAKE_GOOGLE_RESULTS)

    @patch("backend.services.search_service.search_google")
    def test_benchmark_mode_preserves_result_order(self, mock_google):
        """benchmark_mode should preserve the exact order from Google."""
        ordered = [{"title": f"T{i}", "link": f"https://{i}.com", "snippet": ""} for i in range(5)]
        mock_google.return_value = list(ordered)
        from backend.services.search_service import search

        results = search("query", user_id="user1", benchmark_mode=True)

        for i in range(5):
            assert results[i]["title"] == f"T{i}"
