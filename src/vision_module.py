import base64
import logging
import os
import time
from enum import Enum
from typing import Optional, Tuple

import cv2
import requests
from dotenv import load_dotenv

from src.config import APIConfig, VisionConfig

# Load API keys from your .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class PlantIdentificationResult(Enum):
    """Enumeration of plant identification result types."""

    SUCCESS = "success"
    BLURRY_IMAGE = "blurry_image"
    NOT_A_PLANT = "not_a_plant"
    RATE_LIMIT = "rate_limit"
    AUTH_ERROR = "auth_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    API_ERROR = "api_error"
    NO_PLANT_IDENTIFIED = "no_plant_identified"


def check_blur(image_path: str, threshold: int = None) -> Tuple[bool, float]:
    """
    Calculates the Laplacian variance to detect if an image is blurry.
    A higher score means a sharper image.

    Args:
        image_path: Path to the image file
        threshold: Blur threshold (uses config default if None)

    Returns:
        Tuple of (is_sharp, blur_score)
    """
    if threshold is None:
        threshold = VisionConfig.BLUR_THRESHOLD

    try:
        img = cv2.imread(image_path)
        if img is None:
            logger.warning(f"Could not read image at {image_path}")
            return False, 0

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # The Laplacian operator highlights regions of an image containing rapid intensity changes
        score = cv2.Laplacian(gray, cv2.CV_64F).var()

        is_sharp = bool(score > threshold)
        logger.debug(
            f"Blur check: score={score:.2f}, threshold={threshold}, sharp={is_sharp}"
        )
        return is_sharp, float(score)
    except Exception as e:
        logger.error(f"Error during blur detection: {e}")
        return False, 0


def identify_plant(
    image_path: str,
) -> Tuple[Optional[str], float, PlantIdentificationResult]:
    """
    Identifies a plant from an image using the Plant.id API.

    Args:
        image_path: Path to the image file

    Returns:
        Tuple of (scientific_name, probability_score, result_type)
        result_type indicates the status of the identification attempt
    """
    # First, check image quality (The "Alarm" logic)
    is_sharp, score = check_blur(image_path)
    if not is_sharp:
        return "BLURRY_IMAGE", score, PlantIdentificationResult.BLURRY_IMAGE

    # Prepare API details
    api_key = APIConfig.PLANTID_API_KEY
    if not api_key:
        logger.error("PLANTID_API_KEY not configured")
        return None, 0, PlantIdentificationResult.AUTH_ERROR

    # Using v3 endpoint for the most accurate and up-to-date results
    api_url = "https://api.plant.id/v3/identification"

    # Retry configuration for rate limiting
    max_retries = 1
    retry_delay = 2  # seconds

    for attempt in range(max_retries + 1):
        try:
            # Encode image to Base64
            with open(image_path, "rb") as file:
                base64_image = base64.b64encode(file.read()).decode("ascii")

            # Define request payload
            payload = {
                "images": [base64_image],
                "latitude": 49.1951,  # Optional: Change to your coordinates for better accuracy
                "longitude": 16.6068,
                "similar_images": True,
            }

            headers = {"Content-Type": "application/json", "Api-Key": api_key}

            # Send POST request to Plant.id with timeout
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                params={"details": "common_names,url,description"},
                timeout=APIConfig.PLANTID_TIMEOUT,
            )

            # Handle the response
            if response.status_code in (200, 201):
                try:
                    result = response.json()
                except ValueError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    return None, 0, PlantIdentificationResult.API_ERROR

                # Check if a plant was actually found in the image
                if (
                    not result.get("result", {})
                    .get("is_plant", {})
                    .get("binary", False)
                ):
                    logger.info("Image does not contain a plant")
                    return "NOT_A_PLANT", 0, PlantIdentificationResult.NOT_A_PLANT

                # Get the top suggestion
                suggestions = (
                    result.get("result", {})
                    .get("classification", {})
                    .get("suggestions", [])
                )
                if suggestions:
                    top_match = suggestions[0]
                    scientific_name = top_match.get("name")
                    probability = top_match.get("probability")

                    if scientific_name and probability is not None:
                        logger.info(
                            f"Identified plant: {scientific_name} (confidence: {probability:.2%})"
                        )
                        return (
                            scientific_name,
                            probability,
                            PlantIdentificationResult.SUCCESS,
                        )
                    else:
                        logger.warning("Malformed suggestion data received")
                        return None, 0, PlantIdentificationResult.API_ERROR
                else:
                    logger.warning("No suggestions in API response")
                    return None, 0, PlantIdentificationResult.NO_PLANT_IDENTIFIED
            elif response.status_code == 401:
                logger.error("Plant.id API authentication failed")
                return None, 0, PlantIdentificationResult.AUTH_ERROR
            elif response.status_code == 429:
                logger.warning("Plant.id API rate limit exceeded")
                # Check for Retry-After header
                retry_after = response.headers.get("Retry-After")
                if retry_after and attempt < max_retries:
                    try:
                        wait_time = int(retry_after)
                        logger.info(
                            f"Rate limited. Waiting {wait_time} seconds before retry..."
                        )
                        time.sleep(wait_time)
                        continue
                    except ValueError:
                        # If Retry-After is not a number, use default delay
                        logger.info(
                            f"Rate limited. Waiting {retry_delay} seconds before retry..."
                        )
                        time.sleep(retry_delay)
                        continue
                elif attempt < max_retries:
                    logger.info(
                        f"Rate limited. Waiting {retry_delay} seconds before retry..."
                    )
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(
                        "Plant.id API rate limit exceeded (max retries reached)"
                    )
                    return None, 0, PlantIdentificationResult.RATE_LIMIT
            else:
                logger.error(
                    f"Plant.id API error: {response.status_code} - {response.text}"
                )
                return None, 0, PlantIdentificationResult.API_ERROR

        except requests.exceptions.Timeout:
            logger.error("Plant.id API request timed out")
            return None, 0, PlantIdentificationResult.TIMEOUT
        except requests.exceptions.RequestException as e:
            logger.error(f"Plant.id API request failed: {e}")
            return None, 0, PlantIdentificationResult.NETWORK_ERROR
        except IOError as e:
            logger.error(f"Failed to read image file: {e}")
            return None, 0, PlantIdentificationResult.API_ERROR
        except Exception as e:
            logger.error(f"Unexpected error in plant identification: {e}")
            return None, 0, PlantIdentificationResult.API_ERROR

    return None, 0, PlantIdentificationResult.API_ERROR


# Test Block (Run this file directly to test)
if __name__ == "__main__":
    # Configure logging for standalone testing
    logging.basicConfig(level=logging.INFO)

    # Create a dummy image or use an existing one to test
    test_image = "test_plant.jpg"
    if os.path.exists(test_image):
        name, prob = identify_plant(test_image)
        print(f"Result: {name} with {prob * 100:.2f}% confidence.")
    else:
        print("Please place a 'test_plant.jpg' in the folder to test this script.")
