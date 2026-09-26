# 🍳 SmartChef — Intelligent Recipe Generator

SmartChef is an intelligent recipe-generation web application that helps users discover recipes from available ingredients. The project combines a web interface with machine-learning and computer-vision components for ingredient recognition, OCR-based input, and recipe recommendation.

## ✨ Features

- 🥗 **Ingredient-based recipe generation** — find recipes based on available ingredients.
- 📷 **Ingredient image processing** — process ingredient images using computer-vision/ML components.
- 🔎 **OCR support** — extract ingredient information from images/text.
- 🤖 **ML-based recommendations** — recommend relevant recipes using machine-learning components.
- ❤️ **Favorites** — save and manage favorite recipes.
- 👤 **User pages** — login, dashboard, home, favorites, and contact pages.
- 🗃️ **Recipe dataset** — recipe information is stored in a structured CSV dataset.
- 🔐 **Environment-based API configuration** — API credentials are kept outside the source code using `.env`.

## 🛠️ Technology Stack

| Area | Technologies |
|---|---|
| Frontend | HTML |
| Backend | Python |
| Machine Learning | Python ML components |
| Computer Vision | Image processing, YOLO |
| OCR | OCR processing |
| Data | CSV recipe dataset |
| API | Groq API |
| Version Control | Git & GitHub |

## 🧠 Machine Learning Components

The `ml/` directory contains the project's ML-related modules:

- `image_processing.py` — image-processing functionality
- `model_loader.py` — model loading
- `ocr.py` — OCR-related processing
- `recommender.py` — recipe recommendation logic
- `recommender_ml.py` — ML-based recommendation functionality

The project also includes a YOLO model file (`yolov8n.pt`) for computer-vision functionality.

## 📁 Project Structure

```text
SmartChef/
│
├── dataset/
│   └── recipes.csv
│
├── ml/
│   ├── image_processing.py
│   ├── model_loader.py
│   ├── ocr.py
│   ├── recommender.py
│   └── recommender_ml.py
│
├── main.py
├── database.py
├── models.py
├── schemas.py
├── import_recipes.py
│
├── home.html
├── login.html
├── dashboard.html
├── favorites.html
└── contact.html
```

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/Chethan-92/SmartChef.git
cd SmartChef
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

Install the packages required by the project. If a `requirements.txt` file is added later, use:

```bash
pip install -r requirements.txt
```

For the environment-variable integration used by the current project:

```bash
pip install python-dotenv
```

Depending on the ML/OCR configuration, additional packages used by the project may also be required.

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

**Never commit `.env` or API keys to GitHub.**

The application reads the key from the environment rather than storing it directly in source code.

## ▶️ Running the Project

After activating the virtual environment and installing the required dependencies:

```bash
python main.py
```

Follow the application's configured local URL/output to access SmartChef.

> The exact run command may depend on the backend framework and configuration used in your local environment.

## 🔄 How It Works

```text
User
  │
  ├── Enters ingredients
  │
  ├── Uploads/processes ingredient image
  │
  ▼
Ingredient Processing / OCR
  │
  ▼
Recipe & ML Recommendation
  │
  ▼
SmartChef
  │
  ├── Suggested Recipes
  ├── Recipe Details
  └── Favorites
```

## 🎯 Project Objective

The objective of SmartChef is to make recipe discovery easier by connecting available ingredients with intelligent recipe recommendations. The project explores the integration of web development, machine learning, computer vision, OCR, and AI-assisted functionality in a single application.

## 🚀 Future Enhancements

- Improve ingredient-detection accuracy.
- Add nutrition and calorie information.
- Support multilingual recipe recommendations.
- Add personalized recommendations based on user preferences.
- Improve responsive UI/UX.
- Add automated tests and deployment.
- Provide a production-ready API and database architecture.

## 👨‍💻 Project

**SmartChef — Ingredient-Based Intelligent Recipe Generator System**

Developed as part of an **Infosys Springboard internship project** and maintained here as a personal portfolio showcase.

---

⭐ If you find this project useful, feel free to explore the repository and the implementation.
