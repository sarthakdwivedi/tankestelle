import streamlit as st
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
#import pyheif
import io
import pandas as pd

# Path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\Tesseract.exe"  # Update this to your Tesseract-OCR installation path

def preprocess_image(image):
    """ Preprocess the image for better OCR results """
    image = image.convert('L')  # Convert to grayscale
    image = image.filter(ImageFilter.SHARPEN)  # Sharpen the image
    image = ImageEnhance.Contrast(image).enhance(2)  # Enhance contrast
    return image

def extract_text_from_image(image):
    """ Extract text from the preprocessed image """
    return pytesseract.image_to_string(image)

def parse_amounts(text):
    """ Parse net, tax, and gross amounts from the extracted text """
    lines = text.split('\n')
    net_line = next((line for line in lines if "Netto" in line), None)
    next_line_index = lines.index(net_line) + 1 if net_line else None
    next_line = lines[next_line_index] if next_line_index and next_line_index < len(lines) else None
    
    net_line_words = net_line.split() if net_line else []
    next_line_words = next_line.split() if next_line else []
    
    # Extract numbers from the next line
    numbers = re.findall(r'\d+[\.,]?\d*', next_line)
    
    amounts = {
        'Net': numbers[1] if len(numbers) > 1 else None,
        'Tax': numbers[2] if len(numbers) > 2 else None,
        'Gross': numbers[3] if len(numbers) > 3 else None,
        'Net_Line_Words': net_line_words,
        'Next_Line_Words': next_line_words
    }

    return amounts

def read_heic_image(file):
    """ Read HEIC image and convert to PIL Image """
    # heif_file = pyheif.read_heif(file)
    # image = Image.frombytes(
        # heif_file.mode,
        # heif_file.size,
        # heif_file.data,
        # "raw",
        # heif_file.mode,
        # heif_file.stride,
    # )
    return image

def save_corrections(original, corrected):
    """ Save corrections to a CSV file """
    df = pd.DataFrame([original, corrected], index=["Original", "Corrected"])
    df.to_csv('corrections.csv', mode='a', header=False)

def main():
    st.title("Extract Net, Tax, and Gross Amounts from Image")
    
    uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png", "heic"])
    
    if uploaded_file is not None:
        file_type = uploaded_file.type
        if file_type == "image/heic":
            image = read_heic_image(uploaded_file)
        else:
            image = Image.open(uploaded_file)
        
        st.image(image, caption='Uploaded Image', use_column_width=True)
        
        preprocessed_image = preprocess_image(image)
        extracted_text = extract_text_from_image(preprocessed_image)
        amounts = parse_amounts(extracted_text)
        
        st.subheader("Extracted Text")
        st.text(extracted_text)
        
        st.subheader("Extracted Amounts")
        st.json(amounts)
        
        original_amounts = {}
        corrected_amounts = {}
        
        for key, value in amounts.items():
            if key not in ['Net_Line_Words', 'Next_Line_Words']:
                original_amounts[key] = value
                corrected_amounts[key] = st.text_input(f"Correct {key}", value=value if value else "")
        
        if st.button("Save Corrections"):
            save_corrections(original_amounts, corrected_amounts)
            st.success("Corrections saved successfully.")
        
        st.subheader("Parsing Debug Info")
        st.json({
            "Extracted Text": extracted_text,
            "Parsed Amounts": amounts,
            "Net Line Words": amounts['Net_Line_Words'],
            "Next Line Words": amounts['Next_Line_Words'],
        })

if __name__ == "__main__":
    main()
