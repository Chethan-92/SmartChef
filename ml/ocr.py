import pytesseract
import cv2
import numpy as np
import re
from PIL import Image

# IMPORTANT: Set your tesseract path (adjust if different)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_from_image(image_path):
    # Read image
    img = cv2.imread(image_path)

    if img is None:
        return ""

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Increase contrast
    gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

    # Apply threshold
    thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

    # Convert to PIL
    pil_img = Image.fromarray(thresh)

    # Extract text
    text = pytesseract.image_to_string(pil_img, config='--psm 6')

    return text


def clean_ingredients(text):
    text = text.lower()

    # Remove special characters
    text = re.sub(r'[^a-zA-Z0-9,\s\[\]\(\)%]', ' ', text)

    # Split by commas
    words = text.split(",")

    cleaned = []

    for word in words:
        word = word.strip()
        if len(word) > 2:
            cleaned.append(word)

    return cleaned