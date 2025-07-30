import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import re
from langdetect import detect
from field_config import FIELD_KEYS
from semantic_kernel.functions import kernel_function

# 🧠 OCR + Language Filtering
def extract_text_with_ocr(path: str) -> str:
    doc = fitz.open(path)
    all_text = ""

    for page in doc:
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = pytesseract.image_to_string(img)
        all_text += text + "\n"



    return all_text

# 🧩 Dispatch Extraction Based on Document Type
def extract_fields(text: str, doc_type: str) -> dict:
    if not text.strip():
        return {}

    extractors = {
        "PAN": extract_pan_fields,
        "Aadhar": extract_aadhaar_fields,
        "Policy": extract_policy_fields,
        "Invoice": extract_invoice_fields,
    }

    extractor = extractors.get(doc_type)
    if extractor:
        return extractor(text)
    else:
        print(f"⚠️ No extractor available for doc type: {doc_type}")
        return {}

# 🔹 PAN Card
def extract_pan_fields(text: str) -> dict:
    fields = {}

    # Split into cleaned lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # PAN Number
    pan_match = re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text)
    fields["Pan number"] = pan_match.group(0) if pan_match else ""

    # Name (look for all-uppercase line that doesn't contain keywords)
    name_candidates = [line for line in lines if re.match(r"^[A-Z\s]{3,}$", line)]
    fields["name"] = name_candidates[0] if name_candidates else ""

    # Father's Name (next all-uppercase line after name)
    name_index = lines.index(fields["name"]) if fields["name"] in lines else -1
    father_line = lines[name_index + 1] if name_index != -1 and name_index + 1 < len(lines) else ""
    fields["father's name"] = father_line if re.match(r"^[A-Z\s]{3,}$", father_line) else ""

    # DOB (find first valid date format)
    dob_match = re.search(r"\b\d{2}/\d{2}/\d{4}\b", text)
    fields["dob"] = dob_match.group(0) if dob_match else ""

    return fields


    fields = {}

    # PAN Number: format like ABCDE1234F
    pan_match = re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text)
    fields["Pan number"] = pan_match.group(0) if pan_match else ""

    # Name: after "Name"
    name_match = re.search(r"Name\s*\n([A-Z][A-Z\s]+)", text)
    fields["name"] = name_match.group(1).strip() if name_match else ""

    # Father's Name: after "Father's Name"
    father_match = re.search(r"Father's Name\s*\n([A-Z][A-Z\s]+)", text)
    fields["father's name"] = father_match.group(1).strip() if father_match else ""

    # DOB: after "Date of Birth"
    dob_match = re.search(r"Date of Birth\s*\n(\d{2}/\d{2}/\d{4})", text)
    fields["dob"] = dob_match.group(1) if dob_match else ""

    return fields


# 🔹 Aadhaar
def extract_aadhaar_fields(text: str) -> dict:
    fields = {}
    fields["uid"] = re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", text).group(0).replace(" ", "") if re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", text) else ""
    fields["dob"] = re.search(r"\b\d{2}/\d{2}/\d{4}\b", text).group(0) if re.search(r"\b\d{2}/\d{2}/\d{4}\b", text) else ""
    fields["name"] = re.search(r"\b[A-Z]{2,}\s[A-Z]{2,}\b", text).group(0) if re.search(r"\b[A-Z]{2,}\s[A-Z]{2,}\b", text) else ""

    return fields

# 🔹 Insurance Policy
import re

def extract_policy_fields(text: str) -> dict:
    fields = {}

    # Normalize text: lowercase, remove extra spaces, replace line breaks
    clean_text = re.sub(r"\s+", " ", text).lower()

    # Policy number (accept formats with trailing slash or extra digits)
    match = re.search(r"policy number[:\s]*([a-z0-9\-\/]+)", clean_text)
    fields["policy number"] = match.group(1).split("/")[0] if match else ""

    # Insured name — look for a name-like sequence near the word "owner" or "insured"
    name_match = re.search(r"(owner|insured)[^a-zA-Z]*([a-z]{2,}\s[a-z]{2,})", clean_text)
    fields["insured name"] = name_match.group(2).title() if name_match else ""

    # Expiry date — flexible capture using keywords near dates
    expiry_match = re.search(r"(expire|expires|valid till)[^\d]*(\d{2}/\d{2}/\d{4})", clean_text)
    fields["expiry date"] = expiry_match.group(2) if expiry_match else ""

    # Start date — try detecting near the word "start" or "from"
    start_match = re.search(r"(start|from)[^\d]*(\d{2}/\d{2}/\d{4})", clean_text)
    fields["start date"] = start_match.group(2) if start_match else ""

    # Insurance provider — look for known entities or words around "insurer"
    provider_match = re.search(r"(insurance company|insurer)[:\s]*([a-z&\s]+)", clean_text)
    fields["insurance provider"] = provider_match.group(2).title().strip() if provider_match else ""

    return fields


# 🔹 Invoice
def extract_invoice_fields(text: str) -> dict:
    fields = {}
    fields["vendor name"] = re.search(r"(Vendor|Seller|Company)[:\s]*([\w\s&]+)", text).group(2).strip() if re.search(r"(Vendor|Seller|Company)[:\s]*([\w\s&]+)", text) else ""
    fields["total amount"] = re.search(r"(Total Amount|Grand Total)[:\s]*₹?\s?([\d,]+)", text).group(2).replace(",", "") if re.search(r"(Total Amount|Grand Total)[:\s]*₹?\s?([\d,]+)", text) else ""
    fields["line items"] = re.findall(r"\d+\s+[A-Za-z\s]+\s+\d+\s+₹?\d+", text)

    return fields
