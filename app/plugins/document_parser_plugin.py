from semantic_kernel.functions import kernel_function
from extractors import extract_fields, extract_text_with_ocr


@kernel_function(name="extractText", description="Extract English OCR text from document")
def extract_text(args: dict) -> dict:
    path = args.get("file_path", "")
    return { "text": extract_text_with_ocr(path) }

@kernel_function(name="extractFields", description="Extract structured fields from OCR text")
def extract_fields_plugin(args: dict) -> dict:
    text = args.get("text", "")
    doc_type = args.get("doc_type", "")
    return { "fields": extract_fields(text, doc_type) }