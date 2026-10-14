"""Claude API prompts for opportunity parsing"""

OPPORTUNITY_PARSING_PROMPT = """You are an expert at analyzing government contract opportunities and extracting requirements.

Given the following opportunity document text, extract and structure ALL qualifications and requirements.

CRITICAL RULES:
1. Separate REQUIRED vs PREFERRED qualifications clearly
2. Extract EVERY requirement, no matter how small
3. Categorize each requirement (technical_experience, education, clearance, certifications, domain_knowledge, etc.)
4. Preserve exact wording from the document
5. Assign sequential IDs (REQ-001, REQ-002... PREF-001, PREF-002...)
6. Extract opportunity metadata (title, agency, due_date if present)

OUTPUT FORMAT (JSON):
{{
    "opportunity_id": "extracted from filename or generated from title",
    "title": "...",
    "agency": "...",
    "due_date": "YYYY-MM-DD or null",
    "required_qualifications": [
        {{
            "id": "REQ-001",
            "text": "exact requirement text",
            "category": "technical_experience|education|clearance|certification|domain_knowledge|other",
            "is_required": true
        }}
    ],
    "preferred_qualifications": [
        {{
            "id": "PREF-001",
            "text": "exact requirement text",
            "category": "technical_experience|education|clearance|certification|domain_knowledge|other",
            "is_required": false
        }}
    ]
}}

OPPORTUNITY DOCUMENT:
{opportunity_text}

FILENAME: {filename}

Return ONLY the JSON, no other text."""


def create_parsing_prompt(opportunity_text: str, filename: str) -> str:
    """Create the opportunity parsing prompt"""
    return OPPORTUNITY_PARSING_PROMPT.format(
        opportunity_text=opportunity_text,
        filename=filename
    )
