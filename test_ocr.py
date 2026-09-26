import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

img = Image.open("test.jpg")   # put your biscuit image name here

text = pytesseract.image_to_string(img)

print(text)