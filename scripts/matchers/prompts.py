"""Claude API prompts for resume matching"""

RESUME_MATCHING_PROMPT = """You are an expert at matching resumes to government contract requirements with ABSOLUTE PRECISION.

CRITICAL RULES - READ CAREFULLY:
1. The resume is the ONLY source of truth
2. NEVER invent, assume, or infer anything not explicitly stated in the resume
3. ALL evidence must be EXACT QUOTES from the resume
4. If information is not in the resume, mark as "not_evidenced"
5. When calculating years of experience:
   - ONLY count if dates are explicitly stated in the resume
   - If dates are vague ("Recent", "Currently") -> partial evidence at best
   - If no dates -> mark years_calculated as null
6. Distinguish between "meets" (clear evidence), "partial" (some evidence), and "not_evidenced" (no evidence)

For EACH requirement, provide:
- status: "meets" | "partial" | "not_evidenced"
- evidence_snippets: [array of EXACT quotes from resume]
- roles_used: [which job titles/roles provided the evidence]
- years_calculated: number or null (only if dates exist)
- confidence: 0.0-1.0 (0.9-1.0 = strong evidence, 0.6-0.8 = partial, <0.6 = weak/none)
- reasoning: brief explanation of assessment

RESUME TEXT:
{resume_text}

REQUIREMENTS TO MATCH:
{requirements_json}

OUTPUT FORMAT (JSON):
{{
    "candidate_name": "extracted from resume",
    "resume_file": "{resume_file_name}",
    "opportunity_id": "{opportunity_id}",
    "match_results": [
        {{
            "requirement_id": "REQ-001",
            "requirement_text": "...",
            "status": "meets|partial|not_evidenced",
            "evidence_snippets": ["exact quote 1", "exact quote 2"],
            "roles_used": ["Senior Software Engineer at XYZ Corp"],
            "years_calculated": 5.5 or null,
            "confidence": 0.85,
            "reasoning": "Resume shows 5.5 years of Python development across two roles with specific dates (2018-2021, 2021-present)."
        }}
    ],
    "overall_match_percentage": 75.5,
    "critical_gaps": ["REQ-003: Active security clearance", "REQ-007: Government contracting experience"]
}}

Return ONLY the JSON, no other text."""


def create_matching_prompt(
    resume_text: str,
    resume_file_name: str,
    opportunity_id: str,
    requirements: list
) -> str:
    """Create the resume matching prompt"""
    import json

    # Format requirements as JSON
    requirements_json = json.dumps(requirements, indent=2)

    return RESUME_MATCHING_PROMPT.format(
        resume_text=resume_text,
        resume_file_name=resume_file_name,
        opportunity_id=opportunity_id,
        requirements_json=requirements_json
    )
