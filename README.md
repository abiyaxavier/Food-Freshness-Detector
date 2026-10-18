# 🍎 FreshEye – AI-Powered Food Freshness Detector

### Smart Fruit Freshness Detection Using Deep Learning

FreshEye is an AI-powered web application designed to identify the
freshness of fruits using image classification and deep learning.

The system allows users to upload or capture an image of a fruit and
predicts whether it is Fresh or Rotten.

FreshEye uses a MobileNetV2-based deep learning model for image
classification, Angular for the frontend, and FastAPI for backend
communication.

The application also provides general storage recommendations
to help users understand appropriate fruit storage conditions.

---

## 🎯 Project Objectives

- Develop an AI-based fruit freshness detection system.
- Classify fruit images as Fresh or Rotten.
- Provide a simple and user-friendly interface.
- Integrate deep learning with a web application.
- Provide general fruit storage recommendations.
- Explore technology-assisted approaches to reducing food waste.

---

## ✨ Features

### 🍎 AI-Based Freshness Detection
Uses a deep learning model to classify fruit images as Fresh or Rotten.

### 📸 Camera and Image Upload
Users can capture images using their device camera or upload images
from their gallery.

### 📊 Prediction Confidence
Displays the model's confidence percentage for each prediction.

### 🍌 Fruit Selection
Supports manual selection of three fruit types:

- Apple
- Banana
- Orange

### 🌿 Storage Recommendations
Provides general storage guidance based on the selected fruit.

Users can choose between:

- Room Temperature
- Refrigerator

### 🕘 Prediction History
Displays recent predictions during the current application session.

### 📱 Responsive Interface
Designed to work on desktop and mobile browsers.

---

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| Angular | Frontend Development |
| TypeScript | Frontend Logic |
| HTML | Page Structure |
| CSS | Styling |
| Bootstrap | Responsive Design |
| Python | Backend and AI Integration |
| FastAPI | REST API |
| TensorFlow | Deep Learning |
| Keras | Model Development |
| MobileNetV2 | Image Classification |
| Git & GitHub | Version Control |

---

## 🧠 Deep Learning Model

FreshEye uses MobileNetV2, a lightweight convolutional neural
network architecture suitable for image classification tasks.

### Model Details

| Parameter | Description |
|-----------|-------------|
| Architecture | MobileNetV2 |
| Learning Approach | Transfer Learning |
| Input | Fruit Image |
| Image Size | 224 × 224 pixels |
| Output | Fresh / Rotten |
| Classification Type | Binary Classification |

### Supported Fruits

- Apples
- Bananas
- Oranges

### Model Workflow

1. The user uploads a fruit image.
2. The frontend sends the image to the FastAPI backend.
3. The backend validates the uploaded image.
4. The image is resized and preprocessed.
5. The trained MobileNetV2 model analyzes the image.
6. The model predicts Fresh or Rotten.
7. The prediction and confidence percentage are returned.
8. The frontend displays the result.

**Note:** The model predicts freshness, not fruit type.
Fruit type is selected manually by the user.

---

## 🏗️ System Architecture

```text
              USER
                |
                v
        ANGULAR FRONTEND
                |
                v
        IMAGE UPLOAD
                |
                v
          FASTAPI API
                |
                v
       IMAGE PREPROCESSING
                |
                v
       MOBILENETV2 MODEL
                |
                v
      FRESH / ROTTEN RESULT
                |
                v
        ANGULAR FRONTEND
                |
                v
     PREDICTION DISPLAY
                |
                v
    STORAGE RECOMMENDATIONS
```

---

## 📂 Project Structure

```text
Food-Freshness-Detector/
│
├── backend/
│   ├── main.py
│   ├── model.keras
│   └── class_names.json
│
├── src/
│   └── app/
│       ├── components/
│       │   └── predict/
│       │       ├── predict.component.ts
│       │       ├── predict.component.html
│       │       └── predict.component.css
│       │
│       ├── services/
│       │   └── prediction.service.ts
│       │
│       └── models/
│           └── prediction.model.ts
│
├── package.json
├── angular.json
├── .gitignore
└── README.md
```

**Note:** The trained model file is excluded from Git tracking.
It must be obtained separately before running the backend.

---

## ⚙️ Installation and Setup

### Prerequisites

Install the following:

- Node.js
- Python
- Git
- Visual Studio Code

### Step 1: Clone the Repository

```bash
git clone <YOUR-REPOSITORY-URL>
```

Open the downloaded project folder.

### Step 2: Install Angular Dependencies

Open a terminal in the Angular project folder.

```bash
npm install
```

### Step 3: Install Backend Dependencies

Open another terminal and navigate to the backend folder.

```bash
cd backend
```

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the required Python packages:

```bash
pip install fastapi uvicorn tensorflow pillow python-multipart
```

Make sure the trained model file and class names file are
available in the locations expected by the backend.

### Step 4: Start the FastAPI Backend

From the backend directory:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

The API runs on port 8000.

### Step 5: Start the Angular Frontend

Open another terminal in the Angular project folder.

```bash
npx ng serve
```

Open the local Angular development address displayed in the terminal.

The frontend must be configured to communicate with the
running FastAPI backend.

---

## 🧪 Testing

The application should be tested using images that were not
included in the training dataset.

Recommended test cases include:

- Fresh apple image
- Rotten apple image
- Fresh banana image
- Rotten banana image
- Fresh orange image
- Rotten orange image
- Invalid file upload
- Large image upload
- Backend connection failure

### Model Evaluation

The trained model should be evaluated using a separate test dataset.

Relevant evaluation metrics include:

- Accuracy
- Precision
- Recall
- F1-Score
- Confusion Matrix

The reported model performance should be supported by
recorded evaluation results.

---

## 🌍 Social Relevance

FreshEye explores how artificial intelligence can support
visual food freshness assessment.

Potential benefits include:

- Raising awareness about food spoilage.
- Encouraging better fruit storage practices.
- Supporting technology-assisted food inspection.
- Exploring ways to reduce avoidable food waste.

### Sustainable Development Goals

**SDG 2 – Zero Hunger**

Explores technology that may contribute to improved food
management and reduced avoidable losses.

**SDG 9 – Industry, Innovation and Infrastructure**

Demonstrates the application of artificial intelligence
and software engineering to a practical problem.

**SDG 12 – Responsible Consumption and Production**

Supports awareness of responsible food consumption
and food waste reduction.

---

## ⚠️ Limitations

- The model currently supports apples, bananas, and oranges.
- The model performs binary Fresh/Rotten classification.
- Fruit type must be selected manually.
- Prediction accuracy depends on image quality and training data.
- Internal spoilage cannot always be identified from photographs.
- The system cannot guarantee whether food is safe to consume.
- Storage recommendations are general estimates, not predictions
  of the exact remaining shelf life.

---

## 🚀 Future Scope

Potential future improvements include:

1. Automatic fruit type identification.
2. Support for additional fruits and vegetables.
3. Android mobile application development.
4. Offline freshness prediction.
5. Improved model evaluation and generalization.
6. More detailed storage recommendations.
7. Deployment as a publicly accessible web application.

---

## 📌 Project Status

**Current Status:** Functional prototype

The application includes:

- Angular frontend
- FastAPI backend
- MobileNetV2 freshness classification
- Image upload and camera support
- Prediction confidence display
- Manual fruit selection
- General storage recommendations
- Session-based prediction history

---

## 📜 Disclaimer

FreshEye is an educational AI project.

Its predictions are based on visible image characteristics
and should not be used as the sole basis for food safety decisions.

---

## ⭐ Support

If you find this project interesting, consider giving
the repository a star!
