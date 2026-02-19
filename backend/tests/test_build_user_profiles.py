"""
Tests for scripts/build_user_profiles.py – run_profile_build.
"""
import pytest
from unittest.mock import patch, MagicMock, call
from io import StringIO


class TestRunProfileBuild:
    """Test cases for the run_profile_build script function."""

    @patch("scripts.build_user_profiles.queries_col")
    @patch("scripts.build_user_profiles.build_user_profile")
    def test_no_users_found(self, mock_build, mock_queries_col, capsys):
        """When there are no users, run_profile_build should print zero users and not build any profiles."""
        # Arrange
        mock_queries_col.distinct.return_value = []

        # Act
        from scripts.build_user_profiles import run_profile_build
        run_profile_build()

        # Assert
        mock_queries_col.distinct.assert_called_once_with("user_id")
        mock_build.assert_not_called()
        captured = capsys.readouterr()
        assert "Found 0 users" in captured.out
        assert "Done building all user profiles" in captured.out

    @patch("scripts.build_user_profiles.queries_col")
    @patch("scripts.build_user_profiles.build_user_profile")
    def test_single_user(self, mock_build, mock_queries_col, capsys):
        """With one user, build_user_profile should be called exactly once."""
        # Arrange
        mock_queries_col.distinct.return_value = ["user_1"]
        mock_build.return_value = {
            "implicit_interests": {"python": 0.9, "testing": 0.7}
        }

        # Act
        from scripts.build_user_profiles import run_profile_build
        run_profile_build()

        # Assert
        mock_build.assert_called_once_with("user_1")
        captured = capsys.readouterr()
        assert "Found 1 users" in captured.out
        assert "user_1" in captured.out
        assert "2 implicit interests" in captured.out

    @patch("scripts.build_user_profiles.queries_col")
    @patch("scripts.build_user_profiles.build_user_profile")
    def test_multiple_users(self, mock_build, mock_queries_col, capsys):
        """With multiple users, build_user_profile should be called once per user."""
        # Arrange
        user_ids = ["user_a", "user_b", "user_c"]
        mock_queries_col.distinct.return_value = user_ids
        mock_build.side_effect = [
            {"implicit_interests": {"ml": 0.8}},
            {"implicit_interests": {"web": 0.6, "css": 0.3}},
            {"implicit_interests": {}},
        ]

        # Act
        from scripts.build_user_profiles import run_profile_build
        run_profile_build()

        # Assert
        assert mock_build.call_count == 3
        mock_build.assert_any_call("user_a")
        mock_build.assert_any_call("user_b")
        mock_build.assert_any_call("user_c")
        captured = capsys.readouterr()
        assert "Found 3 users" in captured.out
        assert "1 implicit interests" in captured.out   # user_a
        assert "2 implicit interests" in captured.out   # user_b
        assert "0 implicit interests" in captured.out   # user_c

    @patch("scripts.build_user_profiles.queries_col")
    @patch("scripts.build_user_profiles.build_user_profile")
    def test_calls_in_order(self, mock_build, mock_queries_col):
        """build_user_profile should be called in the same order users are returned."""
        # Arrange
        user_ids = ["alpha", "bravo", "charlie"]
        mock_queries_col.distinct.return_value = user_ids
        mock_build.return_value = {"implicit_interests": {}}

        # Act
        from scripts.build_user_profiles import run_profile_build
        run_profile_build()

        # Assert
        expected_calls = [call("alpha"), call("bravo"), call("charlie")]
        assert mock_build.call_args_list == expected_calls

    @patch("scripts.build_user_profiles.queries_col")
    @patch("scripts.build_user_profiles.build_user_profile")
    def test_build_failure_propagates(self, mock_build, mock_queries_col):
        """If build_user_profile raises an exception it should propagate up."""
        # Arrange
        mock_queries_col.distinct.return_value = ["failing_user"]
        mock_build.side_effect = RuntimeError("DB connection lost")

        # Act / Assert
        from scripts.build_user_profiles import run_profile_build
        with pytest.raises(RuntimeError, match="DB connection lost"):
            run_profile_build()

    @patch("scripts.build_user_profiles.queries_col")
    @patch("scripts.build_user_profiles.build_user_profile")
    def test_output_shows_partial_interests(self, mock_build, mock_queries_col, capsys):
        """Output should include a slice of the implicit interests items."""
        # Arrange
        mock_queries_col.distinct.return_value = ["u1"]
        interests = {f"topic_{i}": float(i) for i in range(10)}
        mock_build.return_value = {"implicit_interests": interests}

        # Act
        from scripts.build_user_profiles import run_profile_build
        run_profile_build()

        # Assert – the script prints the first 8 items followed by "..."
        captured = capsys.readouterr()
        assert "..." in captured.out
        assert "10 implicit interests" in captured.out

    @patch("scripts.build_user_profiles.queries_col")
    @patch("scripts.build_user_profiles.build_user_profile")
    def test_distinct_called_with_correct_field(self, mock_build, mock_queries_col):
        """queries_col.distinct should be called with 'user_id'."""
        # Arrange
        mock_queries_col.distinct.return_value = []

        # Act
        from scripts.build_user_profiles import run_profile_build
        run_profile_build()

        # Assert
        mock_queries_col.distinct.assert_called_once_with("user_id")
