"""
Tests for models/data_models.py – make_query_doc, make_interaction_doc, make_user_profile_doc.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from backend.models.data_models import (
    make_query_doc,
    make_interaction_doc,
    make_user_profile_doc,
)


class TestMakeQueryDoc:
    """Test cases for make_query_doc."""

    def test_returns_required_keys(self):
        """A query document should contain all expected keys."""
        doc = make_query_doc(user_id="u1", raw_text="hello world")
        assert set(doc.keys()) == {"_id", "user_id", "raw_text", "enhanced_text", "timestamp"}

    def test_user_id_and_raw_text_stored(self):
        """Supplied user_id and raw_text should appear verbatim in the document."""
        doc = make_query_doc(user_id="user_42", raw_text="python tutorial")
        assert doc["user_id"] == "user_42"
        assert doc["raw_text"] == "python tutorial"

    def test_enhanced_text_defaults_to_none(self):
        """When enhanced_text is not provided it should be None."""
        doc = make_query_doc(user_id="u1", raw_text="q")
        assert doc["enhanced_text"] is None

    def test_enhanced_text_stored_when_provided(self):
        """When enhanced_text is provided it should be stored."""
        doc = make_query_doc(user_id="u1", raw_text="q", enhanced_text="expanded q")
        assert doc["enhanced_text"] == "expanded q"

    def test_id_is_valid_uuid4(self):
        """The _id field should be a valid UUID4 string."""
        doc = make_query_doc(user_id="u1", raw_text="q")
        parsed = uuid.UUID(doc["_id"], version=4)
        assert str(parsed) == doc["_id"]

    def test_id_is_unique_across_calls(self):
        """Each call should generate a unique _id."""
        ids = {make_query_doc("u1", "q")["_id"] for _ in range(50)}
        assert len(ids) == 50

    def test_timestamp_is_valid_utc_iso(self):
        """Timestamp should be a parseable ISO-8601 string close to now."""
        before = datetime.now(timezone.utc)
        doc = make_query_doc(user_id="u1", raw_text="q")
        after = datetime.now(timezone.utc)

        ts = datetime.fromisoformat(doc["timestamp"])
        assert before <= ts <= after

    def test_empty_raw_text_accepted(self):
        """An empty raw_text string should be stored without error."""
        doc = make_query_doc(user_id="u1", raw_text="")
        assert doc["raw_text"] == ""

    def test_benchmark_metadata_not_present_by_default(self):
        """When benchmark_metadata is not provided, key should be absent."""
        doc = make_query_doc(user_id="u1", raw_text="q")
        assert "benchmark_metadata" not in doc

    def test_benchmark_metadata_stored_when_provided(self):
        """When benchmark_metadata is provided, it should be stored in the document."""
        metadata = {
            "experiment_arm": "baseline",
            "use_enhanced": False,
            "semantic_mode": "clarify_only",
            "benchmark_mode": True,
        }
        doc = make_query_doc(user_id="u1", raw_text="q", benchmark_metadata=metadata)
        assert doc["benchmark_metadata"] == metadata
        assert doc["benchmark_metadata"]["experiment_arm"] == "baseline"

    def test_benchmark_metadata_expanded_arm(self):
        """Expanded experiment arm should be stored correctly."""
        metadata = {
            "experiment_arm": "expanded",
            "use_enhanced": True,
            "semantic_mode": "clarify_only",
            "benchmark_mode": True,
        }
        doc = make_query_doc(user_id="u1", raw_text="q", benchmark_metadata=metadata)
        assert doc["benchmark_metadata"]["experiment_arm"] == "expanded"
        assert doc["benchmark_metadata"]["use_enhanced"] is True


class TestMakeInteractionDoc:
    """Test cases for make_interaction_doc."""

    def test_returns_required_keys(self):
        """An interaction document should contain all expected keys."""
        doc = make_interaction_doc(
            user_id="u1", query_id="q1", clicked_url="https://example.com", rank=1
        )
        assert set(doc.keys()) == {
            "_id", "user_id", "query_id", "clicked_url", "rank", "timestamp", "action_type"
        }

    def test_fields_stored_correctly(self):
        """All supplied field values should be stored verbatim."""
        doc = make_interaction_doc(
            user_id="u2", query_id="q3", clicked_url="https://foo.bar", rank=5
        )
        assert doc["user_id"] == "u2"
        assert doc["query_id"] == "q3"
        assert doc["clicked_url"] == "https://foo.bar"
        assert doc["rank"] == 5

    def test_action_type_defaults_to_click(self):
        """Default action_type should be 'click'."""
        doc = make_interaction_doc("u1", "q1", "https://a.com", 1)
        assert doc["action_type"] == "click"

    def test_action_type_positive_feedback(self):
        """action_type should be stored when explicitly set to positive_feedback."""
        doc = make_interaction_doc("u1", "q1", "https://a.com", 1, action_type="positive_feedback")
        assert doc["action_type"] == "positive_feedback"

    def test_action_type_negative_feedback(self):
        """action_type should be stored when explicitly set to negative_feedback."""
        doc = make_interaction_doc("u1", "q1", "https://a.com", 1, action_type="negative_feedback")
        assert doc["action_type"] == "negative_feedback"

    def test_id_is_valid_uuid4(self):
        """The _id field should be a valid UUID4 string."""
        doc = make_interaction_doc("u1", "q1", "https://a.com", 1)
        parsed = uuid.UUID(doc["_id"], version=4)
        assert str(parsed) == doc["_id"]

    def test_id_is_unique_across_calls(self):
        """Each call should produce a unique _id."""
        ids = {make_interaction_doc("u1", "q1", "https://a.com", 1)["_id"] for _ in range(50)}
        assert len(ids) == 50

    def test_timestamp_is_valid_utc_iso(self):
        """Timestamp should be a parseable ISO-8601 string close to now."""
        before = datetime.now(timezone.utc)
        doc = make_interaction_doc("u1", "q1", "https://a.com", 1)
        after = datetime.now(timezone.utc)

        ts = datetime.fromisoformat(doc["timestamp"])
        assert before <= ts <= after

    def test_rank_zero(self):
        """A rank of 0 should be stored without error."""
        doc = make_interaction_doc("u1", "q1", "https://a.com", 0)
        assert doc["rank"] == 0


class TestMakeUserProfileDoc:
    """Test cases for make_user_profile_doc."""

    def test_returns_required_keys(self):
        """A user profile document should contain all expected keys."""
        doc = make_user_profile_doc(
            user_id="u1",
            interests={"python": 0.9},
            query_history=["q1"],
            click_history=["https://a.com"],
        )
        expected_keys = {
            "user_id", "implicit_interests", "query_history",
            "click_history", "last_updated", "explicit_interests", "embedding"
        }
        assert set(doc.keys()) == expected_keys

    def test_fields_stored_correctly(self):
        """Supplied fields should appear verbatim in the document."""
        interests = {"ml": 0.8, "web": 0.6}
        q_hist = ["q1", "q2"]
        c_hist = ["https://a.com"]
        doc = make_user_profile_doc("u5", interests, q_hist, c_hist)
        assert doc["user_id"] == "u5"
        assert doc["implicit_interests"] == interests
        assert doc["query_history"] == q_hist
        assert doc["click_history"] == c_hist

    def test_explicit_interests_defaults_to_empty_list(self):
        """When explicit_interests is omitted it should default to an empty list."""
        doc = make_user_profile_doc("u1", {}, [], [])
        assert doc["explicit_interests"] == []

    def test_explicit_interests_stored_when_provided(self):
        """When explicit_interests is provided it should be stored."""
        explicit = [{"keyword": "python", "weight": 1.0}]
        doc = make_user_profile_doc("u1", {}, [], [], explicit_interests=explicit)
        assert doc["explicit_interests"] == explicit

    def test_explicit_interests_none_coerced_to_empty_list(self):
        """Passing None for explicit_interests should yield an empty list."""
        doc = make_user_profile_doc("u1", {}, [], [], explicit_interests=None)
        assert doc["explicit_interests"] == []

    def test_embedding_is_none(self):
        """The embedding field should always be None at creation time."""
        doc = make_user_profile_doc("u1", {}, [], [])
        assert doc["embedding"] is None

    def test_timestamp_is_valid_utc_iso(self):
        """last_updated should be a parseable ISO-8601 string close to now."""
        before = datetime.now(timezone.utc)
        doc = make_user_profile_doc("u1", {}, [], [])
        after = datetime.now(timezone.utc)

        ts = datetime.fromisoformat(doc["last_updated"])
        assert before <= ts <= after

    def test_empty_interests_and_histories(self):
        """Empty dicts/lists for interests and histories should be stored cleanly."""
        doc = make_user_profile_doc("u1", {}, [], [])
        assert doc["implicit_interests"] == {}
        assert doc["query_history"] == []
        assert doc["click_history"] == []
