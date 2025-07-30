# app/field_config.py

FIELD_KEYS = {
    "Aadhar": {
        "uid": "12digits",
        "name": "string",
        "address": "string",
        "father's name": "string",
        "dob": "date"
    },
    "PAN": {
        "Pan number": "string",
        "name": "string",
        "dob": "date"
    },
    "Insurance": {
        "policy number": "string",
        "expiry date": "date",
        "start date": "date",
        "vehicle id number": "string",
        "engine number": "string",
        "insurance provider": "string"
    },
    "Invoice": {
        "vendor_name": "string",
        "total_amount": "integer",
        "line_items": "list",
        "date": "date",
    }
}
