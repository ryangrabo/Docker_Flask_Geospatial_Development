import sys
import os
from ultralytics import YOLO  # YOLO inference
import time
import logging  # I use this for debugging and tracking what's happening in the code
import pymongo  # I use this for additional MongoDB functionality when needed
from app.utils import convert_to_degrees, connect_to_mongodb
import exifread  # I use this to read EXIF data from images
from pymongo import MongoClient  # I use this to connect to MongoDB databases
from flask import Blueprint, render_template, request, redirect, url_for, send_file, abort, Flask, Response, redirect, flash, session  # I use these Flask utilities for creating views, rendering templates, sending files, etc.
import gridfs  # storing and retrieving the images in MongoDB
from bson import ObjectId, Binary  # I use these for handling MongoDB object IDs and binary data
from io import BytesIO  # creating in-memory streams for file-like operations
import numpy as np  # numerical operations (like array handling)
import cv2  # image manipulation with OpenCV
from PIL import Image  #  working with images in Python
import csv
from datetime import datetime


#setup logging
logging.basicConfig(level=logging.INFO)

WAIT_INTERVAL=1

# # Offsets for drone error:
# LATITUDE_OFFSET = 0.00004
# LONGITUDE_OFFSET = 0.00
# AGL_OFFSET_FEET = -10  # Adjust to make AGL values ~20 feet

# Use the Docker service name when running inside Docker
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

DATABASE_NAME = "InvasiveSpeciesDB"
COLLECTION_NAME = "ImageProcessingResults"

#file storage system for mongo
client = MongoClient(MONGO_URI)  # Connect to MongoDB
db = client[DATABASE_NAME]  # Get database instance
fs = gridfs.GridFS(db)  
fs_files = db["fs.files"]

#load model
model_path = os.path.join(os.getcwd(), "app", "single_model0.3.1.pt")
model = YOLO(model_path)  # Load the model

client = connect_to_mongodb()
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

def process_image(file_id):
    """
    Process an image and store results in the collection
    :param file_id: string of the file_id of the object from fs.files
    :return: returns info if it was completed or not
    """
    #first, check if the image is in image_db
    # Retrieve the image from MongoDB
    try:
        retrieved_file = fs.get(ObjectId(file_id))
    except Exception as e:
        logging.error(f"Unable to access id {file_id}.\nError: {e}")
        return f"Unable to access id {file_id}.\nError: {e}"
    
    try:
        file_bytes = retrieved_file.read()
        image_data = np.array(Image.open(BytesIO(file_bytes)))  # Convert to NumPy array
        image_data = cv2.cvtColor(image_data, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR
    except Exception as e:
        logging.error(f"Unable to convert Object with ID: {file_id} to image_data. \nError: {e}") 
        return f"Unable to convert Object with ID: {file_id} to image_data."
    # Run YOLO inference
    #result = model.predict(image_data, verbose=False)[0]
    result = model.predict(image_data, verbose=False, device=0)[0]
    
 
    # get results
    top_index = result.probs.top1  # Get top prediction index
    top_class = result.names[top_index]  # Get class name
    probabilities = result.probs.data.tolist()  # Get probabilities

    #low probability flag
    if probabilities[top_index] < .85 :
        low_prob = True
    else :
        low_prob = False
            
    # Extract EXIF metadata
    stream = BytesIO(file_bytes)
    tags = exifread.process_file(stream, details=False)

    # Extract GPS data
    lat, lon = None, None
    try:
        if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
            lat = convert_to_degrees(tags['GPS GPSLatitude'], tags.get('GPS GPSLatitudeRef'))
            lon = convert_to_degrees(tags['GPS GPSLongitude'], tags.get('GPS GPSLongitudeRef'))
            # lat = lat - LATITUDE_OFFSET if lat is not None else None
            # lon = lon - LONGITUDE_OFFSET if lon is not None else None
    except Exception as e:
        logging.error(f"GPS extraction failed for file_id {file_id}: {e}")

    # # Extract image direction (yaw) if available
    # yaw = "Unknown"
    # try:
    #     if 'GPS GPSImgDirection' in tags:
    #         direction = tags['GPS GPSImgDirection'].values[0]
    #         yaw = float(direction.num) / float(direction.den)
    # except Exception:
    #     yaw = "Unknown"

    # # Extract altitude (meters) if available
    # altitude_meters = None
    # try:
    #     if 'GPS GPSAltitude' in tags:
    #         altitude = tags['GPS GPSAltitude'].values[0]
    #         altitude_meters = float(altitude.num) / float(altitude.den)
    # except Exception:
    #     altitude_meters = None

    # Ensure geometry is valid
    geometry = {"type": "Point", "coordinates": [lon, lat]} if lat is not None and lon is not None else None
    # total_inference = result.speed['inference']+result.speed['preprocess']+result.speed['postprocess']
    
    # Create GeoJSON formatted result
    geojson_result = {
        "type": "Feature",
        "properties": {
            "filename": retrieved_file.filename ,
            "predicted_class": top_class,
            "narrowleaf_cattail_prob": probabilities[0],
            "none_prob": probabilities[1],
            "phragmites_prob": probabilities[2],
            "purple_loosestrife_prob": probabilities[3],
            "low_prob_flag": low_prob,
            "file_id": str(file_id),
            # "yaw": yaw,
            # "msl_alt": altitude_meters,
            # "total_inference": total_inference,
            # "inference": result.speed['inference'],
            # "preprocess": result.speed['preprocess'],
            # "postprocess": result.speed['postprocess'],
            # "timestamp": datetime.now().isoformat(),
        },
        "geometry": geometry
    }

    # save results in MongoDB immediately in the loop
    insert_result = collection.insert_one(geojson_result)

    update_result = fs_files.update_one(
        {"_id": ObjectId(file_id)},  # Ensure ObjectId conversion
        {"$set": {"metadata.processed": True}}
    )

    # if update_result.modified_count == 0:
    #     logging.warning(f"Failed to update metadata for file_id {file_id}")
    # else:
    #     logging.info(f"Marked file {file_id} as processed.")

    if insert_result.inserted_id:
        logging.info(f"Saved results with id: {insert_result.inserted_id}")
        return f"Saved results with id: {insert_result.inserted_id}"

    return "error: unable to save to DB"

def process_images():
    """
    Runs a loop that queries DB based on an interval
    Processes any images that it find that are unprocessed
    """
    logging.info(f"Process images Worker Started with PID: {os.getpid()}\nChecks DB every {WAIT_INTERVAL} seconds for unprocessed images.")
    while True:
        query_results = list(fs_files.find({"metadata.processed": False}).batch_size(50))  # Convert cursor to list
        length = len(query_results)
        if length > 0:
            logging.info(f"Found {length} unprocessed images.")

            #logging.info(query_results)

            for doc in query_results:
                id = str(doc["_id"])
                #logging.info(f"To be processed: Object ID: {id}")
                process_image(id)
            
            #continue to next iteration instead of waiting, because there may be more images then were found in the initial query
            continue

        time.sleep(WAIT_INTERVAL)
        
