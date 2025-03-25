import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ultralytics import YOLO  # YOLO inference
import time
import logging  # I use this for debugging and tracking what's happening in the code
import pymongo  # I use this for additional MongoDB functionality when needed
from app.utils import convert_to_degrees, connect_to_mongodb
import exifread  # I use this to read EXIF data from images
from pymongo import MongoClient  # I use this to connect to MongoDB databases
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, send_file, abort, Flask, Response, redirect, flash, session  # I use these Flask utilities for creating views, rendering templates, sending files, etc.

#setup logging
logging.basicConfig(level=logging.INFO)

# Offsets for drone error:
LATITUDE_OFFSET = 0.00004
LONGITUDE_OFFSET = 0.00
AGL_OFFSET_FEET = -10  # Adjust to make AGL values ~20 feet

# Use the Docker service name when running inside Docker
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

DATABASE_NAME = "seniorDesignTesting"
COLLECTION_NAME = "sendAndRecievePlantInfoTest"
IMAGES_COLLECTION_NAME ="image_db"

#upload folder
UPLOAD_FOLDER="../images"

#file storage system for mongo
client = MongoClient(MONGO_URI)  # Connect to MongoDB
db = client[DATABASE_NAME]  # Get database instance

#load model
model_path = os.path.join(os.getcwd(), "app", "single_model0.3.1.pt")
model = YOLO(model_path)  # Load the model

client = connect_to_mongodb()
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]
upload_collection = db[IMAGES_COLLECTION_NAME]

def process_image(image_path):
    #first, check if the image is in image_db
    image_doc = upload_collection.find_one({"filepath": image_path})

    if image_doc:
        image_id = image_doc["_id"]  # Extract the ObjectId
    else:
        return f"Error, could not find object for {image_path} in DB"
    result = model.predict(image_path, stream=False, verbose=False)[0]  # Get the first result

    # get results
    top_index = result.probs.top1  # Get top prediction index
    top_class = result.names[top_index]  # Get class name
    probabilities = result.probs.data.tolist()  # Get probabilities
        
    # Extract EXIF metadata
    tags = exifread.process_file(image_path, details=False)

    # Extract GPS data
    lat, lon = None, None
    try:
        if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
            lat = convert_to_degrees(tags['GPS GPSLatitude'], tags.get('GPS GPSLatitudeRef'))
            lon = convert_to_degrees(tags['GPS GPSLongitude'], tags.get('GPS GPSLongitudeRef'))
            lat = lat - LATITUDE_OFFSET if lat is not None else None
            lon = lon - LONGITUDE_OFFSET if lon is not None else None
    except Exception as e:
        logging.error(f"GPS extraction failed for file_id {file_id}: {e}")

    # Extract image direction (yaw) if available
    yaw = "Unknown"
    try:
        if 'GPS GPSImgDirection' in tags:
            direction = tags['GPS GPSImgDirection'].values[0]
            yaw = float(direction.num) / float(direction.den)
    except Exception:
        yaw = "Unknown"

    # Extract altitude (meters) if available
    altitude_meters = None
    try:
        if 'GPS GPSAltitude' in tags:
            altitude = tags['GPS GPSAltitude'].values[0]
            altitude_meters = float(altitude.num) / float(altitude.den)
    except Exception:
        altitude_meters = None

    # Ensure geometry is valid
    geometry = {"type": "Point", "coordinates": [lon, lat]} if lat is not None and lon is not None else None

    # Create GeoJSON formatted result
    geojson_result = {
        "type": "Feature",
        "properties": {
            "filename": file.filename,
            "predicted_class": top_class,
            "narrowleaf_cattail_prob": probabilities[0],
            "none_prob": probabilities[1],
            "phragmites_prob": probabilities[2],
            "purple_loosestrife_prob": probabilities[3],
            "file_id": str(image_id),
            "yaw": yaw,
            "msl_alt": altitude_meters,
        },
        "geometry": geometry
    }

    # save results in MongoDB
    insert_result = collection.insert_one(geojson_result)
    if insert_result.inserted_id:
        return f"Saved {image_path} with ID: {insert_result.inserted_id}"

    return f"Error: unable to save to DB"

def process_folder(folder_path):
    """
    Processes a folder of images by inferencing, getting location metadata, and storing results in the DB
    :param folder_path: path to the folder
    :return: 
    """
    start_time = time.perf_counter()

    image_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)]

    for file in image_files:
        process_image(file)

    end_time = time.perf_counter()
    elapsed_time = round(end_time - start_time, 4)
    logging.info(f"Total process Time for the folder: {elapsed_time:.4f} seconds.")

# In process_folder.py
if __name__ == "__main__":
    folder_path = sys.argv[1]  # Get folder path from command line argument
    process_folder(folder_path)


    