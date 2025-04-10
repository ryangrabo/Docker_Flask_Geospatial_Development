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
from app.exportToExcel import fetch_and_save_excel

#create worker to query DB regularly and check for unprocessed images:
threading.Thread(target=process_images, daemon=True).start()

bp = Blueprint("main", __name__)

DATABASE_NAME = "seniorDesignTesting"
COLLECTION_NAME = "sendAndRecievePlantInfoTest"

#load model
model_path = os.path.join(os.getcwd(), "app", "single_model0.3.1.pt")
model = YOLO(model_path)  # Load the model

logging.basicConfig(level=logging.INFO)

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
    """Fetches image data from MongoDB and returns it directly as GeoJSON."""
    if "user" not in session:
        flash("Please log in to access this page.")
        return redirect(url_for("auth.login"))

    client = connect_to_mongodb()
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    # Directly return the entire collection as a GeoJSON FeatureCollection
    geojson_data = {
        "type": "FeatureCollection",
        "features": list(collection.find({}, {"_id": 0}))  # Exclude MongoDB's _id
    }

    return jsonify(geojson_data)


@bp.route('/filterImages/<checkString>', methods=["GET"])
def filterImages(checkString):
    if "user" not in session:
        flash("Please log in to access this page.")
        return redirect(url_for("auth.login"))

    """Fetches image data from MongoDB and returns it directly as GeoJSON."""
    client = connect_to_mongodb()
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    # Turn passed string into list of classes
    classList = checkString.split(",")
    #logging.info(f"Classes selected: {classList}")

    # Directly return the entire collection as a GeoJSON FeatureCollection
    featureList = list(collection.find({"properties.predicted_class": {'$in': classList}}, {"_id": 0}))
    geojson_data = { "type": "FeatureCollection", "features": featureList }
    
    #logging.info(f"Completed feature list: {geojson_data}")

    return jsonify(geojson_data)


@bp.route("/getImage/<file_id>", methods=["GET"])
def get_image(file_id):
    
    """Retrieve and serve an image stored in MongoDB GridFS."""
    if "user" not in session:
             flash("Please log in to access this page.")
             return redirect(url_for("auth.login"))
    
    #file storage system for mongo
    client = connect_to_mongodb()  # Connect to MongoDB
    db = client[DATABASE_NAME]  # Get database instance
    fs = gridfs.GridFS(db)

    try:
        # Convert file_id from string to ObjectId
        file_object_id = ObjectId(file_id)

        # Retrieve the image from GridFS
        retrieved_file = fs.get(file_object_id)

        return send_file(BytesIO(retrieved_file.read()), mimetype="image/jpeg")

    except Exception as e:
        return jsonify({"error": f"Image not found: {str(e)}"}), 404


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

    #file storage system for mongo
    client = connect_to_mongodb()  # Connect to MongoDB
    db = client[DATABASE_NAME]  # Get database instance
    fs = gridfs.GridFS(db)

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


@bp.route('/images_table', methods=['GET', 'POST'])
def images_table():
    if "user" not in session:
        flash("Please log in to access this page.")
        return redirect(url_for("auth.login"))
    
    # Map the human-readable class names to database values
    class_mapping = {
        "Narrowleaf Cattail": "narrowleaf_cattail",
        "Native": "none",  # 'none' is stored in the database as 'Native'
        "Phragmites": "phragmites",
        "Purple Loosestrife": "purple_loosestrife"
    }

    # Get the selected classes from the URL query parameters
    selected_classes = request.args.getlist('class')  # List of selected classes from the checkboxes

    # Convert the selected class names to database field names
    db_classes = [class_mapping.get(class_name) for class_name in selected_classes if class_name in class_mapping]

    # Connect to MongoDB
    client = connect_to_mongodb()
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    # Build the query to filter by predicted class
    query = {}
    if db_classes:
        query['properties.predicted_class'] = {"$in": db_classes}

    # Find the filtered documents
    docs = collection.find(query, {"_id": 0})

    # Extract the data for rendering
    images = [{
        "filename": doc["properties"]["filename"],
        "file_id": doc["properties"]["file_id"], 
        "predicted_class": doc["properties"]["predicted_class"].replace("none", "Native"),
        "narrowleaf_prob": doc["properties"]["narrowleaf_cattail_prob"],
        "none_prob": doc["properties"]["none_prob"],
        "phragmites_prob": doc["properties"]["phragmites_prob"],
        "purple_prob": doc["properties"]["purple_loosestrife_prob"],
        "lat": doc["geometry"]["coordinates"][1],
        "lon": doc["geometry"]["coordinates"][0]
    } for doc in docs]

    return render_template("table.html", images=images, selected_classes=selected_classes)

@bp.route('/download_excel', methods=['GET'])
def download_excel():
    if "user" not in session:
        flash("Please log in.")
        return redirect(url_for("auth.login"))

    filename = fetch_and_save_excel()
    if filename is None:
        flash("Error generating file.")
        return redirect(url_for("main.images_table"))

    return send_file(filename, as_attachment=True)



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
