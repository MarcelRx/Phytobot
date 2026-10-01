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
    from src.vision_module import (
        PlantIdentificationResult,
        check_blur,
        identify_plant,
    )

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

        name, score, result_type = identify_plant(img_path)
        assert name is None
        assert score == 0
        assert result_type == PlantIdentificationResult.AUTH_ERROR

    @patch("src.vision_module.check_blur")
    def test_identify_plant_blurry_image(self, mock_check_blur, tmp_path):
        """Test plant identification with blurry image."""
        mock_check_blur.return_value = (False, 50.0)

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score, result_type = identify_plant(img_path)
        assert name == "BLURRY_IMAGE"
        assert score == 50.0
        assert result_type == PlantIdentificationResult.BLURRY_IMAGE

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

        name, score, result_type = identify_plant(img_path)
        assert name is None
        assert score == 0
        assert result_type == PlantIdentificationResult.API_ERROR

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

        name, score, result_type = identify_plant(img_path)
        assert name == "Rosa canina"
        assert score == 0.95
        assert result_type == PlantIdentificationResult.SUCCESS

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

        name, score, result_type = identify_plant(img_path)
        assert name == "NOT_A_PLANT"
        assert score == 0
        assert result_type == PlantIdentificationResult.NOT_A_PLANT

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

        name, score, result_type = identify_plant(img_path)
        assert name is None
        assert score == 0
        assert result_type == PlantIdentificationResult.API_ERROR

    @patch("src.vision_module.check_blur")
    @patch("src.vision_module.requests.post")
    @patch("src.vision_module.APIConfig")
    def test_identify_plant_rate_limit_429(
        self, mock_config, mock_post, mock_check_blur, tmp_path
    ):
        """Test plant identification with HTTP 429 rate limit."""
        mock_config.PLANTID_API_KEY = "test_key"
        mock_check_blur.return_value = (True, 100.0)

        # Mock 429 response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}
        mock_post.return_value = mock_response

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score, result_type = identify_plant(img_path)
        assert name is None
        assert score == 0
        assert result_type == PlantIdentificationResult.RATE_LIMIT

    @patch("src.vision_module.check_blur")
    @patch("src.vision_module.requests.post")
    @patch("src.vision_module.APIConfig")
    def test_identify_plant_rate_limit_with_retry_after(
        self, mock_config, mock_post, mock_check_blur, tmp_path
    ):
        """Test plant identification with HTTP 429 and Retry-After header."""
        mock_config.PLANTID_API_KEY = "test_key"
        mock_check_blur.return_value = (True, 100.0)

        # Mock 429 response with Retry-After header
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "1"}

        # Mock successful response after retry
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "result": {
                "is_plant": {"binary": True},
                "classification": {
                    "suggestions": [{"name": "Rosa canina", "probability": 0.95}]
                },
            }
        }

        # First call returns 429, second call succeeds
        mock_post.side_effect = [mock_response_429, mock_response_success]

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score, result_type = identify_plant(img_path)
        assert name == "Rosa canina"
        assert score == 0.95
        assert result_type == PlantIdentificationResult.SUCCESS

    @patch("src.vision_module.check_blur")
    @patch("src.vision_module.requests.post")
    @patch("src.vision_module.APIConfig")
    def test_identify_plant_rate_limit_retry_after_capped(
        self, mock_config, mock_post, mock_check_blur, tmp_path
    ):
        """Test plant identification with HTTP 429 and large Retry-After header (capped at max)."""
        mock_config.PLANTID_API_KEY = "test_key"
        mock_check_blur.return_value = (True, 100.0)

        # Mock 429 response with large Retry-After header (should be capped at 60s)
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "300"}

        # Mock successful response after retry
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "result": {
                "is_plant": {"binary": True},
                "classification": {
                    "suggestions": [{"name": "Rosa canina", "probability": 0.95}]
                },
            }
        }

        # First call returns 429, second call succeeds
        mock_post.side_effect = [mock_response_429, mock_response_success]

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score, result_type = identify_plant(img_path)
        assert name == "Rosa canina"
        assert score == 0.95
        assert result_type == PlantIdentificationResult.SUCCESS

    @patch("src.vision_module.check_blur")
    @patch("src.vision_module.requests.post")
    @patch("src.vision_module.APIConfig")
    def test_identify_plant_auth_error_401(
        self, mock_config, mock_post, mock_check_blur, tmp_path
    ):
        """Test plant identification with HTTP 401 authentication error."""
        mock_config.PLANTID_API_KEY = "test_key"
        mock_check_blur.return_value = (True, 100.0)

        # Mock 401 response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score, result_type = identify_plant(img_path)
        assert name is None
        assert score == 0
        assert result_type == PlantIdentificationResult.AUTH_ERROR

    @patch("src.vision_module.check_blur")
    @patch("src.vision_module.requests.post")
    @patch("src.vision_module.APIConfig")
    def test_identify_plant_auth_error_403(
        self, mock_config, mock_post, mock_check_blur, tmp_path
    ):
        """Test plant identification with HTTP 403 authorization error."""
        mock_config.PLANTID_API_KEY = "test_key"
        mock_check_blur.return_value = (True, 100.0)

        # Mock 403 response
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_post.return_value = mock_response

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score, result_type = identify_plant(img_path)
        assert name is None
        assert score == 0
        assert result_type == PlantIdentificationResult.AUTH_ERROR

    @patch("src.vision_module.check_blur")
    @patch("src.vision_module.requests.post")
    @patch("src.vision_module.APIConfig")
    def test_identify_plant_bad_request_400(
        self, mock_config, mock_post, mock_check_blur, tmp_path
    ):
        """Test plant identification with HTTP 400 bad request."""
        mock_config.PLANTID_API_KEY = "test_key"
        mock_check_blur.return_value = (True, 100.0)

        # Mock 400 response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_post.return_value = mock_response

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score, result_type = identify_plant(img_path)
        assert name is None
        assert score == 0
        assert result_type == PlantIdentificationResult.API_ERROR

    @patch("src.vision_module.check_blur")
    @patch("src.vision_module.requests.post")
    @patch("src.vision_module.APIConfig")
    def test_identify_plant_server_error_500(
        self, mock_config, mock_post, mock_check_blur, tmp_path
    ):
        """Test plant identification with HTTP 500 server error."""
        mock_config.PLANTID_API_KEY = "test_key"
        mock_check_blur.return_value = (True, 100.0)

        # Mock 500 response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score, result_type = identify_plant(img_path)
        assert name is None
        assert score == 0
        assert result_type == PlantIdentificationResult.API_ERROR

    @patch("src.vision_module.check_blur")
    @patch("src.vision_module.requests.post")
    @patch("src.vision_module.APIConfig")
    def test_identify_plant_network_error(
        self, mock_config, mock_post, mock_check_blur, tmp_path
    ):
        """Test plant identification with network error."""
        mock_config.PLANTID_API_KEY = "test_key"
        mock_check_blur.return_value = (True, 100.0)

        # Mock network error
        import requests

        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score, result_type = identify_plant(img_path)
        assert name is None
        assert score == 0
        assert result_type == PlantIdentificationResult.NETWORK_ERROR

    @patch("src.vision_module.check_blur")
    @patch("src.vision_module.requests.post")
    @patch("src.vision_module.APIConfig")
    def test_identify_plant_timeout_error(
        self, mock_config, mock_post, mock_check_blur, tmp_path
    ):
        """Test plant identification with timeout error."""
        mock_config.PLANTID_API_KEY = "test_key"
        mock_check_blur.return_value = (True, 100.0)

        # Mock timeout error
        import requests

        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score, result_type = identify_plant(img_path)
        assert name is None
        assert score == 0
        assert result_type == PlantIdentificationResult.TIMEOUT

    @patch("src.vision_module.check_blur")
    @patch("src.vision_module.requests.post")
    @patch("src.vision_module.APIConfig")
    def test_identify_plant_no_suggestions(
        self, mock_config, mock_post, mock_check_blur, tmp_path
    ):
        """Test plant identification when API returns no suggestions."""
        mock_config.PLANTID_API_KEY = "test_key"
        mock_check_blur.return_value = (True, 100.0)

        # Mock API response with no suggestions
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "is_plant": {"binary": True},
                "classification": {"suggestions": []},
            }
        }
        mock_post.return_value = mock_response

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = str(tmp_path / "test.jpg")
        cv2.imwrite(img_path, img)

        name, score, result_type = identify_plant(img_path)
        assert name is None
        assert score == 0
        assert result_type == PlantIdentificationResult.NO_PLANT_IDENTIFIED
