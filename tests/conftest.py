import pytest
from craft_cli.client import CraftClient


@pytest.fixture
def mock_client(mocker):
    """Client with mocked session."""
    mocker.patch("craft_cli.client.get_api_base", return_value="https://example.com/api/v1")
    mocker.patch("craft_cli.client.get_api_key", return_value="test-key")
    return CraftClient()


@pytest.fixture
def live_client():
    """Real client for integration tests."""
    return CraftClient()
