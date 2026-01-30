import cv2
import numpy as np
import base64
import requests
import os
from dotenv import load_dotenv

# Load API keys from your .env file
load_dotenv()

def check_blur(image_path, threshold=70):
    """
    Calculates the Laplacian variance to detect if an image is blurry.
    A higher score means a sharper image.
    """
    img = cv2.imread(image_path)
    if img is None:
        return False, 0
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # The Laplacian operator highlights regions of an image containing rapid intensity changes
    score = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    return score > threshold, score

def identify_plant(image_path):
    """
    Identifies a plant from an image using the Plant.id API.
    Returns: (scientific_name, probability_score) or ("BLURRY_IMAGE", score)
    """
    # First, check image quality (The "Alarm" logic)
    is_sharp, score = check_blur(image_path)
    if not is_sharp:
        return "BLURRY_IMAGE", score

    # Prepare API details
    api_key = os.getenv("PLANTID_API_KEY")
    # Using v3 endpoint for the most accurate and up-to-date results
    api_url = "https://api.plant.id/v3/identification"
    
    try:
        # Encode image to Base64
        with open(image_path, "rb") as file:
            base64_image = base64.b64encode(file.read()).decode("ascii")

        # Define request payload
        payload = {
            "images": [base64_image],
            "latitude": 49.1951, # Optional: Change to your coordinates for better accuracy
            "longitude": 16.6068,
            "similar_images": True
        }

        headers = {
            "Content-Type": "application/json",
            "Api-Key": api_key
        }

        # Send POST request to Plant.id
        response = requests.post(
            api_url, 
            json=payload, 
            headers=headers, 
            params={"details": "common_names,url,description"}
        )
        
        # Handle the response
        if response.status_code == 201 or response.status_code == 200:
            result = response.json()
            
            # Check if a plant was actually found in the image
            if not result.get("result", {}).get("is_plant", {}).get("binary", False):
                return "NOT_A_PLANT", 0

            # Get the top suggestion
            suggestions = result.get("result", {}).get("classification", {}).get("suggestions", [])
            if suggestions:
                top_match = suggestions[0]
                scientific_name = top_match.get("name")
                probability = top_match.get("probability")
                
                return scientific_name, probability
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return None, 0

    except Exception as e:
        print(f"Vision Module Critical Error: {e}")
        return None, 0

    return None, 0

# Test Block (Run this file directly to test)
if __name__ == "__main__":
    # Create a dummy image or use an existing one to test
    test_image = "test_plant.jpg" 
    if os.path.exists(test_image):
        name, prob = identify_plant(test_image)
        print(f"Result: {name} with {prob*100:.2f}% confidence.")
    else:
        print("Please place a 'test_plant.jpg' in the folder to test this script.")