import unittest
from unittest.mock import patch, MagicMock
from backend.http_client import RequestManager


class TestRequestManager(unittest.TestCase):
    def test_request_manager_initialization(self):
        """Test que RequestManager se inicializa correctamente"""
        manager = RequestManager(timeout=10)
        assert manager.timeout == 10

    def test_default_timeout(self):
        """Test timeout por default es 5 segundos"""
        manager = RequestManager()
        assert manager.timeout == 5

    @patch('backend.http_client.requests.Session.get')
    def test_get_with_timeout(self, mock_get):
        """Test que get() aplica timeout"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        manager = RequestManager(timeout=8)
        result = manager.get("http://test.com", params={"q": "test"})

        # Verificar que se pasó timeout
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs.get("timeout") == 8
