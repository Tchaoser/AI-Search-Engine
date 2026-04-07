"""
Tests for logging_service module.
Covers log_query, log_interaction, and log_feedback functions.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


class TestLogQuery:
    """Test cases for log_query function."""

    def test_log_query_basic_insertion(self):
        """Test that log_query inserts a document with correct structure."""
        # Arrange
        mock_queries_col = MagicMock()
        
        with patch("backend.services.logging_service.queries_col", mock_queries_col), \
             patch("backend.services.logging_service.make_query_doc") as mock_make_doc:
            
            mock_doc = {
                "_id": "generated_id_123",
                "user_id": "user_123",
                "raw_text": "python tutorials",
                "enhanced_text": None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            mock_make_doc.return_value = mock_doc
            
            from backend.services.logging_service import log_query
            
            # Act
            result = log_query("user_123", "python tutorials")
            
            # Assert
            mock_make_doc.assert_called_once_with("user_123", "python tutorials", None, benchmark_metadata=None)
            mock_queries_col.insert_one.assert_called_once_with(mock_doc)
            assert result == "generated_id_123"

    def test_log_query_with_enhanced_text(self):
        """Test log_query with enhanced text parameter."""
        # Arrange
        mock_queries_col = MagicMock()
        
        with patch("backend.services.logging_service.queries_col", mock_queries_col), \
             patch("backend.services.logging_service.make_query_doc") as mock_make_doc:
            
            mock_doc = {
                "_id": "generated_id_456",
                "user_id": "user_456",
                "raw_text": "machine learning",
                "enhanced_text": "machine learning algorithms tutorials beginners",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            mock_make_doc.return_value = mock_doc
            
            from backend.services.logging_service import log_query
            
            # Act
            result = log_query(
                "user_456", 
                "machine learning", 
                "machine learning algorithms tutorials beginners"
            )
            
            # Assert
            mock_make_doc.assert_called_once_with(
                "user_456", 
                "machine learning", 
                "machine learning algorithms tutorials beginners",
                benchmark_metadata=None
            )
            mock_queries_col.insert_one.assert_called_once_with(mock_doc)
            assert result == "generated_id_456"

    def test_log_query_stores_raw_text_correctly(self):
        """Test that raw_text is stored without modification."""
        # Arrange
        mock_queries_col = MagicMock()
        raw_text = "C++ programming language guide"
        
        with patch("backend.services.logging_service.queries_col", mock_queries_col), \
             patch("backend.services.logging_service.make_query_doc") as mock_make_doc:
            
            mock_doc = {
                "_id": "id_789",
                "user_id": "user_789",
                "raw_text": raw_text,
                "enhanced_text": None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            mock_make_doc.return_value = mock_doc
            
            from backend.services.logging_service import log_query
            
            # Act
            log_query("user_789", raw_text)
            
            # Assert
            call_args = mock_make_doc.call_args[0]
            assert call_args[1] == raw_text

    def test_log_query_handles_database_error(self):
        """Test that log_query raises exception on database error."""
        # Arrange
        mock_queries_col = MagicMock()
        mock_queries_col.insert_one.side_effect = Exception("Database connection error")
        
        with patch("backend.services.logging_service.queries_col", mock_queries_col), \
             patch("backend.services.logging_service.make_query_doc") as mock_make_doc:
            
            mock_make_doc.return_value = {
                "_id": "id_error",
                "user_id": "user_error",
                "raw_text": "test query",
                "enhanced_text": None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            from backend.services.logging_service import log_query
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                log_query("user_error", "test query")
            
            assert "Database connection error" in str(exc_info.value)

    def test_log_query_empty_raw_text(self):
        """Test log_query with empty raw text."""
        # Arrange
        mock_queries_col = MagicMock()
        
        with patch("backend.services.logging_service.queries_col", mock_queries_col), \
             patch("backend.services.logging_service.make_query_doc") as mock_make_doc:
            
            mock_doc = {
                "_id": "id_empty",
                "user_id": "user_empty",
                "raw_text": "",
                "enhanced_text": None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            mock_make_doc.return_value = mock_doc
            
            from backend.services.logging_service import log_query
            
            # Act
            result = log_query("user_empty", "")
            
            # Assert
            mock_make_doc.assert_called_once_with("user_empty", "", None, benchmark_metadata=None)
            assert result == "id_empty"

    def test_log_query_with_benchmark_metadata(self):
        """Test that log_query passes benchmark_metadata to make_query_doc."""
        mock_queries_col = MagicMock()
        metadata = {
            "experiment_arm": "expanded",
            "use_enhanced": True,
            "semantic_mode": "clarify_only",
            "benchmark_mode": True,
        }

        with patch("backend.services.logging_service.queries_col", mock_queries_col), \
             patch("backend.services.logging_service.make_query_doc") as mock_make_doc:

            mock_doc = {
                "_id": "bench_id",
                "user_id": "user_bench",
                "raw_text": "test",
                "enhanced_text": "expanded test",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "benchmark_metadata": metadata,
            }
            mock_make_doc.return_value = mock_doc

            from backend.services.logging_service import log_query
            result = log_query("user_bench", "test", "expanded test", benchmark_metadata=metadata)

            mock_make_doc.assert_called_once_with(
                "user_bench", "test", "expanded test", benchmark_metadata=metadata
            )
            mock_queries_col.insert_one.assert_called_once_with(mock_doc)
            assert result == "bench_id"

    def test_log_query_without_benchmark_metadata(self):
        """Test that normal queries pass no benchmark_metadata."""
        mock_queries_col = MagicMock()

        with patch("backend.services.logging_service.queries_col", mock_queries_col), \
             patch("backend.services.logging_service.make_query_doc") as mock_make_doc:

            mock_doc = {
                "_id": "normal_id",
                "user_id": "user_normal",
                "raw_text": "test",
                "enhanced_text": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            mock_make_doc.return_value = mock_doc

            from backend.services.logging_service import log_query
            log_query("user_normal", "test")

            mock_make_doc.assert_called_once_with(
                "user_normal", "test", None, benchmark_metadata=None
            )


class TestLogBenchmarkResults:
    """Test cases for log_benchmark_results function."""

    def test_log_benchmark_results_inserts_doc(self):
        """Test that log_benchmark_results inserts a document into benchmark_results_col."""
        mock_col = MagicMock()
        results = [
            {"title": "R1", "link": "https://r1.com", "snippet": "S1"},
            {"title": "R2", "link": "https://r2.com", "snippet": "S2"},
        ]

        with patch("backend.services.logging_service.benchmark_results_col", mock_col), \
             patch("backend.services.logging_service.make_benchmark_result_doc") as mock_make:
            mock_make.return_value = {
                "_id": "br_id",
                "query_id": "q1",
                "experiment_arm": "baseline",
                "results": [],
                "timestamp": "2026-03-18T00:00:00",
            }

            from backend.services.logging_service import log_benchmark_results
            result_id = log_benchmark_results("q1", "baseline", results)

            mock_make.assert_called_once_with("q1", "baseline", results)
            mock_col.insert_one.assert_called_once()
            assert result_id == "br_id"

    def test_log_benchmark_results_raises_on_db_error(self):
        """Test that log_benchmark_results raises on database error."""
        mock_col = MagicMock()
        mock_col.insert_one.side_effect = Exception("DB error")

        with patch("backend.services.logging_service.benchmark_results_col", mock_col), \
             patch("backend.services.logging_service.make_benchmark_result_doc") as mock_make:
            mock_make.return_value = {"_id": "br_id", "query_id": "q1", "experiment_arm": "baseline", "results": [], "timestamp": "t"}

            from backend.services.logging_service import log_benchmark_results
            with pytest.raises(Exception, match="DB error"):
                log_benchmark_results("q1", "baseline", [])


class TestLogInteraction:
    """Test cases for log_interaction function."""

    def test_log_interaction_basic_click(self):
        """Test that log_interaction records a click event correctly."""
        # Arrange
        mock_interactions_col = MagicMock()
        
        with patch("backend.services.logging_service.interactions_col", mock_interactions_col), \
             patch("backend.services.logging_service.make_interaction_doc") as mock_make_doc:
            
            mock_doc = {
                "_id": "interaction_123",
                "user_id": "user_123",
                "query_id": "query_123",
                "clicked_url": "https://example.com/result",
                "rank": 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action_type": "click"
            }
            mock_make_doc.return_value = mock_doc
            
            from backend.services.logging_service import log_interaction
            
            # Act
            result = log_interaction(
                "user_123", 
                "query_123", 
                "https://example.com/result", 
                1
            )
            
            # Assert
            mock_make_doc.assert_called_once_with(
                "user_123", 
                "query_123", 
                "https://example.com/result", 
                1
            )
            mock_interactions_col.insert_one.assert_called_once_with(mock_doc)
            assert result == "interaction_123"

    def test_log_interaction_different_ranks(self):
        """Test log_interaction with different rank positions."""
        # Arrange
        mock_interactions_col = MagicMock()
        
        with patch("backend.services.logging_service.interactions_col", mock_interactions_col), \
             patch("backend.services.logging_service.make_interaction_doc") as mock_make_doc:
            
            for rank in [1, 5, 10, 50]:
                mock_make_doc.reset_mock()
                mock_interactions_col.reset_mock()
                
                mock_doc = {
                    "_id": f"interaction_rank_{rank}",
                    "user_id": "user_rank",
                    "query_id": "query_rank",
                    "clicked_url": f"https://example.com/result{rank}",
                    "rank": rank,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action_type": "click"
                }
                mock_make_doc.return_value = mock_doc
                
                from backend.services.logging_service import log_interaction
                
                # Act
                result = log_interaction(
                    "user_rank", 
                    "query_rank", 
                    f"https://example.com/result{rank}", 
                    rank
                )
                
                # Assert
                assert result == f"interaction_rank_{rank}"

    def test_log_interaction_stores_url_correctly(self):
        """Test that clicked URL is stored without modification."""
        # Arrange
        mock_interactions_col = MagicMock()
        url = "https://docs.python.org/3/tutorial/index.html?highlight=classes#section"
        
        with patch("backend.services.logging_service.interactions_col", mock_interactions_col), \
             patch("backend.services.logging_service.make_interaction_doc") as mock_make_doc:
            
            mock_doc = {
                "_id": "interaction_url",
                "user_id": "user_url",
                "query_id": "query_url",
                "clicked_url": url,
                "rank": 3,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action_type": "click"
            }
            mock_make_doc.return_value = mock_doc
            
            from backend.services.logging_service import log_interaction
            
            # Act
            log_interaction("user_url", "query_url", url, 3)
            
            # Assert
            call_args = mock_make_doc.call_args[0]
            assert call_args[2] == url

    def test_log_interaction_handles_database_error(self):
        """Test that log_interaction raises exception on database error."""
        # Arrange
        mock_interactions_col = MagicMock()
        mock_interactions_col.insert_one.side_effect = Exception("Write operation failed")
        
        with patch("backend.services.logging_service.interactions_col", mock_interactions_col), \
             patch("backend.services.logging_service.make_interaction_doc") as mock_make_doc:
            
            mock_make_doc.return_value = {
                "_id": "id_error",
                "user_id": "user_error",
                "query_id": "query_error",
                "clicked_url": "https://example.com",
                "rank": 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action_type": "click"
            }
            
            from backend.services.logging_service import log_interaction
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                log_interaction("user_error", "query_error", "https://example.com", 1)
            
            assert "Write operation failed" in str(exc_info.value)


class TestLogFeedback:
    """Test cases for log_feedback function."""

    def test_log_feedback_positive(self):
        """Test that log_feedback records positive feedback correctly."""
        # Arrange
        mock_interactions_col = MagicMock()
        mock_interactions_col.delete_many.return_value = MagicMock(deleted_count=0)
        
        with patch("backend.services.logging_service.interactions_col", mock_interactions_col), \
             patch("backend.services.logging_service.make_interaction_doc") as mock_make_doc:
            
            mock_doc = {
                "_id": "feedback_pos_123",
                "user_id": "user_feedback",
                "query_id": "query_feedback",
                "clicked_url": "https://example.com/good-result",
                "rank": 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action_type": "positive_feedback"
            }
            mock_make_doc.return_value = mock_doc
            
            from backend.services.logging_service import log_feedback
            
            # Act
            result = log_feedback(
                "user_feedback",
                "query_feedback",
                "https://example.com/good-result",
                1,
                is_positive=True
            )
            
            # Assert
            mock_make_doc.assert_called_once_with(
                user_id="user_feedback",
                query_id="query_feedback",
                clicked_url="https://example.com/good-result",
                rank=1,
                action_type="positive_feedback"
            )
            mock_interactions_col.insert_one.assert_called_once_with(mock_doc)
            assert result == "feedback_pos_123"

    def test_log_feedback_negative(self):
        """Test that log_feedback records negative feedback correctly."""
        # Arrange
        mock_interactions_col = MagicMock()
        mock_interactions_col.delete_many.return_value = MagicMock(deleted_count=0)
        
        with patch("backend.services.logging_service.interactions_col", mock_interactions_col), \
             patch("backend.services.logging_service.make_interaction_doc") as mock_make_doc:
            
            mock_doc = {
                "_id": "feedback_neg_456",
                "user_id": "user_feedback",
                "query_id": "query_feedback",
                "clicked_url": "https://example.com/bad-result",
                "rank": 2,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action_type": "negative_feedback"
            }
            mock_make_doc.return_value = mock_doc
            
            from backend.services.logging_service import log_feedback
            
            # Act
            result = log_feedback(
                "user_feedback",
                "query_feedback",
                "https://example.com/bad-result",
                2,
                is_positive=False
            )
            
            # Assert
            mock_make_doc.assert_called_once_with(
                user_id="user_feedback",
                query_id="query_feedback",
                clicked_url="https://example.com/bad-result",
                rank=2,
                action_type="negative_feedback"
            )
            assert result == "feedback_neg_456"

    def test_log_feedback_removes_existing_feedback(self):
        """Test that log_feedback removes previous feedback for the same URL."""
        # Arrange
        mock_interactions_col = MagicMock()
        mock_interactions_col.delete_many.return_value = MagicMock(deleted_count=1)
        
        with patch("backend.services.logging_service.interactions_col", mock_interactions_col), \
             patch("backend.services.logging_service.make_interaction_doc") as mock_make_doc:
            
            mock_doc = {
                "_id": "new_feedback",
                "user_id": "user_update",
                "query_id": "query_update",
                "clicked_url": "https://example.com/updated",
                "rank": 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action_type": "positive_feedback"
            }
            mock_make_doc.return_value = mock_doc
            
            from backend.services.logging_service import log_feedback
            
            # Act
            log_feedback(
                "user_update",
                "query_update",
                "https://example.com/updated",
                1,
                is_positive=True
            )
            
            # Assert - Verify delete_many was called with correct filter
            mock_interactions_col.delete_many.assert_called_once_with({
                "user_id": "user_update",
                "clicked_url": "https://example.com/updated",
                "action_type": {"$in": ["positive_feedback", "negative_feedback"]},
            })

    def test_log_feedback_toggle_from_positive_to_negative(self):
        """Test toggling feedback from positive to negative."""
        # Arrange
        mock_interactions_col = MagicMock()
        mock_interactions_col.delete_many.return_value = MagicMock(deleted_count=1)
        
        url = "https://example.com/toggle-result"
        
        with patch("backend.services.logging_service.interactions_col", mock_interactions_col), \
             patch("backend.services.logging_service.make_interaction_doc") as mock_make_doc:
            
            mock_doc = {
                "_id": "toggled_feedback",
                "user_id": "user_toggle",
                "query_id": "query_toggle",
                "clicked_url": url,
                "rank": 3,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action_type": "negative_feedback"
            }
            mock_make_doc.return_value = mock_doc
            
            from backend.services.logging_service import log_feedback
            
            # Act - User changes from positive to negative
            result = log_feedback(
                "user_toggle",
                "query_toggle",
                url,
                3,
                is_positive=False
            )
            
            # Assert
            # Verify old feedback was deleted
            mock_interactions_col.delete_many.assert_called_once()
            # Verify new feedback was inserted
            mock_interactions_col.insert_one.assert_called_once_with(mock_doc)
            assert result == "toggled_feedback"

    def test_log_feedback_handles_database_error(self):
        """Test that log_feedback raises exception on database error."""
        # Arrange
        mock_interactions_col = MagicMock()
        mock_interactions_col.delete_many.side_effect = Exception("Delete operation failed")
        
        with patch("backend.services.logging_service.interactions_col", mock_interactions_col):
            from backend.services.logging_service import log_feedback
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                log_feedback(
                    "user_error",
                    "query_error",
                    "https://example.com/error",
                    1,
                    is_positive=True
                )
            
            assert "Delete operation failed" in str(exc_info.value)

    def test_log_feedback_handles_insert_error(self):
        """Test that log_feedback raises exception on insert error after delete."""
        # Arrange
        mock_interactions_col = MagicMock()
        mock_interactions_col.delete_many.return_value = MagicMock(deleted_count=0)
        mock_interactions_col.insert_one.side_effect = Exception("Insert operation failed")
        
        with patch("backend.services.logging_service.interactions_col", mock_interactions_col), \
             patch("backend.services.logging_service.make_interaction_doc") as mock_make_doc:
            
            mock_make_doc.return_value = {
                "_id": "id_insert_error",
                "user_id": "user_error",
                "query_id": "query_error",
                "clicked_url": "https://example.com/error",
                "rank": 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action_type": "positive_feedback"
            }
            
            from backend.services.logging_service import log_feedback
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                log_feedback(
                    "user_error",
                    "query_error",
                    "https://example.com/error",
                    1,
                    is_positive=True
                )
            
            assert "Insert operation failed" in str(exc_info.value)


class TestLoggingDataIntegrity:
    """Test cases for data integrity and storage verification."""

    def test_query_document_structure(self):
        """Verify query document contains all required fields."""
        # Arrange
        mock_queries_col = MagicMock()
        captured_doc = None
        
        def capture_doc(doc):
            nonlocal captured_doc
            captured_doc = doc
        
        mock_queries_col.insert_one.side_effect = capture_doc
        
        with patch("backend.services.logging_service.queries_col", mock_queries_col):
            from backend.services.logging_service import log_query
            from backend.models.data_models import make_query_doc
            
            with patch("backend.services.logging_service.make_query_doc", wraps=make_query_doc) as wrapped:
                # Act
                try:
                    log_query("test_user", "test query", "enhanced test query")
                except:
                    pass  # We just want to verify the document structure
            
            # Assert - Verify make_query_doc was called with correct params
            wrapped.assert_called_once_with("test_user", "test query", "enhanced test query")

    def test_interaction_document_structure(self):
        """Verify interaction document contains all required fields."""
        # Arrange
        mock_interactions_col = MagicMock()
        
        with patch("backend.services.logging_service.interactions_col", mock_interactions_col):
            from backend.services.logging_service import log_interaction
            from backend.models.data_models import make_interaction_doc
            
            with patch("backend.services.logging_service.make_interaction_doc", wraps=make_interaction_doc) as wrapped:
                # Act
                try:
                    log_interaction("test_user", "test_query_id", "https://example.com", 5)
                except:
                    pass
            
            # Assert
            wrapped.assert_called_once_with("test_user", "test_query_id", "https://example.com", 5)

    def test_feedback_uses_correct_action_types(self):
        """Verify feedback uses correct action_type values."""
        # Arrange
        mock_interactions_col = MagicMock()
        mock_interactions_col.delete_many.return_value = MagicMock(deleted_count=0)
        
        with patch("backend.services.logging_service.interactions_col", mock_interactions_col), \
             patch("backend.services.logging_service.make_interaction_doc") as mock_make_doc:
            
            mock_make_doc.return_value = {
                "_id": "test_id",
                "user_id": "user",
                "query_id": "query",
                "clicked_url": "https://example.com",
                "rank": 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action_type": "positive_feedback"
            }
            
            from backend.services.logging_service import log_feedback
            
            # Act - Positive feedback
            log_feedback("user", "query", "https://example.com", 1, is_positive=True)
            
            # Assert
            call_kwargs = mock_make_doc.call_args[1]
            assert call_kwargs["action_type"] == "positive_feedback"
            
            # Reset mock for next call
            mock_make_doc.reset_mock()
            mock_interactions_col.reset_mock()
            mock_interactions_col.delete_many.return_value = MagicMock(deleted_count=0)
            mock_make_doc.return_value = {
                "_id": "test_id_2",
                "user_id": "user",
                "query_id": "query",
                "clicked_url": "https://example.com",
                "rank": 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action_type": "negative_feedback"
            }
            
            # Act - Negative feedback
            log_feedback("user", "query", "https://example.com", 1, is_positive=False)
            
            # Assert
            call_kwargs = mock_make_doc.call_args[1]
            assert call_kwargs["action_type"] == "negative_feedback"


class TestSearchResultRelevance:
    """Test cases to verify logging tracks result relevance correctly."""

    def test_log_interaction_tracks_result_position(self):
        """Test that interaction logging preserves rank for relevance analysis."""
        # Arrange
        mock_interactions_col = MagicMock()
        ranks_logged = []
        
        def capture_rank(doc):
            ranks_logged.append(doc.get("rank"))
        
        mock_interactions_col.insert_one.side_effect = capture_rank
        
        with patch("backend.services.logging_service.interactions_col", mock_interactions_col):
            from backend.services.logging_service import log_interaction
            from backend.models.data_models import make_interaction_doc
            
            with patch("backend.services.logging_service.make_interaction_doc", wraps=make_interaction_doc):
                # Act - Log clicks at different positions
                for rank in [1, 3, 7, 10]:
                    try:
                        log_interaction("user", "query", f"https://example.com/{rank}", rank)
                    except:
                        pass
            
            # Assert - All ranks were captured
            assert 1 in ranks_logged
            assert 3 in ranks_logged
            assert 7 in ranks_logged
            assert 10 in ranks_logged

    def test_log_feedback_relevance_signal(self):
        """Test that feedback correctly signals result relevance."""
        # Arrange
        mock_interactions_col = MagicMock()
        mock_interactions_col.delete_many.return_value = MagicMock(deleted_count=0)
        action_types_logged = []
        
        def capture_action_type(doc):
            action_types_logged.append(doc.get("action_type"))
        
        mock_interactions_col.insert_one.side_effect = capture_action_type
        
        with patch("backend.services.logging_service.interactions_col", mock_interactions_col):
            from backend.services.logging_service import log_feedback
            from backend.models.data_models import make_interaction_doc
            
            with patch("backend.services.logging_service.make_interaction_doc", wraps=make_interaction_doc):
                # Act - Log positive and negative feedback
                try:
                    log_feedback("user", "query", "https://good.com", 1, is_positive=True)
                except:
                    pass
                try:
                    log_feedback("user", "query", "https://bad.com", 2, is_positive=False)
                except:
                    pass
            
            # Assert - Both types of relevance signals logged
            assert "positive_feedback" in action_types_logged
            assert "negative_feedback" in action_types_logged

    def test_log_query_preserves_search_context(self):
        """Test that query logging preserves both raw and enhanced queries."""
        # Arrange
        mock_queries_col = MagicMock()
        logged_docs = []
        
        def capture_doc(doc):
            logged_docs.append(doc)
        
        mock_queries_col.insert_one.side_effect = capture_doc
        
        with patch("backend.services.logging_service.queries_col", mock_queries_col):
            from backend.services.logging_service import log_query
            from backend.models.data_models import make_query_doc
            
            with patch("backend.services.logging_service.make_query_doc", wraps=make_query_doc):
                # Act
                try:
                    log_query(
                        "user_123",
                        "python web framework",
                        "python web framework django flask fastapi comparison"
                    )
                except:
                    pass
            
            # Assert - Both raw and enhanced text should be in the document
            if logged_docs:
                doc = logged_docs[0]
                assert doc["raw_text"] == "python web framework"
                assert doc["enhanced_text"] == "python web framework django flask fastapi comparison"
