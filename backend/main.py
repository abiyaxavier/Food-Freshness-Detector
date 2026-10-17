from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
import io

app = FastAPI()

# Allow Angular to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ],
    allow_origin_regex=r"http://(?:192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}):4200",
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "Food Freshness Detector Backend is Running!",
        "status": "success"
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):

    # Check file type
    if file.content_type not in [
        "image/jpeg",
        "image/png",
        "image/webp"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Please upload a JPG, PNG or WEBP image."
        )

    # Read image with 10 MB limit
    contents = await file.read(10 * 1024 * 1024 + 1)

    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Image must be smaller than 10 MB."
        )

    # Open image
    try:
        image = Image.open(io.BytesIO(contents))
        image = image.convert("RGB")

    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=400,
            detail="Invalid image file."
        )

    # Resize image for MobileNetV2
    image = image.resize((224, 224))

    # Model is not connected yet
    return {
        "message": "Image received successfully!",
        "filename": file.filename,
        "image_size": list(image.size),
        "model_status": "Not connected yet"
    }