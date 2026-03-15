import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.ingest.sentinel import SentinelIngestor, CopernicusAuth
from src.common.schemas import BoundingBox, SensorType

@pytest.fixture
def ingestor(tmp_path):
    storage = tmp_path / "raw"
    storage.mkdir()
    return SentinelIngestor(raw_storage=storage)

def test_auth_token_retrieval():
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"access_token": "mock_token"}
        
        auth = CopernicusAuth("id", "secret")
        token = auth.get_token()
        assert token == "mock_token"

@pytest.mark.asyncio
async def test_ingest_item_rejection_low_quality(ingestor):
    # Mock STAC Item
    mock_item = MagicMock()
    mock_item.id = "S2_TEST_1"
    mock_item.properties = {
        "eo:cloud_cover": 95.0, # Too cloudy
        "datetime": "2023-01-01T12:00:00Z",
        "platform": "Sentinel-2A"
    }
    
    event = await ingestor.ingest_item(mock_item)
    assert event.status.value == "REJECTED"
    assert "Gate failure" in event.reason_if_not_accepted
