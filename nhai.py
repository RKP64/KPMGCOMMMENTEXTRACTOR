import streamlit as st
import fitz  # PyMuPDF for PDF processing
import io
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Load API key securely from Streamlit secrets
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

if not GEMINI_API_KEY:
    st.error("API Key not found! Please set it in Streamlit secrets.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

def extract_colored_comments_from_pdf(uploaded_file):
    """Extract colored text (comments) from a PDF."""
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    extracted_text = []

    for page in doc:
        for text in page.get_text("dict")["blocks"]:
            if "lines" in text:
                for line in text["lines"]:
                    for span in line["spans"]:
                        color = span["color"]  # Extract text color

                        # Ignore black text (color = 0 in PyMuPDF)
                        if color != 0:
                            extracted_text.append(span["text"])

    return "\n".join(extracted_text)

def process_text_with_gemini(text):
    """Enhance extracted comments using Gemini AI."""
    prompt = f"""
    You are an AI assistant helping to refine and summarize extracted comments.
    - Summarize the text while keeping all key details.
    - Categorize comments based on their topics.
    - Improve readability and remove unnecessary text.
    Extracted comments:
    {text}
    """

    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    
    return response.text if response.text else "No response from AI."

def generate_pdf(text):
    """Create a PDF with extracted/processed text."""
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.setFont("Helvetica", 12)

    y_position = 750  # Start writing from top of the page
    for line in text.split("\n"):
        c.drawString(50, y_position, line)
        y_position -= 20
        if y_position < 50:  # New page if text exceeds the limit
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = 750

    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

# Streamlit UI
st.title("AI-Based Comment Extractor Powered by KPMG")
st.write("Upload a PDF, extract **colored comments**, process them with AI, and download the refined content.")

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_file:
    # User choice: Raw Extraction or AI Processed Output
    extraction_method = st.radio("Choose Extraction Method:", ("Raw Extraction", "AI Processed Output"))

    with st.spinner("Extracting colored comments..."):
        extracted_text = extract_colored_comments_from_pdf(uploaded_file)

    if extracted_text:
        st.subheader("Extracted Colored Comments")
        st.write(extracted_text)

        # Process with Gemini if selected
        if extraction_method == "AI Processed Output":
            with st.spinner("Processing with Gemini AI..."):
                extracted_text = process_text_with_gemini(extracted_text)
            st.subheader("Refined Comments (Gemini Output)")
            st.write(extracted_text)

        # Generate final PDF
        pdf_buffer = generate_pdf(extracted_text)

        st.subheader("Download Processed Comments as PDF")
        st.download_button(label="Download PDF",
                           data=pdf_buffer,
                           file_name="processed_colored_comments.pdf",
                           mime="application/pdf")
    else:
        st.warning("No colored comments detected.")




















    





