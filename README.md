# Gov Submission Bot

A pipeline that checks candidate resumes against the requirements in government contract solicitations
(RFPs/SOWs). For each candidate it produces an evidence-backed **requirements compliance matrix**, a
**risk assessment**, and a draft submission email.

## Why I built it

Responding to a government opportunity means proving, requirement by requirement, that the people you
propose actually meet the contract's qualifications. Doing that by hand is slow, and it's easy to overstate
a fit. I wanted a tool that works like a compliance reviewer: pull out every requirement, map each one
to proof in the resume, and flag the gaps and risks before anything is submitted.

The core rule is that **the resume is the only source of truth**. The model has to quote exact evidence,
and the code checks every quote against the resume text. If a claim can't be traced back to the resume, it gets downgraded.

## How it works

```
inbox/ + resumes/ ─► Extract (PDF/DOCX) ─► Parse requirements ─► Match resume to each requirement
                                              │                        │
                                     opps/<id>/requirements.json   evidence validation (fuzzy quote check)
                                                                       │
                       outputs/<opp>/<candidate>/ ◄─ Bundle: matrix + risk flags + email ─► Slack summary
```

1. **Extract**: read text from PDF (pdfminer.six) and DOCX (python-docx) files.
2. **Parse**: an LLM (Anthropic API, temperature 0) turns the solicitation into structured requirements
   (required vs. preferred), saved as `opps/<opp_id>/requirements.json`.
3. **Match**: each requirement is scored against each resume as *Meets / Partial / Not Evidenced*, with
   exact evidence snippets, years of experience where it can be calculated, and a confidence score.
4. **Validate evidence**: every quoted snippet is checked against the resume with RapidFuzz. If a snippet
   isn't found, the match is downgraded, so made-up evidence can't pass as compliant.
5. **Generate the bundle** for each candidate and opportunity:
   - `requirements_matrix.md`: requirement → status → evidence → confidence
   - `risk_flags.md`: critical gaps (unmet required quals), missing preferred quals, low-confidence matches,
     strengths, an overall **HIGH / MEDIUM / LOW** risk rating and a recommendation
   - `submission_email.txt`: a draft email with a summary of qualifications
6. **Notify**: post a run summary and any errors to Slack through an incoming webhook.

### Risk rating logic
- **HIGH**: 3 or more unmet or partially met *required* qualifications
- **MEDIUM**: at least 1 required gap, or 3 or more low-confidence matches
- **LOW**: neither of the above

### Resilience
- One bad file is logged and skipped, and doesn't crash the run.
- API calls retry with exponential backoff (1s / 2s / 4s).
- Every run writes a timestamped log to `logs/`.

## Tech stack

Python 3, Anthropic API, pdfminer.six, python-docx, RapidFuzz, httpx, python-dotenv, Slack incoming webhooks.

## Project structure

```
scripts/
├── run_pipeline.py      # orchestrator
├── config.py            # settings loaded from env
├── logger.py
├── models/              # Opportunity, Resume, MatchResult, Bundle dataclasses
├── extractors/          # PDF/DOCX extraction (factory pattern)
├── parsers/             # requirement extraction + prompts
├── matchers/            # resume ↔ requirement matching + evidence validation
├── generators/          # matrix, risk, email, bundle writer
└── notifiers/           # Slack
inbox/  resumes/         # inputs (git-ignored; real documents never get committed)
opps/   outputs/         # generated (git-ignored)
```

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # set ANTHROPIC_API_KEY; SLACK_WEBHOOK_URL is optional
```

## Usage

```bash
cp /path/to/solicitation.pdf inbox/
cp /path/to/candidate_resume.docx resumes/
python -m scripts.run_pipeline
ls outputs/
```

## Status / Roadmap

Status: the end-to-end pipeline works and I've run it on real solicitations and resumes. That data is private and isn't in this repo.

Roadmap:
- Sample (fictional) solicitation and resume so anyone can run a demo
- Unit tests for evidence validation and risk scoring
- Export the matrix to Excel/CSV for proposal teams
- Make the risk thresholds configurable

## Data handling

Resumes and solicitations can contain personal and procurement-sensitive information. The `.gitignore`
keeps every input and output folder out of version control, and secrets live only in `.env`.
