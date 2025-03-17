import requests
import random
import uuid
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
DOG_API_URL = "https://dog.ceo/api/breeds/image/random"
NAME_API_URL = "https://randomuser.me/api/"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_dog_image():
    response = requests.get(DOG_API_URL)
    if response.status_code == 200:
        image_url = response.json()["message"]
        parts = image_url.split("/")
        if len(parts) >= 5:
            breed = parts[4]
            return image_url, breed
        return image_url, "NA"
    return None, None

def fetch_random_name():
    response = requests.get(NAME_API_URL)
    if response.status_code == 200:
        return response.json()["results"][0]["name"]["first"]
    return "Unknown"

def insert_dog_data():
    # Set to keep track of already used dog image URLs
    used_image_urls = set()
    
    for _ in range(500):
        dog_name = fetch_random_name()
        dog_image, dog_breed = None, None
        
        # Keep trying until we get a unique dog image
        while True:
            dog_image, dog_breed = fetch_dog_image()
            if dog_image and dog_image not in used_image_urls:
                used_image_urls.add(dog_image)
                break
        
        dog_price = int(random.uniform(50, 200))

        if dog_image:
            data = {
                "id": str(uuid.uuid4()),
                "name": dog_name,
                "image": dog_image,
                "breed": dog_breed,
                "price": dog_price,
                "bought": False
            }
            try:
                supabase.table("dogs").insert(data).execute()
                print(f"Inserted: {data}")
            except Exception as e:
                print(f"Error inserting data: {e}")

insert_dog_data()
