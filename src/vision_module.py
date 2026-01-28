import requests
import os
from dotenv import load_dotenv

load_dotenv()

def identify_plant(image_path):
    # Get API key from environment
    api_key = os.getenv("PLANTID_API_KEY")
    
    # Open image file in binary mode
    with open(image_path, "rb") as f:
        # Send POST request to Plant.id API
        response = requests.post(
            "https://api.plant.id/v2/identify",
            files={"images[]": f},
            headers={"Api-Key": api_key}
        )
    
    # Check if request was successful
    if response.status_code == 200:
        # Parse JSON response data
        result = response.json()
        # Extract plant details from response
        suggestion = result['suggestions'][0]
        plant_name = suggestion['plant_details']['scientific_name']
        probability = suggestion['probability']
    # Return results as tuple
    return plant_name, probability