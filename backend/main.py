from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps, UnidentifiedImageError

import tensorflow as tf
import numpy as np
import json
import io

from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200"
    ],
    allow_origin_regex=(
        r"http://(?:192\.168\.\d{1,3}\.\d{1,3}|"
        r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|"
        r"10\.\d{1,3}\.\d{1,3}):4200"
    ),
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

# Load trained AI model
BASE_DIR = Path(__file__).resolve().parent

model = tf.keras.models.load_model(
    BASE_DIR / "model.keras",
    compile=False
)

with open(BASE_DIR / "class_names.json", "r") as f:
    class_names = json.load(f)

print("AI model loaded successfully!")
print("Classes:", class_names)


@app.get("/")
def home():
    return {
        "message": "Food Freshness Detector Backend is Running!",
        "model_status": "Loaded"
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):

    if file.content_type not in [
        "image/jpeg",
        "image/png",
        "image/webp"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Please upload a JPG, PNG, or WEBP image."
        )

    contents = await file.read(10 * 1024 * 1024 + 1)

    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Image must be smaller than 10 MB."
        )

    try:
        image = Image.open(io.BytesIO(contents))
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGB")
        image = image.resize((224, 224))

    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=400,
            detail="Invalid image file."
        )

    # Convert image into model input
    image_array = np.array(image, dtype=np.float32)
    image_array = np.expand_dims(image_array, axis=0)

    # AI prediction
    result = model.predict(image_array, verbose=0)

    # The trained model uses binary sigmoid output
    probability = float(result[0][0])

    if probability >= 0.5:
        prediction = class_names[1]
        confidence = probability * 100
    else:
        prediction = class_names[0]
        confidence = (1 - probability) * 100

    return {
        "prediction": prediction,
        "confidence": f"{confidence:.2f}%"

    }

