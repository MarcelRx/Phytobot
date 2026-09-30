"""
Tests for vision module.
Note: These tests are skipped if heavy dependencies (cv2, requests) are not available.
"""

import pytest

# Try to import, but skip tests if dependencies are missing
try:
    from unittest.mock import MagicMock, patch

    import cv2
    import numpy as np

    from src.config import APIConfig, VisionConfig
    from src.vision_module import check_blur, identify_plant

    VISION_MODULE_AVAILABLE = True
except ImportError:
    VISION_MODULE_AVAILABLE = False
    pytest.skip("Heavy dependencies not available", allow_module_level=True)


@pytest.mark.skipif(
    not VISION_MODULE_AVAILABLE, reason="Heavy dependencies not available"
)
class TestBlurDetection:
    """Test blur detection functionality."""

    def test_check_blur_with_sharp_image(self, tmp_path):
        """Test blur detection with a sharp image."""
        # Create a sharp test image
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "sharp.jpg")
        cv2.imwrite(img_path, img)

        is_sharp, score = check_blur(img_path)
        assert isinstance(is_sharp, (bool, np.bool_))
        assert isinstance(score, (float, np.floating))
        assert score >= 0

    def test_check_blur_with_nonexistent_file(self, tmp_path):
        """Test blur detection with nonexistent file."""
        is_sharp, score = check_blur(str(tmp_path / "nonexistent.jpg"))
        assert not is_sharp
        assert score == 0

    def test_check_blur_with_custom_threshold(self, tmp_path):
        """Test blur detection with custom threshold."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        is_sharp_default, _ = check_blur(img_path)
        is_sharp_custom, _ = check_blur(img_path, threshold=1000)

        # Results should be consistent
        assert isinstance(is_sharp_default, (bool, np.bool_))
        assert isinstance(is_sharp_custom, (bool, np.bool_))


@pytest.mark.skipif(
    not VISION_MODULE_AVAILABLE, reason="Heavy dependencies not available"
)
class TestPlantIdentification:
    """Test plant identification functionality."""

    @patch("src.vision_module.APIConfig")
    def test_identify_plant_no_api_key(self, mock_config, tmp_path):
        """Test plant identification with missing API key."""
        mock_config.PLANTID_API_KEY = None

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score = identify_plant(img_path)
        assert name is None
        assert score == 0

    @patch("src.vision_module.check_blur")
    def test_identify_plant_blurry_image(self, mock_check_blur, tmp_path):
        """Test plant identification with blurry image."""
        mock_check_blur.return_value = (False, 50.0)

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score = identify_plant(img_path)
        assert name == "BLURRY_IMAGE"
        assert score == 50.0

    @patch("src.vision_module.check_blur")
    @patch("src.vision_module.requests.post")
    @patch("src.vision_module.APIConfig")
    def test_identify_plant_api_timeout(
        self, mock_config, mock_post, mock_check_blur, tmp_path
    ):
        """Test plant identification with API timeout."""
        mock_config.PLANTID_API_KEY = "test_key"
        mock_check_blur.return_value = (True, 100.0)
        mock_post.side_effect = Exception("Timeout")

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score = identify_plant(img_path)
        assert name is None
        assert score == 0

    @patch("src.vision_module.check_blur")
    @patch("src.vision_module.requests.post")
    @patch("src.vision_module.APIConfig")
    def test_identify_plant_success(
        self, mock_config, mock_post, mock_check_blur, tmp_path
    ):
        """Test successful plant identification."""
        mock_config.PLANTID_API_KEY = "test_key"
        mock_check_blur.return_value = (True, 100.0)

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "is_plant": {"binary": True},
                "classification": {
                    "suggestions": [{"name": "Rosa canina", "probability": 0.95}]
                },
            }
        }
        mock_post.return_value = mock_response

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score = identify_plant(img_path)
        assert name == "Rosa canina"
        assert score == 0.95

    @patch("src.vision_module.check_blur")
    @patch("src.vision_module.requests.post")
    @patch("src.vision_module.APIConfig")
    def test_identify_plant_not_a_plant(
        self, mock_config, mock_post, mock_check_blur, tmp_path
    ):
        """Test plant identification when image is not a plant."""
        mock_config.PLANTID_API_KEY = "test_key"
        mock_check_blur.return_value = (True, 100.0)

        # Mock API response indicating not a plant
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {"is_plant": {"binary": False}}}
        mock_post.return_value = mock_response

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score = identify_plant(img_path)
        assert name == "NOT_A_PLANT"
        assert score == 0

    @patch("src.vision_module.check_blur")
    @patch("src.vision_module.requests.post")
    @patch("src.vision_module.APIConfig")
    def test_identify_plant_malformed_json(
        self, mock_config, mock_post, mock_check_blur, tmp_path
    ):
        """Test plant identification with malformed JSON response."""
        mock_config.PLANTID_API_KEY = "test_key"
        mock_check_blur.return_value = (True, 100.0)

        # Mock response with invalid JSON
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score = identify_plant(img_path)
        assert name is None
        assert score == 0
