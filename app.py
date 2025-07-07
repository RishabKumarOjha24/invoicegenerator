import streamlit as st
from PIL import Image
import pytesseract
from fpdf import FPDF
from datetime import datetime
import io
import re
from pdf2image import convert_from_bytes

# --- Sidebar Settings ---
st.sidebar.title("Invoice Generator Settings")
invoice_style = st.sidebar.selectbox("Choose Invoice Format", ["Simple", "Modern", "Minimal"])

st.title("Multi-Format Invoice Generator")

uploaded_file = st.file_uploader("Upload an invoice screenshot or PDF", type=["png", "jpg", "jpeg", "pdf"])

def extract_text_from_file(file):
    if file.type == "application/pdf":
        pages = convert_from_bytes(file.read())
        text = "\n".join([pytesseract.image_to_string(page) for page in pages])
        return text
    else:
        image = Image.open(file)
        return pytesseract.image_to_string(image)

if uploaded_file:
    text = extract_text_from_file(uploaded_file)
    st.subheader("Extracted Text")
    st.text(text)

    # Attempt to auto-extract fields
    entity_match = re.search(r"(?:From|To|Name|Entity):?\s*(.+)", text, re.IGNORECASE)
    date_match = re.search(r"(\d{2}[\/\-]\d{2}[\/\-]\d{4})", text)
    amount_match = re.search(r"(?:Total|Amount):?\s*\$?\s*([\d,]+\.\d{2})", text)
    description_match = re.search(r"(?:Description|For):?\s*(.+)", text)

    # Fallbacks if not found
    entity = st.text_input("Entity Name", entity_match.group(1).strip() if entity_match else "")
    date_input = st.date_input("Transaction Date", datetime.now().date())
    amount = st.text_input("Amount", amount_match.group(1).strip() if amount_match else "")
    description = st.text_area("Description", description_match.group(1).strip() if description_match else "")

    filename = f"{entity.replace(' ', '_')}_{date_input.strftime('%d_%m_%Y')}.pdf"

    # --- Generate PDF based on selected template ---
    pdf = FPDF()
    pdf.add_page()

    if invoice_style == "Simple":
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="INVOICE", ln=True, align='C')
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Entity: {entity}", ln=True)
        pdf.cell(200, 10, txt=f"Date: {date_input.strftime('%d-%m-%Y')}", ln=True)
        pdf.cell(200, 10, txt=f"Amount: ${amount}", ln=True)
        pdf.multi_cell(200, 10, txt=f"Description: {description}", align='L')

    elif invoice_style == "Modern":
        pdf.set_font("Arial", size=14)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(200, 10, txt="*** Invoice Summary ***", ln=True, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 10, f"""
        Entity: {entity}
        Date: {date_input.strftime('%d-%m-%Y')}
        Amount: ${amount}
        -------------------------
        Description: {description}
        """)

    elif invoice_style == "Minimal":
        pdf.set_font("Courier", size=12)
        pdf.multi_cell(0, 10, f"{entity} | {date_input.strftime('%d-%m-%Y')} | ${amount}")
        pdf.ln(10)
        pdf.multi_cell(0, 10, description)

    # --- Stream PDF as download ---
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)

    st.download_button(
        label="Download Invoice PDF",
        data=buffer,
        file_name=filename,
        mime="application/pdf"
    )
