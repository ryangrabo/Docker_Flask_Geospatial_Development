import logging
import pandas as pd
from pymongo import MongoClient
from gridfs import GridFS
from io import BytesIO
import xlsxwriter
from PIL import Image
from bson import ObjectId
from app.utils import connect_to_mongodb
# MongoDB Connection
# MONGO_URI = "mongodb://localhost:27017/"  # Change if needed
DATABASE_NAME = "InvasiveSpeciesDB"
COLLECTION_NAME = "ImageProcessingResults"

#client = MongoClient(MONGO_URI)
client = connect_to_mongodb()
db = client[DATABASE_NAME]
col = db[COLLECTION_NAME]
fs = GridFS(db)  # GridFS for image retrieval

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def clean_record(record):
    """Flattens 'properties' and removes unnecessary fields."""
    keys_to_remove = ["type", "geometry", "geometry.coordinates"]

    flat_record = {k: v for k, v in record.items() if k not in keys_to_remove}

    # Extract 'properties' attributes and merge into top level
    if "properties" in flat_record:
        properties_data = flat_record.pop("properties")
        if isinstance(properties_data, dict):
            flat_record.update(properties_data)

    return flat_record


def fetch_images(file_ids):
    """Retrieve images from MongoDB GridFS and store them in-memory."""
    images = {}
    for file_id in file_ids:
        try:
            file_object_id = ObjectId(file_id)
            retrieved_file = fs.get(file_object_id)
            images[file_id] = Image.open(BytesIO(retrieved_file.read()))
        except Exception as e:
            logging.error(f"Error retrieving image {file_id}: {e}")
            images[file_id] = None  # Store None if image retrieval fails
    return images

def fetch_nothing(file_ids):
    """get nothing."""
    images = {}
    for file_id in file_ids:
        try:
            images[file_id] = None
        except Exception as e:
            logging.error(f"Error retrieving image {file_id}: {e}")
            images[file_id] = None  # Store None if image retrieval fails
    return images


def fetch_and_save_excel(output_filename="MongoDB_Data_Test.xlsx"):
    """Fetches data from MongoDB, cleans it, retrieves images, and saves it as an Excel file."""
    try:
        # Fetch data
        data_list = list(col.find())

        if not data_list:
            logging.info("No data found in MongoDB.")
            return None

        logging.info(f"Retrieved {len(data_list)} records from MongoDB.")

        # Process records
        cleaned_data = [clean_record(record) for record in data_list]

        # Convert to DataFrame
        df = pd.DataFrame(cleaned_data)

        # Extract file_ids to fetch images
        #CHANGE IF YOU WANT IMAGES
        file_ids = df["file_id"].dropna().unique().tolist()
        #images = fetch_images(file_ids)
        images = fetch_nothing(file_ids)

        # Remove MongoDB '_id' column if present
        if "_id" in df.columns:
            df.drop(columns=["_id"], inplace=True)

        # Save to Excel with images
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet("Data")

        # Write DataFrame to Excel
        for col_num, column in enumerate(df.columns):
            worksheet.write(0, col_num, column)  # Write column headers
            for row_num, value in enumerate(df[column], start=1):
                worksheet.write(row_num, col_num, str(value))  # Write data values

        # Insert images at the end
        img_col = len(df.columns)  # Next column after last data column
        worksheet.write(0, img_col, "Image")  # Header for image column

        for row_num, file_id in enumerate(df["file_id"], start=1):
            if file_id in images and images[file_id] is not None:
                img_io = BytesIO()
                images[file_id].thumbnail((100, 100))  # Resize to fit in cell
                images[file_id].save(img_io, format="PNG")
                worksheet.insert_image(row_num, img_col, f"{file_id}.png", {"image_data": img_io})

        workbook.close()
        output.seek(0)  # Reset pointer

        # Save locally (optional)
        with open(output_filename, "wb") as f:
            f.write(output.getbuffer())

        logging.info(f"Excel file saved as {output_filename}")
        return output_filename

    except Exception as e:
        logging.error(f"Error exporting to Excel: {e}")
        return None


if __name__ == "__main__":
    fetch_and_save_excel()
