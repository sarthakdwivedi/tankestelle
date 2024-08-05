import streamlit as st
import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re

# No need to set pytesseract.pytesseract.tesseract_cmd as Streamlit Share should handle it

st.title("Extract Net, Tax, and Gross Amounts from Image")

uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

# Ensure the directories exist
output_folder = 'output'
wip_folder = 'wip'
os.makedirs(output_folder, exist_ok=True)
os.makedirs(wip_folder, exist_ok=True)

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
    net_line = next((line for line in lines if "Netto" in line or "Net" in line), None)
    next_line_index = lines.index(net_line) + 1 if net_line else None
    next_line = lines[next_line_index] if next_line_index and next_line_index < len(lines) else None
    
    # Extract numbers from the next line
    numbers = re.findall(r'\d+[\.,]?\d*', next_line if next_line else "")
    amounts = {
        'Net': numbers[0] if len(numbers) > 0 else None,
        'Tax': numbers[1] if len(numbers) > 1 else None,
        'Gross': numbers[2] if len(numbers) > 2 else None,
    }

    return amounts

def add_summary_row(df):
    summary_row = {}
    for column in df.columns:
        if df[column].dtype in [float, int]:  # Only sum numeric columns
            summary_row[column] = df[column].sum()
        else:  # Set 'taxi_numbers' to 'Summe' for the summary row
            summary_row[column] = 'Summe'
    
    # Convert the summary_row dictionary to a DataFrame
    summary_df = pd.DataFrame([summary_row])
    
    # Use pd.concat to append the summary row to the original DataFrame
    return pd.concat([df, summary_df], ignore_index=True)

def generate_excel_file(tax_amounts):
    output_excel_path = os.path.join(output_folder, "extracted_data.xlsx")
    wb = Workbook()
    ws = wb.active
    ws.title = "Data"
    
    bold_font = Font(bold=True)  # Create a bold font object

    df = pd.DataFrame(tax_amounts)
    # df = add_summary_row(df)

    # Write DataFrame to Excel with bold headers
    for r, df_row in enumerate(dataframe_to_rows(df, index=False, header=True), start=1):
        for c, value in enumerate(df_row, start=1):
            cell = ws.cell(row=r, column=c, value=value)
            # Apply bold formatting to header row
            if r == 1:
                cell.font = bold_font

    # Save the workbook
    wb.save(output_excel_path)
    
    if os.path.exists(output_excel_path):
        st.success(f"Data successfully extracted and written to {output_excel_path}")
    
        # Read the file into a BytesIO object
        with open(output_excel_path, 'rb') as f:
            data = f.read()
        
        # Create a download button
        st.download_button(
            label="Download Excel file",
            data=data,
            file_name="extracted_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error(f"Failed to create the file: {output_excel_path}")

if uploaded_file:
    uploaded_file_name = uploaded_file.name
    file_with_path = os.path.join(wip_folder, uploaded_file_name)

    image = Image.open(uploaded_file)
        
    st.image(image, caption='Uploaded Image', use_column_width=True)
    
    preprocessed_image = preprocess_image(image)
    extracted_text = extract_text_from_image(preprocessed_image)
    tax_amounts = parse_amounts(extracted_text)
    
    #st.subheader("Extracted Text")
    #st.text(extracted_text)
    
    #st.subheader("Extracted Amounts")
    #st.json(tax_amounts)

    for key, value in tax_amounts.items():
        tax_amounts[key] = st.text_input(f"Correct {key}", value=value if value else "")

    if st.button('Save corrections'):
        generate_excel_file([tax_amounts])
