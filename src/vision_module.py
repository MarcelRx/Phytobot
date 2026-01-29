import os
import requests
from dotenv import load_dotenv

load_dotenv()


def identify_plant(image_path):
    """
    Identifies a plant from an image using Plant.id API.
    Returns:
    - scientific or common name
    - confidence probability (0.0 - 1.0)
    """

    plant_name = None
    probability = 0.0
    api_key = os.getenv("PLANTID_API_KEY")

    try:
        with open(image_path, "rb") as f:
            response = requests.post(
                "https://api.plant.id/v2/identify",
                files={"images[]": f},
                headers={"Api-Key": api_key},
                timeout=10
            )

        if response.status_code == 200:
            result = response.json()
            if result.get("suggestions"):
                best = result["suggestions"][0]
                plant_name = (
                    best.get("plant_details", {})
                    .get("scientific_name")
                    or best.get("plant_name")
                )
                probability = best.get("probability", 0.0)

    except Exception as e:
        print(f"Vision API Error: {e}")

    return plant_name, probability
