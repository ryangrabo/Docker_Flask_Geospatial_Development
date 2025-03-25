import os
import logging
import pymongo  # I use this for additional MongoDB functionality when needed
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, send_file, abort, Flask, Response, redirect, flash, session  # I use these Flask utilities for creating views, rendering templates, sending files, etc.
from pymongo import MongoClient  # I use this to connect to MongoDB databases

#setup logging
logging.basicConfig(level=logging.INFO)

# Use the Docker service name when running inside Docker
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

ALLOWED_EXTENSIONS = {"jpg", "jpeg"}

# @login_required
def connect_to_mongodb():

    """Connects to MongoDB and returns a client."""
    client = MongoClient(MONGO_URI)
    # Quick test to ensure we can ping the server
    client.admin.command("ping")
    logging.info("Connected successfully to MongoDB")
    return client


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_to_degrees(value, ref_tag):
    """
    Converts the GPS coordinates stored in the EXIF to degrees in float format.
    :param value: EXIF GPS coordinate value.
    :param ref_tag: EXIF GPS reference tag (e.g., 'N', 'S', 'E', 'W').
    :return: GPS coordinate in degrees (float) or None if conversion fails.
    """
    try:
        d = value.values[0].num / value.values[0].den
        m = value.values[1].num / value.values[1].den
        s = value.values[2].num / value.values[2].den
        result = d + (m / 60.0) + (s / 3600.0)
        if ref_tag and ref_tag.values[0] in ['S', 'W']:
            result = -result
        return result
    except Exception as e:
        logging.error(f"Error converting GPS value: {e}")
        return None

