import os       # I use this for working with the file system and environment variables
import logging  # I use this for debugging and tracking what's happening in the code
import base64   # I use this for encoding/decoding data to and from Base64
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, send_file, abort, Flask, Response, redirect, flash, session  # I use these Flask utilities for creating views, rendering templates, sending files, etc.
from werkzeug.utils import secure_filename  # I use this to safely handle filenames when uploading
from pymongo import MongoClient  # I use this to connect to MongoDB databases
import pymongo  # I use this for additional MongoDB functionality when needed
from bson import ObjectId, Binary  # I use these for handling MongoDB object IDs and binary data
import exifread  # I use this to read EXIF data from images
from io import BytesIO  # creating in-memory streams for file-like operations
from ultralytics import YOLO  # YOLO inference
import time  # time
import cv2  # image manipulation with OpenCV
import numpy as np  # numerical operations (like array handling)
from PIL import Image  #  working with images in Python
import gridfs  # storing and retrieving the images in MongoDB
from app.utils import convert_to_degrees, allowed_file, connect_to_mongodb
import threading
from app.process_images import process_images

#create worker to query DB regularly and check for unprocessed images:
threading.Thread(target=process_images, daemon=True).start()

bp = Blueprint("main", __name__)

# Use the Docker service name when running inside Docker
MONGO_URI = os.getenv("MONGO_URI", "mongodb://0.0.0.0:27017/")

DATABASE_NAME = "seniorDesignTesting"
COLLECTION_NAME = "sendAndRecievePlantInfoTest"

#file storage system for mongo
client = MongoClient(MONGO_URI)  # Connect to MongoDB
db = client[DATABASE_NAME]  # Get database instance
fs = gridfs.GridFS(db)  

# Offsets for drone error:
LATITUDE_OFFSET = 0.00004
LONGITUDE_OFFSET = 0.00
AGL_OFFSET_FEET = -10  # Adjust to make AGL values ~20 feet

#load model
model_path = os.path.join(os.getcwd(), "app", "single_model0.3.1.pt")
model = YOLO(model_path)  # Load the model

logging.basicConfig(level=logging.INFO)


#MAPBOX

@bp.route("/", endpoint="index")
def index():
    if "user" not in session:
             flash("Please log in to access this page.")
             return redirect(url_for("auth.login"))
    """Render a simple landing page."""
    return render_template("mapbox.html", mapbox_token=os.getenv("MAPBOX_TOKEN"))
    #return render_template("index.html", mapbox_token=os.getenv("MAPBOX_TOKEN"))

@bp.route('/images')
def get_images():
    if "user" not in session:
        flash("Please log in to access this page.")
        return redirect(url_for("auth.login"))

    """Fetches image data from MongoDB and returns it directly as GeoJSON."""
    client = connect_to_mongodb()
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    # Directly return the entire collection as a GeoJSON FeatureCollection
    geojson_data = {
        "type": "FeatureCollection",
        "features": list(collection.find({}, {"_id": 0}))  # Exclude MongoDB's _id
    }

    return jsonify(geojson_data)


@bp.route("/getImage/<file_id>", methods=["GET"])
def get_image(file_id):
    
    """Retrieve and serve an image stored in MongoDB GridFS."""
    if "user" not in session:
             flash("Please log in to access this page.")
             return redirect(url_for("auth.login"))
    try:
        # Convert file_id from string to ObjectId
        file_object_id = ObjectId(file_id)

        # Retrieve the image from GridFS
        retrieved_file = fs.get(file_object_id)

        return send_file(BytesIO(retrieved_file.read()), mimetype="image/jpeg")

    except Exception as e:
        return jsonify({"error": f"Image not found: {str(e)}"}), 404



@bp.route("/runInference", methods=["GET", "POST"])
def run_inference():
    if "user" not in session:
                flash("Please log in to access this page.")
                return redirect(url_for("auth.login"))

    if request.method == "GET":
        return render_template("runInference.html")

    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    files = request.files.getlist("file")  # Handle multiple files

    if not files:
        return jsonify({"error": "No files selected"}), 400

    results_list = []
    start_time = time.perf_counter()

    for file in files:
        if file.filename == "":
            continue

        if not file or not allowed_file(file.filename):
            continue
        
        filename = secure_filename(file.filename)

        # Save file to MongoDB GridFS
        file_id = fs.put(file, filename=filename)
        logging.info(f"Saved to MongoDB with ID: {file_id}")

        # Retrieve the image from MongoDB
        retrieved_file = fs.get(file_id)
        image_data = np.array(Image.open(BytesIO(retrieved_file.read())))  # Convert to NumPy array
        image_data = cv2.cvtColor(image_data, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR
        
        # Run YOLO inference
        results = model.predict(image_data, stream=True, verbose=False)

        for result in results:
            top_index = result.probs.top1  # Get top prediction index
            top_class = result.names[top_index]  # Get class name
            probabilities = result.probs.data.tolist()  # Get probabilities
            total_inference = result.speed['inference']+result.speed['preprocess']+result.speed['postprocess']

            results_list.append({
                "total_inference_time": total_inference,
                "filename": filename,
                "predicted_class": top_class,
                "narrowleaf_cattail_prob": probabilities[0],
                "none_prob": probabilities[1],
                "phragmites_prob": probabilities[2],
                "purple_loosestrife_prob": probabilities[3],
                "top_index": top_index,
                "file_id": str(file_id)  # Store MongoDB file ID
            })

    end_time = time.perf_counter()
    elapsed_time = round(end_time - start_time, 4)

    return jsonify({
        "results": results_list,
        "elapsed_time": elapsed_time
    })


@bp.route("/upload_images", methods=["POST"])
def upload_images():
    if "user" not in session:
        flash("Please log in to access this page.")
        return redirect(url_for("auth.login"))

    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    files = request.files.getlist("file")  # Handle multiple files

    if not files:
        return jsonify({"error": "No files selected"}), 400

    client = connect_to_mongodb()
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    inserted_count=0
    start_time = time.perf_counter()

    for file in files:
        if file.filename == "":
            continue

        if not file or not allowed_file(file.filename):
            continue
        
        filename = secure_filename(file.filename)

        # Save file to MongoDB GridFS
        file_id = fs.put(file, filename=filename, metadata={"processed": False})
        logging.info(f"Saved to MongoDB with ID: {file_id}")

        if file_id:
            inserted_count+=1
   
    # return message to client
    if inserted_count>0:
        logging.info(f"Saved {inserted_count} images into the DB")
        return jsonify({"message": f"Saved {inserted_count} images to be processed."})

    return jsonify({"error": "No valid results to save"}), 400

        

    

@bp.route("/saveResults", methods=["POST"])
def save_results():
    if "user" not in session:
             flash("Please log in to access this page.")
             return redirect(url_for("auth.login"))
    
    client = connect_to_mongodb()
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    data = request.json
    results = data.get("results", [])

    if not results:
        return jsonify({"error": "No results provided"}), 400

    geojson_results = []

    for result in results:
        try:
            # Ensure `result` is a valid dictionary
            if not isinstance(result, dict):
                logging.warning(f"Skipping invalid result entry: {result}")
                continue  # Skip invalid entries

            file_id = result.get("file_id")
            if not file_id:
                logging.warning(f"Skipping result due to missing file_id: {result}")
                continue  # Skip this entry

            # Retrieve image file from MongoDB GridFS
            try:
                retrieved_file = fs.get(ObjectId(file_id))
            except Exception as e:
                logging.error(f"File not found in MongoDB for file_id: {file_id}, Error: {e}")
                continue  # Skip if file retrieval fails

            file_bytes = retrieved_file.read()

            # Extract EXIF metadata
            stream = BytesIO(file_bytes)
            tags = exifread.process_file(stream, details=False)

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
            geojson_results.append({
                "type": "Feature",
                "properties": {
                    "filename": result.get("filename", "Unknown"),
                    "predicted_class": result.get("predicted_class", "Unknown"),
                    #"total_inference_time": result.get("total_inference_time", 0),
                    "narrowleaf_cattail_prob": result.get("narrowleaf_cattail_prob", 0),
                    "none_prob": result.get("none_prob", 0),
                    "phragmites_prob": result.get("phragmites_prob", 0),
                    "purple_loosestrife_prob": result.get("purple_loosestrife_prob", 0),
                    "file_id": file_id,
                    "yaw": yaw,
                    "msl_alt": altitude_meters,
                },
                "geometry": geometry
            })

        except Exception as e:
            logging.error(f"Unexpected error processing file (file_id unknown): {e}")

    # Save results in MongoDB
    if geojson_results:
        inserted_ids = collection.insert_many(geojson_results).inserted_ids
        return jsonify({"message": f"Saved {len(inserted_ids)} results to the database"})

    return jsonify({"error": "No valid results to save"}), 400


@bp.route("/exportData")
def export_Data():
    if "user" not in session:
             flash("Please log in to access this page.")
             return redirect(url_for("auth.login"))
    return render_template("exportData.html")

@bp.route('/getLowProbImages', methods=["GET"])
def get_low_prob_images_html():
    if "user" not in session:
        flash("Please log in to access this page.")
        return redirect(url_for("auth.login"))
    client = connect_to_mongodb()
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    # Find all documents where low_prob == "1"
    low_prob_docs = collection.find({"properties.low_prob": 1})

    # Extract filenames for rendering
    images = [{"filename": doc["properties"]["filename"],
        "file_id": doc["properties"]["file_id"]} for doc in low_prob_docs]

    return render_template("lowProbImages.html", images=images)

@bp.route('/numLowProbimages')
def get_num_low_prob_images():
    if "user" not in session:
        flash("Please log in to access this page.")
        return redirect(url_for("auth.login"))

    client = connect_to_mongodb()
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    num_low_prob = collection.count_documents({"properties.low_prob": 1})
    logging.info(f"Found {num_low_prob} low_prob images.")


    return jsonify({"num_low_prob": num_low_prob})

@bp.route("/categorize_images", methods=["POST"])
def categorize_images():
    if "user" not in session:
        flash("Please log in to access this page.")
        return redirect(url_for("auth.login"))

    filename = request.form.get("filename")
    category = request.form.get("category")

    if not filename or not category:
        flash("Missing filename or category.")
        return redirect(url_for("main.get_low_prob_images_html"))

    client = connect_to_mongodb()
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    # Update the image's predicted_class and set low_prob to "0"
    result = collection.update_one(
        {"properties.filename": filename},
        {"$set": {
            "properties.predicted_class": category,
            "properties.low_prob": 0
        }}
    )

    if result.modified_count > 0:
        logging.info(f"Image {filename} updated with category '{category}'")
    else:
        logging.warning(f"No matching image found for {filename}")

    return redirect(url_for("main.get_low_prob_images_html"))
