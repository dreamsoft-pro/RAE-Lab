# RAE-Lab/tests/test_insight_engine.py
import pytest
import os
import shutil
from unittest.mock import MagicMock, patch
from core.experiment_manager import ExperimentManager

@pytest.fixture
def temp_storage(tmp_path):
    storage = tmp_path / "rae_lab_test"
    os.makedirs(storage, exist_ok=True)
    return str(storage)

@pytest.fixture
def mock_rae_api():
    with patch("httpx.AsyncClient.post") as mock_post:
        yield mock_post

@pytest.mark.asyncio
async def test_trend_calculation_down(temp_storage, mock_rae_api):
    """Test if trend is correctly identified as 'down' when quality decreases."""
    # Mocking historical high scores (0.9, 0.8)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {"metadata": {"score": 0.9}},
            {"metadata": {"score": 0.8}}
        ]
    }
    mock_rae_api.return_value = mock_resp
    
    manager = ExperimentManager(storage_path=temp_storage)
    current_scan = {"project_id": "test-proj", "quality_score": 0.5, "complexity": 10}
    
    insight = await manager.generate_kaizen_insight("test-proj", current_scan)
    
    assert insight["metrics"]["trend"] == "down"
    assert "OSTRZEŻENIE" in insight["suggestion"]

@pytest.mark.asyncio
async def test_trend_calculation_up(temp_storage, mock_rae_api):
    """Test if trend is correctly identified as 'up' when quality increases."""
    # Mocking historical low scores (0.3, 0.4)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {"metadata": {"score": 0.3}},
            {"metadata": {"score": 0.4}}
        ]
    }
    mock_rae_api.return_value = mock_resp
    
    manager = ExperimentManager(storage_path=temp_storage)
    current_scan = {"project_id": "test-proj", "quality_score": 0.9, "complexity": 10}
    
    insight = await manager.generate_kaizen_insight("test-proj", current_scan)
    
    assert insight["metrics"]["trend"] == "up"
    assert "STABILNIE" in insight["suggestion"]
