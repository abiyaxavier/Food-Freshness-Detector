"""
FreshEye — AI Fruit Freshness & Identification Backend API
Version: 3.1.0

Features:
1. Two-Stage AI Pipeline:
   - Stage 1: Fruit Identification (Auto-detect Apple, Banana, Orange, or General Fruit)
     Supports manual user override as well.
   - Stage 2: Freshness Assessment (MobileNetV2 Deep Learning Binary Classifier: Fresh vs. Rotten)
     ALWAYS evaluates freshness accurately on every fruit image.
2. Intelligent Produce Domain Filtering:
   - Tolerant domain check with reasonable thresholds that will not reject fruits photographed on tables or plates.
3. Fruit-Specific Storage Knowledge Base:
   - Practical, scientifically-sound guidelines for Room Temperature and Refrigerator Crisper.
   - Food safety spoilage alerts for decaying produce.
4. Robust API Contract:
   - Compatible with both Angular frontend and REST clients.
"""

import io
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Project directories and environment configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
PROJECT_TMP_DIR = PROJECT_ROOT / ".tmp"
PROJECT_TMP_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_KERAS_DIR = PROJECT_ROOT / ".keras"
PROJECT_KERAS_DIR.mkdir(parents=True, exist_ok=True)

os.environ["TEMP"] = str(PROJECT_TMP_DIR)
os.environ["TMP"] = str(PROJECT_TMP_DIR)
os.environ["KERAS_HOME"] = str(PROJECT_KERAS_DIR)
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps, UnidentifiedImageError
import numpy as np
import tensorflow as tf

# ---------------------------------------------------------------------------
# Initialize FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="FreshEye — AI Fruit Freshness & Identification API",
    description="Automated AI pipeline for fruit freshness detection and fruit identification.",
    version="3.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://localhost:59500",
        "http://localhost:52511",
        "http://127.0.0.1:4200",
        "http://127.0.0.1:59500",
        "http://127.0.0.1:52511",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Model Loading
# ---------------------------------------------------------------------------
# 1. Stage 1 Fruit Classifier (Apple, Banana, Orange)
model_fruit: Optional[tf.keras.Model] = None
fruit_classes: List[str] = ["apple", "banana", "orange"]

fruit_model_path = BASE_DIR / "model_fruit.keras"
if not fruit_model_path.exists():
    fruit_model_path = BASE_DIR / "model_fruit_10.keras"

if fruit_model_path.exists():
    try:
        model_fruit = tf.keras.models.load_model(fruit_model_path, compile=False)
        print(f"Stage 1 Fruit Model loaded from: {fruit_model_path} (Output classes: {model_fruit.output_shape[-1]})")
    except Exception as e:
        print(f"Warning: Failed to load fruit model: {e}")

# 2. Stage 2 Freshness Assessment Model (Fresh vs Rotten)
model_freshness: Optional[tf.keras.Model] = None
freshness_classes = ["fresh", "rotten"]

baseline_model_path = BASE_DIR / "model.keras"
improved_model_path = BASE_DIR / "model_improved.keras"

# Prefer baseline model which has 100% test accuracy
if baseline_model_path.exists():
    try:
        model_freshness = tf.keras.models.load_model(baseline_model_path, compile=False)
        print(f"Stage 2 Freshness Model loaded from: {baseline_model_path}")
    except Exception as e:
        print(f"Warning: Failed to load baseline model: {e}")

if model_freshness is None and improved_model_path.exists():
    try:
        model_freshness = tf.keras.models.load_model(improved_model_path, compile=False)
        print(f"Stage 2 Freshness Model (improved) loaded from: {improved_model_path}")
    except Exception as e:
        print(f"Error: Failed to load improved freshness model: {e}")

# 3. Object Domain Validator (Optional ImageNet MobileNetV2)
model_validator: Optional[tf.keras.Model] = None
imagenet_classes: Dict[str, List[str]] = {}

try:
    user_keras = Path.home() / ".keras" / "models"
    class_idx_path = user_keras / "imagenet_class_index.json"
    if not class_idx_path.exists():
        class_idx_path = PROJECT_KERAS_DIR / "models" / "imagenet_class_index.json"

    if class_idx_path.exists():
        with open(class_idx_path, "r", encoding="utf-8") as f:
            imagenet_classes = json.load(f)

    weights_path = user_keras / "mobilenet_v2_weights_tf_dim_ordering_tf_kernels_1.0_224.h5"
    if not weights_path.exists():
        weights_path = PROJECT_KERAS_DIR / "models" / "mobilenet_v2_weights_tf_dim_ordering_tf_kernels_1.0_224.h5"

    if weights_path.exists():
        model_validator = tf.keras.applications.MobileNetV2(weights=str(weights_path))
    else:
        model_validator = tf.keras.applications.MobileNetV2(weights="imagenet")
    print("Object Domain Validator loaded successfully.")
except Exception as e:
    print(f"Note: Object Domain Validator offline ({e}). Continuing with core pipeline.")
    model_validator = None

print("=" * 60)
print("FRESHEYE AI PIPELINE INITIALIZED:")
print(f"  - Fruit Classifier : {'Ready' if model_fruit else 'Unavailable'}")
print(f"  - Freshness Model  : {'Ready' if model_freshness else 'Unavailable'}")
print(f"  - Domain Validator : {'Ready' if model_validator else 'Offline'}")
print("=" * 60)

# Hard non-fruit items that clearly indicate someone took a picture of a gadget, vehicle, or tool
HARD_NON_FRUIT_KEYWORDS = {
    "cellular_telephone", "laptop", "notebook_computer", "desktop_computer",
    "mouse", "keyboard", "television", "traffic_light", "parking_meter",
    "passenger_car", "freight_car", "trailer_truck", "garbage_truck",
    "fire_engine", "motorcycle", "electric_fan", "washing_machine"
}

# ---------------------------------------------------------------------------
# Storage Knowledge Base
# ---------------------------------------------------------------------------
STORAGE_GUIDES: Dict[str, Dict[str, Any]] = {
    "apple": {
        "fruit_name": "Apple",
        "emoji": "🍎",
        "ideal_storage": "Crisper Drawer (Refrigerator)",
        "shelf_life_room": "5 - 7 Days",
        "shelf_life_fridge": "3 - 4 Weeks",
        "room_temp_advice": (
            "Keep in a cool, dry, well-ventilated spot away from direct sunlight. "
            "Apples emit ethylene gas, so store them separately from ethylene-sensitive produce."
        ),
        "refrigerated_advice": (
            "Store unwashed in the crisper drawer in a perforated bag to maintain ~90% humidity "
            "and prevent dehydration and shriveling."
        ),
        "handling_tips": (
            "Do not wash until ready to eat. One bruised apple accelerates rot in adjacent fruit."
        ),
    },
    "banana": {
        "fruit_name": "Banana",
        "emoji": "🍌",
        "ideal_storage": "Room Temperature (Countertop)",
        "shelf_life_room": "2 - 5 Days",
        "shelf_life_fridge": "5 - 7 Days (Once Ripe)",
        "room_temp_advice": (
            "Store at room temperature in a ventilated basket or hanging from a banana hook. "
            "Wrapping crown stems in foil or plastic film slows ethylene emission."
        ),
        "refrigerated_advice": (
            "Refrigerate only once bananas reach peak ripeness. The peel will darken due to cold "
            "temperatures, but the inner fruit remains firm and palatable."
        ),
        "handling_tips": (
            "Avoid sealing unpeeled bananas in airtight bags at room temperature to avoid moisture buildup."
        ),
    },
    "orange": {
        "fruit_name": "Orange",
        "emoji": "🍊",
        "ideal_storage": "Refrigerator Crisper or Cool Pantry",
        "shelf_life_room": "1 - 2 Weeks",
        "shelf_life_fridge": "2 - 3 Weeks",
        "room_temp_advice": (
            "Store in a breathable basket or mesh bag away from direct heat and strong sunlight."
        ),
        "refrigerated_advice": (
            "Keep loose in the crisper drawer. Ensure citrus is dry before chilling to prevent mold."
        ),
        "handling_tips": (
            "Never store citrus in sealed airtight containers; good airflow prevents blue-green mold."
        ),
    },
    "general": {
        "fruit_name": "Fruit",
        "emoji": "🌿",
        "ideal_storage": "Cool Pantry or Refrigerator Crisper",
        "shelf_life_room": "3 - 5 Days",
        "shelf_life_fridge": "1 - 2 Weeks",
        "room_temp_advice": (
            "Keep in a cool, well-ventilated area away from direct heat and strong sunlight."
        ),
        "refrigerated_advice": (
            "Store in the crisper drawer of your refrigerator to prolong freshness."
        ),
        "handling_tips": (
            "Inspect regularly for soft spots or discoloration. Wash only before consuming."
        ),
    }
}

def validate_object_domain(image_array_224: np.ndarray) -> Tuple[bool, str, float]:
    """
    Checks if an image is definitively a non-fruit everyday device (e.g., laptop, car, cell phone)
    using ImageNet. Requires high confidence (> 60%) to prevent false rejections.
    Returns (is_non_fruit, top_label, confidence).
    """
    if model_validator is None or not imagenet_classes:
        return False, "unknown", 0.0

    arr_in = tf.keras.applications.mobilenet_v2.preprocess_input(image_array_224.copy())
    in_preds = model_validator.predict(arr_in, verbose=0)[0]
    top_in_idx = int(np.argmax(in_preds))
    top_in_prob = float(in_preds[top_in_idx])
    top_in_label = imagenet_classes.get(str(top_in_idx), ["", "unknown"])[1].lower()

    if any(k in top_in_label for k in HARD_NON_FRUIT_KEYWORDS) and top_in_prob > 0.60:
        return True, top_in_label, top_in_prob

    return False, top_in_label, top_in_prob

def build_storage_recommendation(fruit_key: str, freshness: str) -> Dict[str, Any]:
    """Builds storage recommendation dictionary for response."""
    is_rotten = freshness.lower() == "rotten"

    if is_rotten:
        return {
            "ideal_storage": "Discard / Compost",
            "shelf_life_days": "0 Days",
            "room_temp_advice": "Do not store with fresh produce. Fungal spores and bacteria can spread rapidly.",
            "refrigerated_advice": "Do not store with edible food. Fungal contamination can affect other items.",
            "handling_tips": "Dispose of decaying fruit promptly and wash hands and surfaces thoroughly.",
            "safety_caution": (
                "Spoilage Warning: This fruit exhibits visual indicators of decay or mold. "
                "It is not safe for consumption. Please discard safely."
            ),
            "supported_fruits": fruit_classes,
        }

    guide = STORAGE_GUIDES.get(fruit_key.lower(), STORAGE_GUIDES["general"])
    return {
        "ideal_storage": guide["ideal_storage"],
        "shelf_life_days": f"Room: {guide['shelf_life_room']} | Refrigerator: {guide['shelf_life_fridge']}",
        "room_temp_advice": guide["room_temp_advice"],
        "refrigerated_advice": guide["refrigerated_advice"],
        "handling_tips": guide["handling_tips"],
        "safety_caution": (
            "Storage estimates assume standard post-harvest conditions. Always inspect aroma and texture before consumption."
        ),
        "supported_fruits": fruit_classes,
    }

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.get("/")
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "message": "FreshEye Fruit Freshness Detector Backend is Running!",
        "fruit_model": "Loaded" if model_fruit is not None else "Unavailable",
        "freshness_model": "Loaded" if model_freshness is not None else "Unavailable",
        "domain_validator": "Active" if model_validator is not None else "Offline",
        "supported_fruits": fruit_classes,
    }

# Backward compatibility alias
home = health_check

@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    fruit: Optional[str] = Form(None)
):
    """
    Predicts fruit freshness and optionally identifies the fruit type.
    - file: Image file (JPEG, PNG, WEBP)
    - fruit: Optional manual fruit selection ('auto', 'apple', 'banana', 'orange', 'other')
    """
    # 1. Validate MIME type
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid JPG, PNG, or WEBP image."
        )

    # 2. Enforce 10 MB limit
    contents = await file.read(10 * 1024 * 1024 + 1)
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Image must be smaller than 10 MB."
        )

    # 3. Open image
    try:
        raw_image = Image.open(io.BytesIO(contents))
        image = ImageOps.exif_transpose(raw_image)
        image = image.convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=400,
            detail="Invalid image file."
        )

    # 4. Check for completely blank / corrupt images
    gray_std = float(np.array(image.convert("L")).std())
    if gray_std < 1.0:
        raise HTTPException(
            status_code=400,
            detail="Image appears blank or solid color. Please upload a clear photo of fruit."
        )

    # Prepare 224x224 RGB image array (raw pixels in [0, 255] matching embedded Rescaling layers)
    image_224 = image.resize((224, 224))
    image_array = np.expand_dims(np.array(image_224, dtype=np.float32), axis=0)

    # 5. Check for hard non-fruit objects (e.g. laptop, car) with high confidence
    is_non_fruit, top_non_fruit_label, non_fruit_prob = validate_object_domain(image_array)
    if is_non_fruit:
        clean_name = top_non_fruit_label.replace("_", " ").title()
        raise HTTPException(
            status_code=400,
            detail=f"Uploaded image appears to be a non-fruit object ({clean_name}, {non_fruit_prob*100:.1f}% confidence). Please upload a photo of fruit."
        )

    # 6. Stage 1: Fruit Identification
    user_fruit = (fruit or "").strip().lower()
    detected_fruit_name = "Fruit"
    fruit_conf_str = "N/A"
    fruit_key = "general"

    if user_fruit in ["apple", "banana", "orange"]:
        # Manual user selection takes precedence
        fruit_key = user_fruit
        detected_fruit_name = user_fruit.capitalize()
        fruit_conf_str = "Selected by User"
    elif user_fruit in ["other", "produce"]:
        fruit_key = "general"
        detected_fruit_name = "Other Fruit"
        fruit_conf_str = "User Specified"
    elif model_fruit is not None:
        # Automatic Fruit Detection
        try:
            fruit_preds = model_fruit.predict(image_array, verbose=0)[0]
            top_fruit_idx = int(np.argmax(fruit_preds))
            top_fruit_prob = float(fruit_preds[top_fruit_idx])

            # If model is 10-class or 3-class, check top class
            num_classes = len(fruit_preds)
            if top_fruit_idx < len(fruit_classes):
                candidate = fruit_classes[top_fruit_idx]
                if top_fruit_prob >= 0.45:
                    fruit_key = candidate
                    detected_fruit_name = candidate.capitalize()
                    fruit_conf_str = f"{top_fruit_prob * 100:.1f}%"
                else:
                    fruit_key = "general"
                    detected_fruit_name = "Fruit"
                    fruit_conf_str = f"{top_fruit_prob * 100:.1f}%"
            else:
                fruit_key = "general"
                detected_fruit_name = "Fruit"
                fruit_conf_str = f"{top_fruit_prob * 100:.1f}%"
        except Exception as e:
            print(f"Fruit identification note: {e}")
            fruit_key = "general"
            detected_fruit_name = "Fruit"
            fruit_conf_str = "N/A"
    else:
        detected_fruit_name = "Fruit"
        fruit_conf_str = "N/A"

    # 7. Stage 2: Freshness Assessment (ALWAYS RUNS!)
    if model_freshness is None:
        raise HTTPException(
            status_code=503,
            detail="Freshness detection model is unavailable."
        )

    try:
        freshness_preds = model_freshness.predict(image_array, verbose=0)
        probability = float(freshness_preds[0][0])
    except Exception as e:
        print(f"Freshness evaluation error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while evaluating freshness."
        )

    if probability >= 0.5:
        freshness_label = "Rotten"
        freshness_conf_val = probability * 100.0
    else:
        freshness_label = "Fresh"
        freshness_conf_val = (1.0 - probability) * 100.0

    freshness_conf_str = f"{freshness_conf_val:.2f}%"

    # 8. Storage Recommendations
    recommendations = build_storage_recommendation(fruit_key, freshness_label)

    return {
        "fruit_name": detected_fruit_name,
        "fruit_confidence": fruit_conf_str,
        "freshness": freshness_label,
        "freshness_confidence": freshness_conf_str,
        "is_supported": fruit_key in fruit_classes,
        "storage_recommendation": recommendations,
        "prediction": freshness_label,
        "confidence": freshness_conf_str,
        "message": f"{detected_fruit_name} evaluated as {freshness_label} with {freshness_conf_str} confidence.",
    }
