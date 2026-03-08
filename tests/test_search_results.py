import pytest
from unittest.mock import MagicMock, patch
from backend.handlers import CommandHandler


@pytest.fixture
def mock_tmdb():
    return MagicMock()


@pytest.fixture
def mock_storage():
    return MagicMock()


@patch('backend.handlers.Storage')
@patch('backend.handlers.TMDbClient')
def test_exact_match_still_auto_adds(mock_tmdb_class, mock_storage_class):
    """Test that exact match still auto-adds without showing options"""
    # Setup mocks
    mock_tmdb = MagicMock()
    mock_tmdb_class.return_value = mock_tmdb
    mock_storage = MagicMock()
    mock_storage_class.return_value = mock_storage

    # Exact match should still auto-add
    mock_tmdb.search_movie.return_value = {
        "title": "Dune",
        "id": 438632,
        "release_date": "2021-10-01"
    }

    handler = CommandHandler("test_key", "data/test.json")
    result = handler.handle_add(["Dune"])

    assert "✅" in result
    mock_storage.add_movie.assert_called_once()
