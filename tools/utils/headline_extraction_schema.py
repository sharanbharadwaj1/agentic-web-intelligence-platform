# tools/utils/headline_extraction_schema.py

HEADLINE_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "headlines": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1,
            "maxItems": 10
        }
    },
    "required": ["headlines"],
    "additionalProperties": False
}

