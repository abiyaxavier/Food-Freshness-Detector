"""
FreshEye — AI Fruit Freshness & Identification Backend API
Version: 3.0.0

Features:
1. Multi-Stage AI Pipeline:
   - Image Quality & Clarity Analysis (Laplacian Sharpness Check)
   - Pretrained ImageNet Object Validation (Distinguishes non-fruit objects like phones, laptops, bottles, books)
   - Stage 1 Fruit Identification:
     - Primary: 10-Class Classifier (Apple, Banana, Orange, Mango, Grapes, Strawberry, Pineapple, Watermelon, Pear, Kiwi)
     - Fallback: Working 3-Class Classifier (Apple, Banana, Orange)
   - Stage 2 Freshness Assessment:
     - Improved Deep Convolutional Binary Freshness Model (Fresh vs. Rotten)
2. Fruit-Specific Storage Knowledge Base:
   - Comprehensive practical advice for all 10 supported fruits
   - Refrigerator vs. Room temperature guidelines
   - Spoilage warnings and food safety caveats
3. Backward Compatibility:
   - Full support for existing Angular frontend and legacy clients
   - Consistent JSON response contract
"""

import io
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Project directories and environment configuration
# (Must be configured BEFORE importing TensorFlow / Keras)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
PROJECT_TMP_DIR = PROJECT_ROOT / ".tmp"
PROJECT_TMP_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_KERAS_DIR = PROJECT_ROOT / ".keras"
PROJECT_KERAS_DIR.mkdir(parents=True, exist_ok=True)

# Protect system drive C: by pointing temp and cache directories to project drive D:
os.environ["TEMP"] = str(PROJECT_TMP_DIR)
os.environ["TMP"] = str(PROJECT_TMP_DIR)
os.environ["KERAS_HOME"] = str(PROJECT_KERAS_DIR)
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps, UnidentifiedImageError
import numpy as np
import tensorflow as tf

# ---------------------------------------------------------------------------
# Initialize FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="FreshEye — AI Fruit Freshness & Identification API",
    description="Automated multi-stage AI pipeline for fruit identification, object validation, and freshness detection.",
    version="3.0.0"
)

# CORS configuration preserving existing origins
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
# Model Loading (Loaded ONCE at startup with graceful fallbacks)
# ---------------------------------------------------------------------------

# 1. Pretrained Object Domain Validator (ImageNet MobileNetV2)
model_validator: Optional[tf.keras.Model] = None
imagenet_classes: Dict[str, List[str]] = {}

try:
    class_idx_path = PROJECT_KERAS_DIR / "models" / "imagenet_class_index.json"
    if class_idx_path.exists():
        with open(class_idx_path, "r", encoding="utf-8") as f:
            imagenet_classes = json.load(f)

    weights_path = PROJECT_KERAS_DIR / "models" / "mobilenet_v2_weights_tf_dim_ordering_tf_kernels_1.0_224.h5"
    if weights_path.exists():
        model_validator = tf.keras.applications.MobileNetV2(weights=str(weights_path))
    else:
        model_validator = tf.keras.applications.MobileNetV2(weights="imagenet")
    print("Object Domain Validator (ImageNet MobileNetV2) loaded successfully.")
except Exception as e:
    print(f"Warning: Object Domain Validator could not be initialized: {e}")
    model_validator = None

# Non-fruit keyword indicators
NON_FRUIT_KEYWORDS = {
    "phone", "cellular", "telephone", "ipod", "laptop", "notebook", "computer",
    "screen", "monitor", "television", "radio", "loudspeaker", "microphone",
    "bottle", "nipple", "saltshaker", "pitcher", "coffeepot", "teapot", "jug",
    "book", "book_jacket", "binder", "comic_book", "envelope", "pen", "pencil",
    "panpipe", "flute", "guitar", "piano", "violin", "accordion", "organ",
    "desk", "chair", "table", "couch", "sofa", "bed", "wardrobe", "lamp",
    "car", "automobile", "truck", "bicycle", "motorcycle", "bus", "train",
    "hammer", "screwdriver", "wrench", "drill", "pliers", "hatchet",
    "shoe", "sneaker", "boot", "sandal", "sock", "suit", "jersey", "sunglasses",
    "wallet", "backpack", "purse", "handbag", "umbrella", "watch", "clock"
}

# Explicitly unsupported produce that does not overlap with supported 10 fruits
UNSUPPORTED_PRODUCE_KEYWORDS = {
    "lemon", "fig", "jackfruit", "pomegranate",
    "cucumber", "zucchini", "broccoli", "cauliflower",
    "head_cabbage", "corn"
}

# 2. Stage 1: Fruit Type Classification Model (10-Fruit preferred, 3-Fruit fallback)
model_fruit: Optional[tf.keras.Model] = None
fruit_classes: List[str] = ["apple", "banana", "orange"]
active_fruit_version = "unavailable"

fruit_10_model_path = BASE_DIR / "model_fruit_10.keras"
fruit_10_classes_path = BASE_DIR / "fruit_classes_10.json"
fruit_3_model_path = BASE_DIR / "model_fruit.keras"
fruit_3_classes_path = BASE_DIR / "fruit_classes.json"

# Attempt to load 10-fruit model
if fruit_10_model_path.exists() and fruit_10_classes_path.exists():
    try:
        with open(fruit_10_classes_path, "r", encoding="utf-8") as f:
            classes_10 = json.load(f)
        loaded_model_10 = tf.keras.models.load_model(fruit_10_model_path, compile=False)
        print("Fruit model input shape:", loaded_model_10.input_shape)
        print("Fruit model output shape:", loaded_model_10.output_shape)
        print("Fruit class order:", classes_10)
        output_dim = loaded_model_10.output_shape[-1]
        if output_dim == len(classes_10) and len(classes_10) == 10:
            model_fruit = loaded_model_10
            fruit_classes = classes_10
            active_fruit_version = "10-fruit"
            print(f"Active Fruit Classifier: 10-Fruit Model loaded successfully ({fruit_classes})")
        else:
            print(f"Warning: 10-fruit model output dimension mismatch: {output_dim} vs {len(classes_10)}")
    except Exception as e:
        print(f"Warning: Failed to load 10-fruit model: {e}")

# Fallback to existing 3-fruit classifier if 10-fruit model is unavailable
if model_fruit is None and fruit_3_model_path.exists() and fruit_3_classes_path.exists():
    try:
        with open(fruit_3_classes_path, "r", encoding="utf-8") as f:
            classes_3 = json.load(f)
        loaded_model_3 = tf.keras.models.load_model(fruit_3_model_path, compile=False)
        output_dim = loaded_model_3.output_shape[-1]
        if output_dim == len(classes_3):
            model_fruit = loaded_model_3
            fruit_classes = classes_3
            active_fruit_version = "3-fruit-fallback"
            print(f"Active Fruit Classifier: 3-Fruit Fallback loaded successfully ({fruit_classes})")
    except Exception as e:
        print(f"Warning: Failed to load fallback 3-fruit model: {e}")

# 3. Stage 2: Freshness Assessment Model
model_freshness: Optional[tf.keras.Model] = None
freshness_classes = ["fresh", "rotten"]

improved_model_path = BASE_DIR / "model_improved.keras"
baseline_model_path = BASE_DIR / "model.keras"
improved_classes_path = BASE_DIR / "class_names_improved.json"
baseline_classes_path = BASE_DIR / "class_names.json"

if improved_classes_path.exists():
    with open(improved_classes_path, "r", encoding="utf-8") as f:
        freshness_classes = json.load(f)
elif baseline_classes_path.exists():
    with open(baseline_classes_path, "r", encoding="utf-8") as f:
        freshness_classes = json.load(f)

if improved_model_path.exists():
    try:
        model_freshness = tf.keras.models.load_model(improved_model_path, compile=False)
        print(f"Stage 2 Freshness Model (improved) loaded from: {improved_model_path}")
    except Exception as e:
        print(f"Warning: Failed to load improved freshness model: {e}")

if model_freshness is None and baseline_model_path.exists():
    try:
        model_freshness = tf.keras.models.load_model(baseline_model_path, compile=False)
        print(f"Stage 2 Freshness Model (baseline fallback) loaded from: {baseline_model_path}")
    except Exception as e:
        print(f"Error: Failed to load baseline freshness model: {e}")

print("=" * 60)
print("FRESHEYE AI PIPELINE INITIALIZED:")
print(f"  - Object Validator : {'Ready' if model_validator else 'Offline'}")
print(f"  - Fruit Classifier : {active_fruit_version.upper()} ({len(fruit_classes)} classes)")
print(f"  - Freshness Model  : {'Ready' if model_freshness else 'Unavailable'}")
print("=" * 60)

# ---------------------------------------------------------------------------
# Storage Knowledge Base for 10 Supported Fruits
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
    "mango": {
        "fruit_name": "Mango",
        "emoji": "🥭",
        "ideal_storage": "Countertop until ripe, then Refrigerator",
        "shelf_life_room": "3 - 5 Days (Ripening)",
        "shelf_life_fridge": "5 - 7 Days (Ripe)",
        "room_temp_advice": (
            "Keep firm, unripe mangoes at room temperature until they yield slightly to gentle pressure and emit a sweet aroma."
        ),
        "refrigerated_advice": (
            "Once fully ripe, move mangoes into the refrigerator to halt softening and prolong sweetness."
        ),
        "handling_tips": (
            "Do not refrigerate hard, unripened mangoes as temperatures below 12°C impair normal ripening."
        ),
    },
    "grapes": {
        "fruit_name": "Grapes",
        "emoji": "🍇",
        "ideal_storage": "Refrigerator Crisper (High Humidity)",
        "shelf_life_room": "1 - 2 Days",
        "shelf_life_fridge": "1 - 2 Weeks",
        "room_temp_advice": (
            "Grapes deteriorate rapidly at room temperature. Keep in a cool, ventilated area if consuming immediately."
        ),
        "refrigerated_advice": (
            "Store unwashed in their original ventilated clamshell or bag towards the back of the crisper drawer."
        ),
        "handling_tips": (
            "Wash only immediately prior to eating; surface moisture promotes rapid mold on stems and berries."
        ),
    },
    "strawberry": {
        "fruit_name": "Strawberry",
        "emoji": "🍓",
        "ideal_storage": "Refrigerator (Cold & Dry)",
        "shelf_life_room": "1 Day",
        "shelf_life_fridge": "4 - 7 Days",
        "room_temp_advice": (
            "Strawberries are highly perishable at room temperature. Keep out of direct sun and consume promptly."
        ),
        "refrigerated_advice": (
            "Store unwashed in a paper towel-lined container with a loosely fitted lid in the main refrigerator compartment."
        ),
        "handling_tips": (
            "Never wash or hull strawberries prior to storage; inspect container and remove any soft berry immediately."
        ),
    },
    "pineapple": {
        "fruit_name": "Pineapple",
        "emoji": "🍍",
        "ideal_storage": "Countertop or Refrigerator",
        "shelf_life_room": "2 - 3 Days",
        "shelf_life_fridge": "3 - 5 Days",
        "room_temp_advice": (
            "Store whole pineapple upright at cool room temperature away from heat sources."
        ),
        "refrigerated_advice": (
            "Whole pineapples can be placed in a loose plastic bag in the refrigerator to extend freshness."
        ),
        "handling_tips": (
            "Pineapples do not ripen further post-harvest; consume when sweet fragrance is noticeable at the stem base."
        ),
    },
    "watermelon": {
        "fruit_name": "Watermelon",
        "emoji": "🍉",
        "ideal_storage": "Cool Room Temp (Whole) / Refrigerator (Cut)",
        "shelf_life_room": "7 - 10 Days",
        "shelf_life_fridge": "2 - 3 Weeks (Whole) / 3 - 4 Days (Cut)",
        "room_temp_advice": (
            "Keep whole uncut watermelon at moderate room temperature to preserve maximum flavor and antioxidants."
        ),
        "refrigerated_advice": (
            "Once cut, wrap tightly in plastic film or store in an airtight container and refrigerate promptly."
        ),
        "handling_tips": (
            "Inspect the rind for soft spots, dents, or watery discoloration indicating interior decomposition."
        ),
    },
    "pear": {
        "fruit_name": "Pear",
        "emoji": "🍐",
        "ideal_storage": "Countertop until ripe, then Refrigerator",
        "shelf_life_room": "3 - 6 Days (Ripening)",
        "shelf_life_fridge": "1 - 2 Weeks (Ripe)",
        "room_temp_advice": (
            "Pears ripen from the inside out. Leave at room temperature until the neck flesh yields gently to light thumb pressure."
        ),
        "refrigerated_advice": (
            "Transfer ripe pears to the refrigerator crisper to keep them firm and crisp for up to two weeks."
        ),
        "handling_tips": (
            "Handle gently to prevent surface bruising; do not store directly adjacent to strong odors."
        ),
    },
    "kiwi": {
        "fruit_name": "Kiwi",
        "emoji": "🥝",
        "ideal_storage": "Room Temp until ripe, then Refrigerator",
        "shelf_life_room": "3 - 5 Days",
        "shelf_life_fridge": "2 - 3 Weeks",
        "room_temp_advice": (
            "Keep firm kiwis at room temperature. To speed ripening, place inside a paper bag with an apple or banana."
        ),
        "refrigerated_advice": (
            "Once kiwi yields slightly to gentle pressure, refrigerate in a plastic bag to lock in moisture."
        ),
        "handling_tips": (
            "Inspect skin for shriveling or soft sunken areas; keep away from high-ethylene emitters once ripe."
        ),
    },
}

def check_image_sharpness(img_pil: Image.Image) -> float:
    """Computes Laplacian variance to assess image focus and sharpness."""
    gray = np.array(img_pil.convert("L"), dtype=np.float32)
    lap = -4.0 * gray[1:-1, 1:-1] + gray[:-2, 1:-1] + gray[2:, 1:-1] + gray[1:-1, :-2] + gray[1:-1, 2:]
    return float(lap.var())

def validate_object_domain(image_array_224: np.ndarray) -> Tuple[str, str, float]:
    """
    Evaluates whether the uploaded image contains an everyday non-fruit object
    or unsupported produce using the pretrained ImageNet MobileNetV2 backbone.
    Returns (domain_status, top_label, confidence).
    domain_status: 'fruit_candidate', 'non_fruit', 'unsupported_produce'
    """
    if model_validator is None:
        return "fruit_candidate", "unknown", 0.0

    arr_in = tf.keras.applications.mobilenet_v2.preprocess_input(image_array_224.copy())
    in_preds = model_validator.predict(arr_in, verbose=0)[0]
    top_in_idx = int(np.argmax(in_preds))
    top_in_prob = float(in_preds[top_in_idx])
    top_in_label = imagenet_classes.get(str(top_in_idx), ["", "unknown"])[1].lower()

    # 1. Check if top prediction is a non-fruit everyday object
    if any(k in top_in_label for k in NON_FRUIT_KEYWORDS) and top_in_prob > 0.08:
        return "non_fruit", top_in_label, top_in_prob

    # 2. Check if top prediction is explicitly unsupported produce
    if any(k in top_in_label for k in UNSUPPORTED_PRODUCE_KEYWORDS) and top_in_prob > 0.25:
        return "unsupported_produce", top_in_label, top_in_prob

    return "fruit_candidate", top_in_label, top_in_prob

def build_storage_recommendation(
    raw_fruit_name: Optional[str],
    freshness: str,
    is_supported: bool
) -> Dict[str, Any]:
    """Generates structured storage advice based on detected fruit and freshness status."""
    is_rotten = freshness.lower() == "rotten"

    if is_rotten:
        return {
            "ideal_storage": "Discard / Compost",
            "shelf_life_days": "0 Days",
            "room_temp_advice": "Do not store at room temperature. Spores will spread to adjacent produce.",
            "refrigerated_advice": "Do not store with edible food. Fungal contamination can affect other items.",
            "handling_tips": "Wash hands and sanitize produce contact surfaces thoroughly.",
            "safety_caution": (
                "⚠️ Spoilage Notice: This fruit exhibits visual indicators of decay or mold and is not safe for consumption. "
                "Discard promptly to avoid contaminating nearby foods."
            ),
            "is_supported": is_supported,
            "supported_fruits": fruit_classes,
        }

    fruit_key = (raw_fruit_name or "").lower()
    guide = STORAGE_GUIDES.get(fruit_key)

    if guide and is_supported:
        return {
            "ideal_storage": guide["ideal_storage"],
            "shelf_life_days": f"Room: {guide['shelf_life_room']} | Refrigerator: {guide['shelf_life_fridge']}",
            "room_temp_advice": guide["room_temp_advice"],
            "refrigerated_advice": guide["refrigerated_advice"],
            "handling_tips": guide["handling_tips"],
            "safety_caution": (
                "Note: Estimates assume standard post-harvest conditions. Always inspect aroma and texture before consumption."
            ),
            "is_supported": True,
            "supported_fruits": fruit_classes,
        }

    return {
        "ideal_storage": "Cool Pantry or Refrigerator Crisper",
        "shelf_life_days": "3 - 7 Days",
        "room_temp_advice": "Store in a cool, well-ventilated spot out of direct sunlight.",
        "refrigerated_advice": "Store in a breathable container in the crisper drawer.",
        "handling_tips": f"Supported fruits are: {', '.join(c.capitalize() for c in fruit_classes)}.",
        "safety_caution": "Fruit type could not be confidently identified among supported classes.",
        "is_supported": False,
        "supported_fruits": fruit_classes,
    }

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.get("/")
@app.get("/health")
def health_check():
    """Health check and model status endpoint."""
    return {
        "message": "FreshEye Fruit Freshness Detector Backend is Running!",
        "stage1_fruit_model": "Loaded" if model_fruit is not None else "Unavailable",
        "stage1_active_version": active_fruit_version,
        "stage2_freshness_model": "Loaded" if model_freshness is not None else "Unavailable",
        "object_validator": "Active" if model_validator is not None else "Offline",
        "supported_fruit_classes": fruit_classes,
        "freshness_classes": freshness_classes,
    }

# Backward compatibility alias
home = health_check

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Multi-stage AI prediction endpoint:
    1. Image validation & preprocessing
    2. Quality / Blur detection
    3. Object domain validation (Distinguishes non-fruit objects)
    4. Fruit type identification (10-fruit classifier or fallback)
    5. Freshness evaluation (Fresh vs. Rotten)
    6. Structured storage recommendations
    """
    # 1. Validate MIME type
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
            status_code=400,
            detail="Please upload a JPG, PNG, or WEBP image."
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

    # 4. Check Image Quality / Clarity
    sharpness = check_image_sharpness(image)
    gray_std = float(np.array(image.convert("L")).std())
    if sharpness < 20.0 or gray_std < 5.0:
        return {
            "fruit_name": "Unable to Identify",
            "fruit_confidence": "N/A",
            "freshness": None,
            "freshness_confidence": "N/A",
            "is_supported": False,
            "object_type": "unclear",
            "message": "Please upload a clearer image with the fruit visible.",
            "storage_recommendation": None,
            "prediction": "Unable to Identify",
            "confidence": "N/A",
        }

    # Prepare 224x224 RGB image array (raw pixels in [0, 255] matching models' embedded Rescaling layers)
    image_224 = image.resize((224, 224))
    image_array = np.expand_dims(np.array(image_224, dtype=np.float32), axis=0)

    # 5. Pre-validation: Object Domain Check (Detect Non-Fruit Objects)
    domain_status, top_label, in_prob = validate_object_domain(image_array)

    if domain_status == "non_fruit":
        return {
            "fruit_name": "Unidentified Object",
            "fruit_confidence": "N/A",
            "freshness": None,
            "freshness_confidence": "N/A",
            "is_supported": False,
            "object_type": "non_fruit",
            "message": "This image does not appear to contain a supported fruit. Please upload a clear image of a fruit.",
            "storage_recommendation": None,
            "prediction": "Unidentified Object",
            "confidence": "N/A",
        }

    # 6. Stage 1: Fruit Identification
    if model_fruit is None:
        raise HTTPException(
            status_code=503,
            detail="Fruit classification models are currently unavailable."
        )

    try:
        fruit_preds = model_fruit.predict(image_array, verbose=0)[0]
        top_fruit_idx = int(np.argmax(fruit_preds))
        top_fruit_prob = float(fruit_preds[top_fruit_idx])
    except Exception as e:
        print(f"Fruit classification error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while identifying the fruit."
        )

    # Confidence threshold: 55%
    CONFIDENCE_THRESHOLD = 0.55
    if top_fruit_prob < CONFIDENCE_THRESHOLD:
        if domain_status == "unsupported_produce":
            clean_produce = top_label.replace("_", " ").capitalize()
            return {
                "fruit_name": "Unidentified Fruit",
                "fruit_confidence": f"{in_prob * 100:.2f}%",
                "freshness": None,
                "freshness_confidence": "N/A",
                "is_supported": False,
                "object_type": "unsupported_fruit",
                "message": f"This fruit or produce ({clean_produce}) is not currently supported by FreshEye.",
                "storage_recommendation": None,
                "prediction": "Unidentified Fruit",
                "confidence": "N/A",
            }
        return {
            "fruit_name": "Unidentified Fruit",
            "fruit_confidence": f"{top_fruit_prob * 100:.2f}%",
            "freshness": None,
            "freshness_confidence": "N/A",
            "is_supported": False,
            "object_type": "unsupported_fruit",
            "message": "This fruit is not currently supported by FreshEye.",
            "storage_recommendation": None,
            "prediction": "Unidentified Fruit",
            "confidence": "N/A",
        }

    raw_fruit_class = fruit_classes[top_fruit_idx]
    detected_fruit_name = raw_fruit_class.capitalize()
    fruit_conf_str = f"{top_fruit_prob * 100:.2f}%"

    # 7. Stage 2: Freshness Assessment
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
        freshness_label = freshness_classes[1].capitalize()  # "Rotten"
        freshness_conf_val = probability * 100.0
    else:
        freshness_label = freshness_classes[0].capitalize()  # "Fresh"
        freshness_conf_val = (1.0 - probability) * 100.0

    freshness_conf_str = f"{freshness_conf_val:.2f}%"

    # 8. Storage Recommendations
    recommendations = build_storage_recommendation(
        raw_fruit_class,
        freshness_label,
        is_supported=True
    )

    return {
        "fruit_name": detected_fruit_name,
        "fruit_confidence": fruit_conf_str,
        "freshness": freshness_label,
        "freshness_confidence": freshness_conf_str,
        "is_supported": True,
        "object_type": "fruit",
        "message": f"{detected_fruit_name} identified successfully.",
        "storage_recommendation": recommendations,

        # Backward compatibility
        "prediction": freshness_label,
        "confidence": freshness_conf_str,
    }
